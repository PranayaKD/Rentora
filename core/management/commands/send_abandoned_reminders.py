import logging
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from core.models import Booking

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Sends reminder emails to users who abandoned their booking after 2 hours'

    def handle(self, *args, **options):
        # Time threshold: 2 hours ago
        threshold = timezone.now() - timedelta(hours=2)
        
        # Find bookings: Pending, Not Paid, Created > 2h ago, Reminder not yet sent
        abandoned_bookings = Booking.objects.filter(
            status='Pending',
            is_paid=False,
            created_at__lte=threshold,
            abandoned_reminder_sent=False
        ).select_related('user', 'car')

        if not abandoned_bookings.exists():
            self.stdout.write(self.style.SUCCESS('No abandoned bookings found for the current threshold.'))
            return

        cnt = 0
        for booking in abandoned_bookings:
            try:
                subject = f"Finish your booking for the {booking.car.brand} {booking.car.name}"
                
                context = {
                    'booking': booking,
                    'domain': settings.DOMAIN_URL,
                }
                
                html_content = render_to_string('emails/abandoned_cart_email.html', context)
                text_content = strip_tags(html_content)
                
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=text_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[booking.user.email],
                )
                email.attach_alternative(html_content, "text/html")
                email.send()
                
                # Mark as sent to prevent multiple reminders
                booking.abandoned_reminder_sent = True
                booking.save(update_fields=['abandoned_reminder_sent'])
                
                cnt += 1
                self.stdout.write(self.style.SUCCESS(f'Successfully sent reminder to {booking.user.email} for {booking.booking_reference}'))
                
            except Exception as e:
                logger.error(f"Error sending abandoned reminder for {booking.booking_reference}: {e}", exc_info=True)
                self.stdout.write(self.style.ERROR(f'Failed to send reminder for {booking.booking_reference}'))

        self.stdout.write(self.style.SUCCESS(f'Total reminders sent: {cnt}'))
