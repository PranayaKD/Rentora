from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth.models import User

class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        # Auto-link to existing local user account with the same email
        if sociallogin.is_existing:
            return

        if not sociallogin.user.email:
            return

        try:
            user = User.objects.get(email=sociallogin.user.email)
            sociallogin.connect(request, user)
        except User.DoesNotExist:
            pass
