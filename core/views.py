import logging
import json
from datetime import datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db import transaction, models
from django.db.models import Q, Avg, F, Count
from decimal import Decimal
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY

logger = logging.getLogger(__name__)

from django.utils import timezone
from django.utils.dateparse import parse_datetime
from core.models import Car, Booking, Review, Wishlist, PromoCode, Profile, Notification
from accounts.models import UserProfile
from .forms import BookingLocationForm, BookingDatesForm, BookingStepOneForm, ReviewForm, ContactForm
from core.services import (
    BookingService, RefundService, TripExtensionService, 
    LateReturnService, TollReconcilerService, EmergencySOSService, 
    VehicleInspectionService
)


def parse_session_date(date_str):
    """Parse session date string supporting ISO and Y-m-d formats."""
    if not date_str:
        return None
    # Try ISO format first (from .isoformat())
    try:
        dt = datetime.fromisoformat(date_str)
        if timezone.is_aware(dt):
            dt = timezone.localtime(dt).replace(tzinfo=None)
        return dt
    except (ValueError, TypeError):
        pass
    # Try 'Y-m-d H:M'
    if ' ' in date_str:
        try:
            return datetime.strptime(date_str, '%Y-%m-%d %H:%M')
        except ValueError:
            pass
    # Fallback to date-only
    try:
        return datetime.combine(datetime.strptime(date_str, '%Y-%m-%d').date(), datetime.min.time())
    except ValueError:
        return None


def send_booking_email(booking, request=None):
    """Send professional HTML booking confirmation with PDF invoice to User and Admin."""
    subject = f'Booking Confirmed: {booking.booking_reference}'
    admin_email = getattr(settings, 'ADMIN_EMAIL', settings.DEFAULT_FROM_EMAIL)
    
    # Context for template
    context = {
        'booking': booking,
        'domain': settings.DOMAIN_URL,
    }
    
    # Render HTML and Text versions
    html_content = render_to_string('emails/booking_confirmation_email.html', context)
    text_content = strip_tags(html_content)
    
    # Generate PDF Invoice
    pdf_buffer = None
    try:
        from .utils_pdf import render_invoice_pdf
        pdf_buffer, pdf_ok = render_invoice_pdf(booking)
        if not pdf_ok:
            logger.warning(f"PDF generation failed for {booking.booking_reference}, sending email without attachment")
            pdf_buffer = None
    except Exception as e:
        logger.error(f"PDF generation error: {e}", exc_info=True)
    
    # --- 1. Send to USER ---
    try:
        user_email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[booking.user.email],
        )
        user_email.attach_alternative(html_content, "text/html")
        if pdf_buffer:
            user_email.attach(
                f'Invoice_{booking.booking_reference}.pdf',
                pdf_buffer.read(),
                'application/pdf'
            )
            pdf_buffer.seek(0)  # Reset for admin email
        user_email.send()
        logger.info(f"Confirmation email sent to USER {booking.user.email} for {booking.booking_reference}")
    except Exception as e:
        logger.error(f"Failed to send user booking email: {e}", exc_info=True)
    
    # --- 2. Send to ADMIN ---
    try:
        admin_subject = f'[ADMIN] New Booking: {booking.booking_reference} — {booking.car.brand} {booking.car.name}'
        admin_text = (
            f"New booking received!\n\n"
            f"Reference: {booking.booking_reference}\n"
            f"Customer: {booking.user.get_full_name() or booking.user.username} ({booking.user.email})\n"
            f"Vehicle: {booking.car.brand} {booking.car.name}\n"
            f"Pickup: {booking.pickup_location} on {booking.pickup_date}\n"
            f"Drop-off: {booking.dropoff_location} on {booking.dropoff_date}\n"
            f"Total: ₹{booking.total_with_gst}\n"
            f"Status: PAID\n"
        )
        admin_msg = EmailMultiAlternatives(
            subject=admin_subject,
            body=admin_text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[admin_email],
        )
        admin_msg.attach_alternative(html_content, "text/html")
        if pdf_buffer:
            admin_msg.attach(
                f'Invoice_{booking.booking_reference}.pdf',
                pdf_buffer.read(),
                'application/pdf'
            )
        admin_msg.send()
        logger.info(f"Admin notification email sent to {admin_email} for {booking.booking_reference}")
    except Exception as e:
        logger.error(f"Failed to send admin booking email: {e}", exc_info=True)

# Note: PROMO_CODES are now managed in the Database via PromoCode model
def index_view(request):
    """Landing page with high-performance internal caching."""
    from django.core.cache import cache
    
    # Cache the heavy car data query for 5 minutes
    # This ensures 10k users don't hammer the DB, but keeps UI dynamic for each user
    all_available = cache.get('homepage_cars_data')
    if not all_available:
        all_available = list(Car.objects.filter(is_available=True).annotate(
            avg_rating=Avg('reviews__rating')
        ).prefetch_related('reviews'))
        cache.set('homepage_cars_data', all_available, 300) # 5 min cache
    
    # Categorization in memory (extremely fast)
    budget_cars = [c for c in all_available if c.price_per_day <= 2500][:6]
    mid_range_cars = [c for c in all_available if 2500 < c.price_per_day <= 10000][:6]
    electric_cars = [c for c in all_available if 'Electric' in (c.fuel_type or '')][:6]
    
    city_names = ['Alto K10', 'Swift', 'i20']
    family_names = ['Innova Crysta', 'Ertiga', 'Safari', 'Alcazar']
    weekend_names = ['Thar', 'Scorpio N', 'Fortuner', 'Thar Roxx']
    airport_names = ['Dzire', 'City', 'Verna']
    luxury_cats = ['Luxury Sedan', 'Ultra Luxury', 'Premium SUV']

    city_cars = [c for c in all_available if c.name in city_names][:3]
    family_cars = [c for c in all_available if c.name in family_names][:3]
    weekend_cars = [c for c in all_available if c.name in weekend_names][:3]
    airport_cars = [c for c in all_available if c.name in airport_names][:3]
    luxury_cars = [c for c in all_available if c.price_per_day > 10000 or c.category in luxury_cats][:6]

    wishlisted_car_ids = []
    if request.user.is_authenticated:
        wishlisted_car_ids = list(Wishlist.objects.filter(user=request.user).values_list('car_id', flat=True))

    context = {
        'all_available': all_available[:8],
        'budget_cars': budget_cars,
        'electric_cars': electric_cars,
        'city_cars': city_cars,
        'family_cars': family_cars,
        'weekend_cars': weekend_cars,
        'airport_cars': airport_cars,
        'luxury_cars': luxury_cars,
        'mid_range_cars': mid_range_cars,
        'wishlisted_car_ids': wishlisted_car_ids,
        'contact_form': ContactForm(),
        'current_city': request.session.get('current_city', 'Bhubaneswar'),
    }
    return render(request, 'index.html', context)


def how_it_works_view(request):
    """Dedicated How it Works page featuring the complete 5-step self-drive process."""
    return render(request, 'how-it-works.html', {'active_tab': 'how_it_works'})


def subscription_view(request):
    """Dedicated Car Subscription (Long-Term Monthly Mobility) page."""
    featured_cars = Car.objects.filter(is_available=True).order_by('-price_per_day')[:8]
    context = {
        'active_tab': 'subscription',
        'featured_cars': featured_cars,
        'current_city': request.session.get('current_city', 'Bhubaneswar'),
    }
    return render(request, 'subscription.html', context)


