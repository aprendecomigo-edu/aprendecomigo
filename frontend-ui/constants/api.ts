// API URL configuration for different environments
import Constants from 'expo-constants';
import { Platform } from 'react-native';

// Default environment is development
const ENV = Constants.expoConfig?.extra?.env || 'development';

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
    API_URL: 'https://staging-api.aprendecomigo.com/api',
  },
  production: {
    API_URL: 'https://api.aprendecomigo.com/api',
  },
};

// Allow overriding from physical device testing
// Uncomment and modify this line for testing on physical devices
// config.development.API_URL = 'http://192.168.1.X:8000/api'; // Replace X with your IP

// Select the appropriate configuration
const activeConfig = config[ENV as keyof typeof config] || config.development;

// Export the API URL
export const API_URL = activeConfig.API_URL;

// Debug information
if (__DEV__) {
  console.log(`Environment: ${ENV}`);
  console.log(`API URL: ${API_URL}`);
}
