# Backend Instructions for Biometric Authentication

This document provides instructions for implementing the backend support needed for the biometric authentication feature in the Aprende Conmigo application. The frontend has been updated to support biometric authentication, but the backend needs to implement a specific endpoint to complete the feature.

## Overview

The mobile application now supports biometric authentication (Face ID, Touch ID, and Fingerprint scanning) as an alternative to the traditional email verification code flow. This feature improves user experience by allowing faster logins without requiring users to check their email for codes each time.

## How Biometric Authentication Works

1. **User Registration/Enrollment:**
   - Users first authenticate using the regular email code verification process
   - After successful authentication, users can opt-in to enable biometric login
   - The app securely associates the user's email with the device's biometric capabilities
   - The biometric data itself NEVER leaves the user's device

2. **Biometric Login Flow:**
   - When a user attempts to log in with biometrics, the app:
     1. Validates the biometric data on the device (using OS security features)
     2. Retrieves the associated email address from secure device storage
     3. Calls the backend to authenticate without requiring a code

## Required Backend Implementation

### 1. New Endpoint: Biometric Authentication

Create a new endpoint that accepts an email and provides an authentication token:

```
POST /auth/biometric-verify/
```

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Response (Success - 200 OK):**
```json
{
  "token": "auth_token_here",
  "expiry": "2023-05-01T12:00:00Z",
  "user": {
    "id": 123,
    "email": "user@example.com",
    "name": "User Name",
    "phone_number": "+123456789",
    "user_type": "student",
    "is_admin": false,
    "created_at": "2023-01-01T00:00:00Z",
    "updated_at": "2023-01-01T00:00:00Z"
  }
}
```

**Response (Error - 401 Unauthorized):**
```json
{
  "error": "User not found or biometric authentication not allowed"
}
```

### 2. Security Considerations

- **Rate Limiting**: Implement rate limiting on the biometric verification endpoint to prevent brute force attacks
- **Suspicious Activity Detection**: Monitor for unusual login patterns that might indicate abuse
- **Token Security**: Ensure tokens have appropriate expiration times and are properly signed
- **Email Validation**: Verify that the email exists in your system before issuing a token

### 3. Implementation Guidelines

1. **Validation Layer**:
   - Validate the incoming email format and existence in your database
   - Check if the user has completed email verification at least once

2. **Authorization Logic**:
   - Generate the same type of authentication token you use for regular sign-ins
   - Include the same user information in the response

3. **Logging**:
   - Implement proper logging for biometric authentication attempts
   - Track success/failure rates for analysis and security monitoring

4. **Error Handling**:
   - Return clear error messages with appropriate HTTP status codes
   - Implement consistent error format across all authentication endpoints

### 4. Testing Recommendations

1. Test the endpoint with:
   - Valid emails of existing users
   - Invalid or non-existent emails
   - Malformed requests

2. Verify that:
   - Tokens generated via biometric verification have the same capabilities as regular tokens
   - Rate limiting properly prevents excessive authentication attempts
   - Logs properly capture biometric authentication events

## Important Notes

1. The frontend handles all biometric data collection and validation using the device's secure hardware - the backend never receives or processes actual biometric data.

2. This is a "trusted device" approach - the backend is trusting that if the frontend sends a biometric verification request with an email, the user has already authenticated using the device's secure biometric system.

3. Consider implementing additional security measures such as device fingerprinting or requiring periodic re-authentication with email codes (e.g., every 30 days) even for biometric users.

4. For additional security, you could require the frontend to send a signed timestamp or other proof that biometric verification actually occurred on the device, though this is an advanced feature that can be implemented in a future iteration.

## Example Implementation (Pseudocode)

```python
@app.route('/auth/biometric-verify/', methods=['POST'])
def biometric_verify():
    # Get request data
    data = request.json
    email = data.get('email')

    # Validate email
    if not email or not is_valid_email(email):
        return jsonify({'error': 'Invalid email format'}), 400

    # Rate limiting check
    if is_rate_limited(email):
        return jsonify({'error': 'Too many attempts, please try again later'}), 429

    # Find user
    user = find_user_by_email(email)
    if not user:
        # Use a generic error message for security
        return jsonify({'error': 'Authentication failed'}), 401

    # Optional: Check if user has completed email verification before
    if not user.has_completed_email_verification:
        return jsonify({'error': 'Email verification required before using biometric login'}), 401

    # Generate auth token (same as your regular authentication)
    token = generate_auth_token(user)

    # Log the successful biometric authentication
    log_authentication_event(user.id, 'biometric', success=True)

    # Return the same response format as regular authentication
    return jsonify({
        'token': token,
        'expiry': calculate_expiry_time(),
        'user': user.to_dict()
    }), 200
```

## Contact Information

If you have any questions about implementing this endpoint or need technical assistance, please contact the frontend development team.
