# Stripe Webhook QA Test Suite

## Overview

This comprehensive test suite validates the Stripe webhook handler implementation for GitHub Issue #28: "Create Stripe Webhook Handler". The tests ensure the webhook system is secure, reliable, and production-ready for handling real payment processing.

## Test Coverage

### WEBHOOK-001: Security Validation
- **Purpose**: Validate signature verification, authentication, and security controls
- **Focus**: CSRF exemption, HTTP method restrictions, unauthorized request prevention
- **Critical**: Prevents webhook exploitation and unauthorized access
- **Duration**: ~25 minutes

### WEBHOOK-002: Event Processing
- **Purpose**: Validate payment event handling (success/failure/cancellation)
- **Focus**: Transaction updates, hour crediting, database consistency
- **Critical**: Ensures accurate payment processing and customer billing
- **Duration**: ~35 minutes

### WEBHOOK-003: Idempotency Testing
- **Purpose**: Validate duplicate event handling and retry safety
- **Focus**: Prevents double-processing, state consistency, atomic operations
- **Critical**: Prevents financial discrepancies from Stripe retries
- **Duration**: ~30 minutes

### WEBHOOK-004: Error Handling
- **Purpose**: Validate graceful degradation and error recovery
- **Focus**: Malformed requests, API failures, resource exhaustion
- **Critical**: Ensures system stability under adverse conditions
- **Duration**: ~40 minutes

### WEBHOOK-005: Integration Testing
- **Purpose**: Validate PaymentService integration and database consistency
- **Focus**: End-to-end flow, model relationships, atomic transactions
- **Critical**: Ensures reliable integration with platform components
- **Duration**: ~45 minutes

### WEBHOOK-006: Stripe CLI Testing
- **Purpose**: Validate real webhook testing with Stripe infrastructure
- **Focus**: Live event processing, management command validation
- **Critical**: Confirms production readiness with real Stripe environment
- **Duration**: ~50 minutes

## Prerequisites

### System Requirements
- Python virtual environment configured (.venv directory)
- Django development environment with PostgreSQL
- Stripe CLI installed and authenticated
- Test environment with proper Stripe configuration

### Environment Setup
```bash
# Activate virtual environment
cd /Users/anapmc/Code/aprendecomigo
source .venv/bin/activate

# Start development servers
make dev

# Install Stripe CLI (if not already installed)
# macOS: brew install stripe/stripe-cli/stripe
# Other: https://stripe.com/docs/stripe-cli

# Authenticate Stripe CLI
stripe login
```

### Required Environment Variables
```bash
export STRIPE_SECRET_KEY="sk_test_..."
export STRIPE_PUBLIC_KEY="pk_test_..."
export STRIPE_WEBHOOK_SECRET="whsec_..."  # Updated during CLI testing
export DJANGO_ENV=development
```

## Test Execution

### Individual Test Execution
```bash
cd qa-tests/webhook/webhook-001
# Follow test-case.txt instructions step-by-step

cd qa-tests/webhook/webhook-002
# Follow test-case.txt instructions step-by-step

# Continue for all webhook tests...
```

### Management Command Testing
```bash
cd backend

# Comprehensive webhook testing
python manage.py test_stripe_webhook --all

# Individual command functions
python manage.py test_stripe_webhook --validate-config
python manage.py test_stripe_webhook --create-test-data
python manage.py test_stripe_webhook --test-endpoint
python manage.py test_stripe_webhook --stripe-cli-instructions
```

### Stripe CLI Integration
```bash
# Start webhook forwarding
stripe listen --forward-to http://localhost:8000/api/finances/webhooks/stripe/

# Trigger test events
stripe trigger payment_intent.succeeded
stripe trigger payment_intent.payment_failed
stripe trigger payment_intent.canceled
```

## Critical Test Areas

