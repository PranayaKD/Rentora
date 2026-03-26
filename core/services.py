from decimal import Decimal
import logging
import stripe
from django.conf import settings
from django.urls import reverse
from .models import Car, Booking, PromoCode, Profile
from django.db import transaction
from django.db.models import F

logger = logging.getLogger(__name__)

class BookingService:
    @staticmethod
    def create_stripe_session(booking, car, days, pickup_dt, dropoff_dt, final_total):
        """Orchestrate Stripe Checkout Session creation with Decimal precision."""
        try:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            domain_url = settings.DOMAIN_URL
            
            # Convert to cents using string-based Decimal math to avoid floating point errors
            amount_in_cents = int(round(Decimal(str(final_total)) * 100))
            
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[
                    {
                        'price_data': {
                            'currency': settings.STRIPE_CURRENCY,
                            'unit_amount': amount_in_cents,
                            'product_data': {
                                'name': f"Rental: {car.brand} {car.name}",
                                'description': f"{days} days ({pickup_dt.strftime('%d %b, %H:%M')} to {dropoff_dt.strftime('%d %b, %H:%M')})"
                            },
                        },
                        'quantity': 1,
                    },
                ],
                mode='payment',
                success_url=domain_url + reverse('confirmation', args=[booking.id]) + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=domain_url + reverse('payment'),
                client_reference_id=str(booking.id),
                customer_email=booking.user.email,
            )
            return checkout_session
        except Exception as e:
            logger.error(f"Stripe Session Creation Error for Booking {booking.id}: {str(e)}")
            raise e

    @staticmethod
    def create_razorpay_order(booking, final_total):
        """Create a Razorpay Order for UPI & Netbanking payments in India."""
        import razorpay
        try:
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            amount_in_paise = int(round(Decimal(str(final_total)) * 100))
            
            data = {
                "amount": amount_in_paise,
                "currency": "INR",
                "receipt": str(booking.booking_reference),
                "notes": {
                    "email": booking.user.email,
                    "phone": booking.user.profile.phone_number if hasattr(booking.user, 'profile') else ""
                }
            }
            order = client.order.create(data=data)
            return order
        except Exception as e:
            logger.error(f"Razorpay Order Creation Error for Booking {booking.id}: {str(e)}")
            raise e

    @staticmethod
    def clear_booking_session(request):
        """Clear all booking-related keys from the session."""
        keys_to_clear = [
            'pickup_location', 'dropoff_location', 'pickup_date', 'dropoff_date',
            'car_id', 'discount_percent', 'applied_promo', 'applied_promo_id',
            'discount_type', 'discount_value', 'is_outstation'
        ]
        for key in keys_to_clear:
            request.session.pop(key, None)

    @staticmethod
    @transaction.atomic
    def process_successful_payment(booking, session_id):
        """Handle post-payment logic: mark paid, send email, create notifications."""
        try:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            session = stripe.checkout.Session.retrieve(session_id)
            
            if session.payment_status == 'paid':
                booking.is_paid = True
                booking.status = 'Active'
                booking.payment_intent_id = session.payment_intent
                booking.save()
                
                # Proactive logging instead of print
                logger.info(f"Booking {booking.booking_reference} marked as PAID via session {session_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error processing success for Booking {booking.id}: {str(e)}")
            return False

    @staticmethod
    @transaction.atomic
    def process_razorpay_success(booking, razorpay_payment_id, razorpay_order_id, razorpay_signature):
        """Verify Razorpay signature and mark booking as paid."""
        import razorpay
        try:
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            params_dict = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            }
            # Verify signature will raise a SignatureVerificationError if invalid
            client.utility.verify_payment_signature(params_dict)
            
            booking.is_paid = True
            booking.status = 'Active'
            booking.payment_intent_id = razorpay_payment_id
            booking.save()
            
            logger.info(f"Booking {booking.booking_reference} marked as PAID via Razorpay {razorpay_payment_id}")
            return True
        except Exception as e:
            logger.error(f"Razorpay Verification Error for Booking {booking.id}: {str(e)}")
            return False
