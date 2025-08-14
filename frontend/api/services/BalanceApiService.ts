/**
 * Balance API Service
 * Handles all balance and transaction-related API operations using dependency injection
 */

import { ApiClient } from '../client/ApiClient';

export interface Balance {
  available_balance: number;
  pending_balance: number;
  currency: string;
  last_updated: string;
}

export interface Transaction {
  id: string;
  type: 'credit' | 'debit';
  amount: number;
  currency: string;
  description: string;
  status: 'pending' | 'completed' | 'failed';
  created_at: string;
  reference_id?: string;
}

export interface TransactionFilters {
  type?: 'credit' | 'debit';
  status?: 'pending' | 'completed' | 'failed';
  start_date?: string;
  end_date?: string;
  limit?: number;
  offset?: number;
}

export class BalanceApiService {
  constructor(private readonly apiClient: ApiClient) {}

  /**
   * Get user's current balance
   */
  async getBalance(): Promise<Balance> {
    const response = await this.apiClient.get<Balance>('/balance/');
    return response.data;
  }

  /**
   * Get transaction history
   */
  async getTransactions(filters?: TransactionFilters): Promise<Transaction[]> {
    const params = new URLSearchParams();

    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined) {
          params.append(key, value.toString());
        }
      });
    }

    const url = `/balance/transactions/${params.toString() ? `?${params}` : ''}`;
    const response = await this.apiClient.get<Transaction[]>(url);
    return response.data;
  }

  /**
   * Get a specific transaction
   */
  async getTransaction(transactionId: string): Promise<Transaction> {
    const response = await this.apiClient.get<Transaction>(
      `/balance/transactions/${transactionId}/`
    );
    return response.data;
  }
}
