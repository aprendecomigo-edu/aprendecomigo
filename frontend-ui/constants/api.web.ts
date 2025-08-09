import { ENVIRONMENT } from './env';

// Configuration for different environments on web platform
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

// Export the API URL
export const API_URL = activeConfig.API_URL;

// Debug information
if (__DEV__) {
  console.log(`API URL (Web): ${API_URL}`);
}
