"""
Management command for testing Stripe webhook integration.

This command helps developers test the webhook handler by:
1. Creating test transactions in the database
2. Providing instructions for using Stripe CLI
3. Validating webhook endpoint configuration
4. Running integration tests with mock events
"""

from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from accounts.models import CustomUser
from finances.models import (
    PurchaseTransaction,
    StudentAccountBalance,
    TransactionPaymentStatus,
    TransactionType,
)
from finances.services.stripe_base import StripeService


class Command(BaseCommand):
    """Management command for testing Stripe webhook functionality."""

    help = "Test Stripe webhook integration by creating test data and providing instructions for Stripe CLI testing"

    def add_arguments(self, parser):
        """Add command-line arguments."""
        parser.add_argument(
            "--create-test-data", action="store_true", help="Create test transaction data for webhook testing"
        )

        parser.add_argument("--validate-config", action="store_true", help="Validate Stripe webhook configuration")

        parser.add_argument("--test-endpoint", action="store_true", help="Test webhook endpoint with mock events")

        parser.add_argument(
            "--stripe-cli-instructions", action="store_true", help="Show instructions for testing with Stripe CLI"
        )

        parser.add_argument(
            "--payment-intent-id", type=str, help="Specific payment intent ID to create test transaction for"
        )

        parser.add_argument("--all", action="store_true", help="Run all tests and validations")

    def handle(self, *args, **options):
        """Handle the command execution."""
        self.stdout.write(self.style.SUCCESS("Stripe Webhook Test Command"))
        self.stdout.write("=" * 50)

        # If --all is specified, run everything
        if options["all"]:
            options.update(
                {
                    "validate_config": True,
                    "create_test_data": True,
                    "test_endpoint": True,
                    "stripe_cli_instructions": True,
                }
            )

        # Validate configuration
        if options["validate_config"]:
            self._validate_configuration()

        # Create test data
        if options["create_test_data"]:
            self._create_test_data(options.get("payment_intent_id"))

        # Test endpoint
        if options["test_endpoint"]:
            self._test_webhook_endpoint()

        # Show Stripe CLI instructions
        if options["stripe_cli_instructions"]:
            self._show_stripe_cli_instructions()

        # If no specific options provided, show help
        if not any(
            [
                options["validate_config"],
                options["create_test_data"],
                options["test_endpoint"],
                options["stripe_cli_instructions"],
                options["all"],
            ]
        ):
            self._show_usage_help()

    def _validate_configuration(self):
        """Validate Stripe webhook configuration."""
        self.stdout.write("\n1. Validating Stripe Configuration...")
        self.stdout.write("-" * 40)

        try:
            # Initialize and test Stripe service
            stripe_service = StripeService()

            # Check required settings
            required_settings = ["STRIPE_SECRET_KEY", "STRIPE_PUBLIC_KEY", "STRIPE_WEBHOOK_SECRET"]

            missing_settings = []
            for setting in required_settings:
                value = getattr(settings, setting, None)
                if not value:
                    missing_settings.append(setting)
                else:
                    # Mask the key for security
                    masked_value = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
                    self.stdout.write(f"✓ {setting}: {masked_value}")

            if missing_settings:
                self.stdout.write(self.style.ERROR(f"✗ Missing settings: {', '.join(missing_settings)}"))
                raise CommandError("Missing required Stripe settings")

            # Test API connection
            self.stdout.write("\nTesting Stripe API connection...")
            result = stripe_service.verify_api_connection()

            if result["success"]:
                self.stdout.write(self.style.SUCCESS("✓ Stripe API connection successful"))
                self.stdout.write(f"  Account ID: {result.get('account_id', 'N/A')}")
            else:
                self.stdout.write(self.style.ERROR(f"✗ Stripe API connection failed: {result.get('message')}"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Configuration validation failed: {e!s}"))

    def _create_test_data(self, payment_intent_id: str | None = None):
        """Create test transaction data for webhook testing."""
        self.stdout.write("\n2. Creating Test Data...")
        self.stdout.write("-" * 40)

        try:
            # Create or get test student
            test_email = "webhook.test@aprendecomigo.com"
            student, created = CustomUser.objects.get_or_create(
                email=test_email, defaults={"name": "Webhook Test Student"}
            )

            if created:
                self.stdout.write(f"✓ Created test student: {test_email}")
            else:
                self.stdout.write(f"✓ Using existing test student: {test_email}")

            # Create or get student account balance
            _balance, created = StudentAccountBalance.objects.get_or_create(
                student=student,
                defaults={
                    "hours_purchased": Decimal("0.00"),
                    "hours_consumed": Decimal("0.00"),
                    "balance_amount": Decimal("0.00"),
                },
            )

            if created:
                self.stdout.write("✓ Created student account balance")
            else:
                self.stdout.write("✓ Using existing student account balance")

            # Create test transaction
            if not payment_intent_id:
                payment_intent_id = f"pi_test_webhook_{int(timezone.now().timestamp())}"

            # Check if transaction already exists
            existing_transaction = PurchaseTransaction.objects.filter(
                stripe_payment_intent_id=payment_intent_id
            ).first()

            if existing_transaction:
                self.stdout.write(f"✓ Using existing transaction with payment intent: {payment_intent_id}")
                transaction = existing_transaction
            else:
                transaction = PurchaseTransaction.objects.create(
                    student=student,
                    transaction_type=TransactionType.PACKAGE,
                    amount=Decimal("50.00"),
                    payment_status=TransactionPaymentStatus.PROCESSING,
                    stripe_payment_intent_id=payment_intent_id,
                    metadata={"hours": "10.00", "package_name": "10-hour test package", "test_transaction": True},
                )
                self.stdout.write(f"✓ Created test transaction with payment intent: {payment_intent_id}")

            # Display test data summary
            self.stdout.write("\nTest Data Summary:")
            self.stdout.write(f"  Student ID: {student.id}")
            self.stdout.write(f"  Student Email: {student.email}")
            self.stdout.write(f"  Transaction ID: {transaction.id}")
            self.stdout.write(f"  Payment Intent ID: {payment_intent_id}")
            self.stdout.write(f"  Amount: €{transaction.amount}")
            self.stdout.write(f"  Status: {transaction.payment_status}")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Failed to create test data: {e!s}"))

    def _test_webhook_endpoint(self):
        """Test webhook endpoint with mock events."""
        self.stdout.write("\n3. Testing Webhook Endpoint...")
        self.stdout.write("-" * 40)

        try:
            client = Client()
            webhook_url = reverse("finances:stripe-webhook")

            # Test 1: Missing signature
            self.stdout.write("Test 1: Missing signature header...")
            response = client.post(webhook_url, data="{}", content_type="application/json")

            if response.status_code == 400:
                self.stdout.write("✓ Correctly rejected request with missing signature")
            else:
                self.stdout.write(self.style.WARNING(f"⚠ Unexpected status code: {response.status_code}"))

            # Test 2: Invalid signature
            self.stdout.write("Test 2: Invalid signature...")
            response = client.post(
                webhook_url, data="{}", content_type="application/json", HTTP_STRIPE_SIGNATURE="invalid_signature"
            )

            if response.status_code == 400:
                self.stdout.write("✓ Correctly rejected request with invalid signature")
            else:
                self.stdout.write(self.style.WARNING(f"⚠ Unexpected status code: {response.status_code}"))

            # Test 3: Wrong HTTP method
            self.stdout.write("Test 3: Wrong HTTP method...")
            response = client.get(webhook_url)

            if response.status_code == 405:
                self.stdout.write("✓ Correctly rejected GET request (POST only)")
            else:
                self.stdout.write(self.style.WARNING(f"⚠ Unexpected status code: {response.status_code}"))

            self.stdout.write(f"\nWebhook endpoint URL: {webhook_url}")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Webhook endpoint testing failed: {e!s}"))

    def _show_stripe_cli_instructions(self):
        """Show instructions for testing with Stripe CLI."""
        self.stdout.write("\n4. Stripe CLI Testing Instructions")
        self.stdout.write("-" * 40)

        # Get webhook URL
        webhook_url = reverse("finances:stripe-webhook")
        base_url = getattr(settings, "WEBHOOK_BASE_URL", "http://localhost:8000")
        full_webhook_url = f"{base_url}{webhook_url}"

        instructions = f"""
1. Install Stripe CLI:
   Download from: https://stripe.com/docs/stripe-cli

2. Login to Stripe CLI:
   stripe login

3. Forward events to your local webhook endpoint:
   stripe listen --forward-to {full_webhook_url}

4. Copy the webhook signing secret from the CLI output and add to your .env:
   STRIPE_WEBHOOK_SECRET=whsec_...

5. Test specific events:
   # Test successful payment
   stripe trigger payment_intent.succeeded

   # Test failed payment
   stripe trigger payment_intent.payment_failed

   # Test canceled payment
   stripe trigger payment_intent.canceled

6. Monitor webhook events:
   # Watch Django logs
   tail -f logs/django.log

   # Check Stripe dashboard
   https://dashboard.stripe.com/test/events

7. Test with real payment intent (replace pi_xxx with actual ID):
   stripe events resend evt_xxx

8. Test idempotency by sending the same event twice:
   stripe events resend evt_xxx
   stripe events resend evt_xxx

IMPORTANT NOTES:
- Ensure your Django development server is running: python manage.py runserver
- Use test mode keys only (sk_test_xxx, pk_test_xxx)
- Test transactions created by this command use IDs starting with 'pi_test_webhook_'
- Check your database to verify transactions are updated correctly
- Monitor logs for detailed webhook processing information

TROUBLESHOOTING:
- If webhook signature verification fails, ensure STRIPE_WEBHOOK_SECRET matches CLI output
- If events aren't processed, check Django logs for errors
- If database updates fail, verify test data exists (run with --create-test-data)
"""

        self.stdout.write(instructions)

    def _show_usage_help(self):
        """Show usage help and examples."""
        self.stdout.write("\nUsage Examples:")
        self.stdout.write("-" * 40)

        examples = """
# Run all tests and validations
python manage.py test_stripe_webhook --all

# Just validate configuration
python manage.py test_stripe_webhook --validate-config

# Create test data only
python manage.py test_stripe_webhook --create-test-data

# Create test data with specific payment intent ID
python manage.py test_stripe_webhook --create-test-data --payment-intent-id pi_test_123

# Test endpoint functionality
python manage.py test_stripe_webhook --test-endpoint

# Show Stripe CLI instructions
python manage.py test_stripe_webhook --stripe-cli-instructions

# Combine multiple options
python manage.py test_stripe_webhook --validate-config --create-test-data --stripe-cli-instructions
"""

        self.stdout.write(examples)

        self.stdout.write("\nFor more information, use:")
        self.stdout.write("python manage.py test_stripe_webhook --help")
