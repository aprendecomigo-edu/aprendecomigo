/**
 * Business Service Types and Interfaces
 *
 * This file defines the interfaces for business logic services
 * that handle payment processing, balance calculations, and other domain logic.
 */

import type { TopUpPackage, PaymentMethod, QuickTopUpRequest, PackageInfo } from '@/types/purchase';

// ==================== Payment Service Types ====================

export interface PaymentCalculationResult {
  totalPrice: number;
  pricePerHour: number;
  originalPrice: number;
  discountAmount: number;
  discountPercentage: number;
  hasDiscount: boolean;
}

export interface PaymentMethodValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
  canProcess: boolean;
}

export interface PaymentServiceInterface {
  /**
   * Process quick top-up purchase request
   * @param packageId The package ID to purchase
   * @param paymentMethodId The payment method ID (null for default)
   * @param email Optional email for admin access
   */
  processQuickTopUp(
    packageId: number,
    paymentMethodId: string | null,
    email?: string | null
  ): Promise<QuickTopUpRequest>;

  /**
   * Calculate package pricing with discounts
   * @param pkg The top-up package
   */
  calculatePackagePrice(pkg: TopUpPackage): PaymentCalculationResult;

  /**
   * Validate payment method for processing
   * @param method The payment method to validate
   */
  validatePaymentMethod(method: PaymentMethod): PaymentMethodValidationResult;
}

// ==================== Balance Service Types ====================

export interface PackageBreakdown {
  transactionId: number;
  planName: string;
  remainingHours: number;
  percentageRemaining: number;
}

export interface RemainingHoursCalculation {
  totalRemainingHours: number;
  totalPurchasedHours: number;
  totalConsumedHours: number;
  packageBreakdown: PackageBreakdown[];
}

export interface BalanceStatusLevel {
  level: 'critical' | 'low' | 'medium' | 'healthy';
  color: string;
  bgColor: string;
  progressColor: string;
  icon: string;
  message: string;
  urgency: 'urgent' | 'warning' | 'info' | 'success';
  percentage: number;
  recommendedAction: 'immediate_purchase' | 'plan_purchase' | 'monitor' | 'none';
}

export interface ConsumptionRecord {
  date: string;
  hoursConsumed: number;
}

export interface ExpiryPrediction {
  estimatedExpiryDate: Date | null;
  daysUntilExpiry: number | null;
  weeklyConsumptionRate: number;
  monthlyConsumptionRate: number;
  confidence: 'high' | 'medium' | 'low';
  reasoning: string;
}

export interface BalanceServiceInterface {
  /**
   * Calculate remaining hours from purchase packages
   * @param packages Array of active packages
   */
  calculateRemainingHours(packages: PackageInfo[]): RemainingHoursCalculation;

  /**
   * Determine balance status level based on remaining hours
   * @param remainingHours Current remaining hours
   * @param totalHours Total purchased hours
   */
  getBalanceStatus(remainingHours: number, totalHours: number): BalanceStatusLevel;

  /**
   * Predict when balance will be exhausted based on usage patterns
   * @param balance Current balance calculation
   * @param consumptionHistory Historical consumption data
   */
  predictExpiryDate(
    balance: RemainingHoursCalculation,
    consumptionHistory: ConsumptionRecord[]
  ): ExpiryPrediction;
}

// ==================== Service Dependencies ====================

export interface BusinessServices {
  paymentService: PaymentServiceInterface;
  balanceService: BalanceServiceInterface;
}

// ==================== Extended Dependencies Interface ====================

declare module '@/services/di/types' {
  interface Dependencies {
    paymentService: PaymentServiceInterface;
    balanceService: BalanceServiceInterface;
  }
}
