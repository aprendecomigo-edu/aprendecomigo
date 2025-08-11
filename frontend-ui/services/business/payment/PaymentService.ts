/**
 * PaymentService - Business Logic for Payment Processing
 * 
 * This service handles all payment-related business logic including
 * package pricing calculations, payment method validation, and quick top-up processing.
 * 
 * Pure functions with no UI dependencies - suitable for testing and business logic isolation.
 */

import type {
  TopUpPackage,
  PaymentMethod,
  QuickTopUpRequest,
} from '@/types/purchase';
import type {
  PaymentCalculationResult,
  PaymentMethodValidationResult,
  PaymentServiceInterface,
} from '../types';

export class PaymentService implements PaymentServiceInterface {
  /**
   * Process quick top-up purchase request
   * @param packageId The package ID to purchase
   * @param paymentMethodId The payment method ID (null for default)
   * @param email Optional email for admin access
   */
  async processQuickTopUp(
    packageId: number,
    paymentMethodId: string | null,
    email?: string | null
  ): Promise<QuickTopUpRequest> {
    // Validate inputs
    if (!packageId || packageId <= 0) {
      throw new Error('Package ID is required');
    }

    if (!paymentMethodId && !email) {
      throw new Error('Either payment method ID or use default payment method must be specified');
    }

    // Create the request object based on whether we have a specific payment method
    const request: QuickTopUpRequest = {
      package_id: packageId,
      confirm_immediately: true,
    };

    if (paymentMethodId) {
      request.payment_method_id = paymentMethodId;
      request.use_default_payment_method = false;
    } else {
      request.use_default_payment_method = true;
    }

    return request;
  }

  /**
   * Calculate package pricing with discounts
   * @param pkg The top-up package
   */
  calculatePackagePrice(pkg: TopUpPackage): PaymentCalculationResult {
    const totalPrice = parseFloat(pkg.price_eur);
    const pricePerHour = parseFloat(pkg.price_per_hour);
    
    // Calculate original price if there's a discount
    const hasDiscount = (pkg.discount_percentage || 0) > 0;
    const discountPercentage = pkg.discount_percentage || 0;
    
    let originalPrice = totalPrice;
    let discountAmount = 0;
    
    if (hasDiscount && discountPercentage > 0) {
      // If there's a discount, calculate the original price
      // totalPrice = originalPrice * (1 - discountPercentage / 100)
      // Therefore: originalPrice = totalPrice / (1 - discountPercentage / 100)
      originalPrice = totalPrice / (1 - discountPercentage / 100);
      discountAmount = originalPrice - totalPrice;
    }

    return {
      totalPrice,
      pricePerHour,
      originalPrice,
      discountAmount,
      discountPercentage,
      hasDiscount,
    };
  }

  /**
   * Validate payment method for processing
   * @param method The payment method to validate
   */
  validatePaymentMethod(method: PaymentMethod): PaymentMethodValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];

    // Validate payment method ID
    if (!method.id || method.id.trim() === '') {
      errors.push('Invalid payment method ID');
    }

    // Validate card details
    if (!method.card.brand || !method.card.last4 || !method.card.exp_month || !method.card.exp_year) {
      errors.push('Incomplete card details');
    }

    // Check if card is expired
    const currentDate = new Date();
    const currentYear = currentDate.getFullYear();
    const currentMonth = currentDate.getMonth() + 1; // getMonth() returns 0-11

    const cardYear = method.card.exp_year;
    const cardMonth = method.card.exp_month;

    if (cardYear < currentYear || (cardYear === currentYear && cardMonth < currentMonth)) {
      errors.push('Payment method has expired');
    }

    // Check if card is expiring soon (within current month of current year)
    if (cardYear === currentYear && cardMonth === currentMonth) {
      warnings.push('Payment method expires soon');
    }

    // Check funding type
    if (method.card.funding === 'prepaid') {
      warnings.push('Prepaid card may have restrictions');
    }

    const isValid = errors.length === 0;
    const canProcess = isValid;

    return {
      isValid,
      errors,
      warnings,
      canProcess,
    };
  }
}