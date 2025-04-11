# Aprende Comigo Frontend

This is the React Native frontend for the Aprende Comigo platform, a school management system.

## Technology Stack

- React Native with Expo
- TypeScript
- React Navigation
- React Native Paper (UI components)
- Axios (for API requests)
- AsyncStorage (for local storage)

## Project Structure

```
/frontend
├── /assets            # Static assets like images, fonts
├── /src
│   ├── /api           # API service files
│   ├── /components    # Reusable UI components
│   │   └── /auth      # Authentication related components
│   ├── /constants     # Constants and configuration
│   ├── /context       # React Context providers
│   ├── /hooks         # Custom React hooks
│   ├── /navigation    # Navigation related files
│   ├── /screens       # Screen components
│   │   ├── /auth      # Authentication screens
│   │   └── /dashboard # Dashboard screens
│   ├── /types         # TypeScript type definitions
│   └── /utils         # Utility functions
├── App.tsx            # Main application component
├── app.json           # Expo configuration
└── package.json       # Project dependencies
```

## Authentication Flow

The app uses a passwordless authentication system:

1. User enters their email address
2. Backend sends a 6-digit code to the email
3. User enters the code to verify their identity
4. Backend returns JWT tokens (access and refresh)
5. App stores the tokens locally and uses them for API calls
6. Tokens are automatically refreshed using the refresh token when expired

## Authentication Details

### Passwordless Authentication System

The application implements a passwordless authentication flow that relies on email verification:

1. **Request Email Verification**
   - User enters email on login screen
   - Frontend calls `requestEmailCode(email)`
   - Backend generates a 6-digit code and saves it to database
   - Code is emailed to the user (valid for 10 minutes)

2. **Verify Email Code**
   - User enters the received 6-digit code
   - Frontend submits code to backend
   - Backend validates the code and generates JWT tokens

3. **Token Management**
   - Frontend stores tokens in AsyncStorage:
     ```typescript
     await AsyncStorage.setItem('access_token', response.data.access);
     await AsyncStorage.setItem('refresh_token', response.data.refresh);
     ```
   - Every API request includes the access token in the Authorization header
   - When access token expires, refresh token is used to obtain a new one

### JWT (JSON Web Tokens) Explained

JWT is a compact, self-contained way to securely transmit information between parties as a JSON object:

- **Structure**: JWTs consist of three parts separated by dots:
  - Header: Contains token type and signing algorithm
  - Payload: Contains claims (user data and metadata)
  - Signature: Ensures the token hasn't been altered

- **How It Works in Our App**:
  1. The backend signs tokens with a secret key
  2. The frontend includes the token in API requests
  3. The backend verifies the token signature and expiration
  4. If valid, the request is processed; if invalid, it's rejected

- **Token Types**:
  - **Access Token**: Short-lived (typically 5-15 minutes), used for API access
  - **Refresh Token**: Longer-lived (typically days/weeks), used to obtain new access tokens

### Security Considerations

1. **Token Storage**:
   - Tokens are stored in AsyncStorage, which isn't secure against malicious native code
   - For production apps with high-security requirements, consider more secure storage options like Keychain (iOS) or EncryptedSharedPreferences (Android)

2. **Token Security**:
   - Access tokens have short lifespans to minimize risk if compromised
   - Tokens should be transmitted over HTTPS only
   - Backend validates token integrity and expiration for every request

3. **Verification Code Security**:
   - Codes expire after 10 minutes
   - Codes are single-use only
   - Rate limiting should be implemented to prevent brute force attacks

4. **Attack Mitigation**:
   - Implement rate limiting on verification code requests
   - Monitor for unusual authentication patterns
   - Implement token revocation mechanisms for compromised accounts

5. **Additional Recommendations**:
   - For sensitive operations, consider requiring re-authentication
   - Implement proper CORS policies on the backend
   - Consider HTTP-only cookies for web environments if applicable

This passwordless system offers a streamlined user experience while maintaining strong security, avoiding the need to store passwords while still providing secure user authentication.

