# Environment Setup for Frontend

This document explains how to set up and use different environments (development, staging, production) for the frontend application.

## Available Environments

- **Development**: Local development environment, connecting to localhost or emulator-specific URLs
- **Staging**: Testing environment with staging API endpoints
- **Production**: Live production environment with production API endpoints

## Environment Configuration

Environment settings are managed through:

1. Environment variables (`EXPO_PUBLIC_ENV`)
2. Configuration in `app.json` (fallback)
3. Default to 'development' if none specified

## Running the App in Different Environments

### Development Environment

```bash
# Start the development server
npm run start:dev

# Or manually:
EXPO_PUBLIC_ENV=development npx expo start
```

### Staging Environment

```bash
# Start with staging configuration
npm run start:staging

# Or manually:
EXPO_PUBLIC_ENV=staging npx expo start
```

### Production Environment

```bash
# Start with production configuration
npm run start:prod

# Or manually:
EXPO_PUBLIC_ENV=production npx expo start
```

## Building Web for Different Environments

```bash
# Build for development
npm run build:web:dev

# Build for staging
npm run build:web:staging

# Build for production
npm run build:web:prod
```

## Deployment

### Web Deployment

For web deployment, you should build the application with the appropriate environment:

```bash
# Build web app for production
npm run build:web:prod
```

Then deploy the generated files from the `dist` directory to your web hosting platform.

### GitHub Automated Deployments

The repository is configured with GitHub Actions workflows to automatically deploy to different environments:

#### Staging Deployment
- Triggered when code is pushed to the `develop` branch
- Builds the web app with staging environment configuration
- Deploys to the staging Netlify site
- Can also be manually triggered through GitHub Actions interface

#### Production Deployment
- Triggered when code is pushed to the `main` branch
- Builds the web app with production environment configuration
- Deploys to the production Netlify site
- Can also be manually triggered through GitHub Actions interface

Required GitHub Secrets:
- `NETLIFY_AUTH_TOKEN`: Your Netlify authentication token
- `NETLIFY_STAGING_SITE_ID`: ID of your staging Netlify site
- `NETLIFY_PROD_SITE_ID`: ID of your production Netlify site

### Native App Deployment with EAS

For native app deployment using EAS (Expo Application Services):

```bash
# Configure app.json with the right environment first
# Build for production
eas build --platform all --profile production
```

## Adding New Environment Variables

To add new environment-specific variables:

1. Add them to the configuration in `constants/env.ts` and `constants/api.ts`
2. Export variables from appropriate files
3. Import and use them in your components/screens

## Troubleshooting

- If you're testing on a physical device, you may need to update the API URL in `constants/api.ts` to point to your local machine's IP address
- Ensure that the correct environment is set before building for deployment
- Check the console logs to verify the active environment and API URL
