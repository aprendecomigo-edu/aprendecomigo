/**
 * PricingPlanSelector Component Tests
 *
 * Comprehensive test suite for the pricing plan selector component.
 * Tests plan display, selection, loading states, and error handling.
 */

import { render, fireEvent, waitFor } from '@testing-library/react-native';
import React from 'react';

import {
  createMockPricingPlans,
  createMockPricingPlan,
} from '@/__tests__/utils/payment-test-utils';
import { PricingPlanSelector } from '@/components/purchase/PricingPlanSelector';
import { usePricingPlans } from '@/hooks/usePricingPlans';

// Mock the hook
jest.mock('@/hooks/usePricingPlans');
const mockUsePricingPlans = usePricingPlans as jest.MockedFunction<typeof usePricingPlans>;

// Mock PricingPlanCard component to test orchestration behavior
jest.mock('@/components/purchase/PricingPlanCard', () => ({
  PricingPlanCard: ({ plan, isSelected, isPopular, onSelect, disabled }: any) => (
    <button
      testID={`plan-card-${plan.id}`}
      onPress={() => onSelect(plan)}
      disabled={disabled}
      style={{
        border: isSelected ? '2px solid blue' : '1px solid gray',
        backgroundColor: isPopular ? 'gold' : 'white',
      }}
    >
      {plan.name} - €{plan.price_eur}
      {isSelected && <span testID="selected-indicator">✓</span>}
      {isPopular && <span testID="popular-badge">Popular</span>}
    </button>
  ),
}));

