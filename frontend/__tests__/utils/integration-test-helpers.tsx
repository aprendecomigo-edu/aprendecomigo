/**
 * Integration test helpers for Aprende Comigo platform
 * Provides utilities for cross-platform integration testing
 */

import React from 'react';
import { render, RenderOptions } from '@testing-library/react-native';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Platform detection utilities for tests
export const mockPlatforms = {
  web: () => {
    jest.doMock('react-native/Libraries/Utilities/Platform', () => ({
      OS: 'web',
      select: (spec: any) => spec.web || spec.default,
    }));
  },
  ios: () => {
    jest.doMock('react-native/Libraries/Utilities/Platform', () => ({
      OS: 'ios',
      select: (spec: any) => spec.ios || spec.native || spec.default,
    }));
  },
  android: () => {
    jest.doMock('react-native/Libraries/Utilities/Platform', () => ({
      OS: 'android',
      select: (spec: any) => spec.android || spec.native || spec.default,
    }));
  },
};

// Mock dimensions for different screen sizes
export const mockScreenSizes = {
  mobile: { width: 375, height: 667 },
  tablet: { width: 768, height: 1024 },
  desktop: { width: 1200, height: 800 },
};

/**
 * Sets up mock dimensions for testing responsive behavior
 */
export const setMockDimensions = (dimensions: { width: number; height: number }) => {
  const mockDimensions = {
    get: jest.fn(() => dimensions),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
  };

  jest.doMock('react-native', () => {
    const RN = jest.requireActual('react-native');
    return {
      ...RN,
      Dimensions: mockDimensions,
    };
  });

  return mockDimensions;
};

/**
 * Mock auth context for integration tests
 */
interface MockAuthContextValue {
  user: any;
  isAuthenticated: boolean;
  login: jest.Mock;
  logout: jest.Mock;
  loading: boolean;
}

export const createMockAuthContext = (
  overrides: Partial<MockAuthContextValue> = {},
): MockAuthContextValue => ({
  user: { id: 'test-user', email: 'test@example.com', role: 'student' },
  isAuthenticated: true,
  login: jest.fn(),
  logout: jest.fn(),
  loading: false,
  ...overrides,
});

/**
 * Mock navigation for integration tests
 */
export const createMockNavigation = () => ({
  navigate: jest.fn(),
  goBack: jest.fn(),
  reset: jest.fn(),
  setParams: jest.fn(),
  dispatch: jest.fn(),
  setOptions: jest.fn(),
  isFocused: jest.fn(() => true),
  addListener: jest.fn(() => jest.fn()),
});

/**
 * Creates a test wrapper with all necessary providers
 */
interface TestWrapperProps {
  children: React.ReactNode;
  authContext?: Partial<MockAuthContextValue>;
  queryClient?: QueryClient;
  initialRoute?: string;
}

export const TestWrapper: React.FC<TestWrapperProps> = ({
  children,
  authContext = {},
  queryClient,
  initialRoute = '/',
}) => {
  const testQueryClient =
    queryClient ||
    new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });

  const mockAuth = createMockAuthContext(authContext);

  // Mock AuthContext Provider
  const AuthContextMock = React.createContext(mockAuth);

  return (
    <QueryClientProvider client={testQueryClient}>
      <AuthContextMock.Provider value={mockAuth}>{children}</AuthContextMock.Provider>
    </QueryClientProvider>
  );
};

/**
 * Custom render function with TestWrapper
 */
export const renderWithProviders = (
  ui: React.ReactElement,
  options: RenderOptions & {
    authContext?: Partial<MockAuthContextValue>;
    queryClient?: QueryClient;
    initialRoute?: string;
  } = {},
) => {
  const { authContext, queryClient, initialRoute, ...renderOptions } = options;

  const Wrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
    <TestWrapper authContext={authContext} queryClient={queryClient} initialRoute={initialRoute}>
      {children}
    </TestWrapper>
  );

  return render(ui, { wrapper: Wrapper, ...renderOptions });
};

/**
 * Utility for testing responsive components across platforms
 */
export const testAcrossPlatforms = (
  testFn: (platform: string) => void,
  platforms: string[] = ['web', 'ios', 'android'],
) => {
  platforms.forEach(platform => {
    describe(`on ${platform}`, () => {
      beforeEach(() => {
        // Set up platform mock
        if (platform === 'web') mockPlatforms.web();
        else if (platform === 'ios') mockPlatforms.ios();
        else if (platform === 'android') mockPlatforms.android();
      });

      testFn(platform);
    });
  });
};

