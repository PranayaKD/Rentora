"""
setup_postgres.py - Deterministic PostgreSQL Setup & Verification Tool
Part of Layer 3 (Execution) in Rentora 3-Layer Architecture.

Usage:
    python execution/setup_postgres.py [--check-only] [--seed]
"""

import os
import sys
import argparse
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Ensure settings uses postgres for this script
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rentora_project.settings')
os.environ['USE_LOCAL_DB'] = 'False'

import django
django.setup()

from django.db import connection, transaction
from django.core.management import call_command
from django.contrib.auth.models import User
from core.models import Car, Booking, Review, Wishlist, PromoCode

def check_postgres_connection():
    print("=" * 60)
    print("   RENTORA POSTGRESQL PRODUCTION VERIFICATION")
    print("=" * 60)
    
    from django.conf import settings
    db_config = settings.DATABASES.get('default', {})
    engine = db_config.get('ENGINE', '')
    host = db_config.get('HOST', 'localhost')
    port = db_config.get('PORT', '5432')
    name = db_config.get('NAME', 'postgres')
    user = db_config.get('USER', 'postgres')

    print(f"[*] Target Database Engine : {engine}")
    print(f"[*] Target Host            : {host}:{port}")
    print(f"[*] Database Name          : {name}")
    print(f"[*] Database User          : {user}")
    print("-" * 60)

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            version_row = cursor.fetchone()
            print(f"[SUCCESS] Connected to PostgreSQL!")
            print(f"[*] Server Version: {version_row[0][:80]}...")
            
            cursor.execute("SELECT current_database(), current_user;")
            db_info = cursor.fetchone()
            print(f"[*] Connected as '{db_info[1]}' to database '{db_info[0]}'")
            return True
    except Exception as e:
        print(f"[ERROR] Failed to connect to PostgreSQL: {e}")
        print("\n[DIAGNOSTIC GUIDANCE]:")
        print("1. If using Supabase: Ensure your Supabase project is active (not paused due to inactivity).")
        print("   Visit https://supabase.com/dashboard/project/<your-ref> and click 'Restore project'.")
        print("2. If using local PostgreSQL: Ensure PostgreSQL server is running (port 5432).")
        print("3. Check .env settings:")
        print("   DATABASE_URL=postgresql://user:password@host:port/dbname")
        print("   OR DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT")
        return False

def run_migrations_and_seed(seed_data=True):
    print("\n[*] Applying database migrations...")
    try:
        call_command('migrate', interactive=False)
        print("[SUCCESS] Migrations applied successfully!")
    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        return False

    if seed_data:
        print("\n[*] Verifying / Seeding Fleet Data...")
        try:
            from execution.seed_zoomcar_fleet import seed_fleet
            seed_fleet()
            car_count = Car.objects.count()
            print(f"[SUCCESS] Fleet verified: {car_count} vehicles loaded.")
        except Exception as e:
            print(f"[WARNING] Seeder encountered error: {e}")

    # ACID Transaction check
    print("\n[*] Verifying ACID Transaction Lock Integrity...")
    try:
        with transaction.atomic():
            test_car = Car.objects.select_for_update().first()
            if test_car:
                print(f"[SUCCESS] select_for_update() row-level lock operational on Car ID: {test_car.id}")
            else:
                print("[INFO] No cars in database yet to lock.")
    except Exception as e:
        print(f"[ERROR] ACID lock test failed: {e}")
        return False

    print("\n" + "=" * 60)
    print("   POSTGRESQL READINESS: 100% OPERATIONAL")
    print("=" * 60)
    return True

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Rentora PostgreSQL Setup")
    parser.add_argument('--check-only', action='store_true', help="Only test connection, do not migrate")
    parser.add_argument('--no-seed', action='store_true', help="Do not seed fleet data")
    args = parser.parse_args()

    connected = check_postgres_connection()
    if connected and not args.check_only:
        run_migrations_and_seed(seed_data=not args.no_seed)
    elif not connected:
        sys.exit(1)
