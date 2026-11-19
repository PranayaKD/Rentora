import rentora_project.compat  # noqa: F401
import logging
from decimal import Decimal
import uuid
from django.db import models, transaction
from django.contrib.auth.models import User
from django.utils import timezone
from .constants import GST_PERCENTAGE, REFERRAL_REWARD_INR
from accounts.models import UserProfile as Profile

logger = logging.getLogger(__name__)


class Car(models.Model):
    CATEGORY_CHOICES = [
        ('Hatchback', 'Hatchback'),
        ('Sedan', 'Sedan'),
        ('Compact SUV', 'Compact SUV'),
        ('SUV', 'SUV'),
        ('Premium SUV', 'Premium SUV'),
        ('Luxury Sedan', 'Luxury Sedan'),
        ('Ultra Luxury', 'Ultra Luxury'),
        ('Electric', 'Electric'),
        ('MPV', 'MPV'),
        ('Off-road SUV', 'Off-road SUV'),
        ('Micro SUV', 'Micro SUV'),
        ('Hybrid', 'Hybrid'),
    ]
    BRAND_CHOICES = [
        ('Maruti Suzuki', 'Maruti Suzuki'),
        ('Tata', 'Tata'),
        ('Hyundai', 'Hyundai'),
        ('Mahindra', 'Mahindra'),
        ('Kia', 'Kia'),
        ('Toyota', 'Toyota'),
        ('Honda', 'Honda'),
        ('Volkswagen', 'Volkswagen'),
        ('Skoda', 'Skoda'),
        ('MG', 'MG'),
        ('BMW', 'BMW'),
        ('Mercedes-Benz', 'Mercedes-Benz'),
        ('Audi', 'Audi'),
        ('Porsche', 'Porsche'),
        ('Ferrari', 'Ferrari'),
        ('Lamborghini', 'Lamborghini'),
        ('Rolls Royce', 'Rolls Royce'),
        ('Bentley', 'Bentley'),
        ('Tesla', 'Tesla'),
        ('Range Rover', 'Range Rover'),
    ]
    name = models.CharField(max_length=100)
    brand = models.CharField(max_length=50, choices=BRAND_CHOICES)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    price_per_day = models.DecimalField(max_digits=8, decimal_places=2, db_index=True)
    security_deposit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    free_km = models.IntegerField(default=150, blank=True, null=True)
    seats = models.IntegerField(db_index=True)
    fuel_type = models.CharField(max_length=30, db_index=True)
    transmission = models.CharField(max_length=20)
    engine = models.CharField(max_length=50)
    mileage = models.CharField(max_length=30)
    image = models.ImageField(upload_to='cars/', blank=True, null=True)
    is_available = models.BooleanField(default=True)
    features = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['is_available']),
            models.Index(fields=['brand']),
            models.Index(fields=['name']),
            models.Index(fields=['created_at']),
        ]
        constraints = [
            models.CheckConstraint(check=models.Q(price_per_day__gte=0), name='car_price_per_day_positive'),
        ]

    def __str__(self):
        return f"{self.brand} {self.name}"

    @property
    def rating(self):
        if hasattr(self, 'annotated_rating'):
            if self.annotated_rating is not None:
                return float(round(self.annotated_rating, 1))
        else:
            avg = self.reviews.aggregate(models.Avg('rating'))['rating__avg']
            if avg:
                return float(round(avg, 1))
        # Deterministic fallback rating based on vehicle ID when reviews are empty
        import random
        random.seed(self.id)
        return round(random.uniform(4.7, 4.9), 1)

    @property
    def rating_count(self):
        if hasattr(self, 'annotated_review_count'):
            count = self.annotated_review_count or 0
        else:
            count = self.reviews.count()
        if count > 0:
            return count
        # Deterministic review count fallback when no reviews exist
        import random
        random.seed(self.id)
        return random.randint(12, 48)

    @property
    def hourly_rate(self):
        feat = self.features or {}
        if 'hourly_rate' in feat:
            return int(feat['hourly_rate'])
        return max(49, int(round(float(self.price_per_day) / 24)))

    @property
    def hourly_rate_unlimited(self):
        feat = self.features or {}
        if 'unlimited_hourly_rate' in feat:
            return int(feat['unlimited_hourly_rate'])
        return int(round(self.hourly_rate * 1.2))

    @property
    def daily_rate(self):
        return self.price_per_day

    @property
    def price_per_day_unlimited(self):
        feat = self.features or {}
        if 'unlimited_daily_rate' in feat:
            return int(feat['unlimited_daily_rate'])
        return int(round(float(self.price_per_day) * 1.2))

    @property
    def badge(self):
        feat = self.features or {}
        if feat.get('badge'):
            return feat['badge']
        if self.rating >= 4.85:
            return 'Guest Favorite'
        elif self.rating >= 4.75:
            return 'Top Rated'
        return 'Verified Fleet'

    @property
    def host_name(self):
        feat = self.features or {}
        return feat.get('host_name', 'Rentora Fleet Host')

    @property
    def host_type(self):
        feat = self.features or {}
        return feat.get('host_type', 'Professional Host')

    @property
    def distance_km(self):
        feat = self.features or {}
        if 'distance_km' in feat:
            return feat['distance_km']
        return round(1.2 + ((self.id or 1) % 12) * 0.8, 1)

    @property
    def delivery_available(self):
        feat = self.features or {}
        return feat.get('delivery_available', True)

    @property
    def extra_km_rate(self):
        feat = self.features or {}
        return feat.get('extra_km_rate', 7)

    @property
    def gallery_images(self):
        feat = self.features or {}
        imgs = feat.get('gallery_images', [])
        if imgs and isinstance(imgs, list):
            return imgs
        if self.image:
            return [self.image.url]
        return ['/static/images/ui/car-placeholder.jpg']

    @classmethod
    def is_available_for_dates(cls, car_id, pickup_date, dropoff_date, exclude_booking_id=None, exclude_user_id=None):
        from django.apps import apps
        from django.utils import timezone
        from datetime import timedelta
        Booking = apps.get_model('core', 'Booking')

        qs = Booking.objects.filter(
            car_id=car_id,
            pickup_date__lt=dropoff_date,
            dropoff_date__gt=pickup_date
        )

        if exclude_booking_id:
            qs = qs.exclude(id=exclude_booking_id)

        # Confirmed or paid bookings strictly block the vehicle
        confirmed_block = qs.filter(
            models.Q(status__in=[Booking.Status.CONFIRMED, 'Confirmed', 'Active']) |
            models.Q(is_paid=True)
        )
        if confirmed_block.exists():
            return False

        # Unpaid pending bookings older than 15 minutes expire automatically.
        # If exclude_user_id is provided, the current user is not blocked by their own previous attempt.
        cutoff = timezone.now() - timedelta(minutes=15)
        pending_qs = qs.filter(
            status__in=[Booking.Status.PENDING, 'Pending'],
            is_paid=False,
            created_at__gte=cutoff
        )
        if exclude_user_id:
            pending_qs = pending_qs.exclude(user_id=exclude_user_id)

        return not pending_qs.exists()

    def calculate_rental_price(self, pickup_date, dropoff_date):
        """
        Calculate rental subtotal with a 15% weekend surcharge applied to Friday, Saturday, and Sunday.
        """
        from datetime import timedelta
        total_subtotal = Decimal('0.00')
        current_date = pickup_date
        
        # Minimum booking duration is 1 day
        duration = dropoff_date - pickup_date
        total_days = max(1, duration.days)
        
        for i in range(total_days):
            day_price = Decimal(str(self.price_per_day))
            # weekday() 4=Fri, 5=Sat, 6=Sun
            if current_date.weekday() in [4, 5, 6]:
                day_price *= Decimal('1.15')
            
            total_subtotal += day_price
            current_date += timedelta(days=1)
            
        return total_subtotal.quantize(Decimal('0.01'))

    @property
    def weekend_price_estimate(self):
        """Estimate for 1 weekend day (15% surcharge) for UI display."""
        return (Decimal(str(self.price_per_day)) * Decimal('1.15')).quantize(Decimal('0'))


