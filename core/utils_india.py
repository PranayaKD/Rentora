import requests
from django.conf import settings
from .constants import GST_PERCENTAGE

def send_otp_msg91(phone_number, otp):
    """
    Send OTP via MSG91 API.
    Required settings: MSG91_AUTH_KEY, MSG91_TEMPLATE_ID
    """
    auth_key = getattr(settings, 'MSG91_AUTH_KEY', None)
    template_id = getattr(settings, 'MSG91_TEMPLATE_ID', None)
    
    if not auth_key or not template_id:
        print(f"[MOCK] Sending MSG91 OTP {otp} to {phone_number}")
        return True
        
    url = "https://api.msg91.com/api/v5/otp"
    payload = {
        "template_id": template_id,
        "mobile": phone_number,
        "authkey": auth_key,
        "otp": otp
    }
    try:
        response = requests.get(url, params=payload)
        return response.json().get('type') == 'success'
    except Exception as e:
        print(f"MSG91 Error: {e}")
        return False

def send_whatsapp_confirmation(booking):
    """
    Send booking confirmation via Twilio WhatsApp API to BOTH User and Admin.
    Required settings: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER
    """
    account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
    auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
    from_number = getattr(settings, 'TWILIO_WHATSAPP_NUMBER', 'whatsapp:+14155238886') # Sandbox number
    admin_phone = getattr(settings, 'ADMIN_PHONE', None)
    
    # --- User Message ---
    user_phone = getattr(booking.user, 'profile', None)
    user_phone = f"whatsapp:{user_phone.phone}" if user_phone and user_phone.phone else None
    
    user_message = (
        f"🚗 *Rentora Booking Confirmed!*\n\n"
        f"Hi {booking.user.first_name or booking.user.username},\n"
        f"Your booking for *{booking.car.brand} {booking.car.name}* is confirmed.\n"
        f"📅 Date: {booking.pickup_date} to {booking.dropoff_date}\n"
        f"📍 Pickup: {booking.pickup_location}\n"
        f"🆔 Ref: {booking.booking_reference}\n"
        f"💰 Total: ₹{booking.total_with_gst}\n\n"
        f"Happy Driving! 🏁"
    )
    
    # --- Admin Message ---
    admin_message = (
        f"🔔 *New Booking Alert — Rentora*\n\n"
        f"🆔 Ref: {booking.booking_reference}\n"
        f"👤 Customer: {booking.user.get_full_name() or booking.user.username}\n"
        f"📧 Email: {booking.user.email}\n"
        f"🚗 Vehicle: {booking.car.brand} {booking.car.name}\n"
        f"📅 {booking.pickup_date} → {booking.dropoff_date}\n"
        f"📍 Pickup: {booking.pickup_location}\n"
        f"💰 Total: ₹{booking.total_with_gst}\n"
        f"✅ Status: PAID"
    )

    if not account_sid or not auth_token:
        if user_phone:
            print(f"[MOCK] Sending WhatsApp to {user_phone}:\n{user_message}")
        if admin_phone:
            print(f"[MOCK] Sending WhatsApp to Admin whatsapp:{admin_phone}:\n{admin_message}")
        return True

    from twilio.rest import Client
    client = Client(account_sid, auth_token)
    
    # Send to User
    if user_phone:
        try:
            client.messages.create(body=user_message, from_=from_number, to=user_phone)
        except Exception as e:
            print(f"Twilio WhatsApp Error (User): {e}")
    
    # Send to Admin
    if admin_phone:
        try:
            client.messages.create(body=admin_message, from_=from_number, to=f"whatsapp:{admin_phone}")
        except Exception as e:
            print(f"Twilio WhatsApp Error (Admin): {e}")
    
    return True

def calculate_india_gst(amount):
    """Calculate GST amount for Indian transactions."""
    gst_amt = amount * (GST_PERCENTAGE / 100)
    return round(gst_amt, 2)
