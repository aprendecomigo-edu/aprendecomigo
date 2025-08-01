# GitHub Issue #57: Student Hour Balance Dashboard Backend Analysis

**Date:** 2025-08-01  
**Issue:** Student Hour Balance Dashboard and Renewal System Backend Implementation  
**Status:** Technical Analysis Complete

## Executive Summary

After analyzing the current Django backend infrastructure, I've identified that the Aprende Comigo platform already has a robust foundation for student hour balance management through the `finances` app. The existing models and services provide strong support for tracking balances, but need extensions for notifications and renewal functionality to fully support GitHub Issue #57.

## Current Infrastructure Analysis

### Existing Models (Strong Foundation)

#### 1. StudentAccountBalance Model
- **Location:** `backend/finances/models.py`
- **Status:** Production Ready ✅
- **Features:**
  - Tracks `hours_purchased`, `hours_consumed`, `balance_amount`
  - Calculates `remaining_hours` property
  - One-to-one relationship with CustomUser
  - Automatic balance updates via save() overrides

#### 2. PurchaseTransaction Model
- **Status:** Production Ready ✅
- **Features:**
  - Complete Stripe integration with `stripe_payment_intent_id`
  - Package expiration tracking with `expires_at` field
  - Metadata storage for plan details
  - Transaction status management
  - Support for both packages and subscriptions

#### 3. HourConsumption Model
- **Status:** Production Ready ✅
- **Features:**
  - Links sessions to specific purchase transactions (FIFO tracking)
  - Refund functionality with `is_refunded` flag
  - Detailed audit trail for hour usage

#### 4. PricingPlan Model
- **Status:** Production Ready ✅
- **Features:**
  - Active plan management with `is_active` flag
  - Package vs subscription support
  - Display ordering and featured plan support

### Existing Services (Strong Foundation)

#### 1. PaymentService
- **Location:** `backend/finances/services/payment_service.py`
- **Features:**
  - Complete Stripe payment intent creation
  - Payment completion confirmation
  - Automatic hour crediting
  - Account balance updates

#### 2. StudentBalanceViewSet
- **Location:** `backend/finances/views.py` (lines 1455-1828)
- **Status:** Production Ready ✅
- **Features:**
  - Balance summary API endpoint
  - Purchase history with pagination
  - Package status tracking (active/expired)
  - Upcoming expiration detection
  - Booking eligibility checks

#### 3. HourDeductionService
- **Location:** `backend/finances/services/hour_deduction_service.py`
- **Features:**
  - FIFO hour consumption logic
  - Package expiration validation
  - Insufficient balance detection

## Gap Analysis for Issue #57 Requirements

### 1. ✅ Hour Balance Tracking - COMPLETE
**Current Status:** Fully implemented
- Real-time balance calculation
- Purchase/consumption tracking
- Expiration management

### 2. ✅ Usage History - COMPLETE  
**Current Status:** Fully implemented
- Complete transaction history API
- Session-linked consumption tracking
- Refund audit trails

### 3. ⚠️ Automatic Notifications - PARTIAL
**Current Status:** Infrastructure exists but needs implementation
- Empty `notifications` app exists
- Package expiration detection implemented
- Missing: Email/in-app notification delivery

### 4. ⚠️ One-Click Renewals - PARTIAL
**Current Status:** Payment infrastructure ready, needs renewal logic
- Stripe integration complete
- Missing: Renewal-specific endpoints
- Missing: Saved payment method handling

### 5. ⚠️ Quick Top-ups - PARTIAL
**Current Status:** Same as renewals
- Purchase initiation API exists
- Missing: Saved payment method integration

### 6. ❌ Saved Payment Methods - NOT IMPLEMENTED
**Current Status:** Needs implementation
- Stripe Customer creation exists
- Missing: Payment method storage/retrieval
- Missing: Security compliance for stored methods

## Recommended Implementation Strategy

### Phase 1: Notification System (2-3 days)
**Priority:** HIGH - Required for balance warnings

#### Backend Tasks:
1. **Create Notification Models**
   ```python
   # backend/notifications/models.py
   class NotificationType(models.TextChoices):
       LOW_BALANCE = "low_balance", _("Low Balance Warning")
       PACKAGE_EXPIRING = "package_expiring", _("Package Expiring")
       BALANCE_DEPLETED = "balance_depleted", _("Balance Depleted")
   
   class Notification(models.Model):
       user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
       type = models.CharField(choices=NotificationType.choices)
       title = models.CharField(max_length=200)
       message = models.TextField()
       is_read = models.BooleanField(default=False)
       created_at = models.DateTimeField(auto_now_add=True)
   ```

2. **Create Notification Service**
   ```python
   # backend/notifications/services/notification_service.py
   class NotificationService:
       @staticmethod
       def check_balance_alerts(student_user):
           # Check balance thresholds (e.g., < 2 hours)
           # Create notifications if needed
           # Send emails if configured
   
       @staticmethod
       def check_expiration_warnings():
           # Check packages expiring in 7 days
           # Create notifications
           # Send reminder emails
   ```

