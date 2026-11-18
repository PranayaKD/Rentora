"""
Upload local vehicle images to Cloudinary via Django default_storage
and update database records with real Cloudinary URLs.
"""

import os
import sys
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rentora_project.settings')

import django
django.setup()

from django.core.files.storage import default_storage
from django.core.files import File
from core.models import Car

MEDIA_CARS = BASE_DIR / 'media' / 'cars'

# Name to local file mapping for accurate matching
IMAGE_MAP = {
    'swift': 'marutiswift.webp',
    'baleno': 'marutibaleno.webp',
    'punch': 'tatapunch.webp',
    'thar': 'thar.webp',
    'creta': 'hyundaicreta.webp',
    'scorpio': 'scorpion.webp',
    'innova': 'innovacrysta.webp',
    'nexon': 'tatanexonev.webp',
    'dzire': 'marutidzire.webp',
    'ertiga': 'marutiertiga.webp',
    'brezza': 'marutibrezza.webp',
    'alto': 'marutialtok10.webp',
    'wagon': 'marutiwagonr.webp',
    'seltos': 'kiaseltos.webp',
    'sonet': 'kiasonet.webp',
    'carens': 'kiacarens.webp',
    'fortuner': 'toyotafortuner.webp',
    'hycross': 'innovahycross.webp',
    'city': 'hondacity.webp',
    'elevate': 'hondaelevate.webp',
    'amaze': 'hondaamaze.webp',
    'virtus': 'vwvirtus.webp',
    'taigun': 'vwtaigun.webp',
    'slavia': 'skodaslavia.webp',
    'kushaq': 'skodakushaq.webp',
    'safari': 'tatasafari.webp',
    'harrier': 'tataharrier.webp',
    'tiago': 'tatatiago.webp',
    'tigor': 'tatatigor.webp',
    'xuv700': 'xuv700.webp',
    'xuv300': 'mahindraxuv300.webp',
    'bolero': 'boleroneo.webp',
    'bmw 3': 'bmw3series.webp',
    'bmw 5': 'bmw5series.webp',
    'bmw x1': 'bmwx1.webp',
    'bmw x5': 'bmwx5.webp',
    'audi a4': 'audia4.webp',
    'audi q3': 'audiq3.webp',
    'mercedes c': 'mercedescclass.webp',
    'mercedes e': 'mercedeseclass.webp',
    'defender': 'defender110.webp',
}

def find_image_for_car(car):
    """Finds the best matching webp/png/jpg file in media/cars."""
    name_lower = car.name.lower()
    
    # 1. Direct map lookup
    for key, filename in IMAGE_MAP.items():
        if key in name_lower:
            p = MEDIA_CARS / filename
            if p.exists():
                return p

    # 2. Check if car.image already points to an existing local file
    if car.image:
        candidate = MEDIA_CARS / Path(str(car.image)).name
        if candidate.exists():
            return candidate

    # 3. Fuzzy search in MEDIA_CARS
    clean_name = ''.join(c for c in name_lower if c.isalnum())
    for f in MEDIA_CARS.glob('*.webp'):
        clean_file = ''.join(c for c in f.stem.lower() if c.isalnum())
        if clean_file in clean_name or clean_name in clean_file:
            return f

    return None

def sync():
    cars = list(Car.objects.all())
    print(f"Syncing images for {len(cars)} cars in database...")
    
    success_count = 0
    for car in cars:
        local_path = find_image_for_car(car)
        if not local_path:
            print(f"[WARN] No local image file found for '{car.name}' ({car.brand})")
            continue

        print(f"Uploading '{car.name}' from {local_path.name}...")
        try:
            with open(local_path, 'rb') as f:
                # default_storage saves to Cloudinary via django-cloudinary-storage
                target_name = f"cars/{local_path.name}"
                saved_name = default_storage.save(target_name, File(f))
                car.image = saved_name
                car.save(update_fields=['image'])
                success_count += 1
                print(f"  [OK] Saved: {saved_name} -> {car.image.url}")
        except Exception as e:
            print(f"  [ERROR] Upload failed for '{car.name}': {e}")

    print(f"\nDone! Successfully uploaded and linked {success_count}/{len(cars)} car images to Cloudinary.")

if __name__ == '__main__':
    sync()
