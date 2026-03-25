from django.utils.deprecation import MiddlewareMixin
from django.db.models import Prefetch
from .models import UserProfile

class ProfilePrefetchMiddleware(MiddlewareMixin):
    """
    Middleware to prefetch UserProfile on every authenticated request.
    This prevents N+1 queries in templates that access request.user.profile.
    """
    def process_request(self, request):
        if request.user.is_authenticated:
            # We use select_related to join User and UserProfile in one query
            # However, request.user is already loaded by AuthenticationMiddleware.
            # To optimize, we can check if it's already cached or force a join.
            # A simpler way in Django is to just hit it once or use a cached property.
            try:
                # Accessing it once here ensures it's cached for the rest of the request
                _ = request.user.profile
            except UserProfile.DoesNotExist:
                pass
        return None
