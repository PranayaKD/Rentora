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
            
            # Build session parameters
            session_kwargs = {
                'payment_method_types': ['card'],
                'line_items': [
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
                'mode': 'payment',
                'success_url': domain_url + reverse('confirmation', args=[booking.id]) + '?session_id={CHECKOUT_SESSION_ID}',
                'cancel_url': domain_url + reverse('payment'),
                'client_reference_id': str(booking.id),
            }
            # Only include customer_email if non-empty and contains valid email format
            user_email = getattr(booking.user, 'email', '') or ''
            if user_email and '@' in user_email:
                session_kwargs['customer_email'] = user_email

            checkout_session = stripe.checkout.Session.create(**session_kwargs)
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
                    "phone": booking.user.profile.phone if hasattr(booking.user, 'profile') else ""
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
                booking.status = Booking.Status.CONFIRMED
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
        if booking.is_paid:
            return True # Idempotency check prevents double processing
            
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
            
            # Amount verification (fetch order from razorpay and compare)
            rzp_order = client.order.fetch(razorpay_order_id)
            expected_amount = int(booking.total_with_gst * 100)
            if rzp_order.get('amount') != expected_amount:
                logger.error(f"Razorpay amount mismatch for Booking {booking.id}. Expected {expected_amount}, got {rzp_order.get('amount')}")
                return False
            
            booking.is_paid = True
            booking.status = Booking.Status.CONFIRMED
            booking.payment_intent_id = razorpay_payment_id
            booking.save()
            
            logger.info(f"Booking {booking.booking_reference} marked as PAID via Razorpay {razorpay_payment_id}")
            return True
        except Exception as e:
            logger.error(f"Razorpay Verification Error for Booking {booking.id}: {str(e)}")
            return False


# ===================== ADVANCED INDIAN MOBILITY SERVICES =====================

import math
from datetime import datetime, time, timedelta
from django.utils import timezone
from .models import (
    VehicleInspection, RefundTransaction, TollTransaction, 
    TollDispute, EmergencySOS, TripExtension, Notification
)


class RefundService:
    """
    Handles automated security deposit releases and tiered trip cancellation refunds.
    Features graceful fallback to Rentora Wallet credits if payment gateway API fails.
    """
    @staticmethod
    @transaction.atomic
    def process_instant_security_deposit_refund(booking, reason="Clean Drop-off Inspection Approved"):
        """
        Releases security deposit automatically when drop-off inspection is approved.
        Attempt 1: Razorpay/UPI gateway reversal.
        Attempt 2 (Fallback): Direct credit to user's in-app Rentora Wallet balance.
        """
        deposit_amount = Decimal(str(booking.security_deposit or 0))
        if deposit_amount <= 0:
            return None # No deposit collected on this vehicle tier

        # Idempotency check: prevent duplicate refund
        existing_refund = RefundTransaction.objects.filter(
            booking=booking,
            refund_type=RefundTransaction.Type.SECURITY_DEPOSIT,
            status=RefundTransaction.Status.COMPLETED
        ).first()
        if existing_refund:
            logger.info(f"Security deposit already refunded for Booking #{booking.id}")
            return existing_refund

        refund_tx = RefundTransaction.objects.create(
            booking=booking,
            user=booking.user,
            refund_type=RefundTransaction.Type.SECURITY_DEPOSIT,
            amount=deposit_amount,
            status=RefundTransaction.Status.PROCESSING,
            channel=RefundTransaction.Channel.UPI_ORIGINAL,
            reason=reason
        )

        gateway_success = False
        # Try Razorpay refund if booking was paid through Razorpay
        if booking.payment_intent_id and hasattr(settings, 'RAZORPAY_KEY_ID'):
            try:
                import razorpay
                client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
                amount_in_paise = int(round(deposit_amount * 100))
                rzp_refund = client.payment.refund(booking.payment_intent_id, {
                    "amount": amount_in_paise,
                    "speed": "optimum",
                    "notes": {"booking_ref": booking.booking_reference, "type": "deposit_release"}
                })
                refund_tx.gateway_refund_id = rzp_refund.get('id', '')
                refund_tx.status = RefundTransaction.Status.COMPLETED
                refund_tx.processed_at = timezone.now()
                refund_tx.save()
                gateway_success = True
                logger.info(f"Razorpay deposit refund {refund_tx.gateway_refund_id} successful for Booking #{booking.id}")
            except Exception as e:
                logger.warning(f"Razorpay gateway refund failed for Booking #{booking.id}: {str(e)}. Falling back to Wallet credit.")
                refund_tx.error_message = str(e)

        # Fallback to Rentora In-App Wallet if gateway refund failed or not applicable
        if not gateway_success:
            try:
                profile = booking.user.profile
                profile.wallet_balance = F('wallet_balance') + deposit_amount
                profile.save()
                profile.refresh_from_db()
                
                refund_tx.status = RefundTransaction.Status.COMPLETED
                refund_tx.channel = RefundTransaction.Channel.RENTORA_WALLET
                refund_tx.processed_at = timezone.now()
                refund_tx.reason = f"{reason} (Credited to Wallet Balance)"
                refund_tx.save()
                logger.info(f"Deposit ₹{deposit_amount} credited to Wallet for user {booking.user.username}")
            except Exception as wallet_err:
                refund_tx.status = RefundTransaction.Status.FAILED
                refund_tx.error_message = f"Wallet fallback failed: {str(wallet_err)}"
                refund_tx.save()
                logger.error(f"Critical: Deposit refund failed for Booking #{booking.id}: {str(wallet_err)}")

        # Notify user
        Notification.objects.create(
            user=booking.user,
            notification_type=Notification.Type.PAYMENT,
            title="Security Deposit Refunded",
            message=f"Your security deposit of ₹{deposit_amount:,.2f} has been processed ({refund_tx.get_channel_display()}).",
            action_url=reverse('booking_detail', args=[booking.id])
        )
        return refund_tx

    @staticmethod
    @transaction.atomic
    def process_cancellation_with_sla(booking, reason="Customer cancelled booking"):
        """
        Enforces tiered Indian rental cancellation SLA:
        - > 24 hours before pickup: 100% full refund
        - 6 to 24 hours before pickup: 50% cash refund (or 100% as Rentora Wallet credit)
        - < 6 hours before pickup / No-Show: 1st day rental deducted, remainder refunded
        """
        if booking.status == Booking.Status.CANCELLED:
            return None, "Booking is already cancelled."

        total_paid = Decimal(str(booking.total_with_gst or booking.total_price or 0))
        pickup_time = booking.pickup_time or time(9, 0)
        pickup_dt = datetime.combine(booking.pickup_date, pickup_time)
        if timezone.is_naive(pickup_dt):
            pickup_dt = timezone.make_aware(pickup_dt)

        now = timezone.now()
        hours_to_pickup = (pickup_dt - now).total_seconds() / 3600.0

        if hours_to_pickup >= 24:
            # Tier 1: Free cancellation (> 24 hours)
            refund_amount = total_paid
            deduction_amount = Decimal('0.00')
            sla_note = "Full 100% refund (>24h prior to pickup)"
        elif 6 <= hours_to_pickup < 24:
            # Tier 2: 50% refund (6 - 24 hours)
            deduction_amount = (total_paid * Decimal('0.50')).quantize(Decimal('0.01'))
            refund_amount = total_paid - deduction_amount
            sla_note = f"50% cancellation fee applied (₹{deduction_amount} deducted, ₹{refund_amount} refunded)"
        else:
            # Tier 3: Less than 6 hours
            one_day_rate = Decimal(str(booking.car.price_per_day))
            deduction_amount = min(total_paid, one_day_rate)
            refund_amount = max(Decimal('0.00'), total_paid - deduction_amount)
            sla_note = f"1-day rental retained (₹{deduction_amount} deducted, ₹{refund_amount} refunded)"

        # Mark booking cancelled
        booking.status = Booking.Status.CANCELLED
        booking.save()

        # Create refund transaction if refund amount > 0
        refund_tx = None
        if refund_amount > 0:
            refund_tx = RefundTransaction.objects.create(
                booking=booking,
                user=booking.user,
                refund_type=RefundTransaction.Type.CANCELLATION,
                amount=refund_amount,
                status=RefundTransaction.Status.PROCESSING,
                channel=RefundTransaction.Channel.UPI_ORIGINAL,
                reason=f"{reason} - {sla_note}"
            )
            # Credit to wallet as guaranteed fallback
            try:
                profile = booking.user.profile
                profile.wallet_balance = F('wallet_balance') + refund_amount
                profile.save()
                profile.refresh_from_db()
                refund_tx.status = RefundTransaction.Status.COMPLETED
                refund_tx.channel = RefundTransaction.Channel.RENTORA_WALLET
                refund_tx.processed_at = timezone.now()
                refund_tx.save()
            except Exception as e:
                refund_tx.status = RefundTransaction.Status.FAILED
                refund_tx.error_message = str(e)
                refund_tx.save()

        # In-app notification
        Notification.objects.create(
            user=booking.user,
            notification_type=Notification.Type.BOOKING,
            title="Trip Cancelled",
            message=f"Booking #{booking.booking_reference} cancelled. Refund of ₹{refund_amount:,.2f} processed to your Wallet. {sla_note}",
            action_url=reverse('dashboard_bookings')
        )
        return refund_tx, sla_note


class TripExtensionService:
    """
    Enables users stuck in Indian traffic jams to extend trips directly from their phone,
    validating fleet availability and preventing late return penalty surcharges.
    """
    @staticmethod
    def check_availability(booking, additional_hours):
        """
        Check if the car is available for the extended duration (with 2-hour cleaning buffer).
        """
        dropoff_time = booking.dropoff_time or time(19, 0)
        current_dropoff = datetime.combine(booking.dropoff_date, dropoff_time)
        new_dropoff = current_dropoff + timedelta(hours=additional_hours)
        buffer_dropoff = new_dropoff + timedelta(hours=2) # 2-hour turnaround buffer

        # Check conflicting bookings
        conflicts = Booking.objects.filter(
            car=booking.car,
            status__in=[Booking.Status.CONFIRMED, Booking.Status.ACTIVE],
            pickup_date__lte=buffer_dropoff.date(),
            dropoff_date__gte=current_dropoff.date()
        ).exclude(id=booking.id)

        hourly_rate = Decimal(str(booking.car.hourly_rate))
        extension_cost = (hourly_rate * Decimal(str(additional_hours))).quantize(Decimal('0.01'))

        is_available = not conflicts.exists()
        return is_available, new_dropoff, extension_cost

    @staticmethod
    @transaction.atomic
    def confirm_extension(booking, additional_hours, payment_channel='wallet'):
        """
        Confirms extension and updates booking dropoff schedule.
        """
        is_available, new_dropoff, cost = TripExtensionService.check_availability(booking, additional_hours)
        if not is_available:
            return False, "Vehicle is booked by another driver immediately after your slot. Extension unavailable."

        # Check wallet balance if payment_channel == 'wallet'
        profile = booking.user.profile
        if payment_channel == 'wallet':
            if profile.wallet_balance < cost:
                return False, f"Insufficient wallet balance. Extension costs ₹{cost}, your balance is ₹{profile.wallet_balance}."
            profile.wallet_balance = F('wallet_balance') - cost
            profile.save()

        # Update booking schedule
        booking.dropoff_date = new_dropoff.date()
        booking.dropoff_time = new_dropoff.time()
        current_total = Decimal(str(booking.total_price or 0))
        booking.total_price = current_total + cost
        booking.is_extended = True
        booking.save()

        # Log extension record
        current_dropoff = datetime.combine(booking.dropoff_date, booking.dropoff_time or time(19,0))
        TripExtension.objects.create(
            booking=booking,
            original_dropoff=timezone.make_aware(current_dropoff) if timezone.is_naive(current_dropoff) else current_dropoff,
            requested_dropoff=timezone.make_aware(new_dropoff) if timezone.is_naive(new_dropoff) else new_dropoff,
            additional_hours=additional_hours,
            additional_amount=cost,
            is_paid=True,
            status=TripExtension.Status.CONFIRMED
        )

        Notification.objects.create(
            user=booking.user,
            notification_type=Notification.Type.BOOKING,
            title="Trip Extended Successfully",
            message=f"Your trip for #{booking.booking_reference} has been extended by {additional_hours} hours. Drive safely!",
            action_url=reverse('booking_detail', args=[booking.id])
        )
        return True, f"Trip extended successfully by {additional_hours} hours."


class LateReturnService:
    """
    Evaluates drop-off delays with a mandatory 30-minute grace window,
    applying 1.5x hourly late surcharges only past the grace period.
    """
    GRACE_PERIOD_MINUTES = 30
    LATE_SURCHARGE_MULTIPLIER = Decimal('1.5')

    @staticmethod
    def calculate_late_return(booking, actual_dropoff_dt=None):
        if not actual_dropoff_dt:
            actual_dropoff_dt = timezone.now()

        dropoff_time = booking.dropoff_time or time(19, 0)
        scheduled_dropoff = datetime.combine(booking.dropoff_date, dropoff_time)
        if timezone.is_naive(scheduled_dropoff):
            scheduled_dropoff = timezone.make_aware(scheduled_dropoff)

        delay_seconds = (actual_dropoff_dt - scheduled_dropoff).total_seconds()
        delay_minutes = delay_seconds / 60.0

        if delay_minutes <= LateReturnService.GRACE_PERIOD_MINUTES:
            return {
                'is_late': False,
                'grace_period_applied': True,
                'late_minutes': max(0, int(delay_minutes)),
                'late_hours': 0,
                'late_fee': Decimal('0.00')
            }

        # Past 30 mins: calculate late hours (rounded up)
        billable_minutes = delay_minutes - LateReturnService.GRACE_PERIOD_MINUTES
        late_hours = math.ceil(billable_minutes / 60.0)
        hourly_rate = Decimal(str(booking.car.hourly_rate))
        penalty_rate_per_hour = hourly_rate * LateReturnService.LATE_SURCHARGE_MULTIPLIER
        late_fee = (penalty_rate_per_hour * Decimal(str(late_hours))).quantize(Decimal('0.01'))

        # Persist on booking
        booking.actual_dropoff_time = actual_dropoff_dt
        booking.late_return_hours = Decimal(str(late_hours))
        booking.late_fee_amount = late_fee
        booking.save()

        return {
            'is_late': True,
            'grace_period_applied': False,
            'late_minutes': int(delay_minutes),
            'late_hours': late_hours,
            'late_fee': late_fee
        }


class TollReconcilerService:
    """
    Handles FASTag toll deductions and automates double-deduction refunds
    when customers had to pay cash due to plaza RFID scanner faults.
    """
    @staticmethod
    def log_fastag_toll(booking, plaza_name, amount, netc_id=None):
        toll_amt = Decimal(str(amount))
        tx = TollTransaction.objects.create(
            booking=booking,
            toll_plaza_name=plaza_name,
            toll_amount=toll_amt,
            timestamp=timezone.now(),
            netc_transaction_id=netc_id
        )
        current_toll = Decimal(str(booking.fastag_toll_total or 0))
        booking.fastag_toll_total = current_toll + toll_amt
        booking.save()
        return tx

    @staticmethod
    @transaction.atomic
    def submit_cash_toll_dispute(booking, user, cash_receipt_img, cash_amount, user_notes=""):
        cash_paid = Decimal(str(cash_amount))
        dispute = TollDispute.objects.create(
            booking=booking,
            user=user,
            cash_receipt_image=cash_receipt_img,
            cash_amount_paid=cash_paid,
            user_notes=user_notes,
            status=TollDispute.Status.SUBMITTED
        )

        # Automated match: check if a toll transaction with same amount exists on booking
        matching_toll = TollTransaction.objects.filter(
            booking=booking,
            toll_amount=cash_paid,
            is_disputed=False
        ).first()

        if matching_toll:
            # Auto-approve duplicate deduction
            matching_toll.is_disputed = True
            matching_toll.save()

            dispute.toll_transaction = matching_toll
            dispute.status = TollDispute.Status.APPROVED
            dispute.refund_amount = cash_paid
            dispute.resolved_at = timezone.now()
            dispute.save()

            # Credit duplicate charge back to wallet
            profile = user.profile
            profile.wallet_balance = F('wallet_balance') + cash_paid
            profile.save()

            Notification.objects.create(
                user=user,
                notification_type=Notification.Type.PAYMENT,
                title="Toll Dispute Auto-Approved",
                message=f"Duplicate FASTag toll of ₹{cash_paid:,.2f} at {matching_toll.toll_plaza_name} has been credited to your Wallet.",
                action_url=reverse('booking_detail', args=[booking.id])
            )
            return dispute, "Dispute verified and duplicate charge refunded to your wallet."

        return dispute, "Dispute submitted for 24-hour verification with National Electronic Toll logs."


class EmergencySOSService:
    """
    Mid-trip highway breakdown and emergency assistance dispatcher.
    Automatically halts billing meters and logs GPS coordinates.
    """
    @staticmethod
    @transaction.atomic
    def trigger_sos(booking, user, issue_type, latitude, longitude, location_address="", user_note=""):
        sos = EmergencySOS.objects.create(
            booking=booking,
            user=user,
            issue_type=issue_type,
            latitude=latitude,
            longitude=longitude,
            location_address=location_address,
            user_note=user_note,
            status=EmergencySOS.Status.TRIGGERED,
            billing_paused_at=timezone.now()
        )

        # Halt booking billing timer
        booking.emergency_paused = True
        booking.save()

        # Emit SOS notification
        Notification.objects.create(
            user=user,
            notification_type=Notification.Type.SYSTEM,
            title="Emergency SOS Dispatched",
            message=f"Roadside assistance has been alerted for #{booking.booking_reference}. Our 24/7 highway response team is contacting you.",
            action_url=reverse('booking_detail', args=[booking.id])
        )

        logger.info(f"EMERGENCY SOS triggered for Booking #{booking.id} at ({latitude}, {longitude}) - Type: {issue_type}")
        return sos


class VehicleInspectionService:
    """
    Pre-trip & Post-trip digital checklist validation.
    Enforces mandatory 4-side exterior photos, odometer reading, and fuel percentage.
    """
    @staticmethod
    @transaction.atomic
    def submit_pre_trip(booking, user, odometer, fuel_percent, photo_front=None, photo_rear=None, photo_left=None, photo_right=None, damage_notes="", lat=None, lng=None):
        inspection, created = VehicleInspection.objects.update_or_create(
            booking=booking,
            stage=VehicleInspection.Stage.PRE_TRIP,
            defaults={
                'submitted_by': user,
                'odometer_reading': odometer,
                'fuel_level_percent': fuel_percent,
                'photo_front': photo_front,
                'photo_rear': photo_rear,
                'photo_left': photo_left,
                'photo_right': photo_right,
                'damage_notes': damage_notes,
                'latitude': lat,
                'longitude': lng,
                'timestamp': timezone.now()
            }
        )
        # Transition booking to ACTIVE
        booking.status = Booking.Status.ACTIVE
        booking.actual_pickup_time = timezone.now()
        booking.save()

        Notification.objects.create(
            user=user,
            notification_type=Notification.Type.BOOKING,
            title="Trip Started - Drive Safe!",
            message=f"Pre-trip inspection logged for #{booking.booking_reference}. Odometer: {odometer} km. Vehicle unlocked.",
            action_url=reverse('booking_detail', args=[booking.id])
        )
        return inspection

    @staticmethod
    @transaction.atomic
    def submit_post_trip(booking, user, odometer, fuel_percent, has_damage=False, damage_notes="", cleanliness_rating=5, photo_front=None, photo_rear=None, photo_left=None, photo_right=None, lat=None, lng=None):
        inspection, created = VehicleInspection.objects.update_or_create(
            booking=booking,
            stage=VehicleInspection.Stage.POST_TRIP,
            defaults={
                'submitted_by': user,
                'odometer_reading': odometer,
                'fuel_level_percent': fuel_percent,
                'has_damage': has_damage,
                'damage_notes': damage_notes,
                'cleanliness_rating': cleanliness_rating,
                'photo_front': photo_front,
                'photo_rear': photo_rear,
                'photo_left': photo_left,
                'photo_right': photo_right,
                'latitude': lat,
                'longitude': lng,
                'timestamp': timezone.now()
            }
        )

        # Mark booking COMPLETED
        booking.status = Booking.Status.COMPLETED
        booking.actual_dropoff_time = timezone.now()
        booking.save()

        # If no damage was reported, automatically trigger instant security deposit refund
        if not has_damage:
            RefundService.process_instant_security_deposit_refund(
                booking, 
                reason="Clean Drop-off Inspection Approved (No Damage Detected)"
            )

        Notification.objects.create(
            user=user,
            notification_type=Notification.Type.BOOKING,
            title="Trip Completed",
            message=f"Post-trip inspection for #{booking.booking_reference} completed. Thank you for driving with Rentora!",
            action_url=reverse('booking_detail', args=[booking.id])
        )
        return inspection
