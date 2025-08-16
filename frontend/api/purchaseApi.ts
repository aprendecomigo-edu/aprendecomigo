/**
 * API client functions for purchase-related operations.
 *
 * Handles communication with the backend purchase APIs including
 * pricing plans, purchase initiation, student balance, and Stripe configuration.
 */

import apiClient from './apiClient';

import type {
  PricingPlan,
  PurchaseInitiationRequest,
  PurchaseInitiationResponse,
  StudentBalanceResponse,
  StripeConfig,
  PaginatedTransactionHistory,
  PaginatedPurchaseHistory,
  TransactionFilterOptions,
  PurchaseFilterOptions,
  TopUpPackage,
  RenewalRequest,
  RenewalResponse,
  QuickTopUpRequest,
  QuickTopUpResponse,
} from '@/types/purchase';

/**
 * Purchase API client with comprehensive error handling and type safety.
 */
export class PurchaseApiClient {
  /**
   * Fetch all active pricing plans.
   *
   * @returns Promise resolving to array of active pricing plans
   * @throws Error with descriptive message if request fails
   */
  static async getPricingPlans(): Promise<PricingPlan[]> {
    try {
      const response = await apiClient.get('/finances/pricing-plans/');

      if (!Array.isArray(response.data)) {
        throw new Error('Invalid response format: expected array of pricing plans');
      }

      return response.data.map((plan: any) => ({
        id: plan.id,
        name: plan.name,
        description: plan.description,
        plan_type: plan.plan_type,
        plan_type_display: plan.plan_type_display,
        hours_included: plan.hours_included,
        price_eur: plan.price_eur,
        price_per_hour: plan.price_per_hour,
        validity_days: plan.validity_days,
        is_active: plan.is_active,
        display_order: plan.display_order,
      }));
    } catch (error: any) {
      console.error('Error fetching pricing plans:', error);

      if (error.response?.status === 503) {
        throw new Error('Pricing service temporarily unavailable. Please try again later.');
      } else if (error.response?.status >= 500) {
        throw new Error('Server error occurred while loading pricing plans');
      } else if (error.code === 'NETWORK_ERROR' || error.message === 'Network Error') {
        throw new Error('Network connection error. Please check your internet connection.');
      } else {
        throw new Error('Failed to load pricing plans. Please try again.');
      }
    }
  }

  /**
   * Initiate a purchase for a specific pricing plan.
   *
   * @param request Purchase initiation request data
   * @returns Promise resolving to purchase initiation response
   * @throws Error with descriptive message if request fails
   */
  static async initiatePurchase(
    request: PurchaseInitiationRequest,
  ): Promise<PurchaseInitiationResponse> {
    try {
      const response = await apiClient.post('/finances/purchase/initiate/', request);

      return {
        success: response.data.success,
        client_secret: response.data.client_secret,
        transaction_id: response.data.transaction_id,
        payment_intent_id: response.data.payment_intent_id,
        plan_details: response.data.plan_details,
        message: response.data.message,
      };
    } catch (error: any) {
      console.error('Error initiating purchase:', error);

      // Handle validation errors with detailed field information
      if (error.response?.status === 400 && error.response.data) {
        const errorData = error.response.data;
        return {
          success: false,
          error_type: errorData.error_type || 'validation_error',
          message: errorData.message || 'Invalid request data',
          field_errors: errorData.field_errors || {},
        };
      }

      // Handle rate limiting
      if (error.response?.status === 429) {
        throw new Error('Too many purchase attempts. Please try again later.');
      }

      // Handle server errors
      if (error.response?.status >= 500) {
        throw new Error('Server error occurred during purchase initiation');
      }

      // Handle network errors
      if (error.code === 'NETWORK_ERROR' || error.message === 'Network Error') {
        throw new Error('Network connection error. Please check your internet connection.');
      }

      // Handle payment service errors
      if (error.response?.data?.error_type === 'api_connection_error') {
        throw new Error('Payment service temporarily unavailable. Please try again later.');
      }

      // Generic error fallback
      const errorMessage = error.response?.data?.message || 'Failed to initiate purchase';
      throw new Error(errorMessage);
    }
  }

  /**
   * Get student balance information.
   *
   * @param email Optional email parameter for admin access
   * @returns Promise resolving to student balance data
   * @throws Error with descriptive message if request fails
   */
  static async getStudentBalance(email?: string): Promise<StudentBalanceResponse> {
    try {
      const params = email ? { email } : {};
      const response = await apiClient.get('/finances/student-balance/', { params });

      return {
        student_info: response.data.student_info,
        balance_summary: response.data.balance_summary,
        package_status: response.data.package_status,
        upcoming_expirations: response.data.upcoming_expirations,
      };
    } catch (error: any) {
      console.error('Error fetching student balance:', error);

      if (error.response?.status === 404) {
        throw new Error('Student not found');
      } else if (error.response?.status === 403) {
        throw new Error('Access denied. Unable to retrieve balance information.');
      } else if (error.response?.status >= 500) {
        throw new Error('Server error occurred while loading balance information');
      } else if (error.code === 'NETWORK_ERROR' || error.message === 'Network Error') {
        throw new Error('Network connection error. Please check your internet connection.');
      } else {
        throw new Error('Failed to load balance information. Please try again.');
      }
    }
  }

