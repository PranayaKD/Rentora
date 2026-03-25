from django.test import TestCase
from django.contrib.auth.models import User
from .models import UserProfile

class UserProfileTest(TestCase):
    def test_profile_creation_on_user_signup(self):
        """Test that a UserProfile is automatically created when a User is created."""
        user = User.objects.create_user(username='newuser', password='password123')
        
        # Profile should exist due to signals
        self.assertTrue(UserProfile.objects.filter(user=user).exists())
        
        profile = user.profile
        self.assertEqual(profile.wallet_balance, 0) # Default balance
        
    def test_wallet_balance_isolation(self):
        """Ensure different users have isolated wallet balances."""
        user1 = User.objects.create_user(username='user1', password='password')
        user2 = User.objects.create_user(username='user2', password='password')
        
        user1.profile.wallet_balance = 500
        user1.profile.save()
        
        user2.profile.wallet_balance = 1000
        user2.profile.save()
        
        self.assertEqual(user1.profile.wallet_balance, 500)
        self.assertEqual(user2.profile.wallet_balance, 1000)
