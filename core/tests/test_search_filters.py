from django.test import TestCase, Client
from django.urls import reverse
from decimal import Decimal
from core.models import Car

class CoreSearchFiltersTest(TestCase):
    """45 comprehensive tests for vehicle catalog searching, filtering, and sorting."""

    @classmethod
    def setUpTestData(cls):
        # Create a diverse test fleet across brands, categories, fuels, transmissions, and prices
        cars_data = [
            ("Thar LX 4x4", "Mahindra", "SUV", Decimal('4200.00'), "Diesel", "Manual", 4),
            ("Scorpio-N Z8", "Mahindra", "SUV", Decimal('4800.00'), "Diesel", "Automatic", 7),
            ("XUV700 AX7", "Mahindra", "SUV", Decimal('5200.00'), "Petrol", "Automatic", 7),
            ("Nexon EV Max", "Tata", "Electric", Decimal('2400.00'), "Electric", "Automatic", 5),
            ("Punch EV", "Tata", "Electric", Decimal('1800.00'), "Electric", "Automatic", 5),
            ("Harrier Dark", "Tata", "SUV", Decimal('4500.00'), "Diesel", "Automatic", 5),
            ("Swift ZXi", "Maruti Suzuki", "Hatchback", Decimal('1600.00'), "Petrol", "Manual", 5),
            ("Baleno Alpha", "Maruti Suzuki", "Hatchback", Decimal('1800.00'), "Petrol", "Automatic", 5),
            ("Grand Vitara Hybrid", "Maruti Suzuki", "SUV", Decimal('3200.00'), "Hybrid", "Automatic", 5),
            ("Creta SX(O)", "Hyundai", "SUV", Decimal('3400.00'), "Diesel", "Automatic", 5),
            ("i20 N-Line", "Hyundai", "Hatchback", Decimal('2200.00'), "Petrol", "Manual", 5),
            ("Verna Turbo", "Hyundai", "Sedan", Decimal('2800.00'), "Petrol", "Automatic", 5),
            ("City ZX", "Honda", "Sedan", Decimal('2600.00'), "Petrol", "Automatic", 5),
            ("Elevate ZX", "Honda", "SUV", Decimal('3100.00'), "Petrol", "Automatic", 5),
            ("Slavia Style", "Skoda", "Sedan", Decimal('3000.00'), "Petrol", "Automatic", 5),
            ("Kushaq Monte Carlo", "Skoda", "SUV", Decimal('3500.00'), "Petrol", "Automatic", 5),
            ("ZS EV Exclusive", "MG", "Electric", Decimal('3200.00'), "Electric", "Automatic", 5),
            ("Hector Plus", "MG", "SUV", Decimal('3800.00'), "Diesel", "Manual", 6),
            ("Innova Crysta VX", "Toyota", "MPV", Decimal('4900.00'), "Diesel", "Manual", 7),
            ("Fortuner 4x4", "Toyota", "SUV", Decimal('7500.00'), "Diesel", "Automatic", 7),
            ("BMW 330i M Sport", "BMW", "Luxury Sedan", Decimal('8500.00'), "Petrol", "Automatic", 5),
            ("Mercedes C200", "Mercedes-Benz", "Luxury Sedan", Decimal('9500.00'), "Petrol", "Automatic", 5),
            ("Audi A4 Technology", "Audi", "Luxury Sedan", Decimal('8800.00'), "Petrol", "Automatic", 5),
            ("Defender 110", "Land Rover", "SUV", Decimal('15000.00'), "Diesel", "Automatic", 7),
        ]
        cls.cars = [
            Car.objects.create(
                name=name, brand=brand, category=cat, price_per_day=price,
                fuel_type=fuel, transmission=trans, seats=seats, is_available=True
            )
            for name, brand, cat, price, fuel, trans, seats in cars_data
        ]

    def setUp(self):
        self.client = Client()

    # Brand filter tests
    def test_filter_brand_mahindra(self):
        response = self.client.get(reverse('cars'), {'brand': 'Mahindra'})
        self.assertEqual(len(response.context['cars']), 3)

    def test_filter_brand_tata(self):
        response = self.client.get(reverse('cars'), {'brand': 'Tata'})
        self.assertEqual(len(response.context['cars']), 3)

    def test_filter_brand_maruti(self):
        response = self.client.get(reverse('cars'), {'brand': 'Maruti Suzuki'})
        self.assertEqual(len(response.context['cars']), 3)

    def test_filter_brand_hyundai(self):
        response = self.client.get(reverse('cars'), {'brand': 'Hyundai'})
        self.assertEqual(len(response.context['cars']), 3)

    def test_filter_brand_honda(self):
        response = self.client.get(reverse('cars'), {'brand': 'Honda'})
        self.assertEqual(len(response.context['cars']), 2)

    def test_filter_brand_skoda(self):
        response = self.client.get(reverse('cars'), {'brand': 'Skoda'})
        self.assertEqual(len(response.context['cars']), 2)

    def test_filter_brand_mg(self):
        response = self.client.get(reverse('cars'), {'brand': 'MG'})
        self.assertEqual(len(response.context['cars']), 2)

    def test_filter_brand_toyota(self):
        response = self.client.get(reverse('cars'), {'brand': 'Toyota'})
        self.assertEqual(len(response.context['cars']), 2)

    def test_filter_brand_bmw(self):
        response = self.client.get(reverse('cars'), {'brand': 'BMW'})
        self.assertEqual(len(response.context['cars']), 1)

    def test_filter_brand_mercedes(self):
        response = self.client.get(reverse('cars'), {'brand': 'Mercedes-Benz'})
        self.assertEqual(len(response.context['cars']), 1)

    def test_filter_brand_audi(self):
        response = self.client.get(reverse('cars'), {'brand': 'Audi'})
        self.assertEqual(len(response.context['cars']), 1)

    def test_filter_brand_land_rover(self):
        response = self.client.get(reverse('cars'), {'brand': 'Land Rover'})
        self.assertEqual(len(response.context['cars']), 1)

    # Category filter tests
    def test_filter_category_suv(self):
        response = self.client.get(reverse('cars'), {'category': 'SUV'})
        self.assertTrue(all('SUV' in c.category for c in response.context['cars']))
        self.assertGreaterEqual(len(response.context['cars']), 8)

    def test_filter_category_hatchback(self):
        response = self.client.get(reverse('cars'), {'category': 'Hatchback'})
        self.assertTrue(all(c.category == 'Hatchback' for c in response.context['cars']))
        self.assertEqual(len(response.context['cars']), 3)

    def test_filter_category_electric(self):
        response = self.client.get(reverse('cars'), {'category': 'Electric'})
        self.assertTrue(all(c.category == 'Electric' for c in response.context['cars']))
        self.assertEqual(len(response.context['cars']), 3)

    def test_filter_category_sedan(self):
        response = self.client.get(reverse('cars'), {'category': 'Sedan'})
        self.assertTrue(all('Sedan' in c.category for c in response.context['cars']))

    def test_filter_category_luxury_sedan(self):
        response = self.client.get(reverse('cars'), {'category': 'Luxury Sedan'})
        self.assertTrue(all('Luxury' in c.category for c in response.context['cars']))
        self.assertEqual(len(response.context['cars']), 3)

    def test_filter_category_mpv(self):
        response = self.client.get(reverse('cars'), {'category': 'MPV'})
        self.assertTrue(all(c.category == 'MPV' for c in response.context['cars']))
        self.assertEqual(len(response.context['cars']), 1)

    # Fuel type filter tests
    def test_filter_fuel_diesel(self):
        response = self.client.get(reverse('cars'), {'fuel': 'Diesel'})
        self.assertTrue(all(c.fuel_type == 'Diesel' for c in response.context['cars']))

    def test_filter_fuel_petrol(self):
        response = self.client.get(reverse('cars'), {'fuel': 'Petrol'})
        self.assertTrue(all(c.fuel_type == 'Petrol' for c in response.context['cars']))

    def test_filter_fuel_electric(self):
        response = self.client.get(reverse('cars'), {'fuel': 'Electric'})
        self.assertTrue(all(c.fuel_type == 'Electric' for c in response.context['cars']))

    # Transmission filter tests
    def test_filter_transmission_manual(self):
        response = self.client.get(reverse('cars'), {'transmission': 'Manual'})
        self.assertTrue(all(c.transmission == 'Manual' for c in response.context['cars']))

    def test_filter_transmission_automatic(self):
        response = self.client.get(reverse('cars'), {'transmission': 'Automatic'})
        self.assertTrue(all('Auto' in c.transmission for c in response.context['cars']))

    # Seats filter tests
    def test_filter_seats_4(self):
        response = self.client.get(reverse('cars'), {'seats': '4'})
        self.assertTrue(all(c.seats == 4 for c in response.context['cars']))

    def test_filter_seats_5(self):
        response = self.client.get(reverse('cars'), {'seats': '5'})
        self.assertTrue(all(c.seats == 5 for c in response.context['cars']))

    def test_filter_seats_7(self):
        response = self.client.get(reverse('cars'), {'seats': '7'})
        self.assertTrue(all(c.seats == 7 for c in response.context['cars']))

    # Combined filters
    def test_filter_combined_brand_and_category(self):
        response = self.client.get(reverse('cars'), {'brand': 'Tata', 'category': 'Electric'})
        self.assertEqual(len(response.context['cars']), 2)

    def test_filter_combined_brand_and_fuel(self):
        response = self.client.get(reverse('cars'), {'brand': 'Mahindra', 'fuel': 'Diesel'})
        self.assertEqual(len(response.context['cars']), 2)

    def test_filter_combined_suv_automatic(self):
        response = self.client.get(reverse('cars'), {'category': 'SUV', 'transmission': 'Automatic'})
        self.assertTrue(all('SUV' in c.category and 'Auto' in c.transmission for c in response.context['cars']))

    def test_filter_combined_electric_automatic(self):
        response = self.client.get(reverse('cars'), {'category': 'Electric', 'transmission': 'Automatic'})
        self.assertEqual(len(response.context['cars']), 3)

    # Search keyword queries
    def test_search_by_model_name_swift(self):
        response = self.client.get(reverse('cars'), {'q': 'Swift'})
        self.assertEqual(len(response.context['cars']), 1)
        self.assertEqual(response.context['cars'][0].name, 'Swift ZXi')

    def test_search_by_model_name_creta(self):
        response = self.client.get(reverse('cars'), {'q': 'Creta'})
        self.assertEqual(len(response.context['cars']), 1)
        self.assertEqual(response.context['cars'][0].name, 'Creta SX(O)')

    def test_search_by_model_name_fortuner(self):
        response = self.client.get(reverse('cars'), {'q': 'Fortuner'})
        self.assertEqual(len(response.context['cars']), 1)
        self.assertEqual(response.context['cars'][0].name, 'Fortuner 4x4')

    def test_search_by_model_name_defender(self):
        response = self.client.get(reverse('cars'), {'q': 'Defender'})
        self.assertEqual(len(response.context['cars']), 1)
        self.assertEqual(response.context['cars'][0].name, 'Defender 110')

    def test_search_case_insensitive(self):
        response = self.client.get(reverse('cars'), {'q': 'tHaR'})
        self.assertGreaterEqual(len(response.context['cars']), 1)

    def test_search_partial_match(self):
        response = self.client.get(reverse('cars'), {'q': 'XUV'})
        self.assertGreaterEqual(len(response.context['cars']), 1)

    def test_search_nonexistent_term(self):
        response = self.client.get(reverse('cars'), {'q': 'LamborghiniAventador'})
        self.assertEqual(response.context['total_match_count'], 0)
        self.assertTrue(response.context['is_fallback'])

    # Price range filters
    def test_filter_price_max_2500(self):
        response = self.client.get(reverse('cars'), {'max_price': '2500'})
        self.assertTrue(all(c.price_per_day <= Decimal('2500.00') for c in response.context['cars']))

    def test_filter_price_min_5000(self):
        response = self.client.get(reverse('cars'), {'min_price': '5000'})
        self.assertTrue(all(c.price_per_day >= Decimal('5000.00') for c in response.context['cars']))

    def test_filter_price_between_3000_and_5000(self):
        response = self.client.get(reverse('cars'), {'min_price': '3000', 'max_price': '5000'})
        self.assertTrue(all(Decimal('3000.00') <= c.price_per_day <= Decimal('5000.00') for c in response.context['cars']))

    # Sorting
    def test_sort_price_low_to_high(self):
        response = self.client.get(reverse('cars'), {'sort': 'price_low'})
        prices = [c.price_per_day for c in response.context['cars']]
        self.assertEqual(prices, sorted(prices))

    def test_sort_price_high_to_low(self):
        response = self.client.get(reverse('cars'), {'sort': 'price_high'})
        prices = [c.price_per_day for c in response.context['cars']]
        self.assertEqual(prices, sorted(prices, reverse=True))

    def test_total_fleet_count(self):
        response = self.client.get(reverse('cars'))
        self.assertGreaterEqual(response.context['total_match_count'], len(self.cars))

    def test_search_endpoint_alias(self):
        response = self.client.get(reverse('search'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('cars', response.context)

    def test_cars_page_pagination_or_list_presence(self):
        response = self.client.get(reverse('cars'))
        self.assertIn('cars', response.context)
        self.assertGreater(len(response.context['cars']), 0)
