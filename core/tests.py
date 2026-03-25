from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from core.models import Car, Booking
from accounts.models import UserProfile

class CarModelTest(TestCase):
    def setUp(self):
        self.car = Car.objects.create(
            name="Thar",
            brand="Mahindra",
            category="SUV",
            price_per_day=Decimal('5000.00'),
            seats=4,
            fuel_type="Diesel",
            is_available=True
        )

    def test_car_availability_logic(self):
        """Test the overlap logic for car availability."""
        pickup = timezone.now() + timedelta(days=1)
        dropoff = timezone.now() + timedelta(days=3)
        
        # Initially available
        self.assertTrue(Car.is_available_for_dates(self.car.id, pickup, dropoff))
        
        # Create a conflicting booking
        user = User.objects.create_user(username='testuser', password='password')
        Booking.objects.create(
            user=user,
            car=self.car,
            pickup_date=pickup,
            dropoff_date=dropoff,
            total_price=Decimal('10000.00'),
            status='Pending',
            booking_reference='TEST-REF-1'
        )
        
        # Now should be unavailable for same dates
        self.assertFalse(Car.is_available_for_dates(self.car.id, pickup, dropoff))
        
        # Should be available for non-overlapping dates
        future_pickup = timezone.now() + timedelta(days=5)
        future_dropoff = timezone.now() + timedelta(days=7)
        self.assertTrue(Car.is_available_for_dates(self.car.id, future_pickup, future_dropoff))

class BookingModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='traveller', password='password')
        self.car = Car.objects.create(
            name="Swift",
            brand="Maruti Suzuki",
            category="Hatchback",
            price_per_day=Decimal('2000.00'),
            seats=5,
            fuel_type="Petrol"
        )

    def test_booking_financials(self):
        """Test that GST and total_with_gst are calculated correctly on save."""
        booking = Booking.objects.create(
            user=self.user,
            car=self.car,
            pickup_date=timezone.now(),
            dropoff_date=timezone.now() + timedelta(days=2),
            total_price=Decimal('4000.00'),
            booking_reference='FIN-TEST-1'
        )
        
        # GST is 18%
        expected_gst = Decimal('4000.00') * Decimal('0.18')
        expected_total = Decimal('4000.00') + expected_gst
        
        self.assertEqual(booking.gst_amount, expected_gst)
        self.assertEqual(booking.total_with_gst, expected_total)

    def test_referral_reward_system(self):
        """Test that completing a booking rewards the user's wallet."""
        profile = self.user.profile
        initial_balance = profile.wallet_balance
        
        booking = Booking.objects.create(
            user=self.user,
            car=self.car,
            pickup_date=timezone.now(),
            dropoff_date=timezone.now() + timedelta(days=1),
            total_price=Decimal('2000.00'),
            status='Pending'
        )
        
        # Transition to Completed
        booking.status = 'Completed'
        booking.save()
        
        # Refresh from DB
        profile.refresh_from_db()
        # REFERRAL_REWARD_INR is 500 in constants.py
        self.assertEqual(profile.wallet_balance, initial_balance + 500)
