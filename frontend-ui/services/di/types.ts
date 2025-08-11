/**
 * Dependency Injection Types and Interfaces
 *
 * This file defines all service interfaces and types used in the DI system.
 * These interfaces define the contracts that business logic expects from external services.
 */

// ==================== Base Service Types ====================

export interface ServiceGateway<T> {
  service: T;
  isActive: boolean;
  metadata: {
    name: string;
    version: string;
    environment?: string;
  };
  initialize?: () => Promise<void> | void;
  dispose?: () => Promise<void> | void;
}

// ==================== Service Interfaces ====================

export interface AuthApiService {
  requestEmailCode(params: { email: string } | { phone: string }): Promise<any>;
  verifyEmailCode(params: { email?: string; phone?: string; code: string }): Promise<any>;
  createUser(data: any): Promise<any>;
}

export interface StorageService {
  setItem(key: string, value: string): Promise<void>;
  getItem(key: string): Promise<string | null>;
  removeItem(key: string): Promise<void>;
}

export interface AnalyticsService {
  track(event: string, properties?: Record<string, any>): void;
  identify(userId: string, properties?: Record<string, any>): void;
  screen(name: string, properties?: Record<string, any>): void;
}

export interface RouterService {
  push(route: string): void;
  back(): void;
  replace(route: string): void;
}

export interface ToastService {
  showToast(type: 'success' | 'error' | 'info' | 'warning', message: string): void;
}

export interface AuthContextService {
  checkAuthStatus(): Promise<any>;
  setUserProfile?(user: any): Promise<void>;
  userProfile?: any;
}

export interface OnboardingApiService {
  getNavigationPreferences(): Promise<any>;
  getOnboardingProgress(): Promise<any>;
}

// ==================== Dependencies Container ====================

export interface Dependencies {
  authApi: AuthApiService;
  storageService: StorageService;
  analyticsService: AnalyticsService;
  routerService: RouterService;
  toastService: ToastService;
  authContextService: AuthContextService;
  onboardingApiService: OnboardingApiService;
}

// ==================== Mock Dependencies for Testing ====================

export type MockDependencies = {
  [K in keyof Dependencies]: {
    [P in keyof Dependencies[K]]: Dependencies[K][P] extends (...args: any[]) => any
      ? jest.MockedFunction<Dependencies[K][P]>
      : Dependencies[K][P];
  };
};

// ==================== Partial Dependencies for Testing ====================

export type PartialDependencies = {
  [K in keyof Dependencies]?: Partial<Dependencies[K]>;
};

// ==================== Type Guards and Utility Types ====================

export type DependencyKey = keyof Dependencies;

export type DependencyService<K extends DependencyKey> = Dependencies[K];

// Helper type for dependency overrides
export type DependencyOverrides = {
  [K in keyof Dependencies]?: Dependencies[K];
};