def airport_transfer_view(request):
    """Dedicated Airport Transfer (Live Flight Tracking & Terminal Hubs) page."""
    airport_cars = Car.objects.filter(is_available=True).filter(
        Q(category__in=['Sedan', 'SUV', 'Premium SUV', 'Luxury Sedan', 'MPV']) |
        Q(brand__in=['Toyota', 'Maruti Suzuki', 'Hyundai', 'BMW', 'Mercedes-Benz'])
    )[:8]
    context = {
        'active_tab': 'airport_transfer',
        'airport_cars': airport_cars,
        'current_city': request.session.get('current_city', 'Bhubaneswar'),
    }
    return render(request, 'airport-transfer.html', context)


def why_rentora_view(request):
    """Dedicated Why Rentora page showcasing Rentora's key advantages and value props."""
    context = {
        'active_tab': 'why_rentora',
        'current_city': request.session.get('current_city', 'Bhubaneswar'),
    }
    return render(request, 'why-rentora.html', context)


def cars_view(request):
    """Car listing with filters, search, sort, and pagination."""
    cars = Car.objects.filter(is_available=True)

    # Date-based Availability Filter
    pickup_date_str = request.GET.get('pickup_date')
    return_date_str = request.GET.get('return_date')
    
    if pickup_date_str and return_date_str:
        try:
            p_dt = parse_datetime(pickup_date_str)
            r_dt = parse_datetime(return_date_str)

            if p_dt and r_dt:
                if timezone.is_naive(p_dt):
                    p_dt = timezone.make_aware(p_dt)
                if timezone.is_naive(r_dt):
                    r_dt = timezone.make_aware(r_dt)

                # Car overlap check:
                # Find bookings that cross into our requested range
                booked_car_ids = Booking.objects.filter(
                    status__in=[Booking.Status.PENDING, Booking.Status.CONFIRMED, 'Pending', 'Active', 'Confirmed'],
                    pickup_date__lt=r_dt,
                    dropoff_date__gt=p_dt
                ).values_list('car_id', flat=True)
                
                cars = cars.exclude(id__in=booked_car_ids)
        except Exception as e:
            logger.error(f"Availability Query Error: {e}")
            pass
    
    # Pre-optimize results & eliminate N+1 review queries
    cars = cars.annotate(
        annotated_rating=Avg('reviews__rating'),
        annotated_review_count=Count('reviews')
    ).prefetch_related('reviews')

    # Fleet filter
    fleet = request.GET.get('fleet', '')
    if fleet == 'premium':
        cars = cars.filter(Q(category__icontains='Luxury') | Q(price_per_day__gte=5000))
    elif fleet == 'standard':
        cars = cars.exclude(Q(category__icontains='Luxury') | Q(price_per_day__gte=5000))

    # Budget filter
    budget = request.GET.get('budget', '')
    if budget == 'under_1500':
        cars = cars.filter(price_per_day__lt=1500)
    elif budget == '1500_3000':
        cars = cars.filter(price_per_day__gte=1500, price_per_day__lte=3000)
    elif budget == '3000_8000':
        cars = cars.filter(price_per_day__gte=3000, price_per_day__lte=8000)
    elif budget == '8000_20000':
        cars = cars.filter(price_per_day__gte=8000, price_per_day__lte=20000)
    elif budget == 'above_20000':
        cars = cars.filter(price_per_day__gt=20000)

    # Numeric price range filter
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        try:
            cars = cars.filter(price_per_day__gte=Decimal(min_price))
        except Exception:
            pass
    if max_price:
        try:
            cars = cars.filter(price_per_day__lte=Decimal(max_price))
        except Exception:
            pass

    # Category filter
    category = request.GET.get('category', '')
    if category and category != 'All':
        if category == 'Luxury':
            cars = cars.filter(category__icontains='Luxury')
        elif category == 'Off-road':
            cars = cars.filter(category__icontains='Off-road')
        elif category == 'SUV':
            # Broaden SUV to include Compact SUV, Micro SUV, Premium SUV
            cars = cars.filter(category__icontains='SUV')
        else:
            cars = cars.filter(category__icontains=category)

    # Brand filter
    brand = request.GET.get('brand', '')
    if brand and brand != 'All':
        cars = cars.filter(brand=brand)

    # Search & Location Parsing
    location_query = request.GET.get('location', '').strip()
    q = request.GET.get('q', '').strip()

    # Detect if q is a location / neighborhood / city rather than a car model
    known_loc_terms = [
        'bhubaneswar', 'bbsr', 'cuttack', 'puri', 'rourkela', 'sambalpur', 'berhampur',
        'patia', 'khandagiri', 'saheed nagar', 'badambadi', 'marine drive', 'kiit', 'infocity',
        'aiims', 'master canteen', 'gopalpur', 'burla', 'panposh', 'cda', 'link road',
        'airport', 'bengaluru', 'bangalore', 'delhi', 'mumbai', 'hyderabad', 'chennai', 'pune'
    ]
    if q and any(term in q.lower() for term in known_loc_terms):
        if not location_query:
            location_query = q
        q = ''  # Clear car model search so we don't zero out cars for a location query!

    # Smart Search Detection: If location_query contains a vehicle model, brand, or category
    if location_query and not q:
        has_car_match = Car.objects.filter(
            Q(name__icontains=location_query) | 
            Q(brand__icontains=location_query) | 
            Q(category__icontains=location_query)
        ).exists()
        if has_car_match:
            q = location_query

    if location_query:
        for city in ['Bhubaneswar', 'Cuttack', 'Puri', 'Rourkela', 'Sambalpur', 'Berhampur', 'Bengaluru', 'Delhi NCR', 'Mumbai']:
            if city.lower() in location_query.lower() or (city == 'Bhubaneswar' and 'bbsr' in location_query.lower()):
                request.session['current_city'] = city
                break

    if q:
        cars = cars.filter(Q(name__icontains=q) | Q(brand__icontains=q) | Q(category__icontains=q))

    # Fuel type filter
    fuel = request.GET.get('fuel', '')
    if fuel and fuel != 'All':
        cars = cars.filter(fuel_type__icontains=fuel)

    # Seats filter
    seats = request.GET.get('seats', '')
    if seats == '4':
        cars = cars.filter(seats=4)
    elif seats == '5':
        cars = cars.filter(seats=5)
    elif seats == '6':
        cars = cars.filter(seats=6)
    elif seats == '7':
        cars = cars.filter(seats=7)
    elif seats == '8+':
        cars = cars.filter(seats__gte=8)

    # Transmission filter
    transmission = request.GET.get('transmission', '')
    if transmission and transmission != 'All':
        cars = cars.filter(transmission__icontains=transmission)

    # Tag / Quick Filter
    tag = request.GET.get('tag', '')
    if tag == 'guest_favorite':
        cars = cars.filter(Q(name__icontains='Swift') | Q(name__icontains='Thar') | Q(name__icontains='Baleno') | Q(name__icontains='Nexon'))
    elif tag == 'super_host':
        cars = cars.filter(Q(name__icontains='Scorpio') | Q(name__icontains='Innova') | Q(name__icontains='Punch'))
    elif tag == 'home_delivery':
        # Default all seeded cars have home delivery available
        pass
    elif tag == 'electric':
        cars = cars.filter(fuel_type__icontains='Electric')
    elif tag == 'suv':
        cars = cars.filter(category__icontains='SUV')
    elif tag == 'automatic':
        cars = cars.filter(transmission__icontains='Auto')

    # Sort
    sort = request.GET.get('sort', '')
    if sort == 'price_low':
        cars = cars.order_by('price_per_day')
    elif sort == 'price_high':
        cars = cars.order_by('-price_per_day')
    elif sort == 'rating':
        cars = cars.order_by(F('annotated_rating').desc(nulls_last=True))
    else:
        cars = cars.order_by('-created_at')

    # Total match count & Smart Fallback Recommendations logic
    total_match_count = cars.count()
    is_fallback = False
    fallback_reason = ""
    recommended_cars = []

    if total_match_count == 0:
        is_fallback = True
        base_pool = Car.objects.filter(is_available=True).annotate(
            annotated_rating=Avg('reviews__rating'),
            annotated_review_count=Count('reviews')
        ).prefetch_related('reviews')

        active_city = request.session.get('current_city', 'Bhubaneswar')

        # Fallback Strategy 1: Match category if specified
        if category and category != 'All':
            if 'SUV' in category:
                recommended_cars = list(base_pool.filter(Q(category__icontains='SUV') | Q(category__icontains='MPV'))[:6])
                fallback_reason = f"No exact matches for {category} with current filters in {active_city}. Here are verified SUVs & spacious vehicles available."
            elif category == 'Luxury':
                recommended_cars = list(base_pool.filter(Q(category__icontains='Sedan') | Q(price_per_day__gte=3500))[:6])
                fallback_reason = f"No luxury cars matched those exact criteria. Here are executive cars available in {active_city}."
            elif category == 'Hatchback':
                recommended_cars = list(base_pool.filter(Q(category__icontains='Hatchback') | Q(price_per_day__lte=2500))[:6])
                fallback_reason = f"No hatchbacks found with those options. Here are convenient city cars available in {active_city}."
            else:
                recommended_cars = list(base_pool.filter(category__icontains=category)[:6])
                fallback_reason = f"No exact {category} matches with active filters. Here are alternative cars ready for booking."

        # Fallback Strategy 2: Match Brand if specified
        elif brand and brand != 'All':
            recommended_cars = list(base_pool.filter(brand__in=['Mahindra', 'Tata', 'Maruti Suzuki', 'Hyundai']).order_by(F('annotated_rating').desc(nulls_last=True))[:6])
            fallback_reason = f"No {brand} vehicles currently match all filters in {active_city}. Here are reliable alternatives from top Indian automakers."

        # Fallback Strategy 3: Match Seating capacity
        elif seats:
            target_seats = int(seats) if seats.isdigit() else 5
            recommended_cars = list(base_pool.filter(seats__gte=target_seats).order_by('price_per_day')[:6])
            if not recommended_cars:
                recommended_cars = list(base_pool.order_by('-seats')[:6])
            fallback_reason = f"No {seats}-seater cars found matching all criteria. Here are our most spacious alternative vehicles."

        # Fallback Strategy 4: Match Fuel or Transmission
        elif fuel and fuel != 'All':
            recommended_cars = list(base_pool.filter(Q(fuel_type__icontains=fuel) | Q(fuel_type='Petrol')).order_by(F('annotated_rating').desc(nulls_last=True))[:6])
            fallback_reason = f"No {fuel} cars match your exact combination in {active_city}. Here are high-efficiency alternatives available right now."
        elif transmission and transmission != 'All':
            recommended_cars = list(base_pool.filter(transmission__icontains=transmission)[:6])
            fallback_reason = f"No {transmission} cars match all current filters. Here are other smooth {transmission} options."

        # Default Fallback: Top-rated popular cars in Odisha
        if not recommended_cars:
            recommended_cars = list(base_pool.order_by(F('annotated_rating').desc(nulls_last=True), '-created_at')[:6])
            fallback_reason = f"No cars matched your exact filter combination in {active_city}. Here are top-rated vehicles ready for instant booking."

    # Pagination: Paginate either the matched cars or the fallback recommended cars
    display_cars = recommended_cars if is_fallback else cars
    paginator = Paginator(display_cars, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Optimization: Pre-fetch wishlist for logged-in user to avoid N+1 in template
    wishlisted_car_ids = []
    if request.user.is_authenticated:
        wishlisted_car_ids = list(Wishlist.objects.filter(user=request.user).values_list('car_id', flat=True))

    categories = ['All', 'Hatchback', 'Sedan', 'Compact SUV', 'SUV', 'MPV', 'Electric', 'Luxury', 'Off-road', 'Ultra Luxury']
    brands = ['Maruti Suzuki', 'Tata', 'Hyundai', 'Mahindra', 'Kia', 'Toyota', 'Honda', 'Volkswagen', 'Skoda', 'MG', 'BMW', 'Mercedes-Benz', 'Audi']
    fuels = ['All', 'Petrol', 'Diesel', 'Electric', 'CNG', 'Hybrid']
    seat_options = ['4', '5', '6', '7', '8+']
    budget_options = [
        ('under_1500', 'Under ₹1,500/day'),
        ('1500_3000', '₹1,500 - ₹3,000'),
        ('3000_8000', '₹3,000 - ₹8,000'),
        ('8000_20000', '₹8,000 - ₹20,000'),
        ('above_20000', 'Above ₹20,000')
    ]

    context = {
        'page_obj': page_obj,
        'cars': page_obj,
        'total_match_count': total_match_count,
        'is_fallback': is_fallback,
        'fallback_reason': fallback_reason,
        'recommended_cars': recommended_cars,
        'wishlisted_car_ids': wishlisted_car_ids,
        'current_category': category,
        'current_brand': brand,
        'current_budget': budget,
        'current_fuel': fuel,
        'current_seats': seats,
        'current_transmission': transmission,
        'current_tag': tag,
        'current_sort': sort,
        'current_fleet': fleet,
        'search_query': q,
        'current_location': location_query or request.session.get('current_city', 'Bhubaneswar'),
        'categories': categories,
        'brands': brands,
        'fuels': fuels,
        'seat_options': seat_options,
        'budget_options': budget_options,
        'pickup_date': pickup_date_str,
        'return_date': return_date_str,
    }
    return render(request, 'cars.html', context)


def car_detail_view(request, car_id):
    """Car detail page with specs, reviews, and booking panel."""
    car = get_object_or_404(Car, id=car_id, is_available=True)
    reviews = Review.objects.filter(car=car).select_related('user').order_by('-created_at')

    # Check if user has wishlisted this car
    is_wishlisted = False
    if request.user.is_authenticated:
        is_wishlisted = Wishlist.objects.filter(user=request.user, car=car).exists()

    current_city = request.session.get('current_city', 'Bhubaneswar')

    context = {
        'car': car,
        'reviews': reviews,
        'is_wishlisted': is_wishlisted,
        'review_form': ReviewForm(),
        'current_city': current_city,
        'current_location': current_city,
    }
    return render(request, 'car-detail.html', context)




@login_required
def booking_location_direct(request, car_id):
    """Entry point for direct car booking from car-detail."""
    from django.shortcuts import get_object_or_404
    car = get_object_or_404(Car, id=car_id)
    request.session['booking_car_id'] = car.id
    return redirect('booking_location')

@login_required
def booking_location_view(request):
    """Booking Step 1: Unified Location and Date/Time selection."""
    preselect_car = request.GET.get('preselect_car') or request.POST.get('preselect_car')
    if preselect_car:
        request.session['booking_car_id'] = preselect_car

    car_id = request.session.get('booking_car_id')
    selected_car = None
    if car_id:
        try:
            selected_car = Car.objects.filter(id=car_id).first()
        except Exception:
            selected_car = None

    if request.method == 'POST':
        form = BookingStepOneForm(request.POST)
        if form.is_valid():
            request.session['pickup_location'] = form.cleaned_data['pickup_location']
            request.session['dropoff_location'] = form.cleaned_data['dropoff_location'] or form.cleaned_data['pickup_location']
            request.session['pickup_date'] = form.cleaned_data['pickup_date'].isoformat()
            request.session['dropoff_date'] = form.cleaned_data['dropoff_date'].isoformat()
            request.session['is_outstation'] = form.cleaned_data.get('is_outstation', False)

            # If user already selected a car (from homepage, fleet, or car-detail), go directly to checkout
            if request.session.get('booking_car_id'):
                return redirect('payment')
            return redirect('booking_select')
    else:
        # Default dates: today + 2 hours for pickup, pickup + 2 days for dropoff
        default_pickup = timezone.now() + timedelta(hours=2)
        default_pickup = default_pickup.replace(minute=0, second=0, microsecond=0)
        default_dropoff = default_pickup + timedelta(days=2)

        session_pickup = request.session.get('pickup_date')
        session_dropoff = request.session.get('dropoff_date')
        
        pickup_val = parse_session_date(session_pickup) if session_pickup else default_pickup
        dropoff_val = parse_session_date(session_dropoff) if session_dropoff else default_dropoff

        form = BookingStepOneForm(initial={
            'pickup_location': request.session.get('pickup_location') or request.session.get('current_city', 'Bhubaneswar'),
            'dropoff_location': request.session.get('dropoff_location', ''),
            'pickup_date': pickup_val.strftime('%Y-%m-%d %H:%M') if pickup_val else '',
            'dropoff_date': dropoff_val.strftime('%Y-%m-%d %H:%M') if dropoff_val else '',
            'is_outstation': request.session.get('is_outstation', False),
        })

    has_car = bool(selected_car)
    context = {
        'form': form,
        'step': 1,
        'total_steps': 2 if has_car else 3,
        'selected_car': selected_car,
        'has_car': has_car,
        'car_id': selected_car.id if selected_car else None,
        'car': selected_car,
    }
    return render(request, 'booking-flow.html', context)


@login_required
def booking_dates_view(request):
    """Booking dates route: forwards to combined booking step 1."""
    if not request.session.get('pickup_location'):
        return redirect('booking_location')
    return booking_location_view(request)


@login_required
def booking_select_view(request):
    """Booking Step 2 (if car not chosen upfront): Select a Car."""
    if request.session.get('booking_car_id'):
        return redirect('payment')

    if not request.session.get('pickup_date') or not request.session.get('pickup_location'):
        messages.warning(request, "Please set your trip location and dates first.")
        return redirect('booking_location')

    pickup_date_str = request.session['pickup_date']
    dropoff_date_str = request.session['dropoff_date']
    
    pickup_dt = parse_session_date(pickup_date_str)
    dropoff_dt = parse_session_date(dropoff_date_str)
    if not pickup_dt or not dropoff_dt:
        pickup_dt = timezone.now() + timedelta(hours=2)
        dropoff_dt = pickup_dt + timedelta(days=2)

    # Exclude cars with confirmed or paid bookings for the selected dates
    booked_car_ids = Booking.objects.filter(
        models.Q(status__in=[Booking.Status.CONFIRMED, 'Confirmed', 'Active']) |
        models.Q(is_paid=True),
        pickup_date__lt=dropoff_dt,
        dropoff_date__gt=pickup_dt
    ).values_list('car_id', flat=True)

    available_cars = Car.objects.filter(is_available=True).exclude(id__in=booked_car_ids)

    if request.method == 'POST':
        car_id = request.POST.get('car_id')
        is_outstation = request.POST.get('is_outstation') == 'on'
        if car_id:
            car = get_object_or_404(Car, id=car_id)
            request.session['booking_car_id'] = car_id
            request.session['is_outstation'] = is_outstation
            return redirect('payment')

    days = max(1, (dropoff_dt - pickup_dt).days)

    context = {
        'cars': available_cars,
        'step': 2,
        'total_steps': 3,
        'pickup_date': pickup_dt,
        'dropoff_date': dropoff_dt,
        'days': days,
        'selected_car_id': request.session.get('booking_car_id'),
        'is_outstation': request.session.get('is_outstation', False),
    }
    return render(request, 'booking-flow.html', context)


@login_required
def payment_view(request):
    """Booking Step 2: Checkout & Payment review page."""
    car_id = request.session.get('booking_car_id')
    pickup_date_str = request.session.get('pickup_date')
    dropoff_date_str = request.session.get('dropoff_date')
    pickup_location = request.session.get('pickup_location')
    dropoff_location = request.session.get('dropoff_location') or pickup_location
    is_outstation = request.session.get('is_outstation', False)

    if not car_id:
        messages.info(request, "Please choose a vehicle for your reservation.")
        return redirect('cars')

    if not all([pickup_date_str, dropoff_date_str, pickup_location]):
        messages.warning(request, "Please select your trip location and schedule.")
        return redirect('booking_location')

    car = get_object_or_404(Car, id=car_id)
    
    pickup_dt = parse_session_date(pickup_date_str)
    dropoff_dt = parse_session_date(dropoff_date_str)
    
    if not pickup_dt or not dropoff_dt:
        messages.warning(request, "Invalid date format. Please verify your itinerary dates.")
        return redirect('booking_location')
    
    days = (dropoff_dt - pickup_dt).days
    if days <= 0:
        days = 1
    
    subtotal = car.calculate_rental_price(pickup_dt, dropoff_dt)
    tax = (subtotal * Decimal('0.18')).quantize(Decimal('0.01'))
    total = subtotal + tax
    
    promo_id = request.session.get('applied_promo_id')
    discount_amount = Decimal('0')
    promo_code_str = ""
    
    if promo_id:
        try:
            promo = PromoCode.objects.get(id=promo_id, is_active=True)
            if promo.is_valid():
                promo_code_str = promo.code
                if promo.discount_type == 'Percentage':
                    discount_amount = subtotal * Decimal(str(promo.discount_value)) / Decimal('100')
                else:
                    discount_amount = Decimal(str(promo.discount_value))
            else:
                del request.session['applied_promo_id']
        except PromoCode.DoesNotExist:
            del request.session['applied_promo_id']
        
    final_total = max(Decimal('0.00'), total - discount_amount)

    context = {
        'car': car,
        'pickup_date': pickup_dt,
        'dropoff_date': dropoff_dt,
        'pickup_location': pickup_location,
        'dropoff_location': dropoff_location,
        'days': days,
        'subtotal': subtotal,
        'tax': tax,
        'total': total,
        'discount_amount': discount_amount,
        'final_total': final_total,
        'is_outstation': is_outstation,
        'step': 2,
        'total_steps': 2,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
    }

    if request.method == 'POST':
        try:
            with transaction.atomic():
                locked_car = Car.objects.select_for_update().get(id=car.id)
                
                is_available = Car.is_available_for_dates(
                    locked_car.id, pickup_dt, dropoff_dt, exclude_user_id=request.user.id
                )
                if not is_available:
                    messages.error(request, "Sorry, this vehicle is no longer available for the selected dates.")
                    return redirect('booking_location')

                # Reuse existing unpaid pending booking if present to avoid duplicate row creation
                existing_pending = Booking.objects.filter(
                    user=request.user,
                    car=locked_car,
                    status=Booking.Status.PENDING,
                    is_paid=False
                ).order_by('-id').first()

                if existing_pending:
                    booking = existing_pending
                    booking.pickup_location = pickup_location
                    booking.dropoff_location = dropoff_location
                    booking.pickup_date = pickup_dt
                    booking.dropoff_date = dropoff_dt
                    booking.total_price = final_total
                    booking.is_outstation = is_outstation
                    booking.promo_code = promo_code_str
                    booking.discount_amount = discount_amount
                    booking.save()
                else:
                    booking = Booking.objects.create(
                        user=request.user,
                        car=locked_car,
                        pickup_location=pickup_location,
                        dropoff_location=dropoff_location,
                        pickup_date=pickup_dt,
                        dropoff_date=dropoff_dt,
                        total_price=final_total,
                        status=Booking.Status.PENDING,
                        is_outstation=is_outstation,
                        promo_code=promo_code_str,
                        discount_amount=discount_amount,
                        is_paid=False
                    )
                
                if promo_id:
                    PromoCode.objects.filter(id=promo_id, used_count__lt=F('usage_limit')).update(used_count=F('used_count') + 1)

            payment_method = request.POST.get('payment_method_choice', 'razorpay')
            
            if payment_method == 'razorpay':
                razorpay_order = BookingService.create_razorpay_order(booking, final_total)
                booking.razorpay_order_id = razorpay_order['id']
                booking.payment_intent_id = razorpay_order['id']
                booking.save()
                
                context['trigger_razorpay'] = True
                context['razorpay_order_id'] = razorpay_order['id']
                context['razorpay_amount'] = final_total
                context['razorpay_amount_paise'] = int(round(final_total * 100))
                context['razorpay_key_id'] = settings.RAZORPAY_KEY_ID
                context['booking'] = booking
                return render(request, 'payment.html', context)
            else:
                try:
                    checkout_session = BookingService.create_stripe_session(
                        booking, car, days, pickup_dt, dropoff_dt, final_total
                    )
                    booking.stripe_session_id = checkout_session.id
                    booking.save()
                    return redirect(checkout_session.url, code=303)
                except Exception as stripe_err:
                    logger.error(f"Stripe Session Error: {stripe_err}")
                    messages.error(request, f"Card gateway unavailable: {str(stripe_err)}. You can also pay via UPI / Netbanking.")
                    context['booking'] = booking
                    return render(request, 'payment.html', context)

        except Exception as e:
            if 'booking' in locals():
                booking.status = 'Cancelled'
                booking.save()
            error_msg = f"Payment Gateway Error: {str(e)}" if settings.DEBUG else "We encountered an issue preparing checkout. Please try again."
            logger.error(f"Payment Checkout Error: {e}")
            messages.error(request, error_msg)
            return render(request, 'payment.html', context)

    return render(request, 'payment.html', context)


@csrf_exempt
def razorpay_callback(request):
    """Webhook callback for Razorpay UI Checkout"""
    if request.method == "POST":
        payment_id = request.POST.get('razorpay_payment_id', '')
        order_id = request.POST.get('razorpay_order_id', '')
        signature = request.POST.get('razorpay_signature', '')
        
        try:
            booking = Booking.objects.get(payment_intent_id=order_id)
            
            # Security: Verify ownership since this is a user-redirect callback
            if request.user.is_authenticated and booking.user != request.user:
                messages.error(request, "Permission denied.")
                return redirect('index')
                
            success = BookingService.process_razorpay_success(booking, payment_id, order_id, signature)
            if success:
                BookingService.clear_booking_session(request)
                return redirect('confirmation', booking_id=booking.id)
            else:
                messages.error(request, "Payment verification failed.")
                return redirect('payment')
        except Booking.DoesNotExist:
            messages.error(request, "Booking not found.")
            return redirect('booking_select')
    
    from django.http import HttpResponseBadRequest
    return HttpResponseBadRequest()


@login_required
def confirmation_view(request, booking_id):
    """Booking confirmation page."""
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    # Check session_id from Stripe redirection
    session_id = request.GET.get('session_id')
    
    # Verify and process payment via Service Layer
    if session_id and not booking.is_paid:
        try:
            if BookingService.process_successful_payment(booking, session_id):
                send_booking_email(booking)
                # Auto-create notifications
                create_notification(
                    booking.user, 'booking', 'Booking Confirmed',
                    f'Your rental for the {booking.car.brand} {booking.car.name} has been confirmed. Pick-up instructions are now available in your trip details.',
                    f'/dashboard/'
                )
                create_notification(
                    booking.user, 'payment', 'Payment Received',
                    f'We\'ve successfully processed your payment for your upcoming trip. Your invoice is ready for download.',
                    f'/booking/invoice/{booking.id}/'
                )
                try:
                    from .utils_india import send_whatsapp_confirmation
                    send_whatsapp_confirmation(booking)
                except Exception as e:
                    logger.error(f"WhatsApp Error: {e}")
                
                messages.success(request, f"Payment successful! Booking confirmed! Reference: {booking.booking_reference}")
            else:
                messages.error(request, "Could not verify payment status.")
        except Exception as e:
            logger.error(f"Payment verification failed: {str(e)}")
            messages.error(request, "An error occurred during payment verification.")

    context = {
        'booking': booking,
    }
    return render(request, 'confirmation.html', context)


@login_required
def booking_detail_view(request, booking_id):
    """Detailed view for an individual booking."""
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    can_cancel = booking.status.upper() in ['PENDING', 'CONFIRMED']
    total = booking.total_with_gst or booking.total_price or Decimal('0.00')
    gst = booking.gst_amount or (total * Decimal('0.18') / Decimal('1.18')).quantize(Decimal('0.01'))
    base_fare = (total - gst).quantize(Decimal('0.01'))
    protection_fee = Decimal('0.00')

    booking.base_fare = base_fare
    booking.protection_fee = protection_fee
    booking.taxes = gst
    booking.total_price = total
    booking.can_cancel = can_cancel
    booking.can_extend = False

    context = {
        'booking': booking,
        'can_cancel': can_cancel,
        'base_fare': base_fare,
        'protection_fee': protection_fee,
        'taxes': gst,
        'total_price': total,
        'refund_message': f"Full refund of ₹{total} will be credited to original payment method in 3-5 business days." if can_cancel else None,
    }
    return render(request, 'booking_detail.html', context)


@login_required
@require_POST
def cancel_booking_view(request, booking_id):
    """Cancel booking endpoint."""
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    if booking.status.upper() in ['PENDING', 'CONFIRMED']:
        booking.status = Booking.Status.CANCELLED
        booking.save()
        create_notification(
            booking.user,
            'booking',
            'Booking Cancelled',
            f'Your booking {booking.booking_reference} has been cancelled.',
            '/accounts/dashboard/bookings/'
        )
        messages.success(request, f"Trip {booking.booking_reference} has been cancelled successfully.")
    else:
        messages.warning(request, "This booking cannot be cancelled.")
    return redirect('dashboard_bookings')


@login_required
def invoice_view(request, booking_id):
    """Render a printable premium GST invoice."""
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    if not booking.is_paid:
        messages.error(request, "Invoice is only available for paid bookings.")
        return redirect('confirmation', booking_id=booking.id)
    
    return render(request, 'invoice.html', {'booking': booking})


@login_required
def download_receipt_view(request, booking_id):
    """Generate a simple text receipt for download."""
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    if not booking.is_paid:
        messages.error(request, "Receipt is only available for paid bookings.")
        return redirect('confirmation', booking_id=booking.id)
    
    content = f"""
    RENTORA - YOUR JOURNEY, YOUR WAY
    --------------------------------
    RECEIPT FOR BOOKING: {booking.booking_reference}
    
    Customer: {booking.user.get_full_name() or booking.user.username}
    Vehicle: {booking.car.brand} {booking.car.name}
    
    Pickup: {booking.pickup_location} ({booking.pickup_date})
    Drop-off: {booking.dropoff_location} ({booking.dropoff_date})
    Outstation: {'Yes' if booking.is_outstation else 'No'}
    
    Subtotal: ₹{booking.total_price}
    GST (18%): ₹{booking.gst_amount}
    Total Paid: ₹{booking.total_with_gst}
    Status: PAID
    
    Thank you for choosing Rentora!
    """

    
    response = HttpResponse(content, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="receipt_{booking.booking_reference}.txt"'
    return response


@csrf_exempt
def stripe_webhook(request):
    """Webhook to listen for Stripe events (like payment_intent.succeeded)."""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)

    # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        # Fulfill the purchase...
        booking_id = session.get('client_reference_id')
        if booking_id:
            try:
                booking = Booking.objects.get(id=booking_id)
                booking.is_paid = True
                booking.status = Booking.Status.CONFIRMED
                booking.save()
                send_booking_email(booking)
                # Auto-create notifications
                create_notification(
                    booking.user, 'booking', 'Booking Confirmed',
                    f'Your rental for the {booking.car.brand} {booking.car.name} has been confirmed.',
                    f'/booking/confirmation/{booking.id}/'
                )
                create_notification(
                    booking.user, 'payment', 'Payment Received',
                    f'We\'ve successfully processed your payment of ₹{booking.total_with_gst:,.0f}.',
                    f'/booking/invoice/{booking.id}/'
                )
                try:
                    from .utils_india import send_whatsapp_confirmation
                    send_whatsapp_confirmation(booking)
                except Exception as e:
                    logger.error(f"WhatsApp Error: {e}")
            except Booking.DoesNotExist:

                pass

    return JsonResponse({'status': 'success'}, status=200)


def contact_view(request):
    """Handle contact form submission with email delivery."""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            email = form.cleaned_data['email']
            message = form.cleaned_data['message']
            
            subject = f"New Contact Query from {first_name} {last_name}"
            email_body = f"""
            New inquiry received on Rentora:
            
            Name: {first_name} {last_name}
            Email: {email}
            
            Message:
            {message}
            
            --
            Rentora Contact System
            """
            
            try:
                send_mail(
                    subject,
                    email_body,
                    settings.DEFAULT_FROM_EMAIL,
                    [settings.DEFAULT_FROM_EMAIL], # Send to admin
                    fail_silently=False,
                )
                messages.success(request, "Thank you for your message! We'll get back to you soon.")
            except Exception as e:
                logger.error(f"Contact form email error: {e}")
                messages.warning(request, "Message sent, but we had trouble notifying the team. We'll still check it!")
                
            return redirect('contact')
    return render(request, 'contact.html')


@login_required
@require_POST
def add_review_view(request, car_id):
    """Add review for a completed booking."""
    car = get_object_or_404(Car, id=car_id)
    booking_id = request.POST.get('booking_id')
    booking = get_object_or_404(Booking, id=booking_id, user=request.user, car=car, status__in=[Booking.Status.COMPLETED, 'Completed', 'COMPLETED'])

    # Check if review already exists
    if Review.objects.filter(booking=booking).exists():
        messages.warning(request, "You've already reviewed this booking.")
        return redirect('car_detail', car_id=car_id)

    form = ReviewForm(request.POST)
    if form.is_valid():
        review = form.save(commit=False)
        review.user = request.user
        review.car = car
        review.booking = booking
        review.save()

        # Update car average rating
        # The car's rating property will now dynamically calculate the average.
        # No need to explicitly update and save the car object here for rating.

        messages.success(request, "Review submitted successfully!")
    else:
        messages.error(request, "Please fix the errors in your review.")

    return redirect('car_detail', car_id=car_id)


# ===================== API Endpoints =====================

def api_cars_search(request):
    """Search cars via JSON API."""
    q = request.GET.get('q', '')
    brand = request.GET.get('brand', '')
    category = request.GET.get('category', '')
    fuel = request.GET.get('fuel', '')
    cars = Car.objects.filter(is_available=True)
    if q:
        cars = cars.filter(Q(name__icontains=q) | Q(brand__icontains=q))
    if brand:
        cars = cars.filter(brand__iexact=brand)
    if category:
        cars = cars.filter(category__iexact=category)
    if fuel:
        cars = cars.filter(fuel_type__iexact=fuel)

    data = [{
        'id': car.id,
        'name': f"{car.brand} {car.name}",
        'brand': car.brand,
        'category': car.category,
        'price_per_day': str(car.price_per_day),
        'seats': car.seats,
        'fuel_type': car.fuel_type,
        'transmission': car.transmission,
        'rating': str(car.rating),
        'image': car.image.url if car.image else '',
    } for car in cars[:20]]

    return JsonResponse({'cars': data})


def api_check_availability(request):
    """Check car availability for given dates."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    car_id = request.POST.get('car_id')
    pickup_date = request.POST.get('pickup_date')
    dropoff_date = request.POST.get('dropoff_date')

    if not car_id or not pickup_date or not dropoff_date:
        return JsonResponse({'error': 'Missing required fields: car_id, pickup_date, and dropoff_date are required.'}, status=400)

    try:
        car = Car.objects.get(id=car_id, is_available=True)
        # Precision check: handle both 'Y-m-d' and 'Y-m-d H:M'
        if ' ' in pickup_date:
            pickup = timezone.make_aware(datetime.strptime(pickup_date, '%Y-%m-%d %H:%M'))
            dropoff = timezone.make_aware(datetime.strptime(dropoff_date, '%Y-%m-%d %H:%M'))
        else:
            pickup = timezone.make_aware(datetime.strptime(pickup_date, '%Y-%m-%d'))
            dropoff = timezone.make_aware(datetime.strptime(dropoff_date, '%Y-%m-%d'))

        existing = Booking.objects.filter(
            car=car,
            status__in=[Booking.Status.PENDING, Booking.Status.CONFIRMED, 'Pending', 'Active', 'Confirmed'],
            pickup_date__lt=dropoff,
            dropoff_date__gt=pickup
        ).exists()

        return JsonResponse({
            'available': not existing,
            'car_name': str(car),
            'price_per_day': str(car.price_per_day),
        })
    except Car.DoesNotExist:
        return JsonResponse({'available': False, 'error': 'Car not found'})


@require_POST
def api_apply_promo(request):
    """Apply promo code and return discount info."""
    code_str = request.POST.get('code', '').upper().strip()
    cart_total = request.POST.get('cart_total', 0)
    
    try:
        promo = PromoCode.objects.get(code=code_str, is_active=True)
        if not promo.is_valid(cart_total=cart_total):
            if float(cart_total) < float(promo.min_purchase):
                return JsonResponse({
                    'valid': False, 
                    'message': f'Minimum purchase of ₹{promo.min_purchase} required for this code.'
                })
            return JsonResponse({'valid': False, 'message': 'Promo code expired or fully used'})
            
        # Store in session for checkout
        request.session['applied_promo_id'] = promo.id
        request.session['discount_type'] = promo.discount_type
        request.session['discount_value'] = float(promo.discount_value)
        
        msg = f"{promo.discount_value}% discount applied!" if promo.discount_type == 'Percentage' else f"₹{promo.discount_value} discount applied!"
        
        return JsonResponse({
            'valid': True,
            'discount': float(promo.discount_value),
            'type': promo.discount_type,
            'message': msg,
        })
    except PromoCode.DoesNotExist:
        return JsonResponse({
            'valid': False,
            'message': 'Invalid promo code',
        })



@login_required
@require_POST
def api_wishlist_toggle(request, car_id):
    """Toggle wishlist for a car."""
    car = get_object_or_404(Car, id=car_id)
    wishlist, created = Wishlist.objects.get_or_create(user=request.user, car=car)

    if not created:
        wishlist.delete()
        return JsonResponse({'wishlisted': False, 'message': 'Removed from wishlist'})

    return JsonResponse({'wishlisted': True, 'message': 'Added to wishlist'})


# ===================== Notification Views =====================

@login_required
def notifications_view(request):
    """Notification center page."""
    notifications = Notification.objects.filter(user=request.user)
    unread_count = notifications.filter(is_read=False).count()
    return render(request, 'notifications.html', {
        'notifications': notifications,
        'unread_count': unread_count,
    })


@login_required
@require_POST
def api_mark_notification_read(request, notification_id):
    """Mark a single notification as read."""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return JsonResponse({'success': True})


@login_required
@require_POST
def api_mark_all_notifications_read(request):
    """Mark all notifications as read."""
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'success': True})


def api_notification_count(request):
    """Return unread notification count for navbar bell."""
    if not request.user.is_authenticated:
        return JsonResponse({'count': 0})
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'count': count})


# ===================== Onboarding Views =====================

@login_required
def onboarding_view(request):
    """Driving Licence KYC onboarding view."""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        license_number = request.POST.get('license_number', '').strip().upper()
        license_front = request.FILES.get('license_front')

        if license_number:
            profile.license_number = license_number
        if license_front:
            profile.license_image = license_front
        profile.save()
        messages.success(request, "Driving licence submitted successfully! Verification in progress.")
        return redirect('onboarding')

    kyc_status = 'upload'
    if profile.is_verified:
        kyc_status = 'verified'
    elif profile.license_number and profile.license_image:
        kyc_status = 'pending'

    context = {
        'profile': profile,
        'kyc_status': kyc_status,
    }
    return render(request, 'onboarding.html', context)


def skip_onboarding(request):
    """Mark onboarding as done and redirect."""
    request.session['onboarding_done'] = True
    return redirect('index')


# ===================== Notification Helper =====================

def create_notification(user, notification_type, title, message, action_url=''):
    """Helper to create a notification for a user."""
    Notification.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        message=message,
        action_url=action_url,
    )

def robots_txt(request):
    lines = [
        "User-agent: *",
        "Disallow: /admin/",
        "Disallow: /dashboard/",
        "Allow: /",
        f"Sitemap: {request.scheme}://{request.get_host()}/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


def sitemap_xml(request):
    host = f"{request.scheme}://{request.get_host()}"
    urls = [
        {'loc': host, 'changefreq': 'daily', 'priority': '1.0'},
        {'loc': f"{host}/cars/", 'changefreq': 'daily', 'priority': '0.9'},
        {'loc': f"{host}/fleet/premium/", 'changefreq': 'weekly', 'priority': '0.8'},
    ]
    
    # Add all available cars
    for car in Car.objects.filter(is_available=True):
        urls.append({
            'loc': f"{host}/car/{car.id}/",
            'changefreq': 'weekly',
            'priority': '0.7',
            'lastmod': car.created_at.strftime('%Y-%m-%d')
        })
        
    xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for url in urls:
        xml.append('  <url>')
        xml.append(f"    <loc>{url['loc']}</loc>")
        xml.append(f"    <changefreq>{url['changefreq']}</changefreq>")
        xml.append(f"    <priority>{url['priority']}</priority>")
        if 'lastmod' in url:
            xml.append(f"    <lastmod>{url['lastmod']}</lastmod>")
        xml.append('  </url>')
    xml.append('</urlset>')
    
    return HttpResponse("\n".join(xml), content_type="application/xml")

def get_booked_dates(request, car_id):
    """
    API endpoint that returns an array of ISO dates that are already booked.
    Used by Flatpickr to disable unavailable dates.
    """
    from .models import Booking
    from datetime import timedelta
    from django.http import JsonResponse
    
    bookings = Booking.objects.filter(
        car_id=car_id,
        status__in=[Booking.Status.PENDING, Booking.Status.CONFIRMED]
    )
    
    booked_dates = []
    for booking in bookings:
        current_date = booking.pickup_date
        while current_date <= booking.dropoff_date:
            booked_dates.append(current_date.isoformat())
            current_date += timedelta(days=1)
            
    return JsonResponse({'booked_dates': list(set(booked_dates))})

@require_POST
def set_city_view(request):
    """
    Saves selected Odisha city/hub and optional pickup address to session and returns JSON response.
    Defaults to Bhubaneswar (BBSR).
    """
    city = 'Bhubaneswar'
    pickup_location = ''
    valid_cities = ['Bhubaneswar', 'Cuttack', 'Puri', 'Rourkela', 'Sambalpur', 'Berhampur']
    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body.decode('utf-8'))
            candidate = data.get('city', 'Bhubaneswar').strip()
            pickup_location = data.get('pickup_location', data.get('address', '')).strip()
        else:
            candidate = request.POST.get('city', 'Bhubaneswar').strip()
            pickup_location = request.POST.get('pickup_location', request.POST.get('address', '')).strip()
        
        # Match case-insensitively or BBSR alias
        if candidate.lower() in ['bbsr', 'bhubaneshwar']:
            city = 'Bhubaneswar'
        else:
            matched = next((c for c in valid_cities if c.lower() == candidate.lower()), None)
            city = matched if matched else candidate or 'Bhubaneswar'
    except Exception:
        pass
        
    request.session['current_city'] = city
    if pickup_location:
        request.session['pickup_location'] = pickup_location
    if hasattr(request.session, 'modified'):
        request.session.modified = True
    return JsonResponse({'status': 'success', 'city': city, 'pickup_location': pickup_location})

def terms_view(request):
    """Terms of Service static view."""
    return render(request, 'legal/terms.html', {'title': 'Terms of Service - Rentora'})

def privacy_view(request):
    """Privacy Policy static view."""
    return render(request, 'legal/privacy.html', {'title': 'Privacy Policy - Rentora'})

def health_check_view(request):
    """
    Lightweight health check endpoint for monitoring, load balancers,
    and keep-alive pings (prevents Render instance from sleeping).
    """
    return JsonResponse({
        'status': 'healthy',
        'service': 'rentora',
        'timestamp': timezone.now().isoformat(),
    })


# ===================== ADVANCED INDIAN MOBILITY API ENDPOINTS =====================

@login_required
@require_POST
def api_trip_inspection(request, booking_id):
    """
    Submit digital pre-trip or post-trip vehicle checklist with 4-side exterior photos,
    odometer reading, and fuel percentage. Prevents damage disputes.
    """
    booking = get_object_or_404(Booking, id=booking_id)
    if booking.user != request.user and not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    stage = request.POST.get('stage', 'PRE_TRIP').upper()
    try:
        odometer = int(request.POST.get('odometer', 0))
        fuel_percent = int(request.POST.get('fuel_percent', 100))
    except (ValueError, TypeError):
        return JsonResponse({'success': False, 'error': 'Invalid odometer or fuel percent values'}, status=400)

    damage_notes = request.POST.get('damage_notes', '').strip()
    lat = request.POST.get('latitude')
    lng = request.POST.get('longitude')
    
    photo_front = request.FILES.get('photo_front')
    photo_rear = request.FILES.get('photo_rear')
    photo_left = request.FILES.get('photo_left')
    photo_right = request.FILES.get('photo_right')

    if stage == 'PRE_TRIP':
        inspection = VehicleInspectionService.submit_pre_trip(
            booking=booking,
            user=request.user,
            odometer=odometer,
            fuel_percent=fuel_percent,
            photo_front=photo_front,
            photo_rear=photo_rear,
            photo_left=photo_left,
            photo_right=photo_right,
            damage_notes=damage_notes,
            lat=lat,
            lng=lng
        )
        return JsonResponse({
            'success': True,
            'stage': 'PRE_TRIP',
            'booking_status': booking.status,
            'message': 'Pre-trip inspection logged. Vehicle unlocked. Have a safe drive!'
        })
    elif stage == 'POST_TRIP':
        has_damage = request.POST.get('has_damage', 'false').lower() in ('true', '1', 'yes')
        cleanliness = int(request.POST.get('cleanliness', 5))
        inspection = VehicleInspectionService.submit_post_trip(
            booking=booking,
            user=request.user,
            odometer=odometer,
            fuel_percent=fuel_percent,
            has_damage=has_damage,
            damage_notes=damage_notes,
            cleanliness_rating=cleanliness,
            photo_front=photo_front,
            photo_rear=photo_rear,
            photo_left=photo_left,
            photo_right=photo_right,
            lat=lat,
            lng=lng
        )
        return JsonResponse({
            'success': True,
            'stage': 'POST_TRIP',
            'booking_status': booking.status,
            'has_damage': has_damage,
            'message': 'Drop-off inspection approved. Trip completed!'
        })
    else:
        return JsonResponse({'success': False, 'error': 'Invalid inspection stage'}, status=400)


@login_required
def api_trip_extend(request, booking_id):
    """
    Check extension availability and price, or confirm trip extension directly from phone.
    """
    booking = get_object_or_404(Booking, id=booking_id)
    if booking.user != request.user and not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    if request.method == 'GET':
        hours = int(request.GET.get('hours', 2))
        is_avail, new_dropoff, cost = TripExtensionService.check_availability(booking, hours)
        return JsonResponse({
            'available': is_avail,
            'requested_hours': hours,
            'new_dropoff': new_dropoff.strftime('%d %b %Y, %I:%M %p'),
            'cost': float(cost),
            'wallet_balance': float(request.user.profile.wallet_balance) if hasattr(request.user, 'profile') else 0.0
        })

    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8')) if request.content_type == 'application/json' else request.POST
            hours = int(data.get('hours', 2))
            channel = data.get('channel', 'wallet')
            success, msg = TripExtensionService.confirm_extension(booking, hours, payment_channel=channel)
            return JsonResponse({'success': success, 'message': msg})
        except Exception as e:
            logger.error(f"Trip extension error for Booking #{booking_id}: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_POST
def api_trip_sos(request, booking_id):
    """
    Trigger emergency SOS for highway breakdowns, punctures, or accidents.
    Automatically pauses billing meter and logs GPS coordinates.
    """
    booking = get_object_or_404(Booking, id=booking_id)
    if booking.user != request.user and not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    try:
        data = json.loads(request.body.decode('utf-8')) if request.content_type == 'application/json' else request.POST
        issue_type = data.get('issue_type', 'OTHER')
        lat = Decimal(str(data.get('latitude', 12.9716)))
        lng = Decimal(str(data.get('longitude', 77.5946)))
        address = data.get('location_address', 'Highway breakdown point')
        note = data.get('note', '')

        sos = EmergencySOSService.trigger_sos(
            booking=booking,
            user=request.user,
            issue_type=issue_type,
            latitude=lat,
            longitude=lng,
            location_address=address,
            user_note=note
        )
        return JsonResponse({
            'success': True,
            'sos_id': sos.id,
            'issue_type': sos.get_issue_type_display(),
            'message': 'Roadside assistance dispatched. Billing timer paused from this moment.'
        })
    except Exception as e:
        logger.error(f"Emergency SOS error: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_POST
def api_toll_dispute(request, booking_id):
    """
    Submit cash toll slip photo when FASTag scanner failed, preventing double deductions.
    """
    booking = get_object_or_404(Booking, id=booking_id)
    if booking.user != request.user and not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    cash_amount = request.POST.get('cash_amount')
    receipt_img = request.FILES.get('receipt_image')
    notes = request.POST.get('notes', '')

    if not cash_amount or not receipt_img:
        return JsonResponse({'success': False, 'error': 'Toll amount and receipt image are required'}, status=400)

    try:
        dispute, msg = TollReconcilerService.submit_cash_toll_dispute(
            booking=booking,
            user=request.user,
            cash_receipt_img=receipt_img,
            cash_amount=cash_amount,
            user_notes=notes
        )
        return JsonResponse({
            'success': True,
            'dispute_id': dispute.id,
            'status': dispute.status,
            'message': msg
        })
    except Exception as e:
        logger.error(f"Toll dispute error: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_POST
def api_cancel_booking_sla(request, booking_id):
    """
    Cancel booking with tiered Indian rental SLA matrix:
    >24h: 100% refund, 6-24h: 50% refund, <6h: 1-day rental retained.
    """
    booking = get_object_or_404(Booking, id=booking_id)
    if booking.user != request.user and not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    reason = request.POST.get('reason', 'Customer initiated cancellation')
    refund_tx, sla_note = RefundService.process_cancellation_with_sla(booking, reason=reason)
    
    return JsonResponse({
        'success': True,
        'booking_status': booking.status,
        'refund_amount': float(refund_tx.amount) if refund_tx else 0.0,
        'channel': refund_tx.get_channel_display() if refund_tx else 'N/A',
        'sla_note': sla_note
    })