class Booking(models.Model):
    class Status(models.TextChoices):
        PAYMENT_PENDING = 'PAYMENT_PENDING', 'Payment Pending'
        PENDING = 'PENDING', 'Pending'
        CONFIRMED = 'CONFIRMED', 'Confirmed'
        ACTIVE = 'ACTIVE', 'Active (Trip in Progress)'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='bookings')
    booking_reference = models.CharField(max_length=12, editable=False, null=True, blank=True, default='')
    pickup_date = models.DateField()
    dropoff_date = models.DateField()
    pickup_time = models.TimeField(null=True, blank=True)
    dropoff_time = models.TimeField(null=True, blank=True)
    pickup_location = models.CharField(max_length=255, default='Main Office')
    dropoff_location = models.CharField(max_length=255, default='Main Office')
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    stripe_session_id = models.CharField(max_length=255, blank=True, null=True, unique=True)
    razorpay_order_id = models.CharField(max_length=255, blank=True, null=True, unique=True)
    
    # Financial tracking
    is_paid = models.BooleanField(default=False)
    payment_intent_id = models.CharField(max_length=255, blank=True, null=True)
    
    promo_code = models.CharField(max_length=50, blank=True, null=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    is_outstation = models.BooleanField(default=False)
    security_deposit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    gst_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_with_gst = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    gst_number = models.CharField(max_length=15, blank=True, null=True) # For commercial bookings

    # Operational lifecycle tracking
    actual_pickup_time = models.DateTimeField(null=True, blank=True)
    actual_dropoff_time = models.DateTimeField(null=True, blank=True)
    late_return_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    late_fee_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fastag_toll_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_extended = models.BooleanField(default=False)
    emergency_paused = models.BooleanField(default=False)
    
    # Notifications Tracking
    abandoned_reminder_sent = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # self.clean() omitted here to avoid interfering with payment webhook updates
        if not self.booking_reference:
            # Generate short booking reference (e.g. RNT-XXXXXXXX)
            import uuid
            uid = str(uuid.uuid4()).upper().replace('-', '')
            ref = str(uid)[:8]
            self.booking_reference = f"RNT-{ref}"
        
        # Calculate GST on rental amount (security deposit is not subject to tax)
        if not self.pk and self.car:
            self.security_deposit = self.security_deposit or self.car.security_deposit
            
        rental_amount = Decimal(str(self.total_price))
        gst_fraction = Decimal(str(GST_PERCENTAGE)) / Decimal('100')
        self.gst_amount = (rental_amount * gst_fraction).quantize(Decimal('0.01'))
        self.total_with_gst = rental_amount + self.gst_amount + Decimal(str(self.security_deposit))
        
        # Credit referral reward to user and referrer wallet once booking is completed
        if self.pk:
            from django.db import transaction
            try:
                old_status = Booking.objects.get(pk=self.pk).status
                if old_status.lower() != 'completed' and self.status.lower() == 'completed':
                    with transaction.atomic():
                        from .models import Profile
                        user_profile = Profile.objects.select_for_update().get(user=self.user)
                        user_profile.wallet_balance += REFERRAL_REWARD_INR
                        user_profile.save(update_fields=['wallet_balance'])
                        
                        if user_profile.referred_by:
                            referrer_profile = Profile.objects.select_for_update().get(id=user_profile.referred_by.id)
                            referrer_profile.wallet_balance += REFERRAL_REWARD_INR
                            referrer_profile.save(update_fields=['wallet_balance'])
            except Exception as e:
                logger.error(f"Referral Reward Payment Error during booking save: {str(e)}", exc_info=True)
        
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['pickup_date']),
            models.Index(fields=['is_paid']),
            models.Index(fields=['created_at']),
            models.Index(fields=['car', 'status', 'pickup_date', 'dropoff_date']),
        ]
        constraints = [
            models.CheckConstraint(check=models.Q(dropoff_date__gte=models.F('pickup_date')), name='booking_dropoff_gte_pickup'),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.car.name} ({self.pickup_date} to {self.dropoff_date})"

    def check_overlap(self):
        """Check if this booking overlaps with any existing confirmed or pending bookings."""
        # We check against CONFIRMED bookings and PENDING bookings (to prevent race conditions during payment)
        overlapping_bookings = Booking.objects.filter(
            car=self.car,
            status__in=[Booking.Status.PENDING, Booking.Status.CONFIRMED, 'Pending', 'Active', 'Confirmed'],
        ).exclude(pk=self.pk).filter(
            pickup_date__lte=self.dropoff_date,
            dropoff_date__gte=self.pickup_date
        )
        return overlapping_bookings.exists()

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.pickup_date and self.dropoff_date:
            if self.pickup_date > self.dropoff_date:
                raise ValidationError("Drop-off date cannot be before pick-up date.")
            
            if self.check_overlap():
                raise ValidationError(f"The {self.car.name} is already reserved for these dates. Please choose different dates.")


    @property
    def duration_days(self):
        return (self.dropoff_date - self.pickup_date).days


