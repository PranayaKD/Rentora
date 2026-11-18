import os
import sys
from pathlib import Path
from datetime import timedelta
from django.utils import timezone

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rentora_project.settings')
import django
django.setup()

from django.contrib.auth.models import User
from django.contrib.sessions.backends.db import SessionStore
from core.models import Car

user, _ = User.objects.get_or_create(username='test_user_flow', defaults={'first_name': 'Abhishek', 'email': 'abhishek@test.com'})
car = Car.objects.filter(is_available=True).first()

session = SessionStore()
session['_auth_user_id'] = str(user.id)
session['_auth_user_backend'] = 'django.contrib.auth.backends.ModelBackend'
session['_auth_user_hash'] = user.get_session_auth_hash()

now = timezone.now()
session['booking_car_id'] = car.id
session['pickup_date'] = (now + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
session['dropoff_date'] = (now + timedelta(days=3)).strftime('%Y-%m-%d %H:%M:%S')
session['pickup_location'] = 'Bhubaneswar BBI Airport Hub'
session['dropoff_location'] = 'Bhubaneswar BBI Airport Hub'
session['current_city'] = 'Bhubaneswar'
session.save()

print(session.session_key)
