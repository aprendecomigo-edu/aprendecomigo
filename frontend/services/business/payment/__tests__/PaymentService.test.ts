/**
 * PaymentService Tests - TDD RED STATE
 *
 * These tests define the expected behavior for payment business logic extraction
 * from UI components. They will initially fail until the PaymentService is implemented.
 */

import { PaymentService } from '../PaymentService';

import type { TopUpPackage, PaymentMethod, QuickTopUpRequest } from '@/types/purchase';

describe('PaymentService', () => {
  let paymentService: PaymentService;

  beforeEach(() => {
    paymentService = new PaymentService();
  });

  describe('processQuickTopUp', () => {
    const mockPackage: TopUpPackage = {
      id: 1,
      name: '10 Hour Package',
      hours: 10,
      price_eur: '99.50',
      price_per_hour: '9.95',
      is_popular: true,
      discount_percentage: 10,
      display_order: 2,
    };

    const mockPaymentMethod: PaymentMethod = {
      id: 'pm_test123',
      type: 'card',
      card: {
        brand: 'visa',
        last4: '4242',
        exp_month: 12,
        exp_year: 2025,
        funding: 'credit',
      },
      billing_details: {
        name: 'John Doe',
        email: 'john@example.com',
      },
      is_default: true,
      created_at: '2024-01-01T00:00:00Z',
    };

    it('should create a valid QuickTopUpRequest with payment method ID', async () => {
      const result = await paymentService.processQuickTopUp(
        mockPackage.id,
        mockPaymentMethod.id,
        'student@example.com',
      );

      expect(result).toEqual({
        package_id: 1,
        payment_method_id: 'pm_test123',
        use_default_payment_method: false,
        confirm_immediately: true,
      });
    });

    it('should create a valid QuickTopUpRequest using default payment method', async () => {
      const result = await paymentService.processQuickTopUp(
        mockPackage.id,
        null,
        'student@example.com',
      );

      expect(result).toEqual({
        package_id: 1,
        use_default_payment_method: true,
        confirm_immediately: true,
      });
    });

    it('should handle admin access with email parameter', async () => {
      const result = await paymentService.processQuickTopUp(
        mockPackage.id,
        mockPaymentMethod.id,
        'admin@school.com',
      );

      expect(result.package_id).toBe(mockPackage.id);
      expect(result.payment_method_id).toBe(mockPaymentMethod.id);
      expect(result.confirm_immediately).toBe(true);
    });

    it('should validate package ID is required', async () => {
      await expect(
        paymentService.processQuickTopUp(0, mockPaymentMethod.id, 'test@example.com'),
      ).rejects.toThrow('Package ID is required');
    });

    it('should validate either payment method ID or default payment method flag', async () => {
      await expect(paymentService.processQuickTopUp(mockPackage.id, null, null)).rejects.toThrow(
        'Either payment method ID or use default payment method must be specified',
      );
    });
  });

  describe('calculatePackagePrice', () => {
    it('should calculate correct price for package without discount', () => {
      const pkg: TopUpPackage = {
        id: 1,
        name: '5 Hour Package',
        hours: 5,
        price_eur: '50.00',
        price_per_hour: '10.00',
        is_popular: false,
        display_order: 1,
      };

      const result = paymentService.calculatePackagePrice(pkg);

      expect(result).toEqual({
        totalPrice: 50.0,
        pricePerHour: 10.0,
        originalPrice: 50.0,
        discountAmount: 0,
        discountPercentage: 0,
        hasDiscount: false,
      });
    });

    it('should calculate correct price for package with discount', () => {
      const pkg: TopUpPackage = {
        id: 2,
        name: '20 Hour Package',
        hours: 20,
        price_eur: '180.00',
        price_per_hour: '9.00',
        is_popular: true,
        discount_percentage: 10,
        display_order: 3,
      };

      const result = paymentService.calculatePackagePrice(pkg);

      expect(result).toEqual({
        totalPrice: 180.0,
        pricePerHour: 9.0,
        originalPrice: 200.0, // 20 hours * 10.00 per hour
        discountAmount: 20.0,
        discountPercentage: 10,
        hasDiscount: true,
      });
    });

    it('should handle edge case with zero hours', () => {
      const pkg: TopUpPackage = {
        id: 3,
        name: 'Invalid Package',
        hours: 0,
        price_eur: '0.00',
        price_per_hour: '0.00',
        is_popular: false,
        display_order: 1,
      };

      const result = paymentService.calculatePackagePrice(pkg);

      expect(result.totalPrice).toBe(0);
      expect(result.pricePerHour).toBe(0);
    });

    it('should handle string price conversion correctly', () => {
      const pkg: TopUpPackage = {
        id: 4,
        name: '15 Hour Package',
        hours: 15,
        price_eur: '142.50',
        price_per_hour: '9.50',
        is_popular: false,
        discount_percentage: 5,
        display_order: 2,
      };

      const result = paymentService.calculatePackagePrice(pkg);

      expect(result.totalPrice).toBe(142.5);
      expect(result.pricePerHour).toBe(9.5);
      expect(result.hasDiscount).toBe(true);
      expect(result.discountPercentage).toBe(5);
    });
  });

  describe('validatePaymentMethod', () => {
    const validPaymentMethod: PaymentMethod = {
      id: 'pm_valid123',
      type: 'card',
      card: {
        brand: 'visa',
        last4: '4242',
        exp_month: 12,
        exp_year: 2025,
        funding: 'credit',
      },
      billing_details: {
        name: 'John Doe',
        email: 'john@example.com',
      },
      is_default: true,
      created_at: '2024-01-01T00:00:00Z',
    };

    it('should return valid status for a valid payment method', () => {
      const result = paymentService.validatePaymentMethod(validPaymentMethod);

      expect(result).toEqual({
        isValid: true,
        errors: [],
        warnings: [],
        canProcess: true,
      });
    });

    it('should detect expired payment method', () => {
      const expiredPaymentMethod: PaymentMethod = {
        ...validPaymentMethod,
        card: {
          ...validPaymentMethod.card,
          exp_month: 1,
          exp_year: 2023, // Expired
        },
      };

      const result = paymentService.validatePaymentMethod(expiredPaymentMethod);

      expect(result.isValid).toBe(false);
      expect(result.errors).toContain('Payment method has expired');
      expect(result.canProcess).toBe(false);
    });

    it('should detect payment method expiring soon', () => {
      const currentDate = new Date();
      const soonExpiringPaymentMethod: PaymentMethod = {
        ...validPaymentMethod,
        card: {
          ...validPaymentMethod.card,
          exp_month: currentDate.getMonth() + 1,
          exp_year: currentDate.getFullYear(),
        },
      };

      const result = paymentService.validatePaymentMethod(soonExpiringPaymentMethod);

      expect(result.isValid).toBe(true);
      expect(result.warnings).toContain('Payment method expires soon');
      expect(result.canProcess).toBe(true);
    });

    it('should validate payment method ID format', () => {
      const invalidPaymentMethod: PaymentMethod = {
        ...validPaymentMethod,
        id: '', // Invalid empty ID
      };

      const result = paymentService.validatePaymentMethod(invalidPaymentMethod);

      expect(result.isValid).toBe(false);
      expect(result.errors).toContain('Invalid payment method ID');
      expect(result.canProcess).toBe(false);
    });

    it('should validate card details are present', () => {
      const incompletePaymentMethod = {
        ...validPaymentMethod,
        card: {
          brand: '',
          last4: '',
          exp_month: 0,
          exp_year: 0,
          funding: '',
        },
      };

      const result = paymentService.validatePaymentMethod(incompletePaymentMethod);

      expect(result.isValid).toBe(false);
      expect(result.errors).toContain('Incomplete card details');
      expect(result.canProcess).toBe(false);
    });

    it('should handle funding type validation', () => {
      const prepaidPaymentMethod: PaymentMethod = {
        ...validPaymentMethod,
        card: {
          ...validPaymentMethod.card,
          funding: 'prepaid',
        },
      };

      const result = paymentService.validatePaymentMethod(prepaidPaymentMethod);

      expect(result.isValid).toBe(true);
      expect(result.warnings).toContain('Prepaid card may have restrictions');
      expect(result.canProcess).toBe(true);
    });
  });

  describe('Business Logic Validation', () => {
    it('should be a pure function service with no UI dependencies', () => {
      // PaymentService should not depend on React hooks, components, or UI state
      expect(typeof PaymentService).toBe('function');
      expect(paymentService).toBeInstanceOf(PaymentService);

      // Should have all expected methods
      expect(typeof paymentService.processQuickTopUp).toBe('function');
      expect(typeof paymentService.calculatePackagePrice).toBe('function');
      expect(typeof paymentService.validatePaymentMethod).toBe('function');
    });

    it('should handle concurrent payment processing validation', async () => {
      const requests = [
        paymentService.processQuickTopUp(1, 'pm_test1', 'user1@example.com'),
        paymentService.processQuickTopUp(2, 'pm_test2', 'user2@example.com'),
        paymentService.processQuickTopUp(3, null, 'user3@example.com'),
      ];

      const results = await Promise.all(requests);

      expect(results).toHaveLength(3);
      results.forEach((result, index) => {
        expect(result.package_id).toBe(index + 1);
        expect(result.confirm_immediately).toBe(true);
      });
    });

    it('should maintain immutability in calculation methods', () => {
      const originalPackage: TopUpPackage = {
        id: 1,
        name: '10 Hour Package',
        hours: 10,
        price_eur: '100.00',
        price_per_hour: '10.00',
        is_popular: true,
        discount_percentage: 15,
        display_order: 1,
      };

      const packageCopy = { ...originalPackage };

      paymentService.calculatePackagePrice(originalPackage);

      // Original package should not be modified
      expect(originalPackage).toEqual(packageCopy);
    });
  });
});
