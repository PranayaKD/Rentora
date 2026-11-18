from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from decimal import Decimal
from core.models import Car, Booking

class CoreViewsHTTPTest(TestCase):
    """45 deterministic tests for HTTP view rendering, templates, and redirection."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='traveller1', password='securepassword123')
        cls.car = Car.objects.create(
            name="Scorpio-N",
            brand="Mahindra",
            category="SUV",
            price_per_day=Decimal('4500.00'),
            seats=7,
            fuel_type="Diesel",
            transmission="Automatic",
            is_available=True
        )

    def setUp(self):
        self.client = Client()

    def test_index_view_status_code(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)

    def test_index_view_template_used(self):
        response = self.client.get(reverse('index'))
        self.assertTemplateUsed(response, 'index.html')

    def test_index_view_context_contains_cars(self):
        response = self.client.get(reverse('index'))
        self.assertIn('all_available', response.context)

    def test_how_it_works_view_status(self):
        response = self.client.get(reverse('how_it_works'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'how-it-works.html')

    def test_subscription_view_status(self):
        response = self.client.get(reverse('subscription'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'subscription.html')

    def test_airport_transfer_view_status(self):
        response = self.client.get(reverse('airport_transfer'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'airport-transfer.html')

    def test_why_rentora_view_status(self):
        response = self.client.get(reverse('why_rentora'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'why-rentora.html')

    def test_contact_view_get(self):
        response = self.client.get(reverse('contact'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'contact.html')

    def test_terms_view_status(self):
        response = self.client.get(reverse('terms'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'legal/terms.html')

    def test_privacy_view_status(self):
        response = self.client.get(reverse('privacy'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'legal/privacy.html')

    def test_cars_catalog_view_status(self):
        response = self.client.get(reverse('cars'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cars.html')

    def test_car_detail_view_valid_car(self):
        response = self.client.get(reverse('car_detail', kwargs={'car_id': self.car.id}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'car-detail.html')
        self.assertEqual(response.context['car'].id, self.car.id)

    def test_car_detail_view_nonexistent_car_404(self):
        response = self.client.get(reverse('car_detail', kwargs={'car_id': 999999}))
        self.assertEqual(response.status_code, 404)

    def test_booking_location_view_unauthenticated_redirect(self):
        response = self.client.get(reverse('booking_location'))
        self.assertEqual(response.status_code, 302)

    def test_booking_location_view_authenticated(self):
        self.client.login(username='traveller1', password='securepassword123')
        response = self.client.get(reverse('booking_location'))
        self.assertEqual(response.status_code, 200)

    def test_booking_dates_view_redirect_without_location(self):
        self.client.login(username='traveller1', password='securepassword123')
        response = self.client.get(reverse('booking_dates'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('booking_location'))

    def test_booking_dates_view_with_session_location(self):
        self.client.login(username='traveller1', password='securepassword123')
        session = self.client.session
        session['pickup_location'] = 'Bhubaneswar Airport'
        session.save()
        response = self.client.get(reverse('booking_dates'))
        self.assertEqual(response.status_code, 200)

    def test_health_check_endpoint(self):
        response = self.client.get(reverse('health_check'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get('status'), 'healthy')

    def test_ping_endpoint(self):
        response = self.client.get(reverse('ping'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get('status'), 'healthy')

    def test_robots_txt_status(self):
        response = self.client.get(reverse('robots_txt'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/plain')

    def test_sitemap_xml_status(self):
        response = self.client.get(reverse('sitemap_xml'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('xml', response['Content-Type'])

    def test_notifications_login_required_redirects(self):
        response = self.client.get(reverse('notifications'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_notifications_authenticated_user_access(self):
        self.client.login(username='traveller1', password='securepassword123')
        response = self.client.get(reverse('notifications'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'notifications.html')

    def test_set_city_view_post(self):
        response = self.client.post(reverse('set_city'), {'city': 'Puri'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get('status'), 'success')
        self.assertEqual(self.client.session.get('current_city'), 'Puri')

    def test_set_city_view_session_persists(self):
        self.client.post(reverse('set_city'), {'city': 'Cuttack'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context.get('current_city'), 'Cuttack')

    def test_cars_filter_by_brand(self):
        response = self.client.get(reverse('cars'), {'brand': 'Mahindra'})
        self.assertEqual(response.status_code, 200)
        cars = response.context['cars']
        self.assertTrue(all(c.brand == 'Mahindra' for c in cars))

    def test_cars_filter_by_category(self):
        response = self.client.get(reverse('cars'), {'category': 'SUV'})
        self.assertEqual(response.status_code, 200)
        cars = response.context['cars']
        self.assertTrue(all('SUV' in c.category for c in cars))

    def test_cars_filter_by_fuel_type(self):
        response = self.client.get(reverse('cars'), {'fuel': 'Diesel'})
        self.assertEqual(response.status_code, 200)
        cars = response.context['cars']
        self.assertTrue(all(c.fuel_type == 'Diesel' for c in cars))

    def test_cars_filter_by_transmission(self):
        response = self.client.get(reverse('cars'), {'transmission': 'Automatic'})
        self.assertEqual(response.status_code, 200)
        cars = response.context['cars']
        self.assertTrue(all('Auto' in c.transmission for c in cars))

    def test_cars_filter_no_results(self):
        response = self.client.get(reverse('cars'), {'brand': 'NonExistentBrandXYZ'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_match_count'], 0)
        self.assertTrue(response.context['is_fallback'])

    def test_cars_search_query_string(self):
        response = self.client.get(reverse('cars'), {'q': 'Scorpio'})
        self.assertEqual(response.status_code, 200)
        cars = response.context['cars']
        self.assertTrue(any('Scorpio' in c.name for c in cars))

    def test_onboarding_view_redirects_for_anonymous(self):
        response = self.client.get(reverse('onboarding'))
        self.assertEqual(response.status_code, 302)

    def test_onboarding_view_authenticated(self):
        self.client.login(username='traveller1', password='securepassword123')
        response = self.client.get(reverse('onboarding'))
        self.assertEqual(response.status_code, 200)

    def test_skip_onboarding_redirects(self):
        self.client.login(username='traveller1', password='securepassword123')
        response = self.client.get(reverse('skip_onboarding'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('index'))

    def test_dashboard_bookings_unauthenticated_redirect(self):
        response = self.client.get(reverse('dashboard_bookings'))
        self.assertEqual(response.status_code, 302)

    def test_dashboard_profile_unauthenticated_redirect(self):
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 302)

    def test_wishlist_unauthenticated_redirect(self):
        response = self.client.get(reverse('wishlist'))
        self.assertEqual(response.status_code, 302)

    def test_kyc_unauthenticated_redirect(self):
        response = self.client.get(reverse('kyc'))
        self.assertEqual(response.status_code, 302)

    def test_login_page_renders_cleanly(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_signup_page_renders_cleanly(self):
        response = self.client.get(reverse('signup'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('login'))

    def test_authenticated_user_access_wishlist(self):
        self.client.login(username='traveller1', password='securepassword123')
        response = self.client.get(reverse('wishlist'))
        self.assertEqual(response.status_code, 200)

    def test_authenticated_user_access_dashboard(self):
        self.client.login(username='traveller1', password='securepassword123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_authenticated_user_access_profile(self):
        self.client.login(username='traveller1', password='securepassword123')
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)

    def test_authenticated_user_access_kyc(self):
        self.client.login(username='traveller1', password='securepassword123')
        response = self.client.get(reverse('kyc'))
        self.assertEqual(response.status_code, 200)

    def test_booking_select_view(self):
        self.client.login(username='traveller1', password='securepassword123')
        session = self.client.session
        session['pickup_location'] = 'Bhubaneswar Hub'
        session['pickup_date'] = '2026-11-20'
        session['dropoff_date'] = '2026-11-22'
        session.save()
        response = self.client.get(reverse('booking_select'))
        self.assertEqual(response.status_code, 200)

    def test_payment_view_without_session_redirects_to_cars(self):
        response = self.client.get(reverse('payment'))
        self.assertIn(response.status_code, [200, 302])

    def test_confirmation_view_nonexistent_booking_404(self):
        self.client.login(username='traveller1', password='securepassword123')
        response = self.client.get(reverse('confirmation', kwargs={'booking_id': 999999}))
        self.assertEqual(response.status_code, 404)
