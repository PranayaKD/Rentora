"""
Upload site branding assets (hero, about, promotional banners)
to Cloudinary CDN for instant global edge delivery.
"""

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rentora_project.settings')

import django
django.setup()

import cloudinary
import cloudinary.uploader
from django.conf import settings

cloud_name = getattr(settings, 'CLOUDINARY_CLOUD_NAME', None) or os.getenv('CLOUDINARY_CLOUD_NAME')
api_key = getattr(settings, 'CLOUDINARY_API_KEY', None) or os.getenv('CLOUDINARY_API_KEY')
api_secret = getattr(settings, 'CLOUDINARY_API_SECRET', None) or os.getenv('CLOUDINARY_API_SECRET')

cloudinary.config(
    cloud_name=cloud_name,
    api_key=api_key,
    api_secret=api_secret,
    secure=True
)

STATIC_IMAGES = BASE_DIR / 'static' / 'images'

ASSETS_TO_UPLOAD = {
    'hero_odisha_coastal': STATIC_IMAGES / 'hero' / 'odisha_coastal_hero.webp',
    'about_rentora_coastal': STATIC_IMAGES / 'about' / 'about_rentora_coastal.webp',
    'banner_airport_curb': STATIC_IMAGES / 'banners' / 'banner_airport_curb.webp',
    'banner_unlimited_km': STATIC_IMAGES / 'banners' / 'banner_unlimited_km.webp',
    'banner_zero_deposit': STATIC_IMAGES / 'banners' / 'banner_zero_deposit.webp',
    'banner_ev_cars': STATIC_IMAGES / 'banners' / 'banner_ev_cars.webp',
    'banner_monthly_subscription': STATIC_IMAGES / 'banners' / 'banner_monthly_subscription.webp',
}

def upload_all():
    print(f"Uploading {len(ASSETS_TO_UPLOAD)} site assets to Cloudinary account: {cloud_name}...")
    uploaded_urls = {}
    
    for key, file_path in ASSETS_TO_UPLOAD.items():
        if not file_path.exists():
            print(f"[SKIP] File not found: {file_path}")
            continue
        
        public_id = f"rentora/site/{key}"
        try:
            res = cloudinary.uploader.upload(
                str(file_path),
                public_id=public_id,
                overwrite=True,
                resource_type="image",
                format="webp",
                quality="auto:good",
                fetch_format="auto"
            )
            url = res.get('secure_url')
            uploaded_urls[key] = url
            print(f"[OK] {key} -> {url}")
        except Exception as e:
            print(f"[FAIL] {key}: {e}")
            
    print("\n--- Summary of Cloudinary Site Asset URLs ---")
    for k, u in uploaded_urls.items():
        print(f"'{k}': '{u}',")

if __name__ == '__main__':
    upload_all()