  /**
   * Get Stripe configuration for frontend initialization.
   *
   * @returns Promise resolving to Stripe configuration
   * @throws Error with descriptive message if request fails
   */
  static async getStripeConfig(): Promise<StripeConfig> {
    try {
      const response = await apiClient.get('/finances/stripe/config/');

      return {
        public_key: response.data.public_key,
        success: response.data.success,
      };
    } catch (error: any) {
      console.error('Error fetching Stripe config:', error);

      if (error.response?.status === 503) {
        throw new Error('Payment service temporarily unavailable');
      } else if (error.response?.status >= 500) {
        throw new Error('Server error occurred while loading payment configuration');
      } else if (error.code === 'NETWORK_ERROR' || error.message === 'Network Error') {
        throw new Error('Network connection error. Please check your internet connection.');
      } else {
        throw new Error('Failed to load payment configuration. Please try again.');
      }
    }
  }

  /**
   * Check if a student can book a session of specified duration.
   *
   * @param durationHours Session duration in hours
   * @param email Optional email parameter for admin access
   * @returns Promise resolving to booking eligibility information
   * @throws Error with descriptive message if request fails
   */
  static async checkBookingEligibility(durationHours: number, email?: string): Promise<any> {
    try {
      const params: any = { duration_hours: durationHours.toString() };
      if (email) {
        params.email = email;
      }

      const response = await apiClient.get('/finances/student-balance/check-booking/', {
        params,
      });
      return response.data;
    } catch (error: any) {
      console.error('Error checking booking eligibility:', error);

      if (error.response?.status === 400) {
        throw new Error(error.response.data?.error || 'Invalid booking request');
      } else if (error.response?.status === 404) {
        throw new Error('Student not found');
      } else if (error.response?.status >= 500) {
        throw new Error('Server error occurred while checking booking eligibility');
      } else if (error.code === 'NETWORK_ERROR' || error.message === 'Network Error') {
        throw new Error('Network connection error. Please check your internet connection.');
      } else {
        throw new Error('Failed to check booking eligibility. Please try again.');
      }
    }
  }

  /**
   * Get student transaction history.
   *
   * @param options Query options for filtering and pagination
   * @returns Promise resolving to paginated transaction history
   * @throws Error with descriptive message if request fails
   */
  static async getTransactionHistory(
    options: TransactionFilterOptions & {
      page?: number;
      page_size?: number;
      email?: string;
    } = {},
  ): Promise<PaginatedTransactionHistory> {
    try {
      const response = await apiClient.get('/finances/student-balance/history/', {
        params: options,
      });
      return response.data;
    } catch (error: any) {
      console.error('Error fetching transaction history:', error);

      if (error.response?.status === 404) {
        throw new Error('Student not found');
      } else if (error.response?.status === 403) {
        throw new Error('Access denied. Unable to retrieve transaction history.');
      } else if (error.response?.status >= 500) {
        throw new Error('Server error occurred while loading transaction history');
      } else if (error.code === 'NETWORK_ERROR' || error.message === 'Network Error') {
        throw new Error('Network connection error. Please check your internet connection.');
      } else {
        throw new Error('Failed to load transaction history. Please try again.');
      }
    }
  }

  /**
   * Get detailed purchase history with consumption tracking.
   *
   * @param options Query options for filtering and pagination
   * @returns Promise resolving to detailed purchase history
   * @throws Error with descriptive message if request fails
   */
  static async getPurchaseHistory(
    options: PurchaseFilterOptions & {
      page?: number;
      page_size?: number;
      email?: string;
    } = {},
  ): Promise<PaginatedPurchaseHistory> {
    try {
      const params: any = { ...options };
      if (options.active_only !== undefined) {
        params.active_only = options.active_only.toString();
      }
      if (options.include_consumption !== undefined) {
        params.include_consumption = options.include_consumption.toString();
      }

      const response = await apiClient.get('/finances/student-balance/purchases/', {
        params,
      });
      return response.data;
    } catch (error: any) {
      console.error('Error fetching purchase history:', error);

      if (error.response?.status === 404) {
        throw new Error('Student not found');
      } else if (error.response?.status === 403) {
        throw new Error('Access denied. Unable to retrieve purchase history.');
      } else if (error.response?.status >= 500) {
        throw new Error('Server error occurred while loading purchase history');
      } else if (error.code === 'NETWORK_ERROR' || error.message === 'Network Error') {
        throw new Error('Network connection error. Please check your internet connection.');
      } else {
        throw new Error('Failed to load purchase history. Please try again.');
      }
    }
  }

