/**
 * API client functions for payment monitoring and administrative operations.
 *
 * Handles communication with the backend payment monitoring APIs including
 * dashboard metrics, transaction management, refunds, disputes, and fraud detection.
 */

import apiClient from './apiClient';

import type {
  PaymentMetrics,
  PaymentTrendData,
  WebhookStatus,
  TransactionMonitoring,
  PaginatedTransactionMonitoring,
  TransactionSearchFilters,
  RefundRequest,
  RefundResponse,
  RefundRecord,
  DisputeRecord,
  DisputeEvidenceRequest,
  DisputeEvidenceResponse,
  FraudAlert,
  FraudAlertAction,
  FraudAlertResponse,
  PaymentRetryRecord,
  PaymentRetryRequest,
  PaymentRetryResponse,
  PaginatedAuditLog,
  AdminPermissions,
  TwoFactorAuthState,
} from '@/types/paymentMonitoring';

/**
 * Payment Monitoring API client with comprehensive error handling and type safety.
 */
export class PaymentMonitoringApiClient {
  /**
   * Get dashboard metrics for specified time range.
   *
   * @param timeRange Time range for metrics ('last_24h', 'last_7d', 'last_30d', or custom)
   * @param customRange Optional custom date range
   * @returns Promise resolving to payment metrics
   * @throws Error with descriptive message if request fails
   */
  static async getDashboardMetrics(
    timeRange: 'last_24h' | 'last_7d' | 'last_30d' | 'custom' = 'last_24h',
    customRange?: { start_date: string; end_date: string },
  ): Promise<PaymentMetrics> {
    try {
      const params: any = { time_range: timeRange };
      if (timeRange === 'custom' && customRange) {
        params.start_date = customRange.start_date;
        params.end_date = customRange.end_date;
      }

      const response = await apiClient.get('/api/admin/payments/metrics/', { params });
      return response.data;
    } catch (error: any) {
      console.error('Error fetching dashboard metrics:', error);

      if (error.response?.status === 403) {
        throw new Error('Access denied. Admin privileges required.');
      } else if (error.response?.status === 401) {
        throw new Error('Authentication required. Please log in.');
      } else if (error.response?.status >= 500) {
        throw new Error('Server error occurred while loading metrics');
      } else if (error.code === 'NETWORK_ERROR' || error.message === 'Network Error') {
        throw new Error('Network connection error. Please check your internet connection.');
      } else {
        throw new Error('Failed to load dashboard metrics. Please try again.');
      }
    }
  }

  /**
   * Get payment trend data for charts.
   *
   * @param timeRange Time range for trend data
   * @param customRange Optional custom date range
   * @returns Promise resolving to trend data
   * @throws Error with descriptive message if request fails
   */
  static async getPaymentTrends(
    timeRange: 'last_24h' | 'last_7d' | 'last_30d' | 'custom' = 'last_7d',
    customRange?: { start_date: string; end_date: string },
  ): Promise<PaymentTrendData> {
    try {
      const params: any = { time_range: timeRange };
      if (timeRange === 'custom' && customRange) {
        params.start_date = customRange.start_date;
        params.end_date = customRange.end_date;
      }

      const response = await apiClient.get('/api/admin/payments/trends/', { params });
      return response.data;
    } catch (error: any) {
      console.error('Error fetching payment trends:', error);

      if (error.response?.status === 403) {
        throw new Error('Access denied. Admin privileges required.');
      } else if (error.response?.status >= 500) {
        throw new Error('Server error occurred while loading trend data');
      } else if (error.code === 'NETWORK_ERROR' || error.message === 'Network Error') {
        throw new Error('Network connection error. Please check your internet connection.');
      } else {
        throw new Error('Failed to load payment trends. Please try again.');
      }
    }
  }