/**
 * Utility for testing responsive behavior across screen sizes
 */
export const testAcrossScreenSizes = (
  testFn: (screenSize: string, dimensions: { width: number; height: number }) => void,
) => {
  Object.entries(mockScreenSizes).forEach(([sizeName, dimensions]) => {
    describe(`on ${sizeName} screen`, () => {
      beforeEach(() => {
        setMockDimensions(dimensions);
      });

      testFn(sizeName, dimensions);
    });
  });
};

/**
 * Mock API responses for integration tests
 */
export const mockApiResponses = {
  success: (data: any) => Promise.resolve({ ok: true, json: () => Promise.resolve(data) }),
  error: (status: number, message: string) =>
    Promise.reject(new Error(`API Error ${status}: ${message}`)),
  loading: () => new Promise(() => {}), // Never resolves, simulates loading state
};

/**
 * Mock WebSocket for integration tests
 */
export const createIntegrationWebSocketMock = () => {
  const messageHandlers: ((data: any) => void)[] = [];
  const errorHandlers: ((error: Error) => void)[] = [];
  const connectHandlers: (() => void)[] = [];
  const disconnectHandlers: (() => void)[] = [];

  return {
    connect: jest.fn(),
    disconnect: jest.fn(),
    send: jest.fn(),
    onMessage: jest.fn(handler => messageHandlers.push(handler)),
    onError: jest.fn(handler => errorHandlers.push(handler)),
    onConnect: jest.fn(handler => connectHandlers.push(handler)),
    onDisconnect: jest.fn(handler => disconnectHandlers.push(handler)),
    isConnected: jest.fn(() => true),

    // Test utilities
    simulateMessage: (data: any) => messageHandlers.forEach(handler => handler(data)),
    simulateError: (error: Error) => errorHandlers.forEach(handler => handler(error)),
    simulateConnect: () => connectHandlers.forEach(handler => handler()),
    simulateDisconnect: () => disconnectHandlers.forEach(handler => handler()),
  };
};

/**
 * Utility to wait for async operations in tests
 */
export const waitFor = (conditionFn: () => boolean, timeout: number = 1000): Promise<void> => {
  return new Promise((resolve, reject) => {
    const startTime = Date.now();

    const check = () => {
      if (conditionFn()) {
        resolve();
        return;
      }

      if (Date.now() - startTime > timeout) {
        reject(new Error(`Condition not met within ${timeout}ms`));
        return;
      }

      setTimeout(check, 10);
    };

    check();
  });
};

/**
 * Mock form data for testing
 */
export const mockFormData = {
  signUp: {
    email: 'test@example.com',
    firstName: 'Test',
    lastName: 'User',
    userType: 'student' as const,
  },
  signIn: {
    email: 'test@example.com',
  },
  verifyCode: {
    code: '123456',
  },
  purchase: {
    amount: 50,
    hours: 10,
    paymentMethodId: 'pm_test_123',
  },
};

/**
 * Utility to simulate user interactions
 */
export const userActions = {
  fillForm: async (getByTestId: any, formData: Record<string, string>) => {
    for (const [field, value] of Object.entries(formData)) {
      const input = getByTestId(`input-${field}`);
      // Simulate user typing
      input.props.onChangeText?.(value);
    }
  },

  submitForm: async (getByTestId: any, formTestId: string = 'submit-button') => {
    const submitButton = getByTestId(formTestId);
    submitButton.props.onPress?.();
  },
};

/**
 * Mock payment method for Stripe testing
 */
export const mockStripeSetup = () => {
  const mockStripe = {
    confirmPayment: jest.fn(),
    createPaymentMethod: jest.fn(),
    retrievePaymentIntent: jest.fn(),
  };

  const mockElements = {
    getElement: jest.fn(),
    create: jest.fn(),
  };

  // Set up global mocks
  global.__stripeUseStripeMock = jest.fn(() => mockStripe);
  global.__stripeUseElementsMock = jest.fn(() => mockElements);

  return { mockStripe, mockElements };
};

/**
 * Cleanup utilities for after each test
 */
export const cleanup = () => {
  // Clear WebSocket mocks
  global.__mockWebSocketClients = [];
  global.__lastMockWebSocketClient = null;
  global.__webSocketGlobalFailure = false;

  // Clear Stripe mocks
  global.__stripeUseStripeMock = jest.fn();
  global.__stripeUseElementsMock = jest.fn();

  // Clear any timeout/intervals
  jest.clearAllTimers();
};
