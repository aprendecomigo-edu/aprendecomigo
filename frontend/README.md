# Aprende Conmigo Frontend

React Native app with Gluestack UI components for web, iOS, and Android.

## Dependency Notes

### React 19 + Expo SDK 53 Compatibility

This project uses React 19 with Expo SDK 53. Due to react-refresh v0.14.2 incompatibility with React 19's module structure:

- **Mobile Development**: Full hot reload support (unchanged workflow)
- **Web Development**: Production-only builds (~60s build cycle, no hot reload)
- **Workaround**: Uses production builds for web development while maintaining full mobile experience

Key changes:
- Environment-safe `__DEV__` detection with `utils/env.ts`
- Updated to Gluestack UI v2 patterns (removed obsolete `createIcon`)
- React Native SVG v15.12.1 for React Native Web compatibility

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

### Mobile Development (React 19 + Hot Reload)
- `npm run dev` - Start mobile development with hot reload (iOS + Android)
- `npx expo start --ios` - iOS only
- `npx expo start --android` - Android only

### Web Development (React 19 Compatible - Production Builds Only)
- `npm run build:web` - Build web app for development
- `npm run preview:web` - Serve built web app at http://localhost:3000
- `npm run build:web && npm run preview:web` - Complete web workflow

### Testing
- `npm test` - Run tests
- `npm run test:watch` - Run tests in watch mode

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

### Mobile Development (Full React 19 Support)
- `npm run dev` - Start mobile development with hot reload (recommended)
- `npm run start` - Start Expo development server (all platforms)

### Web Development (React 19 Compatible)
- `npm run web` - Shows web development instructions (react-refresh incompatible)
- `npm run build:web` - Build web application for development
- `npm run preview:web` - Serve built web app locally

### Development Workflow
- **Mobile**: Use `npm run dev` for hot reload development
- **Web**: Use `npm run build:web && npm run preview:web` (~60s build cycle)

### Other Scripts
- `npm test` - Run tests
- `npm run lint` - Run ESLint
- `npm run typecheck` - Run TypeScript checking

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
