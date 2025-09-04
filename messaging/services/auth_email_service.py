"""
Authentication Email Service

This service provides basic email and SMS functionality for authentication flows.
"""

from datetime import datetime
import logging
from typing import Any

from django.conf import settings
from django.core.mail import send_mail

from .sms import send_sms

logger = logging.getLogger(__name__)


def send_email_verification_code(email, code):
    """Send email verification code for authentication"""
    return send_mail(
        subject="Aprende Comigo - Verification Code",
        message=f"Your verification code is: {code}\n\nThis code will expire in 5 minutes.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )


def send_magic_link_email(email, magic_link, user_name=None):
    """Send magic link authentication email"""
    greeting = f"Hello {user_name}" if user_name else "Hello"

    try:
        send_mail(
            subject="Aprende Comigo - Login Link",
            message=f"""{greeting},

Click the link below to sign in to your Aprende Comigo account:

{magic_link}

This link will expire in 15 minutes for security reasons.

If you didn't request this login link, please ignore this email.

Best regards,
The Aprende Comigo Team""",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        
        logger.info(f"Magic link email sent successfully to {email}")
        return {
            "success": True,
            "email": email,
            "sent_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Magic link email sending failed: {e!s}")
        return {
            "success": False,
            "error": f"Email sending failed: {e!s}",
            "email": email
        }


def send_sms_otp(phone_number: str, otp_code: str, user_name: str | None = None) -> dict[str, Any]:
    """
    Send SMS OTP using external SMS service
    
    Args:
        phone_number: The phone number to send SMS to
        otp_code: The OTP code to send
        user_name: Optional user name for personalization
        
    Returns:
        dict with success status and details
    """
    greeting = f"Hello {user_name}" if user_name else "Hello"
    
    message = f"""{greeting},

Your Aprende Comigo verification code is: {otp_code}

This code will expire in 5 minutes.

If you didn't request this code, please ignore this message."""

    try:
        # Use the new SMS service
        result = send_sms(to=phone_number, message=message)
        
        # Add additional metadata for OTP context
        result.update({
            "phone_number": phone_number,
            "sent_at": datetime.now().isoformat(),
            "service": "otp_verification",
        })
        
        # Only include OTP code in development mode for debugging
        if settings.DEBUG and not result.get('success'):
            logger.info(f"[SMS DEBUG] OTP Code for {phone_number}: {otp_code}")
            result["debug_otp_code"] = otp_code
        
        if result['success']:
            logger.info(f"SMS OTP sent successfully to {phone_number}: {result.get('message_id', 'N/A')}")
        else:
            logger.error(f"SMS OTP failed for {phone_number}: {result.get('error', 'Unknown error')}")
            
        return result
        
    except Exception as e:
        logger.error(f"SMS OTP error for {phone_number}: {str(e)}")
        return {
            "success": False,
            "error": f"SMS service error: {str(e)}",
            "phone_number": phone_number,
            "sent_at": datetime.now().isoformat()
        }


