/**
 * Dependency Injection Testing Utilities
 * 
 * This file provides comprehensive utilities for testing with dependency injection,
 * including mock creation, test providers, and builder patterns.
 */

import React, { ComponentType } from 'react';
import { 
  Dependencies, 
  MockDependencies, 
  PartialDependencies,
  AuthApiService,
  StorageService,
  AnalyticsService,
  RouterService,
  ToastService,
  AuthContextService,
  OnboardingApiService
} from './types';
import type { PaymentServiceInterface, BalanceServiceInterface } from '../business/types';
import { DependencyProvider } from './context';

// ==================== Mock Creation Functions ====================

export const createMockDependencies = (): MockDependencies => {
  return {
    authApi: {
      requestEmailCode: jest.fn(),
      verifyEmailCode: jest.fn(),
      createUser: jest.fn(),
    },
    storageService: {
      setItem: jest.fn(),
      getItem: jest.fn(),
      removeItem: jest.fn(),
    },
    analyticsService: {
      track: jest.fn(),
      identify: jest.fn(),
      screen: jest.fn(),
    },
    routerService: {
      push: jest.fn(),
      back: jest.fn(),
      replace: jest.fn(),
    },
    toastService: {
      showToast: jest.fn(),
    },
    authContextService: {
      checkAuthStatus: jest.fn(),
      setUserProfile: jest.fn(),
      userProfile: null,
    },
    onboardingApiService: {
      getNavigationPreferences: jest.fn(),
      getOnboardingProgress: jest.fn(),
    },
    paymentService: {
      processQuickTopUp: jest.fn(),
      calculatePackagePrice: jest.fn(),
      validatePaymentMethod: jest.fn(),
    },
    balanceService: {
      calculateRemainingHours: jest.fn(),
      getBalanceStatus: jest.fn(),
      predictExpiryDate: jest.fn(),
    },
  };
};

export const createPartialMockDependencies = (
  partialDeps: PartialDependencies
): PartialDependencies => {
  return partialDeps;
};

// ==================== Higher-Order Component for Testing ====================

export const withMockDependencies = <P extends object>(
  Component: ComponentType<P>,
  dependencies: Dependencies
) => {
  const WrappedComponent = (props: P) => {
    return React.createElement(
      DependencyProvider,
      { dependencies },
      React.createElement(Component, props)
    );
  };
  
  WrappedComponent.displayName = `withMockDependencies(${Component.displayName || Component.name})`;
  
  return WrappedComponent;
};

// ==================== Mock Dependency Builder ====================

export class MockDependencyBuilder {
  private dependencies: Partial<Dependencies> = {};

  withAuthApi(authApi: AuthApiService): this {
    this.dependencies.authApi = authApi;
    return this;
  }

  withStorageService(storageService: StorageService): this {
    this.dependencies.storageService = storageService;
    return this;
  }

  withAnalyticsService(analyticsService: AnalyticsService): this {
    this.dependencies.analyticsService = analyticsService;
    return this;
  }

  withRouterService(routerService: RouterService): this {
    this.dependencies.routerService = routerService;
    return this;
  }

  withToastService(toastService: ToastService): this {
    this.dependencies.toastService = toastService;
    return this;
  }

  withAuthContextService(authContextService: AuthContextService): this {
    this.dependencies.authContextService = authContextService;
    return this;
  }

  withOnboardingApiService(onboardingApiService: OnboardingApiService): this {
    this.dependencies.onboardingApiService = onboardingApiService;
    return this;
  }

  withPaymentService(paymentService: PaymentServiceInterface): this {
    this.dependencies.paymentService = paymentService;
    return this;
  }

  withBalanceService(balanceService: BalanceServiceInterface): this {
    this.dependencies.balanceService = balanceService;
    return this;
  }

  reset(): this {
    this.dependencies = {};
    return this;
  }

  build(): Dependencies {
    const mockDeps = createMockDependencies();
    
    return {
      authApi: this.dependencies.authApi || mockDeps.authApi,
      storageService: this.dependencies.storageService || mockDeps.storageService,
      analyticsService: this.dependencies.analyticsService || mockDeps.analyticsService,
      routerService: this.dependencies.routerService || mockDeps.routerService,
      toastService: this.dependencies.toastService || mockDeps.toastService,
      authContextService: this.dependencies.authContextService || mockDeps.authContextService,
      onboardingApiService: this.dependencies.onboardingApiService || mockDeps.onboardingApiService,
      paymentService: this.dependencies.paymentService || mockDeps.paymentService,
      balanceService: this.dependencies.balanceService || mockDeps.balanceService,
    };
  }
}

