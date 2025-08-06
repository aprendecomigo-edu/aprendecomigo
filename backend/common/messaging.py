import json
import logging

import requests
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def send_email_verification_code(email, code):
    return send_mail(
        subject="Aprende Comigo - Verification Code",
        message=f"Your verification code is: {code}\n\nThis code will expire in 5 minutes.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )


def send_sms(phone_number, message):
    """
    Send SMS using GatewayAPI.

    In DEBUG mode, just logs the message instead of actually sending it.

    Args:
        phone_number: Recipient's phone number (should include country code)
        message: SMS content to send

    Returns:
        dict: Response from API or simulated response in DEBUG mode
    """
    if settings.DEBUG:
        logger.info(f"SMS to {phone_number}: {message}")
        return {"success": True, "debug_mode": True}

    try:
        # Remove any potential formatting characters from phone number
        cleaned_number = "".join(filter(str.isdigit, str(phone_number)))

        # Prepare request data
        payload = {
            "message": message,
            "recipients": [{"msisdn": cleaned_number}],
            "sender": settings.SMS_SENDER_ID,
        }

        # Make API request
        response = requests.post(
            url=settings.SMS_API_URL,
            headers={"Content-Type": "application/json"},
            auth=(settings.SMS_API_KEY, ""),
            data=json.dumps(payload),
        )

        response_data = response.json()

        if response.status_code != 200:
            logger.error(f"SMS sending failed: {response_data}")
            return {"success": False, "error": response_data}

        logger.info(f"SMS sent successfully to {phone_number}")
        return {"success": True, "response": response_data}

    except Exception as e:
        logger.exception(f"Error sending SMS: {e!s}")
        return {"success": False, "error": str(e)}


def send_phone_verification_code(phone_number, code):
    return send_sms(
        phone_number, f"Your verification code is: {code}\n\nThis code will expire in 5 minutes."
    )


