"""
audit_images.py - Audit all database vehicles and template image assets.
"""
import os
import re
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rentora_project.settings')
import django
django.setup()

from django.conf import settings
from core.models import Car

def main():
    print("=" * 60)
    print("      RENTORA ASSET & IMAGE VERIFICATION AUDIT")
    print("=" * 60)

    # 1. DATABASE CAR AUDIT
    print("\n[1] Verifying Fleet Database Records & Media Files...")
    cars = Car.objects.all().order_by('id')
    print(f"Total cars in database: {cars.count()}")
    missing_cars = 0
    for car in cars:
        if not car.image:
            print(f"  [MISSING FIELD] Car #{car.id} ({car.brand} {car.name}) has no image field set.")
            missing_cars += 1
            continue
        
        file_path = os.path.join(settings.MEDIA_ROOT, str(car.image).replace('/', os.sep))
        if not os.path.isfile(file_path):
            print(f"  [FILE NOT FOUND] Car #{car.id} ({car.brand} {car.name}) -> {car.image}")
            missing_cars += 1
        else:
            size_kb = os.path.getsize(file_path) / 1024
            print(f"  [OK] #{car.id:02d} {car.brand} {car.name:<20} -> {str(car.image):<25} ({size_kb:.1f} KB)")

    if missing_cars == 0:
        print("[SUCCESS] All database car images exist on disk.")
    else:
        print(f"[ERROR] {missing_cars} database car image(s) missing!")

    # 2. STATIC BRAND LOGOS AUDIT
    print("\n[2] Verifying Static Brand Logos...")
    brands_dir = os.path.join(settings.BASE_DIR, 'static', 'images', 'brands')
    if os.path.isdir(brands_dir):
        brand_files = os.listdir(brands_dir)
        print(f"Total brand logos present: {len(brand_files)}")
        for bf in sorted(brand_files):
            print(f"  [OK] Brand logo: {bf}")
    else:
        print(f"[ERROR] Brands directory not found: {brands_dir}")

    # 3. TEMPLATE IMAGE REFERENCES AUDIT
    print("\n[3] Auditing HTML Template Asset References...")
    template_dir = os.path.join(settings.BASE_DIR, 'templates')
    static_dir = os.path.join(settings.BASE_DIR, 'static')
    media_dir = os.path.join(settings.BASE_DIR, 'media')

    broken_refs = []
    scanned_count = 0

    for root, _, files in os.walk(template_dir):
        for f in files:
            if not f.endswith('.html'):
                continue
            html_path = os.path.join(root, f)
            with open(html_path, 'r', encoding='utf-8') as fh:
                content = fh.read()

            # Find static tag references: {% static '...' %}
            static_tags = re.findall(r"""\{%\s*static\s+['"]([^'"]+)['"]\s*%\}""", content)
            for tag in static_tags:
                scanned_count += 1
                # Skip css and js for image check, but verify file exists
                disk_path = os.path.join(static_dir, tag.replace('/', os.sep))
                if not os.path.isfile(disk_path):
                    broken_refs.append((f, 'static tag', tag, disk_path))

            # Find hardcoded /media/ references
            media_refs = re.findall(r"""['"](/media/[^'"><\s]+)['"]""", content)
            for m in media_refs:
                scanned_count += 1
                rel = m[len('/media/'):]
                disk_path = os.path.join(media_dir, rel.replace('/', os.sep))
                if not os.path.isfile(disk_path):
                    broken_refs.append((f, 'media ref', m, disk_path))

            # Find hardcoded /static/ references
            hard_static = re.findall(r"""['"](/static/[^'"><\s]+)['"]""", content)
            for hs in hard_static:
                scanned_count += 1
                rel = hs[len('/static/'):]
                disk_path = os.path.join(static_dir, rel.replace('/', os.sep))
                if not os.path.isfile(disk_path):
                    broken_refs.append((f, 'hardcoded static', hs, disk_path))

    print(f"Scanned {scanned_count} asset references across templates.")
    if not broken_refs:
        print("[SUCCESS] All template image and asset references resolve to valid files!")
    else:
        print(f"[FAIL] Found {len(broken_refs)} broken reference(s):")
        for tmpl, kind, ref, expected in broken_refs:
            print(f"  In {tmpl} ({kind}): '{ref}' -> missing at: {expected}")

    print("\n" + "=" * 60)
    print("                AUDIT SUMMARY")
    print("=" * 60)
    if missing_cars == 0 and len(broken_refs) == 0:
        print("RESULT: PERFECT - 0 missing car images, 0 broken template references.")
        return 0
    else:
        print(f"RESULT: ISSUES FOUND - {missing_cars} car images, {len(broken_refs)} broken refs.")
        return 1

if __name__ == '__main__':
    sys.exit(main())

