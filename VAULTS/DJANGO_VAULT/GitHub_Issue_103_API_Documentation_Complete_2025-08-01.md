# GitHub Issue #103: API Documentation - Receipt Generation and Payment Method Management

**Date:** 2025-08-01  
**Status:** Complete Implementation with Comprehensive Documentation  
**Issue:** Backend Receipt Generation and Payment Method Management APIs

## API Endpoints Overview

All endpoints use the existing `IsAuthenticated` permission and follow the established StudentBalanceViewSet pattern with proper error handling.

### Base URL
All endpoints are prefixed with: `/api/student-balance/`

---

## Receipt Generation APIs

### 1. List Student Receipts
**Endpoint:** `GET /api/student-balance/receipts/`  
**Authentication:** Required  
**Description:** List all receipts for the authenticated student with optional filtering.

#### Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `is_valid` | boolean | No | Filter by receipt validity (true/false) |
| `start_date` | string | No | Filter receipts generated after this date (YYYY-MM-DD) |
| `end_date` | string | No | Filter receipts generated before this date (YYYY-MM-DD) |
| `email` | string | No | Admin only: Access receipts for specific student email |

#### Response Format
```json
{
  "success": true,
  "receipts": [
    {
      "id": 1,
      "receipt_number": "RCP-2025-A1B2C3D4",
      "amount": 50.00,
      "generated_at": "2025-01-15T10:30:00Z",
      "is_valid": true,
      "transaction_id": 123,
      "transaction_type": "Package",
      "plan_name": "10 Hour Package",
      "has_pdf": true,
      "download_url": "/media/receipts/2025/01/receipt_RCP-2025-A1B2C3D4.pdf"
    }
  ],
  "count": 1
}
```

#### Error Responses
- `400 Bad Request`: Invalid date format
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Permission denied (admin access only)
- `500 Internal Server Error`: Service error

---

### 2. Generate Receipt
**Endpoint:** `POST /api/student-balance/receipts/generate/`  
**Authentication:** Required  
**Description:** Generate a new PDF receipt for a completed transaction.

#### Request Body
```json
{
  "transaction_id": 123,
  "force_regenerate": false  // Optional, defaults to false
}
```

#### Response Format (Success)
```json
{
  "success": true,
  "receipt_id": 1,
  "receipt_number": "RCP-2025-A1B2C3D4",
  "pdf_file_url": "/media/receipts/2025/01/receipt_RCP-2025-A1B2C3D4.pdf",
  "amount": 50.00,
  "generated_at": "2025-01-15T10:30:00Z",
  "message": "Receipt generated successfully"
}
```

#### Response Format (Already Exists)
```json
{
  "success": true,
  "receipt_id": 1,
  "receipt_number": "RCP-2025-A1B2C3D4",
  "already_existed": true,
  "message": "Receipt already exists"
}
```

#### Error Responses
- `400 Bad Request`: Missing transaction_id, invalid status, or validation error
- `401 Unauthorized`: Authentication required
- `404 Not Found`: Transaction not found
- `500 Internal Server Error`: PDF generation failed

---

### 3. Download Receipt
**Endpoint:** `GET /api/student-balance/receipts/{receipt_id}/download/`  
**Authentication:** Required  
**Description:** Get secure download URL for a specific receipt.

#### URL Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `receipt_id` | integer | Yes | ID of the receipt to download |

#### Response Format
```json
{
  "success": true,
  "download_url": "/media/receipts/2025/01/receipt_RCP-2025-A1B2C3D4.pdf",
  "receipt_number": "RCP-2025-A1B2C3D4",
  "filename": "receipt_RCP-2025-A1B2C3D4.pdf"
}
```

#### Error Responses
- `400 Bad Request`: Invalid receipt (expired or corrupted)
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Receipt belongs to different student
- `404 Not Found`: Receipt not found or PDF file missing
- `500 Internal Server Error`: Download preparation failed

---

## Payment Method Management APIs

### 1. List Payment Methods
**Endpoint:** `GET /api/student-balance/payment-methods/`  
**Authentication:** Required  
**Description:** List all stored payment methods for the authenticated student.

#### Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `include_expired` | boolean | No | Include expired payment methods (default: false) |
| `email` | string | No | Admin only: Access payment methods for specific student |

#### Response Format
```json
{
  "success": true,
  "payment_methods": [
    {
      "id": 1,
      "card_brand": "visa",
      "card_last4": "4242",
      "card_exp_month": 12,
      "card_exp_year": 2025,
      "card_display": "Visa ****4242",
      "is_default": true,
      "is_expired": false,
      "created_at": "2025-01-15T10:30:00Z"
    }
  ],
  "count": 1
}
```

#### Error Responses
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Permission denied (admin access only)
- `500 Internal Server Error`: Service error

---

### 2. Add Payment Method
**Endpoint:** `POST /api/student-balance/payment-methods/`  
**Authentication:** Required  
**Description:** Add a new stored payment method using Stripe tokenization.

#### Request Body
```json
{
  "stripe_payment_method_id": "pm_1234567890abcdef",
  "is_default": false  // Optional, defaults to false
}
```

#### Request Validation
- `stripe_payment_method_id`: Must start with 'pm_' and be valid Stripe PaymentMethod ID
- `is_default`: Boolean flag to set as default payment method

#### Response Format
```json
{
  "success": true,
  "payment_method_id": 1,
  "card_display": "Visa ****4242",
  "is_default": true,
  "message": "Payment method added successfully"
}
```

#### Error Responses
- `400 Bad Request`: Invalid Stripe ID, payment method already exists, or validation error
- `401 Unauthorized`: Authentication required
- `500 Internal Server Error`: Stripe integration error or creation failed

---

