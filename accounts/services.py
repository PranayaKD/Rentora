import os
import logging
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

logger = logging.getLogger(__name__)

class TwilioService:
    @staticmethod
    def get_client():
        return Client(
            os.getenv('TWILIO_ACCOUNT_SID'),
            os.getenv('TWILIO_AUTH_TOKEN')
        )

    @staticmethod
    def send_otp(phone_number):
        """Send a 6-digit verification code to the phone number."""
        # Development / Sandbox Fallback
        if os.getenv('DEBUG', 'False') == 'True' and (not os.getenv('TWILIO_ACCOUNT_SID') or os.getenv('TWILIO_ACCOUNT_SID').startswith('AC_dummy')):
            logger.info(f"[DEV MODE] Simulating OTP send to {phone_number}. Use 123456.")
            return True

        try:
            client = TwilioService.get_client()
            verify_sid = os.getenv('TWILIO_VERIFY_SERVICE_SID')
            verification = client.verify.v2.services(verify_sid) \
                .verifications \
                .create(to=phone_number, channel='sms')
            return verification.status == 'pending'
        except Exception as e:
            logger.error(f"Twilio Send OTP Error: {str(e)}")
            # In debug mode fallback to success for testing
            if os.getenv('DEBUG', 'False') == 'True':
                logger.info(f"[DEV FALLBACK] Twilio error, allowing test OTP 123456 for {phone_number}")
                return True
            return False

    @staticmethod
    def verify_otp(phone_number, code):
        """Check if the provided code matches the one sent by Twilio."""
        # Development test code
        if os.getenv('DEBUG', 'False') == 'True' and code in ['123456', '000000']:
            return True

        try:
            client = TwilioService.get_client()
            verify_sid = os.getenv('TWILIO_VERIFY_SERVICE_SID')
            verification_check = client.verify.v2.services(verify_sid) \
                .verification_checks \
                .create(to=phone_number, code=code)
            return verification_check.status == 'approved'
        except Exception as e:
            logger.error(f"Twilio Verify OTP Error: {str(e)}")
            if os.getenv('DEBUG', 'False') == 'True' and code in ['123456', '000000']:
                return True
            return False
