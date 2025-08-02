/**
 * Transaction Management Screen - GitHub Issue #118
 *
 * Administrative interface for searching, viewing, and managing transactions
 * including bulk actions, detailed investigation, and transaction lifecycle management.
 */

import {
  Search,
  Filter,
  Download,
  RefreshCw,
  AlertCircle,
  Settings,
  Plus,
} from 'lucide-react-native';
import React, { useEffect, useState, useCallback } from 'react';
import { ScrollView } from 'react-native';

import { PaymentMonitoringApiClient } from '@/api/paymentMonitoringApi';
import BulkActionModal from '@/components/payment-monitoring/BulkActionModal';
import RefundConfirmationModal from '@/components/payment-monitoring/RefundConfirmationModal';
import TransactionDetailModal from '@/components/payment-monitoring/TransactionDetailModal';
import TransactionManagementTable from '@/components/payment-monitoring/TransactionManagementTable';
import TransactionSearchInterface from '@/components/payment-monitoring/TransactionSearchInterface';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Button } from '@/components/ui/button';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Modal, ModalBackdrop, ModalContent } from '@/components/ui/modal';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

// Import custom components (to be created)

// Import API and hooks
import { useTransactionWebSocket } from '@/hooks/usePaymentMonitoringWebSocket';
import type {
  TransactionMonitoring,
  PaginatedTransactionMonitoring,
  TransactionSearchFilters,
  SavedSearch,
} from '@/types/paymentMonitoring';

interface TransactionManagementState {
  selectedTransactions: string[];
  bulkAction: 'refund' | 'retry' | 'mark_fraudulent' | null;
  searchFilters: TransactionSearchFilters;
  savedSearches: SavedSearch[];
  activeSavedSearch?: string;
  sortBy: 'created_at' | 'amount' | 'status' | 'risk_score';
  sortOrder: 'asc' | 'desc';
  currentPage: number;
  pageSize: number;
}

interface ModalState {
  transactionDetail: TransactionMonitoring | null;
  bulkActionModal: boolean;
  refundConfirmation: TransactionMonitoring | null;
}

