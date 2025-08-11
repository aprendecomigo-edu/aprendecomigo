/**
 * Default Service Implementations
 * 
 * This file provides default implementations of all service interfaces
 * using existing API clients and utilities from the codebase.
 */

import { 
  Dependencies,
  AuthApiService, 
  StorageService, 
  AnalyticsService, 
  RouterService, 
  ToastService, 
  AuthContextService,
  OnboardingApiService 
} from './types';

// Import existing API clients and utilities
import * as authApi from '@/api/authApi';
import { onboardingApi } from '@/api/onboardingApi';
import { storage } from '@/utils/storage';

// Import business services
import { createBusinessServices } from '../business/factory';

// ==================== Default Auth API Service ====================

class DefaultAuthApiService implements AuthApiService {
  constructor() {
    // Check if authApi functions are available during construction
    if (!authApi.requestEmailCode) {
      throw new Error('AuthApi requestEmailCode not available');
    }
    if (!authApi.verifyEmailCode) {
      throw new Error('AuthApi verifyEmailCode not available');
    }
    if (!authApi.createUser) {
      throw new Error('AuthApi createUser not available');
    }
  }

  async requestEmailCode(params: { email: string } | { phone: string }) {
    return authApi.requestEmailCode(params as any);
  }

  async verifyEmailCode(params: { email?: string; phone?: string; code: string }) {
    return authApi.verifyEmailCode(params);
  }

  async createUser(data: any) {
    return authApi.createUser(data);
  }
}

// ==================== Default Storage Service ====================

class DefaultStorageService implements StorageService {
  async setItem(key: string, value: string): Promise<void> {
    return storage.setItem(key, value);
  }

  async getItem(key: string): Promise<string | null> {
    return storage.getItem(key);
  }

  async removeItem(key: string): Promise<void> {
    return storage.removeItem(key);
  }
}

// ==================== Default Analytics Service ====================

class DefaultAnalyticsService implements AnalyticsService {
  track(event: string, properties?: Record<string, any>): void {
    // Only log in development mode, check both __DEV__ and NODE_ENV
    if ((__DEV__ || process.env.NODE_ENV === 'development') && process.env.NODE_ENV !== 'production') {
      console.log('Analytics Track:', event, properties);
    }
    // In production, this would send to actual analytics service
  }

  identify(userId: string, properties?: Record<string, any>): void {
    // Only log in development mode, check both __DEV__ and NODE_ENV
    if ((__DEV__ || process.env.NODE_ENV === 'development') && process.env.NODE_ENV !== 'production') {
      console.log('Analytics Identify:', userId, properties);
    }
    // In production, this would send to actual analytics service
  }

  screen(name: string, properties?: Record<string, any>): void {
    // Only log in development mode, check both __DEV__ and NODE_ENV
    if ((__DEV__ || process.env.NODE_ENV === 'development') && process.env.NODE_ENV !== 'production') {
      console.log('Analytics Screen:', name, properties);
    }
    // In production, this would send to actual analytics service
  }
}

// ==================== Default Router Service ====================

class DefaultRouterService implements RouterService {
  private router: any;

  constructor() {
    try {
      // Import and use the router implementation
      const useRouter = require('@unitools/router').default;
      this.router = useRouter();
    } catch (error) {
      // Fallback for testing
      this.router = {
        push: () => console.log('Router push'),
        back: () => console.log('Router back'),
        replace: () => console.log('Router replace'),
      };
    }
  }

  push(route: string): void {
    this.router.push(route);
  }

  back(): void {
    this.router.back();
  }

  replace(route: string): void {
    this.router.replace(route);
  }
}

// ==================== Default Toast Service ====================

class DefaultToastService implements ToastService {
  private toast: any;

  constructor() {
    try {
      const { useToast } = require('@/components/ui/toast');
      const toastHook = useToast();
      if (!toastHook || !toastHook.showToast) {
        throw new Error('Toast service unavailable');
      }
      this.toast = toastHook;
    } catch (error) {
      if (error instanceof Error && error.message === 'Toast service unavailable') {
        throw error;
      }
      // Fallback for testing
      this.toast = {
        showToast: (type: string, message: string) => {
          if (__DEV__) {
            console.log('Toast:', type, message);
          }
        },
      };
    }
  }

  showToast(type: 'success' | 'error' | 'info' | 'warning', message: string): void {
    this.toast.showToast(type, message);
  }
}

// ==================== Default Auth Context Service ====================

class DefaultAuthContextService implements AuthContextService {
  private auth: any;

  constructor() {
    try {
      const { useAuth } = require('@/api/auth');
      this.auth = useAuth();
    } catch (error) {
      // Fallback for testing
      this.auth = {
        checkAuthStatus: async () => ({ authenticated: false }),
        userProfile: null,
      };
    }
  }

  get userProfile(): any {
    return this.auth.userProfile;
  }

  async checkAuthStatus(): Promise<any> {
    return this.auth.checkAuthStatus();
  }

  get setUserProfile(): ((user: any) => Promise<void>) | undefined {
    // Return the method only if it exists on the auth object
    return this.auth.setUserProfile ? this.auth.setUserProfile.bind(this.auth) : undefined;
  }
}

// ==================== Default Onboarding API Service ====================

class DefaultOnboardingApiService implements OnboardingApiService {
  async getNavigationPreferences() {
    return onboardingApi.getNavigationPreferences();
  }

  async getOnboardingProgress() {
    return onboardingApi.getOnboardingProgress();
  }
}

// ==================== Create Default Dependencies Function ====================

export const createDefaultDependencies = (): Dependencies => {
  const businessServices = createBusinessServices();
  
  return {
    authApi: new DefaultAuthApiService(),
    storageService: new DefaultStorageService(),
    analyticsService: new DefaultAnalyticsService(),
    routerService: new DefaultRouterService(),
    toastService: new DefaultToastService(),
    authContextService: new DefaultAuthContextService(),
    onboardingApiService: new DefaultOnboardingApiService(),
    paymentService: businessServices.paymentService,
    balanceService: businessServices.balanceService,
  };
};