class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='reviews')
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='review')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.car} - {self.rating}★"


class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlists')
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='wishlisted_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'car')

    def __str__(self):
        return f"{self.user.username} ♥ {self.car}"


class PromoCode(models.Model):
    DISCOUNT_TYPES = [
        ('Percentage', 'Percentage'),
        ('Fixed', 'Fixed Amount'),
    ]
    code = models.CharField(max_length=20, unique=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES, default='Percentage')
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    min_purchase = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    expiry_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    usage_limit = models.IntegerField(default=100)
    used_count = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.code} ({self.discount_value}{'%' if self.discount_type == 'Percentage' else ' off'})"

    def is_valid(self, cart_total=0):
        now = timezone.now()
        basic_valid = self.is_active and self.expiry_date > now and self.used_count < self.usage_limit
        if not basic_valid:
            return False
        return float(cart_total) >= float(self.min_purchase)


class PushSubscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='push_subscriptions')
    subscription_info = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Push Subscription for {self.user.username}"


class Notification(models.Model):
    class Type(models.TextChoices):
        BOOKING = 'booking', 'Booking'
        PAYMENT = 'payment', 'Payment'
        REMINDER = 'reminder', 'Reminder'
        REVIEW = 'review', 'Review'
        KYC = 'kyc', 'KYC'
        PROMO = 'promo', 'Promo'
        SYSTEM = 'system', 'System'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=Type.choices)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    action_url = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user} - {self.title}"


