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


def send_magic_link_email(email, magic_link, user_name=None, is_verification=False):
    """Send magic link authentication or verification email"""
    greeting = f"Hello {user_name}" if user_name else "Hello"

    if is_verification:
        subject = "Aprende Comigo - Verify Your Email"
        message = f"""{greeting},

Welcome to Aprende Comigo! Please verify your email address by clicking the link below:

{magic_link}

You can continue using Aprende Comigo for 24 hours without verification, but you'll need to verify your email to access your account after that.

This verification link will expire in 24 hours.

If you didn't create an account, please ignore this email.

Best regards,
The Aprende Comigo Team"""
    else:
        subject = "Aprende Comigo - Login Link"
        message = f"""{greeting},

Click the link below to sign in to your Aprende Comigo account:

{magic_link}

This link will expire in 15 minutes for security reasons.

If you didn't request this login link, please ignore this email.

Best regards,
The Aprende Comigo Team"""

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )

        logger.info(f"{'Verification' if is_verification else 'Magic link'} email sent successfully to {email}")
        return {
            "success": True,
            "email": email,
            "sent_at": datetime.now().isoformat(),
            "is_verification": is_verification
        }
    except Exception as e:
        logger.error(f"{'Verification' if is_verification else 'Magic link'} email sending failed: {e!s}")
        return {
            "success": False,
            "error": f"Email sending failed: {e!s}",
            "email": email
        }


def send_sms_otp(phone_number: str, otp_code: str, user_name: str | None = None, is_verification: bool = False) -> dict[str, Any]:
    """
    Send SMS OTP using external SMS service

    Args:
        phone_number: The phone number to send SMS to
        otp_code: The OTP code to send
        user_name: Optional user name for personalization
        is_verification: If True, send as account verification SMS

    Returns:
        dict with success status and details
    """
    greeting = f"Hello {user_name}" if user_name else "Hello"

    if is_verification:
        message = f"""{greeting},

Welcome to Aprende Comigo! Your phone verification code is: {otp_code}

You have 24 hours to verify your phone number. Enter this code in the app to complete verification.

This code will expire in 30 minutes."""
    else:
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

        # Log OTP code in development mode for debugging
        if settings.DEBUG:
            if result.get('debug'):
                logger.info(f"[SMS DEBUG] OTP Code for {phone_number}: {otp_code}")
                result["debug_otp_code"] = otp_code

        if result['success']:
            logger.info(f"SMS OTP sent successfully to {phone_number}: {result.get('message_id', 'N/A')}")
        else:
            logger.error(f"SMS OTP failed for {phone_number}: {result.get('error', 'Unknown error')}")

        return result

    except Exception as e:
        logger.error(f"SMS OTP error for {phone_number}: {e!s}")
        return {
            "success": False,
            "error": f"SMS service error: {e!s}",
            "phone_number": phone_number,
            "sent_at": datetime.now().isoformat()
        }


