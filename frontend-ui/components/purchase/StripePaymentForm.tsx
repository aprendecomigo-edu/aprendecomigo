/**
 * Stripe Payment Form Component - Fallback Implementation
 *
 * Main entry point with Platform.OS fallback.
 * Platform-specific files should override this implementation.
 */

import React from 'react';
import { Platform } from 'react-native';

import {
  StripePaymentFormProps,
  PlatformNotSupportedState,
  LoadingState,
} from './stripe-payment-common';

// Export types for external usage
export type { StripePaymentFormProps };

/**
 * Fallback Stripe payment form wrapper component.
 * Platform-specific implementations should override this.
 */
export function StripePaymentForm({
  className = '',
}: StripePaymentFormProps) {
  // Fallback implementation
  if (Platform.OS === 'web') {
    return <LoadingState className={className} />;
  }

  return <PlatformNotSupportedState className={className} />;
}