## Auth improvements
1. Token Storage on Mobile Client
Current Issue:
Tokens stored in AsyncStorage, which is not secure against malicious native code or rooted/jailbroken devices.
Recommendations:
Use secure storage options:
iOS: Keychain Services
Android: EncryptedSharedPreferences
Implement using expo-secure-store or react-native-keychain
```python
// Example with expo-secure-store
import * as SecureStore from 'expo-secure-store';

// Store
await SecureStore.setItemAsync('access_token', token);

// Retrieve
const token = await SecureStore.getItemAsync('access_token');

```

2. Token Authentication Implementation
Current Issue:
Using Simple JWT which is stateless - cannot revoke individual tokens without blacklisting
No implementation of token invalidation on logout
No token rotation for enhanced security
Recommendations:
Consider Django Rest Knox for improved token security:
Server-side token storage allows token invalidation
Per-client tokens (multiple devices)
Automatic token expiration
Token rotation capabilities

```python

# settings.py
INSTALLED_APPS = [
    # ...
    'knox',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'knox.auth.TokenAuthentication',
    ]
}

# Implementation for token creation in VerifyEmailCodeView
from knox.models import AuthToken

# In your view
token_instance, token = AuthToken.objects.create(user)
return Response({
    'user': UserSerializer(user).data,
    'token': token,
    'expiry': token_instance.expiry,
})
```

3. Rate Limiting and Brute Force Protection
Current Issue:
No evident rate limiting for verification code requests
Potential for brute force attacks against verification codes
Recommendations:
Implement rate limiting on verification endpoints
Add exponential backoff for multiple failed verification attempts
Log and monitor suspicious authentication attempts

```python
# settings.py
REST_FRAMEWORK = {
    # ...
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '5/minute',
        'auth_attempts': '3/minute',
    }
}

# In RequestEmailCodeView
from rest_framework.throttling import AnonRateThrottle

class EmailCodeRateThrottle(AnonRateThrottle):
    rate = '3/minute'
    scope = 'auth_attempts'

class RequestEmailCodeView(APIView):
    throttle_classes = [EmailCodeRateThrottle]
    # ...
```
4. Improve Email Verification Security
Current Issue:
6-digit numeric code (1 million possibilities, but brute-forceable)
No tracking of failed verification attempts
Recommendations:
Use longer alphanumeric codes or time-based one-time passwords (TOTP)
Track failed verification attempts and lock out after N failures
Consider implementing IP-based restrictions for suspicious activity
5. HTTPS Implementation
Current Issue:
Not explicitly enforced in the code (though likely configured at server level)
Recommendations:
Ensure HTTPS is enforced for all API endpoints
Implement HTTP Strict Transport Security (HSTS)
Consider certificate pinning for the mobile app
6. Cross-Site Request Forgery (CSRF) Protection
Current Issue:
CSRF protection not explicitly configured for API endpoints
Recommendations:
Ensure CSRF protection for browser contexts
Properly configure CORS for API access
Implementation Plan
Immediate Security Improvements:
Migrate from AsyncStorage to secure storage
Implement rate limiting for authentication endpoints
Add monitoring for suspicious authentication attempts
Medium-term Improvements:
Consider migrating from Simple JWT to Knox for better token management
Implement proper token invalidation on logout
Add brute force prevention for verification codes
Long-term Security Enhancements:
Consider multi-factor authentication for sensitive operations
Implement anomaly detection for authentication patterns
Add device fingerprinting to detect suspicious login attempts
By implementing these recommendations, you can significantly improve the security posture of your authentication system while maintaining the user-friendly passwordless authentication flow.


## Local Development

1. Install dependencies:
   ```
   npm install
   ```

2. Start the development server:
   ```
   npm start
   ```

3. Run on devices:
   - Press `i` to run on iOS simulator
   - Press `a` to run on Android emulator
   - Press `w` to run on web

## Backend Integration

The app connects to a Django REST Framework backend. The API URL is configured in `/src/constants/api.ts` and defaults to:
- Development: `http://localhost:8000/api`
- Production: `https://api.aprendecomigo.com/api`
