import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncDate, TruncMonth
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User

from .decorators import staff_required
from .forms import CarForm
from core.models import Car, Booking, Notification
from accounts.models import UserProfile


@staff_required
def admin_dashboard_view(request):
    """Admin dashboard with stats and revenue chart data."""
    total_cars = Car.objects.count()
    booking_stats = Booking.objects.aggregate(
        active=Count('id', filter=Q(status='Active')),
        pending=Count('id', filter=Q(status='Pending')),
        total=Count('id'),
        revenue=Sum('total_price', filter=Q(status='Completed'))
    )
    total_users = User.objects.count()
    total_revenue = booking_stats['revenue'] or 0
    total_bookings = booking_stats['total']
    active_bookings = booking_stats['active']
    pending_bookings = booking_stats['pending']
    new_users = User.objects.filter(date_joined__month=timezone.now().month).count()
    pending_kyc = UserProfile.objects.filter(is_verified=False).exclude(license_number='').count()

    # 7-Day Revenue
    today = timezone.now().date()
    seven_days_ago = today - timedelta(days=6)

    daily_revenue = Booking.objects.filter(
        status='Completed',
        created_at__date__gte=seven_days_ago
    ).annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        total=Sum('total_price')
    ).order_by('date')

    # Build a dictionary to map date -> total
    revenue_map = {entry['date']: float(entry['total']) for entry in daily_revenue}

    chart_data = []
    max_revenue = 0

    for i in range(7):
        current_date = seven_days_ago + timedelta(days=i)
        rev = revenue_map.get(current_date, 0)
        max_revenue = max(max_revenue, rev)
        chart_data.append({
            'day': current_date.strftime('%a'),
            'revenue': rev,
        })

    # Calculate percentage heights (avoid division by zero)
    for day_data in chart_data:
        day_data['height_percent'] = (day_data['revenue'] / max_revenue * 100) if max_revenue > 0 else 0

    # Monthly Revenue (last 7 months)
    monthly_revenue = Booking.objects.filter(
        status='Completed'
    ).annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        total=Sum('total_price')
    ).order_by('month')

    monthly_revenue_list = [{'month': entry['month'].strftime('%b'), 'total': float(entry['total'])} for entry in monthly_revenue]

    # Recent bookings
    recent_bookings = Booking.objects.select_related('user', 'car').order_by('-created_at')[:10]

    context = {
        'total_cars': total_cars,
        'active_bookings': active_bookings,
        'total_revenue': total_revenue,
        'total_users': total_users,
        'total_bookings': total_bookings,
        'pending_bookings': pending_bookings,
        'new_users': new_users,
        'pending_kyc': pending_kyc,
        'recent_bookings': recent_bookings,
        'chart_data': chart_data,
        'max_revenue': max_revenue,
        'monthly_revenue': monthly_revenue_list,
    }
    return render(request, 'admin_panel.html', context)


@staff_required
def admin_cars_list_view(request):
    """List all cars in admin panel."""
    cars = Car.objects.all()
    category = request.GET.get('category', '')
    if category:
        cars = cars.filter(category=category)

    paginator = Paginator(cars, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'cars': page_obj,
    }
    return render(request, 'admin_panel.html', context)


@staff_required
def admin_car_add_view(request):
    """Add a new car."""
    if request.method == 'POST':
        form = CarForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Car added successfully!")
            return redirect('admin_cars_list')
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = CarForm()

    context = {
        'form': form,
        'action': 'Add',
    }
    return render(request, 'admin_panel.html', context)


@staff_required
def admin_car_edit_view(request, car_id):
    """Edit an existing car."""
    car = get_object_or_404(Car, id=car_id)

    if request.method == 'POST':
        form = CarForm(request.POST, request.FILES, instance=car)
        if form.is_valid():
            form.save()
            messages.success(request, f"{car} updated successfully!")
            return redirect('admin_cars_list')
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = CarForm(instance=car)

    context = {
        'form': form,
        'car': car,
        'action': 'Edit',
    }
    return render(request, 'admin_panel.html', context)


@staff_required
def admin_car_delete_view(request, car_id):
    """Soft delete a car (mark as unavailable)."""
    car = get_object_or_404(Car, id=car_id)
    car.is_available = False
    car.save()
    messages.success(request, f"{car} has been removed from the fleet.")
    return redirect('admin_cars_list')


@staff_required
def admin_bookings_list_view(request):
    """View all bookings with filters."""
    bookings = Booking.objects.select_related('user', 'car').all()

    status_filter = request.GET.get('status', '')
    if status_filter:
        bookings = bookings.filter(status=status_filter)

    paginator = Paginator(bookings, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'bookings': page_obj,
        'page_obj': page_obj,
        'current_status': status_filter,
    }
    return render(request, 'admin_panel.html', context)


@staff_required
def admin_booking_status_view(request, booking_id):
    """Change booking status."""
    booking = get_object_or_404(Booking, id=booking_id)
    new_status = request.POST.get('status')

    if new_status in dict(Booking.STATUS_CHOICES):
        booking.status = new_status
        booking.save()
        messages.success(request, f"Booking {booking.booking_reference} status changed to {new_status}.")
    else:
        messages.error(request, "Invalid status.")

    return redirect('admin_bookings_list')


@staff_required
def api_admin_revenue(request):
    """Monthly revenue data for Chart.js."""
    revenue_data = Booking.objects.filter(
        status='Completed'
    ).annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        total=Sum('total_price')
    ).order_by('month')

    months = [entry['month'].strftime('%b %Y') for entry in revenue_data]
    revenues = [float(entry['total']) for entry in revenue_data]

    return JsonResponse({'months': months, 'revenues': revenues})
