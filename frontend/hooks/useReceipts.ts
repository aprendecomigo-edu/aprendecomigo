/**
 * Custom hook for managing receipt data and operations.
 *
 * Provides state management for receipt listing, generation, and download functionality.
 */

import { useState, useCallback, useEffect } from 'react';

import { ReceiptApiClient, type Receipt, type ReceiptGenerationResponse } from '@/api/receiptApi';

interface UseReceiptsResult {
  // Data state
  receipts: Receipt[];
  loading: boolean;
  error: string | null;

  // Operation states
  generating: boolean;
  downloading: boolean;
  generationError: string | null;
  downloadError: string | null;

  // Actions
  refreshReceipts: () => Promise<void>;
  generateReceipt: (transactionId: string) => Promise<ReceiptGenerationResponse | null>;
  downloadReceipt: (receiptId: string) => Promise<void>;
  getPreviewUrl: (receiptId: string) => Promise<string | null>;
  clearErrors: () => void;
}

/**
 * Hook for managing receipt data and operations.
 */
export function useReceipts(email?: string): UseReceiptsResult {
  // Receipt data state
  const [receipts, setReceipts] = useState<Receipt[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Operation states
  const [generating, setGenerating] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [generationError, setGenerationError] = useState<string | null>(null);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  // Refresh receipts data
  const refreshReceipts = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const receiptsData = await ReceiptApiClient.getReceipts(email);
      setReceipts(receiptsData);
    } catch (error: any) {
      console.error('Error fetching receipts:', error);
      setError(error.message || 'Failed to load receipts');
      setReceipts([]);
    } finally {
      setLoading(false);
    }
  }, [email]);

  // Generate receipt for transaction
  const generateReceipt = useCallback(
    async (transactionId: string): Promise<ReceiptGenerationResponse | null> => {
      setGenerating(true);
      setGenerationError(null);

      try {
        const result = await ReceiptApiClient.generateReceipt(transactionId, email);

        // Refresh receipts to get the new one
        await refreshReceipts();

        return result;
      } catch (error: any) {
        console.error('Error generating receipt:', error);
        setGenerationError(error.message || 'Failed to generate receipt');
        return null;
      } finally {
        setGenerating(false);
      }
    },
    [email, refreshReceipts]
  );

  // Download receipt
  const downloadReceipt = useCallback(
    async (receiptId: string): Promise<void> => {
      setDownloading(true);
      setDownloadError(null);

      try {
        await ReceiptApiClient.downloadReceipt(receiptId, email);
      } catch (error: any) {
        console.error('Error downloading receipt:', error);
        setDownloadError(error.message || 'Failed to download receipt');
        throw error; // Re-throw to allow component to handle
      } finally {
        setDownloading(false);
      }
    },
    [email]
  );

  // Get receipt preview URL
  const getPreviewUrl = useCallback(
    async (receiptId: string): Promise<string | null> => {
      try {
        return await ReceiptApiClient.getReceiptPreviewUrl(receiptId, email);
      } catch (error: any) {
        console.error('Error getting receipt preview:', error);
        setError(error.message || 'Failed to load receipt preview');
        return null;
      }
    },
    [email]
  );

  // Clear all errors
  const clearErrors = useCallback(() => {
    setError(null);
    setGenerationError(null);
    setDownloadError(null);
  }, []);

  // Initial data fetch
  useEffect(() => {
    refreshReceipts();
  }, [refreshReceipts]);

  return {
    receipts,
    loading,
    error,
    generating,
    downloading,
    generationError,
    downloadError,
    refreshReceipts,
    generateReceipt,
    downloadReceipt,
    getPreviewUrl,
    clearErrors,
  };
}
