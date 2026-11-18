from django.test import SimpleTestCase
from django.urls import reverse, resolve
from core import views

class CoreURLTests(SimpleTestCase):
    """36 deterministic tests for core URL routing and view resolution."""

    def test_url_index(self):
        url = reverse('index')
        self.assertEqual(url, '/')
        self.assertEqual(resolve(url).func, views.index_view)

    def test_url_how_it_works(self):
        url = reverse('how_it_works')
        self.assertEqual(url, '/how-it-works/')
        self.assertEqual(resolve(url).func, views.how_it_works_view)

    def test_url_subscription(self):
        url = reverse('subscription')
        self.assertEqual(url, '/subscription/')
        self.assertEqual(resolve(url).func, views.subscription_view)

    def test_url_airport_transfer(self):
        url = reverse('airport_transfer')
        self.assertEqual(url, '/airport-transfer/')
        self.assertEqual(resolve(url).func, views.airport_transfer_view)

    def test_url_why_rentora(self):
        url = reverse('why_rentora')
        self.assertEqual(url, '/why-rentora/')
        self.assertEqual(resolve(url).func, views.why_rentora_view)

    def test_url_cars(self):
        url = reverse('cars')
        self.assertEqual(url, '/cars/')
        self.assertEqual(resolve(url).func, views.cars_view)

    def test_url_car_detail(self):
        url = reverse('car_detail', kwargs={'car_id': 42})
        self.assertEqual(url, '/cars/42/')
        self.assertEqual(resolve(url).func, views.car_detail_view)

    def test_url_booking_location(self):
        url = reverse('booking_location')
        self.assertEqual(url, '/booking/')
        self.assertEqual(resolve(url).func, views.booking_location_view)

    def test_url_booking_location_direct(self):
        url = reverse('booking_location_direct', kwargs={'car_id': 7})
        self.assertEqual(url, '/booking/7/')
        self.assertEqual(resolve(url).func, views.booking_location_direct)

    def test_url_booking_dates(self):
        url = reverse('booking_dates')
        self.assertEqual(url, '/booking/dates/')
        self.assertEqual(resolve(url).func, views.booking_dates_view)

    def test_url_booking_select(self):
        url = reverse('booking_select')
        self.assertEqual(url, '/booking/select/')
        self.assertEqual(resolve(url).func, views.booking_select_view)

    def test_url_payment(self):
        url = reverse('payment')
        self.assertEqual(url, '/booking/payment/')
        self.assertEqual(resolve(url).func, views.payment_view)

    def test_url_confirmation(self):
        url = reverse('confirmation', kwargs={'booking_id': 101})
        self.assertEqual(url, '/booking/confirmation/101/')
        self.assertEqual(resolve(url).func, views.confirmation_view)

    def test_url_booking_detail(self):
        url = reverse('booking_detail', kwargs={'booking_id': 101})
        self.assertEqual(url, '/booking/101/detail/')
        self.assertEqual(resolve(url).func, views.booking_detail_view)

    def test_url_cancel_booking(self):
        url = reverse('cancel_booking', kwargs={'booking_id': 101})
        self.assertEqual(url, '/booking/101/cancel/')
        self.assertEqual(resolve(url).func, views.cancel_booking_view)

    def test_url_invoice(self):
        url = reverse('invoice', kwargs={'booking_id': 101})
        self.assertEqual(url, '/booking/invoice/101/')
        self.assertEqual(resolve(url).func, views.invoice_view)

    def test_url_download_receipt(self):
        url = reverse('download_receipt', kwargs={'booking_id': 101})
        self.assertEqual(url, '/booking/receipt/101/')
        self.assertEqual(resolve(url).func, views.download_receipt_view)

    def test_url_search(self):
        url = reverse('search')
        self.assertEqual(url, '/search/')
        self.assertEqual(resolve(url).func, views.cars_view)

    def test_url_contact(self):
        url = reverse('contact')
        self.assertEqual(url, '/contact/')
        self.assertEqual(resolve(url).func, views.contact_view)

    def test_url_add_review(self):
        url = reverse('add_review', kwargs={'car_id': 5})
        self.assertEqual(url, '/cars/5/review/')
        self.assertEqual(resolve(url).func, views.add_review_view)

    def test_url_api_cars_search(self):
        url = reverse('api_cars_search')
        self.assertEqual(url, '/api/cars/search/')
        self.assertEqual(resolve(url).func, views.api_cars_search)

    def test_url_api_check_availability(self):
        url = reverse('api_check_availability')
        self.assertEqual(url, '/api/booking/check-availability/')
        self.assertEqual(resolve(url).func, views.api_check_availability)

    def test_url_api_apply_promo(self):
        url = reverse('api_apply_promo')
        self.assertEqual(url, '/api/promo/apply/')
        self.assertEqual(resolve(url).func, views.api_apply_promo)

    def test_url_api_wishlist_toggle(self):
        url = reverse('api_wishlist_toggle', kwargs={'car_id': 12})
        self.assertEqual(url, '/api/wishlist/toggle/12/')
        self.assertEqual(resolve(url).func, views.api_wishlist_toggle)

    def test_url_car_booked_dates(self):
        url = reverse('car_booked_dates', kwargs={'car_id': 12})
        self.assertEqual(url, '/api/cars/12/booked-dates/')
        self.assertEqual(resolve(url).func, views.get_booked_dates)

    def test_url_notifications(self):
        url = reverse('notifications')
        self.assertEqual(url, '/notifications/')
        self.assertEqual(resolve(url).func, views.notifications_view)

    def test_url_api_notification_count(self):
        url = reverse('api_notification_count')
        self.assertEqual(url, '/api/notifications/count/')
        self.assertEqual(resolve(url).func, views.api_notification_count)

    def test_url_terms(self):
        url = reverse('terms')
        self.assertEqual(url, '/terms/')
        self.assertEqual(resolve(url).func, views.terms_view)

    def test_url_privacy(self):
        url = reverse('privacy')
        self.assertEqual(url, '/privacy/')
        self.assertEqual(resolve(url).func, views.privacy_view)

    def test_url_set_city(self):
        url = reverse('set_city')
        self.assertEqual(url, '/api/city/set/')
        self.assertEqual(resolve(url).func, views.set_city_view)

    def test_url_onboarding(self):
        url = reverse('onboarding')
        self.assertEqual(url, '/onboarding/')
        self.assertEqual(resolve(url).func, views.onboarding_view)

    def test_url_api_trip_inspection(self):
        url = reverse('api_trip_inspection', kwargs={'booking_id': 99})
        self.assertEqual(url, '/api/trip/99/inspection/')
        self.assertEqual(resolve(url).func, views.api_trip_inspection)

    def test_url_api_trip_extend(self):
        url = reverse('api_trip_extend', kwargs={'booking_id': 99})
        self.assertEqual(url, '/api/trip/99/extend/')
        self.assertEqual(resolve(url).func, views.api_trip_extend)

    def test_url_api_trip_sos(self):
        url = reverse('api_trip_sos', kwargs={'booking_id': 99})
        self.assertEqual(url, '/api/trip/99/sos/')
        self.assertEqual(resolve(url).func, views.api_trip_sos)

    def test_url_api_toll_dispute(self):
        url = reverse('api_toll_dispute', kwargs={'booking_id': 99})
        self.assertEqual(url, '/api/trip/99/toll-dispute/')
        self.assertEqual(resolve(url).func, views.api_toll_dispute)

    def test_url_api_cancel_booking_sla(self):
        url = reverse('api_cancel_booking_sla', kwargs={'booking_id': 99})
        self.assertEqual(url, '/api/trip/99/cancel-sla/')
        self.assertEqual(resolve(url).func, views.api_cancel_booking_sla)
