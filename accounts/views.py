from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages

from .models import UserProfile
from .forms import LoginForm, SignupForm, ProfileForm, ChangePasswordForm
from .services import TwilioService
from core.models import Booking, Wishlist
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
import re


def login_view(request):
    """Unified Phone OTP login page."""
    if request.user.is_authenticated:
        return redirect('/')

    if request.GET.get('change'):
        request.session.pop('login_phone', None)

    next_url = request.GET.get('next') or request.POST.get('next') or ''
    phone = request.session.get('login_phone', '')

    context = {
        'active_tab': 'login',
        'next': next_url,
        'phone': phone,
    }
    return render(request, 'auth.html', context)


def signup_view(request):
    """Redirect to unified login (auto-signup)."""
    return redirect('login')


def logout_view(request):
    """Logout and redirect to home."""
    logout(request)
    messages.info(request, "You've been logged out successfully.")
    return redirect('index')


@login_required
def dashboard_view(request):
    """User dashboard with active bookings."""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    bookings = Booking.objects.filter(user=request.user).select_related('car').prefetch_related('car__reviews')
    active_bookings = bookings.filter(status__in=[Booking.Status.PENDING, Booking.Status.CONFIRMED, 'Pending', 'Active', 'Confirmed'])
    recent_bookings = bookings[:5]

    context = {
        'profile': profile,
        'active_bookings': active_bookings,
        'recent_bookings': recent_bookings,
        'total_bookings': bookings.count(),
    }
    return render(request, 'dashboard.html', context)



@login_required
def bookings_view(request):
    """User booking history with filters."""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    all_user_bookings = Booking.objects.filter(user=request.user).select_related('car').prefetch_related('car__reviews')
    bookings = all_user_bookings

    status_filter = request.GET.get('status', '')
    if status_filter:
        bookings = bookings.filter(status=status_filter)

    active_bookings = all_user_bookings.filter(status__in=[Booking.Status.PENDING, Booking.Status.CONFIRMED, 'Pending', 'Active', 'Confirmed'])

    context = {
        'profile': profile,
        'bookings': bookings,
        'active_bookings': active_bookings,
        'recent_bookings': all_user_bookings[:5],
        'total_bookings': all_user_bookings.count(),
        'current_status': status_filter,
    }
    return render(request, 'dashboard.html', context)



@login_required
def profile_view(request):
    """Profile settings and account verification page."""
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        # Route 1: Password change submission
        if 'change_password' in request.POST or 'old_password' in request.POST:
            password_form = ChangePasswordForm(request.POST)
            form = ProfileForm(initial={
                'full_name': f"{request.user.first_name} {request.user.last_name}".strip(),
                'email': request.user.email,
                'phone': profile.phone,
                'date_of_birth': profile.date_of_birth,
                'license_number': profile.license_number,
                'aadhaar_number': profile.aadhaar_number,
                'pan_number': profile.pan_number,
            })
            if password_form.is_valid():
                if request.user.check_password(password_form.cleaned_data['old_password']):
                    request.user.set_password(password_form.cleaned_data['new_password'])
                    request.user.save()
                    login(request, request.user, backend='django.contrib.auth.backends.ModelBackend')
                    messages.success(request, "Password changed successfully!")
                    return redirect('profile')
                else:
                    messages.error(request, "Current password is incorrect.")
            else:
                for error_list in password_form.errors.values():
                    for err in error_list:
                        messages.error(request, err)
        # Route 2: Profile details update
        else:
            form = ProfileForm(request.POST, request.FILES)
            password_form = ChangePasswordForm()
            if form.is_valid():
                full_name = form.cleaned_data['full_name'].strip()
                name_parts = full_name.split(' ', 1)
                request.user.first_name = name_parts[0]
                request.user.last_name = name_parts[1] if len(name_parts) > 1 else ''
                
                email = form.cleaned_data.get('email')
                if email:
                    existing_email_user = User.objects.filter(email=email).exclude(id=request.user.id).first()
                    if existing_email_user:
                        messages.error(request, "This email address is already in use by another account.")
                        context = {
                            'profile_form': form,
                            'password_form': password_form,
                            'profile': profile,
                        }
                        return render(request, 'dashboard.html', context)
                    request.user.email = email
                request.user.save()

                if form.cleaned_data.get('phone'):
                    profile.phone = form.cleaned_data['phone']
                if form.cleaned_data.get('license_number'):
                    profile.license_number = form.cleaned_data['license_number']
                if form.cleaned_data.get('aadhaar_number'):
                    profile.aadhaar_number = form.cleaned_data['aadhaar_number']
                if form.cleaned_data.get('pan_number'):
                    profile.pan_number = form.cleaned_data['pan_number']
                if form.cleaned_data.get('date_of_birth'):
                    profile.date_of_birth = form.cleaned_data['date_of_birth']
                
                if form.cleaned_data.get('profile_photo'):
                    profile.profile_photo = form.cleaned_data['profile_photo']
                if form.cleaned_data.get('license_image'):
                    profile.license_image = form.cleaned_data['license_image']
                
                profile.save()

                messages.success(request, "Profile updated successfully!")
                return redirect('profile')
            else:
                for error_list in form.errors.values():
                    for err in error_list:
                        messages.error(request, err)
    else:
        form = ProfileForm(initial={
            'full_name': f"{request.user.first_name} {request.user.last_name}".strip(),
            'email': request.user.email,
            'phone': profile.phone,
            'date_of_birth': profile.date_of_birth,
            'license_number': profile.license_number,
            'aadhaar_number': profile.aadhaar_number,
            'pan_number': profile.pan_number,
        })
        password_form = ChangePasswordForm()

    context = {
        'profile_form': form,
        'password_form': password_form,
        'profile': profile,
    }
    return render(request, 'dashboard.html', context)


