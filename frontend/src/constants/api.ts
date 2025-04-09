/**
 * API constants for different environments
 */

// Development environment - local backend
export const DEV_API_URL = 'http://localhost:8000/api';

// Production environment - deployed backend
export const PROD_API_URL = 'https://api.aprendecomigo.com/api';

// Current API URL based on environment
export const API_URL = __DEV__ ? DEV_API_URL : PROD_API_URL; 