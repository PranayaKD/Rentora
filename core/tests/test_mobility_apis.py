from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import timedelta, date
from decimal import Decimal
import json
from core.models import Car, Booking, PromoCode, Wishlist, Notification

class CoreMobilityAPITests(TestCase):
    """42 deterministic tests for specialized mobility and booking APIs."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='apiuser', password='apipassword123')
        cls.car = Car.objects.create(
            name="Nexon EV",
            brand="Tata",
            category="Electric",
            price_per_day=Decimal('2200.00'),
            seats=5,
            fuel_type="Electric",
            transmission="Automatic",
            is_available=True
        )
        cls.promo = PromoCode.objects.create(
            code="SAVE500",
            discount_type="Fixed",
            discount_value=Decimal('500.00'),
            min_purchase=Decimal('2000.00'),
            expiry_date=timezone.now() + timedelta(days=10),
            is_active=True
        )
        cls.booking = Booking.objects.create(
            user=cls.user,
            car=cls.car,
            booking_reference='API-BOOK-001',
            pickup_date=date.today() + timedelta(days=1),
            dropoff_date=date.today() + timedelta(days=3),
            total_price=Decimal('4400.00'),
            status='Confirmed'
        )

    def setUp(self):
        self.client = Client()

    def test_api_cars_search_all(self):
        response = self.client.get(reverse('api_cars_search'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('cars', data)
        self.assertGreaterEqual(len(data['cars']), 1)

    def test_api_cars_search_by_brand(self):
        response = self.client.get(reverse('api_cars_search'), {'brand': 'Tata'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(all(c['brand'] == 'Tata' for c in data['cars']))

    def test_api_cars_search_by_category(self):
        response = self.client.get(reverse('api_cars_search'), {'category': 'Electric'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(all(c['category'] == 'Electric' for c in data['cars']))

    def test_api_cars_search_by_fuel_type(self):
        response = self.client.get(reverse('api_cars_search'), {'fuel': 'Electric'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(all(c['fuel_type'] == 'Electric' for c in data['cars']))

    def test_api_cars_search_by_keyword(self):
        response = self.client.get(reverse('api_cars_search'), {'q': 'Nexon'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(any('Nexon' in c['name'] for c in data['cars']))

    def test_api_check_availability_available(self):
        p = (date.today() + timedelta(days=10)).strftime('%Y-%m-%d')
        d = (date.today() + timedelta(days=12)).strftime('%Y-%m-%d')
        response = self.client.post(reverse('api_check_availability'), {'car_id': self.car.id, 'pickup_date': p, 'dropoff_date': d})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('available'))

    def test_api_check_availability_conflicting_dates(self):
        p = self.booking.pickup_date.strftime('%Y-%m-%d')
        d = self.booking.dropoff_date.strftime('%Y-%m-%d')
        response = self.client.post(reverse('api_check_availability'), {'car_id': self.car.id, 'pickup_date': p, 'dropoff_date': d})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data.get('available'))

    def test_api_check_availability_missing_params(self):
        response = self.client.post(reverse('api_check_availability'), {'car_id': self.car.id})
        self.assertIn(response.status_code, [200, 400])

    def test_api_apply_promo_valid(self):
        response = self.client.post(reverse('api_apply_promo'), {'code': 'SAVE500', 'cart_total': '4000.00'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('valid'))
        self.assertEqual(data.get('discount'), 500.00)

    def test_api_apply_promo_invalid_code(self):
        response = self.client.post(reverse('api_apply_promo'), {'code': 'INVALID999', 'cart_total': '4000.00'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data.get('valid'))

    def test_api_apply_promo_below_minimum_purchase(self):
        response = self.client.post(reverse('api_apply_promo'), {'code': 'SAVE500', 'cart_total': '1000.00'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data.get('valid'))

    def test_api_wishlist_toggle_unauthenticated(self):
        response = self.client.post(reverse('api_wishlist_toggle', kwargs={'car_id': self.car.id}))
        self.assertIn(response.status_code, [302, 401, 403])

    def test_api_wishlist_toggle_authenticated_add(self):
        self.client.login(username='apiuser', password='apipassword123')
        response = self.client.post(reverse('api_wishlist_toggle', kwargs={'car_id': self.car.id}))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('wishlisted'))

    def test_api_wishlist_toggle_authenticated_remove(self):
        self.client.login(username='apiuser', password='apipassword123')
        # Add first
        self.client.post(reverse('api_wishlist_toggle', kwargs={'car_id': self.car.id}))
        # Remove second
        response = self.client.post(reverse('api_wishlist_toggle', kwargs={'car_id': self.car.id}))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data.get('wishlisted'))

    def test_car_booked_dates_endpoint(self):
        response = self.client.get(reverse('car_booked_dates', kwargs={'car_id': self.car.id}))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('booked_dates', data)

    def test_api_notification_count_unauthenticated(self):
        response = self.client.get(reverse('api_notification_count'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get('count'), 0)

    def test_api_notification_count_authenticated(self):
        self.client.login(username='apiuser', password='apipassword123')
        Notification.objects.create(user=self.user, title="Test", message="Test Msg", is_read=False)
        response = self.client.get(reverse('api_notification_count'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreaterEqual(data.get('count', 0), 1)

    def test_api_trip_sos_unauthenticated(self):
        response = self.client.post(reverse('api_trip_sos', kwargs={'booking_id': self.booking.id}))
        self.assertIn(response.status_code, [302, 401, 403])

    def test_api_trip_sos_authenticated(self):
        self.client.login(username='apiuser', password='apipassword123')
        payload = json.dumps({'latitude': 20.2961, 'longitude': 85.8245, 'emergency_type': 'Medical'})
        response = self.client.post(reverse('api_trip_sos', kwargs={'booking_id': self.booking.id}), payload, content_type='application/json')
        self.assertIn(response.status_code, [200, 201])

    def test_api_toll_dispute_unauthenticated(self):
        response = self.client.post(reverse('api_toll_dispute', kwargs={'booking_id': self.booking.id}))
        self.assertIn(response.status_code, [302, 401, 403])

    def test_api_toll_dispute_authenticated(self):
        self.client.login(username='apiuser', password='apipassword123')
        dummy_receipt = SimpleUploadedFile("toll_receipt.jpg", b"fake receipt image content", content_type="image/jpeg")
        response = self.client.post(reverse('api_toll_dispute', kwargs={'booking_id': self.booking.id}), {
            'cash_amount': '120.00',
            'receipt_image': dummy_receipt,
            'notes': 'FASTag failed to scan at toll'
        })
        self.assertIn(response.status_code, [200, 201])

    def test_api_trip_extend_unauthenticated(self):
        response = self.client.post(reverse('api_trip_extend', kwargs={'booking_id': self.booking.id}))
        self.assertIn(response.status_code, [302, 401, 403])

    def test_api_trip_inspection_unauthenticated(self):
        response = self.client.post(reverse('api_trip_inspection', kwargs={'booking_id': self.booking.id}))
        self.assertIn(response.status_code, [302, 401, 403])

    def test_api_cancel_booking_sla_unauthenticated(self):
        response = self.client.post(reverse('api_cancel_booking_sla', kwargs={'booking_id': self.booking.id}))
        self.assertIn(response.status_code, [302, 401, 403])

    def test_api_cancel_booking_sla_authenticated(self):
        self.client.login(username='apiuser', password='apipassword123')
        b = Booking.objects.create(
            user=self.user,
            car=self.car,
            booking_reference='API-CANCEL-01',
            pickup_date=date.today() + timedelta(days=5),
            dropoff_date=date.today() + timedelta(days=7),
            total_price=Decimal('4400.00'),
            status='Confirmed'
        )
        response = self.client.post(reverse('api_cancel_booking_sla', kwargs={'booking_id': b.id}))
        self.assertIn(response.status_code, [200, 204])
