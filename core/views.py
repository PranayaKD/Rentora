import logging
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db import transaction, models
from django.db.models import Q, Avg, F
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
from .forms import BookingLocationForm, BookingDatesForm, ReviewForm, ContactForm
from core.services import BookingService


def parse_session_date(date_str):
    """Robustly parse dates stored in session (ISO, 'Y-m-d H:M', or 'Y-m-d')."""
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
    }
    return render(request, 'index.html', context)


def how_it_works_view(request):
    """How it works information page."""
    return render(request, 'how-it-works.html')


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
                    status__in=['Pending', 'Active'],
                    pickup_date__lt=r_dt,
                    dropoff_date__gt=p_dt
                ).values_list('car_id', flat=True)
                
                cars = cars.exclude(id__in=booked_car_ids)
        except Exception as e:
            logger.error(f"Availability Query Error: {e}")
            pass
    
    # Pre-optimize results
    cars = cars.prefetch_related('reviews')

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

    # Search
    q = request.GET.get('q', '')
    if q:
        cars = cars.filter(Q(name__icontains=q) | Q(brand__icontains=q))

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

    # Sort
    sort = request.GET.get('sort', '')
    if sort == 'price_low':
        cars = cars.order_by('price_per_day')
    elif sort == 'price_high':
        cars = cars.order_by('-price_per_day')
    elif sort == 'rating':
        cars = cars.order_by('-rating')
    else:
        cars = cars.order_by('-created_at')

    # Pagination
    paginator = Paginator(cars, 9)
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
        'wishlisted_car_ids': wishlisted_car_ids,
        'current_category': category,
        'current_brand': brand,
        'current_budget': budget,
        'current_fuel': fuel,
        'current_seats': seats,
        'current_sort': sort,
        'current_fleet': fleet,
        'search_query': q,
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

    context = {
        'car': car,
        'reviews': reviews,
        'is_wishlisted': is_wishlisted,
        'review_form': ReviewForm(),
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
    """Booking Step 1: Location selection."""
    # Pre-select car if provided from GET/POST parameter (legacy support)
    preselect_car = request.GET.get('preselect_car') or request.POST.get('preselect_car')
    if preselect_car:
        request.session['booking_car_id'] = preselect_car

    if request.method == 'POST':
        form = BookingLocationForm(request.POST)
        if form.is_valid():
            request.session['pickup_location'] = form.cleaned_data['pickup_location']
            request.session['dropoff_location'] = form.cleaned_data['dropoff_location']
            return redirect('booking_dates')
    else:
        form = BookingLocationForm(initial={
            'pickup_location': request.session.get('pickup_location', ''),
            'dropoff_location': request.session.get('dropoff_location', ''),
        })

    has_car = bool(request.session.get('booking_car_id'))
    context = {
        'form': form,
        'step': 1,
        'total_steps': 3 if has_car else 4,
    }
    return render(request, 'booking-flow.html', context)


@login_required
def booking_dates_view(request):
    """Booking Step 2: Date selection."""
    if not request.session.get('pickup_location'):
        messages.warning(request, "Please select a location first.")
        return redirect('booking_location')

    if request.method == 'POST':
        form = BookingDatesForm(request.POST)
        if form.is_valid():
            request.session['pickup_date'] = form.cleaned_data['pickup_date'].isoformat()
            request.session['dropoff_date'] = form.cleaned_data['dropoff_date'].isoformat()
            # Skip car selection if car is already pre-selected
            if request.session.get('booking_car_id'):
                return redirect('payment')
            return redirect('booking_select')
    else:
        form = BookingDatesForm()

    has_car = bool(request.session.get('booking_car_id'))
    context = {
        'form': form,
        'step': 2,
        'total_steps': 3 if has_car else 4,
    }
    return render(request, 'booking-flow.html', context)


@login_required
def booking_select_view(request):
    """Booking Step 2: Select a Car (if not already selected)."""
    # SKIP if car is already selected in session (from car-detail "Start Booking")
    if request.session.get('booking_car_id'):
        return redirect('payment')

    if not request.session.get('pickup_date'):
        messages.warning(request, "Please select dates first.")
        return redirect('booking_dates')

    # Handle full datetime 'Y-m-d H:i' or date-only 'Y-m-d'
    pickup_date_str = request.session['pickup_date']
    dropoff_date_str = request.session['dropoff_date']
    
    if ' ' in pickup_date_str:
        pickup_dt = parse_session_date(pickup_date_str)
        dropoff_dt = parse_session_date(dropoff_date_str)
    else:
        pickup_dt = datetime.combine(datetime.strptime(pickup_date_str, '%Y-%m-%d').date(), datetime.min.time())
        dropoff_dt = datetime.combine(datetime.strptime(dropoff_date_str, '%Y-%m-%d').date(), datetime.max.time())

    # Get available cars (excluding already booked ones for selected dates)
    booked_car_ids = Booking.objects.filter(
        status__in=['Pending', 'Active'],
        pickup_date__lt=dropoff_dt,
        dropoff_date__gt=pickup_dt
    ).values_list('car_id', flat=True)

    available_cars = Car.objects.filter(is_available=True).exclude(id__in=booked_car_ids)

    if request.method == 'POST':
        car_id = request.POST.get('car_id')
        is_outstation = request.POST.get('is_outstation') == 'on'
        if car_id:
            car = get_object_or_404(Car, id=car_id)
            # Store everything elegantly in the session to avoid db bloat
            request.session['booking_car_id'] = car_id
            request.session['is_outstation'] = is_outstation
            return redirect('payment')

    days = (dropoff_dt - pickup_dt).days
    if days == 0: days = 1 # Minimum 1 day charge

    context = {
        'cars': available_cars,
        'step': 3,
        'total_steps': 4,
        'pickup_date': pickup_dt,
        'dropoff_date': dropoff_dt,
        'days': days,
        'selected_car_id': request.session.get('booking_car_id'),
        'is_outstation': request.session.get('is_outstation', False),
    }
    return render(request, 'booking-flow.html', context)



@login_required
def payment_view(request):
    """Booking Step 4: Payment page utilizing session architecture."""
    car_id = request.session.get('booking_car_id')
    pickup_date_str = request.session.get('pickup_date')
    dropoff_date_str = request.session.get('dropoff_date')
    pickup_location = request.session.get('pickup_location')
    dropoff_location = request.session.get('dropoff_location')
    is_outstation = request.session.get('is_outstation', False)

    if not all([car_id, pickup_date_str, dropoff_date_str, pickup_location, dropoff_location]):
        messages.warning(request, "Your booking session has expired or is invalid.")
        return redirect('booking_select')

    # KYC check removed — prioritize frictionless booking experience
    
    car = get_object_or_404(Car, id=car_id)
    
    pickup_dt = parse_session_date(pickup_date_str)
    dropoff_dt = parse_session_date(dropoff_date_str)
    
    if not pickup_dt or not dropoff_dt:
        messages.warning(request, "Invalid date format. Please select dates again.")
        return redirect('booking_dates')
    
    days = (dropoff_dt - pickup_dt).days
    if days <= 0: days = 1 # Minimum 1 day charge
    
    # Use the new Dynamic Pricing Engine (Weekend Surcharges)
    subtotal = car.calculate_rental_price(pickup_dt, dropoff_dt)
    tax = (subtotal * Decimal('0.18')).quantize(Decimal('0.01'))
    total = subtotal + tax
    
    # Check for applied promo in session (New PromoCode Model)
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
                # Promo expired since it was applied
                del request.session['applied_promo_id']
        except PromoCode.DoesNotExist:
            del request.session['applied_promo_id']
        
    final_total = total - discount_amount

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
    }

    if request.method == 'POST':
        with transaction.atomic():
            # Lock the car row to prevent race conditions (double-booking)
            locked_car = Car.objects.select_for_update().get(id=car.id)
            
            # Check availability one final time
            is_available = Car.is_available_for_dates(locked_car.id, pickup_dt, dropoff_dt)

            if not is_available:
                messages.error(request, "Sorry, this car is no longer available for the selected dates.")
                return redirect('booking_select')

        # Process Booking Creation
        try:
            # Create real booking
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
            
            # Clear pending booking logic from session
            request.session.pop('booking_car_id', None)
            
            if promo_id:
                PromoCode.objects.filter(id=promo_id).update(used_count=F('used_count') + 1)

            payment_method = request.POST.get('payment_method_choice', 'stripe')
            
            if payment_method == 'razorpay':
                # Create Razorpay Order
                razorpay_order = BookingService.create_razorpay_order(booking, final_total)
                booking.razorpay_order_id = razorpay_order['id']
                booking.save()
                
                # Re-render payment page with Razorpay config to pop open the modal
                context['trigger_razorpay'] = True
                context['razorpay_order_id'] = razorpay_order['id']
                context['razorpay_amount'] = final_total # passed for reference
                context['razorpay_key_id'] = settings.RAZORPAY_KEY_ID
                context['booking'] = booking
                return render(request, 'payment.html', context)
            else:
                # Default to Stripe
                checkout_session = BookingService.create_stripe_session(
                    booking, car, days, pickup_dt, dropoff_dt, final_total
                )
                booking.stripe_session_id = checkout_session.id
                booking.save()
                return redirect(checkout_session.url, code=303)

        except Exception as e:
            if 'booking' in locals():
                booking.status = 'Cancelled'
                booking.save()
            # Professional error logging with detail for the USER to debug
            error_msg = f"Payment Gateway Error: {str(e)}" if settings.DEBUG else "We encountered an issue processing your payment. Please try again."
            messages.error(request, error_msg)
            return redirect('payment')

    context = {
        'car': car,
        'pickup_date': pickup_dt,
        'dropoff_date': dropoff_dt,
        'days': days,
        'subtotal': subtotal,
        'tax': tax,
        'total': total,
        'discount_amount': discount_amount,
        'final_total': final_total,
        'step': 3,
        'total_steps': 3,
        'pickup_location': request.session.get('pickup_location', ''),
        'dropoff_location': request.session.get('dropoff_location', ''),
    }
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
                booking.status = 'Active'
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
                
            return redirect('index')
    return redirect('index')


@login_required
@require_POST
def add_review_view(request, car_id):
    """Add review for a completed booking."""
    car = get_object_or_404(Car, id=car_id)
    booking_id = request.POST.get('booking_id')
    booking = get_object_or_404(Booking, id=booking_id, user=request.user, car=car, status='Completed')

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
    cars = Car.objects.filter(is_available=True)
    if q:
        cars = cars.filter(Q(name__icontains=q) | Q(brand__icontains=q))

    data = [{
        'id': car.id,
        'name': f"{car.brand} {car.name}",
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
            status__in=['Pending', 'Active'],
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

def onboarding_view(request):
    """Show onboarding slides to new users."""
    if request.session.get('onboarding_done'):
        return redirect('/')
    return render(request, 'onboarding.html')


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
