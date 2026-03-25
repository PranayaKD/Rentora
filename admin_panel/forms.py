from django import forms
from django.core.exceptions import ValidationError
from core.models import Car


class CarForm(forms.ModelForm):
    class Meta:
        model = Car
        fields = ['name', 'brand', 'category', 'price_per_day', 'seats', 'fuel_type',
                  'transmission', 'engine', 'mileage', 'image', 'is_available']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full bg-slate-50 dark:bg-slate-800 border-slate-200 dark:border-slate-700 rounded-xl px-4 py-3',
                'placeholder': 'e.g. Model S',
            }),
            'brand': forms.TextInput(attrs={
                'class': 'w-full bg-slate-50 dark:bg-slate-800 border-slate-200 dark:border-slate-700 rounded-xl px-4 py-3',
                'placeholder': 'e.g. Tesla',
            }),
            'category': forms.Select(attrs={
                'class': 'w-full bg-slate-50 dark:bg-slate-800 border-slate-200 dark:border-slate-700 rounded-xl px-4 py-3',
            }),
            'price_per_day': forms.NumberInput(attrs={
                'class': 'w-full bg-slate-50 dark:bg-slate-800 border-slate-200 dark:border-slate-700 rounded-xl px-4 py-3',
                'placeholder': '0.00',
            }),
            'seats': forms.NumberInput(attrs={
                'class': 'w-full bg-slate-50 dark:bg-slate-800 border-slate-200 dark:border-slate-700 rounded-xl px-4 py-3',
            }),
            'fuel_type': forms.TextInput(attrs={
                'class': 'w-full bg-slate-50 dark:bg-slate-800 border-slate-200 dark:border-slate-700 rounded-xl px-4 py-3',
                'placeholder': 'e.g. Electric, Petrol',
            }),
            'transmission': forms.TextInput(attrs={
                'class': 'w-full bg-slate-50 dark:bg-slate-800 border-slate-200 dark:border-slate-700 rounded-xl px-4 py-3',
                'placeholder': 'e.g. Automatic',
            }),
            'engine': forms.TextInput(attrs={
                'class': 'w-full bg-slate-50 dark:bg-slate-800 border-slate-200 dark:border-slate-700 rounded-xl px-4 py-3',
                'placeholder': 'e.g. Dual Motor AWD',
            }),
            'mileage': forms.TextInput(attrs={
                'class': 'w-full bg-slate-50 dark:bg-slate-800 border-slate-200 dark:border-slate-700 rounded-xl px-4 py-3',
                'placeholder': 'e.g. 405 km range',
            }),
            'image': forms.FileInput(attrs={
                'class': 'w-full bg-slate-50 dark:bg-slate-800 border-slate-200 dark:border-slate-700 rounded-xl px-4 py-3',
                'accept': 'image/*',
            }),
            'is_available': forms.CheckboxInput(attrs={
                'class': 'rounded text-accent focus:ring-accent',
            }),
        }

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            # 2MB limit
            if image.size > 2 * 1024 * 1024:
                raise ValidationError("Image file size must be under 2MB.")
            
            # Restrict to safe types
            allowed_types = ['image/jpeg', 'image/png', 'image/webp']
            if getattr(image, 'content_type', '') not in allowed_types:
                raise ValidationError("Only JPG, PNG, or WEBP images are allowed.")
        return image

    def clean_price_per_day(self):
        price = self.cleaned_data.get('price_per_day')
        if price is not None and price <= 0:
            raise ValidationError("Price per day must be strictly positive.")
        return price
