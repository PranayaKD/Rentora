from django import forms
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
        from django.utils import timezone
        cleaned_data = super().clean()
        pickup = cleaned_data.get('pickup_date')
        dropoff = cleaned_data.get('dropoff_date')
        
        if pickup:
            if pickup < timezone.now():
                raise forms.ValidationError("Pickup date cannot be in the past.")
                
        if pickup and dropoff and dropoff <= pickup:
            raise forms.ValidationError("Drop-off date must be after pickup date.")
            
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
