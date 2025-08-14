/**
 * Payment API Service
 * Handles all payment-related API operations using dependency injection
 */

import { ApiClient } from '../client/ApiClient';

export interface PaymentMethod {
  id: string;
  type: string;
  last_four?: string;
  brand?: string;
  is_default?: boolean;
}

export interface CreatePaymentMethodData {
  payment_method_id: string;
  set_as_default?: boolean;
}

export interface PaymentData {
  amount: number;
  currency?: string;
  payment_method_id?: string;
  description?: string;
}

export interface PaymentResponse {
  paymentId: string;
  status: string;
  amount: number;
  currency: string;
}

export class PaymentApiService {
  constructor(private readonly apiClient: ApiClient) {}

  /**
   * Get user's payment methods
   */
  async getPaymentMethods(): Promise<PaymentMethod[]> {
    const response = await this.apiClient.get<PaymentMethod[]>('/payments/methods/');
    return response.data;
  }

  /**
   * Create a new payment method
   */
  async createPaymentMethod(data: CreatePaymentMethodData): Promise<PaymentMethod> {
    const response = await this.apiClient.post<PaymentMethod>('/payments/methods/', data);
    return response.data;
  }

  /**
   * Delete a payment method
   */
  async deletePaymentMethod(paymentMethodId: string): Promise<void> {
    await this.apiClient.delete(`/payments/methods/${paymentMethodId}/`);
  }

  /**
   * Process a payment
   */
  async processPayment(data: PaymentData): Promise<PaymentResponse> {
    const response = await this.apiClient.post<PaymentResponse>('/payments/process/', data);
    return response.data;
  }

  /**
   * Get payment history
   */
  async getPaymentHistory(): Promise<PaymentResponse[]> {
    const response = await this.apiClient.get<PaymentResponse[]>('/payments/history/');
    return response.data;
  }
}
