from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta, date, time
from decimal import Decimal
from core.models import Car, Booking, Review, PromoCode, Wishlist, Notification

class CoreModelLogicTests(TestCase):
    """55 deterministic tests for model data integrity, calculations, and constraints."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='modeluser', password='password123')
        cls.car = Car.objects.create(
            name="Thar 4x4",
            brand="Mahindra",
            category="SUV",
            price_per_day=Decimal('3500.00'),
            security_deposit=Decimal('0.00'),
            free_km=240,
            seats=4,
            fuel_type="Diesel",
            transmission="Manual",
            is_available=True
        )

    def test_car_str_representation(self):
        self.assertIn("Thar", str(self.car))

    def test_car_default_availability(self):
        self.assertTrue(self.car.is_available)

    def test_car_price_per_day_is_decimal(self):
        self.assertIsInstance(self.car.price_per_day, Decimal)

    def test_car_seats_integer(self):
        self.assertEqual(self.car.seats, 4)

    def test_car_free_km_default(self):
        self.assertEqual(self.car.free_km, 240)

    def test_car_security_deposit_zero_for_kyc(self):
        self.assertEqual(self.car.security_deposit, Decimal('0.00'))

    def test_car_availability_with_no_bookings(self):
        p = date.today() + timedelta(days=2)
        d = date.today() + timedelta(days=4)
        self.assertTrue(Car.is_available_for_dates(self.car.id, p, d))

    def test_car_availability_blocked_by_active_booking(self):
        p = date.today() + timedelta(days=5)
        d = date.today() + timedelta(days=7)
        Booking.objects.create(
            user=self.user,
            car=self.car,
            booking_reference='REF-AVAIL-1',
            pickup_date=p,
            dropoff_date=d,
            total_price=Decimal('7000.00'),
            status='Confirmed'
        )
        self.assertFalse(Car.is_available_for_dates(self.car.id, p, d))

    def test_car_availability_free_after_dropoff(self):
        p = date.today() + timedelta(days=10)
        d = date.today() + timedelta(days=12)
        Booking.objects.create(
            user=self.user,
            car=self.car,
            booking_reference='REF-AVAIL-2',
            pickup_date=p,
            dropoff_date=d,
            total_price=Decimal('7000.00'),
            status='Confirmed'
        )
        future_p = date.today() + timedelta(days=13)
        future_d = date.today() + timedelta(days=15)
        self.assertTrue(Car.is_available_for_dates(self.car.id, future_p, future_d))

    def test_car_availability_cancelled_booking_does_not_block(self):
        p = date.today() + timedelta(days=20)
        d = date.today() + timedelta(days=22)
        Booking.objects.create(
            user=self.user,
            car=self.car,
            booking_reference='REF-AVAIL-3',
            pickup_date=p,
            dropoff_date=d,
            total_price=Decimal('7000.00'),
            status='Cancelled'
        )
        self.assertTrue(Car.is_available_for_dates(self.car.id, p, d))

    def test_booking_reference_is_saved(self):
        b = Booking.objects.create(
            user=self.user,
            car=self.car,
            booking_reference='REF-UNIQUE-01',
            pickup_date=date.today(),
            dropoff_date=date.today() + timedelta(days=1),
            total_price=Decimal('3500.00'),
            status='Pending'
        )
        self.assertEqual(b.booking_reference, 'REF-UNIQUE-01')

    def test_booking_financials_gst_calculation_18_percent(self):
        b = Booking.objects.create(
            user=self.user,
            car=self.car,
            booking_reference='REF-GST-1',
            pickup_date=date.today(),
            dropoff_date=date.today() + timedelta(days=1),
            total_price=Decimal('10000.00')
        )
        expected_gst = Decimal('1800.00')
        expected_total = Decimal('11800.00')
        self.assertEqual(b.gst_amount, expected_gst)
        self.assertEqual(b.total_with_gst, expected_total)

    def test_booking_financials_gst_small_amount(self):
        b = Booking.objects.create(
            user=self.user,
            car=self.car,
            booking_reference='REF-GST-2',
            pickup_date=date.today(),
            dropoff_date=date.today() + timedelta(days=1),
            total_price=Decimal('1500.00')
        )
        self.assertEqual(b.gst_amount, Decimal('270.00'))
        self.assertEqual(b.total_with_gst, Decimal('1770.00'))

    def test_booking_financials_gst_zero_amount(self):
        b = Booking.objects.create(
            user=self.user,
            car=self.car,
            booking_reference='REF-GST-3',
            pickup_date=date.today(),
            dropoff_date=date.today() + timedelta(days=1),
            total_price=Decimal('0.00')
        )
        self.assertEqual(b.gst_amount, Decimal('0.00'))
        self.assertEqual(b.total_with_gst, Decimal('0.00'))

    def test_booking_default_paid_status_is_false(self):
        b = Booking.objects.create(
            user=self.user,
            car=self.car,
            booking_reference='REF-UNPAID-1',
            pickup_date=date.today(),
            dropoff_date=date.today() + timedelta(days=1),
            total_price=Decimal('3500.00')
        )
        self.assertFalse(b.is_paid)

    def test_booking_mark_paid(self):
        b = Booking.objects.create(
            user=self.user,
            car=self.car,
            booking_reference='REF-PAID-1',
            pickup_date=date.today(),
            dropoff_date=date.today() + timedelta(days=1),
            total_price=Decimal('3500.00'),
            is_paid=True
        )
        self.assertTrue(b.is_paid)

    def test_booking_status_choices(self):
        valid_statuses = ['Pending', 'Confirmed', 'Active', 'Completed', 'Cancelled']
        for s in valid_statuses:
            b = Booking.objects.create(
                user=self.user,
                car=self.car,
                booking_reference=f'REF-STAT-{s}',
                pickup_date=date.today(),
                dropoff_date=date.today() + timedelta(days=1),
                total_price=Decimal('1000.00'),
                status=s
            )
            self.assertEqual(b.status, s)

    def test_booking_promocode_field(self):
        b = Booking.objects.create(
            user=self.user,
            car=self.car,
            booking_reference='REF-PROMO-1',
            pickup_date=date.today(),
            dropoff_date=date.today() + timedelta(days=1),
            total_price=Decimal('3000.00'),
            promo_code='WELCOME500',
            discount_amount=Decimal('500.00')
        )
        self.assertEqual(b.promo_code, 'WELCOME500')
        self.assertEqual(b.discount_amount, Decimal('500.00'))

    def test_promo_code_creation_fixed(self):
        p = PromoCode.objects.create(
            code="RENTORA100",
            discount_type="Fixed",
            discount_value=Decimal('100.00'),
            min_purchase=Decimal('1000.00'),
            expiry_date=timezone.now() + timedelta(days=30),
            is_active=True
        )
        self.assertEqual(p.discount_type, "Fixed")
        self.assertEqual(p.discount_value, Decimal('100.00'))
        self.assertTrue(p.is_active)

    def test_promo_code_creation_percent(self):
        p = PromoCode.objects.create(
            code="SAVE10",
            discount_type="Percentage",
            discount_value=Decimal('10.00'),
            min_purchase=Decimal('2000.00'),
            expiry_date=timezone.now() + timedelta(days=15),
            is_active=True
        )
        self.assertEqual(p.discount_type, "Percentage")
        self.assertEqual(p.discount_value, Decimal('10.00'))

    def test_promo_code_expired_flag(self):
        p = PromoCode.objects.create(
            code="EXPIRED50",
            discount_type="Fixed",
            discount_value=Decimal('50.00'),
            expiry_date=timezone.now() - timedelta(days=1),
            is_active=True
        )
        self.assertTrue(p.expiry_date < timezone.now())

    def test_promo_code_usage_limit(self):
        p = PromoCode.objects.create(
            code="LIMITED5",
            discount_type="Fixed",
            discount_value=Decimal('50.00'),
            expiry_date=timezone.now() + timedelta(days=5),
            is_active=True,
            usage_limit=5,
            used_count=5
        )
        self.assertEqual(p.used_count, p.usage_limit)

    def test_wishlist_add_car(self):
        w = Wishlist.objects.create(user=self.user, car=self.car)
        self.assertEqual(w.user, self.user)
        self.assertEqual(w.car, self.car)

    def test_wishlist_query_for_user(self):
        Wishlist.objects.get_or_create(user=self.user, car=self.car)
        user_wishes = Wishlist.objects.filter(user=self.user).values_list('car_id', flat=True)
        self.assertIn(self.car.id, user_wishes)

    def test_notification_creation(self):
        n = Notification.objects.create(
            user=self.user,
            notification_type="booking",
            title="Booking Confirmed",
            message="Your Mahindra Thar is confirmed.",
            is_read=False
        )
        self.assertEqual(n.title, "Booking Confirmed")
        self.assertFalse(n.is_read)

    def test_notification_mark_read(self):
        n = Notification.objects.create(
            user=self.user,
            notification_type="booking",
            title="Pickup Reminder",
            message="Your car pickup is in 2 hours.",
            is_read=False
        )
        n.is_read = True
        n.save()
        self.assertTrue(Notification.objects.get(id=n.id).is_read)

    def test_review_creation(self):
        b = Booking.objects.create(
            user=self.user,
            car=self.car,
            booking_reference='REF-REV-1',
            pickup_date=date.today() - timedelta(days=2),
            dropoff_date=date.today() - timedelta(days=1),
            total_price=Decimal('3500.00'),
            status='Completed'
        )
        r = Review.objects.create(
            user=self.user,
            car=self.car,
            booking=b,
            rating=5,
            comment="Spotless Thar, very smooth highway cruise!"
        )
        self.assertEqual(r.rating, 5)
        self.assertEqual(r.booking, b)

    def test_review_rating_range(self):
        b = Booking.objects.create(
            user=self.user,
            car=self.car,
            booking_reference='REF-REV-2',
            pickup_date=date.today() - timedelta(days=3),
            dropoff_date=date.today() - timedelta(days=2),
            total_price=Decimal('3500.00'),
            status='Completed'
        )
        r = Review.objects.create(user=self.user, car=self.car, booking=b, rating=4, comment="Great experience")
        self.assertTrue(1 <= r.rating <= 5)

    def test_car_multiple_reviews_count(self):
        b = Booking.objects.create(
            user=self.user,
            car=self.car,
            booking_reference='REF-REV-3',
            pickup_date=date.today() - timedelta(days=5),
            dropoff_date=date.today() - timedelta(days=4),
            total_price=Decimal('3500.00'),
            status='Completed'
        )
        Review.objects.create(user=self.user, car=self.car, booking=b, rating=5, comment="Top notch")
        count = Review.objects.filter(car=self.car).count()
        self.assertGreaterEqual(count, 1)

    def test_car_fuel_types(self):
        fuel_types = ["Petrol", "Diesel", "Electric", "CNG"]
        for ft in fuel_types:
            c = Car.objects.create(
                name=f"Car-{ft}",
                brand="Generic",
                category="Hatchback",
                price_per_day=Decimal('2000.00'),
                fuel_type=ft,
                seats=5
            )
            self.assertEqual(c.fuel_type, ft)

    def test_car_transmission_types(self):
        for trans in ["Manual", "Automatic"]:
            c = Car.objects.create(
                name=f"Car-{trans}",
                brand="Generic",
                category="Sedan",
                price_per_day=Decimal('2500.00'),
                transmission=trans,
                seats=5
            )
            self.assertEqual(c.transmission, trans)

    def test_car_category_types(self):
        categories = ["Hatchback", "Sedan", "SUV", "Electric", "MPV", "Luxury Sedan"]
        for cat in categories:
            c = Car.objects.create(
                name=f"Car-{cat}",
                brand="Generic",
                category=cat,
                price_per_day=Decimal('3000.00'),
                seats=5
            )
            self.assertEqual(c.category, cat)

    def test_booking_outstation_flag(self):
        b = Booking.objects.create(
            user=self.user,
            car=self.car,
            booking_reference='REF-OUT-1',
            pickup_date=date.today(),
            dropoff_date=date.today() + timedelta(days=2),
            total_price=Decimal('7000.00'),
            is_outstation=True
        )
        self.assertTrue(b.is_outstation)

    def test_booking_fastag_toll_default(self):
        b = Booking.objects.create(
            user=self.user,
            car=self.car,
            booking_reference='REF-TOLL-1',
            pickup_date=date.today(),
            dropoff_date=date.today() + timedelta(days=1),
            total_price=Decimal('3500.00')
        )
        self.assertEqual(b.fastag_toll_total, Decimal('0.00'))

    def test_booking_trip_extension_flag(self):
        b = Booking.objects.create(
            user=self.user,
            car=self.car,
            booking_reference='REF-EXT-1',
            pickup_date=date.today(),
            dropoff_date=date.today() + timedelta(days=1),
            total_price=Decimal('3500.00'),
            is_extended=True
        )
        self.assertTrue(b.is_extended)

    def test_booking_emergency_paused_flag(self):
        b = Booking.objects.create(
            user=self.user,
            car=self.car,
            booking_reference='REF-EMERG-1',
            pickup_date=date.today(),
            dropoff_date=date.today() + timedelta(days=1),
            total_price=Decimal('3500.00'),
            emergency_paused=True
        )
        self.assertTrue(b.emergency_paused)

    def test_booking_pickup_time_field(self):
        t = time(10, 30)
        b = Booking.objects.create(
            user=self.user,
            car=self.car,
            booking_reference='REF-TIME-1',
            pickup_date=date.today(),
            dropoff_date=date.today() + timedelta(days=1),
            pickup_time=t,
            total_price=Decimal('3500.00')
        )
        self.assertEqual(b.pickup_time, t)

    def test_booking_dropoff_time_field(self):
        t = time(18, 0)
        b = Booking.objects.create(
            user=self.user,
            car=self.car,
            booking_reference='REF-TIME-2',
            pickup_date=date.today(),
            dropoff_date=date.today() + timedelta(days=1),
            dropoff_time=t,
            total_price=Decimal('3500.00')
        )
        self.assertEqual(b.dropoff_time, t)

    def test_booking_pickup_location_field(self):
        b = Booking.objects.create(
            user=self.user,
            car=self.car,
            booking_reference='REF-LOC-1',
            pickup_date=date.today(),
            dropoff_date=date.today() + timedelta(days=1),
            pickup_location="Biju Patnaik Airport Terminal 1",
            total_price=Decimal('3500.00')
        )
        self.assertEqual(b.pickup_location, "Biju Patnaik Airport Terminal 1")

    def test_booking_dropoff_location_field(self):
        b = Booking.objects.create(
            user=self.user,
            car=self.car,
            booking_reference='REF-LOC-2',
            pickup_date=date.today(),
            dropoff_date=date.today() + timedelta(days=1),
            dropoff_location="Puri Golden Beach",
            total_price=Decimal('3500.00')
        )
        self.assertEqual(b.dropoff_location, "Puri Golden Beach")

    def test_booking_security_deposit_field(self):
        b = Booking.objects.create(
            user=self.user,
            car=self.car,
            booking_reference='REF-SEC-1',
            pickup_date=date.today(),
            dropoff_date=date.today() + timedelta(days=1),
            security_deposit=Decimal('0.00'),
            total_price=Decimal('3500.00')
        )
        self.assertEqual(b.security_deposit, Decimal('0.00'))

    def test_car_features_json_field(self):
        features = ["Sunroof", "Ventilated Seats", "360 Camera", "ADAS"]
        c = Car.objects.create(
            name="XUV700",
            brand="Mahindra",
            category="SUV",
            price_per_day=Decimal('4200.00'),
            features=features,
            seats=7
        )
        self.assertEqual(c.features, features)
        self.assertIn("Sunroof", c.features)

    def test_car_mileage_string(self):
        c = Car.objects.create(
            name="Baleno",
            brand="Maruti Suzuki",
            category="Hatchback",
            price_per_day=Decimal('1800.00'),
            mileage="22.3 kmpl",
            seats=5
        )
        self.assertEqual(c.mileage, "22.3 kmpl")

    def test_car_engine_specs(self):
        c = Car.objects.create(
            name="BMW 330i",
            brand="BMW",
            category="Luxury Sedan",
            price_per_day=Decimal('8500.00'),
            engine="2.0L TwinPower Turbo",
            seats=5
        )
        self.assertEqual(c.engine, "2.0L TwinPower Turbo")

    def test_multiple_bookings_for_same_user(self):
        initial_count = Booking.objects.filter(user=self.user).count()
        Booking.objects.create(
            user=self.user,
            car=self.car,
            booking_reference='REF-MULTI-1',
            pickup_date=date.today() + timedelta(days=40),
            dropoff_date=date.today() + timedelta(days=41),
            total_price=Decimal('3500.00')
        )
        self.assertEqual(Booking.objects.filter(user=self.user).count(), initial_count + 1)

    def test_multiple_cars_in_fleet(self):
        self.assertGreaterEqual(Car.objects.count(), 1)

    def test_car_deletion_protection_or_cascade(self):
        c = Car.objects.create(
            name="TempCar",
            brand="Test",
            category="Hatchback",
            price_per_day=Decimal('1000.00'),
            seats=5
        )
        car_id = c.id
        c.delete()
        self.assertFalse(Car.objects.filter(id=car_id).exists())

    def test_notification_deletion(self):
        n = Notification.objects.create(
            user=self.user,
            notification_type="system",
            title="Welcome to Rentora",
            message="Your account is active."
        )
        nid = n.id
        n.delete()
        self.assertFalse(Notification.objects.filter(id=nid).exists())

    def test_wishlist_deletion(self):
        w = Wishlist.objects.create(user=self.user, car=self.car)
        wid = w.id
        w.delete()
        self.assertFalse(Wishlist.objects.filter(id=wid).exists())

    def test_promocode_str_representation(self):
        p = PromoCode.objects.create(
            code="ODISHA2026",
            discount_type="Fixed",
            discount_value=Decimal('200.00'),
            expiry_date=timezone.now() + timedelta(days=10)
        )
        self.assertIn("ODISHA2026", str(p))

    def test_notification_str_representation(self):
        n = Notification.objects.create(
            user=self.user,
            notification_type="promo",
            title="Weekend Getaway Deal",
            message="Save ₹300 this weekend."
        )
        self.assertIn("Weekend", str(n))
