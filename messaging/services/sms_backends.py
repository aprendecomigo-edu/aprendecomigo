"""
SMS backend implementations following Django's email backend pattern.

This module provides different SMS backends that can be configured via SMS_BACKEND setting:
- ConsoleSMSBackend: Logs SMS messages to console (development)
- SNSSMSBackend: Sends SMS via Amazon SNS (staging/production)
"""

from abc import ABC, abstractmethod
import asyncio
import logging

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

# AWS imports for SNS (optional)
try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    boto3 = None
    ClientError = Exception  # Fallback for type hints

logger = logging.getLogger(__name__)


class BaseSMSBackend(ABC):
    """
    Base class for SMS backends.
    """

    @abstractmethod
    def send(self, to: str, message: str, from_number: str | None = None) -> dict:
        """Send a single SMS message."""
        pass

    @abstractmethod
    async def send_async(self, to: str, message: str, from_number: str | None = None) -> dict:
        """Send a single SMS message asynchronously."""
        pass

    def send_bulk(self, recipients: list[str], message: str, from_number: str | None = None) -> list[dict]:
        """Send SMS to multiple recipients."""
        return [self.send(recipient, message, from_number) for recipient in recipients]

    async def send_bulk_async(self, recipients: list[str], message: str, from_number: str | None = None) -> list[dict]:
        """Send SMS to multiple recipients asynchronously."""
        tasks = [self.send_async(recipient, message, from_number) for recipient in recipients]
        return await asyncio.gather(*tasks)


class ConsoleSMSBackend(BaseSMSBackend):
    """
    SMS backend that logs messages to console instead of sending them.
    Perfect for development environments.
    """

    def send(self, to: str, message: str, from_number: str | None = None) -> dict:
        """Log SMS to console."""
        logger.info("=" * 60)
        logger.info("SMS MESSAGE (Console Backend)")
        logger.info("=" * 60)
        logger.info(f"To: {to}")
        if from_number:
            logger.info(f"From: {from_number}")
        logger.info(f"Message: {message}")
        logger.info("=" * 60)

        return {
            "success": True,
            "message_id": "console-backend-debug",
            "provider": "console",
            "to": to,
            "debug": True,
        }

    async def send_async(self, to: str, message: str, from_number: str | None = None) -> dict:
        """Log SMS to console asynchronously."""
        return self.send(to, message, from_number)


class SNSSMSBackend(BaseSMSBackend):
    """
    SMS backend that sends messages via Amazon SNS.
    Used for staging and production environments.
    """

    def __init__(self):
        super().__init__()
        if boto3 is None:
            raise ImproperlyConfigured("boto3 is required for SNS SMS backend. Install with: pip install boto3")

        self.region_name = getattr(settings, "AWS_SNS_REGION", getattr(settings, "AWS_DEFAULT_REGION", "us-east-1"))

        # Initialize boto3 client
        try:
            session_params = {}
            aws_access_key_id = getattr(settings, "AWS_ACCESS_KEY_ID", None)
            aws_secret_access_key = getattr(settings, "AWS_SECRET_ACCESS_KEY", None)

            if aws_access_key_id and aws_secret_access_key:
                session_params = {
                    "aws_access_key_id": aws_access_key_id,
                    "aws_secret_access_key": aws_secret_access_key,
                    "region_name": self.region_name,
                }
            else:
                # Use default AWS credentials (IAM roles, env vars, etc.)
                session_params = {"region_name": self.region_name}

            self.sns_client = boto3.client("sns", **session_params)

        except Exception as e:
            raise ImproperlyConfigured(f"Failed to initialize SNS client: {e}")

    def send(self, to: str, message: str, from_number: str | None = None) -> dict:
        """Send SMS via Amazon SNS."""
        return asyncio.run(self.send_async(to, message, from_number))

    async def send_async(self, to: str, message: str, from_number: str | None = None) -> dict:
        """Send SMS via Amazon SNS asynchronously."""
        # Normalize phone number - SNS expects E.164 format
        to_normalized = to if to.startswith("+") else f"+{to.lstrip('+')}"

        try:
            # Run the synchronous SNS call in a thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, lambda: self._send_sms_sync(to_normalized, message, from_number)
            )
            return response

        except Exception as e:
            logger.error(f"SNS SMS error to {to}: {e!s}")
            return {"success": False, "error": str(e), "provider": "sns", "to": to}

    def _send_sms_sync(self, to: str, message: str, from_number: str | None = None) -> dict:
        """Send SMS via SNS synchronously."""
        try:
            publish_params = {
                "PhoneNumber": to,
                "Message": message,
                "MessageAttributes": {
                    "AWS.SNS.SMS.SMSType": {
                        "DataType": "String",
                        "StringValue": "Transactional",  # Use 'Promotional' for marketing messages
                    },
                    "AWS.SNS.SMS.MaxPrice": {
                        "DataType": "Number",
                        "StringValue": "1.00",  # Max price per message in USD
                    },
                },
            }

            # Add sender ID if provided (not supported in all regions/countries)
            if from_number:
                publish_params["MessageAttributes"]["AWS.SNS.SMS.SenderID"] = {
                    "DataType": "String",
                    "StringValue": from_number,
                }

            response = self.sns_client.publish(**publish_params)

            logger.info(f"SMS sent successfully to {to}: {response.get('MessageId')}")

            return {
                "success": True,
                "message_id": response.get("MessageId"),
                "provider": "sns",
                "to": to,
                "response": response,
            }

        except Exception as e:
            # Handle both ClientError (from boto3) and other exceptions
            if hasattr(e, "response") and "Error" in e.response:
                error_code = e.response["Error"]["Code"]
                error_message = e.response["Error"]["Message"]
                error_detail = f"{error_code}: {error_message}"
            else:
                error_detail = str(e)

            logger.error(f"SNS SMS failed to {to}: {error_detail}")
            return {"success": False, "error": error_detail, "provider": "sns", "to": to}


def get_sms_backend() -> BaseSMSBackend:
    """
    Get the configured SMS backend instance.
    Similar to Django's get_connection() for email.
    """
    backend_path = getattr(settings, "SMS_BACKEND", "messaging.services.sms_backends.ConsoleSMSBackend")

    try:
        # Import the backend class
        if "." not in backend_path:
            raise ValueError("Backend path must contain at least one dot")

        module_path, class_name = backend_path.rsplit(".", 1)
        module = __import__(module_path, fromlist=[class_name])
        backend_class = getattr(module, class_name)

        # Return instance of the backend
        return backend_class()

    except (ImportError, AttributeError, ValueError) as e:
        raise ImproperlyConfigured(f"SMS backend '{backend_path}' could not be loaded: {e}")
