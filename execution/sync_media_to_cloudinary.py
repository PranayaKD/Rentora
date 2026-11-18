"""
Rentora Cloudinary Media Sync Script
Deterministic tool to upload local media/cars/ to Cloudinary
and update database image URLs.
"""

import os
import sys
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rentora_project.settings')

def main():
    import django
    django.setup()

    import cloudinary
    import cloudinary.uploader
    from django.conf import settings
    from core.models import Car

    cloud_name = getattr(settings, 'CLOUDINARY_CLOUD_NAME', None) or os.getenv('CLOUDINARY_CLOUD_NAME')
    api_key = getattr(settings, 'CLOUDINARY_API_KEY', None) or os.getenv('CLOUDINARY_API_KEY')
    api_secret = getattr(settings, 'CLOUDINARY_API_SECRET', None) or os.getenv('CLOUDINARY_API_SECRET')

    if not (cloud_name and api_key and api_secret):
        print("ERROR: Cloudinary credentials missing in .env or settings.")
        print("Required: CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET")
        return

    cloudinary.config(
        cloud_name=cloud_name,
        api_key=api_key,
        api_secret=api_secret,
        secure=True
    )

    media_cars_dir = BASE_DIR / 'media' / 'cars'
    if not media_cars_dir.exists():
        print(f"Directory not found: {media_cars_dir}")
        return

    print("--- Starting Cloudinary Media Sync for Rentora ---")
    cars = Car.objects.all()
    uploaded_count = 0

    for car in cars:
        if not car.image:
            continue

        local_path = BASE_DIR / str(car.image).lstrip('/')
        if not local_path.exists():
            # Check directly in media/cars
            filename = Path(str(car.image)).name
            local_path = media_cars_dir / filename

        if not local_path.exists():
            print(f"[SKIP] File not found for car '{car.name}': {car.image}")
            continue

        public_id = f"rentora/cars/{local_path.stem}"
        try:
            res = cloudinary.uploader.upload(
                str(local_path),
                public_id=public_id,
                overwrite=True,
                resource_type="image"
            )
            # Store Cloudinary public ID or secure URL
            car.image = res.get('public_id') or res.get('secure_url')
            car.save(update_fields=['image'])
            uploaded_count += 1
            print(f"[OK] Uploaded '{car.name}' -> {public_id}")
        except Exception as e:
            print(f"[FAIL] Upload failed for '{car.name}': {e}")

    print(f"\n--- Sync Complete: {uploaded_count} vehicle images synced to Cloudinary ---")

if __name__ == '__main__':
    main()
