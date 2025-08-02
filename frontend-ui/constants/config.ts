/**
 * Configuration file for frontend constants and settings.
 *
 * This file consolidates all configuration settings including API URLs,
 * Stripe configuration, and other environment-specific settings.
 */

// Re-export API configuration
export { API_URL } from './api';

// Re-export environment configuration
export { ENVIRONMENT } from './env';

// Re-export Stripe configuration
export {
  STRIPE_PUBLIC_KEY,
  STRIPE_CLIENT_ID,
  STRIPE_API_CONFIG,
  getStripeConfig,
  validateStripeConfig,
} from './stripe';

/**
 * General application configuration.
 */
export const APP_CONFIG = {
  name: 'Aprende Comigo',
  version: '1.0.0',

  // Features flags
  features: {
    stripeIntegration: true,
    webhookSupport: true,
    subscriptions: true,
    packages: true,
  },

  // UI Configuration
  ui: {
    defaultTheme: 'light',
    supportedLanguages: ['en', 'pt'],
    defaultLanguage: 'en',
  },

  // Payment configuration
  payment: {
    currency: 'EUR',
    defaultCurrency: 'EUR',
    supportedCurrencies: ['EUR', 'USD'],

    // Package configuration
    packages: {
      minHours: 1,
      maxHours: 100,
      defaultHours: 10,
    },

    // Subscription configuration
    subscriptions: {
      supportedPlans: ['basic', 'premium', 'enterprise'],
      defaultPlan: 'basic',
    },
  },

  // Security configuration
  security: {
    sessionTimeout: 24 * 60 * 60 * 1000, // 24 hours in milliseconds
    tokenRefreshInterval: 55 * 60 * 1000, // 55 minutes in milliseconds
  },
};

/**
 * Get complete application configuration.
 *
 * Returns a consolidated configuration object with all settings
 * including validation status and environment information.
 */
export const getAppConfig = () => {
  const stripeConfig = getStripeConfig();

  return {
    ...APP_CONFIG,
    environment: ENVIRONMENT,
    api: {
      baseUrl: API_URL,
    },
    stripe: stripeConfig,
    isProduction: ENVIRONMENT === 'production',
    isDevelopment: ENVIRONMENT === 'development',
    isStaging: ENVIRONMENT === 'staging',
  };
};
