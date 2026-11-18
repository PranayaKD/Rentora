import os
import sys
import json
from pathlib import Path

# Add project root to sys.path
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
from core.models import Car

def run_tests():
    print("==================================================")
    print("  RENTORA - ZOOMCAR REVERSE-ENGINEER VERIFICATION ")
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

    # TEST 1: Homepage renders with Zoomcar reverse-engineered elements
    resp = client.get('/')
    assert_test(resp.status_code == 200, "1. Homepage returns HTTP 200")
    content = resp.content.decode('utf-8')
    assert_test("Self-Drive Car Rental in" in content or "Bengaluru" in content, "2. Homepage contains City Selector")
    assert_test("Daily Drives" in content and "Subscription" in content, "3. Homepage contains Zoomcar Product Mode switchers")
    assert_test("25,000+ Verified Cars" in content or "25,000+" in content, "4. Homepage contains Live Trust Ticker")
    assert_test("100% Freedom" in content and "Doorstep Delivery" in content, "5. Homepage contains 'Why Rentora' value props")
    hiw_resp = client.get('/how-it-works/')
    assert_test(hiw_resp.status_code == 200 and "How Rentora Works" in hiw_resp.content.decode('utf-8') and "Compare KM Plans" in hiw_resp.content.decode('utf-8'), "6. Dedicated /how-it-works/ page contains 5-step journey")

    # TEST 2: Cars Search Catalog renders with mobile-first filters
    resp = client.get('/cars/')
    assert_test(resp.status_code == 200, "7. /cars/ catalog returns HTTP 200")
    cars_content = resp.content.decode('utf-8')
    assert_test("300 km incl." in cars_content and "Unlimited km" in cars_content, "8. Contains Floating Sticky KM Package Switcher")
    assert_test("Guest Favorite" in cars_content, "9. Contains Guest Favorite / Super Host filter badges")
    assert_test("rentora-car-card" in cars_content, "10. Renders Zoomcar-style car cards")

    # TEST 3: Category filter for SUV
    resp_suv = client.get('/cars/?category=SUV')
    assert_test(resp_suv.status_code == 200, "11. /cars/?category=SUV returns HTTP 200")
    suv_cars = resp_suv.context['cars']
    assert_test(all('SUV' in c.category for c in suv_cars), "12. All returned vehicles match SUV category")

    # TEST 4: Transmission filter for Automatic
    resp_auto = client.get('/cars/?transmission=Automatic')
    assert_test(resp_auto.status_code == 200, "13. /cars/?transmission=Automatic returns HTTP 200")
    auto_cars = resp_auto.context['cars']
    assert_test(all('Auto' in c.transmission for c in auto_cars), "14. All returned vehicles match Automatic transmission")

    # TEST 5: Car Detail Page renders with Zoomcar parity elements
    first_car = Car.objects.filter(brand="Maruti Suzuki", name__icontains="Swift").first() or Car.objects.first()
    assert_test(first_car is not None, "15. Seeded car found in database")
    resp_detail = client.get(f'/cars/{first_car.id}/')
    assert_test(resp_detail.status_code == 200, "16. /cars/<id>/ detail page returns HTTP 200")
    detail_content = resp_detail.content.decode('utf-8')
    assert_test("Damage Protection Cover" in detail_content, "17. Detail page contains Damage Protection selector")
    assert_test("Doorstep Delivery" in detail_content, "18. Detail page contains Doorstep Delivery status")
    assert_test("Book Now" in detail_content or "Proceed to Book" in detail_content, "19. Detail page contains Mobile Sticky Booking Bar")

    # TEST 6: Instant Mobile OTP Request & Verification
    test_phone = "+919876543210"
    otp_req = client.post('/auth/login/otp/request/', 
                          data=json.dumps({"phone": test_phone}), 
                          content_type='application/json')
    assert_test(otp_req.status_code == 200 and otp_req.json().get('success') is True, "20. OTP send API successfully triggers")

    otp_verify = client.post('/auth/login/otp/verify/', 
                            data=json.dumps({"phone": test_phone, "code": "123456"}), 
                            content_type='application/json')
    assert_test(otp_verify.status_code == 200 and otp_verify.json().get('success') is True, "21. OTP verify API logs user in with auto-signup")

    # TEST 7: Pricing properties & calculation verification
    swift = Car.objects.filter(brand="Maruti Suzuki", name="Swift 2026").first() or Car.objects.filter(brand="Maruti Suzuki", name__icontains="Swift").order_by('id').first()
    if swift:
        assert_test(swift.hourly_rate == 80, "22. Maruti Swift hourly rate is Rs. 80/hr (300 km)")
        assert_test(swift.hourly_rate_unlimited == 96, "23. Maruti Swift hourly rate is Rs. 96/hr (Unlimited km)")
        assert_test(swift.price_per_day == 1920, "24. Maruti Swift daily rate is Rs. 1,920/day (300 km)")
        assert_test(swift.price_per_day_unlimited == 2304, "25. Maruti Swift daily rate is Rs. 2,304/day (Unlimited km)")

    # TEST 8: Checkout & Payment Page with Zoomcar Parity
    session = client.session
    session['booking_car_id'] = first_car.id
    session['pickup_date'] = '2026-12-01 10:00'
    session['dropoff_date'] = '2026-12-02 10:00'
    session['pickup_location'] = 'Indiranagar, Bengaluru'
    session['dropoff_location'] = 'Koramangala, Bengaluru'
    session.save()

    resp_pay = client.get('/booking/payment/')
    assert_test(resp_pay.status_code == 200, "26. /booking/payment/ returns HTTP 200")
    pay_content = resp_pay.content.decode('utf-8')
    assert_test("Plan Included" in pay_content and "Fuel Policy" in pay_content, "27. Payment page contains KM Plan & Fuel Policy breakdown")
    assert_test("Damage Protection" in pay_content, "28. Payment page contains Damage Protection cover itemization")
    assert_test("mobile-summary-total" in pay_content, "29. Payment page contains Mobile Sticky Checkout Bar")
    assert_test("Pay Now" in pay_content or "Proceed to Secure Payment" in pay_content, "30. Payment page contains high-contrast mobile pay action")

    # TEST 9: New UI Enhancements (Phases 1-3)
    # A. Homepage Explore by Category & Broken JS removal
    assert_test("Explore by Category" in content, "31. Homepage contains 'Explore by Category' section")
    assert_test("Hatchbacks" in content and "SUVs & 4x4" in content and "Electric (EVs)" in content, "32. Homepage contains all Zoomcar vehicle categories")
    assert_test("Popular Brands" in content, "33. Homepage contains Popular Brands quick chips")
    assert_test("toggleDriver" not in content, "34. Broken toggleDriver() function cleanly removed from homepage JS")

    # B. Car Detail Page Trust Badges & Touch Gallery
    assert_test("₹0 Deposit Option" in detail_content, "35. Car detail contains '₹0 Deposit Option' badge")
    assert_test("Same-to-Same Fuel" in detail_content, "36. Car detail contains 'Same-to-Same Fuel' badge")
    assert_test("Free Cancellation" in detail_content, "37. Car detail contains 'Free Cancellation' badge")
    assert_test("detail-gallery-container" in detail_content, "38. Car detail contains touch-swipeable gallery container")

    # C. Booking Flow 1-Tap & Duration Pill
    user = User.objects.filter(username__icontains=test_phone).first() or User.objects.first()
    if user:
        client.force_login(user)

    resp_b1 = client.get(f'/booking/{first_car.id}/', follow=True)
    assert_test(resp_b1.status_code == 200, "39. Booking Step 1 returns HTTP 200")
    b1_content = resp_b1.content.decode('utf-8')
    assert_test("diff-dropoff-toggle" in b1_content, "40. Booking Step 1 contains 'Drop-off at different location' toggle")
    assert_test("Continue to Dates" in b1_content, "41. Booking Step 1 contains 1-tap 'Continue to Dates' CTA")

    resp_b2 = client.get('/booking/dates/', follow=True)
    assert_test(resp_b2.status_code == 200, "42. Booking Step 2 returns HTTP 200")
    b2_content = resp_b2.content.decode('utf-8')
    assert_test("booking-duration-badge" in b2_content, "43. Booking Step 2 contains live trip duration badge")

    # D. In-Page Promo Recalculation logic check
    assert_test("/api/promo/apply/" in pay_content and "discount-row" in pay_content, "44. Payment page contains dynamic in-page promo calculation")

    print(f"\nALL TESTS COMPLETED! {passed}/{total} Passed.")

if __name__ == '__main__':
    run_tests()