  /**
   * Get student receipts.
   *
   * @param email Optional email parameter for admin access
   * @returns Promise resolving to array of receipts
   * @throws Error with descriptive message if request fails
   */
  static async getReceipts(email?: string): Promise<any[]> {
    try {
      const params = email ? { email } : {};
      const response = await apiClient.get('/finances/student-balance/receipts/', { params });
      return response.data;
    } catch (error: any) {
      console.error('Error fetching receipts:', error);
      throw new Error('Failed to load receipts. Please try again.');
    }
  }

  /**
   * Generate a receipt for a transaction.
   *
   * @param transactionId Transaction ID to generate receipt for
   * @param email Optional email parameter for admin access
   * @returns Promise resolving to receipt generation response
   * @throws Error with descriptive message if request fails
   */
  static async generateReceipt(transactionId: string, email?: string): Promise<any> {
    try {
      const data = email
        ? { transaction_id: transactionId, email }
        : { transaction_id: transactionId };
      const response = await apiClient.post('/finances/student-balance/receipts/generate/', data);
      return response.data;
    } catch (error: any) {
      console.error('Error generating receipt:', error);
      throw new Error('Failed to generate receipt. Please try again.');
    }
  }

  /**
   * Get student payment methods.
   *
   * @param email Optional email parameter for admin access
   * @returns Promise resolving to array of payment methods
   * @throws Error with descriptive message if request fails
   */
  static async getPaymentMethods(email?: string): Promise<any[]> {
    try {
      const params = email ? { email } : {};
      const response = await apiClient.get('/finances/student-balance/payment-methods/', {
        params,
      });
      return response.data;
    } catch (error: any) {
      console.error('Error fetching payment methods:', error);
      throw new Error('Failed to load payment methods. Please try again.');
    }
  }

  /**
   * Add a new payment method.
   *
   * @param paymentMethodId Stripe payment method ID
   * @param setAsDefault Whether to set as default payment method
   * @param email Optional email parameter for admin access
   * @returns Promise resolving to payment method addition response
   * @throws Error with descriptive message if request fails
   */
  static async addPaymentMethod(
    paymentMethodId: string,
    setAsDefault: boolean = false,
    email?: string,
  ): Promise<any> {
    try {
      const data = {
        payment_method_id: paymentMethodId,
        set_as_default: setAsDefault,
        ...(email && { email }),
      };
      const response = await apiClient.post('/finances/student-balance/payment-methods/', data);
      return response.data;
    } catch (error: any) {
      console.error('Error adding payment method:', error);
      throw new Error('Failed to add payment method. Please try again.');
    }
  }

  /**
   * Get usage analytics.
   *
   * @param timeRange Optional time range for analytics
   * @param email Optional email parameter for admin access
   * @returns Promise resolving to usage analytics
   * @throws Error with descriptive message if request fails
   */
  static async getUsageAnalytics(
    timeRange?: { start_date: string; end_date: string },
    email?: string,
  ): Promise<any> {
    try {
      const params: any = {};
      if (email) params.email = email;
      if (timeRange) {
        params.start_date = timeRange.start_date;
        params.end_date = timeRange.end_date;
      }

      const response = await apiClient.get('/finances/student-balance/analytics/usage/', {
        params,
      });
      return response.data;
    } catch (error: any) {
      console.error('Error fetching usage analytics:', error);
      throw new Error('Failed to load usage analytics. Please try again.');
    }
  }

  /**
   * Get available top-up packages for quick purchase.
   *
   * @param email Optional email parameter for admin access
   * @returns Promise resolving to array of top-up packages
   * @throws Error with descriptive message if request fails
   */
  static async getTopUpPackages(email?: string): Promise<TopUpPackage[]> {
    try {
      const params = email ? { email } : {};
      const response = await apiClient.get('/finances/student-balance/topup-packages/', { params });

      if (!Array.isArray(response.data)) {
        throw new Error('Invalid response format: expected array of top-up packages');
      }

      return response.data.map((pkg: any) => ({
        id: pkg.id,
        name: pkg.name,
        hours: pkg.hours,
        price_eur: pkg.price_eur,
        price_per_hour: pkg.price_per_hour,
        is_popular: pkg.is_popular,
        discount_percentage: pkg.discount_percentage,
        display_order: pkg.display_order,
      }));
    } catch (error: any) {
      console.error('Error fetching top-up packages:', error);

      if (error.response?.status === 503) {
        throw new Error('Top-up service temporarily unavailable. Please try again later.');
      } else if (error.response?.status >= 500) {
        throw new Error('Server error occurred while loading top-up packages');
      } else if (error.code === 'NETWORK_ERROR' || error.message === 'Network Error') {
        throw new Error('Network connection error. Please check your internet connection.');
      } else {
        throw new Error('Failed to load top-up packages. Please try again.');
      }
    }
  }

