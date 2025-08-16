/**
 * Default implementations of service interfaces using existing API clients
 */

import { useRouter } from 'expo-router';

import {
  AuthApiService,
  StorageService,
  AnalyticsService,
  RouterService,
  ToastService,
  AuthContextService,
  OnboardingApiService,
} from './types';

import { useAuth } from '@/api/auth';
import * as authApi from '@/api/authApi';
import { onboardingApi } from '@/api/onboardingApi';
import { useToast } from '@/components/ui/toast';
import { storage } from '@/utils/storage';

// Default Auth API implementation using existing authApi
export class DefaultAuthApiService implements AuthApiService {
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

// Default Storage implementation using existing storage utility
export class DefaultStorageService implements StorageService {
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

// Default Analytics service (no-op for now, can be replaced with actual analytics)
export class DefaultAnalyticsService implements AnalyticsService {
  track(event: string, properties?: Record<string, any>): void {
    if (__DEV__) {
      if (__DEV__) {
        console.log('Analytics Track:', event, properties);
      }
    }
  }

  identify(userId: string, properties?: Record<string, any>): void {
    if (__DEV__) {
      if (__DEV__) {
        console.log('Analytics Identify:', userId, properties);
      }
    }
  }

  screen(name: string, properties?: Record<string, any>): void {
    if (__DEV__) {
      if (__DEV__) {
        console.log('Analytics Screen:', name, properties);
      }
    }
  }
}

// Router wrapper to create service instance
export const createRouterService = (): RouterService => {
  const router = useRouter();
  return {
    push: router.push,
    back: router.back,
    replace: router.replace,
  };
};

// Toast wrapper to create service instance
export const createToastService = (): ToastService => {
  const toast = useToast();
  return {
    showToast: toast.showToast,
  };
};

// Auth context wrapper to create service instance
export const createAuthContextService = (): AuthContextService => {
  const auth = useAuth();
  return {
    checkAuthStatus: auth.checkAuthStatus,
    setUserProfile: auth.setUserProfile,
    userProfile: auth.userProfile,
  };
};

// Default Onboarding API implementation
export class DefaultOnboardingApiService implements OnboardingApiService {
  async getNavigationPreferences() {
    return onboardingApi.getNavigationPreferences();
  }

  async getOnboardingProgress() {
    return onboardingApi.getOnboardingProgress();
  }
}

// Singleton instances for commonly used services
export const defaultAuthApiService = new DefaultAuthApiService();
export const defaultStorageService = new DefaultStorageService();
export const defaultAnalyticsService = new DefaultAnalyticsService();
export const defaultOnboardingApiService = new DefaultOnboardingApiService();
