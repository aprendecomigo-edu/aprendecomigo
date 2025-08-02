/**
 * Stripe Payment Form - Native Implementation
 *
 * Native-specific implementation that shows platform not supported message
 * and directs users to the web version for payment processing.
 * Future enhancement: Could integrate with native payment sheets.
 */

import React from 'react';

import {
  StripePaymentFormProps,
  PlatformNotSupportedState,
} from './stripe-payment-common';

/**
 * Native payment form component - currently shows not supported message.
 * Future enhancement: Integrate with Apple Pay/Google Pay or native Stripe SDK.
 */
export function StripePaymentForm({
  className = '',
}: StripePaymentFormProps) {
  // For native platforms, show not supported message
  // Future enhancement: Implement native payment sheets integration
  return <PlatformNotSupportedState className={className} />;
}