@login_required
def kyc_view(request):
    """DigiLocker and driving licence KYC verification."""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    return render(request, 'kyc.html', {'profile': profile})


@login_required
def wishlist_view(request):
    """User's saved/wishlisted cars."""
    wishlisted = Wishlist.objects.filter(user=request.user).select_related('car').prefetch_related('car__reviews')

    context = {
        'wishlisted_cars': wishlisted,
    }
    return render(request, 'dashboard.html', context)


@require_POST
def otp_login_request(request):
    """View to send OTP via Twilio. Supports both JSON AJAX and standard Form POST."""
    from django.core.cache import cache
    import time

    ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '')).split(',')[0].strip()
    
    # 1. IP-level rate limiting (max 10 requests per 10 minutes across any number of sessions)
    ip_cache_key = f"otp_ratelimit_ip_{ip}"
    ip_attempts = cache.get(ip_cache_key, 0)
    if ip_attempts >= 10:
        err_msg = 'Too many requests from this network. Please wait a few minutes.'
        if request.content_type == 'application/json' or request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': err_msg}, status=429)
        return render(request, 'auth.html', {'otp_error': err_msg, 'next': request.POST.get('next', ''), 'active_tab': 'login'})

    # 2. Session-based rate limiting (max 5 requests per 60 seconds)
    now = time.time()
    otp_history = request.session.get('otp_request_timestamps', [])
    otp_history = [t for t in otp_history if now - t < 60]
    if len(otp_history) >= 5:
        err_msg = 'Too many OTP requests. Please wait a minute before requesting another.'
        if request.content_type == 'application/json' or request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': err_msg}, status=429)
        return render(request, 'auth.html', {'otp_error': err_msg, 'next': request.POST.get('next', ''), 'active_tab': 'login'})
    otp_history.append(now)
    request.session['otp_request_timestamps'] = otp_history

    is_ajax = request.content_type == 'application/json' or request.headers.get('x-requested-with') == 'XMLHttpRequest'
    next_url = request.GET.get('next') or request.POST.get('next') or ''
    
    if is_ajax:
        try:
            data = json.loads(request.body.decode('utf-8'))
            phone = data.get('phone', '').strip()
            name = data.get('name', '').strip()
            if name:
                request.session['register_name'] = name
        except Exception:
            return JsonResponse({'success': False, 'message': 'Invalid request body.'})
    else:
        phone = request.POST.get('phone', '').strip()
        name = request.POST.get('name', '').strip()
        if name:
            request.session['register_name'] = name

    # Normalize phone: strip hyphens, spaces, parentheses
    clean_phone = re.sub(r'[\s\-\(\)]', '', phone)
    if clean_phone.startswith('+91'):
        phone = clean_phone
    elif clean_phone.startswith('91') and len(clean_phone) == 12:
        phone = f"+{clean_phone}"
    elif clean_phone.isdigit() and len(clean_phone) == 10:
        phone = f"+91{clean_phone}"
    elif clean_phone.startswith('0') and len(clean_phone) == 11:
        phone = f"+91{clean_phone[1:]}"
    else:
        phone = clean_phone

    # 3. Phone-specific rate limiting (max 3 SMS dispatches per phone per 10 minutes)
    phone_cache_key = f"otp_ratelimit_phone_{phone}"
    phone_attempts = cache.get(phone_cache_key, 0)
    if phone_attempts >= 3:
        err_msg = 'Too many OTPs sent to this number. Please wait 10 minutes before requesting again.'
        if is_ajax:
            return JsonResponse({'success': False, 'message': err_msg}, status=429)
        return render(request, 'auth.html', {'otp_error': err_msg, 'next': next_url, 'active_tab': 'login'})

    cache.set(ip_cache_key, ip_attempts + 1, timeout=600)
    cache.set(phone_cache_key, phone_attempts + 1, timeout=600)

    if not phone.startswith('+91') or len(phone) < 13:
        err_msg = 'Invalid Indian phone number. Please enter a valid 10-digit number.'
        if is_ajax:
            return JsonResponse({'success': False, 'message': err_msg})
        return render(request, 'auth.html', {'otp_error': err_msg, 'next': next_url, 'active_tab': 'login'})
        
    success = TwilioService.send_otp(phone)
    if success:
        request.session['login_phone'] = phone
        if is_ajax:
            return JsonResponse({'success': True, 'message': 'OTP sent successfully!'})
        return render(request, 'auth.html', {'phone': phone, 'next': next_url, 'active_tab': 'login'})
    else:
        err_msg = 'Failed to send OTP. Please check your credentials or try later.'
        if is_ajax:
            return JsonResponse({'success': False, 'message': err_msg})
        return render(request, 'auth.html', {'otp_error': err_msg, 'next': next_url, 'active_tab': 'login'})