# ===================== INDIAN MOBILITY ADVANCED MODELS =====================

class VehicleInspection(models.Model):
    """
    Digital pre-trip and post-trip vehicle inspection checklist.
    Prevents disputes by capturing timestamped 4-side exterior photos,
    instrument cluster odometer readings, and fuel gauge levels.
    """
    class Stage(models.TextChoices):
        PRE_TRIP = 'PRE_TRIP', 'Pre-Trip Inspection'
        POST_TRIP = 'POST_TRIP', 'Post-Trip Drop-off Inspection'

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='inspections')
    stage = models.CharField(max_length=20, choices=Stage.choices)
    
    # 4-side exterior photos
    photo_front = models.ImageField(upload_to='inspections/', null=True, blank=True)
    photo_rear = models.ImageField(upload_to='inspections/', null=True, blank=True)
    photo_left = models.ImageField(upload_to='inspections/', null=True, blank=True)
    photo_right = models.ImageField(upload_to='inspections/', null=True, blank=True)
    
    # Cluster readings
    odometer_reading = models.PositiveIntegerField(help_text="Odometer KM reading at inspection")
    odometer_photo = models.ImageField(upload_to='inspections/', null=True, blank=True)
    fuel_level_percent = models.PositiveSmallIntegerField(default=100, help_text="Fuel/Battery percentage (0-100)")
    fuel_gauge_photo = models.ImageField(upload_to='inspections/', null=True, blank=True)
    
    # Condition assessment
    has_damage = models.BooleanField(default=False)
    damage_notes = models.TextField(blank=True, default='')
    cleanliness_rating = models.PositiveSmallIntegerField(default=5, help_text="1 (poor) to 5 (spotless)")
    
    # Audit trail
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['timestamp']
        unique_together = ('booking', 'stage')

    def __str__(self):
        return f"{self.get_stage_display()} - Booking #{self.booking.booking_reference or self.booking.id}"


class RefundTransaction(models.Model):
    """
    Tracks automated security deposit releases, trip cancellations,
    and dispute reimbursements via UPI/Razorpay or Rentora Wallet.
    """
    class Type(models.TextChoices):
        SECURITY_DEPOSIT = 'SECURITY_DEPOSIT', 'Security Deposit Release'
        CANCELLATION = 'CANCELLATION', 'Trip Cancellation Refund'
        TOLL_REIMBURSEMENT = 'TOLL_REIMBURSEMENT', 'Toll Double-Deduction Reimbursement'
        COMPENSATION = 'COMPENSATION', 'Service Delay / Host Compensation'

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending Processing'
        PROCESSING = 'PROCESSING', 'Processing with Gateway'
        COMPLETED = 'COMPLETED', 'Refund Completed'
        FAILED = 'FAILED', 'Refund Failed'

    class Channel(models.TextChoices):
        UPI_ORIGINAL = 'UPI_ORIGINAL', 'Original UPI / Card Account'
        RENTORA_WALLET = 'RENTORA_WALLET', 'Rentora Wallet Balance'
        BANK_TRANSFER = 'BANK_TRANSFER', 'Direct Bank Transfer (NEFT/IMPS)'

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='refund_transactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='refunds')
    refund_type = models.CharField(max_length=30, choices=Type.choices)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    channel = models.CharField(max_length=20, choices=Channel.choices, default=Channel.UPI_ORIGINAL)
    
    gateway_refund_id = models.CharField(max_length=100, blank=True, null=True)
    reason = models.TextField(blank=True, default='')
    error_message = models.TextField(blank=True, default='')
    
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Refund ₹{self.amount} ({self.status}) for Booking #{self.booking.booking_reference or self.booking.id}"


