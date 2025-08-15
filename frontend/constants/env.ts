import Constants from 'expo-constants';

// Environment types
export type Environment = 'development' | 'staging' | 'production';

// Get current environment from process.env or Constants
export const getEnvironment = (): Environment => {
  const env = process.env.EXPO_PUBLIC_ENV || Constants.expoConfig?.extra?.env || 'development';
  return env as Environment;
};

// Current environment
export const ENVIRONMENT = getEnvironment();

// Is this a development environment?
export const isDevelopment = ENVIRONMENT === 'development';

// Is this a production environment?
export const isProduction = ENVIRONMENT === 'production';

// Is this a staging environment?
export const isStaging = ENVIRONMENT === 'staging';

// Debug info in development
if (__DEV__) {
  if (__DEV__) {
    console.log(`App Environment: ${ENVIRONMENT}`);
  }
}
