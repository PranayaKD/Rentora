import os
import sys
from decimal import Decimal
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rentora_project.settings')

import django
django.setup()

from core.models import Car

POPULAR_ZOOMCAR_FLEET = [
    {
        "name": "Swift 2026",
        "brand": "Maruti Suzuki",
        "category": "Hatchback",
        "image": "cars/marutiswift.webp",
        "price_per_day": Decimal("1920.00"),
        "security_deposit": Decimal("0.00"),
        "free_km": 300,
        "seats": 5,
        "fuel_type": "Petrol",
        "transmission": "Manual",
        "engine": "1.2L DualJet Petrol",
        "mileage": "22.5 km/l",
        "features": {
            "hourly_rate": 80,
            "unlimited_hourly_rate": 96,
            "unlimited_daily_rate": 2304,
            "badge": "Guest Favorite",
            "host_name": "Ramesh Kumar (Top Host)",
            "host_type": "Professional Host",
            "distance_km": 2.4,
            "delivery_available": True,
            "extra_km_rate": 7,
            "key_features": ["Air Conditioner", "Touchscreen Audio", "Rear Parking Sensors", "Keyless Entry"],
            "gallery_images": [
                "https://images.unsplash.com/photo-1541899481282-d53bffe3c35d?auto=format&fit=crop&w=800&q=80",
                "https://images.unsplash.com/photo-1502877338535-766e1452684a?auto=format&fit=crop&w=800&q=80"
            ]
        }
    },
    {
        "name": "Punch 2024",
        "brand": "Tata",
        "category": "Micro SUV",
        "image": "cars/tatapunch.webp",
        "price_per_day": Decimal("2040.00"),
        "security_deposit": Decimal("0.00"),
        "free_km": 300,
        "seats": 5,
        "fuel_type": "Petrol",
        "transmission": "Manual",
        "engine": "1.2L Revotron Engine",
        "mileage": "18.8 km/l",
        "features": {
            "hourly_rate": 85,
            "unlimited_hourly_rate": 102,
            "unlimited_daily_rate": 2448,
            "badge": "Top Rated",
            "host_name": "Siddharth N. (Super Host)",
            "host_type": "Professional Host",
            "distance_km": 3.8,
            "delivery_available": True,
            "extra_km_rate": 8,
            "key_features": ["5-Star Safety Rating", "Harman Audio", "Cruise Control", "High Ground Clearance"],
            "gallery_images": [
                "https://images.unsplash.com/photo-1583121274602-3e2820c69888?auto=format&fit=crop&w=800&q=80"
            ]
        }
    },
    {
        "name": "Baleno 2026",
        "brand": "Maruti Suzuki",
        "category": "Hatchback",
        "image": "cars/marutibaleno.webp",
        "price_per_day": Decimal("2088.00"),
        "security_deposit": Decimal("0.00"),
        "free_km": 300,
        "seats": 5,
        "fuel_type": "Petrol",
        "transmission": "Manual",
        "engine": "1.2L K12N Petrol",
        "mileage": "22.3 km/l",
        "features": {
            "hourly_rate": 87,
            "unlimited_hourly_rate": 105,
            "unlimited_daily_rate": 2520,
            "badge": "Guest Favorite",
            "host_name": "Priya Sharma",
            "host_type": "Professional Host",
            "distance_km": 4.1,
            "delivery_available": True,
            "extra_km_rate": 7,
            "key_features": ["360 Degree Camera", "Heads Up Display", "LED Projector Lamps", "Fast Charging"],
            "gallery_images": [
                "https://images.unsplash.com/photo-1617788138017-80ad40651399?auto=format&fit=crop&w=800&q=80"
            ]
        }
    },
    {
        "name": "Thar 4x4 Hard Top",
        "brand": "Mahindra",
        "category": "Off-road SUV",
        "image": "cars/thar.webp",
        "price_per_day": Decimal("3480.00"),
        "security_deposit": Decimal("1000.00"),
        "free_km": 300,
        "seats": 4,
        "fuel_type": "Diesel",
        "transmission": "Automatic",
        "engine": "2.2L mHawk CRDe Turbo",
        "mileage": "15.2 km/l",
        "features": {
            "hourly_rate": 145,
            "unlimited_hourly_rate": 175,
            "unlimited_daily_rate": 4200,
            "badge": "Guest Favorite",
            "host_name": "Vikram Singh (Offroad Enthusiast)",
            "host_type": "Professional Host",
            "distance_km": 5.2,
            "delivery_available": True,
            "extra_km_rate": 11,
            "key_features": ["4x4 Low-Range Gearbox", "Touchscreen with Adventure Gauges", "Drizzle Resistant Roof", "All-Terrain Tyres"],
            "gallery_images": [
                "https://images.unsplash.com/photo-1533473359331-0135ef1b58bf?auto=format&fit=crop&w=800&q=80"
            ]
        }
    },
    {
        "name": "Creta SX(O)",
        "brand": "Hyundai",
        "category": "Compact SUV",
        "image": "cars/hyundaicreta.webp",
        "price_per_day": Decimal("2760.00"),
        "security_deposit": Decimal("0.00"),
        "free_km": 300,
        "seats": 5,
        "fuel_type": "Petrol",
        "transmission": "Automatic",
        "engine": "1.5L SmartStream Petrol",
        "mileage": "17.0 km/l",
        "features": {
            "hourly_rate": 115,
            "unlimited_hourly_rate": 138,
            "unlimited_daily_rate": 3312,
            "badge": "Top Rated",
            "host_name": "Ananya K.",
            "host_type": "Professional Host",
            "distance_km": 1.9,
            "delivery_available": True,
            "extra_km_rate": 9,
            "key_features": ["Panoramic Sunroof", "Ventilated Front Seats", "Bose 8-Speaker Audio", "Wireless Phone Charger"],
            "gallery_images": [
                "https://images.unsplash.com/photo-1549399542-7e3f8b79c341?auto=format&fit=crop&w=800&q=80"
            ]
        }
    },
    {
        "name": "Scorpio-N Z8",
        "brand": "Mahindra",
        "category": "SUV",
        "image": "cars/scorpion.webp",
        "price_per_day": Decimal("3840.00"),
        "security_deposit": Decimal("1000.00"),
        "free_km": 300,
        "seats": 7,
        "fuel_type": "Diesel",
        "transmission": "Automatic",
        "engine": "2.2L mHawk Diesel (175 HP)",
        "mileage": "14.5 km/l",
        "features": {
            "hourly_rate": 160,
            "unlimited_hourly_rate": 192,
            "unlimited_daily_rate": 4608,
            "badge": "Super Host",
            "host_name": "Gaurav Verma",
            "host_type": "Professional Host",
            "distance_km": 6.0,
            "delivery_available": True,
            "extra_km_rate": 12,
            "key_features": ["7 Full-Size Seats", "Sony 3D Surround Sound", "Terrain Response Modes", "Electric Sunroof"],
            "gallery_images": [
                "https://images.unsplash.com/photo-1503376780353-7e6692767b70?auto=format&fit=crop&w=800&q=80"
            ]
        }
    },
    {
        "name": "Innova Crysta 2.4 ZX",
        "brand": "Toyota",
        "category": "MPV",
        "image": "cars/innovacrysta.webp",
        "price_per_day": Decimal("4200.00"),
        "security_deposit": Decimal("1500.00"),
        "free_km": 300,
        "seats": 7,
        "fuel_type": "Diesel",
        "transmission": "Automatic",
        "engine": "2.4L GD Turbo Diesel",
        "mileage": "15.0 km/l",
        "features": {
            "hourly_rate": 175,
            "unlimited_hourly_rate": 210,
            "unlimited_daily_rate": 5040,
            "badge": "Super Host",
            "host_name": "Karthik Reddy",
            "host_type": "Professional Host",
            "distance_km": 7.5,
            "delivery_available": True,
            "extra_km_rate": 13,
            "key_features": ["Captain Seats Second Row", "Supreme Comfort for Long Trips", "Rear AC Vents", "Extra Large Luggage Capacity"],
            "gallery_images": [
                "https://images.unsplash.com/photo-1563720223185-11003d516935?auto=format&fit=crop&w=800&q=80"
            ]
        }
    },
    {
        "name": "Nexon EV Empowered",
        "brand": "Tata",
        "category": "Electric",
        "image": "cars/tatanexonev.webp",
        "price_per_day": Decimal("2640.00"),
        "security_deposit": Decimal("0.00"),
        "free_km": 300,
        "seats": 5,
        "fuel_type": "Electric",
        "transmission": "Automatic",
        "engine": "106 kW Permanent Magnet AC Motor",
        "mileage": "465 km Real-world Range",
        "features": {
            "hourly_rate": 110,
            "unlimited_hourly_rate": 132,
            "unlimited_daily_rate": 3168,
            "badge": "Guest Favorite",
            "host_name": "Deepak Patel (Green Drive)",
            "host_type": "Professional Host",
            "distance_km": 2.1,
            "delivery_available": True,
            "extra_km_rate": 7,
            "key_features": ["Zero Emissions", "V2L Vehicle-to-Load", "Arcade.ev App Suite", "JBL Cinematic Audio"],
            "gallery_images": [
                "https://images.unsplash.com/photo-1560958089-b8a1929cea89?auto=format&fit=crop&w=800&q=80"
            ]
        }
    }
]

def seed_fleet():
    created_count = 0
    updated_count = 0
    for car_data in POPULAR_ZOOMCAR_FLEET:
        car, created = Car.objects.update_or_create(
            name=car_data["name"],
            brand=car_data["brand"],
            defaults=car_data
        )
        if created:
            created_count += 1
            print(f"[CREATED] {car.brand} {car.name} - Rs. {car.hourly_rate}/hr")
        else:
            updated_count += 1
            print(f"[UPDATED] {car.brand} {car.name} - Rs. {car.hourly_rate}/hr")
    print(f"\nDone! Created: {created_count}, Updated: {updated_count}. Total cars in DB: {Car.objects.count()}")

if __name__ == '__main__':
    seed_fleet()