class TollTransaction(models.Model):
    """
    Electronic FASTag toll deductions logged during the trip.
    """
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='toll_transactions')
    toll_plaza_name = models.CharField(max_length=200)
    toll_amount = models.DecimalField(max_digits=8, decimal_places=2)
    timestamp = models.DateTimeField()
    fastag_tag_id = models.CharField(max_length=100, blank=True, default='')
    netc_transaction_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    is_disputed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.toll_plaza_name} - ₹{self.toll_amount}"


class TollDispute(models.Model):
    """
    Customer dispute when cash was paid at toll plaza due to scanner failure,
    preventing double deduction from their deposit or wallet.
    """
    class Status(models.TextChoices):
        SUBMITTED = 'SUBMITTED', 'Dispute Submitted'
        VERIFYING = 'VERIFYING', 'Verifying with Toll Plaza'
        APPROVED = 'APPROVED', 'Dispute Approved & Refunded'
        REJECTED = 'REJECTED', 'Dispute Rejected'

    toll_transaction = models.ForeignKey(TollTransaction, on_delete=models.SET_NULL, related_name='disputes', null=True, blank=True)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='toll_disputes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    cash_receipt_image = models.ImageField(upload_to='toll_receipts/')
    cash_amount_paid = models.DecimalField(max_digits=8, decimal_places=2)
    user_notes = models.TextField(blank=True, default='')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SUBMITTED)
    refund_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Toll Dispute #{self.id} for Booking #{self.booking.booking_reference or self.booking.id}"


class EmergencySOS(models.Model):
    """
    Emergency SOS for highway breakdowns, punctures, battery jumpstarts,
    and collisions with automated billing timer pauses.
    """
    class IssueType(models.TextChoices):
        TIRE_PUNCTURE = 'TIRE_PUNCTURE', 'Flat Tire / Puncture'
        BATTERY_DEAD = 'BATTERY_DEAD', 'Dead Battery / Jumpstart'
        ENGINE_OVERHEAT = 'ENGINE_OVERHEAT', 'Engine Overheating / Mechanical'
        ACCIDENT = 'ACCIDENT', 'Accident / Collision'
        LOCKOUT = 'LOCKOUT', 'Key Locked Inside Vehicle'
        OTHER = 'OTHER', 'Other Emergency'

    class Status(models.TextChoices):
        TRIGGERED = 'TRIGGERED', 'SOS Triggered'
        DISPATCHED = 'DISPATCHED', 'Assistance Dispatched'
        RESOLVED = 'RESOLVED', 'Issue Resolved'
        CANCELLED = 'CANCELLED', 'False Alarm / Cancelled'

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='sos_alerts')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    issue_type = models.CharField(max_length=30, choices=IssueType.choices)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    location_address = models.CharField(max_length=255, blank=True, default='')
    user_note = models.TextField(blank=True, default='')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.TRIGGERED)
    billing_paused_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"SOS {self.get_issue_type_display()} for Booking #{self.booking.booking_reference or self.booking.id}"


class TripExtension(models.Model):
    """
    In-trip extension request to avoid traffic-induced late penalty fees.
    """
    class Status(models.TextChoices):
        REQUESTED = 'REQUESTED', 'Extension Requested'
        CONFIRMED = 'CONFIRMED', 'Confirmed & Extended'
        REJECTED = 'REJECTED', 'Unavailable / Rejected'

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='extensions')
    original_dropoff = models.DateTimeField()
    requested_dropoff = models.DateTimeField()
    additional_hours = models.PositiveIntegerField(default=1)
    additional_amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.REQUESTED)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Extension +{self.additional_hours}hrs for Booking #{self.booking.booking_reference or self.booking.id}"


# ===================== SIGNALS =====================
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache

@receiver([post_save, post_delete], sender=Car)
@receiver([post_save, post_delete], sender=Review)
def clear_homepage_cache(sender, **kwargs):
    """Automatically clear the homepage cache when cars or reviews are updated."""
    cache.delete('homepage_cars_data')
    logger.info("Homepage car data cache cleared due to model update.")
