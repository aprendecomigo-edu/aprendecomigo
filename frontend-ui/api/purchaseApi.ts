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
      const response = await apiClient.get('/finances/api/pricing-plans/');
      
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
  static async initiatePurchase(request: PurchaseInitiationRequest): Promise<PurchaseInitiationResponse> {
    try {
      const response = await apiClient.post('/finances/api/purchase/initiate/', request);
      
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
      const response = await apiClient.get('/finances/api/student-balance/', { params });
      
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
      const response = await apiClient.get('/finances/api/stripe/config/');
      
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
      
      const response = await apiClient.get('/finances/api/student-balance/check-booking/', { params });
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
  static async getTransactionHistory(options: {
    email?: string;
    payment_status?: string;
    transaction_type?: string;
    page?: number;
    page_size?: number;
  } = {}): Promise<any> {
    try {
      const response = await apiClient.get('/finances/api/student-balance/history/', {
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
  static async getPurchaseHistory(options: {
    email?: string;
    active_only?: boolean;
    include_consumption?: boolean;
    page?: number;
    page_size?: number;
  } = {}): Promise<any> {
    try {
      const params: any = { ...options };
      if (options.active_only !== undefined) {
        params.active_only = options.active_only.toString();
      }
      if (options.include_consumption !== undefined) {
        params.include_consumption = options.include_consumption.toString();
      }
      
      const response = await apiClient.get('/finances/api/student-balance/purchases/', {
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
} = PurchaseApiClient;