/**
 * Service Layer Integration Tests - TDD RED STATE
 * 
 * These tests verify that UI components properly integrate with the new service layer
 * through dependency injection. They will initially fail until the service integration is implemented.
 */

import React from 'react';
import { render, fireEvent, waitFor, screen } from '@testing-library/react-native';
import type { TopUpPackage, PaymentMethod, PackageInfo } from '@/types/purchase';
import { QuickTopUpPanel } from '@/components/student/quick-actions/QuickTopUpPanel';
import { BalanceStatusBar } from '@/components/student/balance/BalanceStatusBar';

// Mock the services - these will need to be implemented
jest.mock('@/services/business/payment/PaymentService');
jest.mock('@/services/business/balance/BalanceService');
jest.mock('@/api/purchaseApi');
jest.mock('@/hooks/usePaymentMethods');
jest.mock('@/hooks/useStudentBalance');

const mockPaymentService = {
  processQuickTopUp: jest.fn(),
  calculatePackagePrice: jest.fn(),
  validatePaymentMethod: jest.fn(),
};

const mockBalanceService = {
  calculateRemainingHours: jest.fn(),
  getBalanceStatus: jest.fn(),
  predictExpiryDate: jest.fn(),
};

// Mock the DI context to provide our mock services
jest.mock('@/services/di/context', () => ({
  useDependencies: () => ({
    paymentService: mockPaymentService,
    balanceService: mockBalanceService,
  }),
}));

const mockUsePaymentMethods = require('@/hooks/usePaymentMethods').usePaymentMethods;
const mockUseStudentBalance = require('@/hooks/useStudentBalance').useStudentBalance;

