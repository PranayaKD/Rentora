from django.conf import settings

def vapid_key_processor(request):
    return {
        'vapid_public_key': getattr(settings, 'VAPID_PUBLIC_KEY', '')
    }
