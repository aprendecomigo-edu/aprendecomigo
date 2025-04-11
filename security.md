# Security Audit: Aprende Comigo App

## Authentication System

### Strengths:
1. ✅ **TOTP-Based Authentication**: Using time-based one-time passwords with pyotp for email authentication.
2. ✅ **Token-Based Authentication**: Using Knox for secure token management with auto-expiry.
3. ✅ **Secure Token Storage**: Frontend uses SecureStore with AsyncStorage fallback.
4. ✅ **Rate Limiting**: Implemented for login endpoints (5/hour for code requests, 10/hour for verification).
5. ✅ **Failed Attempt Tracking**: EmailVerificationCode tracks and limits failed verification attempts.

### Vulnerabilities:
1. ❌ **Hardcoded Secret Key**: Default secret key in settings.py (`django-insecure-r0i5j27-gmjj&c6v@0mf5=mz$oi%e75o%iw8-i1ma6ej0m7=^q`).
2. ❌ **Default TOTP Secret**: `DEFAULTSECRETKEYTOBEREPLACED` in EmailVerificationCode model.
3. ❌ **SQLite in Production**: The configuration uses SQLite for all environments, including production.

## Authorization

### Strengths:
1. ✅ **Custom Permissions**: Proper role-based permissions (IsTeacher, IsStudent, IsOwner).
2. ✅ **Object-Level Permissions**: IsOwner checks for object ownership.
3. ✅ **Request/Response Interceptors**: Frontend API client correctly manages tokens.

### Vulnerabilities:
1. ❌ **Potential Model Exposure**: Some viewsets could expose data due to permissive queryset definitions.
2. ❌ **Missing RBAC in Student/Teacher Views**: Teacher data could be partially viewable by students.

## Data Protection

### Strengths:
1. ✅ **HTTPS Configuration**: Secure settings for cookies and HSTS in production.
2. ✅ **CSRF Protection**: Middleware enabled and secure cookie settings.

### Vulnerabilities:
1. ❌ **Sensitive Data Storage**: CC numbers and personal information stored in models without encryption.
2. ❌ **Calendar iFrame**: Potential XSS vector if not properly sanitized (`calendar_iframe` fields).
3. ❌ **Base64 Image Storage**: `cc_photo` field might store base64 encoded citizen card photos without encryption.

## API Security

### Strengths:
1. ✅ **Input Validation**: Proper serializer field validation.
2. ✅ **Throttling**: Global and endpoint-specific rate limits implemented.
3. ✅ **CORS Middleware**: Properly configured but needs specific origins set.

### Vulnerabilities:
1. ❌ **Debug Mode**: Potential for being enabled in production.
2. ❌ **Verbose Error Messages**: Might reveal implementation details (can't confirm without checking custom_exception_handler).

## Sensitive Information

### Strengths:
1. ✅ **Environment Variables**: Using dotenv for configuration.
2. ✅ **Password Validators**: Strong password validation policies.

### Vulnerabilities:
1. ❌ **Email Verification Code Exposure**: Potentially shows provisioning URI to users.
2. ❌ **Exposed Personal Information**: Student and teacher models store addresses and phone numbers that might be exposed via API.

## Code Security

### Strengths:
1. ✅ **Clean Authentication Flow**: Well-structured authentication flow.
2. ✅ **Secure Token Handling**: Proper token handling in front-end code.

### Vulnerabilities:
1. ❌ **Missing Input Sanitization**: Calendar iframe and HTML content might need additional sanitization.
2. ❌ **JWT and Knox Together**: Using both JWT and Knox authentication may lead to confusion or unintended authentication paths.

## Recommendations:

1. **Immediate Fixes:**
   - Replace hardcoded secret keys and default TOTP keys
   - Configure proper database for production (PostgreSQL)
   - Encrypt sensitive fields (CC numbers, personal information)
   - Sanitize all user inputs, especially HTML/iframe content

2. **Short-term Improvements:**
   - Implement field-level data encryption for PII
   - Tighten authorization rules in viewsets
   - Set specific CORS origins
   - Implement proper file upload validations and scanning

3. **Long-term Enhancements:**
   - Implement audit logging
   - Consider adding multi-factor authentication
   - Conduct regular penetration testing
   - Implement a secure secret management solution
   - Add intrusion detection and suspicious activity monitoring
