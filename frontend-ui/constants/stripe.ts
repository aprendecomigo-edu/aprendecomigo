/**
 * Stripe configuration for frontend integration.
 * 
 * This file manages Stripe public keys and provides utilities for
 * initializing Stripe on the frontend with environment-specific configuration.
 */

import { ENVIRONMENT } from './env';

// Stripe configuration for different environments
const stripeConfig = {
  development: {
    // Use test public keys for development
    PUBLIC_KEY: process.env.EXPO_PUBLIC_STRIPE_PUBLIC_KEY || '',
    // Additional development-specific configuration
    CLIENT_ID: process.env.EXPO_PUBLIC_STRIPE_CLIENT_ID || '',
  },
  staging: {
    // Use test public keys for staging
    PUBLIC_KEY: process.env.EXPO_PUBLIC_STRIPE_PUBLIC_KEY || '',
    CLIENT_ID: process.env.EXPO_PUBLIC_STRIPE_CLIENT_ID || '',
  },
  production: {
    // Use live public keys for production
    PUBLIC_KEY: process.env.EXPO_PUBLIC_STRIPE_PUBLIC_KEY || '',
    CLIENT_ID: process.env.EXPO_PUBLIC_STRIPE_CLIENT_ID || '',
  },
};

// Select the appropriate configuration
const activeStripeConfig = stripeConfig[ENVIRONMENT] || stripeConfig.development;

// Export Stripe configuration
export const STRIPE_PUBLIC_KEY = activeStripeConfig.PUBLIC_KEY;
export const STRIPE_CLIENT_ID = activeStripeConfig.CLIENT_ID;

/**
 * Validate Stripe configuration.
 * 
 * Ensures that the required Stripe keys are present and valid
 * for the current environment.
 * 
 * @returns Object with validation status and any errors
 */
export const validateStripeConfig = () => {
  const errors: string[] = [];
  
  // Check if public key is present
  if (!STRIPE_PUBLIC_KEY) {
    errors.push('Missing Stripe public key (EXPO_PUBLIC_STRIPE_PUBLIC_KEY)');
  }
  
  // Validate key format based on environment
  if (STRIPE_PUBLIC_KEY) {
    const isTestKey = STRIPE_PUBLIC_KEY.startsWith('pk_test_');
    const isLiveKey = STRIPE_PUBLIC_KEY.startsWith('pk_live_');
    
    if (!isTestKey && !isLiveKey) {
      errors.push('Invalid Stripe public key format');
    }
    
    // Environment-specific validation
    if (ENVIRONMENT === 'development' && !isTestKey) {
      errors.push('Development environment should use test keys (pk_test_*)');
    }
    
    if (ENVIRONMENT === 'production' && !isLiveKey) {
      errors.push('Production environment should use live keys (pk_live_*)');
    }
  }
  
  return {
    isValid: errors.length === 0,
    errors,
    config: {
      environment: ENVIRONMENT,
      publicKey: STRIPE_PUBLIC_KEY ? `${STRIPE_PUBLIC_KEY.substring(0, 12)}...` : 'not set',
      keyType: STRIPE_PUBLIC_KEY?.startsWith('pk_test_') ? 'test' : 
               STRIPE_PUBLIC_KEY?.startsWith('pk_live_') ? 'live' : 'unknown'
    }
  };
};

/**
 * Get Stripe configuration for frontend initialization.
 * 
 * Returns safe configuration that can be used to initialize
 * Stripe on the frontend.
 * 
 * @returns Object with Stripe configuration
 */
export const getStripeConfig = () => {
  const validation = validateStripeConfig();
  
  if (!validation.isValid) {
    console.warn('Stripe configuration validation failed:', validation.errors);
  }
  
  return {
    publicKey: STRIPE_PUBLIC_KEY,
    clientId: STRIPE_CLIENT_ID,
    environment: ENVIRONMENT,
    isConfigured: validation.isValid,
    validation
  };
};

/**
 * Stripe service configuration for API calls.
 * 
 * This configuration is used by API services to interact
 * with the backend Stripe endpoints.
 */
export const STRIPE_API_CONFIG = {
  endpoints: {
    config: '/api/finances/api/stripe/config/',
    testConnection: '/api/finances/api/stripe/test-connection/',
  },
  // Headers for Stripe-related API calls
  headers: {
    'Content-Type': 'application/json',
  },
};

// Debug information (only in development)
if (__DEV__) {
  const config = getStripeConfig();
  console.log('Stripe Configuration:', {
    environment: config.environment,
    publicKey: config.publicKey ? `${config.publicKey.substring(0, 12)}...` : 'not set',
    isConfigured: config.isConfigured,
    keyType: config.validation.config.keyType
  });
  
  if (!config.isConfigured) {
    console.warn('Stripe configuration issues:', config.validation.errors);
  }
}