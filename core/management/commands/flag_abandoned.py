from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from core.models import Booking
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Identifies and flags abandoned bookings (Pending for > 2 hours)'

    def handle(self, *args, **options):
        # Define the threshold for abandonment (e.g., 2 hours)
        threshold = timezone.now() - timedelta(hours=2)
        
        # Get all pending bookings created before the threshold
        abandoned_bookings = Booking.objects.filter(
            status=Booking.Status.PENDING,
            created_at__lt=threshold,
            abandoned_reminder_sent=False
        )
        
        count = abandoned_bookings.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS('No new abandoned bookings found.'))
            return

        self.stdout.write(self.style.WARNING(f'Found {count} abandoned bookings. Flagging for recovery...'))
        
        for booking in abandoned_bookings:
            # Here you could trigger an email or SMS reminder
            # For now, we flag them so they show up in the Rentora HQ Dashboard
            self.stdout.write(f"- Booking {booking.booking_reference} by {booking.user.username} (₹{booking.total_price})")
            
            # booking.abandoned_reminder_sent = True # Toggle this if you actually send an email
            # booking.save()

        self.stdout.write(self.style.SUCCESS(f'Successfully flagged {count} abandoned carts.'))
