/**
 * API client functions for payment method management operations.
 *
 * Handles communication with the backend payment method APIs including
 * listing, adding, removing, and setting default payment methods.
 */

import apiClient from './apiClient';

export interface PaymentMethod {
  id: string;
  type: 'card';
  card: {
    brand: string;
    last4: string;
    exp_month: number;
    exp_year: number;
    funding: string;
  };
  billing_details: {
    name?: string;
    email?: string;
    address?: {
      line1?: string;
      line2?: string;
      city?: string;
      state?: string;
      postal_code?: string;
      country?: string;
    };
  };
  is_default: boolean;
  created_at: string;
}

export interface AddPaymentMethodRequest {
  payment_method_id: string;
  set_as_default?: boolean;
}

export interface AddPaymentMethodResponse {
  success: boolean;
  payment_method: PaymentMethod;
  message: string;
}

/**
 * Payment Method API client with comprehensive error handling and type safety.
 */
export class PaymentMethodApiClient {
  /**
   * Get all payment methods for the authenticated student.
   *
   * @param email Optional email parameter for admin access
   * @returns Promise resolving to array of payment methods
   * @throws Error with descriptive message if request fails
   */
  static async getPaymentMethods(email?: string): Promise<PaymentMethod[]> {
    try {
      const params = email ? { email } : {};
      const response = await apiClient.get('/api/student-balance/payment-methods/', { params });

      if (!Array.isArray(response.data)) {
        throw new Error('Invalid response format: expected array of payment methods');
      }

      return response.data.map((method: any) => ({
        id: method.id,
        type: method.type,
        card: {
          brand: method.card.brand,
          last4: method.card.last4,
          exp_month: method.card.exp_month,
          exp_year: method.card.exp_year,
          funding: method.card.funding,
        },
        billing_details: {
          name: method.billing_details?.name,
          email: method.billing_details?.email,
          address: method.billing_details?.address
            ? {
                line1: method.billing_details.address.line1,
                line2: method.billing_details.address.line2,
                city: method.billing_details.address.city,
                state: method.billing_details.address.state,
                postal_code: method.billing_details.address.postal_code,
                country: method.billing_details.address.country,
              }
            : undefined,
        },
        is_default: method.is_default,
        created_at: method.created_at,
      }));
    } catch (error: any) {
      console.error('Error fetching payment methods:', error);

      if (error.response?.status === 404) {
        throw new Error('Student not found');
      } else if (error.response?.status === 403) {
        throw new Error('Access denied. Unable to retrieve payment methods.');
      } else if (error.response?.status >= 500) {
        throw new Error('Server error occurred while loading payment methods');
      } else if (error.code === 'NETWORK_ERROR' || error.message === 'Network Error') {
        throw new Error('Network connection error. Please check your internet connection.');
      } else {
        throw new Error('Failed to load payment methods. Please try again.');
      }
    }
  }

  /**
   * Add a new payment method.
   *
   * @param request Payment method addition request data
   * @param email Optional email parameter for admin access
   * @returns Promise resolving to payment method addition response
   * @throws Error with descriptive message if request fails
   */
  static async addPaymentMethod(
    request: AddPaymentMethodRequest,
    email?: string,
  ): Promise<AddPaymentMethodResponse> {
    try {
      const data = email ? { ...request, email } : request;
      const response = await apiClient.post('/api/student-balance/payment-methods/', data);

      return {
        success: response.data.success,
        payment_method: {
          id: response.data.payment_method.id,
          type: response.data.payment_method.type,
          card: {
            brand: response.data.payment_method.card.brand,
            last4: response.data.payment_method.card.last4,
            exp_month: response.data.payment_method.card.exp_month,
            exp_year: response.data.payment_method.card.exp_year,
            funding: response.data.payment_method.card.funding,
          },
          billing_details: response.data.payment_method.billing_details,
          is_default: response.data.payment_method.is_default,
          created_at: response.data.payment_method.created_at,
        },
        message: response.data.message,
      };
    } catch (error: any) {
      console.error('Error adding payment method:', error);

      if (error.response?.status === 400) {
        throw new Error(error.response.data?.message || 'Invalid payment method data');
      } else if (error.response?.status === 402) {
        throw new Error('Payment method could not be verified. Please check your card details.');
      } else if (error.response?.status === 409) {
        throw new Error('This payment method already exists');
      } else if (error.response?.status >= 500) {
        throw new Error('Server error occurred while adding payment method');
      } else if (error.code === 'NETWORK_ERROR' || error.message === 'Network Error') {
        throw new Error('Network connection error. Please check your internet connection.');
      } else {
        throw new Error('Failed to add payment method. Please try again.');
      }
    }
  }

  /**
   * Remove a payment method by ID.
   *
   * @param paymentMethodId The payment method ID to remove
   * @param email Optional email parameter for admin access
   * @returns Promise that resolves when payment method is removed
   * @throws Error with descriptive message if request fails
   */
  static async removePaymentMethod(paymentMethodId: string, email?: string): Promise<void> {
    try {
      const data = email ? { email } : {};
      await apiClient.delete(`/api/student-balance/payment-methods/${paymentMethodId}/`, { data });
    } catch (error: any) {
      console.error('Error removing payment method:', error);

      if (error.response?.status === 400) {
        throw new Error(
          'Cannot remove the default payment method. Please set another method as default first.',
        );
      } else if (error.response?.status === 404) {
        throw new Error('Payment method not found');
      } else if (error.response?.status === 403) {
        throw new Error('Access denied. Unable to remove payment method.');
      } else if (error.response?.status >= 500) {
        throw new Error('Server error occurred while removing payment method');
      } else if (error.code === 'NETWORK_ERROR' || error.message === 'Network Error') {
        throw new Error('Network connection error. Please check your internet connection.');
      } else {
        throw new Error('Failed to remove payment method. Please try again.');
      }
    }
  }

  /**
   * Set a payment method as default.
   *
   * @param paymentMethodId The payment method ID to set as default
   * @param email Optional email parameter for admin access
   * @returns Promise that resolves when payment method is set as default
   * @throws Error with descriptive message if request fails
   */
  static async setDefaultPaymentMethod(paymentMethodId: string, email?: string): Promise<void> {
    try {
      const data = email ? { email } : {};
      await apiClient.post(
        `/api/student-balance/payment-methods/${paymentMethodId}/set-default/`,
        data,
      );
    } catch (error: any) {
      console.error('Error setting default payment method:', error);

      if (error.response?.status === 404) {
        throw new Error('Payment method not found');
      } else if (error.response?.status === 403) {
        throw new Error('Access denied. Unable to set default payment method.');
      } else if (error.response?.status >= 500) {
        throw new Error('Server error occurred while setting default payment method');
      } else if (error.code === 'NETWORK_ERROR' || error.message === 'Network Error') {
        throw new Error('Network connection error. Please check your internet connection.');
      } else {
        throw new Error('Failed to set default payment method. Please try again.');
      }
    }
  }
}

// Convenience exports for direct function access
export const { getPaymentMethods, addPaymentMethod, removePaymentMethod, setDefaultPaymentMethod } =
  PaymentMethodApiClient;
