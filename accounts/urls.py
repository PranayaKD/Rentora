from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='accounts_index'),
    path('profile/', views.profile_view, name='accounts_profile'),
    path('bookings/', views.bookings_view, name='accounts_bookings'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('dashboard/bookings/', views.bookings_view, name='dashboard_bookings'),
    path('dashboard/profile/', views.profile_view, name='profile'),
    path('dashboard/wishlist/', views.wishlist_view, name='wishlist'),
    path('kyc/', views.kyc_view, name='kyc'),
    
    # OTP Login Routes
    path('login/otp/request/', views.otp_login_request, name='otp_login_request'),
    path('login/otp/verify/', views.otp_verify_login, name='otp_verify_login'),
]
