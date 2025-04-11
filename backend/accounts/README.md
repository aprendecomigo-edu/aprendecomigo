# Authentication System Documentation

## Overview

The authentication system for Aprende Comigo uses a passwordless approach with Time-based One-Time Password (TOTP) verification codes and Knox token-based authentication for session management.

## Key Components

### 1. Passwordless Authentication Flow with TOTP

- User requests a verification code by submitting their email
- System generates a TOTP secret key and sends the current code to the user's email
- TOTP codes are time-synchronized and change every 30 seconds
- User verifies their identity by entering the correct code
- Upon successful verification, a Knox token is issued for continued authentication

### 2. Knox Token Authentication

- Server-side token storage for improved security
- Token revocation capabilities (logout and logoutall endpoints)
- Support for multiple devices per user (each with its own token)
- Configurable token expiration (currently set to 10 hours)

### 3. Security Enhancements

- **Time-based One-Time Passwords**: Much more secure than static codes
- **Secure Token Storage**: Using SecureStore on the frontend with AsyncStorage fallback
- **Rate Limiting**:
  - 5 code requests per hour per IP
  - 10 verification attempts per hour per IP
- **Brute Force Protection**: Max 5 failed verification attempts before requiring a new code
- **Failed Attempt Tracking**: Monitoring and limiting invalid verification attempts
- **Consistent Authentication**: Base classes for all authenticated views and viewsets

## API Endpoints

- `POST /api/auth/request-code/`: Request a TOTP verification code
- `POST /api/auth/verify-code/`: Verify the TOTP code and get authentication token
- `POST /api/auth/logout/`: Invalidate the current token
- `POST /api/auth/logoutall/`: Invalidate all tokens for the user
- `GET/PUT /api/auth/profile/`: Get or update user profile

## TOTP Implementation Details

### Backend

- **Secret Key Generation**: Uses `pyotp` library to generate secure random base32 keys
- **Code Verification**: Validates TOTP codes against the stored secret
- **Code Expiry**: TOTP codes change every 30 seconds, reducing the window for attacks
- **QR Code Support**: Provisioning URIs are provided for authenticator app integration
- **Progressive Enhancement**: Fallback to email delivery for users without authenticator apps

### Email Delivery

Instead of requiring an authenticator app, the system sends the current TOTP code via email, providing:
- Enhanced security over static codes
- Familiar user experience (still using email verification)
- No need to install additional apps

### API Response Format

When requesting a verification code, the API response includes:
```json
{
  "message": "Verification code sent to your email",
  "secret": "BASE32_SECRET_KEY",
  "provisioning_uri": "otpauth://totp/test@example.com?secret=BASE32_SECRET_KEY&issuer=Aprende%20Comigo"
}
```

- The `secret` can be used by developers to generate valid codes during testing
- The `provisioning_uri` can be converted to a QR code for authenticator apps

## Implementation Details

### Frontend

- Token is stored securely using expo-secure-store when available
- API requests include the token in the Authorization header
- Automatic token handling in the API client

### Backend

- Django REST Framework with Knox authentication
- TOTP verification system with security limits
- Custom throttling classes for rate limiting
- Base classes for authenticated views:
  - `KnoxAuthenticatedAPIView`: Base class for simple API views
  - `KnoxAuthenticatedViewSet`: Base class for model viewsets

### Authentication Protection

All endpoints (except for the authentication endpoints) are protected with Knox authentication:

- Unauthenticated requests receive a 401 Unauthorized response
- Invalid tokens (expired, malformed, or tampered) are rejected
- Each user can only access their own resources
- Token expiration is enforced to mitigate token theft
- Comprehensive tests verify authentication behavior in all cases

## How to Create Secure Views

### 1. Using Base Classes

Always extend the provided base classes for new views or viewsets:

```python
# For simple API views
class MySecureAPIView(KnoxAuthenticatedAPIView):
    def get(self, request):
        # Your logic here - authentication is already handled
        return Response({"data": "Secure data"})

# For model-based views
class MyModelViewSet(KnoxAuthenticatedViewSet):
    serializer_class = MyModelSerializer

    def get_queryset(self):
        # Restrict queryset to user's data
        return MyModel.objects.filter(user=self.request.user)
```

### 2. Creating Authentication Views

For views that handle authentication (like login):

```python
class MyAuthenticationView(APIView):
    # No authentication required for login views
    authentication_classes = []
    permission_classes = [AllowAny]

    # Consider adding rate limiting
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        # Authentication logic
        # ...

        # On success, create a Knox token
        token_instance, token = AuthToken.objects.create(user, token_ttl)
        return Response({"token": token})
```

### 3. Security Best Practices

When creating new views:

1. **Protect All Non-Authentication Endpoints**: Use the base classes for all views except those explicitly handling authentication
2. **Implement Proper Authorization**: Always check that users can only access their own data
3. **Add Rate Limiting**: Apply throttling to sensitive endpoints
4. **Handle Failures Gracefully**: Don't reveal sensitive information in error messages
5. **Test Authentication Logic**: Write tests to verify authentication behavior

### 4. Running Authentication Tests

Run the authentication tests to verify your endpoints are secure:

```bash
python manage.py test accounts.tests.test_auth_protection
```
