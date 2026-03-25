from django import forms
from django.contrib.auth.models import User
from .models import UserProfile


class LoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'placeholder': 'alex@example.com',
            'class': 'w-full h-14 pl-12 pr-5 rounded-2xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-[#00c9a7]/20 focus:border-[#00c9a7] transition-all',
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': '••••••••',
            'class': 'w-full h-14 pl-12 pr-14 rounded-2xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-[#00c9a7]/20 focus:border-[#00c9a7] transition-all',
        })
    )


class SignupForm(forms.Form):
    full_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'Alex Morgan',
            'class': 'w-full h-12 pl-12 pr-5 rounded-2xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-[#00c9a7]/20 focus:border-[#00c9a7] transition-all',
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'placeholder': 'alex@example.com',
            'class': 'w-full h-12 pl-12 pr-5 rounded-2xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-[#00c9a7]/20 focus:border-[#00c9a7] transition-all',
        })
    )
    
    COUNTRY_CODES = [
        ('+1', '🇺🇸 +1'),
        ('+44', '🇬🇧 +44'),
        ('+91', '🇮🇳 +91'),
        ('+61', '🇦🇺 +61'),
        ('+81', '🇯🇵 +81'),
        ('+49', '🇩🇪 +49'),
    ]
    
    country_code = forms.ChoiceField(
        choices=COUNTRY_CODES,
        initial='+91',
        widget=forms.Select(attrs={
            'class': 'w-[110px] h-12 px-3 rounded-2xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-[#00c9a7]/20 focus:border-[#00c9a7] transition-all appearance-none cursor-pointer',
        })
    )
    
    phone = forms.CharField(
        max_length=10,
        min_length=10,
        widget=forms.TextInput(attrs={
            'placeholder': '9876543210',
            'class': 'flex-1 h-12 px-5 rounded-2xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-[#00c9a7]/20 focus:border-[#00c9a7] transition-all',
        })
    )
    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full h-12 px-5 rounded-2xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-[#00c9a7]/20 focus:border-[#00c9a7] transition-all',
        })
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': '••••••••',
            'class': 'w-full h-12 pl-12 pr-12 rounded-2xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-[#00c9a7]/20 focus:border-[#00c9a7] transition-all',
        })
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': '••••••••',
            'class': 'w-full h-12 pl-12 pr-12 rounded-2xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-[#00c9a7]/20 focus:border-[#00c9a7] transition-all',
        })
    )

    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')
        if dob:
            from django.utils import timezone
            today = timezone.now().date()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            if age < 21:
                raise forms.ValidationError("You must be at least 21 years old to rent a car.")
        return dob

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not phone.isdigit():
            raise forms.ValidationError("Phone number must contain only digits.")
        if len(phone) != 10:
            raise forms.ValidationError("Phone number must be exactly 10 digits.")
        return "+91" + phone

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if len(password) < 8:
            raise forms.ValidationError("Password must be at least 8 characters long.")
        if not any(char.isdigit() for char in password):
            raise forms.ValidationError("Password must contain at least one digit.")
        import re
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            raise forms.ValidationError("Password must contain at least one special character.")
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm = cleaned_data.get('confirm_password')
        if password and confirm and password != confirm:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email


class ProfileForm(forms.Form):
    full_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'w-full h-12 px-5 rounded-2xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-[#00c9a7]/20 focus:border-[#00c9a7] transition-all',
        })
    )
    phone = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': '+91XXXXXXXXXX',
            'class': 'w-full h-12 px-5 rounded-2xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-[#00c9a7]/20 focus:border-[#00c9a7] transition-all',
        })
    )
    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full h-12 px-5 rounded-2xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-[#00c9a7]/20 focus:border-[#00c9a7] transition-all',
        })
    )
    profile_photo = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'hidden',
            'accept': 'image/*',
        })
    )
    license_number = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'DL-XXXXXXXXXXXXX',
            'class': 'w-full h-12 px-5 rounded-2xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-[#00c9a7]/20 focus:border-[#00c9a7] transition-all',
        })
    )
    aadhaar_number = forms.CharField(
        max_length=12,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': '12 Digit Aadhaar Number',
            'class': 'w-full h-12 px-5 rounded-2xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-[#00c9a7]/20 focus:border-[#00c9a7] transition-all',
        })
    )
    pan_number = forms.CharField(
        max_length=10,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'PAN Card Number',
            'class': 'w-full h-12 px-5 rounded-2xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-[#00c9a7]/20 focus:border-[#00c9a7] transition-all',
        })
    )
    license_image = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-primary/10 file:text-primary hover:file:bg-primary/20 transition-all',
            'accept': 'image/*',
        })
    )

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone and not phone.startswith('+91'):
             if phone.isdigit() and len(phone) == 10:
                 phone = "+91" + phone
             else:
                 raise forms.ValidationError("Phone number must be in +91XXXXXXXXXX format.")
        return phone

    def clean_aadhaar_number(self):
        val = self.cleaned_data.get('aadhaar_number')
        if val and (not val.isdigit() or len(val) != 12):
            raise forms.ValidationError("Aadhaar must be exactly 12 digits.")
        return val

    def clean_pan_number(self):
        val = self.cleaned_data.get('pan_number')
        if val:
            import re
            if not re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$', val.upper()):
                raise forms.ValidationError("Enter a valid PAN card number.")
        return val.upper() if val else val


class ChangePasswordForm(forms.Form):
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Current password',
            'class': 'w-full h-12 px-5 rounded-2xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-[#00c9a7]/20 focus:border-[#00c9a7] transition-all',
        })
    )
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'New password',
            'class': 'w-full h-12 px-5 rounded-2xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-[#00c9a7]/20 focus:border-[#00c9a7] transition-all',
        })
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Confirm new password',
            'class': 'w-full h-12 px-5 rounded-2xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-[#00c9a7]/20 focus:border-[#00c9a7] transition-all',
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        new_pw = cleaned_data.get('new_password')
        confirm = cleaned_data.get('confirm_password')
        if new_pw and confirm and new_pw != confirm:
            raise forms.ValidationError("New passwords do not match.")
        return cleaned_data
