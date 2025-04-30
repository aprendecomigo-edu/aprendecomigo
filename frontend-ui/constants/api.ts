// API URL configuration for different environments
import { Platform } from 'react-native';
import { ENVIRONMENT } from './env';

// Configuration for different environments
const config = {
  development: {
    // For emulators/simulators
    API_URL: Platform.select({
      ios: 'http://localhost:8000/api',
      android: 'http://10.0.2.2:8000/api', // Android emulator uses 10.0.2.2 to access host machine
      default: 'http://localhost:8000/api',
    }),
  },
  staging: {
    API_URL: 'https://aprendecomigo.eu.pythonanywhere.com/api',
  },
  production: {
    API_URL: 'https://api.aprendecomigo.com/api', // TODO: Add other production-specific endpoints here if needed
  },
};

// Allow overriding from physical device testing
// Uncomment and modify this line for testing on physical devices
// config.development.API_URL = 'http://192.168.1.X:8000/api'; // Replace X with your IP

// Select the appropriate configuration
const activeConfig = config[ENVIRONMENT] || config.development;

// Export the API URL
export const API_URL = activeConfig.API_URL;

// Debug information
if (__DEV__) {
  console.log(`API URL: ${API_URL}`);
}
