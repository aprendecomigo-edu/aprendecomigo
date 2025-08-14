/**
 * Business Service Factory
 *
 * Factory function to create business service instances with their dependencies.
 * This provides a centralized way to instantiate business logic services.
 */

import { BalanceService } from './balance/BalanceService';
import { PaymentService } from './payment/PaymentService';
import type { BusinessServices } from './types';

/**
 * Create business services with dependency injection
 */
export function createBusinessServices(): BusinessServices {
  return {
    paymentService: new PaymentService(),
    balanceService: new BalanceService(),
  };
}
