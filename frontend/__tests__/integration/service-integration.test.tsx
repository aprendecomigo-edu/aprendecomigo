/**
 * Service Integration Test
 *
 * Tests the integration between business services and service factory
 */

import { createBusinessServices } from '@/services/business/factory';
import { createMockDependencies } from '@/services/di/testing';

describe('Service Integration', () => {
  describe('BalanceService Integration', () => {
    it('should create and use BalanceService correctly', () => {
      // Create business services
      const businessServices = createBusinessServices();

      // Verify business service functionality directly
      const balanceStatus = businessServices.balanceService.getBalanceStatus(15, 20);
      expect(balanceStatus.level).toBe('healthy');
      expect(balanceStatus.percentage).toBe(75);
      expect(balanceStatus.color).toBe('text-success-700');
      expect(balanceStatus.message).toBe('Healthy balance');
    });

    it('should handle critical balance status through BalanceService', () => {
      // Create business services
      const businessServices = createBusinessServices();

      // Verify business service functionality
      const balanceStatus = businessServices.balanceService.getBalanceStatus(1, 20);
      expect(balanceStatus.level).toBe('critical');
      expect(balanceStatus.percentage).toBe(5);
      expect(balanceStatus.color).toBe('text-error-700');
      expect(balanceStatus.message).toBe('Critical balance');
    });

    it('should calculate remaining hours correctly', () => {
      const businessServices = createBusinessServices();

      const mockPackages = [
        {
          transaction_id: 1,
          plan_name: 'Package 1',
          hours_included: '10.0',
          hours_consumed: '3.0',
          hours_remaining: '7.0',
          expires_at: '2024-12-31T23:59:59Z',
          days_until_expiry: 30,
          is_expired: false,
        },
      ];

      const calculation = businessServices.balanceService.calculateRemainingHours(mockPackages);
      expect(calculation.totalRemainingHours).toBe(7);
      expect(calculation.totalPurchasedHours).toBe(10);
      expect(calculation.totalConsumedHours).toBe(3);
    });
  });

  describe('PaymentService Integration', () => {
    it('should create PaymentService without errors', async () => {
      const businessServices = createBusinessServices();

      expect(businessServices.paymentService).toBeDefined();
      expect(typeof businessServices.paymentService.processQuickTopUp).toBe('function');
      expect(typeof businessServices.paymentService.calculatePackagePrice).toBe('function');
      expect(typeof businessServices.paymentService.validatePaymentMethod).toBe('function');
    });

    it('should process quick top-up correctly', async () => {
      const businessServices = createBusinessServices();

      const request = await businessServices.paymentService.processQuickTopUp(
        123,
        null,
        'test@example.com',
      );

      expect(request.package_id).toBe(123);
      expect(request.use_default_payment_method).toBe(true);
      expect(request.confirm_immediately).toBe(true);
    });

    it('should calculate package price correctly', () => {
      const businessServices = createBusinessServices();

      const mockPackage = {
        id: 1,
        name: 'Test Package',
        hours: 10,
        price_eur: '50.00',
        price_per_hour: '5.00',
        discount_percentage: 10,
        is_popular: false,
        display_order: 1,
      };

      const calculation = businessServices.paymentService.calculatePackagePrice(mockPackage);
      expect(calculation.totalPrice).toBe(50);
      expect(calculation.pricePerHour).toBe(5);
      expect(calculation.hasDiscount).toBe(true);
      expect(calculation.discountPercentage).toBe(10);
    });
  });

  describe('Service Factory Integration', () => {
    it('should create all business services correctly', () => {
      const businessServices = createBusinessServices();

      expect(businessServices.paymentService).toBeDefined();
      expect(businessServices.balanceService).toBeDefined();
    });

    it('should integrate with mock dependencies', () => {
      const mockDeps = createMockDependencies();
      const businessServices = createBusinessServices();

      const fullDependencies = {
        ...mockDeps,
        paymentService: businessServices.paymentService,
        balanceService: businessServices.balanceService,
      };

      expect(fullDependencies.paymentService).toBeDefined();
      expect(fullDependencies.balanceService).toBeDefined();
      expect(fullDependencies.authApi).toBeDefined();
      expect(fullDependencies.storageService).toBeDefined();
    });
  });
});
