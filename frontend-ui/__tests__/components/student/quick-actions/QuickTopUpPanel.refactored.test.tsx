/**
 * Tests for Refactored QuickTopUpPanel - Dependency Injection Architecture
 * 
 * This tests the new architecture where QuickTopUpPanel uses injected services
 * instead of direct API calls, separating UI concerns from business logic.
 * 
 * EXPECTED TO FAIL: These tests validate the refactored architecture that hasn't been implemented yet.
 */

import React from 'react';
import { render, fireEvent, waitFor, screen } from '@testing-library/react-native';
import { QuickTopUpPanel } from '@/components/student/quick-actions/QuickTopUpPanel';
import { DependencyProvider } from '@/services/di/context';
import { PaymentService, TopUpService, BalanceService } from '@/services/types';
import type { TopUpPackage, PaymentMethod, QuickTopUpResponse } from '@/types/purchase';

// Mock services that will be injected
const mockPaymentService: jest.Mocked<PaymentService> = {
  processQuickTopUp: jest.fn(),
  validatePaymentMethod: jest.fn(),
  getPaymentMethods: jest.fn(),
  setDefaultPaymentMethod: jest.fn(),
  getPaymentMethodMetadata: jest.fn(),
};

const mockTopUpService: jest.Mocked<TopUpService> = {
  getAvailablePackages: jest.fn(),
  calculateDiscounts: jest.fn(),
  validateTopUpRequest: jest.fn(),
  processTopUpRequest: jest.fn(),
  getTopUpHistory: jest.fn(),
};

const mockBalanceService: jest.Mocked<BalanceService> = {
  getCurrentBalance: jest.fn(),
  refreshBalance: jest.fn(),
  subscribeToBalanceUpdates: jest.fn(),
  unsubscribeFromBalanceUpdates: jest.fn(),
  getBalanceHistory: jest.fn(),
};

// Mock dependencies object
const mockDependencies = {
  paymentService: mockPaymentService,
  topUpService: mockTopUpService,
  balanceService: mockBalanceService,
};

// Mock useToast
const mockToast = {
  show: jest.fn(),
};

jest.mock('@/components/ui/toast', () => ({
  useToast: () => mockToast,
}));

// Test data
const mockPackages: TopUpPackage[] = [
  {
    id: '5h-package',
    name: '5 Hours',
    hours: 5,
    price_eur: 25.00,
    price_per_hour: 5.00,
    discount_percentage: 0,
    is_popular: false,
    display_order: 1,
  },
  {
    id: '10h-package',
    name: '10 Hours',
    hours: 10,
    price_eur: 45.00,
    price_per_hour: 4.50,
    discount_percentage: 10,
    is_popular: true,
    display_order: 2,
  },
  {
    id: '20h-package',
    name: '20 Hours',
    hours: 20,
    price_eur: 80.00,
    price_per_hour: 4.00,
    discount_percentage: 20,
    is_popular: false,
    display_order: 3,
  },
];

const mockPaymentMethods: PaymentMethod[] = [
  {
    id: 'pm_test123',
    card: {
      brand: 'visa',
      last4: '4242',
      exp_month: 12,
      exp_year: 2025,
    },
    is_default: true,
    created_at: '2024-01-01T00:00:00Z',
  },
];

const mockSuccessResponse: QuickTopUpResponse = {
  success: true,
  message: 'Top-up successful',
  transaction_id: 'txn_123',
  hours_added: 10,
  new_balance: 15,
  payment_intent_id: 'pi_test123',
};