  /**
   * Get webhook status information.
   *
   * @returns Promise resolving to webhook status array
   * @throws Error with descriptive message if request fails
   */
  static async getWebhookStatus(): Promise<WebhookStatus[]> {
    try {
      const response = await apiClient.get('/api/admin/webhooks/status/');
      return Array.isArray(response.data) ? response.data : [response.data];
    } catch (error: any) {
      console.error('Error fetching webhook status:', error);

      if (error.response?.status === 403) {
        throw new Error('Access denied. Admin privileges required.');
      } else if (error.response?.status >= 500) {
        throw new Error('Server error occurred while loading webhook status');
      } else if (error.code === 'NETWORK_ERROR' || error.message === 'Network Error') {
        throw new Error('Network connection error. Please check your internet connection.');
      } else {
        throw new Error('Failed to load webhook status. Please try again.');
      }
    }
  }

  /**
   * Get transaction monitoring data with search and filtering.
   *
   * @param filters Search and filter options
   * @param page Page number for pagination
   * @param pageSize Number of items per page
   * @returns Promise resolving to paginated transaction monitoring data
   * @throws Error with descriptive message if request fails
   */
  static async getTransactions(
    filters: TransactionSearchFilters = {},
    page: number = 1,
    pageSize: number = 20,
  ): Promise<PaginatedTransactionMonitoring> {
    try {
      const params: any = {
        page,
        page_size: pageSize,
        ...filters,
      };

      const response = await apiClient.get('/api/admin/payments/transactions/', { params });
      return response.data;
    } catch (error: any) {
      console.error('Error fetching transactions:', error);

      if (error.response?.status === 400) {
        throw new Error('Invalid search criteria. Please check your filters.');
      } else if (error.response?.status === 403) {
        throw new Error('Access denied. Admin privileges required.');
      } else if (error.response?.status >= 500) {
        throw new Error('Server error occurred while loading transactions');
      } else if (error.code === 'NETWORK_ERROR' || error.message === 'Network Error') {
        throw new Error('Network connection error. Please check your internet connection.');
      } else {
        throw new Error('Failed to load transactions. Please try again.');
      }
    }
  }

  /**
   * Get detailed information about a specific transaction.
   *
   * @param paymentIntentId Payment intent ID
   * @returns Promise resolving to transaction details
   * @throws Error with descriptive message if request fails
   */
  static async getTransactionDetail(paymentIntentId: string): Promise<TransactionMonitoring> {
    try {
      const response = await apiClient.get(`/api/admin/payments/transactions/${paymentIntentId}/`);
      return response.data;
    } catch (error: any) {
      console.error('Error fetching transaction detail:', error);

      if (error.response?.status === 404) {
        throw new Error('Transaction not found');
      } else if (error.response?.status === 403) {
        throw new Error('Access denied. Admin privileges required.');
      } else if (error.response?.status >= 500) {
        throw new Error('Server error occurred while loading transaction details');
      } else if (error.code === 'NETWORK_ERROR' || error.message === 'Network Error') {
        throw new Error('Network connection error. Please check your internet connection.');
      } else {
        throw new Error('Failed to load transaction details. Please try again.');
      }
    }
  }

  /**
   * Process a refund for a payment.
   *
   * @param request Refund request data
   * @returns Promise resolving to refund response
   * @throws Error with descriptive message if request fails
   */
  static async processRefund(request: RefundRequest): Promise<RefundResponse> {
    try {
      const response = await apiClient.post('/api/admin/payments/refunds/', request);
      return response.data;
    } catch (error: any) {
      console.error('Error processing refund:', error);

      if (error.response?.status === 400) {
        const errorData = error.response.data;
        return {
          success: false,
          error_type: errorData.error_type || 'validation_error',
          failure_reason: errorData.message || 'Invalid refund request',
        };
      } else if (error.response?.status === 403) {
        throw new Error('Access denied. Refund processing privileges required.');
      } else if (error.response?.status === 404) {
        throw new Error('Payment not found or not eligible for refund');
      } else if (error.response?.status === 429) {
        throw new Error('Too many refund requests. Please try again later.');
      } else if (error.response?.status >= 500) {
        throw new Error('Server error occurred while processing refund');
      } else if (error.code === 'NETWORK_ERROR' || error.message === 'Network Error') {
        throw new Error('Network connection error. Please check your internet connection.');
      } else {
        const errorMessage = error.response?.data?.message || 'Failed to process refund';
        throw new Error(errorMessage);
      }
    }
  }

