# Django Test Fixes TODO List

## Summary
- Total Tests: 1278
- **Errors: 254** (these need fixing)
- Failures: 181 (these are business logic failures, not errors)

## COMPLETED FIXES

### ✅ 1. Messaging Signals Import Issues
- **File**: `messaging/signals/email_automation_signals.py`
- **Error**: Circular import issues with accounts models
- **Fix**: Used lazy references and apps.get_model() for cross-app dependencies
- **Status**: 🟢 FIXED

### ✅ 2. EmailAuthTests AttributeError 
- **File**: `accounts/tests/test_auth.py`
- **Error**: Missing `self.email` attribute and duplicate user creation
- **Fix**: Added `self.email` attribute in setUp() and removed duplicate user creation in tests
- **Status**: 🟢 FIXED

## Priority 1: Current Errors (From test output analysis)

### 2. Stripe Configuration Missing
- **File**: `finances/services/stripe_base.py`
- **Error**: `ValueError: Missing required Stripe configuration: STRIPE_SECRET_KEY`
- **Fix**: Add test configuration for Stripe settings
- **Status**: 🔴 Not Fixed

### 3. EmailAuthTests AttributeError 
- **File**: `accounts/tests/test_auth.py`
- **Error**: Multiple auth test errors, missing setup
- **Fix**: Fix test setup and configuration
- **Status**: 🔴 Not Fixed

### 4. DateTime Timezone Warnings
- **File**: Various models with DateTimeField
- **Error**: `DateTimeField received a naive datetime while time zone support is active`
- **Fix**: Use timezone-aware datetime in tests
- **Status**: 🔴 Not Fixed

### 2. Import/Module Issues
- **Search for**: Import errors, missing dependencies
- **Status**: 🔴 Not Fixed

### 3. Cross-App Dependency Issues
- **Search for**: Circular imports, missing app references
- **Status**: 🔴 Not Fixed

## Priority 2: Configuration Errors

### 4. Database/Migration Issues
- **Search for**: Migration dependency errors
- **Status**: 🔴 Not Fixed

### 5. Settings/Environment Issues
- **Search for**: Missing settings, environment configs
- **Status**: 🔴 Not Fixed

## Priority 3: Model/Signal Issues

### 6. Signal Registration Problems
- **Search for**: Signal connection errors
- **Status**: 🔴 Not Fixed

### 7. Model Reference Issues
- **Search for**: Lazy loading, string references
- **Status**: 🔴 Not Fixed

## Fixing Strategy
1. Fix the first error (EmailAuthTests)
2. Run tests again to discover next error type
3. Categorize and fix errors systematically
4. Apply Django best practices for cross-app dependencies
5. Ensure all fixes follow coding instructions

## Django Best Practices to Apply
- Use lazy references ("app.Model" strings) for ForeignKey relationships
- Use apps.get_model() for runtime model access
- Declare migration dependencies explicitly when needed
- Use AppConfig.ready() for signal registration
- Avoid circular imports at module level
