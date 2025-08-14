/**
 * BalanceService - Business Logic for Balance Calculations
 *
 * This service handles all balance-related business logic including
 * remaining hours calculations, balance status determination, and expiry predictions.
 *
 * Pure functions with no UI dependencies - suitable for testing and business logic isolation.
 */

import type {
  RemainingHoursCalculation,
  PackageBreakdown,
  BalanceStatusLevel,
  ConsumptionRecord,
  ExpiryPrediction,
  BalanceServiceInterface,
} from '../types';

import type { PackageInfo } from '@/types/purchase';

export class BalanceService implements BalanceServiceInterface {
  /**
   * Calculate remaining hours from purchase packages
   * @param packages Array of active packages
   */
  calculateRemainingHours(packages: PackageInfo[]): RemainingHoursCalculation {
    if (packages.length === 0) {
      return {
        totalRemainingHours: 0,
        totalPurchasedHours: 0,
        totalConsumedHours: 0,
        packageBreakdown: [],
      };
    }

    let totalRemainingHours = 0;
    let totalPurchasedHours = 0;
    let totalConsumedHours = 0;
    const packageBreakdown: PackageBreakdown[] = [];

    for (const pkg of packages) {
      const hoursIncluded = parseFloat(pkg.hours_included);
      const hoursConsumed = parseFloat(pkg.hours_consumed);
      const hoursRemaining = parseFloat(pkg.hours_remaining);

      totalRemainingHours += hoursRemaining;
      totalPurchasedHours += hoursIncluded;
      totalConsumedHours += hoursConsumed;

      const percentageRemaining = hoursIncluded > 0 ? (hoursRemaining / hoursIncluded) * 100 : 0;

      packageBreakdown.push({
        transactionId: pkg.transaction_id,
        planName: pkg.plan_name,
        remainingHours: hoursRemaining,
        percentageRemaining: Math.round(percentageRemaining * 100) / 100, // Round to 2 decimal places
      });
    }

    return {
      totalRemainingHours,
      totalPurchasedHours,
      totalConsumedHours,
      packageBreakdown,
    };
  }

  /**
   * Determine balance status level based on remaining hours
   * @param remainingHours Current remaining hours
   * @param totalHours Total purchased hours
   */
  getBalanceStatus(remainingHours: number, totalHours: number): BalanceStatusLevel {
    const percentage = totalHours > 0 ? (remainingHours / totalHours) * 100 : 0;
    const roundedPercentage = Math.round(percentage * 100) / 100; // Round to 2 decimal places

    // Balance depleted
    if (remainingHours <= 0) {
      return {
        level: 'critical',
        color: 'text-error-700',
        bgColor: 'bg-error-50',
        progressColor: 'text-error-500',
        icon: 'AlertTriangle',
        message: 'Balance depleted',
        urgency: 'urgent',
        percentage: roundedPercentage,
        recommendedAction: 'immediate_purchase',
      };
    }

    // Critical balance: ≤2 hours or ≤10%
    if (remainingHours <= 2 || percentage <= 10) {
      return {
        level: 'critical',
        color: 'text-error-700',
        bgColor: 'bg-error-50',
        progressColor: 'text-error-500',
        icon: 'AlertTriangle',
        message: 'Critical balance',
        urgency: 'urgent',
        percentage: roundedPercentage,
        recommendedAction: 'immediate_purchase',
      };
    }

    // Low balance: ≤5 hours or ≤25%
    if (remainingHours <= 5 || percentage <= 25) {
      return {
        level: 'low',
        color: 'text-warning-700',
        bgColor: 'bg-warning-50',
        progressColor: 'text-warning-500',
        icon: 'Clock',
        message: 'Low balance',
        urgency: 'warning',
        percentage: roundedPercentage,
        recommendedAction: 'plan_purchase',
      };
    }

    // Medium balance: ≤50%
    if (percentage <= 50) {
      return {
        level: 'medium',
        color: 'text-primary-700',
        bgColor: 'bg-primary-50',
        progressColor: 'text-primary-500',
        icon: 'TrendingUp',
        message: 'Moderate balance',
        urgency: 'info',
        percentage: roundedPercentage,
        recommendedAction: 'monitor',
      };
    }

    // Healthy balance: >50%
    return {
      level: 'healthy',
      color: 'text-success-700',
      bgColor: 'bg-success-50',
      progressColor: 'text-success-500',
      icon: 'CheckCircle',
      message: 'Healthy balance',
      urgency: 'success',
      percentage: roundedPercentage,
      recommendedAction: 'none',
    };
  }

