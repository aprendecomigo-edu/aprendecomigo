/**
 * API client functions for receipt-related operations.
 *
 * Handles communication with the backend receipt APIs including
 * receipt listing, generation, and download functionality.
 */

import { Linking, Platform } from 'react-native';

import apiClient from './apiClient';

export interface Receipt {
  id: string;
  transaction_id: string;
  purchase_date: string;
  amount: string;
  plan_name: string;
  receipt_number: string;
  status: 'pending' | 'generated' | 'failed';
  download_url?: string;
  generated_at?: string;
}

export interface ReceiptGenerationResponse {
  success: boolean;
  receipt_id: string;
  message: string;
  status: 'pending' | 'generated' | 'failed';
}

/**
 * Receipt API client with comprehensive error handling and type safety.
 */
export class ReceiptApiClient {
  /**
   * Get all receipts for the authenticated student.
   *
   * @param email Optional email parameter for admin access
   * @returns Promise resolving to array of receipts
   * @throws Error with descriptive message if request fails
   */
  static async getReceipts(email?: string): Promise<Receipt[]> {
    try {
      const params = email ? { email } : {};
      const response = await apiClient.get('/api/student-balance/receipts/', { params });

      if (!Array.isArray(response.data)) {
        throw new Error('Invalid response format: expected array of receipts');
      }

      return response.data.map((receipt: any) => ({
        id: receipt.id,
        transaction_id: receipt.transaction_id,
        purchase_date: receipt.purchase_date,
        amount: receipt.amount,
        plan_name: receipt.plan_name,
        receipt_number: receipt.receipt_number,
        status: receipt.status,
        download_url: receipt.download_url,
        generated_at: receipt.generated_at,
      }));
    } catch (error: any) {
      console.error('Error fetching receipts:', error);

      if (error.response?.status === 404) {
        throw new Error('Student not found');
      } else if (error.response?.status === 403) {
        throw new Error('Access denied. Unable to retrieve receipts.');
      } else if (error.response?.status >= 500) {
        throw new Error('Server error occurred while loading receipts');
      } else if (error.code === 'NETWORK_ERROR' || error.message === 'Network Error') {
        throw new Error('Network connection error. Please check your internet connection.');
      } else {
        throw new Error('Failed to load receipts. Please try again.');
      }
    }
  }

  /**
   * Generate a receipt for a specific transaction.
   *
   * @param transactionId The transaction ID to generate receipt for
   * @param email Optional email parameter for admin access
   * @returns Promise resolving to receipt generation response
   * @throws Error with descriptive message if request fails
   */
  static async generateReceipt(
    transactionId: string,
    email?: string
  ): Promise<ReceiptGenerationResponse> {
    try {
      const data = email
        ? { transaction_id: transactionId, email }
        : { transaction_id: transactionId };
      const response = await apiClient.post('/api/student-balance/receipts/generate/', data);

      return {
        success: response.data.success,
        receipt_id: response.data.receipt_id,
        message: response.data.message,
        status: response.data.status,
      };
    } catch (error: any) {
      console.error('Error generating receipt:', error);

      if (error.response?.status === 400) {
        throw new Error(error.response.data?.message || 'Invalid receipt generation request');
      } else if (error.response?.status === 404) {
        throw new Error('Transaction not found');
      } else if (error.response?.status === 409) {
        throw new Error('Receipt already exists for this transaction');
      } else if (error.response?.status >= 500) {
        throw new Error('Server error occurred while generating receipt');
      } else if (error.code === 'NETWORK_ERROR' || error.message === 'Network Error') {
        throw new Error('Network connection error. Please check your internet connection.');
      } else {
        throw new Error('Failed to generate receipt. Please try again.');
      }
    }
  }

  /**
   * Download a receipt by ID.
   *
   * @param receiptId The receipt ID to download
   * @param email Optional email parameter for admin access
   * @returns Promise that resolves when download is initiated
   * @throws Error with descriptive message if request fails
   */
  static async downloadReceipt(receiptId: string, email?: string): Promise<void> {
    try {
      const params = email ? { email } : {};
      const response = await apiClient.get(`/api/student-balance/receipts/${receiptId}/download/`, {
        params,
        responseType: 'blob', // Important for file downloads
      });

      if (Platform.OS === 'web') {
        // Web platform: Create blob URL and trigger download
        const blob = new Blob([response.data], { type: 'application/pdf' });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `receipt-${receiptId}.pdf`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
      } else {
        // Mobile platforms: Use Linking API to open file
        if (response.data.download_url) {
          const supported = await Linking.canOpenURL(response.data.download_url);
          if (supported) {
            await Linking.openURL(response.data.download_url);
          } else {
            throw new Error('Cannot open receipt file on this device');
          }
        } else {
          throw new Error('Download URL not provided by server');
        }
      }
    } catch (error: any) {
      console.error('Error downloading receipt:', error);

      if (error.response?.status === 404) {
        throw new Error('Receipt not found');
      } else if (error.response?.status === 403) {
        throw new Error('Access denied. Unable to download receipt.');
      } else if (error.response?.status >= 500) {
        throw new Error('Server error occurred while downloading receipt');
      } else if (error.code === 'NETWORK_ERROR' || error.message === 'Network Error') {
        throw new Error('Network connection error. Please check your internet connection.');
      } else {
        throw new Error('Failed to download receipt. Please try again.');
      }
    }
  }

  /**
   * Get receipt preview URL for modal display.
   *
   * @param receiptId The receipt ID to preview
   * @param email Optional email parameter for admin access
   * @returns Promise resolving to preview URL
   * @throws Error with descriptive message if request fails
   */
  static async getReceiptPreviewUrl(receiptId: string, email?: string): Promise<string> {
    try {
      const params = email ? { email, preview: 'true' } : { preview: 'true' };
      const response = await apiClient.get(`/api/student-balance/receipts/${receiptId}/download/`, {
        params,
      });

      if (!response.data.preview_url) {
        throw new Error('Preview URL not available');
      }

      return response.data.preview_url;
    } catch (error: any) {
      console.error('Error getting receipt preview:', error);

      if (error.response?.status === 404) {
        throw new Error('Receipt not found');
      } else if (error.response?.status === 403) {
        throw new Error('Access denied. Unable to preview receipt.');
      } else if (error.response?.status >= 500) {
        throw new Error('Server error occurred while loading receipt preview');
      } else if (error.code === 'NETWORK_ERROR' || error.message === 'Network Error') {
        throw new Error('Network connection error. Please check your internet connection.');
      } else {
        throw new Error('Failed to load receipt preview. Please try again.');
      }
    }
  }
}

// Convenience exports for direct function access
export const { getReceipts, generateReceipt, downloadReceipt, getReceiptPreviewUrl } =
  ReceiptApiClient;
