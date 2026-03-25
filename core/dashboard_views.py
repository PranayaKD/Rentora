from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from datetime import timedelta
from core.models import Booking, Car, User
from decimal import Decimal

@user_passes_test(lambda u: u.is_staff)
def dashboard_hq(request):
    """
    Rentora HQ: Executive Dashboard with business intelligence.
    """
    # 1. High-level Metrics
    total_revenue = Booking.objects.filter(is_paid=True).aggregate(Sum('total_price'))['total_price__sum'] or Decimal('0.00')
    active_bookings = Booking.objects.filter(status=Booking.Status.CONFIRMED).count()
    fleet_size = Car.objects.count()
    user_count = User.objects.count()
    
    # 2. Revenue Chart Data (Last 7 days)
    today = timezone.now().date()
    revenue_chart = []
    days_labels = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        rev = Booking.objects.filter(
            pickup_date=day, 
            is_paid=True
        ).aggregate(Sum('total_price'))['total_price__sum'] or Decimal('0.00')
        revenue_chart.append(float(rev))
        days_labels.append(day.strftime('%b %d'))

    # 3. Popular Cars (Top 5)
    popular_cars = Car.objects.annotate(
        booking_count=Count('bookings')
    ).order_by('-booking_count')[:5]

    # 4. Recent Activity
    recent_bookings = Booking.objects.select_related('user', 'car').order_by('-created_at')[:10]

    # 5. Abandoned Carts (Pending for > 2 hours)
    threshold = timezone.now() - timedelta(hours=2)
    abandoned_count = Booking.objects.filter(
        status=Booking.Status.PENDING,
        created_at__lt=threshold
    ).count()

    context = {
        'total_revenue': total_revenue,
        'active_bookings': active_bookings,
        'fleet_size': fleet_size,
        'user_count': user_count,
        'revenue_data': revenue_chart,
        'revenue_labels': days_labels,
        'popular_cars': popular_cars,
        'recent_bookings': recent_bookings,
        'abandoned_count': abandoned_count,
    }
    return render(request, 'admin_dashboard.html', context)
