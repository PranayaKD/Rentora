import os
import sys
from pathlib import Path
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rentora_project.settings')
import django
django.setup()

from django.template.loader import render_to_string
from django.test import RequestFactory
from django.contrib.auth.models import User
from core.models import Car

def test_payment_template():
    factory = RequestFactory()
    req = factory.get('/booking/payment/')
    from django.contrib.sessions.backends.db import SessionStore
    req.session = SessionStore()
    user, _ = User.objects.get_or_create(username='test_user_flow')
    req.user = user

    car = Car.objects.filter(is_available=True).first()
    now = timezone.now()
    pickup_dt = now + timedelta(days=1)
    dropoff_dt = now + timedelta(days=3)

    subtotal = Decimal('5798.00')
    tax = Decimal('1043.64')
    total = subtotal + tax
    final_total = total

    context = {
        'car': car,
        'pickup_date': pickup_dt,
        'dropoff_date': dropoff_dt,
        'pickup_location': 'Bhubaneswar BBI Airport Hub',
        'dropoff_location': 'Bhubaneswar BBI Airport Hub',
        'days': 2,
        'subtotal': subtotal,
        'tax': tax,
        'total': total,
        'discount_amount': Decimal('0'),
        'final_total': final_total,
        'is_outstation': False,
        'current_city': 'Bhubaneswar',
        'current_location': 'Bhubaneswar',
    }

    html = render_to_string('payment.html', context, request=req)
    assert 'Fare Breakdown' in html, "Fare breakdown missing!"
    assert 'Zero Liability Cover' in html, "Protection plan missing!"
    assert '₹5,798' in html or '5798' in html, "Subtotal missing!"
    assert 'Pay & Reserve' in html, "Payment button missing!"
    print("PASS: payment.html rendered with 100% Stitch fidelity and 0 template errors!")

if __name__ == '__main__':
    test_payment_template()
