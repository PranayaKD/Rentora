from django.urls import path
from . import views

urlpatterns = [
    # Landing
    path('', views.index_view, name='index'),
    path('how-it-works/', views.how_it_works_view, name='how_it_works'),
    path('subscription/', views.subscription_view, name='subscription'),
    path('airport-transfer/', views.airport_transfer_view, name='airport_transfer'),
    path('why-rentora/', views.why_rentora_view, name='why_rentora'),

    # Cars
    path('cars/', views.cars_view, name='cars'),
    path('cars/<int:car_id>/', views.car_detail_view, name='car_detail'),

    # Booking flow
    path('booking/', views.booking_location_view, name='booking_location'),
    path('booking/<int:car_id>/', views.booking_location_direct, name='booking_location_direct'),
    path('booking/dates/', views.booking_dates_view, name='booking_dates'),
    path('booking/select/', views.booking_select_view, name='booking_select'),
    path('booking/payment/', views.payment_view, name='payment'),
    path('booking/confirmation/<int:booking_id>/', views.confirmation_view, name='confirmation'),
    path('booking/<int:booking_id>/detail/', views.booking_detail_view, name='booking_detail'),
    path('booking/<int:booking_id>/cancel/', views.cancel_booking_view, name='cancel_booking'),
    path('booking/invoice/<int:booking_id>/', views.invoice_view, name='invoice'),
    path('booking/receipt/<int:booking_id>/', views.download_receipt_view, name='download_receipt'),

    # Search
    path('search/', views.cars_view, name='search'),

    # Contact
    path('contact/', views.contact_view, name='contact'),

    # Reviews
    path('cars/<int:car_id>/review/', views.add_review_view, name='add_review'),

    # API Endpoints
    path('api/cars/search/', views.api_cars_search, name='api_cars_search'),
    path('api/booking/check-availability/', views.api_check_availability, name='api_check_availability'),
    path('api/promo/apply/', views.api_apply_promo, name='api_apply_promo'),
    path('api/wishlist/toggle/<int:car_id>/', views.api_wishlist_toggle, name='api_wishlist_toggle'),
    path('api/cars/<int:car_id>/booked-dates/', views.get_booked_dates, name='car_booked_dates'),
    path('api/stripe/webhook/', views.stripe_webhook, name='stripe_webhook'),
    path('api/razorpay/callback/', views.razorpay_callback, name='razorpay_callback'),

    # Notifications
    path('notifications/', views.notifications_view, name='notifications'),
    path('api/notifications/mark-read/<int:notification_id>/', views.api_mark_notification_read, name='api_mark_notification_read'),
    path('api/notifications/mark-all-read/', views.api_mark_all_notifications_read, name='api_mark_all_notifications_read'),
    path('api/notifications/count/', views.api_notification_count, name='api_notification_count'),

    # Static & Legal
    path('terms/', views.terms_view, name='terms'),
    path('privacy/', views.privacy_view, name='privacy'),
    path('api/city/set/', views.set_city_view, name='set_city'),

    # Onboarding
    path('onboarding/', views.onboarding_view, name='onboarding'),
    path('onboarding/skip/', views.skip_onboarding, name='skip_onboarding'),

    # Advanced Indian Mobility APIs
    path('api/trip/<int:booking_id>/inspection/', views.api_trip_inspection, name='api_trip_inspection'),
    path('api/trip/<int:booking_id>/extend/', views.api_trip_extend, name='api_trip_extend'),
    path('api/trip/<int:booking_id>/sos/', views.api_trip_sos, name='api_trip_sos'),
    path('api/trip/<int:booking_id>/toll-dispute/', views.api_toll_dispute, name='api_toll_dispute'),
    path('api/trip/<int:booking_id>/cancel-sla/', views.api_cancel_booking_sla, name='api_cancel_booking_sla'),
]
