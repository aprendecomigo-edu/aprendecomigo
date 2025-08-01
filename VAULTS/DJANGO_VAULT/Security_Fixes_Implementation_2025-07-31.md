# Security Fixes Implementation - Issue #46
*Date: 2025-07-31*

## Critical Security Vulnerabilities Found

### 1. 🚨 Tutor Detection Vulnerability (CRITICAL)
**Current Implementation:**
```python
# backend/accounts/views.py line 476
is_tutor = "'s Tutoring Practice" in school_name or "Tutoring" in school_name
```

**Problem:** Regular schools can exploit this by including "Tutoring" in their name to gain tutor privileges.

**Solution:** Replace with explicit user_type field from frontend signup flow.

### 2. 🚨 Transaction Rollback Protection (CRITICAL)
**Current Issue:** User and school creation not wrapped in transaction - partial data can be left in database if any step fails.

**Solution:** Wrap all signup operations in `@transaction.atomic` decorator.

### 3. 🚨 Cache Key Security (HIGH)
**Current Issue:** Predictable cache keys like `tutor_analytics_{teacher.id}_{school.id}_{time_range}` vulnerable to cache poisoning.

**Solution:** Use hash-based keys with session tokens.

### 4. Request Rate Limiting (MEDIUM)
**Current Issue:** No protection against automated attacks on signup endpoints.

**Solution:** Implement Django rate limiting decorators.

## Implementation Plan

### Phase 1: Frontend Changes
1. Update OnboardingData interface to include user_type field
2. Modify signup form to pass user_type from URL parameter
3. Test frontend changes

### Phase 2: Backend Changes  
1. Update CreateUserSerializer to accept user_type field
2. Replace vulnerable tutor detection logic
3. Add transaction protection
4. Implement cache key security
5. Add rate limiting

### Phase 3: Security Testing
1. Create test cases for security fixes
2. Verify no regressions in existing functionality
3. Test edge cases and attack scenarios

## Current Frontend Flow Analysis

The frontend already has proper user type selection:
- User selects 'tutor' or 'school' in UserTypeSelectionForm
- Type is passed via URL parameter: `/auth/signup?type=tutor`
- Signup form receives type and validates it
- However, this type is NOT currently sent to the backend API

## Backend API Current Structure

```typescript
interface OnboardingData {
  name: string;
  email: string;
  phone_number: string;
  primary_contact: 'email' | 'phone';
  school: {
    name: string;
    // ... other school fields
  };
  // Missing: user_type field!
}
```

The backend receives this data and tries to infer tutor status from school name patterns - this is the vulnerability we need to fix.