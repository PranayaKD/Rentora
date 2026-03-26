import csv
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Sum, Count, Avg, Q
from django.db.models.functions import TruncDate, TruncMonth
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

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
        revenue=Sum('total_price', filter=Q(is_paid=True))
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
        is_paid=True,
        created_at__date__gte=seven_days_ago
    ).annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        total=Sum('total_price')
    ).order_by('date')

    revenue_map = {entry['date']: float(entry['total']) for entry in daily_revenue}

    chart_data = []
    max_revenue = 0
    for i in range(7):
        current_date = seven_days_ago + timedelta(days=i)
        rev = revenue_map.get(current_date, 0)
        max_revenue = max(max_revenue, rev)
        chart_data.append({'day': current_date.strftime('%a'), 'revenue': rev})

    for day_data in chart_data:
        day_data['height_percent'] = (day_data['revenue'] / max_revenue * 100) if max_revenue > 0 else 0

    recent_bookings = Booking.objects.select_related('user', 'car').order_by('-created_at')[:10]

    context = {
        'active_page': 'dashboard',
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
    }
    return render(request, 'admin/dashboard_content.html', context)


@staff_required
def admin_cars_list_view(request):
    """List all cars in admin panel."""
    cars = Car.objects.all().order_by('-id')
    category = request.GET.get('category', '')
    if category:
        cars = cars.filter(category=category)

    paginator = Paginator(cars, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'active_page': 'cars',
        'page_obj': page_obj,
    }
    return render(request, 'admin/cars_list.html', context)


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
        'active_page': 'cars',
        'form': form,
        'action': 'Add',
    }
    return render(request, 'admin/car_form.html', context)


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
        'active_page': 'cars',
        'form': form,
        'car': car,
        'action': 'Edit',
    }
    return render(request, 'admin/car_form.html', context)


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
    bookings = Booking.objects.select_related('user', 'car').all().order_by('-created_at')

    status_filter = request.GET.get('status', '')
    if status_filter:
        bookings = bookings.filter(status=status_filter)

    paginator = Paginator(bookings, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'active_page': 'bookings',
        'page_obj': page_obj,
        'current_status': status_filter,
    }
    return render(request, 'admin/bookings_list.html', context)


@staff_required
def admin_booking_status_view(request, booking_id):
    """Change booking status."""
    booking = get_object_or_404(Booking, id=booking_id)
    new_status = request.POST.get('status')

    valid_statuses = ['Pending', 'Active', 'Completed', 'Cancelled']
    if new_status in valid_statuses:
        booking.status = new_status
        booking.save()
        messages.success(request, f"Booking {booking.booking_reference} status changed to {new_status}.")
    else:
        messages.error(request, "Invalid status.")

    return redirect('admin_bookings_list')


@staff_required
def admin_bookings_csv_view(request):
    """Export all bookings to CSV."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="rentora_bookings.csv"'

    writer = csv.writer(response)
    writer.writerow(['Reference', 'Customer', 'Email', 'Car', 'Pickup Date', 'Dropoff Date',
                     'Pickup Location', 'Dropoff Location', 'Amount', 'Status', 'Paid', 'Created'])

    bookings = Booking.objects.select_related('user', 'car').all().order_by('-created_at')
    for b in bookings:
        writer.writerow([
            b.booking_reference,
            b.user.get_full_name() or b.user.username,
            b.user.email,
            f"{b.car.brand} {b.car.name}",
            b.pickup_date,
            b.dropoff_date,
            b.pickup_location,
            b.dropoff_location,
            b.total_with_gst,
            b.status,
            'Yes' if b.is_paid else 'No',
            b.created_at.strftime('%Y-%m-%d %H:%M'),
        ])

    return response


@staff_required
def admin_users_list_view(request):
    """View all users with KYC status."""
    users = User.objects.select_related('profile').annotate(
        booking_count=Count('bookings')
    ).order_by('-date_joined')

    kyc_filter = request.GET.get('kyc', '')
    if kyc_filter == 'pending':
        users = users.filter(profile__is_verified=False).exclude(profile__license_number='')

    pending_kyc_count = UserProfile.objects.filter(is_verified=False).exclude(license_number='').count()

    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'active_page': 'users',
        'page_obj': page_obj,
        'kyc_filter': kyc_filter,
        'pending_kyc_count': pending_kyc_count,
    }
    return render(request, 'admin/users_list.html', context)


@staff_required
def admin_revenue_view(request):
    """Revenue analytics page."""
    total_revenue = Booking.objects.filter(is_paid=True).aggregate(Sum('total_price'))['total_price__sum'] or 0
    completed_bookings = Booking.objects.filter(status='Completed').count()
    avg_booking_value = Booking.objects.filter(is_paid=True).aggregate(Avg('total_price'))['total_price__avg'] or 0

    # Monthly Revenue for chart
    monthly_data = Booking.objects.filter(
        is_paid=True
    ).annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        total=Sum('total_price')
    ).order_by('month')

    monthly_labels = json.dumps([entry['month'].strftime('%b %Y') for entry in monthly_data])
    monthly_revenues = json.dumps([float(entry['total']) for entry in monthly_data])

    # Top revenue cars
    top_cars = Car.objects.annotate(
        booking_count=Count('bookings', filter=Q(bookings__is_paid=True)),
        total_revenue=Sum('bookings__total_price', filter=Q(bookings__is_paid=True))
    ).filter(total_revenue__isnull=False).order_by('-total_revenue')[:10]

    context = {
        'active_page': 'revenue',
        'total_revenue': total_revenue,
        'completed_bookings': completed_bookings,
        'avg_booking_value': avg_booking_value,
        'monthly_labels': monthly_labels,
        'monthly_revenues': monthly_revenues,
        'top_cars': top_cars,
    }
    return render(request, 'admin/revenue.html', context)


@staff_required
def api_admin_revenue(request):
    """Monthly revenue data for Chart.js."""
    revenue_data = Booking.objects.filter(
        is_paid=True
    ).annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        total=Sum('total_price')
    ).order_by('month')

    months = [entry['month'].strftime('%b %Y') for entry in revenue_data]
    revenues = [float(entry['total']) for entry in revenue_data]

    return JsonResponse({'months': months, 'revenues': revenues})
