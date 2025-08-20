/**
 * Migration shim for backward compatibility
 * Provides the old API interface while transitioning to the new architecture
 * This allows existing code to continue working during the migration period
 *
 * USAGE:
 * Before using any migration functions, initialize the migration layer:
 *
 * ```typescript
 * import { storage } from '@/utils/storage';
 * import { initializeMigrationLayer } from '@/api/migration';
 *
 * // Initialize the migration layer with proper dependencies
 * initializeMigrationLayer(storage, (error) => {
 *   // Handle auth errors (e.g., redirect to login)
 if (__DEV__) {
   *   console.log('Auth error:', error);
 }
 * });
 *
 * // Now you can use the legacy API functions
 * import { requestEmailCode, verifyEmailCode } from '@/api/migration';
 * ```
 */

import { createApiGateway } from './factory';
import type {
  RequestEmailCodeParams,
  RequestPhoneCodeParams,
  VerifyEmailCodeParams,
  OnboardingData,
} from './services/AuthApiService';
import type { TransactionFilters } from './services/BalanceApiService';
import type { NotificationFilters } from './services/NotificationApiService';
import type { CreatePaymentMethodData, PaymentData } from './services/PaymentApiService';
import type { CreateTaskData, UpdateTaskData, TaskFilters } from './services/TasksApiService';
import type { UserProfileUpdate } from './services/UserApiService';

import { StorageInterface } from '@/utils/storage';

// Migration state - these will be injected through initialization
let _migrationStorage: StorageInterface | null = null;
let globalAuthErrorCallback: (() => void) | null = null;

/**
 * Initialize the migration layer with proper dependencies
 * This must be called before using any migration functions
 */
export const initializeMigrationLayer = (
  storage: StorageInterface,
  authErrorCallback?: (() => void) | null,
) => {
  _migrationStorage = storage;
  globalAuthErrorCallback = authErrorCallback || null;
  // Reset the gateway when storage changes
  _legacyApiGateway = null;
};

/**
 * Set the global auth error callback (for backward compatibility)
 */
export const setAuthErrorCallback = (callback: (() => void) | null) => {
  globalAuthErrorCallback = callback;
  // Reset the gateway when callback changes
  _legacyApiGateway = null;
};

/**
 * Create a backward-compatible API gateway instance
 * This maintains the singleton-like behavior expected by existing code
 */
let _legacyApiGateway: ReturnType<typeof createApiGateway> | null = null;

function getLegacyApiGateway() {
  if (!_migrationStorage) {
    throw new Error(
      'Migration layer not initialized. Call initializeMigrationLayer() with storage before using migration functions.',
    );
  }

  if (!_legacyApiGateway) {
    _legacyApiGateway = createApiGateway(_migrationStorage, globalAuthErrorCallback || undefined);
  }
  return _legacyApiGateway;
}

/**
 * Legacy API functions for backward compatibility
 * These delegate to the new service architecture
 */

// Auth API compatibility
export const requestEmailCode = (params: RequestEmailCodeParams | RequestPhoneCodeParams) =>
  getLegacyApiGateway().auth.requestEmailCode(params);
export const verifyEmailCode = (params: VerifyEmailCodeParams) =>
  getLegacyApiGateway().auth.verifyEmailCode(params);
export const createUser = (data: OnboardingData) => getLegacyApiGateway().auth.createUser(data);
export const logout = () => getLegacyApiGateway().auth.logout();
export const isAuthenticated = async (): Promise<boolean> => {
  try {
    await getLegacyApiGateway().auth.validateToken();
    return true;
  } catch {
    return false;
  }
};
export const markFirstLoginCompleted = () => getLegacyApiGateway().auth.markFirstLoginCompleted();

// User API compatibility
export const getUserProfile = () => getLegacyApiGateway().user.getUserProfile();
export const updateUserProfile = (data: UserProfileUpdate) =>
  getLegacyApiGateway().user.updateUserProfile(data);
export const getDashboardInfo = () => getLegacyApiGateway().user.getDashboardInfo();

// Payment API compatibility
export const getPaymentMethods = () => getLegacyApiGateway().payment.getPaymentMethods();
export const createPaymentMethod = (data: CreatePaymentMethodData) =>
  getLegacyApiGateway().payment.createPaymentMethod(data);
export const processPayment = (data: PaymentData) =>
  getLegacyApiGateway().payment.processPayment(data);

// Tasks API compatibility
export const getTasks = (filters?: TaskFilters) => getLegacyApiGateway().tasks.getTasks(filters);
export const createTask = (data: CreateTaskData) => getLegacyApiGateway().tasks.createTask(data);
export const updateTask = (id: number, data: UpdateTaskData) =>
  getLegacyApiGateway().tasks.updateTask(id, data);
export const deleteTask = (id: number) => getLegacyApiGateway().tasks.deleteTask(id);

// Balance API compatibility
export const getBalance = () => getLegacyApiGateway().balance.getBalance();
export const getTransactions = (filters?: TransactionFilters) =>
  getLegacyApiGateway().balance.getTransactions(filters);

// Notification API compatibility
export const getNotifications = (filters?: NotificationFilters) =>
  getLegacyApiGateway().notification.getNotifications(filters);
export const markAsRead = (id: number) => getLegacyApiGateway().notification.markAsRead(id);

/**
 * Reset the legacy gateway instance (for testing)
 */
export const _resetLegacyGateway = () => {
  _legacyApiGateway = null;
};