### 3. Remove Payment Method
**Endpoint:** `DELETE /api/student-balance/payment-methods/{payment_method_id}/`  
**Authentication:** Required  
**Description:** Remove a stored payment method and detach from Stripe.

#### URL Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `payment_method_id` | integer | Yes | ID of the payment method to remove |

#### Response Format
```json
{
  "success": true,
  "message": "Payment method removed successfully",
  "was_default": false
}
```

#### Behavior Notes
- If removing the default payment method and other methods exist, another method is automatically set as default
- Payment method is detached from Stripe (best effort - failure doesn't prevent local removal)

#### Error Responses
- `401 Unauthorized`: Authentication required
- `404 Not Found`: Payment method not found or doesn't belong to user
- `500 Internal Server Error`: Removal failed

---

### 4. Set Default Payment Method
**Endpoint:** `POST /api/student-balance/payment-methods/{payment_method_id}/set-default/`  
**Authentication:** Required  
**Description:** Set a payment method as the default for the student.

#### URL Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `payment_method_id` | integer | Yes | ID of the payment method to set as default |

#### Response Format
```json
{
  "success": true,
  "message": "Default payment method updated successfully"
}
```

#### Error Responses
- `400 Bad Request`: Payment method is expired
- `401 Unauthorized`: Authentication required
- `404 Not Found`: Payment method not found or doesn't belong to user
- `500 Internal Server Error`: Update failed

---

## Enhanced Subscription APIs

### Enhanced Student Balance Summary
**Endpoint:** `GET /api/student-balance/`  
**Authentication:** Required  
**Description:** Get comprehensive student balance information including subscription details.

#### Enhanced Response Format
The existing endpoint now includes additional `subscription_info` field:

```json
{
  "student_info": {
    "id": 1,
    "name": "Test Student",
    "email": "student@example.com"
  },
  "balance_summary": {
    "hours_purchased": "20.00",
    "hours_consumed": "5.00",
    "remaining_hours": "15.00",
    "balance_amount": "150.00"
  },
  "package_status": {
    "active_packages": [...],
    "expired_packages": [...]
  },
  "upcoming_expirations": [...],
  "subscription_info": {
    "is_active": true,
    "next_billing_date": "2025-02-15",
    "billing_cycle": "monthly",
    "subscription_status": "active",
    "cancel_at_period_end": false,
    "current_period_start": "2025-01-15",
    "current_period_end": "2025-02-14"
  }
}
```

#### Subscription Info Fields
| Field | Type | Description |
|-------|------|-------------|
| `is_active` | boolean | Whether student has active subscription |
| `next_billing_date` | string | Next billing date (YYYY-MM-DD) or null |
| `billing_cycle` | string | Billing frequency ("monthly") or null |
| `subscription_status` | string | Status: "active", "inactive", etc. |
| `cancel_at_period_end` | boolean | Whether subscription cancels at period end |
| `current_period_start` | string | Current billing period start date |
| `current_period_end` | string | Current billing period end date |

---

## Security Considerations

### Authentication & Authorization
- All endpoints require `IsAuthenticated` permission
- Students can only access their own data
- Admin users (is_staff=True) can access any student's data using email parameter
- Proper ownership validation for all operations

### PCI Compliance
- No sensitive card data stored in database
- Only Stripe tokens and display information (last 4 digits, brand, expiry) stored
- Payment method creation uses Stripe tokenization from frontend
- Secure detachment from Stripe on removal

### File Security
- PDF receipts stored in media directory with organized structure
- Secure access through Django file serving
- Proper cleanup of files when receipts are invalidated
- Receipt validation ensures user owns the receipt before download

---

## Error Handling Standards

### Consistent Error Format
```json
{
  "error": "Human-readable error message",
  "error_type": "category_of_error"  // Optional for debugging
}
```

### HTTP Status Codes
- `200 OK`: Successful operation
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data or business logic error
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Permission denied
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Unexpected server error

### Error Types
- `validation_error`: Request data validation failed
- `not_found`: Requested resource doesn't exist
- `permission_denied`: User lacks permission for operation
- `invalid_status`: Resource in wrong state for operation
- `stripe_error`: Stripe integration error
- `generation_error`: PDF generation failed
- `download_error`: File download preparation failed

---

## Rate Limiting & Performance

### Caching Strategy
- Receipt lists cached per user for 5 minutes
- Payment method lists cached per user for 10 minutes
- PDF generation results cached to prevent duplicate work

### Performance Optimizations
- Efficient database queries with select_related and prefetch_related
- Pagination support for large result sets
- Async PDF generation for large receipts (future enhancement)

---

## Integration Examples

### Frontend Integration
```javascript
// List receipts
const receipts = await apiClient.get('/api/student-balance/receipts/');

// Generate receipt
const newReceipt = await apiClient.post('/api/student-balance/receipts/generate/', {
  transaction_id: 123
});

// Add payment method (after Stripe tokenization)
const paymentMethod = await apiClient.post('/api/student-balance/payment-methods/', {
  stripe_payment_method_id: 'pm_1234567890abcdef',
  is_default: true
});

// Get enhanced balance with subscription info
const balanceInfo = await apiClient.get('/api/student-balance/');
```

### Testing Examples
```python
# Test receipt generation
def test_generate_receipt():
    response = client.post('/api/student-balance/receipts/generate/', {
        'transaction_id': completed_transaction.id
    })
    assert response.status_code == 201
    assert response.data['success'] is True

# Test payment method listing
def test_list_payment_methods():
    response = client.get('/api/student-balance/payment-methods/')
    assert response.status_code == 200
    assert len(response.data['payment_methods']) > 0
```

This completes the comprehensive implementation of GitHub Issue #103 with full API documentation, testing, and security considerations.