export default function TransactionManagement() {
  // State management
  const [state, setState] = useState<TransactionManagementState>({
    selectedTransactions: [],
    bulkAction: null,
    searchFilters: {},
    savedSearches: [],
    sortBy: 'created_at',
    sortOrder: 'desc',
    currentPage: 1,
    pageSize: 20,
  });

  const [modalState, setModalState] = useState<ModalState>({
    transactionDetail: null,
    bulkActionModal: false,
    refundConfirmation: null,
  });

  const [transactions, setTransactions] = useState<PaginatedTransactionMonitoring | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState(false);

  // WebSocket connection for real-time transaction updates
  const {
    isConnected: wsConnected,
    error: wsError,
    transactionUpdates,
    clearUpdates,
  } = useTransactionWebSocket(true);

  // Load transactions data
  const loadTransactions = async (filters?: TransactionSearchFilters, page?: number) => {
    try {
      setError(null);
      setLoading(true);

      const response = await PaymentMonitoringApiClient.getTransactions(
        filters || state.searchFilters,
        page || state.currentPage,
        state.pageSize
      );

      setTransactions(response);
    } catch (err: any) {
      console.error('Error loading transactions:', err);
      setError(err.message || 'Failed to load transactions');
    } finally {
      setLoading(false);
    }
  };

  // Handle real-time transaction updates
  useEffect(() => {
    if (transactionUpdates.length > 0 && transactions) {
      const updatedTransactions = { ...transactions };

      transactionUpdates.forEach(update => {
        const existingIndex = updatedTransactions.results.findIndex(
          t => t.id === update.transaction.id
        );

        if (update.action === 'created') {
          if (existingIndex === -1) {
            updatedTransactions.results.unshift(update.transaction);
            updatedTransactions.count += 1;
          }
        } else if (update.action === 'updated' || update.action === 'status_changed') {
          if (existingIndex !== -1) {
            updatedTransactions.results[existingIndex] = update.transaction;
          }
        }
      });

      setTransactions(updatedTransactions);
      clearUpdates();
    }
  }, [transactionUpdates, transactions, clearUpdates]);

  // Initial data load
  useEffect(() => {
    loadTransactions();
  }, [state.currentPage, state.pageSize, state.sortBy, state.sortOrder]);

  // Handle search filter changes
  const handleFiltersChange = useCallback((newFilters: TransactionSearchFilters) => {
    setState(prev => ({
      ...prev,
      searchFilters: newFilters,
      currentPage: 1, // Reset to first page when filtering
    }));
    loadTransactions(newFilters, 1);
  }, []);

  // Handle transaction selection
  const handleTransactionSelect = useCallback((transactionId: string) => {
    setState(prev => ({
      ...prev,
      selectedTransactions: prev.selectedTransactions.includes(transactionId)
        ? prev.selectedTransactions.filter(id => id !== transactionId)
        : [...prev.selectedTransactions, transactionId],
    }));
  }, []);

  // Handle bulk selection
  const handleBulkSelect = useCallback((transactionIds: string[]) => {
    setState(prev => ({
      ...prev,
      selectedTransactions: transactionIds,
    }));
  }, []);

  // Clear selection
  const clearSelection = useCallback(() => {
    setState(prev => ({
      ...prev,
      selectedTransactions: [],
      bulkAction: null,
    }));
  }, []);

  // Handle transaction detail view
  const handleViewTransaction = useCallback(async (transactionId: string) => {
    try {
      const transaction = await PaymentMonitoringApiClient.getTransactionDetail(transactionId);
      setModalState(prev => ({ ...prev, transactionDetail: transaction }));
    } catch (err: any) {
      console.error('Error loading transaction detail:', err);
      setError(err.message || 'Failed to load transaction details');
    }
  }, []);

  // Handle refund request
  const handleRefundRequest = useCallback((transaction: TransactionMonitoring) => {
    setModalState(prev => ({ ...prev, refundConfirmation: transaction }));
  }, []);

  // Handle bulk actions
  const handleBulkAction = useCallback((action: 'refund' | 'retry' | 'mark_fraudulent') => {
    setState(prev => ({ ...prev, bulkAction: action }));
    setModalState(prev => ({ ...prev, bulkActionModal: true }));
  }, []);

  // Process bulk action
  const processBulkAction = useCallback(
    async (action: string, options: any) => {
      try {
        setActionLoading(true);

        // Process each selected transaction
        const promises = state.selectedTransactions.map(async transactionId => {
          switch (action) {
            case 'refund':
              return PaymentMonitoringApiClient.processRefund({
                payment_intent_id: transactionId,
                reason: options.reason,
                reason_description: options.description,
                notify_customer: options.notifyCustomer,
              });
            case 'retry':
              return PaymentMonitoringApiClient.retryPayment({
                payment_intent_id: transactionId,
                retry_strategy: options.strategy,
              });
            // Add more bulk actions as needed
            default:
              throw new Error(`Unknown bulk action: ${action}`);
          }
        });

        await Promise.all(promises);

        // Refresh data and clear selection
        loadTransactions();
        clearSelection();
        setModalState(prev => ({ ...prev, bulkActionModal: false }));
      } catch (err: any) {
        console.error('Error processing bulk action:', err);
        setError(err.message || 'Failed to process bulk action');
      } finally {
        setActionLoading(false);
      }
    },
    [state.selectedTransactions, clearSelection]
  );

  // Handle pagination
  const handlePageChange = useCallback((page: number) => {
    setState(prev => ({ ...prev, currentPage: page }));
  }, []);

  // Handle sort change
  const handleSortChange = useCallback((sortBy: string, sortOrder: 'asc' | 'desc') => {
    setState(prev => ({
      ...prev,
      sortBy: sortBy as any,
      sortOrder,
      currentPage: 1,
    }));
  }, []);

  // Export transactions
  const handleExport = useCallback(async () => {
    try {
      setActionLoading(true);
      // Implementation for exporting transactions
      // This would typically call a backend endpoint to generate and download a report
      console.log('Exporting transactions with filters:', state.searchFilters);
    } catch (err: any) {
      console.error('Error exporting transactions:', err);
      setError(err.message || 'Failed to export transactions');
    } finally {
      setActionLoading(false);
    }
  }, [state.searchFilters]);

  if (loading && !transactions) {
    return (
      <VStack flex={1} className="justify-center items-center p-6">
        <Spinner size="large" />
        <Text className="mt-4 text-typography-600">Loading transactions...</Text>
      </VStack>
    );
  }

  return (
    <VStack flex={1} className="bg-background-0">
      {/* Header */}
      <VStack space="md" className="p-6 border-b border-border-200 bg-background-50">
        <HStack className="justify-between items-center">
          <VStack space="xs">
            <Heading size="xl" className="text-typography-900">
              Transaction Management
            </Heading>
            <HStack space="md" className="items-center">
              {wsConnected && (
                <Badge variant="success" className="flex-row items-center">
                  <Icon as={RefreshCw} size="xs" className="mr-1" />
                  <Text size="xs">Live updates</Text>
                </Badge>
              )}

              {transactions && (
                <Text size="sm" className="text-typography-500">
                  {transactions.count.toLocaleString()} total transactions
                </Text>
              )}
            </HStack>
          </VStack>

          <HStack space="sm" className="items-center">
            {/* Bulk Actions */}
            {state.selectedTransactions.length > 0 && (
              <HStack space="xs">
                <Badge variant="secondary">
                  <Text size="xs">{state.selectedTransactions.length} selected</Text>
                </Badge>

                <Button variant="outline" size="sm" onPress={() => handleBulkAction('refund')}>
                  <Text size="sm">Refund</Text>
                </Button>

                <Button variant="outline" size="sm" onPress={() => handleBulkAction('retry')}>
                  <Text size="sm">Retry</Text>
                </Button>

                <Button variant="outline" size="sm" onPress={clearSelection}>
                  <Text size="sm">Clear</Text>
                </Button>
              </HStack>
            )}

            {/* Export */}
            <Button variant="outline" size="sm" onPress={handleExport} disabled={actionLoading}>
              <Icon as={Download} size="xs" />
              <Text size="sm" className="ml-1">
                Export
              </Text>
            </Button>

            {/* Refresh */}
            <Button
              variant="outline"
              size="sm"
              onPress={() => loadTransactions()}
              disabled={loading}
            >
              <Icon as={RefreshCw} size="xs" className={loading ? 'animate-spin' : ''} />
            </Button>
          </HStack>
        </HStack>

        {/* Error Alert */}
        {error && (
          <Alert variant="destructive">
            <Icon as={AlertCircle} size="sm" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
      </VStack>

      {/* Main Content */}
      <VStack flex={1} space="md" className="p-6">
        {/* Search Interface */}
        <TransactionSearchInterface
          filters={state.searchFilters}
          onFiltersChange={handleFiltersChange}
          savedSearches={state.savedSearches}
          activeSavedSearch={state.activeSavedSearch}
          loading={loading}
        />

        {/* Transaction Table */}
        <Box flex={1}>
          <TransactionManagementTable
            transactions={transactions}
            selectedTransactions={state.selectedTransactions}
            onTransactionSelect={handleTransactionSelect}
            onBulkSelect={handleBulkSelect}
            onViewTransaction={handleViewTransaction}
            onRefundRequest={handleRefundRequest}
            onSortChange={handleSortChange}
            onPageChange={handlePageChange}
            loading={loading}
            sortBy={state.sortBy}
            sortOrder={state.sortOrder}
            currentPage={state.currentPage}
            pageSize={state.pageSize}
          />
        </Box>
      </VStack>

      {/* Modals */}

      {/* Transaction Detail Modal */}
      <TransactionDetailModal
        transaction={modalState.transactionDetail}
        isOpen={!!modalState.transactionDetail}
        onClose={() => setModalState(prev => ({ ...prev, transactionDetail: null }))}
        onRefund={handleRefundRequest}
        onRetry={transaction => {
          // Handle retry action
          console.log('Retry transaction:', transaction.id);
        }}
      />

      {/* Bulk Action Modal */}
      <BulkActionModal
        selectedTransactions={
          transactions?.results.filter(t => state.selectedTransactions.includes(t.id)) || []
        }
        action={state.bulkAction || 'refund'}
        isOpen={modalState.bulkActionModal}
        onClose={() => setModalState(prev => ({ ...prev, bulkActionModal: false }))}
        onConfirm={processBulkAction}
        loading={actionLoading}
      />

      {/* Refund Confirmation Modal */}
      <RefundConfirmationModal
        transaction={modalState.refundConfirmation}
        isOpen={!!modalState.refundConfirmation}
        onClose={() => setModalState(prev => ({ ...prev, refundConfirmation: null }))}
        onConfirm={async request => {
          try {
            setActionLoading(true);
            await PaymentMonitoringApiClient.processRefund(request);
            loadTransactions(); // Refresh data
            setModalState(prev => ({ ...prev, refundConfirmation: null }));
          } catch (err: any) {
            console.error('Error processing refund:', err);
            setError(err.message || 'Failed to process refund');
          } finally {
            setActionLoading(false);
          }
        }}
        loading={actionLoading}
      />
    </VStack>
  );
}
