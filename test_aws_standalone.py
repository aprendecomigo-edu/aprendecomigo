#!/usr/bin/env python3
"""
Standalone AWS messaging services test script.
Tests both SES email and SNS SMS functionality without Django.

Usage:
    python test_aws_standalone.py --email recipient@example.com --sms +1234567890

Before running:
1. Set AWS credentials via environment variables or AWS CLI
2. Verify SES sender email is verified in AWS console
3. Ensure phone number format is correct for SNS (+1234567890)
"""

import argparse
import asyncio
import os
import sys

# Check for boto3 availability
try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
except ImportError:
    print("❌ boto3 is not installed. Install with: pip install boto3")
    sys.exit(1)


class AWSMessagingTester:
    """Standalone AWS messaging tester."""

    def __init__(self):
        self.region = os.getenv('AWS_DEFAULT_REGION', 'eu-west-3') # Paris region
        self.access_key = os.getenv('AWS_ACCESS_KEY_ID')
        self.secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.profile = os.getenv('AWS_PROFILE')

    def check_credentials(self) -> bool:
        """Check if AWS credentials are available."""
        print("Checking AWS credentials...")

        if self.profile:
            print(f"✅ Using AWS Profile: {self.profile}")
            return True
        elif self.access_key and self.secret_key:
            print(f"✅ Using AWS Access Keys (Region: {self.region})")
            return True
        else:
            print("❌ No AWS credentials found!")
            print("   Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables")
            print("   Or configure AWS CLI with: aws configure")
            print("   Or set AWS_PROFILE environment variable")
            return False

    def get_boto3_session(self):
        """Get boto3 session with available credentials."""
        if self.profile:
            return boto3.Session(profile_name=self.profile, region_name=self.region)
        elif self.access_key and self.secret_key:
            return boto3.Session(
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region
            )
        else:
            # Try default credentials
            return boto3.Session(region_name=self.region)

    def test_ses_email(self, recipient_email: str, sender_email: str | None = None) -> bool:
        """Test SES email functionality."""
        print(f"\nTesting Amazon SES Email (Region: {self.region})...")

        if not sender_email:
            sender_email = input("Enter verified sender email address: ").strip()

        try:
            session = self.get_boto3_session()
            ses_client = session.client('ses')

            # Test message
            subject = "AWS SES Standalone Test"
            body_text = """AWS SES Standalone Test

This is a test email sent via Amazon SES to verify the configuration.
If you received this email, SES integration is working correctly!

Sent from AWS SES standalone test script."""

            body_html = f"""<html>
<head></head>
<body>
    <h2>AWS SES Standalone Test</h2>
    <p>This is a test email sent via <strong>Amazon SES</strong> to verify the configuration.</p>
    <p>If you received this email, SES integration is working correctly!</p>
    <hr>
    <small>Sent from AWS SES standalone test script<br>
    Region: {self.region}</small>
</body>
</html>"""

            # Send email
            response = ses_client.send_email(
                Destination={
                    'ToAddresses': [recipient_email],
                },
                Message={
                    'Body': {
                        'Html': {
                            'Charset': 'UTF-8',
                            'Data': body_html,
                        },
                        'Text': {
                            'Charset': 'UTF-8',
                            'Data': body_text,
                        },
                    },
                    'Subject': {
                        'Charset': 'UTF-8',
                        'Data': subject,
                    },
                },
                Source=sender_email,
            )

            message_id = response.get('MessageId')
            print("✅ Email sent successfully!")
            print(f"   To: {recipient_email}")
            print(f"   From: {sender_email}")
            print(f"   Message ID: {message_id}")
            return True

        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            print(f"❌ SES Error: {error_code}")
            print(f"   Message: {error_message}")

            if error_code == 'MessageRejected':
                print("   💡 Make sure the sender email is verified in SES console")
            elif error_code == 'SendingPausedException':
                print("   💡 Your SES account is in sandbox mode or sending is paused")

            return False

        except NoCredentialsError:
            print("❌ AWS credentials not found or invalid")
            return False

        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False

    async def test_sns_sms(self, phone_number: str) -> bool:
        """Test SNS SMS functionality."""
        sns_region = os.getenv('AWS_SNS_REGION', self.region)
        print(f"\nTesting Amazon SNS SMS (Region: {sns_region})...")

        try:
            session = self.get_boto3_session()
            sns_client = session.client('sns', region_name=sns_region)

            # Normalize phone number
            phone_normalized = phone_number if phone_number.startswith('+') else f'+{phone_number.lstrip("+")}'

            # Test message
            message = "AWS SNS Standalone Test: This SMS was sent via Amazon SNS to verify the configuration. If you received this, SNS is working correctly!"

            # Run in thread pool since boto3 is synchronous
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: sns_client.publish(
                    PhoneNumber=phone_normalized,
                    Message=message,
                    MessageAttributes={
                        'AWS.SNS.SMS.SMSType': {
                            'DataType': 'String',
                            'StringValue': 'Transactional'
                        },
                        'AWS.SNS.SMS.MaxPrice': {
                            'DataType': 'Number',
                            'StringValue': '1.00'
                        }
                    }
                )
            )

            message_id = response.get('MessageId')
            print("✅ SMS sent successfully!")
            print(f"   To: {phone_normalized}")
            print(f"   Message ID: {message_id}")
            print(f"   Region: {sns_region}")
            return True

        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            print(f"❌ SNS Error: {error_code}")
            print(f"   Message: {error_message}")

            if error_code == 'InvalidParameter':
                print("   💡 Check phone number format (should be +1234567890)")
            elif error_code == 'OptedOut':
                print("   💡 Phone number has opted out of SMS")

            return False

        except NoCredentialsError:
            print("❌ AWS credentials not found or invalid")
            return False

        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False

    def print_configuration(self):
        """Print current configuration."""
        print("\n" + "="*60)
        print("AWS MESSAGING CONFIGURATION")
        print("="*60)

        print(f"AWS Region: {self.region}")
        print(f"SNS Region: {os.getenv('AWS_SNS_REGION', self.region)}")

        if self.profile:
            print(f"AWS Profile: {self.profile}")
        else:
            print(f"AWS Access Key: {'✅ Set' if self.access_key else '❌ Not set'}")
            print(f"AWS Secret Key: {'✅ Set' if self.secret_key else '❌ Not set'}")

        # Test basic AWS connectivity
        try:
            session = self.get_boto3_session()
            sts_client = session.client('sts')
            identity = sts_client.get_caller_identity()
            print(f"AWS Account: {identity.get('Account')}")
            print(f"AWS User/Role: {identity.get('Arn', '').split('/')[-1]}")
            print("✅ AWS connectivity verified")
        except Exception as e:
            print(f"❌ AWS connectivity failed: {e}")

        print("="*60)


