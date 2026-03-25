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
        client = TwilioService.get_client()
        verify_sid = os.getenv('TWILIO_VERIFY_SERVICE_SID')
        
        try:
            verification = client.verify.v2.services(verify_sid) \
                .verifications \
                .create(to=phone_number, channel='sms')
            return verification.status == 'pending'
        except TwilioRestException as e:
            logger.error(f"Twilio Send OTP Error: {str(e)}")
            return False

    @staticmethod
    def verify_otp(phone_number, code):
        """Check if the provided code matches the one sent by Twilio."""
        client = TwilioService.get_client()
        verify_sid = os.getenv('TWILIO_VERIFY_SERVICE_SID')
        
        try:
            verification_check = client.verify.v2.services(verify_sid) \
                .verification_checks \
                .create(to=phone_number, code=code)
            return verification_check.status == 'approved'
        except TwilioRestException as e:
            logger.error(f"Twilio Verify OTP Error: {str(e)}")
            return False
