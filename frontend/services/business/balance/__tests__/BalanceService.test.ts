/**
 * BalanceService Tests - TDD RED STATE
 *
 * These tests define the expected behavior for balance calculation business logic
 * extraction from UI components. They will initially fail until the BalanceService is implemented.
 */

import { BalanceService } from '../BalanceService';

import type { PackageInfo, BalanceSummary } from '@/types/purchase';

describe('BalanceService', () => {
  let balanceService: BalanceService;

  beforeEach(() => {
    balanceService = new BalanceService();
  });

  describe('calculateRemainingHours', () => {
    const mockActivePackages: PackageInfo[] = [
      {
        transaction_id: 1,
        plan_name: 'Package 1',
        hours_included: '10.0',
        hours_consumed: '3.5',
        hours_remaining: '6.5',
        expires_at: '2024-12-31T23:59:59Z',
        days_until_expiry: 30,
        is_expired: false,
      },
      {
        transaction_id: 2,
        plan_name: 'Package 2',
        hours_included: '20.0',
        hours_consumed: '5.0',
        hours_remaining: '15.0',
        expires_at: '2024-11-30T23:59:59Z',
        days_until_expiry: 60,
        is_expired: false,
      },
      {
        transaction_id: 3,
        plan_name: 'Package 3',
        hours_included: '5.0',
        hours_consumed: '2.0',
        hours_remaining: '3.0',
        expires_at: null,
        days_until_expiry: null,
        is_expired: false,
      },
    ];

    it('should calculate total remaining hours from active packages', () => {
      const result = balanceService.calculateRemainingHours(mockActivePackages);

      expect(result).toEqual({
        totalRemainingHours: 24.5, // 6.5 + 15.0 + 3.0
        totalPurchasedHours: 35.0, // 10.0 + 20.0 + 5.0
        totalConsumedHours: 10.5, // 3.5 + 5.0 + 2.0
        packageBreakdown: [
          {
            transactionId: 1,
            planName: 'Package 1',
            remainingHours: 6.5,
            percentageRemaining: 65.0, // (6.5/10.0) * 100
          },
          {
            transactionId: 2,
            planName: 'Package 2',
            remainingHours: 15.0,
            percentageRemaining: 75.0, // (15.0/20.0) * 100
          },
          {
            transactionId: 3,
            planName: 'Package 3',
            remainingHours: 3.0,
            percentageRemaining: 60.0, // (3.0/5.0) * 100
          },
        ],
      });
    });

    it('should handle empty packages array', () => {
      const result = balanceService.calculateRemainingHours([]);

      expect(result).toEqual({
        totalRemainingHours: 0,
        totalPurchasedHours: 0,
        totalConsumedHours: 0,
        packageBreakdown: [],
      });
    });

    it('should handle packages with zero remaining hours', () => {
      const exhaustedPackages: PackageInfo[] = [
        {
          transaction_id: 1,
          plan_name: 'Exhausted Package',
          hours_included: '10.0',
          hours_consumed: '10.0',
          hours_remaining: '0.0',
          expires_at: '2024-12-31T23:59:59Z',
          days_until_expiry: 30,
          is_expired: false,
        },
      ];

      const result = balanceService.calculateRemainingHours(exhaustedPackages);

      expect(result.totalRemainingHours).toBe(0);
      expect(result.totalPurchasedHours).toBe(10);
      expect(result.totalConsumedHours).toBe(10);
      expect(result.packageBreakdown[0].percentageRemaining).toBe(0);
    });

    it('should handle decimal hour calculations correctly', () => {
      const decimalPackages: PackageInfo[] = [
        {
          transaction_id: 1,
          plan_name: 'Decimal Package',
          hours_included: '7.25',
          hours_consumed: '2.75',
          hours_remaining: '4.5',
          expires_at: null,
          days_until_expiry: null,
          is_expired: false,
        },
      ];

      const result = balanceService.calculateRemainingHours(decimalPackages);

      expect(result.totalRemainingHours).toBe(4.5);
      expect(result.totalPurchasedHours).toBe(7.25);
      expect(result.totalConsumedHours).toBe(2.75);
      expect(result.packageBreakdown[0].percentageRemaining).toBeCloseTo(62.07, 1);
    });
  });

  describe('getBalanceStatus', () => {
    it('should return critical status for zero remaining hours', () => {
      const result = balanceService.getBalanceStatus(0, 20);

      expect(result).toEqual({
        level: 'critical',
        color: 'text-error-700',
        bgColor: 'bg-error-50',
        progressColor: 'text-error-500',
        icon: 'AlertTriangle',
        message: 'Balance depleted',
        urgency: 'urgent',
        percentage: 0,
        recommendedAction: 'immediate_purchase',
      });
    });

    it('should return critical status for very low hours (≤2 hours)', () => {
      const result = balanceService.getBalanceStatus(1.5, 20);

      expect(result).toEqual({
        level: 'critical',
        color: 'text-error-700',
        bgColor: 'bg-error-50',
        progressColor: 'text-error-500',
        icon: 'AlertTriangle',
        message: 'Critical balance',
        urgency: 'urgent',
        percentage: 7.5,
        recommendedAction: 'immediate_purchase',
      });
    });

    it('should return critical status for low percentage (≤10%)', () => {
      const result = balanceService.getBalanceStatus(2, 30); // 6.67%

      expect(result).toEqual({
        level: 'critical',
        color: 'text-error-700',
        bgColor: 'bg-error-50',
        progressColor: 'text-error-500',
        icon: 'AlertTriangle',
        message: 'Critical balance',
        urgency: 'urgent',
        percentage: 6.67,
        recommendedAction: 'immediate_purchase',
      });
    });

    it('should return low status for 5 or fewer hours remaining', () => {
      const result = balanceService.getBalanceStatus(4, 20);

      expect(result).toEqual({
        level: 'low',
        color: 'text-warning-700',
        bgColor: 'bg-warning-50',
        progressColor: 'text-warning-500',
        icon: 'Clock',
        message: 'Low balance',
        urgency: 'warning',
        percentage: 20,
        recommendedAction: 'plan_purchase',
      });
    });

    it('should return low status for ≤25% remaining', () => {
      const result = balanceService.getBalanceStatus(7, 30); // 23.33%

      expect(result).toEqual({
        level: 'low',
        color: 'text-warning-700',
        bgColor: 'bg-warning-50',
        progressColor: 'text-warning-500',
        icon: 'Clock',
        message: 'Low balance',
        urgency: 'warning',
        percentage: 23.33,
        recommendedAction: 'plan_purchase',
      });
    });

    it('should return medium status for ≤50% remaining', () => {
      const result = balanceService.getBalanceStatus(12, 30); // 40%

      expect(result).toEqual({
        level: 'medium',
        color: 'text-primary-700',
        bgColor: 'bg-primary-50',
        progressColor: 'text-primary-500',
        icon: 'TrendingUp',
        message: 'Moderate balance',
        urgency: 'info',
        percentage: 40,
        recommendedAction: 'monitor',
      });
    });

    it('should return healthy status for >50% remaining', () => {
      const result = balanceService.getBalanceStatus(20, 30); // 66.67%

      expect(result).toEqual({
        level: 'healthy',
        color: 'text-success-700',
        bgColor: 'bg-success-50',
        progressColor: 'text-success-500',
        icon: 'CheckCircle',
        message: 'Healthy balance',
        urgency: 'success',
        percentage: 66.67,
        recommendedAction: 'none',
      });
    });

    it('should handle edge case with zero total hours', () => {
      const result = balanceService.getBalanceStatus(0, 0);

      expect(result.level).toBe('critical');
      expect(result.percentage).toBe(0);
      expect(result.message).toBe('Balance depleted');
    });
  });

  describe('predictExpiryDate', () => {
    const mockBalance = {
      totalRemainingHours: 20,
      totalPurchasedHours: 30,
      totalConsumedHours: 10,
      packageBreakdown: [
        {
          transactionId: 1,
          planName: 'Package 1',
          remainingHours: 15,
          percentageRemaining: 75,
        },
        {
          transactionId: 2,
          planName: 'Package 2',
          remainingHours: 5,
          percentageRemaining: 50,
        },
      ],
    };

    it('should predict expiry based on consumption rate (daily usage)', () => {
      const consumptionHistory = [
        { date: '2024-01-01', hoursConsumed: 2 },
        { date: '2024-01-02', hoursConsumed: 1.5 },
        { date: '2024-01-03', hoursConsumed: 2.5 },
        { date: '2024-01-04', hoursConsumed: 1 },
        { date: '2024-01-05', hoursConsumed: 3 },
      ];

      const result = balanceService.predictExpiryDate(mockBalance, consumptionHistory);

      expect(result).toEqual({
        estimatedExpiryDate: expect.any(Date),
        daysUntilExpiry: expect.any(Number),
        weeklyConsumptionRate: expect.any(Number),
        monthlyConsumptionRate: expect.any(Number),
        confidence: expect.any(String), // 'high' | 'medium' | 'low'
        reasoning: expect.any(String),
      });

      expect(result.daysUntilExpiry).toBeGreaterThan(0);
      expect(['high', 'medium', 'low']).toContain(result.confidence);
    });

    it('should handle insufficient consumption history', () => {
      const limitedHistory = [{ date: '2024-01-01', hoursConsumed: 2 }];

      const result = balanceService.predictExpiryDate(mockBalance, limitedHistory);

      expect(result.confidence).toBe('low');
      expect(result.reasoning).toContain('insufficient data');
      expect(result.daysUntilExpiry).toBeGreaterThan(0);
    });

    it('should handle zero consumption (no usage pattern)', () => {
      const noConsumptionHistory: Array<{ date: string; hoursConsumed: number }> = [];

      const result = balanceService.predictExpiryDate(mockBalance, noConsumptionHistory);

      expect(result.confidence).toBe('low');
      expect(result.reasoning).toContain('no consumption history');
      expect(result.daysUntilExpiry).toBeNull();
    });

    it('should provide high confidence for consistent usage patterns', () => {
      const consistentHistory = Array.from({ length: 14 }, (_, i) => ({
        date: new Date(Date.now() - i * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        hoursConsumed: 1.5, // Consistent daily usage
      }));

      const result = balanceService.predictExpiryDate(mockBalance, consistentHistory);

      expect(result.confidence).toBe('high');
      expect(result.weeklyConsumptionRate).toBeCloseTo(10.5, 1); // 1.5 * 7
      expect(result.monthlyConsumptionRate).toBeCloseTo(45, 1); // 1.5 * 30
    });

    it('should handle irregular consumption patterns', () => {
      const irregularHistory = [
        { date: '2024-01-01', hoursConsumed: 5 },
        { date: '2024-01-02', hoursConsumed: 0 },
        { date: '2024-01-03', hoursConsumed: 8 },
        { date: '2024-01-04', hoursConsumed: 0.5 },
        { date: '2024-01-05', hoursConsumed: 0 },
        { date: '2024-01-06', hoursConsumed: 3 },
        { date: '2024-01-07', hoursConsumed: 1 },
      ];

      const result = balanceService.predictExpiryDate(mockBalance, irregularHistory);

      expect(result.confidence).toBe('medium');
      expect(result.reasoning).toContain('irregular usage pattern');
    });
  });

  describe('Business Logic Validation', () => {
    it('should be a pure function service with no UI dependencies', () => {
      // BalanceService should not depend on React hooks, components, or UI state
      expect(typeof BalanceService).toBe('function');
      expect(balanceService).toBeInstanceOf(BalanceService);

      // Should have all expected methods
      expect(typeof balanceService.calculateRemainingHours).toBe('function');
      expect(typeof balanceService.getBalanceStatus).toBe('function');
      expect(typeof balanceService.predictExpiryDate).toBe('function');
    });

    it('should maintain immutability in all calculation methods', () => {
      const originalPackages: PackageInfo[] = [
        {
          transaction_id: 1,
          plan_name: 'Test Package',
          hours_included: '10.0',
          hours_consumed: '3.0',
          hours_remaining: '7.0',
          expires_at: '2024-12-31T23:59:59Z',
          days_until_expiry: 30,
          is_expired: false,
        },
      ];

      const packagesCopy = JSON.parse(JSON.stringify(originalPackages));

      balanceService.calculateRemainingHours(originalPackages);

      // Original packages should not be modified
      expect(originalPackages).toEqual(packagesCopy);
    });

    it('should handle concurrent calculations without side effects', () => {
      const packages1: PackageInfo[] = [
        {
          transaction_id: 1,
          plan_name: 'Package 1',
          hours_included: '10.0',
          hours_consumed: '3.0',
          hours_remaining: '7.0',
          expires_at: null,
          days_until_expiry: null,
          is_expired: false,
        },
      ];

      const packages2: PackageInfo[] = [
        {
          transaction_id: 2,
          plan_name: 'Package 2',
          hours_included: '20.0',
          hours_consumed: '5.0',
          hours_remaining: '15.0',
          expires_at: null,
          days_until_expiry: null,
          is_expired: false,
        },
      ];

      const [result1, result2, status1, status2] = [
        balanceService.calculateRemainingHours(packages1),
        balanceService.calculateRemainingHours(packages2),
        balanceService.getBalanceStatus(7, 10),
        balanceService.getBalanceStatus(15, 20),
      ];

      expect(result1.totalRemainingHours).toBe(7);
      expect(result2.totalRemainingHours).toBe(15);
      expect(status1.level).toBe('healthy');
      expect(status2.level).toBe('healthy');
    });

    it('should provide consistent results for the same inputs', () => {
      const packages: PackageInfo[] = [
        {
          transaction_id: 1,
          plan_name: 'Consistent Test',
          hours_included: '15.5',
          hours_consumed: '4.25',
          hours_remaining: '11.25',
          expires_at: null,
          days_until_expiry: null,
          is_expired: false,
        },
      ];

      const result1 = balanceService.calculateRemainingHours(packages);
      const result2 = balanceService.calculateRemainingHours(packages);
      const status1 = balanceService.getBalanceStatus(11.25, 15.5);
      const status2 = balanceService.getBalanceStatus(11.25, 15.5);

      expect(result1).toEqual(result2);
      expect(status1).toEqual(status2);
    });
  });
});