async def main():
    """Main test function."""
    parser = argparse.ArgumentParser(description='Standalone AWS messaging services test')
    parser.add_argument('--email', help='Email address to send test email to')
    parser.add_argument('--sms', help='Phone number to send test SMS to (E.164 format, e.g., +1234567890)')
    parser.add_argument('--sender', help='Verified sender email address for SES')
    parser.add_argument('--config-only', action='store_true', help='Only show configuration, do not send messages')

    args = parser.parse_args()

    tester = AWSMessagingTester()

    # Always show configuration
    tester.print_configuration()

    if not tester.check_credentials():
        return

    if args.config_only:
        print("\n✅ Configuration check complete!")
        return

    if not args.email and not args.sms:
        print("\n❌ Please provide at least --email or --sms parameter")
        parser.print_help()
        return

    results = []

    # Test email if requested
    if args.email:
        print("\n" + "-"*40)
        email_success = tester.test_ses_email(args.email, args.sender)
        results.append(('Email (SES)', email_success))

    # Test SMS if requested
    if args.sms:
        print("\n" + "-"*40)
        sms_success = await tester.test_sns_sms(args.sms)
        results.append(('SMS (SNS)', sms_success))

    # Print summary
    print("\n" + "="*60)
    print("TEST RESULTS SUMMARY")
    print("="*60)

    all_passed = True
    for service, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{service:15}: {status}")
        if not success:
            all_passed = False

    if all_passed:
        print("\n🎉 All tests passed! AWS messaging is configured correctly.")
    else:
        print("\n⚠️  Some tests failed. Please check the configuration and try again.")
        print("\n💡 Common issues:")
        print("   - SES: Sender email not verified in AWS console")
        print("   - SES: Account in sandbox mode (can only send to verified addresses)")
        print("   - SNS: Phone number format incorrect (use +1234567890)")
        print("   - SNS: Phone number opted out of SMS")
        print("   - AWS: Insufficient IAM permissions")

    print("="*60)


if __name__ == '__main__':
    asyncio.run(main())
