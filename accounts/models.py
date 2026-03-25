from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.utils import timezone

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(
        max_length=15, 
        blank=True,
        db_index=True,
        validators=[RegexValidator(r'^\+91[6-9]\d{9}$', 'Enter a valid Indian mobile number starting with +91')]
    )
    profile_photo = models.ImageField(upload_to='profiles/', blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    
    # KYC Fields (India Specific)
    license_number = models.CharField(max_length=50, blank=True)
    license_image = models.ImageField(upload_to='licenses/', blank=True, null=True)
    aadhaar_number = models.CharField(
        max_length=12, 
        blank=True,
        validators=[RegexValidator(r'^\d{12}$', 'Aadhaar number must be exactly 12 digits')]
    )
    pan_number = models.CharField(
        max_length=10, 
        blank=True,
        validators=[RegexValidator(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$', 'Enter a valid PAN card number (e.g., ABCDE1234F)')]
    )
    is_verified = models.BooleanField(default=False)
    
    # Referral System
    referral_code = models.CharField(max_length=20, unique=True, blank=True, null=True)
    referred_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals')
    wallet_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.referral_code:
            import random, string
            self.referral_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        super().save(*args, **kwargs)

    @property
    def age(self):
        if not self.date_of_birth:
            return 0
        today = timezone.now().date()
        return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))


    def __str__(self):
        return self.user.username