### Security (WEBHOOK-001)
- **Signature Verification**: Ensures only Stripe can trigger webhooks
- **Authentication Controls**: Prevents unauthorized access attempts
- **Input Validation**: Protects against malformed or malicious requests
- **Error Handling**: Prevents information disclosure through error responses

### Financial Accuracy (WEBHOOK-002, WEBHOOK-003)
- **Payment Processing**: Accurate transaction status updates
- **Hour Crediting**: Precise hour allocation for successful payments
- **Idempotency**: Prevents double-charging from duplicate events
- **Database Consistency**: Maintains accurate account balances

### System Reliability (WEBHOOK-004, WEBHOOK-005)
- **Error Recovery**: Graceful handling of API failures and errors
- **Integration Stability**: Reliable PaymentService integration
- **Resource Management**: Prevents memory leaks and exhaustion
- **Atomic Operations**: Ensures data integrity during failures

### Production Readiness (WEBHOOK-006)
- **Live Testing**: Compatibility with real Stripe infrastructure
- **Developer Tools**: Management command functionality
- **Performance**: Acceptable response times under load
- **Monitoring**: Comprehensive logging and debugging capabilities

## Expected Results

### Security Tests (WEBHOOK-001)
- All unauthorized requests properly rejected
- Signature verification working with appropriate error responses
- No information leakage in error messages
- System remains stable under security testing

### Functional Tests (WEBHOOK-002)
- Successful payments credit hours and update transaction status
- Failed payments update status with proper error information
- Canceled payments handled correctly without crediting
- Database consistency maintained across all scenarios

### Reliability Tests (WEBHOOK-003, WEBHOOK-004)
- Duplicate events handled idempotently without double-processing
- Error scenarios handled gracefully without data corruption
- System remains available and responsive under adverse conditions
- Complete audit trail maintained for all events

### Integration Tests (WEBHOOK-005, WEBHOOK-006)
- Perfect integration between webhook and PaymentService
- Live Stripe events processed correctly with real signatures
- Management command provides comprehensive testing capabilities
- Production workflow validated end-to-end

## Troubleshooting

### Common Issues

1. **Signature Verification Failures**
   - Ensure STRIPE_WEBHOOK_SECRET matches Stripe CLI output
   - Check webhook endpoint URL is correctly configured
   - Verify Stripe CLI is forwarding to correct local port

2. **Database Connection Issues**
   - Ensure Django development server is running
   - Check database configuration in settings
   - Verify test data is created successfully

3. **Stripe CLI Problems**
   - Ensure Stripe CLI is installed and authenticated
   - Check network connectivity to Stripe
   - Verify correct test environment (not live keys)

4. **Event Processing Failures**
   - Check Django logs for detailed error information
   - Verify PaymentService is functioning correctly
   - Ensure test transactions exist before triggering events

### Debug Commands
```bash
# Check webhook endpoint status
curl http://localhost:8000/api/finances/webhooks/stripe/

# View recent logs
make logs | tail -50

# Check database state
python manage.py shell -c "
from finances.models import PurchaseTransaction
print(PurchaseTransaction.objects.all().count())
"

# Test Stripe CLI connection
stripe events list --limit 3
```

## Success Criteria

All tests must achieve **PASS** status with the following requirements:

1. **Security**: 100% of security controls functioning correctly
2. **Accuracy**: 100% of payment processing scenarios working correctly  
3. **Reliability**: 100% of error scenarios handled gracefully
4. **Integration**: 100% of system integration points working correctly
5. **Performance**: Acceptable response times under test load
6. **Production**: Ready for deployment with real Stripe infrastructure

Any **FAIL** status indicates critical issues that must be resolved before production deployment.

## Compliance and Audit

This test suite provides comprehensive validation for:
- **PCI DSS Compliance**: Secure payment data handling
- **Financial Accuracy**: Accurate transaction processing
- **System Reliability**: Robust error handling and recovery
- **Audit Requirements**: Complete transaction logging and monitoring

The webhook system processes sensitive financial data and must meet the highest standards for security, accuracy, and reliability.