// ==================== Test Dependency Provider ====================

interface TestDependencyProviderProps {
  children: React.ReactNode;
  dependencies: Dependencies;
  overrides?: Partial<Dependencies>;
}

export const TestDependencyProvider: React.FC<TestDependencyProviderProps> = ({
  children,
  dependencies,
  overrides = {},
}) => {
  const finalDependencies = {
    ...dependencies,
    ...overrides,
  };

  return React.createElement(
    DependencyProvider,
    { dependencies: finalDependencies },
    children
  );
};

// ==================== Test Utilities and Helpers ====================

export const createTestDependencyProvider = (dependencies: Dependencies) => {
  return ({ children }: { children: React.ReactNode }) => {
    return React.createElement(DependencyProvider, { dependencies }, children);
  };
};

export const createMockDependencyProvider = () => {
  const mockDependencies = createMockDependencies();
  return {
    Provider: ({ children }: { children: React.ReactNode }) => 
      React.createElement(DependencyProvider, { dependencies: mockDependencies }, children),
    mocks: mockDependencies,
  };
};

// ==================== Testing Patterns and Utilities ====================

export const setupTestDependencies = (overrides: Partial<Dependencies> = {}): Dependencies => {
  const baseMocks = createMockDependencies();
  return {
    ...baseMocks,
    ...overrides,
  } as Dependencies;
};

export const createAuthScenarioMocks = () => {
  const mockUser = {
    id: 1,
    email: 'test@example.com',
    name: 'Test User',
    user_type: 'student',
  };

  return {
    successfulAuth: createMockDependencies(),
    failedAuth: (() => {
      const mocks = createMockDependencies();
      mocks.authApi.verifyEmailCode.mockRejectedValue(new Error('Invalid code'));
      return mocks;
    })(),
    newUserAuth: (() => {
      const mocks = createMockDependencies();
      mocks.authApi.verifyEmailCode.mockResolvedValue({
        user: mockUser,
        is_new_user: true,
        access_token: 'token',
      });
      return mocks;
    })(),
    mockUser,
  };
};

export const createNetworkErrorScenario = (service: keyof Dependencies, method: string) => {
  const mocks = createMockDependencies();
  const networkError = new Error('Network error');
  
  if (service in mocks && method in mocks[service]) {
    (mocks[service] as any)[method].mockRejectedValue(networkError);
  }
  
  return { mocks, networkError };
};

// ==================== Jest Setup Helpers ====================

export const mockDependenciesBeforeEach = () => {
  let mockDependencies: MockDependencies;

  beforeEach(() => {
    jest.clearAllMocks();
    mockDependencies = createMockDependencies();
  });

  const getMocks = () => mockDependencies;

  return { getMocks };
};

// ==================== Type Guards and Utilities ====================

export const isMockFunction = (fn: any): fn is jest.MockedFunction<any> => {
  return jest.isMockFunction(fn);
};

export const assertMockCalled = (
  mockFn: jest.MockedFunction<any>,
  expectedCalls: number = 1
) => {
  expect(mockFn).toHaveBeenCalledTimes(expectedCalls);
};

export const assertMockCalledWith = (
  mockFn: jest.MockedFunction<any>,
  ...expectedArgs: any[]
) => {
  expect(mockFn).toHaveBeenCalledWith(...expectedArgs);
};

// ==================== Advanced Testing Patterns ====================

export const createAsyncTestScenario = (
  serviceName: keyof Dependencies,
  methodName: string,
  scenarios: Array<{
    name: string;
    mockImplementation: (...args: any[]) => Promise<any>;
    expectedResult?: any;
    expectError?: boolean;
  }>
) => {
  return scenarios.map(scenario => {
    const mocks = createMockDependencies();
    const service = mocks[serviceName] as any;
    
    if (service && service[methodName]) {
      service[methodName].mockImplementation(scenario.mockImplementation);
    }
    
    return {
      name: scenario.name,
      mocks,
      expectedResult: scenario.expectedResult,
      expectError: scenario.expectError,
    };
  });
};

export const createCombinedServiceScenario = (
  services: Array<{
    service: keyof Dependencies;
    method: string;
    mockImplementation: (...args: any[]) => any;
  }>
) => {
  const mocks = createMockDependencies();
  
  services.forEach(({ service, method, mockImplementation }) => {
    const serviceObj = mocks[service] as any;
    if (serviceObj && serviceObj[method]) {
      serviceObj[method].mockImplementation(mockImplementation);
    }
  });
  
  return mocks;
};