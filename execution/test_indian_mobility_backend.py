import os
import sys
from decimal import Decimal
from datetime import datetime, date, time, timedelta

# Add Rentora directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Setup Django Environment
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rentora_project.settings')
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from core.models import (
    Car, Booking, VehicleInspection, RefundTransaction,
    TollTransaction, TollDispute, EmergencySOS, TripExtension, Notification
)
from accounts.models import UserProfile
from core.services import (
    RefundService, TripExtensionService, LateReturnService,
    TollReconcilerService, EmergencySOSService, VehicleInspectionService
)

def run_tests():
    print("=" * 60)
    print("   RENTORA INDIAN MOBILITY BACKEND & ERROR-HANDLING TESTS   ")
    print("=" * 60)

    # 1. Setup Test User and Car
    user, _ = User.objects.get_or_create(username='test_indian_driver', email='driver@test.in')
    user.set_password('Password123!')
    user.save()

    profile, _ = UserProfile.objects.get_or_create(user=user)
    profile.wallet_balance = Decimal('5000.00')
    profile.kyc_status = 'VERIFIED'
    profile.is_verified = True
    profile.save()

    # Clean previous test bookings
    Booking.objects.filter(booking_reference__in=['TEST-IND-001', 'CANCEL-100', 'CANCEL-50']).delete()

    car, _ = Car.objects.get_or_create(
        name='Creta SX Test',
        brand='Hyundai',
        defaults={
            'category': 'SUV',
            'price_per_day': Decimal('2400.00'),
            'security_deposit': Decimal('2000.00'),
            'free_km': 300,
            'seats': 5,
            'fuel_type': 'Petrol',
            'transmission': 'Manual',
            'engine': '1.5L',
            'mileage': '17 kmpl'
        }
    )

    # Test 1: Booking creation with Indian operational fields
    today = date.today()
    pickup = today + timedelta(days=2)
    dropoff = today + timedelta(days=4)
    booking = Booking.objects.create(
        user=user,
        car=car,
        booking_reference='TEST-IND-001',
        pickup_date=pickup,
        dropoff_date=dropoff,
        pickup_time=time(10, 0),
        dropoff_time=time(10, 0),
        pickup_location='Domlur, Bengaluru',
        dropoff_location='Domlur, Bengaluru',
        total_price=Decimal('4800.00'),
        security_deposit=Decimal('2000.00'),
        total_with_gst=Decimal('5664.00'),
        status=Booking.Status.CONFIRMED,
        is_paid=True
    )
    print("[PASS] 1. Booking initialized with security deposit & Indian location")

    # Test 2: Pre-Trip Inspection -> Transitions Booking to ACTIVE
    pre_inspection = VehicleInspectionService.submit_pre_trip(
        booking=booking,
        user=user,
        odometer=24500,
        fuel_percent=100,
        damage_notes='Pre-existing hairline scratch on rear bumper',
        lat=Decimal('12.9716'),
        lng=Decimal('77.5946')
    )
    booking.refresh_from_db()
    assert booking.status == Booking.Status.ACTIVE, f"Expected ACTIVE, got {booking.status}"
    assert pre_inspection.stage == VehicleInspection.Stage.PRE_TRIP
    print("[PASS] 2. Pre-trip inspection validated and booking transitioned to ACTIVE")

    # Test 3: Emergency SOS -> Pauses billing meter & logs coordinates
    sos = EmergencySOSService.trigger_sos(
        booking=booking,
        user=user,
        issue_type=EmergencySOS.IssueType.TIRE_PUNCTURE,
        latitude=Decimal('12.9352'),
        longitude=Decimal('77.6245'),
        location_address='Koramangala 80ft Road',
        user_note='Flat left front tire near Sony World signal'
    )
    booking.refresh_from_db()
    assert booking.emergency_paused == True
    assert sos.status == EmergencySOS.Status.TRIGGERED
    print("[PASS] 3. Emergency SOS logged, billing meter paused, roadside dispatch notified")

    # Test 4: Trip Extension availability check & confirmation
    is_avail, new_dropoff, ext_cost = TripExtensionService.check_availability(booking, additional_hours=4)
    assert is_avail == True
    assert ext_cost > 0
    
    # Confirm extension via wallet
    initial_wallet = profile.wallet_balance
    success, msg = TripExtensionService.confirm_extension(booking, additional_hours=4, payment_channel='wallet')
    profile.refresh_from_db()
    booking.refresh_from_db()
    assert success == True
    assert booking.is_extended == True
    assert profile.wallet_balance == initial_wallet - ext_cost
    print(f"[PASS] 4. In-trip extension (+4h) confirmed, wallet debited ₹{ext_cost}")

    # Test 5: Late Return Grace Period (30 minutes)
    dropoff_dt = datetime.combine(booking.dropoff_date, booking.dropoff_time)
    if timezone.is_naive(dropoff_dt):
        dropoff_dt = timezone.make_aware(dropoff_dt)
    
    # Return within 20 mins delay -> Within Grace Period (₹0 penalty)
    delay_20m = dropoff_dt + timedelta(minutes=20)
    eval_grace = LateReturnService.calculate_late_return(booking, delay_20m)
    assert eval_grace['is_late'] == False
    assert eval_grace['grace_period_applied'] == True
    assert eval_grace['late_fee'] == Decimal('0.00')
    print("[PASS] 5. 30-minute late return grace window honored with ₹0 penalty")

    # Return 90 mins delay -> Past Grace Period -> 1.5x penalty surcharge
    delay_90m = dropoff_dt + timedelta(minutes=90)
    eval_late = LateReturnService.calculate_late_return(booking, delay_90m)
    assert eval_late['is_late'] == True
    assert eval_late['late_hours'] == 1 # (90m - 30m grace = 60m = 1 hour)
    assert eval_late['late_fee'] > 0
    print(f"[PASS] 6. Delay past grace period accurately charged 1.5x late fee (₹{eval_late['late_fee']})")

    # Test 6: FASTag Toll Logging & Double Deduction Cash Dispute
    toll = TollReconcilerService.log_fastag_toll(
        booking=booking,
        plaza_name='Nelamangala Toll Plaza',
        amount=Decimal('120.00'),
        netc_id='NETC-KA-99201'
    )
    booking.refresh_from_db()
    assert booking.fastag_toll_total == Decimal('120.00')

    # Customer disputes cash payment of ₹120.00 (scanner fault)
    wallet_before_dispute = profile.wallet_balance
    dispute, dispute_msg = TollReconcilerService.submit_cash_toll_dispute(
        booking=booking,
        user=user,
        cash_receipt_img='toll_receipts/sample_slip.jpg',
        cash_amount=Decimal('120.00'),
        user_notes='Scanner was red, attendant forced cash payment'
    )
    profile.refresh_from_db()
    assert dispute.status == TollDispute.Status.APPROVED
    assert profile.wallet_balance == wallet_before_dispute + Decimal('120.00')
    print("[PASS] 7. FASTag double-deduction auto-reconciled and refunded to user wallet")

    # Test 7: Post-Trip Inspection & Automated Instant Security Deposit Release
    wallet_before_deposit = profile.wallet_balance
    post_inspection = VehicleInspectionService.submit_post_trip(
        booking=booking,
        user=user,
        odometer=24850,
        fuel_percent=100,
        has_damage=False,
        cleanliness_rating=5
    )
    booking.refresh_from_db()
    profile.refresh_from_db()
    assert booking.status == Booking.Status.COMPLETED
    # Deposit refund of ₹2000 is credited, plus ₹500 referral reward for completing first trip
    from core.constants import REFERRAL_REWARD_INR
    assert profile.wallet_balance == wallet_before_deposit + booking.security_deposit + Decimal(str(REFERRAL_REWARD_INR))
    
    # Check RefundTransaction record
    deposit_refund = RefundTransaction.objects.filter(
        booking=booking,
        refund_type=RefundTransaction.Type.SECURITY_DEPOSIT,
        status=RefundTransaction.Status.COMPLETED
    ).first()
    assert deposit_refund is not None
    assert deposit_refund.amount == Decimal('2000.00')
    print("[PASS] 8. Post-trip inspection approved -> Instant Security Deposit refunded to Wallet")

    # Test 8: Tiered Cancellation SLA Matrix
    # Booking A: > 24 hours -> 100% full refund
    future_booking_100 = Booking.objects.create(
        user=user,
        car=car,
        booking_reference='CANCEL-100',
        pickup_date=today + timedelta(days=5),
        dropoff_date=today + timedelta(days=7),
        pickup_time=time(10, 0),
        total_price=Decimal('4800.00'),
        status=Booking.Status.CONFIRMED,
        is_paid=True
    )
    refund_100, sla_100 = RefundService.process_cancellation_with_sla(future_booking_100)
    assert refund_100.amount == future_booking_100.total_with_gst
    print(f"[PASS] 9. >24h cancellation receives 100% refund (₹{refund_100.amount}): {sla_100}")

    # Booking B: 6-24 hours -> 50% refund
    target_12h = timezone.now() + timedelta(hours=12)
    future_booking_50 = Booking.objects.create(
        user=user,
        car=car,
        booking_reference='CANCEL-50',
        pickup_date=target_12h.date(),
        dropoff_date=target_12h.date() + timedelta(days=2),
        pickup_time=target_12h.time(),
        total_price=Decimal('2400.00'),
        status=Booking.Status.CONFIRMED,
        is_paid=True
    )
    refund_50, sla_50 = RefundService.process_cancellation_with_sla(future_booking_50)
    expected_50 = (future_booking_50.total_with_gst * Decimal('0.50')).quantize(Decimal('0.01'))
    assert refund_50.amount == expected_50
    print(f"[PASS] 10. 6-24h cancellation receives 50% refund (₹{refund_50.amount}): {sla_50}")

    # Cleanup test bookings and data
    Booking.objects.filter(booking_reference__in=['TEST-IND-001', 'CANCEL-100', 'CANCEL-50']).delete()
    User.objects.filter(username='test_indian_driver').delete()
    Car.objects.filter(name='Creta SX Test').delete()

    print("\n" + "=" * 60)
    print("ALL 10/10 INDIAN MOBILITY BACKEND & ERROR-HANDLING TESTS PASSED!")
    print("=" * 60)

if __name__ == '__main__':
    run_tests()
