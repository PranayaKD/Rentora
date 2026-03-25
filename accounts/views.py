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


def login_view(request):
    """Unified Phone OTP login page."""
    if request.user.is_authenticated:
        return redirect('/')

    context = {
        'active_tab': 'login',
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
    active_bookings = bookings.filter(status__in=['Pending', 'Active'])
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
    bookings = Booking.objects.filter(user=request.user).select_related('car').prefetch_related('car__reviews')

    status_filter = request.GET.get('status', '')
    if status_filter:
        bookings = bookings.filter(status=status_filter)

    context = {
        'profile': profile,
        'bookings': bookings,
        'current_status': status_filter,
    }
    return render(request, 'dashboard.html', context)



@login_required
def profile_view(request):
    """Profile settings page."""
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES)
        if form.is_valid():
            full_name = form.cleaned_data['full_name']
            name_parts = full_name.split(' ', 1)
            request.user.first_name = name_parts[0]
            request.user.last_name = name_parts[1] if len(name_parts) > 1 else ''
            request.user.save()

            profile.phone = form.cleaned_data.get('phone', '')
            profile.license_number = form.cleaned_data.get('license_number', '')
            
            if form.cleaned_data.get('profile_photo'):
                profile.profile_photo = form.cleaned_data['profile_photo']
            if form.cleaned_data.get('license_image'):
                profile.license_image = form.cleaned_data['license_image']
            
            profile.save()

            messages.success(request, "Profile updated successfully!")
            return redirect('profile')
    else:
        form = ProfileForm(initial={
            'full_name': f"{request.user.first_name} {request.user.last_name}".strip(),
            'phone': profile.phone,
            'license_number': profile.license_number,
        })

    # Password change form
    password_form = ChangePasswordForm()
    if request.method == 'POST' and 'old_password' in request.POST:
        password_form = ChangePasswordForm(request.POST)
        if password_form.is_valid():
            if request.user.check_password(password_form.cleaned_data['old_password']):
                request.user.set_password(password_form.cleaned_data['new_password'])
                request.user.save()
                login(request, request.user)
                messages.success(request, "Password changed successfully!")
            else:
                messages.error(request, "Current password is incorrect.")

    context = {
        'profile_form': form,
        'password_form': password_form,
        'profile': profile,
    }
    return render(request, 'dashboard.html', context)


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
    """AJAX view to send OTP via Twilio."""
    try:
        data = json.loads(request.body)
        phone = data.get('phone', '').strip()
        
        if not phone.startswith('+91') or len(phone) < 13:
            return JsonResponse({'success': False, 'message': 'Invalid Indian phone number. Use +91 XXXXXXXXXX'})
            
        success = TwilioService.send_otp(phone)
        if success:
            return JsonResponse({'success': True, 'message': 'OTP sent successfully!'})
        else:
            return JsonResponse({'success': False, 'message': 'Failed to send OTP. Check your credentials or try later.'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@require_POST
def otp_verify_login(request):
    """AJAX view to verify OTP and log user in (with auto-signup)."""
    try:
        data = json.loads(request.body)
        phone = data.get('phone', '').strip()
        code = data.get('code', '').strip()
        
        if TwilioService.verify_otp(phone, code):
            # Find or create user atomically
            from django.db import transaction
            
            profile = UserProfile.objects.filter(phone=phone).first()
            if profile:
                user = profile.user
            else:
                # Uber-style: Auto-signup if phone not found
                with transaction.atomic():
                    # Generate a unique username based on phone
                    username = f"user_{phone.replace('+', '')}"
                    user = User.objects.create_user(
                        username=username,
                        first_name="Guest", # Can be updated in profile later
                    )
                    profile = user.profile
                    profile.phone = phone
                    profile.save()
            
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            
            # If it's a new user (no name yet), send to profile/onboarding
            if user.first_name == "Guest":
                return JsonResponse({'success': True, 'redirect': '/accounts/dashboard/profile/'})
                
            return JsonResponse({'success': True, 'redirect': request.GET.get('next', '/')})
        else:
            return JsonResponse({'success': False, 'message': 'Invalid or expired OTP.'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})
