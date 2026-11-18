from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from decimal import Decimal
from core.models import Car, Booking

class AdminPanelTests(TestCase):
    """25 deterministic tests for Admin Panel routing, authorization, and fleet management."""

    @classmethod
    def setUpTestData(cls):
        cls.normal_user = User.objects.create_user(username='regular_user', password='password123')
        cls.admin_user = User.objects.create_superuser(username='superadmin', password='password123', email='admin@rentora.in')
        cls.car = Car.objects.create(
            name="Innova Crysta",
            brand="Toyota",
            category="MPV",
            price_per_day=Decimal('4500.00'),
            seats=7,
            fuel_type="Diesel",
            is_available=True
        )

    def setUp(self):
        self.client = Client()

    def test_admin_dashboard_unauthenticated_redirect(self):
        response = self.client.get(reverse('admin_dashboard'))
        self.assertIn(response.status_code, [302, 403])

    def test_admin_dashboard_non_staff_forbidden_or_redirect(self):
        self.client.login(username='regular_user', password='password123')
        response = self.client.get(reverse('admin_dashboard'))
        self.assertIn(response.status_code, [302, 403])

    def test_admin_dashboard_superuser_access(self):
        self.client.login(username='superadmin', password='password123')
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_admin_cars_list_superuser_access(self):
        self.client.login(username='superadmin', password='password123')
        response = self.client.get(reverse('admin_cars_list'))
        self.assertEqual(response.status_code, 200)

    def test_admin_car_add_view_get(self):
        self.client.login(username='superadmin', password='password123')
        response = self.client.get(reverse('admin_car_add'))
        self.assertEqual(response.status_code, 200)

    def test_admin_car_edit_view_get(self):
        self.client.login(username='superadmin', password='password123')
        response = self.client.get(reverse('admin_car_edit', kwargs={'car_id': self.car.id}))
        self.assertEqual(response.status_code, 200)

    def test_admin_bookings_list_superuser(self):
        self.client.login(username='superadmin', password='password123')
        response = self.client.get(reverse('admin_bookings_list'))
        self.assertEqual(response.status_code, 200)

    def test_admin_bookings_csv_export(self):
        self.client.login(username='superadmin', password='password123')
        response = self.client.get(reverse('admin_bookings_csv'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/csv', response['Content-Type'])

    def test_admin_users_list_superuser(self):
        self.client.login(username='superadmin', password='password123')
        response = self.client.get(reverse('admin_users_list'))
        self.assertEqual(response.status_code, 200)

    def test_admin_revenue_view_superuser(self):
        self.client.login(username='superadmin', password='password123')
        response = self.client.get(reverse('admin_revenue'))
        self.assertEqual(response.status_code, 200)

    def test_api_admin_revenue_superuser(self):
        self.client.login(username='superadmin', password='password123')
        response = self.client.get(reverse('api_admin_revenue'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('months', data)
        self.assertIn('revenues', data)

    def test_admin_cars_list_unauthenticated(self):
        response = self.client.get(reverse('admin_cars_list'))
        self.assertIn(response.status_code, [302, 403])

    def test_admin_car_add_unauthenticated(self):
        response = self.client.get(reverse('admin_car_add'))
        self.assertIn(response.status_code, [302, 403])

    def test_admin_bookings_list_unauthenticated(self):
        response = self.client.get(reverse('admin_bookings_list'))
        self.assertIn(response.status_code, [302, 403])

    def test_admin_users_list_unauthenticated(self):
        response = self.client.get(reverse('admin_users_list'))
        self.assertIn(response.status_code, [302, 403])

    def test_admin_revenue_unauthenticated(self):
        response = self.client.get(reverse('admin_revenue'))
        self.assertIn(response.status_code, [302, 403])

    def test_api_admin_revenue_unauthenticated(self):
        response = self.client.get(reverse('api_admin_revenue'))
        self.assertIn(response.status_code, [302, 403])

    def test_admin_car_edit_unauthenticated(self):
        response = self.client.get(reverse('admin_car_edit', kwargs={'car_id': self.car.id}))
        self.assertIn(response.status_code, [302, 403])

    def test_admin_car_delete_unauthenticated(self):
        response = self.client.post(reverse('admin_car_delete', kwargs={'car_id': self.car.id}))
        self.assertIn(response.status_code, [302, 403])

    def test_admin_booking_status_unauthenticated(self):
        response = self.client.post(reverse('admin_booking_status', kwargs={'booking_id': 1}))
        self.assertIn(response.status_code, [302, 403])

    def test_admin_bookings_csv_unauthenticated(self):
        response = self.client.get(reverse('admin_bookings_csv'))
        self.assertIn(response.status_code, [302, 403])

    def test_admin_car_edit_nonexistent_car_404(self):
        self.client.login(username='superadmin', password='password123')
        response = self.client.get(reverse('admin_car_edit', kwargs={'car_id': 999999}))
        self.assertEqual(response.status_code, 404)

    def test_admin_user_has_staff_permission(self):
        self.assertTrue(self.admin_user.is_staff)
        self.assertTrue(self.admin_user.is_superuser)

    def test_normal_user_lacks_staff_permission(self):
        self.assertFalse(self.normal_user.is_staff)
        self.assertFalse(self.normal_user.is_superuser)

    def test_superuser_email_verified(self):
        self.assertEqual(self.admin_user.email, 'admin@rentora.in')
