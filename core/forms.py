from django import forms
from django.utils import timezone
from datetime import timedelta
from .models import Car, Review


class BookingLocationForm(forms.Form):
    pickup_location = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'placeholder': 'Search or pin pickup location'})
    )
    dropoff_location = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'placeholder': 'Search or pin drop-off location'})
    )


class BookingDatesForm(forms.Form):
    pickup_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'text', 'id': 'pickup_picker'})
    )
    dropoff_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'text', 'id': 'dropoff_picker'})
    )

    def clean(self):
        cleaned_data = super().clean()
        pickup = cleaned_data.get('pickup_date')
        dropoff = cleaned_data.get('dropoff_date')
        
        if pickup:
            if pickup < timezone.now() - timedelta(minutes=15):
                raise forms.ValidationError("Pickup date cannot be in the past.")
                
        if pickup and dropoff and dropoff <= pickup:
            raise forms.ValidationError("Drop-off date must be after pickup date.")
            
        return cleaned_data


class BookingStepOneForm(forms.Form):
    """Unified Step 1 form combining location and date/time selection."""
    pickup_location = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search hub, airport or pin location',
            'id': 'id_pickup_location',
            'autocomplete': 'off',
        })
    )
    dropoff_location = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search drop-off location',
            'id': 'id_dropoff_location',
            'autocomplete': 'off',
        })
    )
    pickup_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'type': 'text',
            'id': 'pickup_picker',
            'placeholder': 'Select pickup date & time',
        })
    )
    dropoff_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'type': 'text',
            'id': 'dropoff_picker',
            'placeholder': 'Select return date & time',
        })
    )
    is_outstation = forms.BooleanField(required=False)

    def clean(self):
        cleaned_data = super().clean()
        pickup_loc = cleaned_data.get('pickup_location')
        dropoff_loc = cleaned_data.get('dropoff_location')
        pickup_dt = cleaned_data.get('pickup_date')
        dropoff_dt = cleaned_data.get('dropoff_date')

        if not dropoff_loc and pickup_loc:
            cleaned_data['dropoff_location'] = pickup_loc

        if pickup_dt:
            if pickup_dt < timezone.now() - timedelta(minutes=15):
                raise forms.ValidationError("Pickup date cannot be in the past.")

        if pickup_dt and dropoff_dt and dropoff_dt <= pickup_dt:
            raise forms.ValidationError("Return date and time must be after pickup date and time.")

        return cleaned_data


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Share your experience...'}),
        }


class ContactForm(forms.Form):
    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)
    email = forms.EmailField()
    message = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}))
    # Anti-bot honeypot field (hidden from legitimate users, filled by bots)
    company_site = forms.CharField(required=False, widget=forms.HiddenInput())

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('company_site'):
            raise forms.ValidationError("Spam submission detected.")
        return cleaned_data