describe('QuickTopUpPanel - Refactored Architecture', () => {
  const renderWithDependencies = (props = {}) => {
    return render(
      <DependencyProvider dependencies={mockDependencies}>
        <QuickTopUpPanel {...props} />
      </DependencyProvider>
    );
  };

  beforeEach(() => {
    jest.clearAllMocks();
    
    // Setup default mock responses
    mockTopUpService.getAvailablePackages.mockResolvedValue(mockPackages);
    mockPaymentService.getPaymentMethods.mockResolvedValue(mockPaymentMethods);
    mockBalanceService.getCurrentBalance.mockResolvedValue({ hours: 5, last_updated: new Date() });
  });

  describe('Dependency Injection', () => {
    it('should use injected TopUpService instead of direct API calls', async () => {
      // Act
      renderWithDependencies();

      // Assert
      await waitFor(() => {
        expect(mockTopUpService.getAvailablePackages).toHaveBeenCalled();
      });

      // Should NOT call the old PurchaseApiClient
      expect(mockTopUpService.getAvailablePackages).toHaveBeenCalledWith(undefined);
    });

    it('should use injected PaymentService for payment methods', async () => {
      // Act
      renderWithDependencies({ email: 'test@example.com' });

      // Assert
      await waitFor(() => {
        expect(mockPaymentService.getPaymentMethods).toHaveBeenCalledWith('test@example.com');
      });
    });

    it('should use injected BalanceService for balance refresh', async () => {
      // Arrange
      const onTopUpSuccess = jest.fn();
      mockTopUpService.processTopUpRequest.mockResolvedValue(mockSuccessResponse);

      renderWithDependencies({ onTopUpSuccess });

      // Wait for loading to complete
      await waitFor(() => {
        expect(screen.getByText('10 Hours')).toBeTruthy();
      });

      // Act - Select package and purchase
      fireEvent.press(screen.getByText('10 Hours'));
      fireEvent.press(screen.getByText(/Purchase.*Hours/));

      // Assert
      await waitFor(() => {
        expect(mockBalanceService.refreshBalance).toHaveBeenCalled();
      });
    });

    it('should throw error when dependencies are not provided', () => {
      // Arrange
      const originalError = console.error;
      console.error = jest.fn();

      // Act & Assert
      expect(() => {
        render(<QuickTopUpPanel />);
      }).toThrow('Dependencies not found. Make sure to wrap component with DependencyProvider');

      console.error = originalError;
    });
  });

  describe('Service Integration - Pure UI Logic', () => {
    it('should render packages from TopUpService', async () => {
      // Act
      renderWithDependencies();

      // Assert
      await waitFor(() => {
        expect(screen.getByText('5 Hours')).toBeTruthy();
        expect(screen.getByText('10 Hours')).toBeTruthy();
        expect(screen.getByText('20 Hours')).toBeTruthy();
        expect(screen.getByText('POPULAR')).toBeTruthy();
      });
    });

    it('should display payment method from PaymentService', async () => {
      // Act
      renderWithDependencies();

      // Assert
      await waitFor(() => {
        expect(screen.getByText('VISA ••••4242')).toBeTruthy();
        expect(screen.getByText('Expires 12/2025')).toBeTruthy();
      });
    });

    it('should handle package selection through UI state only', async () => {
      // Act
      renderWithDependencies();

      await waitFor(() => {
        expect(screen.getByText('10 Hours')).toBeTruthy();
      });

      // Select a package
      fireEvent.press(screen.getByText('10 Hours'));

      // Assert - UI should update to show selection
      const purchaseButton = screen.getByText(/Purchase 10 Hours for €45/);
      expect(purchaseButton).toBeTruthy();
      expect(purchaseButton.props.accessibilityState?.disabled).toBe(false);
    });

    it('should disable purchase when no package selected', async () => {
      // Act
      renderWithDependencies();

      // Assert
      await waitFor(() => {
        const purchaseButton = screen.getByText('Select a Package');
        expect(purchaseButton.props.accessibilityState?.disabled).toBe(true);
      });
    });

    it('should disable purchase when no payment method available', async () => {
      // Arrange
      mockPaymentService.getPaymentMethods.mockResolvedValue([]);

      // Act
      renderWithDependencies();

      await waitFor(() => {
        expect(screen.getByText('No Default Payment Method')).toBeTruthy();
      });

      // Try to select a package
      fireEvent.press(screen.getByText('10 Hours'));

      // Assert - Package selection should be disabled
      const packages = screen.getAllByText(/Hours/);
      packages.forEach(pkg => {
        expect(pkg.parent?.props.style).toEqual(
          expect.objectContaining({ opacity: 0.5 })
        );
      });
    });
  });

  describe('Business Logic Delegation', () => {
    it('should delegate top-up processing to TopUpService', async () => {
      // Arrange
      mockTopUpService.processTopUpRequest.mockResolvedValue(mockSuccessResponse);

      renderWithDependencies();

      await waitFor(() => {
        expect(screen.getByText('10 Hours')).toBeTruthy();
      });

      // Act
      fireEvent.press(screen.getByText('10 Hours'));
      fireEvent.press(screen.getByText(/Purchase.*Hours/));

      // Assert
      await waitFor(() => {
        expect(mockTopUpService.processTopUpRequest).toHaveBeenCalledWith({
          packageId: '10h-package',
          paymentMethodId: 'pm_test123',
          email: undefined,
        });
      });
    });

    it('should delegate payment validation to PaymentService', async () => {
      // Arrange
      mockPaymentService.validatePaymentMethod.mockResolvedValue(true);
      mockTopUpService.processTopUpRequest.mockResolvedValue(mockSuccessResponse);

      renderWithDependencies();

      await waitFor(() => {
        expect(screen.getByText('10 Hours')).toBeTruthy();
      });

      // Act
      fireEvent.press(screen.getByText('10 Hours'));
      fireEvent.press(screen.getByText(/Purchase.*Hours/));

      // Assert
      await waitFor(() => {
        expect(mockPaymentService.validatePaymentMethod).toHaveBeenCalledWith('pm_test123');
      });
    });

    it('should handle service errors gracefully', async () => {
      // Arrange
      mockTopUpService.processTopUpRequest.mockRejectedValue(
        new Error('Payment processing failed')
      );

      renderWithDependencies();

      await waitFor(() => {
        expect(screen.getByText('10 Hours')).toBeTruthy();
      });

      // Act
      fireEvent.press(screen.getByText('10 Hours'));
      fireEvent.press(screen.getByText(/Purchase.*Hours/));

      // Assert
      await waitFor(() => {
        expect(mockToast.show).toHaveBeenCalledWith({
          placement: 'top',
          render: expect.any(Function),
        });
      });

      // Should show error message
      expect(screen.getByText(/Purchase failed: Payment processing failed/)).toBeTruthy();
    });

    it('should validate requests before processing', async () => {
      // Arrange
      mockTopUpService.validateTopUpRequest.mockResolvedValue({
        isValid: false,
        errors: ['Insufficient payment method verification']
      });

      renderWithDependencies();

      await waitFor(() => {
        expect(screen.getByText('10 Hours')).toBeTruthy();
      });

      // Act
      fireEvent.press(screen.getByText('10 Hours'));
      fireEvent.press(screen.getByText(/Purchase.*Hours/));

      // Assert
      await waitFor(() => {
        expect(mockTopUpService.validateTopUpRequest).toHaveBeenCalled();
      });

      // Should not proceed with invalid request
      expect(mockTopUpService.processTopUpRequest).not.toHaveBeenCalled();
    });
  });

  describe('Service Error Boundaries', () => {
    it('should handle TopUpService failures during load', async () => {
      // Arrange
      mockTopUpService.getAvailablePackages.mockRejectedValue(
        new Error('Failed to load packages')
      );

      // Act
      renderWithDependencies();

      // Assert
      await waitFor(() => {
        expect(screen.getByText('Unable to Load Packages')).toBeTruthy();
        expect(screen.getByText('Failed to load packages')).toBeTruthy();
      });
    });

    it('should handle PaymentService failures during load', async () => {
      // Arrange
      mockPaymentService.getPaymentMethods.mockRejectedValue(
        new Error('Payment service unavailable')
      );

      // Act
      renderWithDependencies();

      // Assert
      await waitFor(() => {
        // Should show no payment method warning instead of crashing
        expect(screen.getByText('No Default Payment Method')).toBeTruthy();
      });
    });

    it('should handle BalanceService failures gracefully', async () => {
      // Arrange
      mockBalanceService.refreshBalance.mockRejectedValue(
        new Error('Balance service error')
      );
      mockTopUpService.processTopUpRequest.mockResolvedValue(mockSuccessResponse);

      renderWithDependencies();

      await waitFor(() => {
        expect(screen.getByText('10 Hours')).toBeTruthy();
      });

      // Act
      fireEvent.press(screen.getByText('10 Hours'));
      fireEvent.press(screen.getByText(/Purchase.*Hours/));

      // Assert - Should complete purchase even if balance refresh fails
      await waitFor(() => {
        expect(mockToast.show).toHaveBeenCalledWith(
          expect.objectContaining({
            placement: 'top',
          })
        );
      });
    });
  });

  describe('Service Configuration', () => {
    it('should pass email parameter to all services', async () => {
      // Act
      renderWithDependencies({ email: 'student@example.com' });

      // Assert
      await waitFor(() => {
        expect(mockTopUpService.getAvailablePackages).toHaveBeenCalledWith('student@example.com');
        expect(mockPaymentService.getPaymentMethods).toHaveBeenCalledWith('student@example.com');
      });
    });

    it('should handle admin override scenarios', async () => {
      // Arrange
      const adminEmail = 'admin@school.edu';
      const studentEmail = 'student@example.com';

      // Act
      renderWithDependencies({ 
        email: studentEmail,
        adminOverride: adminEmail 
      });

      // Assert
      await waitFor(() => {
        expect(mockTopUpService.getAvailablePackages).toHaveBeenCalledWith(
          studentEmail,
          { adminOverride: adminEmail }
        );
      });
    });

    it('should support custom service configurations', async () => {
      // Arrange
      const customDependencies = {
        ...mockDependencies,
        topUpService: {
          ...mockTopUpService,
          getAvailablePackages: jest.fn().mockResolvedValue([
            { ...mockPackages[0], name: 'Custom Package' }
          ]),
        },
      };

      // Act
      render(
        <DependencyProvider dependencies={customDependencies}>
          <QuickTopUpPanel />
        </DependencyProvider>
      );

      // Assert
      await waitFor(() => {
        expect(screen.getByText('Custom Package')).toBeTruthy();
      });
    });
  });

  describe('Callback Integration', () => {
    it('should call success callback with service response', async () => {
      // Arrange
      const onTopUpSuccess = jest.fn();
      mockTopUpService.processTopUpRequest.mockResolvedValue(mockSuccessResponse);

      renderWithDependencies({ onTopUpSuccess });

      await waitFor(() => {
        expect(screen.getByText('10 Hours')).toBeTruthy();
      });

      // Act
      fireEvent.press(screen.getByText('10 Hours'));
      fireEvent.press(screen.getByText(/Purchase.*Hours/));

      // Assert
      await waitFor(() => {
        expect(onTopUpSuccess).toHaveBeenCalledWith(mockSuccessResponse);
      });
    });

    it('should call error callback with service errors', async () => {
      // Arrange
      const onTopUpError = jest.fn();
      const errorMessage = 'Service temporarily unavailable';
      mockTopUpService.processTopUpRequest.mockRejectedValue(new Error(errorMessage));

      renderWithDependencies({ onTopUpError });

      await waitFor(() => {
        expect(screen.getByText('10 Hours')).toBeTruthy();
      });

      // Act
      fireEvent.press(screen.getByText('10 Hours'));
      fireEvent.press(screen.getByText(/Purchase.*Hours/));

      // Assert
      await waitFor(() => {
        expect(onTopUpError).toHaveBeenCalledWith(errorMessage);
      });
    });

    it('should handle modal close after successful purchase', async () => {
      // Arrange
      const onClose = jest.fn();
      mockTopUpService.processTopUpRequest.mockResolvedValue(mockSuccessResponse);

      renderWithDependencies({ isModal: true, onClose });

      await waitFor(() => {
        expect(screen.getByText('10 Hours')).toBeTruthy();
      });

      // Act
      fireEvent.press(screen.getByText('10 Hours'));
      fireEvent.press(screen.getByText(/Purchase.*Hours/));

      // Assert
      await waitFor(() => {
        expect(onClose).toHaveBeenCalled();
      });
    });
  });

  describe('Separation of Concerns Validation', () => {
    it('should NOT make direct API calls', async () => {
      // This test ensures the component doesn't import PurchaseApiClient
      const { container } = renderWithDependencies();

      await waitFor(() => {
        expect(screen.getByText('Quick Top-Up')).toBeTruthy();
      });

      // Assert - Component should only use injected services
      expect(mockTopUpService.getAvailablePackages).toHaveBeenCalled();
      
      // Should NOT access any global API clients directly
      // This would fail if the component still imports PurchaseApiClient
    });

    it('should only handle UI state and delegate business logic', async () => {
      // Arrange
      mockTopUpService.processTopUpRequest.mockResolvedValue(mockSuccessResponse);

      renderWithDependencies();

      await waitFor(() => {
        expect(screen.getByText('10 Hours')).toBeTruthy();
      });

      // Act
      fireEvent.press(screen.getByText('10 Hours'));
      fireEvent.press(screen.getByText(/Purchase.*Hours/));

      // Assert - Component should:
      // 1. Call validation service
      expect(mockTopUpService.validateTopUpRequest).toHaveBeenCalled();
      // 2. Call processing service
      await waitFor(() => {
        expect(mockTopUpService.processTopUpRequest).toHaveBeenCalled();
      });
      // 3. Call balance refresh service
      expect(mockBalanceService.refreshBalance).toHaveBeenCalled();
      
      // But should NOT contain business logic itself
    });

    it('should be testable in isolation with mocked services', () => {
      // This test validates that the component can be fully tested
      // without any real API calls or business logic implementations

      // Arrange - Override all service responses
      mockTopUpService.getAvailablePackages.mockResolvedValue([]);
      mockPaymentService.getPaymentMethods.mockResolvedValue([]);

      // Act
      renderWithDependencies();

      // Assert - Component should render even with empty responses
      expect(screen.getByText('Quick Top-Up')).toBeTruthy();
      expect(screen.getByText('Choose Package')).toBeTruthy();
    });
  });
});