  /**
   * Get refund history and status.
   *
   * @param page Page number for pagination
   * @param pageSize Number of items per page
   * @param filters Optional filters for refunds
   * @returns Promise resolving to refund records
   * @throws Error with descriptive message if request fails
   */
  static async getRefunds(
    page: number = 1,
    pageSize: number = 20,
    filters: { status?: string; date_from?: string; date_to?: string } = {},
  ): Promise<{
    count: number;
    next: string | null;
    previous: string | null;
    results: RefundRecord[];
  }> {
    try {
      const params = { page, page_size: pageSize, ...filters };
      const response = await apiClient.get('/api/admin/payments/refunds/', { params });
      return response.data;
    } catch (error: any) {
      console.error('Error fetching refunds:', error);

      if (error.response?.status === 403) {
        throw new Error('Access denied. Admin privileges required.');
      } else if (error.response?.status >= 500) {
        throw new Error('Server error occurred while loading refunds');
      } else if (error.code === 'NETWORK_ERROR' || error.message === 'Network Error') {
        throw new Error('Network connection error. Please check your internet connection.');
      } else {
        throw new Error('Failed to load refunds. Please try again.');
      }
    }
  }

  /**
   * Get dispute records and management data.
   *
   * @param page Page number for pagination
   * @param pageSize Number of items per page
   * @param filters Optional filters for disputes
   * @returns Promise resolving to dispute records
   * @throws Error with descriptive message if request fails
   */
  static async getDisputes(
    page: number = 1,
    pageSize: number = 20,
    filters: { status?: string; evidence_due?: boolean } = {},
  ): Promise<{
    count: number;
    next: string | null;
    previous: string | null;
    results: DisputeRecord[];
  }> {
    try {
      const params = { page, page_size: pageSize, ...filters };
      const response = await apiClient.get('/api/admin/payments/disputes/', { params });
      return response.data;
    } catch (error: any) {
      console.error('Error fetching disputes:', error);

      if (error.response?.status === 403) {
        throw new Error('Access denied. Admin privileges required.');
      } else if (error.response?.status >= 500) {
        throw new Error('Server error occurred while loading disputes');
      } else if (error.code === 'NETWORK_ERROR' || error.message === 'Network Error') {
        throw new Error('Network connection error. Please check your internet connection.');
      } else {
        throw new Error('Failed to load disputes. Please try again.');
      }
    }
  }

  /**
   * Submit evidence for a dispute.
   *
   * @param request Dispute evidence request
   * @returns Promise resolving to evidence submission response
   * @throws Error with descriptive message if request fails
   */
  static async submitDisputeEvidence(
    request: DisputeEvidenceRequest,
  ): Promise<DisputeEvidenceResponse> {
    try {
      const response = await apiClient.post(
        `/api/admin/payments/disputes/${request.dispute_id}/evidence/`,
        request,
      );
      return response.data;
    } catch (error: any) {
      console.error('Error submitting dispute evidence:', error);

      if (error.response?.status === 400) {
        const errorData = error.response.data;
        return {
          success: false,
          message: errorData.message || 'Invalid evidence submission',
          error_type: errorData.error_type || 'validation_error',
        };
      } else if (error.response?.status === 403) {
        throw new Error('Access denied. Dispute management privileges required.');
      } else if (error.response?.status === 404) {
        throw new Error('Dispute not found');
      } else if (error.response?.status >= 500) {
        throw new Error('Server error occurred while submitting evidence');
      } else if (error.code === 'NETWORK_ERROR' || error.message === 'Network Error') {
        throw new Error('Network connection error. Please check your internet connection.');
      } else {
        const errorMessage = error.response?.data?.message || 'Failed to submit dispute evidence';
        throw new Error(errorMessage);
      }
    }
  }