@require_POST
def otp_verify_login(request):
    """View to verify OTP and log user in (with auto-signup). Supports both JSON AJAX and standard Form POST."""
    is_ajax = request.content_type == 'application/json' or request.headers.get('x-requested-with') == 'XMLHttpRequest'
    next_url = request.GET.get('next') or request.POST.get('next') or ''
    
    if is_ajax:
        try:
            data = json.loads(request.body.decode('utf-8'))
            phone = data.get('phone', '').strip()
            code = data.get('code', '').strip()
            name = data.get('name', '').strip()
        except Exception:
            return JsonResponse({'success': False, 'message': 'Invalid request body.'})
    else:
        phone = request.POST.get('phone', '').strip()
        code = request.POST.get('code', '').strip()
        name = request.POST.get('name', '').strip()

    # Normalize phone: strip hyphens, spaces, parentheses
    clean_phone = re.sub(r'[\s\-\(\)]', '', phone)
    if clean_phone.startswith('+91'):
        phone = clean_phone
    elif clean_phone.startswith('91') and len(clean_phone) == 12:
        phone = f"+{clean_phone}"
    elif clean_phone.isdigit() and len(clean_phone) == 10:
        phone = f"+91{clean_phone}"
    elif clean_phone.startswith('0') and len(clean_phone) == 11:
        phone = f"+91{clean_phone[1:]}"
    else:
        phone = clean_phone

    if TwilioService.verify_otp(phone, code):
        from django.db import transaction
        profile = UserProfile.objects.filter(phone=phone).first()
        if profile:
            user = profile.user
        else:
            # Automatically create user profile if phone does not exist
            with transaction.atomic():
                username = f"user_{phone.replace('+', '')}"
                user = User.objects.create_user(
                    username=username,
                    first_name="Guest",
                )
                profile = user.profile
                profile.phone = phone
                profile.save()

        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        reg_name = name or request.session.pop('register_name', '')
        if reg_name and user.first_name in ("Guest", "", None):
            user.first_name = reg_name
            user.save()
        request.session.pop('login_phone', None)
        
        target_url = next_url or '/'
        from django.utils.http import url_has_allowed_host_and_scheme
        if not url_has_allowed_host_and_scheme(target_url, allowed_hosts={request.get_host()}):
            target_url = '/'
        if is_ajax:
            if user.first_name in ("Guest", "") and not next_url:
                target_url = '/dashboard/profile/'
            return JsonResponse({'success': True, 'redirect': target_url})
        return redirect(target_url)
    else:
        err_msg = 'Invalid or expired OTP. Please try again.'
        if is_ajax:
            return JsonResponse({'success': False, 'message': err_msg})
        return render(request, 'auth.html', {'phone': phone, 'otp_error': err_msg, 'next': next_url, 'active_tab': 'login'})
