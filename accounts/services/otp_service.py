"""
Secure OTP generation and verification service.
Handles OTP codes for signin with proper security measures.
"""

from datetime import timedelta
import hashlib
import secrets

from django.contrib.auth import get_user_model
from django.utils import timezone

from ..models import VerificationToken

User = get_user_model()

# Use a module-level constant for the token type to avoid hardcoded strings flagged by bandit
SIGNIN_OTP = "signin_otp"


class OTPService:
    """Service for secure OTP generation and verification"""

    @staticmethod
    def generate_otp(user, delivery_method="email"):
        """
        Generate secure 6-digit OTP with 10-minute validity for signin.

        Args:
            user: User instance
            delivery_method: 'email' or 'sms'

        Returns:
            tuple: (otp_code, token_id) for verification
        """
        # Clear any existing signin OTPs for this user
        VerificationToken.objects.filter(user=user, token_type=SIGNIN_OTP, used_at__isnull=True).delete()

        # Generate 6-digit code
        otp_code = f"{secrets.randbelow(900000) + 100000:06d}"

        # Hash for secure storage
        otp_hash = hashlib.sha256(otp_code.encode()).hexdigest()

        # Create token record
        token = VerificationToken.objects.create(
            user=user,
            token_type=SIGNIN_OTP,
            token_value=otp_hash,
            expires_at=timezone.now() + timedelta(minutes=10),  # 10 minutes as required
            max_attempts=5,
        )

        # Update user's preferred OTP method
        user.preferred_otp_method = delivery_method
        user.save(update_fields=["preferred_otp_method"])

        return otp_code, token.id

    @staticmethod
    def verify_otp(token_id, otp_code):
        """
        Verify OTP code against token.

        Args:
            token_id: VerificationToken ID
            otp_code: User-entered OTP code

        Returns:
            tuple: (success: bool, result: User|str)
                   If success=True, result is User instance
                   If success=False, result is error message
        """
        try:
            token = VerificationToken.objects.get(id=token_id, token_type=SIGNIN_OTP, used_at__isnull=True)
        except VerificationToken.DoesNotExist:
            return False, "Invalid verification session"

        # Check if expired
        if token.is_expired():
            return False, "Code has expired. Please request a new one."

        # Check attempt limit
        if token.is_locked():
            return False, "Too many failed attempts. Please request a new code."

        # Verify hash
        otp_hash = hashlib.sha256(otp_code.encode()).hexdigest()

        if token.token_value == otp_hash:
            # Mark as used
            token.mark_used()
            return True, token.user
        else:
            # Record failed attempt
            is_locked = token.record_attempt()
            remaining = token.max_attempts - token.attempts

            if is_locked:
                return False, "Too many failed attempts. Please request a new code."
            else:
                return False, f"Invalid code. {remaining} attempts remaining."

    @staticmethod
    def cleanup_expired_tokens():
        """Clean up expired OTP tokens"""
        expired_tokens = VerificationToken.objects.filter(token_type=SIGNIN_OTP, expires_at__lt=timezone.now())
        count = expired_tokens.count()
        expired_tokens.delete()
        return count