  /**
   * Get fraud alerts.
   *
   * @param page Page number for pagination
   * @param pageSize Number of items per page
   * @param filters Optional filters for fraud alerts
   * @returns Promise resolving to fraud alerts
   * @throws Error with descriptive message if request fails
   */
  static async getFraudAlerts(
    page: number = 1,
    pageSize: number = 20,
    filters: { status?: string; risk_level?: string } = {},
  ): Promise<{
    count: number;
    next: string | null;
    previous: string | null;
    results: FraudAlert[];
  }> {
    try {
      const params = { page, page_size: pageSize, ...filters };
      const response = await apiClient.get('/api/admin/payments/fraud/', { params });
      return response.data;
    } catch (error: any) {
      console.error('Error fetching fraud alerts:', error);

      if (error.response?.status === 403) {
        throw new Error('Access denied. Admin privileges required.');
      } else if (error.response?.status >= 500) {
        throw new Error('Server error occurred while loading fraud alerts');
      } else if (error.code === 'NETWORK_ERROR' || error.message === 'Network Error') {
        throw new Error('Network connection error. Please check your internet connection.');
      } else {
        throw new Error('Failed to load fraud alerts. Please try again.');
      }
    }
  }

  /**
   * Update a fraud alert status.
   *
   * @param action Fraud alert action
   * @returns Promise resolving to fraud alert response
   * @throws Error with descriptive message if request fails
   */
  static async updateFraudAlert(action: FraudAlertAction): Promise<FraudAlertResponse> {
    try {
      const response = await apiClient.patch(
        `/api/admin/payments/fraud/${action.alert_id}/`,
        action,
      );
      return response.data;
    } catch (error: any) {
      console.error('Error updating fraud alert:', error);

      if (error.response?.status === 400) {
        const errorData = error.response.data;
        return {
          success: false,
          message: errorData.message || 'Invalid fraud alert action',
          error_type: errorData.error_type || 'validation_error',
        };
      } else if (error.response?.status === 403) {
        throw new Error('Access denied. Fraud investigation privileges required.');
      } else if (error.response?.status === 404) {
        throw new Error('Fraud alert not found');
      } else if (error.response?.status >= 500) {
        throw new Error('Server error occurred while updating fraud alert');
      } else if (error.code === 'NETWORK_ERROR' || error.message === 'Network Error') {
        throw new Error('Network connection error. Please check your internet connection.');
      } else {
        const errorMessage = error.response?.data?.message || 'Failed to update fraud alert';
        throw new Error(errorMessage);
      }
    }
  }

  /**
   * Get payment retry records.
   *
   * @param page Page number for pagination
   * @param pageSize Number of items per page
   * @param filters Optional filters for payment retries
   * @returns Promise resolving to payment retry records
   * @throws Error with descriptive message if request fails
   */
  static async getPaymentRetries(
    page: number = 1,
    pageSize: number = 20,
    filters: { status?: string } = {},
  ): Promise<{
    count: number;
    next: string | null;
    previous: string | null;
    results: PaymentRetryRecord[];
  }> {
    try {
      const params = { page, page_size: pageSize, ...filters };
      const response = await apiClient.get('/api/admin/payments/retries/', { params });
      return response.data;
    } catch (error: any) {
      console.error('Error fetching payment retries:', error);

      if (error.response?.status === 403) {
        throw new Error('Access denied. Admin privileges required.');
      } else if (error.response?.status >= 500) {
        throw new Error('Server error occurred while loading payment retries');
      } else if (error.code === 'NETWORK_ERROR' || error.message === 'Network Error') {
        throw new Error('Network connection error. Please check your internet connection.');
      } else {
        throw new Error('Failed to load payment retries. Please try again.');
      }
    }
  }

  /**
   * Retry a failed payment.
   *
   * @param request Payment retry request
   * @returns Promise resolving to payment retry response
   * @throws Error with descriptive message if request fails
   */
  static async retryPayment(request: PaymentRetryRequest): Promise<PaymentRetryResponse> {
    try {
      const response = await apiClient.post('/api/admin/payments/retries/', request);
      return response.data;
    } catch (error: any) {
      console.error('Error retrying payment:', error);

      if (error.response?.status === 400) {
        const errorData = error.response.data;
        return {
          success: false,
          message: errorData.message || 'Invalid payment retry request',
          error_type: errorData.error_type || 'validation_error',
        };
      } else if (error.response?.status === 403) {
        throw new Error('Access denied. Payment retry privileges required.');
      } else if (error.response?.status === 404) {
        throw new Error('Payment not found or not eligible for retry');
      } else if (error.response?.status >= 500) {
        throw new Error('Server error occurred while retrying payment');
      } else if (error.code === 'NETWORK_ERROR' || error.message === 'Network Error') {
        throw new Error('Network connection error. Please check your internet connection.');
      } else {
        const errorMessage = error.response?.data?.message || 'Failed to retry payment';
        throw new Error(errorMessage);
      }
    }
  }

