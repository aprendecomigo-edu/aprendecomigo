/**
 * API URL configuration for different environments.
 *
 * This file automatically resolves to the appropriate platform-specific implementation:
 * - api.web.ts for web platforms
 * - api.native.ts for iOS/Android platforms
 */

import { ENVIRONMENT } from './env';

// Fallback configuration (should be overridden by platform-specific files)
const config = {
  development: {
    API_URL: 'http://localhost:8000/api',
  },
  staging: {
    API_URL: 'https://aprendecomigo.eu.pythonanywhere.com/api',
  },
  production: {
    API_URL: 'https://api.aprendecomigo.com/api',
  },
};

// Select the appropriate configuration
const activeConfig = config[ENVIRONMENT] || config.development;

// Export the API URL (will be overridden by platform-specific files)
export const API_URL = activeConfig.API_URL;

// Debug information
if (__DEV__) {
  console.log(`API URL (Fallback): ${API_URL}`);
}
