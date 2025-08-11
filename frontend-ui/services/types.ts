/**
 * Service interfaces for dependency injection in authentication architecture
 * These interfaces define the contracts that business logic expects from external services
 */

// Auth API Service Interface
export interface AuthApiService {
  requestEmailCode(params: { email: string } | { phone: string }): Promise<any>;
  verifyEmailCode(params: { email?: string; phone?: string; code: string }): Promise<any>;
  createUser(data: any): Promise<any>;
}

// Storage Service Interface
export interface StorageService {
  setItem(key: string, value: string): Promise<void>;
  getItem(key: string): Promise<string | null>;
  removeItem(key: string): Promise<void>;
}

// Analytics Service Interface (for future tracking)
export interface AnalyticsService {
  track(event: string, properties?: Record<string, any>): void;
  identify(userId: string, properties?: Record<string, any>): void;
  screen(name: string, properties?: Record<string, any>): void;
}

// Router Service Interface
export interface RouterService {
  push(route: string): void;
  back(): void;
  replace(route: string): void;
}

// Toast Service Interface
export interface ToastService {
  showToast(type: 'success' | 'error' | 'info' | 'warning', message: string): void;
}

// Auth Context Service Interface
export interface AuthContextService {
  checkAuthStatus(): Promise<any>;
  setUserProfile?(user: any): Promise<void>;
  userProfile?: any;
}

// Onboarding API Service Interface
export interface OnboardingApiService {
  getNavigationPreferences(): Promise<any>;
  getOnboardingProgress(): Promise<any>;
}