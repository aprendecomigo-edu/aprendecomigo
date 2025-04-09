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