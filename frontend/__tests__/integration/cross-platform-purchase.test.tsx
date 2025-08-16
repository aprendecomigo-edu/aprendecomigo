/**
 * Cross-Platform Purchase Flow Integration Tests
 *
 * Tests purchase flow behavior across web, iOS, and Android platforms,
 * ensuring consistent experience while respecting platform differences.
 */

import React from 'react';
import { Platform, Dimensions, AppState } from 'react-native';

import {
  createMockPricingPlans,
  createMockStripeConfig,
  createMockPurchaseInitiationResponse,
  createMockStripe,
  createMockElements,
  createMockStripeSuccess,
  createMockStripeError,
  createMockPaymentMethods,
  VALID_TEST_DATA,
  cleanupMocks,
} from '@/__tests__/utils/payment-test-utils';
import { render, fireEvent, waitFor, act } from '@/__tests__/utils/test-utils';
import { PaymentMethodApiClient } from '@/api/paymentMethodApi';
import { PurchaseApiClient } from '@/api/purchaseApi';
import { PurchaseFlow } from '@/components/purchase/PurchaseFlow';

// Mock APIs
jest.mock('@/api/purchaseApi');
jest.mock('@/api/paymentMethodApi');
const mockPurchaseApiClient = PurchaseApiClient as jest.Mocked<typeof PurchaseApiClient>;
const mockPaymentMethodApiClient = PaymentMethodApiClient as jest.Mocked<
  typeof PaymentMethodApiClient
>;

// Mock Stripe
jest.mock('@stripe/react-stripe-js', () => ({
  Elements: ({ children }: any) => children,
  PaymentElement: () => <div testID="stripe-payment-element">Payment Element</div>,
  useStripe: () => mockStripe,
  useElements: () => mockElements,
}));

// Mock router
const mockPush = jest.fn();
const mockReplace = jest.fn();
jest.mock('expo-router', () => ({
  __esModule: true,
  default: () => ({ push: mockPush, replace: mockReplace }),
}));

// Platform-specific mocks
const mockDimensions = {
  get: jest.fn(),
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
};

// Global test data
const mockPlans = createMockPricingPlans();
const mockStripe = createMockStripe();
const mockElements = createMockElements();

