"""
Seed top popular cars from cars.json into Neon database
and upload their real webp images directly to Cloudinary.
"""

import os
import sys
import json
from decimal import Decimal
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rentora_project.settings')

import django
django.setup()

from django.core.files.storage import default_storage
from django.core.files import File
from core.models import Car

MEDIA_CARS = PROJECT_ROOT / 'media' / 'cars'

# Exact image map for popular models
CAR_IMAGE_MAP = {
    'Maruti Suzuki Ertiga': 'marutiertiga.webp',
    'Maruti Suzuki Dzire': 'marutidzire.webp',
    'Maruti Suzuki Brezza': 'marutibrezza.webp',
    'Maruti Suzuki Alto K10': 'marutialtok10.webp',
    'Toyota Fortuner': 'toyotafortuner.webp',
    'Toyota Innova Hycross': 'innovahycross.webp',
    'Honda City': 'hondacity.webp',
    'Honda Elevate': 'hondaelevate.webp',
    'Volkswagen Virtus': 'vwvirtus.webp',
    'Volkswagen Taigun': 'vwtaigun.webp',
    'Skoda Slavia': 'skodaslavia.webp',
    'Skoda Kushaq': 'skodakushaq.webp',
    'Tata Safari': 'tatasafari.webp',
    'Tata Harrier': 'tataharrier.webp',
    'Tata Tiago EV': 'tatatiagoev.webp',
    'Mahindra XUV700': 'xuv700.webp',
    'Mahindra Bolero Neo': 'boleroneo.webp',
    'Mahindra Thar Roxx': 'tharroxx.webp',
    'Kia Seltos': 'kiaseltos.webp',
    'Kia Carens': 'kiacarens.webp',
    'BMW 3 Series': 'bmw3series.webp',
    'BMW 5 Series': 'bmw5series.webp',
    'BMW X5': 'bmwx5.webp',
    'Audi A4': 'audia4.webp',
    'Audi Q3': 'audiq3.webp',
    'Mercedes-Benz C-Class': 'mercedescclass.webp',
    'Mercedes-Benz E-Class': 'mercedeseclass.webp',
    'Land Rover Defender 110': 'defender110.webp',
}

def run():
    with open(PROJECT_ROOT / 'cars.json', 'r', encoding='utf-8') as f:
        cars_data = json.load(f)

    existing_names = set(Car.objects.values_list('name', flat=True))
    created_count = 0

    for item in cars_data:
        fields = item['fields']
        name = fields.get('name')
        brand = fields.get('brand')
        full_key = f"{brand} {name}"

        # Match with local image
        img_filename = CAR_IMAGE_MAP.get(full_key)
        if not img_filename:
            # Try matching by name
            for k, v in CAR_IMAGE_MAP.items():
                if name.lower() in k.lower():
                    img_filename = v
                    break

        if not img_filename:
            continue

        local_img_path = MEDIA_CARS / img_filename
        if not local_img_path.exists():
            continue

        # If already exists in DB, ensure image is uploaded
        car = Car.objects.filter(name=name, brand=brand).first()
        if not car:
            price = Decimal(str(fields.get('price_per_day', '2499.00')))
            deposit = Decimal(str(fields.get('security_deposit', '0.00')))
            car = Car(
                name=name,
                brand=brand,
                category=fields.get('category', 'SUV'),
                price_per_day=price,
                security_deposit=deposit,
                free_km=fields.get('free_km', 300),
                seats=fields.get('seats', 5),
                fuel_type=fields.get('fuel_type', 'Petrol'),
                transmission=fields.get('transmission', 'Manual'),
                engine=fields.get('engine', '1.5L Turbo'),
                mileage=fields.get('mileage', '18.0 km/l'),
                is_available=True,
                features=fields.get('features') or {}
            )

        # Upload image to Cloudinary if not already a Cloudinary URL
        if not car.image or 'cloudinary' not in str(car.image):
            print(f"Uploading image for {brand} {name} ({img_filename})...")
            try:
                with open(local_img_path, 'rb') as f_img:
                    target_name = f"cars/{img_filename}"
                    saved_name = default_storage.save(target_name, File(f_img))
                    car.image = saved_name
                    car.save()
                    created_count += 1
                    print(f"  [OK] Saved -> {car.image.url}")
            except Exception as e:
                print(f"  [ERROR] Upload failed for {name}: {e}")

    print(f"\nDone! Added/Updated {created_count} cars with Cloudinary images.")
    print(f"Total cars in database: {Car.objects.count()}")

if __name__ == '__main__':
    run()