  /**
   * Get audit log entries.
   *
   * @param page Page number for pagination
   * @param pageSize Number of items per page
   * @param filters Optional filters for audit log
   * @returns Promise resolving to paginated audit log
   * @throws Error with descriptive message if request fails
   */
  static async getAuditLog(
    page: number = 1,
    pageSize: number = 50,
    filters: {
      action_type?: string;
      resource_type?: string;
      performed_by?: string;
      date_from?: string;
      date_to?: string;
    } = {},
  ): Promise<PaginatedAuditLog> {
    try {
      const params = { page, page_size: pageSize, ...filters };
      const response = await apiClient.get('/api/admin/payments/audit-log/', { params });
      return response.data;
    } catch (error: any) {
      console.error('Error fetching audit log:', error);

      if (error.response?.status === 403) {
        throw new Error('Access denied. Audit log access privileges required.');
      } else if (error.response?.status >= 500) {
        throw new Error('Server error occurred while loading audit log');
      } else if (error.code === 'NETWORK_ERROR' || error.message === 'Network Error') {
        throw new Error('Network connection error. Please check your internet connection.');
      } else {
        throw new Error('Failed to load audit log. Please try again.');
      }
    }
  }

  /**
   * Get admin permissions for current user.
   *
   * @returns Promise resolving to admin permissions
   * @throws Error with descriptive message if request fails
   */
  static async getAdminPermissions(): Promise<AdminPermissions> {
    try {
      const response = await apiClient.get('/api/admin/payments/permissions/');
      return response.data;
    } catch (error: any) {
      console.error('Error fetching admin permissions:', error);

      if (error.response?.status === 403) {
        throw new Error('Access denied. Admin account required.');
      } else if (error.response?.status === 401) {
        throw new Error('Authentication required. Please log in.');
      } else if (error.response?.status >= 500) {
        throw new Error('Server error occurred while checking permissions');
      } else if (error.code === 'NETWORK_ERROR' || error.message === 'Network Error') {
        throw new Error('Network connection error. Please check your internet connection.');
      } else {
        throw new Error('Failed to load admin permissions. Please try again.');
      }
    }
  }

  /**
   * Verify two-factor authentication for sensitive operations.
   *
   * @param token Two-factor authentication token
   * @returns Promise resolving to 2FA verification result
   * @throws Error with descriptive message if request fails
   */
  static async verifyTwoFactor(token: string): Promise<TwoFactorAuthState> {
    try {
      const response = await apiClient.post('/api/admin/payments/2fa/verify/', { token });
      return response.data;
    } catch (error: any) {
      console.error('Error verifying two-factor authentication:', error);

      if (error.response?.status === 400) {
        throw new Error('Invalid two-factor authentication token');
      } else if (error.response?.status === 403) {
        throw new Error('Two-factor authentication failed');
      } else if (error.response?.status >= 500) {
        throw new Error('Server error occurred during authentication');
      } else if (error.code === 'NETWORK_ERROR' || error.message === 'Network Error') {
        throw new Error('Network connection error. Please check your internet connection.');
      } else {
        throw new Error('Failed to verify two-factor authentication. Please try again.');
      }
    }
  }
}

// Convenience exports for direct function access
export const {
  getDashboardMetrics,
  getPaymentTrends,
  getWebhookStatus,
  getTransactions,
  getTransactionDetail,
  processRefund,
  getRefunds,
  getDisputes,
  submitDisputeEvidence,
  getFraudAlerts,
  updateFraudAlert,
  getPaymentRetries,
  retryPayment,
  getAuditLog,
  getAdminPermissions,
  verifyTwoFactor,
} = PaymentMonitoringApiClient;