describe('Cross-Platform Purchase Flow Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    cleanupMocks();

    // Setup successful API responses
    mockPurchaseApiClient.getStripeConfig.mockResolvedValue(createMockStripeConfig());
    mockPurchaseApiClient.getPricingPlans.mockResolvedValue(mockPlans);
    mockPaymentMethodApiClient.getPaymentMethods.mockResolvedValue(createMockPaymentMethods());

    // Reset platform and dimensions mocks
    mockDimensions.get.mockReset();
    mockDimensions.addEventListener.mockReset();
    mockDimensions.removeEventListener.mockReset();
  });

  describe('Web Platform Specific Features', () => {
    beforeEach(() => {
      // Mock web platform
      Platform.OS = 'web';
      Platform.select = jest.fn((platforms: any) => platforms.web || platforms.default);

      // Mock window object
      Object.defineProperty(global, 'window', {
        value: {
          location: { reload: jest.fn(), href: 'https://app.aprendecomigo.com' },
          history: { pushState: jest.fn(), replaceState: jest.fn() },
          navigator: { userAgent: 'Mozilla/5.0', onLine: true },
          localStorage: {
            getItem: jest.fn(),
            setItem: jest.fn(),
            removeItem: jest.fn(),
          },
          sessionStorage: {
            getItem: jest.fn(),
            setItem: jest.fn(),
            removeItem: jest.fn(),
          },
          addEventListener: jest.fn(),
          removeEventListener: jest.fn(),
          dispatchEvent: jest.fn(),
        },
        writable: true,
      });
    });

    it('handles web-specific responsive design breakpoints', async () => {
      // Mock different screen sizes
      const testScreenSizes = [
        { width: 320, height: 568, name: 'mobile' },
        { width: 768, height: 1024, name: 'tablet' },
        { width: 1920, height: 1080, name: 'desktop' },
      ];

      for (const screenSize of testScreenSizes) {
        mockDimensions.get.mockReturnValue({
          window: screenSize,
          screen: screenSize,
        });

        const { getByText, getByPlaceholderText, queryByTestId } = render(<PurchaseFlow />);

        await waitFor(() => {
          expect(getByText('Select Plan')).toBeTruthy();
        });

        // Desktop should show plans in grid
        if (screenSize.name === 'desktop') {
          expect(queryByTestId('plans-grid-layout')).toBeTruthy();
        } else {
          expect(queryByTestId('plans-list-layout')).toBeTruthy();
        }

        // Complete flow should work on all screen sizes
        fireEvent.press(getByText('Standard Package'));
        await waitFor(() => getByText('Student Information'));

        fireEvent.changeText(getByPlaceholderText('Student name'), VALID_TEST_DATA.studentName);
        fireEvent.changeText(getByPlaceholderText('Student email'), VALID_TEST_DATA.studentEmail);

        // Form layout should adapt to screen size
        if (screenSize.name === 'desktop') {
          expect(queryByTestId('horizontal-form-layout')).toBeTruthy();
        } else {
          expect(queryByTestId('vertical-form-layout')).toBeTruthy();
        }
      }
    });

    it('handles web browser navigation and URL management', async () => {
      const { getByText, getByPlaceholderText } = render(<PurchaseFlow />);

      // Mock history API
      const mockHistory = {
        pushState: jest.fn(),
        replaceState: jest.fn(),
      };
      Object.defineProperty(window, 'history', { value: mockHistory });

      // Plan selection should update URL
      await waitFor(() => getByText('Select Plan'));
      fireEvent.press(getByText('Standard Package'));

      await waitFor(() => {
        expect(mockHistory.pushState).toHaveBeenCalledWith(
          expect.any(Object),
          '',
          expect.stringContaining('/purchase/user-info'),
        );
      });

      // Form submission should update URL
      await waitFor(() => getByText('Student Information'));
      fireEvent.changeText(getByPlaceholderText('Student name'), VALID_TEST_DATA.studentName);
      fireEvent.changeText(getByPlaceholderText('Student email'), VALID_TEST_DATA.studentEmail);

      mockPurchaseApiClient.initiatePurchase.mockResolvedValue(
        createMockPurchaseInitiationResponse(),
      );
      fireEvent.press(getByText('Continue to Payment'));

      await waitFor(() => {
        expect(mockHistory.pushState).toHaveBeenCalledWith(
          expect.any(Object),
          '',
          expect.stringContaining('/purchase/payment'),
        );
      });
    });

    it('handles web-specific keyboard shortcuts and accessibility', async () => {
      const { getByText, getByPlaceholderText } = render(<PurchaseFlow />);

      await waitFor(() => getByText('Select Plan'));

      // Test keyboard navigation
      const planButton = getByText('Standard Package');

      // Simulate Enter key press
      fireEvent.press(planButton);
      await waitFor(() => getByText('Student Information'));

      const nameInput = getByPlaceholderText('Student name');
      const emailInput = getByPlaceholderText('Student email');

      // Test Tab navigation between inputs
      fireEvent.focus(nameInput);
      fireEvent.changeText(nameInput, VALID_TEST_DATA.studentName);

      // Simulate Tab key to move to next field
      fireEvent.focus(emailInput);
      fireEvent.changeText(emailInput, VALID_TEST_DATA.studentEmail);

      // Test form submission with Enter key
      const continueButton = getByText('Continue to Payment');

      // Should be accessible via keyboard
      expect(continueButton).toHaveProperty('accessible', true);
      expect(continueButton).toHaveProperty('accessibilityRole', 'button');
    });

    it('handles web localStorage state persistence', async () => {
      const mockLocalStorage = window.localStorage as jest.Mocked<Storage>;

      const { getByText, getByPlaceholderText } = render(<PurchaseFlow />);

      // Fill form
      await waitFor(() => getByText('Select Plan'));
      fireEvent.press(getByText('Standard Package'));

      await waitFor(() => getByText('Student Information'));
      fireEvent.changeText(getByPlaceholderText('Student name'), VALID_TEST_DATA.studentName);
      fireEvent.changeText(getByPlaceholderText('Student email'), VALID_TEST_DATA.studentEmail);

      // Verify state is saved to localStorage
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
        'purchase_flow_state',
        JSON.stringify(
          expect.objectContaining({
            step: 'user-info',
            formData: expect.objectContaining({
              selectedPlan: expect.any(Object),
              studentName: VALID_TEST_DATA.studentName,
              studentEmail: VALID_TEST_DATA.studentEmail,
            }),
          }),
        ),
      );
    });

    afterEach(() => {
      // Clean up web mocks
      delete (global as any).window;
    });
  });

  describe('iOS Platform Specific Features', () => {
    beforeEach(() => {
      // Mock iOS platform
      Platform.OS = 'ios';
      Platform.Version = '17.0';
      Platform.select = jest.fn(
        (platforms: any) => platforms.ios || platforms.native || platforms.default,
      );
    });

    it('handles iOS safe area and navigation patterns', async () => {
      // Mock safe area dimensions
      mockDimensions.get.mockReturnValue({
        window: { width: 390, height: 844 }, // iPhone 14
        screen: { width: 390, height: 844 },
      });

      const { getByText, getByTestId, queryByTestId } = render(<PurchaseFlow />);

      await waitFor(() => {
        expect(getByText('Select Plan')).toBeTruthy();
        // Should use iOS safe area wrapper
        expect(queryByTestId('ios-safe-area-view')).toBeTruthy();
      });

      // iOS-specific navigation should be present
      expect(queryByTestId('ios-navigation-bar')).toBeTruthy();
      expect(queryByTestId('back-button-ios')).toBeTruthy();
    });

    it('handles iOS payment methods and Apple Pay integration', async () => {
      // Mock Apple Pay availability
      Object.defineProperty(Platform, 'isIOS', { value: true });

      const { getByText, getByPlaceholderText, queryByText } = render(<PurchaseFlow />);

      // Complete flow to payment step
      await waitFor(() => getByText('Select Plan'));
      fireEvent.press(getByText('Standard Package'));

      await waitFor(() => getByText('Student Information'));
      fireEvent.changeText(getByPlaceholderText('Student name'), VALID_TEST_DATA.studentName);
      fireEvent.changeText(getByPlaceholderText('Student email'), VALID_TEST_DATA.studentEmail);
      fireEvent.press(getByText('Continue to Payment'));

      await waitFor(() => {
        expect(getByText('Payment')).toBeTruthy();
        // Should show Apple Pay option on iOS
        expect(queryByText('Pay with Apple Pay')).toBeTruthy();
        expect(queryByText('Pay with Card')).toBeTruthy();
      });

      // Test Apple Pay flow
      mockStripe.confirmPayment.mockResolvedValue(createMockStripeSuccess());

      if (queryByText('Pay with Apple Pay')) {
        fireEvent.press(getByText('Pay with Apple Pay'));

        await waitFor(() => {
          expect(getByText('Purchase Successful!')).toBeTruthy();
        });
      }
    });

    it('handles iOS app lifecycle and background/foreground transitions', async () => {
      const { getByText, getByPlaceholderText } = render(<PurchaseFlow />);

      // Start purchase flow
      await waitFor(() => getByText('Select Plan'));
      fireEvent.press(getByText('Standard Package'));

      await waitFor(() => getByText('Student Information'));
      fireEvent.changeText(getByPlaceholderText('Student name'), VALID_TEST_DATA.studentName);
      fireEvent.changeText(getByPlaceholderText('Student email'), VALID_TEST_DATA.studentEmail);

      // Simulate iOS app backgrounding
      act(() => {
        AppState.currentState = 'background';
        // Trigger iOS-specific memory warning
        require('react-native').DeviceEventEmitter?.emit('memoryWarning');
      });

      // App returns to foreground
      act(() => {
        AppState.currentState = 'active';
        // iOS should restore state from secure storage
      });

      // Form should maintain state
      await waitFor(() => {
        expect(getByPlaceholderText('Student name')).toHaveProperty(
          'value',
          VALID_TEST_DATA.studentName,
        );
        expect(getByPlaceholderText('Student email')).toHaveProperty(
          'value',
          VALID_TEST_DATA.studentEmail,
        );
      });
    });

    it('handles iOS haptic feedback and user interactions', async () => {
      // Mock iOS haptic feedback
      const mockHaptic = {
        impactAsync: jest.fn(),
        notificationAsync: jest.fn(),
        selectionAsync: jest.fn(),
      };
      jest.doMock('expo-haptics', () => mockHaptic);

      const { getByText, getByPlaceholderText } = render(<PurchaseFlow />);

      // Plan selection should trigger selection haptic
      await waitFor(() => getByText('Select Plan'));
      fireEvent.press(getByText('Standard Package'));

      expect(mockHaptic.selectionAsync).toHaveBeenCalled();

      // Successful purchase should trigger success haptic
      await waitFor(() => getByText('Student Information'));
      fireEvent.changeText(getByPlaceholderText('Student name'), VALID_TEST_DATA.studentName);
      fireEvent.changeText(getByPlaceholderText('Student email'), VALID_TEST_DATA.studentEmail);

      mockPurchaseApiClient.initiatePurchase.mockResolvedValue(
        createMockPurchaseInitiationResponse(),
      );
      fireEvent.press(getByText('Continue to Payment'));

      await waitFor(() => getByText('Payment'));

      mockStripe.confirmPayment.mockResolvedValue(createMockStripeSuccess());
      fireEvent.press(getByText(/Pay €/));

      await waitFor(() => {
        expect(getByText('Purchase Successful!')).toBeTruthy();
        expect(mockHaptic.notificationAsync).toHaveBeenCalledWith('success');
      });
    });
  });

  describe('Android Platform Specific Features', () => {
    beforeEach(() => {
      // Mock Android platform
      Platform.OS = 'android';
      Platform.Version = 33; // Android 13
      Platform.select = jest.fn(
        (platforms: any) => platforms.android || platforms.native || platforms.default,
      );
    });

    it('handles Android material design and navigation', async () => {
      // Mock Android screen dimensions
      mockDimensions.get.mockReturnValue({
        window: { width: 412, height: 892 }, // Pixel 6
        screen: { width: 412, height: 915 }, // Include navigation bar
      });

      const { getByText, queryByTestId } = render(<PurchaseFlow />);

      await waitFor(() => {
        expect(getByText('Select Plan')).toBeTruthy();
        // Should use Android material design components
        expect(queryByTestId('android-app-bar')).toBeTruthy();
        expect(queryByTestId('android-fab')).toBeTruthy();
      });

      // Material design elevation and shadows should be applied
      expect(queryByTestId('material-card-elevation')).toBeTruthy();
    });

    it('handles Android payment methods and Google Pay integration', async () => {
      const { getByText, getByPlaceholderText, queryByText } = render(<PurchaseFlow />);

      // Complete flow to payment step
      await waitFor(() => getByText('Select Plan'));
      fireEvent.press(getByText('Standard Package'));

      await waitFor(() => getByText('Student Information'));
      fireEvent.changeText(getByPlaceholderText('Student name'), VALID_TEST_DATA.studentName);
      fireEvent.changeText(getByPlaceholderText('Student email'), VALID_TEST_DATA.studentEmail);
      fireEvent.press(getByText('Continue to Payment'));

      await waitFor(() => {
        expect(getByText('Payment')).toBeTruthy();
        // Should show Google Pay option on Android
        expect(queryByText('Pay with Google Pay')).toBeTruthy();
        expect(queryByText('Pay with Card')).toBeTruthy();
      });

      // Test Google Pay flow
      mockStripe.confirmPayment.mockResolvedValue(createMockStripeSuccess());

      if (queryByText('Pay with Google Pay')) {
        fireEvent.press(getByText('Pay with Google Pay'));

        await waitFor(() => {
          expect(getByText('Purchase Successful!')).toBeTruthy();
        });
      }
    });

    it('handles Android hardware back button', async () => {
      const { getByText, getByPlaceholderText } = render(<PurchaseFlow />);

      // Navigate through flow
      await waitFor(() => getByText('Select Plan'));
      fireEvent.press(getByText('Standard Package'));
      await waitFor(() => getByText('Student Information'));

      // Mock Android hardware back press
      const mockBackHandler = {
        addEventListener: jest.fn((event, handler) => {
          if (event === 'hardwareBackPress') {
            // Simulate back press
            const shouldPreventDefault = handler();
            return { remove: jest.fn() };
          }
        }),
        removeEventListener: jest.fn(),
      };

      jest.doMock('react-native', () => ({
        ...jest.requireActual('react-native'),
        BackHandler: mockBackHandler,
      }));

      // Back press should go to previous step
      act(() => {
        const backPressHandler = mockBackHandler.addEventListener.mock.calls[0][1];
        const preventDefault = backPressHandler();
        expect(preventDefault).toBe(true); // Should handle the back press
      });

      // Should go back to plan selection
      await waitFor(() => {
        expect(getByText('Select Plan')).toBeTruthy();
      });
    });

    it('handles Android system UI and immersive mode', async () => {
      // Mock Android system bars
      const mockStatusBar = {
        setHidden: jest.fn(),
        setBackgroundColor: jest.fn(),
        setBarStyle: jest.fn(),
      };

      jest.doMock('react-native', () => ({
        ...jest.requireActual('react-native'),
        StatusBar: mockStatusBar,
      }));

      const { getByText } = render(<PurchaseFlow />);

      await waitFor(() => {
        expect(getByText('Select Plan')).toBeTruthy();
        // Should configure status bar for purchase flow
        expect(mockStatusBar.setBarStyle).toHaveBeenCalledWith('dark-content');
        expect(mockStatusBar.setBackgroundColor).toHaveBeenCalledWith('#ffffff');
      });
    });

    it('handles Android permissions and security features', async () => {
      // Mock Android permissions API
      const mockPermissions = {
        request: jest.fn(),
        check: jest.fn(),
        PERMISSIONS: {
          ANDROID: {
            CAMERA: 'android.permission.CAMERA',
            WRITE_EXTERNAL_STORAGE: 'android.permission.WRITE_EXTERNAL_STORAGE',
          },
        },
        RESULTS: {
          GRANTED: 'granted',
          DENIED: 'denied',
        },
      };

      jest.doMock('react-native-permissions', () => mockPermissions);

      const { getByText, getByPlaceholderText } = render(<PurchaseFlow />);

      // Complete to payment step
      await waitFor(() => getByText('Select Plan'));
      fireEvent.press(getByText('Standard Package'));

      await waitFor(() => getByText('Student Information'));
      fireEvent.changeText(getByPlaceholderText('Student name'), VALID_TEST_DATA.studentName);
      fireEvent.changeText(getByPlaceholderText('Student email'), VALID_TEST_DATA.studentEmail);
      fireEvent.press(getByText('Continue to Payment'));

      await waitFor(() => getByText('Payment'));

      // Android secure payment should be enabled
      expect(queryByTestId('android-secure-payment')).toBeTruthy();
    });
  });

  describe('Cross-Platform Consistency Tests', () => {
    it('maintains consistent UX across all platforms', async () => {
      const platforms = ['web', 'ios', 'android'];

      for (const platform of platforms) {
        // Set platform
        Platform.OS = platform as any;
        Platform.select = jest.fn(
          (platforms: any) => platforms[platform] || platforms.native || platforms.default,
        );

        const { getByText, getByPlaceholderText } = render(<PurchaseFlow />);

        // Core flow should be identical
        await waitFor(() => getByText('Select Plan'));
        fireEvent.press(getByText('Standard Package'));

        await waitFor(() => getByText('Student Information'));
        expect(getByText('Step 2 of 4')).toBeTruthy();

        fireEvent.changeText(getByPlaceholderText('Student name'), VALID_TEST_DATA.studentName);
        fireEvent.changeText(getByPlaceholderText('Student email'), VALID_TEST_DATA.studentEmail);
        fireEvent.press(getByText('Continue to Payment'));

        mockPurchaseApiClient.initiatePurchase.mockResolvedValue(
          createMockPurchaseInitiationResponse(),
        );
        await waitFor(() => {
          expect(getByText('Payment')).toBeTruthy();
          expect(getByText('Step 3 of 4')).toBeTruthy();
        });

        mockStripe.confirmPayment.mockResolvedValue(createMockStripeSuccess());
        fireEvent.press(getByText(/Pay €/));

        await waitFor(() => {
          expect(getByText('Purchase Successful!')).toBeTruthy();
          expect(getByText('Step 4 of 4')).toBeTruthy();
        });
      }
    });

    it('handles platform-specific error messages consistently', async () => {
      const platforms = ['web', 'ios', 'android'];

      for (const platform of platforms) {
        Platform.OS = platform as any;

        // Mock platform-specific error
        let expectedErrorMessage = 'Payment failed';
        if (platform === 'ios') expectedErrorMessage = 'Apple Pay not available';
        if (platform === 'android') expectedErrorMessage = 'Google Pay not available';
        if (platform === 'web') expectedErrorMessage = 'Browser not supported';

        mockPurchaseApiClient.getPricingPlans.mockRejectedValue(new Error(expectedErrorMessage));

        const { getByText } = render(<PurchaseFlow />);

        await waitFor(() => {
          expect(getByText('Error')).toBeTruthy();
          expect(getByText(expectedErrorMessage)).toBeTruthy();
        });

        // Reset for next iteration
        mockPurchaseApiClient.getPricingPlans.mockResolvedValue(mockPlans);
      }
    });

    it('ensures accessibility standards across platforms', async () => {
      const platforms = ['web', 'ios', 'android'];

      for (const platform of platforms) {
        Platform.OS = platform as any;

        const { getByRole, getByLabelText, getByText } = render(<PurchaseFlow />);

        await waitFor(() => {
          // All platforms should have accessible elements
          expect(getByRole('heading')).toBeTruthy();

          // Platform-specific accessibility
          if (platform === 'web') {
            expect(getByRole('button', { name: /Standard Package/i })).toBeTruthy();
          } else {
            expect(getByLabelText('Select Standard Package')).toBeTruthy();
          }
        });
      }
    });
  });

  afterEach(() => {
    cleanupMocks();
    // Reset platform mocks
    Platform.OS = 'web'; // Reset to default
    jest.clearAllMocks();
  });
});