  /**
   * Renew expired subscription with saved payment method.
   *
   * @param request Renewal request data
   * @param email Optional email parameter for admin access
   * @returns Promise resolving to renewal response
   * @throws Error with descriptive message if request fails
   */
  static async renewSubscription(
    request: RenewalRequest,
    email?: string,
  ): Promise<RenewalResponse> {
    try {
      const data = email ? { ...request, email } : request;
      const response = await apiClient.post('/finances/student-balance/renew-subscription/', data);

      return {
        success: response.data.success,
        transaction_id: response.data.transaction_id,
        payment_intent_id: response.data.payment_intent_id,
        renewal_details: response.data.renewal_details,
        message: response.data.message,
        client_secret: response.data.client_secret,
      };
    } catch (error: any) {
      console.error('Error renewing subscription:', error);

      // Handle validation errors with detailed field information
      if (error.response?.status === 400 && error.response.data) {
        const errorData = error.response.data;
        return {
          success: false,
          error_type: errorData.error_type || 'validation_error',
          message: errorData.message || 'Invalid renewal request',
          field_errors: errorData.field_errors || {},
        };
      }

      // Handle payment errors
      if (error.response?.status === 402) {
        throw new Error('Payment could not be processed. Please check your payment method.');
      }

      // Handle rate limiting
      if (error.response?.status === 429) {
        throw new Error('Too many renewal attempts. Please try again later.');
      }

      // Handle server errors
      if (error.response?.status >= 500) {
        throw new Error('Server error occurred during subscription renewal');
      }

      // Handle network errors
      if (error.code === 'NETWORK_ERROR' || error.message === 'Network Error') {
        throw new Error('Network connection error. Please check your internet connection.');
      }

      // Handle payment service errors
      if (error.response?.data?.error_type === 'api_connection_error') {
        throw new Error('Payment service temporarily unavailable. Please try again later.');
      }

      // Generic error fallback
      const errorMessage = error.response?.data?.message || 'Failed to renew subscription';
      throw new Error(errorMessage);
    }
  }

  /**
   * Purchase additional hours quickly with saved payment method.
   *
   * @param request Quick top-up request data
   * @param email Optional email parameter for admin access
   * @returns Promise resolving to top-up response
   * @throws Error with descriptive message if request fails
   */
  static async quickTopUp(request: QuickTopUpRequest, email?: string): Promise<QuickTopUpResponse> {
    try {
      const data = email ? { ...request, email } : request;
      const response = await apiClient.post('/finances/student-balance/quick-topup/', data);

      return {
        success: response.data.success,
        transaction_id: response.data.transaction_id,
        payment_intent_id: response.data.payment_intent_id,
        package_details: response.data.package_details,
        message: response.data.message,
        client_secret: response.data.client_secret,
      };
    } catch (error: any) {
      console.error('Error processing quick top-up:', error);

      // Handle validation errors with detailed field information
      if (error.response?.status === 400 && error.response.data) {
        const errorData = error.response.data;
        return {
          success: false,
          error_type: errorData.error_type || 'validation_error',
          message: errorData.message || 'Invalid top-up request',
          field_errors: errorData.field_errors || {},
        };
      }

      // Handle payment errors
      if (error.response?.status === 402) {
        throw new Error('Payment could not be processed. Please check your payment method.');
      }

      // Handle rate limiting
      if (error.response?.status === 429) {
        throw new Error('Too many purchase attempts. Please try again later.');
      }

      // Handle server errors
      if (error.response?.status >= 500) {
        throw new Error('Server error occurred during top-up purchase');
      }

      // Handle network errors
      if (error.code === 'NETWORK_ERROR' || error.message === 'Network Error') {
        throw new Error('Network connection error. Please check your internet connection.');
      }

      // Handle payment service errors
      if (error.response?.data?.error_type === 'api_connection_error') {
        throw new Error('Payment service temporarily unavailable. Please try again later.');
      }

      // Generic error fallback
      const errorMessage = error.response?.data?.message || 'Failed to process top-up purchase';
      throw new Error(errorMessage);
    }
  }
}

// Convenience exports for direct function access
export const {
  getPricingPlans,
  initiatePurchase,
  getStudentBalance,
  getStripeConfig,
  checkBookingEligibility,
  getTransactionHistory,
  getPurchaseHistory,
  getReceipts,
  generateReceipt,
  getPaymentMethods,
  addPaymentMethod,
  getUsageAnalytics,
  getTopUpPackages,
  renewSubscription,
  quickTopUp,
} = PurchaseApiClient;
