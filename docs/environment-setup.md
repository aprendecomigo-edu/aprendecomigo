# Environment Setup

This document explains how to configure different environments for the Aprende Conmigo app.

## Environment Variables

The app uses different API URLs depending on the environment:

- **Development**: Default for local development
  - iOS simulator: `http://localhost:8000/api`
  - Android emulator: `http://10.0.2.2:8000/api`

- **Staging**: `https://staging-api.aprendecomigo.com/api`

- **Production**: `https://api.aprendecomigo.com/api`

## Setting Up the Environment

### During Development

By default, the app runs in development mode. No additional configuration is needed.

For testing on physical devices, modify the `config.development.API_URL` line in `frontend-ui/constants/api.ts`.

### Building for Different Environments

To build the app for a specific environment, use the `APP_ENV` environment variable:

```bash
# For development build
APP_ENV=development expo build:android

# For staging build
APP_ENV=staging expo build:android

# For production build
APP_ENV=production expo build:android
```

## Troubleshooting

If you're experiencing issues with API connectivity:

1. Check that you're using the correct environment setting
2. For physical devices in development, make sure your device and computer are on the same network
3. Verify the API server is running and accessible

## Adding New Environments

To add a new environment:

1. Add a new entry to the `config` object in `frontend-ui/constants/api.ts`
2. Update this documentation to include the new environment