3. **Create Notification API Endpoints**
   ```python
   # GET /api/notifications/ - List user notifications
   # POST /api/notifications/{id}/mark-read/ - Mark as read
   # GET /api/notifications/unread-count/ - Get unread count
   ```

#### Database Migrations:
```bash
python manage.py makemigrations notifications
python manage.py migrate
```

### Phase 2: Payment Method Storage & Renewals (3-4 days)
**Priority:** MEDIUM-HIGH - Core renewal functionality

#### Backend Tasks:
1. **Extend Stripe Integration**
   ```python
   # backend/finances/services/saved_payment_service.py
   class SavedPaymentService:
       @staticmethod
       def save_payment_method(user, payment_method_id):
           # Create/update Stripe Customer
           # Attach payment method to customer
           # Store reference in database
   
       @staticmethod
       def get_saved_methods(user):
           # Retrieve user's saved payment methods
           # Return formatted data for frontend
   ```

2. **Create Renewal API Endpoints**
   ```python
   # POST /api/finances/balance/renew/ - Renew expired package
   # POST /api/finances/balance/top-up/ - Quick hour top-up
   # GET /api/finances/saved-methods/ - List saved payment methods
   # POST /api/finances/saved-methods/ - Save new payment method
   ```

3. **Extend Payment Models**
   ```python
   # Add to CustomUser or create separate model
   class SavedPaymentMethod(models.Model):
       user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
       stripe_payment_method_id = models.CharField(max_length=255)
       is_default = models.BooleanField(default=False)
       card_last_four = models.CharField(max_length=4)
       card_brand = models.CharField(max_length=20)
       expires_month = models.PositiveSmallIntegerField()
       expires_year = models.PositiveSmallIntegerField()
   ```

## Technical Challenges & Solutions

### Challenge 1: Balance Threshold Management
**Solution:** Configurable thresholds per student or global settings
```python
# Add to StudentAccountBalance model
class StudentAccountBalance(models.Model):
    # ... existing fields ...
    low_balance_threshold = models.DecimalField(
        max_digits=4, decimal_places=2, default=Decimal('2.00')
    )
```

### Challenge 2: Notification Delivery Timing
**Solution:** Use Django's task scheduling or Celery for periodic checks
```python
# backend/notifications/tasks.py
from celery import shared_task

@shared_task
def check_balance_notifications():
    # Run every hour to check balance thresholds
    # Send notifications as needed
```

### Challenge 3: PCI Compliance for Saved Payment Methods
**Solution:** Use Stripe's secure payment method storage (no card data on our servers)
- Store only Stripe payment method IDs
- Use Stripe's secure customer portal for payment method management
- Implement proper tokenization

## Database Schema Changes Required

### Minimal Schema Changes:
1. **Notifications App Models** (new tables)
2. **SavedPaymentMethod Model** (new table)
3. **Optional: Balance threshold fields** (alter existing table)

### Migration Strategy:
```bash
# Phase 1
python manage.py makemigrations notifications
python manage.py migrate

# Phase 2
python manage.py makemigrations finances
python manage.py migrate
```

## API Endpoint Architecture

### New Endpoints Needed:

#### Notifications:
- `GET /api/notifications/` - List notifications
- `POST /api/notifications/{id}/read/` - Mark as read
- `GET /api/notifications/unread-count/` - Unread count

#### Payment Methods:
- `GET /api/finances/saved-methods/` - List saved methods
- `POST /api/finances/saved-methods/` - Save new method
- `DELETE /api/finances/saved-methods/{id}/` - Remove method

#### Renewals & Top-ups:
- `POST /api/finances/balance/renew/{transaction_id}/` - Renew package
- `POST /api/finances/balance/quick-topup/` - Quick hour purchase

## Security Considerations

### 1. Payment Method Security
- Never store raw card data
- Use Stripe's secure payment method storage
- Implement proper authentication for payment endpoints
- Add rate limiting for payment operations

### 2. Notification Security
- Ensure users can only access their own notifications
- Sanitize notification content
- Implement proper permission checks

### 3. Balance Check Security
- Validate user access to balance information
- Implement proper role-based access for admin features
- Add audit logging for balance modifications

## Testing Strategy

### 1. Unit Tests Required:
- Notification service tests
- Saved payment method tests
- Renewal logic tests
- Balance threshold detection tests

### 2. Integration Tests Required:
- End-to-end renewal flow
- Stripe webhook processing for renewals
- Notification delivery testing

### 3. Security Tests Required:
- Permission boundary testing
- Payment method access control
- Notification access control

## Conclusion

The Aprende Comigo platform has an excellent foundation for implementing the student hour balance dashboard and renewal system. The existing `finances` app provides robust balance tracking and payment processing infrastructure.

**Recommended approach:**
1. **Start with Phase 1** (Notifications) as it provides immediate value
2. **Follow with Phase 2** (Renewals) to complete the functionality
3. **Leverage existing infrastructure** to minimize development time
4. **Focus on security** especially for payment method storage

**Estimated Timeline:**
- Phase 1 (Notifications): 2-3 days
- Phase 2 (Renewals): 3-4 days
- Total: 5-7 days for complete implementation

The existing codebase quality is high, with proper error handling, comprehensive testing, and good Django conventions throughout.