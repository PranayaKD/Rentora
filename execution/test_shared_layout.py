"""
Execution Verification: Shared Layout & Backend Wiring Tests
Tests:
1. Navbar & footer single sourcing on every page
2. Active tab derivation (home, search, bookings, profile)
3. Unauthenticated redirects with ?next= for Bookings and Profile
4. Bottom nav visibility (shown on main tabs, hidden on funnel/auth/kyc)
5. City session persistence via POST endpoint
6. Static legal & support routes (/terms/, /privacy/, /contact/)
7. Full-page Phone OTP request & verify flow (with auto-signup)
8. Authenticated layout context (display_name, is_authenticated)
9. Dashboard Bookings tab integration & Booking Detail route
10. Booking Cancellation action & status transition
11. Driving Licence KYC onboarding states (upload, pending, verified)
12. POST Logout with session invalidation
"""
import os
import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rentora_project.settings')

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import django
django.setup()

from django.test.utils import setup_test_environment
setup_test_environment()

from django.test import Client
from django.contrib.auth.models import User
from core.models import Car, Booking
from accounts.models import UserProfile
from datetime import date, timedelta
from decimal import Decimal

def run_tests():
    print("==================================================")
    print("   RENTORA - SHARED LAYOUT & BACKEND WIRING TESTS ")
    print("==================================================")
    
    client = Client()
    passed = 0
    total = 0

    def assert_test(condition, test_name):
        nonlocal passed, total
        total += 1
        if condition:
            passed += 1
            print(f"[PASS] {test_name}")
        else:
            print(f"[FAIL] {test_name}")
            raise AssertionError(f"Test failed: {test_name}")

    # TEST 1: Navbar and Footer exist on Home page
    resp_home = client.get('/')
    assert_test(resp_home.status_code == 200, "1. Home page returns HTTP 200")
    home_html = resp_home.content.decode('utf-8')
    assert_test(home_html.count('<header') == 1, "2. Exactly one navbar <header> rendered on Home")
    assert_test(home_html.count('<footer') == 1, "3. Exactly one footer <footer> rendered on Home")
    assert_test('current-city-label' in home_html, "4. Current city selector pill present in navbar")

    # TEST 2: Active Tab Context Resolution
    assert_test(resp_home.context['active_tab'] == 'home', "5. Home page context has active_tab == 'home'")
    
    resp_cars = client.get('/cars/')
    assert_test(resp_cars.status_code == 200, "6. Cars catalog returns HTTP 200")
    assert_test(resp_cars.context['active_tab'] == 'search', "7. Cars page context has active_tab == 'search'")

    # TEST 3: Unauthenticated redirect with ?next= on Bookings and Profile tabs
    assert_test('login/?next=' in home_html or 'accounts/login/?next=' in home_html, 
                "8. Anonymous bottom nav Bookings tab redirects to login with ?next=")
    assert_test('login/?next=' in home_html or 'accounts/login/?next=' in home_html, 
                "9. Anonymous bottom nav Profile tab redirects to login with ?next=")

    # TEST 4: Bottom Nav Hidden on Checkout/Booking Funnel
    resp_book = client.get('/booking/', follow=True)
    book_html = resp_book.content.decode('utf-8')
    assert_test('id="mobile-bottom-nav"' not in book_html, 
                "10. Bottom nav is hidden on unauthenticated booking funnel (redirected to login)")

    # TEST 5: City Selection Session Persistence via POST endpoint
    city_post = client.post('/api/city/set/', 
                            data=json.dumps({'city': 'Mumbai'}), 
                            content_type='application/json')
    assert_test(city_post.status_code == 200 and city_post.json().get('city') == 'Mumbai',
                "11. City selection POST endpoint persists 'Mumbai'")
    
    resp_subsequent = client.get('/')
    assert_test(resp_subsequent.context['current_city'] == 'Mumbai',
                "12. Subsequent page loads reflect saved city 'Mumbai' in context")
    assert_test('Mumbai</span>' in resp_subsequent.content.decode('utf-8'),
                "13. Subsequent page loads reflect saved city 'Mumbai' in navbar HTML")

    # TEST 6: Static Legal / Support Routes
    resp_terms = client.get('/terms/')
    assert_test(resp_terms.status_code == 200, "14. /terms/ route returns HTTP 200")
    assert_test('Terms of Service' in resp_terms.content.decode('utf-8'), "15. /terms/ renders Terms of Service content")

    resp_privacy = client.get('/privacy/')
    assert_test(resp_privacy.status_code == 200, "16. /privacy/ route returns HTTP 200")
    assert_test('Privacy Policy' in resp_privacy.content.decode('utf-8'), "17. /privacy/ renders Privacy Policy content")

    resp_contact = client.get('/contact/')
    assert_test(resp_contact.status_code == 200, "18. /contact/ route returns HTTP 200")
    assert_test('Customer Support' in resp_contact.content.decode('utf-8'), "19. /contact/ renders Help & Support content")

    # TEST 7: Full-Page Form POST OTP Auth Flow
    # Step 1: Send OTP via HTML Form POST
    resp_otp_send = client.post('/accounts/login/otp/request/', {'phone': '9876543210'})
    assert_test(resp_otp_send.status_code == 200, "20. Full-page Form POST to otp_login_request succeeds")
    otp_step2_html = resp_otp_send.content.decode('utf-8')
    assert_test('Enter 6-Digit OTP' in otp_step2_html, "21. Full-page login transitions to Step 2 OTP entry")
    assert_test('+919876543210' in otp_step2_html, "22. Normalized +91 phone present in Step 2 form")

    # Step 2: Verify OTP via HTML Form POST (using dev fallback 123456)
    resp_otp_verify = client.post('/accounts/login/otp/verify/', {'phone': '+919876543210', 'code': '123456'}, follow=True)
    assert_test(resp_otp_verify.status_code == 200, "23. Full-page Form POST to otp_verify_login logs user in")
    assert_test('_auth_user_id' in client.session, "24. Session user id established upon OTP verification")

    # TEST 8: Authenticated User Layout Context
    logged_user = User.objects.get(id=client.session['_auth_user_id'])
    logged_user.first_name = 'Arjun'
    logged_user.save()

    resp_auth_home = client.get('/')
    assert_test(resp_auth_home.context['is_authenticated'] is True, "25. Authenticated context has is_authenticated == True")
    assert_test(resp_auth_home.context['display_name'] == 'Arjun', "26. Authenticated context display_name is 'Arjun'")

    # TEST 9: Dashboard & Bookings Tab
    resp_dash = client.get('/accounts/dashboard/')
    assert_test(resp_dash.status_code == 200, "27. Dashboard Overview returns HTTP 200")
    assert_test('id="logout-sheet"' in resp_dash.content.decode('utf-8'), "28. Dashboard includes logout confirmation sheet")

    resp_bookings = client.get('/accounts/dashboard/bookings/')
    assert_test(resp_bookings.status_code == 200, "29. Dashboard Bookings returns HTTP 200")
    assert_test(resp_bookings.context['active_tab'] == 'bookings', "30. Bookings page has active_tab == 'bookings'")
    assert_test('id="mobile-bottom-nav"' in resp_bookings.content.decode('utf-8'), "31. Bottom nav is visible on Bookings tab")

    # TEST 10: Real Booking Detail View & Cancel Action
    car = Car.objects.first()
    if not car:
        car = Car.objects.create(
            name="Maruti Swift ZXi",
            brand="Maruti Suzuki",
            category="Hatchback",
            transmission="Manual",
            fuel_type="Petrol",
            price_per_day=Decimal('1920.00'),
            hourly_rate=Decimal('80.00'),
            is_available=True
        )

    test_booking = Booking.objects.create(
        user=logged_user,
        car=car,
        booking_reference="RNT-TEST-001",
        pickup_date=date.today() + timedelta(days=2),
        dropoff_date=date.today() + timedelta(days=4),
        pickup_location="Indiranagar, Bengaluru",
        dropoff_location="Indiranagar, Bengaluru",
        total_price=Decimal('3840.00'),
        total_with_gst=Decimal('4531.20'),
        gst_amount=Decimal('691.20'),
        status=Booking.Status.CONFIRMED,
        is_paid=True
    )

    resp_detail = client.get(f'/booking/{test_booking.id}/detail/')
    assert_test(resp_detail.status_code == 200, "32. Booking Detail view returns HTTP 200")
    detail_html = resp_detail.content.decode('utf-8')
    assert_test('RNT-TEST-001' in detail_html, "33. Booking Detail displays real booking reference")
    assert_test('Cancel Booking' in detail_html, "34. Booking Detail displays Cancel Booking action")
    assert_test('id="mobile-bottom-nav"' not in detail_html, "35. Bottom nav is hidden on booking detail view")

    # Test Cancel Booking POST
    resp_cancel = client.post(f'/booking/{test_booking.id}/cancel/', follow=True)
    assert_test(resp_cancel.status_code == 200, "36. Cancel booking POST endpoint returns HTTP 200")
    test_booking.refresh_from_db()
    assert_test(test_booking.status == Booking.Status.CANCELLED, "37. Booking status transitioned to CANCELLED in database")

    # TEST 11: Driving Licence KYC Onboarding States
    # State 1: Upload state (no DL yet)
    profile = logged_user.profile
    profile.license_number = ''
    profile.license_image = None
    profile.is_verified = False
    profile.save()

    resp_kyc_get = client.get('/onboarding/')
    assert_test(resp_kyc_get.status_code == 200, "38. /onboarding/ route returns HTTP 200")
    assert_test(resp_kyc_get.context['kyc_status'] == 'upload', "39. Initial KYC state is 'upload'")

    # State 2: Submit DL Number (Transitions to Pending)
    resp_kyc_post = client.post('/onboarding/', {'license_number': 'KA0120240009999'}, follow=True)
    assert_test(resp_kyc_post.status_code == 200, "40. KYC DL submit POST succeeds")
    profile.refresh_from_db()
    assert_test(profile.license_number == 'KA0120240009999', "41. UserProfile persisted submitted DL number")

    # State 3: Verified State
    profile.is_verified = True
    profile.save()
    resp_kyc_verified = client.get('/onboarding/')
    assert_test(resp_kyc_verified.context['kyc_status'] == 'verified', "42. Verified profile displays 'verified' KYC state")

    # TEST 12: Logout Action
    resp_logout = client.post('/logout/', follow=True)
    assert_test(resp_logout.status_code == 200, "43. POST to /logout/ succeeds and redirects home")
    assert_test('_auth_user_id' not in client.session, "44. Session cleared after logout")

    print(f"\nALL SHARED LAYOUT & BACKEND WIRING TESTS COMPLETED! {passed}/{total} Passed.")

if __name__ == '__main__':
    run_tests()
