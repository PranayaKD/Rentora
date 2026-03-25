import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from django.contrib.auth.decorators import login_required
# from .models import PushSubscription <-- Moved inside
from pywebpush import webpush, WebPushException

@login_required
@csrf_exempt
@require_POST
def save_push_subscription(request):
    """Save or update a user's push subscription."""
    from .models import PushSubscription
    try:
        data = json.loads(request.body)
        subscription_info = data
        
        # Check if subscription already exists for this user and info
        # We use JSONField so we can filter or just update/create
        subscription, created = PushSubscription.objects.update_or_create(
            user=request.user,
            subscription_info=subscription_info,
            defaults={'subscription_info': subscription_info}
        )
        
        return JsonResponse({"status": "success", "created": created})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)

def send_push_notification(user, title, body, url='/dashboard/'):
    """Utility function to send a push notification to all subscriptions of a user."""
    from .models import PushSubscription
    subscriptions = PushSubscription.objects.filter(user=user)
    
    payload = {
        "title": title,
        "body": body,
        "url": url
    }
    
    results = []
    for sub in subscriptions:
        try:
            webpush(
                subscription_info=sub.subscription_info,
                data=json.dumps(payload),
                vapid_private_key=settings.VAPID_PRIVATE_KEY,
                vapid_claims={"sub": f"mailto:{settings.VAPID_ADMIN_EMAIL}"}
            )
            results.append(True)
        except WebPushException as ex:
            # If the subscription is expired or invalid, we should remove it
            if ex.response and ex.response.status_code in [404, 410]:
                sub.delete()
            results.append(False)
            print(f"WebPush Error: {ex}")
            
    return results
