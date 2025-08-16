/**
 * TDD Tests for Default Implementations
 *
 * These tests will INITIALLY FAIL until the new DI default implementations are created.
 * Tests that createDefaultDependencies returns all required services with proper implementations.
 */

// These imports will fail until DI defaults are implemented
import { createDefaultDependencies } from '@/services/di/defaults';
import type { Dependencies } from '@/services/di/types';

// Mock existing API clients and services
jest.mock('@/api/authApi');
jest.mock('@/api/onboardingApi');
jest.mock('@/utils/storage');
jest.mock('@/components/ui/toast');
jest.mock('@unitools/router');
jest.mock('@/api/auth');

const mockAuthApi = {
  requestEmailCode: jest.fn(),
  verifyEmailCode: jest.fn(),
  createUser: jest.fn(),
};

const mockOnboardingApi = {
  getNavigationPreferences: jest.fn(),
  getOnboardingProgress: jest.fn(),
};

const mockStorage = {
  setItem: jest.fn(),
  getItem: jest.fn(),
  removeItem: jest.fn(),
};

const mockToast = {
  showToast: jest.fn(),
};

const mockRouter = {
  push: jest.fn(),
  back: jest.fn(),
  replace: jest.fn(),
};

const mockAuth = {
  checkAuthStatus: jest.fn(),
  setUserProfile: jest.fn(),
  userProfile: null,
};

// Setup mocks
beforeEach(() => {
  jest.clearAllMocks();

  require('@/api/authApi').requestEmailCode = mockAuthApi.requestEmailCode;
  require('@/api/authApi').verifyEmailCode = mockAuthApi.verifyEmailCode;
  require('@/api/authApi').createUser = mockAuthApi.createUser;

  require('@/api/onboardingApi').onboardingApi = mockOnboardingApi;

  require('@/utils/storage').storage = mockStorage;

  require('@/components/ui/toast').useToast = () => mockToast;
  require('@unitools/router').default = () => mockRouter;
  require('@/api/auth').useAuth = () => mockAuth;
});

