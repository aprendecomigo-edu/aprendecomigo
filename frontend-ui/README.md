# Aprende Conmigo Frontend

React Native app with Gluestack UI components for web, iOS, and Android.

## Dependency Notes

### Patched Dependencies

- **@gluestack-ui/checkbox**: Patched to support React 18 compatibility. The patch modifies the peer dependency requirements in the nested `@react-aria/checkbox` package to accept React 18.

### Installation

Always install dependencies with:

```bash
npm install --legacy-peer-deps
```

### Security Vulnerabilities

There are some known vulnerabilities in development packages that don't affect production code. These include:

- cross-spawn in pre-commit package
- got in npm-check package
- send in expo package

To update these packages would require breaking changes to the development workflow. Since they're only used during development, they pose minimal risk.

## Build Commands
- start: `npx expo start`
- android: `npx expo start --android`
- ios: `npx expo start --ios`
- web: `npx expo start --web`
- test: `jest --watchAll`

## Getting Started

### Prerequisites

- Node.js (v16+)
- Yarn or npm
- Expo CLI (`npm install -g expo-cli`)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/aprendecomigo-frontend.git
cd aprendecomigo-frontend

# Install dependencies
yarn install

# Start the development server
yarn start
```

## Available Scripts

- `yarn start` - Start the Expo development server
- `yarn android` - Start the app on an Android device/emulator
- `yarn ios` - Start the app on an iOS simulator
- `yarn web` - Start the app in a web browser
- `yarn test` - Run tests

## Authentication Flow

The application uses a passwordless authentication system designed to be user-friendly, especially for users who may not be tech-savvy.

### Basic Authentication Flow

1. **Request Code Flow**:
   - User enters their email on the sign-in screen
   - System sends a 6-digit verification code to the user's email
   - User enters the verification code to authenticate
   - On successful verification, the user is redirected to the dashboard

2. **Token Management**:
   - Authentication tokens are stored securely using Expo SecureStore
   - Tokens automatically migrate from AsyncStorage to SecureStore for backward compatibility
   - Token validation occurs on each app launch and API request

### Biometric Authentication

The application also supports biometric authentication for a faster and more convenient login experience:

1. **Enabling Biometric Authentication**:
   - After verifying email code, users can opt-in to enable biometric authentication
   - The system securely associates the user's email with biometric credentials on the device
   - Biometric data never leaves the device and is managed by the OS's secure enclave

2. **Biometric Login Flow**:
   - When biometric auth is enabled, users see a biometric login option
   - User authenticates with fingerprint, Face ID, or other biometric method
   - System validates the biometric data and automatically logs the user in
   - If biometric authentication fails, user can fall back to the code-based authentication

3. **Security Considerations**:
   - Biometric data is never stored on servers
   - Email associated with biometrics is stored securely in device storage
   - Biometric authentication can be disabled at any time from profile settings

### Authentication APIs

The application communicates with the following backend endpoints:

- `POST /auth/request-code/` - Request verification code (requires email)
- `POST /auth/verify-code/` - Verify the code and get auth token (requires email, code)
- `POST /auth/biometric-verify/` - Authenticate with biometrics (requires email)
- `GET /auth/profile/` - Get current user profile
- `POST /auth/logout/` - Invalidate the current session

## Project Structure

- `/api` - API clients and auth services
- `/app` - Expo Router file-based routing structure
- `/components` - Reusable UI components
- `/screens` - Screen components
- `/constants` - Application constants and configuration

## Testing

There are currently no automated tests for the frontend.
When tests are added, they will use Jest and React Native Testing Library.

## Contributing

Please refer to the CONTRIBUTING.md file for information on how to contribute to this project.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