  /**
   * Predict when balance will be exhausted based on usage patterns
   * @param balance Current balance calculation
   * @param consumptionHistory Historical consumption data
   */
  predictExpiryDate(
    balance: RemainingHoursCalculation,
    consumptionHistory: ConsumptionRecord[]
  ): ExpiryPrediction {
    // Handle case with no consumption history
    if (consumptionHistory.length === 0) {
      return {
        estimatedExpiryDate: null,
        daysUntilExpiry: null,
        weeklyConsumptionRate: 0,
        monthlyConsumptionRate: 0,
        confidence: 'low',
        reasoning: 'no consumption history available',
      };
    }

    // Handle insufficient data
    if (consumptionHistory.length < 3) {
      const dailyAverage =
        consumptionHistory.reduce((sum, record) => sum + record.hoursConsumed, 0) /
        consumptionHistory.length;
      const weeklyRate = dailyAverage * 7;
      const monthlyRate = dailyAverage * 30;
      const daysUntilExpiry =
        dailyAverage > 0 ? Math.ceil(balance.totalRemainingHours / dailyAverage) : null;
      const estimatedExpiryDate = daysUntilExpiry
        ? new Date(Date.now() + daysUntilExpiry * 24 * 60 * 60 * 1000)
        : null;

      return {
        estimatedExpiryDate,
        daysUntilExpiry,
        weeklyConsumptionRate: weeklyRate,
        monthlyConsumptionRate: monthlyRate,
        confidence: 'low',
        reasoning: 'insufficient data for accurate prediction',
      };
    }

    // Calculate consumption rates
    const totalHoursConsumed = consumptionHistory.reduce(
      (sum, record) => sum + record.hoursConsumed,
      0
    );
    const averageDailyConsumption = totalHoursConsumed / consumptionHistory.length;
    const weeklyConsumptionRate = averageDailyConsumption * 7;
    const monthlyConsumptionRate = averageDailyConsumption * 30;

    // Calculate variance to determine consistency
    const variance =
      consumptionHistory.reduce((sum, record) => {
        const diff = record.hoursConsumed - averageDailyConsumption;
        return sum + diff * diff;
      }, 0) / consumptionHistory.length;

    const standardDeviation = Math.sqrt(variance);
    const coefficientOfVariation =
      averageDailyConsumption > 0 ? standardDeviation / averageDailyConsumption : 0;

    // Determine confidence level based on data quality and consistency
    let confidence: 'high' | 'medium' | 'low';
    let reasoning: string;

    if (consumptionHistory.length >= 14 && coefficientOfVariation < 0.3) {
      confidence = 'high';
      reasoning = 'consistent usage pattern with sufficient data';
    } else if (consumptionHistory.length >= 7) {
      confidence = 'medium';
      reasoning =
        coefficientOfVariation >= 0.6 ? 'irregular usage pattern' : 'moderate data available';
    } else {
      confidence = 'low';
      reasoning = 'limited data available';
    }

    // Calculate predicted expiry date
    let daysUntilExpiry: number | null = null;
    let estimatedExpiryDate: Date | null = null;

    if (averageDailyConsumption > 0) {
      daysUntilExpiry = Math.ceil(balance.totalRemainingHours / averageDailyConsumption);
      estimatedExpiryDate = new Date(Date.now() + daysUntilExpiry * 24 * 60 * 60 * 1000);
    }

    return {
      estimatedExpiryDate,
      daysUntilExpiry,
      weeklyConsumptionRate: Math.round(weeklyConsumptionRate * 100) / 100,
      monthlyConsumptionRate: Math.round(monthlyConsumptionRate * 100) / 100,
      confidence,
      reasoning,
    };
  }
}