describe('Default Implementations', () => {
  describe('createDefaultDependencies Function', () => {
    it('should return complete Dependencies object', () => {
      const dependencies = createDefaultDependencies();

      expect(dependencies).toBeDefined();
      expect(typeof dependencies).toBe('object');

      // Should have all required services
      expect(dependencies.authApi).toBeDefined();
      expect(dependencies.storageService).toBeDefined();
      expect(dependencies.analyticsService).toBeDefined();
      expect(dependencies.routerService).toBeDefined();
      expect(dependencies.toastService).toBeDefined();
      expect(dependencies.authContextService).toBeDefined();
      expect(dependencies.onboardingApiService).toBeDefined();
    });

    it('should implement Dependencies interface correctly', () => {
      const dependencies: Dependencies = createDefaultDependencies();

      // TypeScript compilation should verify interface compliance
      expect(dependencies).toBeDefined();
    });

    it('should create new instances on each call', () => {
      const deps1 = createDefaultDependencies();
      const deps2 = createDefaultDependencies();

      // Should be different objects
      expect(deps1).not.toBe(deps2);

      // But services might share singleton implementations
      // This is implementation-dependent
      expect(deps1.authApi).toBeDefined();
      expect(deps2.authApi).toBeDefined();
    });
  });

  describe('DefaultAuthApiService Implementation', () => {
    it('should implement AuthApiService interface', () => {
      const dependencies = createDefaultDependencies();
      const authApi = dependencies.authApi;

      expect(typeof authApi.requestEmailCode).toBe('function');
      expect(typeof authApi.verifyEmailCode).toBe('function');
      expect(typeof authApi.createUser).toBe('function');
    });

    it('should delegate to existing authApi module', async () => {
      mockAuthApi.requestEmailCode.mockResolvedValue({ success: true });

      const dependencies = createDefaultDependencies();
      const result = await dependencies.authApi.requestEmailCode({ email: 'test@example.com' });

      expect(mockAuthApi.requestEmailCode).toHaveBeenCalledWith({ email: 'test@example.com' });
      expect(result).toEqual({ success: true });
    });

    it('should handle email verification correctly', async () => {
      const mockResponse = {
        user: { id: 1, email: 'test@example.com' },
        access_token: 'token',
        refresh_token: 'refresh',
      };
      mockAuthApi.verifyEmailCode.mockResolvedValue(mockResponse);

      const dependencies = createDefaultDependencies();
      const result = await dependencies.authApi.verifyEmailCode({
        email: 'test@example.com',
        code: '123456',
      });

      expect(mockAuthApi.verifyEmailCode).toHaveBeenCalledWith({
        email: 'test@example.com',
        code: '123456',
      });
      expect(result).toEqual(mockResponse);
    });

    it('should handle user creation correctly', async () => {
      const userData = {
        name: 'Test User',
        email: 'test@example.com',
        user_type: 'student',
      };
      const mockResponse = { user: userData, created: true };
      mockAuthApi.createUser.mockResolvedValue(mockResponse);

      const dependencies = createDefaultDependencies();
      const result = await dependencies.authApi.createUser(userData);

      expect(mockAuthApi.createUser).toHaveBeenCalledWith(userData);
      expect(result).toEqual(mockResponse);
    });

    it('should propagate API errors correctly', async () => {
      const apiError = new Error('Network error');
      mockAuthApi.requestEmailCode.mockRejectedValue(apiError);

      const dependencies = createDefaultDependencies();

      await expect(
        dependencies.authApi.requestEmailCode({ email: 'test@example.com' }),
      ).rejects.toThrow('Network error');
    });
  });

  describe('DefaultStorageService Implementation', () => {
    it('should implement StorageService interface', () => {
      const dependencies = createDefaultDependencies();
      const storageService = dependencies.storageService;

      expect(typeof storageService.setItem).toBe('function');
      expect(typeof storageService.getItem).toBe('function');
      expect(typeof storageService.removeItem).toBe('function');
    });

    it('should delegate to existing storage utility', async () => {
      mockStorage.setItem.mockResolvedValue(undefined);
      mockStorage.getItem.mockResolvedValue('stored_value');
      mockStorage.removeItem.mockResolvedValue(undefined);

      const dependencies = createDefaultDependencies();
      const storage = dependencies.storageService;

      // Test setItem
      await storage.setItem('test_key', 'test_value');
      expect(mockStorage.setItem).toHaveBeenCalledWith('test_key', 'test_value');

      // Test getItem
      const value = await storage.getItem('test_key');
      expect(mockStorage.getItem).toHaveBeenCalledWith('test_key');
      expect(value).toBe('stored_value');

      // Test removeItem
      await storage.removeItem('test_key');
      expect(mockStorage.removeItem).toHaveBeenCalledWith('test_key');
    });

    it('should handle storage errors gracefully', async () => {
      const storageError = new Error('Storage unavailable');
      mockStorage.getItem.mockRejectedValue(storageError);

      const dependencies = createDefaultDependencies();

      await expect(dependencies.storageService.getItem('test_key')).rejects.toThrow(
        'Storage unavailable',
      );
    });

    it('should return null for non-existent keys', async () => {
      mockStorage.getItem.mockResolvedValue(null);

      const dependencies = createDefaultDependencies();
      const value = await dependencies.storageService.getItem('non_existent');

      expect(value).toBeNull();
    });
  });

  describe('DefaultAnalyticsService Implementation', () => {
    it('should implement AnalyticsService interface', () => {
      const dependencies = createDefaultDependencies();
      const analyticsService = dependencies.analyticsService;

      expect(typeof analyticsService.track).toBe('function');
      expect(typeof analyticsService.identify).toBe('function');
      expect(typeof analyticsService.screen).toBe('function');
    });

    it('should provide no-op implementation for development', () => {
      const dependencies = createDefaultDependencies();
      const analytics = dependencies.analyticsService;

      // Should not throw errors
      expect(() => {
        analytics.track('test_event', { prop: 'value' });
        analytics.identify('user_123', { email: 'test@example.com' });
        analytics.screen('Dashboard', { section: 'main' });
      }).not.toThrow();
    });

    it('should log events in development mode', () => {
      const originalDev = (global as any).__DEV__;
      (global as any).__DEV__ = true;

      const consoleSpy = jest.spyOn(console, 'log').mockImplementation();

      const dependencies = createDefaultDependencies();
      const analytics = dependencies.analyticsService;

      analytics.track('test_event', { prop: 'value' });
      analytics.identify('user_123', { email: 'test@example.com' });
      analytics.screen('Dashboard');

      expect(consoleSpy).toHaveBeenCalledWith('Analytics Track:', 'test_event', { prop: 'value' });
      expect(consoleSpy).toHaveBeenCalledWith('Analytics Identify:', 'user_123', {
        email: 'test@example.com',
      });
      expect(consoleSpy).toHaveBeenCalledWith('Analytics Screen:', 'Dashboard', undefined);

      consoleSpy.mockRestore();
      (global as any).__DEV__ = originalDev;
    });

    it('should not log in production mode', () => {
      const originalDev = (global as any).__DEV__;
      (global as any).__DEV__ = false;

      const consoleSpy = jest.spyOn(console, 'log').mockImplementation();

      const dependencies = createDefaultDependencies();
      const analytics = dependencies.analyticsService;

      analytics.track('test_event', { prop: 'value' });

      expect(consoleSpy).not.toHaveBeenCalled();

      consoleSpy.mockRestore();
      (global as any).__DEV__ = originalDev;
    });
  });

  describe('RouterService Implementation', () => {
    it('should implement RouterService interface', () => {
      const dependencies = createDefaultDependencies();
      const routerService = dependencies.routerService;

      expect(typeof routerService.push).toBe('function');
      expect(typeof routerService.back).toBe('function');
      expect(typeof routerService.replace).toBe('function');
    });

    it('should delegate to useRouter hook', () => {
      const dependencies = createDefaultDependencies();
      const router = dependencies.routerService;

      router.push('/test-route');
      router.back();
      router.replace('/new-route');

      expect(mockRouter.push).toHaveBeenCalledWith('/test-route');
      expect(mockRouter.back).toHaveBeenCalled();
      expect(mockRouter.replace).toHaveBeenCalledWith('/new-route');
    });

    it('should handle navigation with parameters', () => {
      const dependencies = createDefaultDependencies();
      const router = dependencies.routerService;

      router.push('/auth/verify-code?email=test%40example.com');
      expect(mockRouter.push).toHaveBeenCalledWith('/auth/verify-code?email=test%40example.com');
    });
  });

  describe('ToastService Implementation', () => {
    it('should implement ToastService interface', () => {
      const dependencies = createDefaultDependencies();
      const toastService = dependencies.toastService;

      expect(typeof toastService.showToast).toBe('function');
    });

    it('should delegate to useToast hook', () => {
      const dependencies = createDefaultDependencies();
      const toast = dependencies.toastService;

      toast.showToast('success', 'Operation completed');
      toast.showToast('error', 'An error occurred');

      expect(mockToast.showToast).toHaveBeenCalledWith('success', 'Operation completed');
      expect(mockToast.showToast).toHaveBeenCalledWith('error', 'An error occurred');
    });

    it('should support all toast types', () => {
      const dependencies = createDefaultDependencies();
      const toast = dependencies.toastService;

      toast.showToast('success', 'Success message');
      toast.showToast('error', 'Error message');
      toast.showToast('info', 'Info message');
      toast.showToast('warning', 'Warning message');

      expect(mockToast.showToast).toHaveBeenCalledWith('success', 'Success message');
      expect(mockToast.showToast).toHaveBeenCalledWith('error', 'Error message');
      expect(mockToast.showToast).toHaveBeenCalledWith('info', 'Info message');
      expect(mockToast.showToast).toHaveBeenCalledWith('warning', 'Warning message');
    });
  });

  describe('AuthContextService Implementation', () => {
    it('should implement AuthContextService interface', () => {
      const dependencies = createDefaultDependencies();
      const authContextService = dependencies.authContextService;

      expect(typeof authContextService.checkAuthStatus).toBe('function');
      expect(authContextService.userProfile).toBeDefined();
    });

    it('should delegate to useAuth hook', async () => {
      const mockAuthStatus = { authenticated: true, user: { id: 1, email: 'test@example.com' } };
      mockAuth.checkAuthStatus.mockResolvedValue(mockAuthStatus);
      mockAuth.userProfile = { id: 1, email: 'test@example.com' };

      const dependencies = createDefaultDependencies();
      const authContext = dependencies.authContextService;

      // Test checkAuthStatus
      const status = await authContext.checkAuthStatus();
      expect(mockAuth.checkAuthStatus).toHaveBeenCalled();
      expect(status).toEqual(mockAuthStatus);

      // Test userProfile
      expect(authContext.userProfile).toEqual({ id: 1, email: 'test@example.com' });
    });

    it('should support optional setUserProfile method', async () => {
      mockAuth.setUserProfile = jest.fn().mockResolvedValue(undefined);

      const dependencies = createDefaultDependencies();
      const authContext = dependencies.authContextService;

      if (authContext.setUserProfile) {
        const testUser = { id: 1, email: 'test@example.com' };
        await authContext.setUserProfile(testUser);
        expect(mockAuth.setUserProfile).toHaveBeenCalledWith(testUser);
      }
    });
  });

  describe('OnboardingApiService Implementation', () => {
    it('should implement OnboardingApiService interface', () => {
      const dependencies = createDefaultDependencies();
      const onboardingApiService = dependencies.onboardingApiService;

      expect(typeof onboardingApiService.getNavigationPreferences).toBe('function');
      expect(typeof onboardingApiService.getOnboardingProgress).toBe('function');
    });

    it('should delegate to onboardingApi module', async () => {
      const mockNavPrefs = { show_onboarding: true, skip_welcome: false };
      const mockProgress = { completion_percentage: 75, current_step: 3 };

      mockOnboardingApi.getNavigationPreferences.mockResolvedValue(mockNavPrefs);
      mockOnboardingApi.getOnboardingProgress.mockResolvedValue(mockProgress);

      const dependencies = createDefaultDependencies();
      const onboardingApi = dependencies.onboardingApiService;

      // Test getNavigationPreferences
      const navPrefs = await onboardingApi.getNavigationPreferences();
      expect(mockOnboardingApi.getNavigationPreferences).toHaveBeenCalled();
      expect(navPrefs).toEqual(mockNavPrefs);

      // Test getOnboardingProgress
      const progress = await onboardingApi.getOnboardingProgress();
      expect(mockOnboardingApi.getOnboardingProgress).toHaveBeenCalled();
      expect(progress).toEqual(mockProgress);
    });

    it('should handle API errors in onboarding calls', async () => {
      const apiError = new Error('Onboarding API unavailable');
      mockOnboardingApi.getNavigationPreferences.mockRejectedValue(apiError);

      const dependencies = createDefaultDependencies();

      await expect(dependencies.onboardingApiService.getNavigationPreferences()).rejects.toThrow(
        'Onboarding API unavailable',
      );
    });
  });

  describe('Service Integration', () => {
    it('should create compatible services that work together', async () => {
      const dependencies = createDefaultDependencies();

      // Mock successful API call
      mockAuthApi.requestEmailCode.mockResolvedValue({ success: true });

      // Use multiple services together
      await dependencies.authApi.requestEmailCode({ email: 'test@example.com' });
      dependencies.toastService.showToast('success', 'Code sent');
      dependencies.routerService.push('/auth/verify-code');
      await dependencies.storageService.setItem('email', 'test@example.com');

      expect(mockAuthApi.requestEmailCode).toHaveBeenCalled();
      expect(mockToast.showToast).toHaveBeenCalled();
      expect(mockRouter.push).toHaveBeenCalled();
      expect(mockStorage.setItem).toHaveBeenCalled();
    });

    it('should maintain service isolation and testability', () => {
      const deps1 = createDefaultDependencies();
      const deps2 = createDefaultDependencies();

      // Services should be independently replaceable
      expect(deps1.authApi).toBeDefined();
      expect(deps2.authApi).toBeDefined();

      // Each dependency object should be its own instance
      expect(deps1).not.toBe(deps2);
    });

    it('should support real-world authentication flow', async () => {
      // Mock complete authentication flow
      mockAuthApi.requestEmailCode.mockResolvedValue({ success: true });
      mockAuthApi.verifyEmailCode.mockResolvedValue({
        user: { id: 1, email: 'test@example.com' },
        access_token: 'token',
        refresh_token: 'refresh',
      });
      mockAuth.setUserProfile = jest.fn().mockResolvedValue(undefined);
      mockAuth.checkAuthStatus.mockResolvedValue({ authenticated: true });

      const dependencies = createDefaultDependencies();

      // Step 1: Request email code
      await dependencies.authApi.requestEmailCode({ email: 'test@example.com' });
      dependencies.toastService.showToast('success', 'Code sent');
      dependencies.routerService.push('/auth/verify-code');

      // Step 2: Verify code
      const verifyResult = await dependencies.authApi.verifyEmailCode({
        email: 'test@example.com',
        code: '123456',
      });

      // Step 3: Update auth context
      if (dependencies.authContextService.setUserProfile) {
        await dependencies.authContextService.setUserProfile(verifyResult.user);
      }
      await dependencies.authContextService.checkAuthStatus();

      // Step 4: Navigate to dashboard
      dependencies.routerService.replace('/dashboard');

      // All services should have been called correctly
      expect(mockAuthApi.requestEmailCode).toHaveBeenCalledWith({ email: 'test@example.com' });
      expect(mockAuthApi.verifyEmailCode).toHaveBeenCalledWith({
        email: 'test@example.com',
        code: '123456',
      });
      expect(mockToast.showToast).toHaveBeenCalledWith('success', 'Code sent');
      expect(mockRouter.push).toHaveBeenCalledWith('/auth/verify-code');
      expect(mockRouter.replace).toHaveBeenCalledWith('/dashboard');
      expect(mockAuth.checkAuthStatus).toHaveBeenCalled();
    });
  });

  describe('Error Handling and Resilience', () => {
    it('should handle service initialization failures gracefully', () => {
      // Mock a service that fails to initialize
      const originalUseToast = require('@/components/ui/toast').useToast;
      require('@/components/ui/toast').useToast = () => {
        throw new Error('Toast service unavailable');
      };

      // Should still create other services
      expect(() => {
        createDefaultDependencies();
      }).toThrow('Toast service unavailable');

      // Restore original
      require('@/components/ui/toast').useToast = originalUseToast;
    });

    it('should provide meaningful error messages for missing dependencies', () => {
      // Mock missing API module
      const originalAuthApi = require('@/api/authApi');
      require('@/api/authApi').requestEmailCode = undefined;

      expect(() => {
        createDefaultDependencies();
      }).toThrow(/AuthApi.*not available/);

      // Restore original
      require('@/api/authApi').requestEmailCode = originalAuthApi.requestEmailCode;
    });

    it('should support fallback implementations for optional services', () => {
      // Mock missing optional service
      mockAuth.setUserProfile = undefined;

      const dependencies = createDefaultDependencies();

      // Should create service without the optional method
      expect(dependencies.authContextService.setUserProfile).toBeUndefined();
      expect(typeof dependencies.authContextService.checkAuthStatus).toBe('function');
    });
  });

  describe('Production Readiness', () => {
    it('should use production-optimized implementations', () => {
      const originalEnv = process.env.NODE_ENV;
      process.env.NODE_ENV = 'production';

      const dependencies = createDefaultDependencies();

      // Analytics should not log in production
      const consoleSpy = jest.spyOn(console, 'log').mockImplementation();
      dependencies.analyticsService.track('test_event');
      expect(consoleSpy).not.toHaveBeenCalled();
      consoleSpy.mockRestore();

      process.env.NODE_ENV = originalEnv;
    });

    it('should minimize memory footprint', () => {
      const dependencies = createDefaultDependencies();

      // All services should be lightweight wrappers
      expect(dependencies).toBeDefined();
      expect(Object.keys(dependencies).length).toBe(9); // All required services including business services
    });

    it('should support service swapping for different environments', () => {
      // Should be able to override specific services for testing
      const dependencies = createDefaultDependencies();

      // This demonstrates how services can be swapped
      const testDependencies = {
        ...dependencies,
        authApi: {
          requestEmailCode: jest.fn().mockResolvedValue({ success: true }),
          verifyEmailCode: jest.fn(),
          createUser: jest.fn(),
        },
      };

      expect(testDependencies.authApi).not.toBe(dependencies.authApi);
      expect(testDependencies.storageService).toBe(dependencies.storageService);
    });
  });
});
