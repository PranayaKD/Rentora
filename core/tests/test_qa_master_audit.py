import re
from django.test import TestCase, Client
from django.conf import settings
from django.contrib.auth import get_user_model
from core.models import Car, Booking

User = get_user_model()

class RentoraMasterQAAuditTest(TestCase):
    """
    Principal QA Master Audit Test Suite for Rentora.
    Validates zero template leaks, sensitive credential security,
    responsive UI hooks, date handling, and core journey integrity.
    """

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="9876543210",
            email="testuser@rentora.in",
            password="TestPassword123!"
        )
        self.car = Car.objects.create(
            name="Mahindra Thar 4x4",
            brand="Mahindra",
            category="SUV",
            price_per_day=3499,
            transmission="Automatic",
            fuel_type="Diesel",
            seats=4,
            engine="2.0L mStallion",
            mileage="15 km/l",
            is_available=True
        )

    def test_zero_template_leaks_on_critical_pages(self):
        """Audit Dimension A: Zero template tags ({{, }}, {%, %}) must leak into rendered HTML."""
        routes = [
            '/',
            '/cars/',
            f'/cars/{self.car.id}/',
            '/how-it-works/',
            '/why-rentora/',
            '/contact/',
            '/subscription/',
            '/airport-transfer/',
            '/accounts/login/',
        ]
        
        # Regex captures visible raw django interpolation syntax
        leak_pattern = re.compile(r'(\{\{\s*[\w\.\_\|\:\"]+\s*\}\}|\{%\s*[\w\s\_\-\'\"]+\s*%\})')
        
        for url in routes:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, f"Route {url} failed with status {response.status_code}")
            html = response.content.decode('utf-8')
            
            # Check for raw {{ ... }} or {% ... %}
            leaks = leak_pattern.findall(html)
            self.assertEqual(
                len(leaks), 0,
                f"Template leak detected on route {url}: {leaks[:3]}"
            )
            
            # Verify explicit default filter syntax did not leak
            self.assertNotIn('|default:', html, f"Raw filter '|default:' leaked on route {url}")
            self.assertNotIn('|date:', html, f"Raw filter '|date:' leaked on route {url}")

    def test_sensitive_credentials_never_exposed_in_html(self):
        """Security Check: Ensure NO secrets or API keys are rendered to client browsers."""
        response = self.client.get('/')
        html = response.content.decode('utf-8')
        
        # Check SECRET_KEY
        if getattr(settings, 'SECRET_KEY', None):
            self.assertNotIn(settings.SECRET_KEY, html, "CRITICAL: Django SECRET_KEY exposed in HTML!")
            
        # Check Razorpay Secret (Key ID is public, Key Secret must NEVER be in client HTML)
        rzp_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', '')
        if rzp_secret and len(rzp_secret) > 6:
            self.assertNotIn(rzp_secret, html, "CRITICAL: RAZORPAY_KEY_SECRET exposed in HTML!")
            
        # Check Twilio Auth Token
        twilio_token = getattr(settings, 'TWILIO_AUTH_TOKEN', '')
        if twilio_token and len(twilio_token) > 6:
            self.assertNotIn(twilio_token, html, "CRITICAL: TWILIO_AUTH_TOKEN exposed in HTML!")

    def test_hero_search_bar_renders_clean_city_hub(self):
        """Verify Hero Search Bar renders actual text, not template tag."""
        response = self.client.get('/')
        html = response.content.decode('utf-8')
        
        self.assertIn('current-city-label', html)
        self.assertIn('Bhubaneswar Hub (BBI)', html)
        self.assertNotIn('{{ current_city', html)

    def test_about_section_word_spacing_integrity(self):
        """Audit Dimension B: Verify About paragraph words have correct spacing in DOM."""
        response = self.client.get('/')
        html = response.content.decode('utf-8')
        
        self.assertIn('Born in Bhubaneswar for Odisha', html)
        self.assertIn('Why Rentora? Because Renting a Car in Odisha Needed to Change.', html)

    def test_coming_soon_modal_and_app_store_buttons(self):
        """Verify Footer contains interactive Coming Soon buttons and modal structure."""
        response = self.client.get('/')
        html = response.content.decode('utf-8')
        
        self.assertIn('id="coming-soon-modal"', html)
        self.assertIn('openComingSoonModal', html)
        self.assertIn('App Store', html)
        self.assertIn('Google Play', html)

    def test_booking_dashboard_date_formatting(self):
        """Verify bookings render dates cleanly without date filter TypeError."""
        booking = Booking.objects.create(
            user=self.user,
            car=self.car,
            pickup_date="2026-12-01",
            dropoff_date="2026-12-03",
            total_price=6998,
            pickup_location="Bhubaneswar Airport (BBI)",
            dropoff_location="Bhubaneswar Airport (BBI)",
            status="CONFIRMED"
        )
        self.client.force_login(self.user)
        response = self.client.get('/accounts/dashboard/bookings/')
        self.assertEqual(response.status_code, 200)
        html = response.content.decode('utf-8')
        
        self.assertIn('Mahindra Thar 4x4', html)
        self.assertNotIn('TypeError', html)
        self.assertNotIn('Exception Value', html)

    def test_csrf_token_present_on_all_forms(self):
        """Security Check: Verify CSRF token presence on authentication and contact forms."""
        auth_response = self.client.get('/accounts/login/')
        self.assertIn('csrfmiddlewaretoken', auth_response.content.decode('utf-8'))
        
        contact_response = self.client.get('/contact/')
        self.assertIn('csrfmiddlewaretoken', contact_response.content.decode('utf-8'))
