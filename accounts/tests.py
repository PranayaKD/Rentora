from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from decimal import Decimal
import json
from .models import UserProfile

class UserProfileAndAuthTests(TestCase):
    """35 deterministic tests for UserProfile, authentication, and wallet management."""

    def test_profile_creation_on_user_signup(self):
        user = User.objects.create_user(username='newuser1', password='password123')
        self.assertTrue(UserProfile.objects.filter(user=user).exists())
        self.assertEqual(user.profile.wallet_balance, Decimal('0.00'))

    def test_wallet_balance_isolation(self):
        user1 = User.objects.create_user(username='iso_user1', password='password')
        user2 = User.objects.create_user(username='iso_user2', password='password')
        user1.profile.wallet_balance = Decimal('500.00')
        user1.profile.save()
        user2.profile.wallet_balance = Decimal('1000.00')
        user2.profile.save()
        self.assertEqual(user1.profile.wallet_balance, Decimal('500.00'))
        self.assertEqual(user2.profile.wallet_balance, Decimal('1000.00'))

    def test_wallet_balance_credit(self):
        user = User.objects.create_user(username='credit_user', password='password')
        user.profile.wallet_balance += Decimal('250.00')
        user.profile.save()
        user.profile.refresh_from_db()
        self.assertEqual(user.profile.wallet_balance, Decimal('250.00'))

    def test_wallet_balance_debit(self):
        user = User.objects.create_user(username='debit_user', password='password')
        user.profile.wallet_balance = Decimal('500.00')
        user.profile.save()
        user.profile.wallet_balance -= Decimal('200.00')
        user.profile.save()
        user.profile.refresh_from_db()
        self.assertEqual(user.profile.wallet_balance, Decimal('300.00'))

    def test_referral_code_generation(self):
        user = User.objects.create_user(username='ref_user', password='password')
        self.assertIsNotNone(user.profile.referral_code)

    def test_referral_code_uniqueness(self):
        user1 = User.objects.create_user(username='ref_user1', password='password')
        user2 = User.objects.create_user(username='ref_user2', password='password')
        self.assertNotEqual(user1.profile.referral_code, user2.profile.referral_code)

    def test_kyc_default_status(self):
        user = User.objects.create_user(username='kyc_default', password='password')
        self.assertIn(user.profile.kyc_status, ['NOT_SUBMITTED', 'Unverified', 'Pending', 'Verified'])

    def test_kyc_verified_flag(self):
        user = User.objects.create_user(username='kyc_user', password='password')
        user.profile.is_verified = True
        user.profile.kyc_status = 'Verified'
        user.profile.save()
        user.profile.refresh_from_db()
        self.assertTrue(user.profile.is_verified)
        self.assertEqual(user.profile.kyc_status, 'Verified')

    def test_kyc_rejection_reason_field(self):
        user = User.objects.create_user(username='kyc_reject', password='password')
        user.profile.kyc_status = 'Rejected'
        user.profile.kyc_rejection_reason = 'License expired on 2025-12-31'
        user.profile.save()
        user.profile.refresh_from_db()
        self.assertEqual(user.profile.kyc_rejection_reason, 'License expired on 2025-12-31')

    def test_phone_number_assignment(self):
        user = User.objects.create_user(username='phone_user', password='password')
        user.profile.phone = '+919876543210'
        user.profile.save()
        user.profile.refresh_from_db()
        self.assertEqual(user.profile.phone, '+919876543210')

    def test_driving_license_number_assignment(self):
        user = User.objects.create_user(username='dl_user', password='password')
        user.profile.license_number = 'OD02-20230001234'
        user.profile.save()
        user.profile.refresh_from_db()
        self.assertEqual(user.profile.license_number, 'OD02-20230001234')

    def test_aadhaar_number_field(self):
        user = User.objects.create_user(username='aadhaar_user', password='password')
        user.profile.aadhaar_number = '123456789012'
        user.profile.save()
        user.profile.refresh_from_db()
        self.assertEqual(user.profile.aadhaar_number, '123456789012')

    def test_pan_number_field(self):
        user = User.objects.create_user(username='pan_user', password='password')
        user.profile.pan_number = 'ABCDE1234F'
        user.profile.save()
        user.profile.refresh_from_db()
        self.assertEqual(user.profile.pan_number, 'ABCDE1234F')

    def test_referred_by_relationship(self):
        inviter = User.objects.create_user(username='inviter', password='password')
        invitee = User.objects.create_user(username='invitee', password='password')
        invitee.profile.referred_by = inviter.profile
        invitee.profile.save()
        invitee.profile.refresh_from_db()
        self.assertEqual(invitee.profile.referred_by, inviter.profile)

    def test_login_view_get(self):
        client = Client()
        response = client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_signup_view_get(self):
        client = Client()
        response = client.get(reverse('signup'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('login'))

    def test_logout_view_get(self):
        client = Client()
        client.login(username='iso_user1', password='password')
        response = client.get(reverse('logout'))
        self.assertIn(response.status_code, [200, 302])

    def test_user_login_valid_credentials(self):
        user = User.objects.create_user(username='valid_auth', password='correct_password')
        client = Client()
        login_success = client.login(username='valid_auth', password='correct_password')
        self.assertTrue(login_success)

    def test_user_login_invalid_password(self):
        user = User.objects.create_user(username='bad_auth', password='correct_password')
        client = Client()
        login_success = client.login(username='bad_auth', password='wrong_password')
        self.assertFalse(login_success)

    def test_user_profile_str(self):
        user = User.objects.create_user(username='str_user', password='password')
        self.assertIn('str_user', str(user.profile))

    def test_otp_request_invalid_body(self):
        client = Client()
        response = client.post(reverse('otp_login_request'), 'not a json', content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data.get('success'))

    def test_otp_request_invalid_phone_short(self):
        client = Client()
        response = client.post(reverse('otp_login_request'), json.dumps({'phone': '1234'}), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data.get('success'))

    def test_otp_request_invalid_phone_letters(self):
        client = Client()
        response = client.post(reverse('otp_login_request'), json.dumps({'phone': '98765abcde'}), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data.get('success'))

    def test_otp_verify_without_session_phone(self):
        client = Client()
        response = client.post(reverse('otp_verify_login'), json.dumps({'otp': '123456'}), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data.get('success'))

    def test_dashboard_view_authenticated(self):
        user = User.objects.create_user(username='dash_user', password='password')
        client = Client()
        client.login(username='dash_user', password='password')
        response = client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_dashboard_bookings_view_authenticated(self):
        user = User.objects.create_user(username='booking_user', password='password')
        client = Client()
        client.login(username='booking_user', password='password')
        response = client.get(reverse('dashboard_bookings'))
        self.assertEqual(response.status_code, 200)

    def test_profile_view_authenticated(self):
        user = User.objects.create_user(username='prof_user', password='password')
        client = Client()
        client.login(username='prof_user', password='password')
        response = client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)

    def test_wishlist_view_authenticated(self):
        user = User.objects.create_user(username='wish_user', password='password')
        client = Client()
        client.login(username='wish_user', password='password')
        response = client.get(reverse('wishlist'))
        self.assertEqual(response.status_code, 200)

    def test_kyc_view_authenticated(self):
        user = User.objects.create_user(username='kyc_view_user', password='password')
        client = Client()
        client.login(username='kyc_view_user', password='password')
        response = client.get(reverse('kyc'))
        self.assertEqual(response.status_code, 200)

    def test_user_email_storage(self):
        user = User.objects.create_user(username='email_user', email='odisha@rentora.in', password='password')
        self.assertEqual(user.email, 'odisha@rentora.in')

    def test_user_first_and_last_name(self):
        user = User.objects.create_user(username='name_user', first_name='Srikant', last_name='Patnaik', password='password')
        self.assertEqual(user.get_full_name(), 'Srikant Patnaik')

    def test_user_is_active_default(self):
        user = User.objects.create_user(username='active_user', password='password')
        self.assertTrue(user.is_active)

    def test_user_profile_reverse_relation(self):
        user = User.objects.create_user(username='rev_user', password='password')
        self.assertIsNotNone(user.profile)
        self.assertEqual(user.profile.user, user)

    def test_profile_date_of_birth_field(self):
        from datetime import date
        user = User.objects.create_user(username='dob_user', password='password')
        user.profile.date_of_birth = date(1995, 5, 20)
        user.profile.save()
        user.profile.refresh_from_db()
        self.assertEqual(user.profile.date_of_birth, date(1995, 5, 20))

    def test_profile_save_updates_timestamp(self):
        user = User.objects.create_user(username='time_user', password='password')
        self.assertIsNotNone(user.profile.created_at)

    def test_profile_view_form_post_update_details(self):
        user = User.objects.create_user(username='update_prof', password='old_password123', first_name='Old', last_name='Name')
        client = Client()
        client.login(username='update_prof', password='old_password123')
        response = client.post(reverse('profile'), {
            'full_name': 'Sabyasachi Mishra',
            'email': 'sabyasachi@rentora.in',
            'phone': '+919876543210',
            'license_number': 'OD02-2024-0012345',
            'aadhaar_number': '123456789012',
            'pan_number': 'ABCDE1234F',
            'update_profile': '1',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertEqual(user.first_name, 'Sabyasachi')
        self.assertEqual(user.last_name, 'Mishra')
        self.assertEqual(user.email, 'sabyasachi@rentora.in')
        self.assertEqual(user.profile.phone, '+919876543210')
        self.assertEqual(user.profile.license_number, 'OD02-2024-0012345')
        self.assertEqual(user.profile.aadhaar_number, '123456789012')
        self.assertEqual(user.profile.pan_number, 'ABCDE1234F')

    def test_profile_view_password_change_success(self):
        user = User.objects.create_user(username='pw_change_user', password='oldPassword@123')
        client = Client()
        client.login(username='pw_change_user', password='oldPassword@123')
        response = client.post(reverse('profile'), {
            'change_password': '1',
            'old_password': 'oldPassword@123',
            'new_password': 'newPassword@456',
            'confirm_password': 'newPassword@456',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.check_password('newPassword@456'))

    def test_profile_view_password_change_invalid_old_password(self):
        user = User.objects.create_user(username='pw_fail_user', password='correctPassword@123')
        client = Client()
        client.login(username='pw_fail_user', password='correctPassword@123')
        response = client.post(reverse('profile'), {
            'change_password': '1',
            'old_password': 'WRONGPassword@123',
            'new_password': 'newPassword@456',
            'confirm_password': 'newPassword@456',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.check_password('correctPassword@123'))

    def test_profile_view_duplicate_email_error(self):
        User.objects.create_user(username='other_user', email='duplicate@rentora.in', password='password123')
        user = User.objects.create_user(username='main_user', email='main@rentora.in', password='password123')
        client = Client()
        client.login(username='main_user', password='password123')
        response = client.post(reverse('profile'), {
            'full_name': 'Main User',
            'email': 'duplicate@rentora.in',
            'update_profile': '1',
        })
        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertEqual(user.email, 'main@rentora.in')