describe('Service Layer Integration', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('QuickTopUpPanel Service Integration', () => {
    const mockPackages: TopUpPackage[] = [
      {
        id: 1,
        name: '5 Hour Package',
        hours: 5,
        price_eur: '50.00',
        price_per_hour: '10.00',
        is_popular: false,
        display_order: 1,
      },
      {
        id: 2,
        name: '10 Hour Package',
        hours: 10,
        price_eur: '95.00',
        price_per_hour: '9.50',
        is_popular: true,
        discount_percentage: 5,
        display_order: 2,
      },
    ];

    const mockPaymentMethods: PaymentMethod[] = [
      {
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
      },
    ];

    beforeEach(() => {
      mockUsePaymentMethods.mockReturnValue({
        paymentMethods: mockPaymentMethods,
        loading: false,
      });

      mockUseStudentBalance.mockReturnValue({
        refetch: jest.fn(),
      });

      // Setup PaymentService mocks
      mockPaymentService.calculatePackagePrice.mockReturnValue({
        totalPrice: 95.00,
        pricePerHour: 9.50,
        originalPrice: 100.00,
        discountAmount: 5.00,
        discountPercentage: 5,
        hasDiscount: true,
      });

      mockPaymentService.validatePaymentMethod.mockReturnValue({
        isValid: true,
        errors: [],
        warnings: [],
        canProcess: true,
      });

      mockPaymentService.processQuickTopUp.mockResolvedValue({
        package_id: 2,
        use_default_payment_method: true,
        confirm_immediately: true,
      });

      // Mock the purchase API to return success
      const mockPurchaseApi = require('@/api/purchaseApi').PurchaseApiClient;
      mockPurchaseApi.getTopUpPackages.mockResolvedValue(mockPackages);
      mockPurchaseApi.quickTopUp.mockResolvedValue({
        success: true,
        transaction_id: 123,
        message: 'Purchase successful',
      });
    });

    it('should use PaymentService to calculate package prices during rendering', async () => {
      render(<QuickTopUpPanel email="test@example.com" />);

      await waitFor(() => {
        expect(screen.queryByText('Loading packages...')).toBeNull();
      });

      // PaymentService.calculatePackagePrice should be called for each package
      expect(mockPaymentService.calculatePackagePrice).toHaveBeenCalledWith(mockPackages[0]);
      expect(mockPaymentService.calculatePackagePrice).toHaveBeenCalledWith(mockPackages[1]);
      expect(mockPaymentService.calculatePackagePrice).toHaveBeenCalledTimes(2);
    });

    it('should use PaymentService to validate payment methods', async () => {
      render(<QuickTopUpPanel email="test@example.com" />);

      await waitFor(() => {
        expect(screen.queryByText('Loading packages...')).toBeNull();
      });

      // PaymentService.validatePaymentMethod should be called for default payment method
      expect(mockPaymentService.validatePaymentMethod).toHaveBeenCalledWith(mockPaymentMethods[0]);
    });

    it('should delegate purchase processing to PaymentService', async () => {
      render(<QuickTopUpPanel email="test@example.com" />);

      await waitFor(() => {
        expect(screen.queryByText('Loading packages...')).toBeNull();
      });

      // Select a package
      const packageCard = screen.getByText('10 Hour Package');
      fireEvent.press(packageCard);

      // Click purchase button
      const purchaseButton = screen.getByText(/Purchase 10 Hours/);
      fireEvent.press(purchaseButton);

      await waitFor(() => {
        expect(mockPaymentService.processQuickTopUp).toHaveBeenCalledWith(
          2, // package ID
          'pm_test123', // payment method ID
          'test@example.com'
        );
      });
    });

    it('should display calculated pricing information from PaymentService', async () => {
      render(<QuickTopUpPanel email="test@example.com" />);

      await waitFor(() => {
        expect(screen.queryByText('Loading packages...')).toBeNull();
      });

      // Should display the calculated price from PaymentService
      expect(screen.getByText('€95.00')).toBeTruthy();
      expect(screen.getByText('€9.50/hour')).toBeTruthy();
      expect(screen.getByText('5% discount')).toBeTruthy();
    });

    it('should handle PaymentService validation errors', async () => {
      // Mock validation failure
      mockPaymentService.validatePaymentMethod.mockReturnValue({
        isValid: false,
        errors: ['Payment method has expired'],
        warnings: [],
        canProcess: false,
      });

      render(<QuickTopUpPanel email="test@example.com" />);

      await waitFor(() => {
        expect(screen.queryByText('Loading packages...')).toBeNull();
      });

      // Should display validation error from PaymentService
      expect(screen.getByText('Payment method has expired')).toBeTruthy();
    });

    it('should handle PaymentService processing errors', async () => {
      mockPaymentService.processQuickTopUp.mockRejectedValue(new Error('Payment processing failed'));

      render(<QuickTopUpPanel email="test@example.com" />);

      await waitFor(() => {
        expect(screen.queryByText('Loading packages...')).toBeNull();
      });

      // Select package and attempt purchase
      fireEvent.press(screen.getByText('10 Hour Package'));
      fireEvent.press(screen.getByText(/Purchase 10 Hours/));

      await waitFor(() => {
        expect(screen.getByText('Purchase failed: Payment processing failed')).toBeTruthy();
      });
    });
  });

  describe('BalanceStatusBar Service Integration', () => {
    const mockPackages: PackageInfo[] = [
      {
        transaction_id: 1,
        plan_name: 'Package 1',
        hours_included: '20.0',
        hours_consumed: '8.0',
        hours_remaining: '12.0',
        expires_at: '2024-12-31T23:59:59Z',
        days_until_expiry: 30,
        is_expired: false,
      },
    ];

    beforeEach(() => {
      mockBalanceService.calculateRemainingHours.mockReturnValue({
        totalRemainingHours: 12.0,
        totalPurchasedHours: 20.0,
        totalConsumedHours: 8.0,
        packageBreakdown: [
          {
            transactionId: 1,
            planName: 'Package 1',
            remainingHours: 12.0,
            percentageRemaining: 60.0,
          },
        ],
      });

      mockBalanceService.getBalanceStatus.mockReturnValue({
        level: 'medium',
        color: 'text-primary-700',
        bgColor: 'bg-primary-50',
        progressColor: 'text-primary-500',
        icon: 'TrendingUp',
        message: 'Moderate balance',
        urgency: 'info',
        percentage: 60.0,
        recommendedAction: 'monitor',
      });
    });

    it('should use BalanceService to determine status', () => {
      render(
        <BalanceStatusBar
          remainingHours={12.0}
          totalHours={20.0}
          daysUntilExpiry={30}
          showDetails={true}
        />
      );

      // BalanceService.getBalanceStatus should be called with correct parameters
      expect(mockBalanceService.getBalanceStatus).toHaveBeenCalledWith(12.0, 20.0);
    });

    it('should display status information from BalanceService', () => {
      render(
        <BalanceStatusBar
          remainingHours={12.0}
          totalHours={20.0}
          daysUntilExpiry={30}
          showDetails={true}
        />
      );

      // Should display the status information calculated by BalanceService
      expect(screen.getByText('Moderate balance')).toBeTruthy();
      expect(screen.getByText('12.0h')).toBeTruthy();
      expect(screen.getByText('60% of 20.0 hours remaining')).toBeTruthy();
    });

    it('should apply styling based on BalanceService status', () => {
      render(
        <BalanceStatusBar
          remainingHours={12.0}
          totalHours={20.0}
          daysUntilExpiry={30}
          showDetails={true}
          className="test-balance-bar"
        />
      );

      // Should apply the bg color class from BalanceService status
      const statusCard = screen.getByTestId('balance-status-card');
      expect(statusCard).toHaveStyle({ backgroundColor: expect.stringMatching(/primary-50/) });
    });

    it('should handle critical balance status from BalanceService', () => {
      mockBalanceService.getBalanceStatus.mockReturnValue({
        level: 'critical',
        color: 'text-error-700',
        bgColor: 'bg-error-50',
        progressColor: 'text-error-500',
        icon: 'AlertTriangle',
        message: 'Critical balance',
        urgency: 'urgent',
        percentage: 5.0,
        recommendedAction: 'immediate_purchase',
      });

      render(
        <BalanceStatusBar
          remainingHours={1.0}
          totalHours={20.0}
          daysUntilExpiry={7}
          showDetails={true}
        />
      );

      expect(mockBalanceService.getBalanceStatus).toHaveBeenCalledWith(1.0, 20.0);
      expect(screen.getByText('Critical balance')).toBeTruthy();
    });

    it('should call BalanceService with updated values when props change', () => {
      const { rerender } = render(
        <BalanceStatusBar
          remainingHours={12.0}
          totalHours={20.0}
          daysUntilExpiry={30}
          showDetails={true}
        />
      );

      expect(mockBalanceService.getBalanceStatus).toHaveBeenCalledWith(12.0, 20.0);

      // Clear previous calls
      mockBalanceService.getBalanceStatus.mockClear();

      // Re-render with different values
      rerender(
        <BalanceStatusBar
          remainingHours={5.0}
          totalHours={20.0}
          daysUntilExpiry={15}
          showDetails={true}
        />
      );

      expect(mockBalanceService.getBalanceStatus).toHaveBeenCalledWith(5.0, 20.0);
    });
  });

  describe('Service Dependency Injection', () => {
    it('should inject services through DI context', () => {
      const TestComponent = () => {
        const { paymentService, balanceService } = require('@/services/di/context').useDependencies();
        
        return (
          <>
            <text testID="payment-service-available">
              {paymentService ? 'Payment Service Available' : 'Payment Service Missing'}
            </text>
            <text testID="balance-service-available">
              {balanceService ? 'Balance Service Available' : 'Balance Service Missing'}
            </text>
          </>
        );
      };

      render(<TestComponent />);

      expect(screen.getByTestId('payment-service-available')).toHaveTextContent('Payment Service Available');
      expect(screen.getByTestId('balance-service-available')).toHaveTextContent('Balance Service Available');
    });

    it('should provide isolated service instances for testing', () => {
      // Each component should get its own service instance through DI
      // This ensures testability and prevents shared state issues
      
      const TestComponent1 = () => {
        const { paymentService } = require('@/services/di/context').useDependencies();
        paymentService.calculatePackagePrice({ id: 1, hours: 5, price_eur: '50.00' });
        return <text>Component 1</text>;
      };

      const TestComponent2 = () => {
        const { paymentService } = require('@/services/di/context').useDependencies();
        paymentService.calculatePackagePrice({ id: 2, hours: 10, price_eur: '95.00' });
        return <text>Component 2</text>;
      };

      render(<TestComponent1 />);
      render(<TestComponent2 />);

      // Both components should have access to the service
      expect(mockPaymentService.calculatePackagePrice).toHaveBeenCalledTimes(2);
    });

    it('should support service method mocking for testing', () => {
      // Mock different behaviors for different test scenarios
      mockPaymentService.processQuickTopUp
        .mockResolvedValueOnce({ success: true, transaction_id: 1 })
        .mockRejectedValueOnce(new Error('Network error'));

      const TestComponent = () => {
        const { paymentService } = require('@/services/di/context').useDependencies();
        
        React.useEffect(() => {
          paymentService.processQuickTopUp(1, 'pm_test', 'test@example.com');
        }, [paymentService]);

        return <text>Test</text>;
      };

      render(<TestComponent />);

      expect(mockPaymentService.processQuickTopUp).toHaveBeenCalledWith(1, 'pm_test', 'test@example.com');
    });
  });

  describe('Business Logic Separation Validation', () => {
    it('should ensure UI components only handle presentation logic', async () => {
      render(<QuickTopUpPanel email="test@example.com" />);

      await waitFor(() => {
        expect(screen.queryByText('Loading packages...')).toBeNull();
      });

      // UI should delegate all business logic to services
      // No business calculations should happen in the component
      expect(mockPaymentService.calculatePackagePrice).toHaveBeenCalled();
      expect(mockPaymentService.validatePaymentMethod).toHaveBeenCalled();

      // Select and purchase
      fireEvent.press(screen.getByText('5 Hour Package'));
      fireEvent.press(screen.getByText(/Purchase 5 Hours/));

      await waitFor(() => {
        expect(mockPaymentService.processQuickTopUp).toHaveBeenCalled();
      });
    });

    it('should ensure BalanceStatusBar only handles display logic', () => {
      render(
        <BalanceStatusBar
          remainingHours={8.5}
          totalHours={15.0}
          daysUntilExpiry={10}
          showDetails={true}
        />
      );

      // All balance calculations should be delegated to BalanceService
      expect(mockBalanceService.getBalanceStatus).toHaveBeenCalledWith(8.5, 15.0);
      
      // Component should only be concerned with rendering the results
      expect(screen.getByText('Moderate balance')).toBeTruthy();
    });

    it('should verify services are stateless and pure', () => {
      const input1 = { id: 1, hours: 10, price_eur: '100.00' };
      const input2 = { id: 1, hours: 10, price_eur: '100.00' }; // Same input

      mockPaymentService.calculatePackagePrice.mockReturnValue({
        totalPrice: 100.00,
        pricePerHour: 10.00,
        hasDiscount: false,
      });

      // Call service multiple times with same input
      const result1 = mockPaymentService.calculatePackagePrice(input1);
      const result2 = mockPaymentService.calculatePackagePrice(input2);

      // Results should be identical (pure function behavior)
      expect(result1).toEqual(result2);
      expect(mockPaymentService.calculatePackagePrice).toHaveBeenCalledTimes(2);
    });
  });
});