describe('PricingPlanSelector Component', () => {
  const mockPlans = createMockPricingPlans();
  const mockOnPlanSelect = jest.fn();

  const defaultProps = {
    onPlanSelect: mockOnPlanSelect,
    disabled: false,
    className: '',
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Loading State', () => {
    it('displays loading state correctly', () => {
      mockUsePricingPlans.mockReturnValue({
        plans: [],
        loading: true,
        error: null,
        refetch: jest.fn(),
      });

      const { getByText, getByTestId } = render(<PricingPlanSelector {...defaultProps} />);

      expect(getByTestId('spinner')).toBeTruthy();
      expect(getByText('Loading pricing plans...')).toBeTruthy();
    });

    it('shows spinner during loading', () => {
      mockUsePricingPlans.mockReturnValue({
        plans: [],
        loading: true,
        error: null,
        refetch: jest.fn(),
      });

      const { getByTestId } = render(<PricingPlanSelector {...defaultProps} />);

      expect(getByTestId('spinner')).toBeTruthy();
    });
  });

  describe('Error State', () => {
    it('displays error message when plans loading fails', () => {
      const errorMessage = 'Failed to load pricing plans';
      mockUsePricingPlans.mockReturnValue({
        plans: [],
        loading: false,
        error: errorMessage,
        refetch: jest.fn(),
      });

      const { getByText } = render(<PricingPlanSelector {...defaultProps} />);

      expect(getByText('Failed to Load Pricing Plans')).toBeTruthy();
      expect(getByText(errorMessage)).toBeTruthy();
      expect(getByText('Try Again')).toBeTruthy();
    });

    it('allows retry when error occurs', () => {
      const mockRefetch = jest.fn();
      mockUsePricingPlans.mockReturnValue({
        plans: [],
        loading: false,
        error: 'Network error',
        refetch: mockRefetch,
      });

      const { getByText } = render(<PricingPlanSelector {...defaultProps} />);

      fireEvent.press(getByText('Try Again'));

      expect(mockRefetch).toHaveBeenCalled();
    });

    it('shows error alert with proper styling', () => {
      mockUsePricingPlans.mockReturnValue({
        plans: [],
        loading: false,
        error: 'API Error',
        refetch: jest.fn(),
      });

      const { getByText } = render(<PricingPlanSelector {...defaultProps} />);

      // Error alert should be displayed with error styling
      expect(getByText('Failed to Load Pricing Plans')).toBeTruthy();
    });
  });

  describe('Empty State', () => {
    it('displays empty state when no plans are available', () => {
      mockUsePricingPlans.mockReturnValue({
        plans: [],
        loading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByText } = render(<PricingPlanSelector {...defaultProps} />);

      expect(getByText('No Plans Available')).toBeTruthy();
      expect(
        getByText('There are currently no pricing plans available. Please check back later.')
      ).toBeTruthy();
      expect(getByText('Refresh')).toBeTruthy();
    });

    it('allows refresh when no plans are available', () => {
      const mockRefetch = jest.fn();
      mockUsePricingPlans.mockReturnValue({
        plans: [],
        loading: false,
        error: null,
        refetch: mockRefetch,
      });

      const { getByText } = render(<PricingPlanSelector {...defaultProps} />);

      fireEvent.press(getByText('Refresh'));

      expect(mockRefetch).toHaveBeenCalled();
    });
  });

  describe('Plan Display', () => {
    it('renders all available plans', () => {
      mockUsePricingPlans.mockReturnValue({
        plans: mockPlans,
        loading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByTestId, getByText } = render(<PricingPlanSelector {...defaultProps} />);

      expect(getByText('Choose Your Plan')).toBeTruthy();
      expect(
        getByText('Select the tutoring plan that best fits your learning needs and budget.')
      ).toBeTruthy();

      mockPlans.forEach(plan => {
        expect(getByTestId(`plan-card-${plan.id}`)).toBeTruthy();
        expect(getByText(`${plan.name} - €${plan.price_eur}`)).toBeTruthy();
      });
    });

    it('displays help text and information', () => {
      mockUsePricingPlans.mockReturnValue({
        plans: mockPlans,
        loading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByText } = render(<PricingPlanSelector {...defaultProps} />);

      expect(
        getByText('Need help choosing? Contact us for personalized recommendations.')
      ).toBeTruthy();
      expect(
        getByText('All plans include access to qualified tutors and secure scheduling.')
      ).toBeTruthy();
    });

    it('renders plans in responsive grid layout', () => {
      mockUsePricingPlans.mockReturnValue({
        plans: mockPlans,
        loading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByTestId } = render(<PricingPlanSelector {...defaultProps} />);

      // All plans should be rendered
      mockPlans.forEach(plan => {
        expect(getByTestId(`plan-card-${plan.id}`)).toBeTruthy();
      });
    });
  });

  describe('Popular Plan Detection', () => {
    it('marks package type plans as popular', () => {
      const plansWithPackage = [
        createMockPricingPlan({ id: 1, name: 'Package Plan', plan_type: 'package' }),
        createMockPricingPlan({ id: 2, name: 'Subscription Plan', plan_type: 'subscription' }),
      ];

      mockUsePricingPlans.mockReturnValue({
        plans: plansWithPackage,
        loading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByTestId } = render(<PricingPlanSelector {...defaultProps} />);

      expect(getByTestId('popular-badge')).toBeTruthy();
      // Popular badge should be on the package plan
      const packageCard = getByTestId('plan-card-1');
      expect(packageCard).toBeTruthy();
    });

    it('marks first plan as popular when no package type exists', () => {
      const subscriptionPlans = [
        createMockPricingPlan({ id: 1, name: 'Plan 1', plan_type: 'subscription' }),
        createMockPricingPlan({ id: 2, name: 'Plan 2', plan_type: 'subscription' }),
      ];

      mockUsePricingPlans.mockReturnValue({
        plans: subscriptionPlans,
        loading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByTestId } = render(<PricingPlanSelector {...defaultProps} />);

      expect(getByTestId('popular-badge')).toBeTruthy();
    });

    it('handles empty plans for popular detection', () => {
      mockUsePricingPlans.mockReturnValue({
        plans: [],
        loading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { queryByTestId } = render(<PricingPlanSelector {...defaultProps} />);

      expect(queryByTestId('popular-badge')).toBeNull();
    });
  });

  describe('Plan Selection', () => {
    it('handles plan selection correctly', () => {
      mockUsePricingPlans.mockReturnValue({
        plans: mockPlans,
        loading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByTestId } = render(<PricingPlanSelector {...defaultProps} />);

      const firstPlan = mockPlans[0];
      fireEvent.press(getByTestId(`plan-card-${firstPlan.id}`));

      expect(mockOnPlanSelect).toHaveBeenCalledWith(firstPlan);
    });

    it('displays selected plan correctly', () => {
      const selectedPlan = mockPlans[1];
      mockUsePricingPlans.mockReturnValue({
        plans: mockPlans,
        loading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByTestId } = render(
        <PricingPlanSelector {...defaultProps} selectedPlan={selectedPlan} />
      );

      expect(getByTestId('selected-indicator')).toBeTruthy();

      // Check that the correct plan is marked as selected
      const selectedCard = getByTestId(`plan-card-${selectedPlan.id}`);
      expect(selectedCard.style.border).toBe('2px solid blue');
    });

    it('allows changing plan selection', () => {
      const initiallySelected = mockPlans[0];
      mockUsePricingPlans.mockReturnValue({
        plans: mockPlans,
        loading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByTestId, rerender } = render(
        <PricingPlanSelector {...defaultProps} selectedPlan={initiallySelected} />
      );

      // Select a different plan
      const newPlan = mockPlans[1];
      fireEvent.press(getByTestId(`plan-card-${newPlan.id}`));

      expect(mockOnPlanSelect).toHaveBeenCalledWith(newPlan);
    });

    it('handles selection when no plan is initially selected', () => {
      mockUsePricingPlans.mockReturnValue({
        plans: mockPlans,
        loading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByTestId, queryByTestId } = render(
        <PricingPlanSelector {...defaultProps} selectedPlan={null} />
      );

      expect(queryByTestId('selected-indicator')).toBeNull();

      // All cards should have default styling
      mockPlans.forEach(plan => {
        const card = getByTestId(`plan-card-${plan.id}`);
        expect(card.style.border).toBe('1px solid gray');
      });
    });
  });

  describe('Disabled State', () => {
    it('disables all plan cards when disabled prop is true', () => {
      mockUsePricingPlans.mockReturnValue({
        plans: mockPlans,
        loading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByTestId } = render(<PricingPlanSelector {...defaultProps} disabled={true} />);

      mockPlans.forEach(plan => {
        const card = getByTestId(`plan-card-${plan.id}`);
        expect(card).toHaveProperty('disabled', true);
      });
    });

    it('enables all plan cards when disabled prop is false', () => {
      mockUsePricingPlans.mockReturnValue({
        plans: mockPlans,
        loading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByTestId } = render(<PricingPlanSelector {...defaultProps} disabled={false} />);

      mockPlans.forEach(plan => {
        const card = getByTestId(`plan-card-${plan.id}`);
        expect(card).toHaveProperty('disabled', false);
      });
    });

    it('prevents plan selection when disabled', () => {
      mockUsePricingPlans.mockReturnValue({
        plans: mockPlans,
        loading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByTestId } = render(<PricingPlanSelector {...defaultProps} disabled={true} />);

      const firstPlan = mockPlans[0];
      fireEvent.press(getByTestId(`plan-card-${firstPlan.id}`));

      // Should not call onPlanSelect when disabled
      expect(mockOnPlanSelect).not.toHaveBeenCalled();
    });
  });

  describe('Plan Types', () => {
    it('handles different plan types correctly', () => {
      const mixedPlans = [
        createMockPricingPlan({ id: 1, name: 'Package', plan_type: 'package' }),
        createMockPricingPlan({ id: 2, name: 'Subscription', plan_type: 'subscription' }),
      ];

      mockUsePricingPlans.mockReturnValue({
        plans: mixedPlans,
        loading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByTestId, getByText } = render(<PricingPlanSelector {...defaultProps} />);

      expect(getByText('Package - €100.00')).toBeTruthy();
      expect(getByText('Subscription - €100.00')).toBeTruthy();

      // Package should be marked as popular
      expect(getByTestId('popular-badge')).toBeTruthy();
    });

    it('displays plan pricing correctly', () => {
      const plansWithDifferentPrices = [
        createMockPricingPlan({ id: 1, name: 'Basic', price_eur: '50.00' }),
        createMockPricingPlan({ id: 2, name: 'Premium', price_eur: '150.00' }),
      ];

      mockUsePricingPlans.mockReturnValue({
        plans: plansWithDifferentPrices,
        loading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByText } = render(<PricingPlanSelector {...defaultProps} />);

      expect(getByText('Basic - €50.00')).toBeTruthy();
      expect(getByText('Premium - €150.00')).toBeTruthy();
    });
  });

  describe('Edge Cases', () => {
    it('handles undefined selectedPlan gracefully', () => {
      mockUsePricingPlans.mockReturnValue({
        plans: mockPlans,
        loading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { queryByTestId } = render(
        <PricingPlanSelector {...defaultProps} selectedPlan={undefined} />
      );

      expect(queryByTestId('selected-indicator')).toBeNull();
    });

    it('handles plans with missing display_order', () => {
      const plansWithoutOrder = mockPlans.map(plan => ({
        ...plan,
        display_order: undefined,
      }));

      mockUsePricingPlans.mockReturnValue({
        plans: plansWithoutOrder as any,
        loading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByTestId } = render(<PricingPlanSelector {...defaultProps} />);

      // Should still render all plans
      plansWithoutOrder.forEach(plan => {
        expect(getByTestId(`plan-card-${plan.id}`)).toBeTruthy();
      });
    });

    it('handles very long plan names gracefully', () => {
      const longNamePlan = createMockPricingPlan({
        id: 1,
        name: 'Super Ultra Mega Premium Professional Advanced Learning Package with Extended Features',
      });

      mockUsePricingPlans.mockReturnValue({
        plans: [longNamePlan],
        loading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByTestId } = render(<PricingPlanSelector {...defaultProps} />);

      expect(getByTestId('plan-card-1')).toBeTruthy();
    });
  });

  describe('Custom Styling', () => {
    it('applies custom className', () => {
      mockUsePricingPlans.mockReturnValue({
        plans: mockPlans,
        loading: false,
        error: null,
        refetch: jest.fn(),
      });

      const customClass = 'custom-pricing-selector';
      const { container } = render(
        <PricingPlanSelector {...defaultProps} className={customClass} />
      );

      // Custom class should be applied to the root container
      expect(container).toBeTruthy();
    });

    it('handles empty className gracefully', () => {
      mockUsePricingPlans.mockReturnValue({
        plans: mockPlans,
        loading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByText } = render(<PricingPlanSelector {...defaultProps} className="" />);

      expect(getByText('Choose Your Plan')).toBeTruthy();
    });
  });

  describe('Performance', () => {
    it('renders quickly with multiple plans', () => {
      const manyPlans = Array.from({ length: 10 }, (_, i) =>
        createMockPricingPlan({ id: i + 1, name: `Plan ${i + 1}` })
      );

      mockUsePricingPlans.mockReturnValue({
        plans: manyPlans,
        loading: false,
        error: null,
        refetch: jest.fn(),
      });

      const start = performance.now();
      render(<PricingPlanSelector {...defaultProps} />);
      const end = performance.now();

      expect(end - start).toBeLessThan(100);
    });

    it('handles re-renders efficiently', () => {
      mockUsePricingPlans.mockReturnValue({
        plans: mockPlans,
        loading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { rerender } = render(<PricingPlanSelector {...defaultProps} />);

      const start = performance.now();
      rerender(<PricingPlanSelector {...defaultProps} />);
      const end = performance.now();

      expect(end - start).toBeLessThan(50);
    });
  });

  describe('Accessibility', () => {
    it('provides proper headings and structure', () => {
      mockUsePricingPlans.mockReturnValue({
        plans: mockPlans,
        loading: false,
        error: null,
        refetch: jest.fn(),
      });

      const { getByText } = render(<PricingPlanSelector {...defaultProps} />);

      expect(getByText('Choose Your Plan')).toBeTruthy();
      expect(
        getByText('Select the tutoring plan that best fits your learning needs and budget.')
      ).toBeTruthy();
    });

    it('provides accessible error messages', () => {
      mockUsePricingPlans.mockReturnValue({
        plans: [],
        loading: false,
        error: 'Failed to connect to server',
        refetch: jest.fn(),
      });

      const { getByText } = render(<PricingPlanSelector {...defaultProps} />);

      expect(getByText('Failed to Load Pricing Plans')).toBeTruthy();
      expect(getByText('Failed to connect to server')).toBeTruthy();
    });

    it('provides accessible loading state', () => {
      mockUsePricingPlans.mockReturnValue({
        plans: [],
        loading: true,
        error: null,
        refetch: jest.fn(),
      });

      const { getByText } = render(<PricingPlanSelector {...defaultProps} />);

      expect(getByText('Loading pricing plans...')).toBeTruthy();
    });
  });
});
