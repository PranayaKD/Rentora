from django.conf import settings
from core.models import Wishlist

def shared_layout_context(request):
    """
    Context processor providing shared layout variables:
    - current_city: stored in session, defaults to 'Bengaluru'
    - is_authenticated: boolean
    - display_name: first name, username, or phone
    - wishlist_count: count of wishlisted cars for user
    - active_tab: 'home', 'search', 'bookings', 'profile', or None
    - hide_bottom_nav: boolean, True on funnel, auth, checkout, and kyc
    - vapid_public_key: VAPID public key for push notifications
    """
    current_city = request.session.get('current_city', 'Bengaluru')
    
    # Active tab and funnel detection based on resolver match
    active_tab = None
    hide_bottom_nav = False
    rname = getattr(request.resolver_match, 'url_name', '') if request.resolver_match else ''
    path = request.path or ''
    
    if rname == 'index':
        active_tab = 'home'
    elif rname in ('cars', 'search'):
        active_tab = 'search'
    elif rname in ('dashboard_bookings',):
        active_tab = 'bookings'
    elif rname in ('dashboard', 'profile'):
        active_tab = 'profile'
        
    funnel_url_names = {
        'car_detail',
        'booking_location',
        'booking_location_direct',
        'booking_dates',
        'booking_select',
        'payment',
        'confirmation',
        'booking_detail',
        'cancel_booking',
        'invoice',
        'download_receipt',
        'login',
        'signup',
        'onboarding',
        'otp_login_request',
        'otp_verify_login',
    }
    
    if (
        rname in funnel_url_names
        or rname.startswith('booking_')
        or any(seg in path for seg in ('/booking/', '/payment', '/checkout', '/login', '/signup', '/onboarding', '/auth'))
    ):
        hide_bottom_nav = True

    is_auth = request.user.is_authenticated
    display_name = ''
    wishlist_count = 0
    
    if is_auth:
        display_name = (
            request.user.first_name.strip()
            or getattr(getattr(request.user, 'profile', None), 'first_name', '')
            or request.user.username
        )
        try:
            wishlist_count = Wishlist.objects.filter(user=request.user).count()
        except Exception:
            wishlist_count = 0

    return {
        'current_city': current_city,
        'is_authenticated': is_auth,
        'display_name': display_name,
        'wishlist_count': wishlist_count,
        'active_tab': active_tab,
        'hide_bottom_nav': hide_bottom_nav,
        'vapid_public_key': getattr(settings, 'VAPID_PUBLIC_KEY', ''),
    }

def vapid_key_processor(request):
    return {
        'vapid_public_key': getattr(settings, 'VAPID_PUBLIC_KEY', '')
    }
