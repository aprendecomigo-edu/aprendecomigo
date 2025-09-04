"""
SMS service implementation using Amazon SNS.
Simple, clean interface for sending SMS messages via AWS SNS.
"""

import asyncio
import logging

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

# AWS imports for SNS
try:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    boto3 = None

logger = logging.getLogger(__name__)


class SNSSMSProvider:
    """Amazon SNS SMS provider implementation."""

    def __init__(self, region_name: str | None = None, aws_access_key_id: str | None = None, aws_secret_access_key: str | None = None):
        if boto3 is None:
            raise ImproperlyConfigured("boto3 is required for SNS SMS service. Install with: pip install boto3")

        self.region_name = region_name or "us-east-1"

        # Initialize boto3 client
        try:
            session_params = {}
            if aws_access_key_id and aws_secret_access_key:
                session_params = {
                    'aws_access_key_id': aws_access_key_id,
                    'aws_secret_access_key': aws_secret_access_key,
                    'region_name': self.region_name
                }
            else:
                # Use default AWS credentials (IAM roles, env vars, etc.)
                session_params = {'region_name': self.region_name}

            self.sns_client = boto3.client('sns', **session_params)

        except Exception as e:
            raise ImproperlyConfigured(f"Failed to initialize SNS client: {e}")

    async def send_sms_async(self, to: str, message: str, from_number: str | None = None) -> dict:
        """Send SMS via Amazon SNS asynchronously."""
        # Normalize phone number - SNS expects E.164 format
        to_normalized = to if to.startswith('+') else f'+{to.lstrip("+")}'

        try:
            # Run the synchronous SNS call in a thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self._send_sms_sync(to_normalized, message, from_number)
            )
            return response

        except Exception as e:
            logger.error(f"SNS SMS error to {to}: {e!s}")
            return {
                'success': False,
                'error': str(e),
                'provider': 'sns',
                'to': to
            }

    def send_sms(self, to: str, message: str, from_number: str | None = None) -> dict:
        """Send SMS synchronously."""
        return asyncio.run(self.send_sms_async(to, message, from_number))

    def _send_sms_sync(self, to: str, message: str, from_number: str | None = None) -> dict:
        """Send SMS via SNS synchronously."""
        try:
            publish_params = {
                'PhoneNumber': to,
                'Message': message,
                'MessageAttributes': {
                    'AWS.SNS.SMS.SMSType': {
                        'DataType': 'String',
                        'StringValue': 'Transactional'  # Use 'Promotional' for marketing messages
                    },
                    'AWS.SNS.SMS.MaxPrice': {
                        'DataType': 'Number',
                        'StringValue': '1.00'  # Max price per message in USD
                    }
                }
            }

            # Add sender ID if provided (not supported in all regions/countries)
            if from_number:
                publish_params['MessageAttributes']['AWS.SNS.SMS.SenderID'] = {
                    'DataType': 'String',
                    'StringValue': from_number
                }

            response = self.sns_client.publish(**publish_params)

            logger.info(f"SMS sent successfully to {to}: {response.get('MessageId')}")

            return {
                'success': True,
                'message_id': response.get('MessageId'),
                'provider': 'sns',
                'to': to,
                'response': response
            }

        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            error_detail = f"{error_code}: {error_message}"

            logger.error(f"SNS SMS failed to {to}: {error_detail}")
            return {
                'success': False,
                'error': error_detail,
                'provider': 'sns',
                'to': to
            }

        except Exception as e:
            logger.error(f"SNS SMS error to {to}: {e!s}")
            return {
                'success': False,
                'error': str(e),
                'provider': 'sns',
                'to': to
            }


class SMSService:
    """SMS service using Amazon SNS."""

    def __init__(self):
        self.provider = self._get_provider()

    def _get_provider(self) -> SNSSMSProvider:
        """Initialize the SNS SMS provider."""
        return SNSSMSProvider(
            region_name=getattr(settings, 'AWS_SNS_REGION', getattr(settings, 'AWS_DEFAULT_REGION', None)),
            aws_access_key_id=getattr(settings, 'AWS_ACCESS_KEY_ID', None),
            aws_secret_access_key=getattr(settings, 'AWS_SECRET_ACCESS_KEY', None)
        )

    async def send_async(self, to: str, message: str, from_number: str | None = None) -> dict:
        """Send SMS asynchronously."""
        return await self.provider.send_sms_async(to, message, from_number)

    def send(self, to: str, message: str, from_number: str | None = None) -> dict:
        """Send SMS synchronously."""
        return self.provider.send_sms(to, message, from_number)

    async def send_bulk_async(self, recipients: list[str], message: str, from_number: str | None = None) -> list[dict]:
        """Send SMS to multiple recipients asynchronously."""
        tasks = [
            self.send_async(recipient, message, from_number)
            for recipient in recipients
        ]
        return await asyncio.gather(*tasks)

    def send_bulk(self, recipients: list[str], message: str, from_number: str | None = None) -> list[dict]:
        """Send SMS to multiple recipients synchronously."""
        return asyncio.run(self.send_bulk_async(recipients, message, from_number))


# Global SMS service instance (lazy initialization)
_sms_service = None


def get_sms_service() -> SMSService:
    """Get or create the SMS service instance."""
    global _sms_service
    if _sms_service is None:
        _sms_service = SMSService()
    return _sms_service


# Convenience functions for easy usage
def send_sms(to: str, message: str, from_number: str | None = None) -> dict:
    """Send a single SMS message."""
    return get_sms_service().send(to, message, from_number)


async def send_sms_async(to: str, message: str, from_number: str | None = None) -> dict:
    """Send a single SMS message asynchronously."""
    return await get_sms_service().send_async(to, message, from_number)


def send_bulk_sms(recipients: list[str], message: str, from_number: str | None = None) -> list[dict]:
    """Send SMS to multiple recipients."""
    return get_sms_service().send_bulk(recipients, message, from_number)


async def send_bulk_sms_async(recipients: list[str], message: str, from_number: str | None = None) -> list[dict]:
    """Send SMS to multiple recipients asynchronously."""
    return await get_sms_service().send_bulk_async(recipients, message, from_number)


# For backwards compatibility - create a callable that returns the service
def sms_service():
    """Get the SMS service instance (backwards compatibility)."""
    return get_sms_service()
