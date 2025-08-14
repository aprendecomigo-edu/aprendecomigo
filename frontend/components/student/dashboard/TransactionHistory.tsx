/**
 * Transaction History Component
 *
 * Displays paginated transaction history with filtering, search,
 * and detailed payment status information.
 */

import {
  Calendar,
  ChevronDown,
  CreditCard,
  DollarSign,
  Filter,
  History,
  RefreshCw,
  Search,
  TrendingDown,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  Clock,
  XCircle,
} from 'lucide-react-native';
import React, { useState } from 'react';

import { Badge } from '@/components/ui/badge';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Divider } from '@/components/ui/divider';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Input, InputField } from '@/components/ui/input';
import { Pressable } from '@/components/ui/pressable';
import {
  Select,
  SelectBackdrop,
  SelectContent,
  SelectDragIndicator,
  SelectDragIndicatorWrapper,
  SelectItem,
  SelectPortal,
  SelectTrigger,
} from '@/components/ui/select';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import type {
  PaginatedTransactionHistory,
  TransactionHistoryItem,
  TransactionFilterOptions,
} from '@/types/purchase';

interface TransactionHistoryProps {
  transactions: PaginatedTransactionHistory | null;
  loading: boolean;
  error: string | null;
  filters: TransactionFilterOptions;
  onFiltersChange: (filters: Partial<TransactionFilterOptions>) => void;
  onRefresh: () => Promise<void>;
  onLoadMore: () => Promise<void>;
  searchQuery: string;
  onSearchChange: (query: string) => void;
}

/**
 * Transaction status configuration
 */
const TRANSACTION_STATUS_CONFIG = {
  pending: {
    icon: Clock,
    color: 'warning',
    label: 'Pending',
  },
  succeeded: {
    icon: CheckCircle,
    color: 'success',
    label: 'Completed',
  },
  failed: {
    icon: XCircle,
    color: 'error',
    label: 'Failed',
  },
  refunded: {
    icon: TrendingDown,
    color: 'secondary',
    label: 'Refunded',
  },
};

/**
 * Transaction type configuration
 */
const TRANSACTION_TYPE_CONFIG = {
  purchase: {
    icon: TrendingUp,
    color: 'success',
    label: 'Purchase',
  },
  consumption: {
    icon: TrendingDown,
    color: 'primary',
    label: 'Usage',
  },
  refund: {
    icon: TrendingDown,
    color: 'warning',
    label: 'Refund',
  },
  adjustment: {
    icon: DollarSign,
    color: 'secondary',
    label: 'Adjustment',
  },
};

/**
 * Individual transaction item component
 */
function TransactionItem({ transaction }: { transaction: TransactionHistoryItem }) {
  const statusConfig =
    TRANSACTION_STATUS_CONFIG[transaction.payment_status] || TRANSACTION_STATUS_CONFIG.pending;
  const typeConfig =
    TRANSACTION_TYPE_CONFIG[transaction.transaction_type] || TRANSACTION_TYPE_CONFIG.purchase;

  const hoursChanged = parseFloat(transaction.hours_changed);
  const isPositiveChange = hoursChanged > 0;

  return (
    <Card className="p-4">
      <VStack space="sm">
        {/* Header */}
        <HStack className="items-center justify-between">
          <HStack space="sm" className="items-center flex-1">
            <Icon as={typeConfig.icon} size="sm" className={`text-${typeConfig.color}-600`} />
            <VStack space="0" className="flex-1">
              <Text className="font-semibold text-typography-900">
                {transaction.transaction_type_display}
              </Text>
              <Text className="text-xs text-typography-600">ID: {transaction.transaction_id}</Text>
            </VStack>
          </HStack>

          <Badge variant="solid" action={statusConfig.color} size="sm">
            <Icon as={statusConfig.icon} size="xs" />
            <Text className="text-xs ml-1">{statusConfig.label}</Text>
          </Badge>
        </HStack>

        {/* Details */}
        <VStack space="xs">
          <HStack className="items-center justify-between">
            <Text className="text-sm text-typography-700">Hours Changed:</Text>
            <Text
              className={`text-sm font-semibold ${
                isPositiveChange ? 'text-success-600' : 'text-error-600'
              }`}
            >
              {isPositiveChange ? '+' : ''}
              {hoursChanged.toFixed(1)}h
            </Text>
          </HStack>

          {transaction.amount !== '0.00' && (
            <HStack className="items-center justify-between">
              <Text className="text-sm text-typography-700">Amount:</Text>
              <Text className="text-sm font-semibold text-typography-900">
                €{parseFloat(transaction.amount).toFixed(2)}
              </Text>
            </HStack>
          )}

          {transaction.plan_name && (
            <HStack className="items-center justify-between">
              <Text className="text-sm text-typography-700">Plan:</Text>
              <Text className="text-sm text-typography-900">{transaction.plan_name}</Text>
            </HStack>
          )}
        </VStack>

        {/* Description */}
        <Text className="text-sm text-typography-600">{transaction.description}</Text>

        <Divider />

        {/* Footer */}
        <HStack className="items-center justify-between">
          <Text className="text-xs text-typography-500">
            {new Date(transaction.created_at).toLocaleDateString('en-US', {
              year: 'numeric',
              month: 'short',
              day: 'numeric',
              hour: '2-digit',
              minute: '2-digit',
            })}
          </Text>

          {transaction.processed_at && (
            <Text className="text-xs text-typography-500">
              Processed:{' '}
              {new Date(transaction.processed_at).toLocaleDateString('en-US', {
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
              })}
            </Text>
          )}
        </HStack>
      </VStack>
    </Card>
  );
}

/**
 * Filter controls component
 */
function TransactionFilters({
  filters,
  onFiltersChange,
}: {
  filters: TransactionFilterOptions;
  onFiltersChange: (filters: Partial<TransactionFilterOptions>) => void;
}) {
  const [showFilters, setShowFilters] = useState(false);

  return (
    <VStack space="md">
      <HStack className="items-center justify-between">
        <HStack className="items-center" space="sm">
          <Heading size="md" className="text-typography-900">
            Filters
          </Heading>
          {(filters.payment_status ||
            filters.transaction_type ||
            filters.date_from ||
            filters.date_to) && (
            <Badge variant="solid" action="primary" size="sm">
              <Text className="text-xs">Active</Text>
            </Badge>
          )}
        </HStack>
        <Pressable
          onPress={() => setShowFilters(!showFilters)}
          className="flex-row items-center"
          accessibilityLabel={showFilters ? 'Hide filters' : 'Show filters'}
        >
          <Icon as={Filter} size="sm" className="text-typography-600 mr-2" />
          <Icon
            as={ChevronDown}
            size="sm"
            className={`text-typography-600 transform transition-transform ${
              showFilters ? 'rotate-180' : 'rotate-0'
            }`}
          />
        </Pressable>
      </HStack>

      {showFilters && (
        <VStack space="md">
          {/* Payment Status Filter */}
          <VStack space="xs">
            <Text className="text-sm font-medium text-typography-800">Payment Status</Text>
            <Select
              selectedValue={filters.payment_status || ''}
              onValueChange={value =>
                onFiltersChange({
                  payment_status: value === 'all' ? undefined : value,
                })
              }
            >
              <SelectTrigger variant="outline" size="md">
                <Text className="text-sm">
                  {filters.payment_status
                    ? TRANSACTION_STATUS_CONFIG[
                        filters.payment_status as keyof typeof TRANSACTION_STATUS_CONFIG
                      ]?.label || filters.payment_status
                    : 'All Statuses'}
                </Text>
              </SelectTrigger>
              <SelectPortal>
                <SelectBackdrop />
                <SelectContent>
                  <SelectDragIndicatorWrapper>
                    <SelectDragIndicator />
                  </SelectDragIndicatorWrapper>
                  <SelectItem label="All Statuses" value="all" />
                  <SelectItem label="Pending" value="pending" />
                  <SelectItem label="Completed" value="succeeded" />
                  <SelectItem label="Failed" value="failed" />
                  <SelectItem label="Refunded" value="refunded" />
                </SelectContent>
              </SelectPortal>
            </Select>
          </VStack>

          {/* Transaction Type Filter */}
          <VStack space="xs">
            <Text className="text-sm font-medium text-typography-800">Transaction Type</Text>
            <Select
              selectedValue={filters.transaction_type || ''}
              onValueChange={value =>
                onFiltersChange({
                  transaction_type: value === 'all' ? undefined : value,
                })
              }
            >
              <SelectTrigger variant="outline" size="md">
                <Text className="text-sm">
                  {filters.transaction_type
                    ? TRANSACTION_TYPE_CONFIG[
                        filters.transaction_type as keyof typeof TRANSACTION_TYPE_CONFIG
                      ]?.label || filters.transaction_type
                    : 'All Types'}
                </Text>
              </SelectTrigger>
              <SelectPortal>
                <SelectBackdrop />
                <SelectContent>
                  <SelectDragIndicatorWrapper>
                    <SelectDragIndicator />
                  </SelectDragIndicatorWrapper>
                  <SelectItem label="All Types" value="all" />
                  <SelectItem label="Purchase" value="purchase" />
                  <SelectItem label="Usage" value="consumption" />
                  <SelectItem label="Refund" value="refund" />
                  <SelectItem label="Adjustment" value="adjustment" />
                </SelectContent>
              </SelectPortal>
            </Select>
          </VStack>

          {/* Date Range Filters */}
          <HStack space="md">
            <VStack space="xs" className="flex-1">
              <Text className="text-sm font-medium text-typography-800">From Date</Text>
              <Input>
                <InputField
                  placeholder="YYYY-MM-DD"
                  value={filters.date_from || ''}
                  onChangeText={value => onFiltersChange({ date_from: value || undefined })}
                  keyboardType="numeric"
                  maxLength={10}
                />
              </Input>
            </VStack>

            <VStack space="xs" className="flex-1">
              <Text className="text-sm font-medium text-typography-800">To Date</Text>
              <Input>
                <InputField
                  placeholder="YYYY-MM-DD"
                  value={filters.date_to || ''}
                  onChangeText={value => onFiltersChange({ date_to: value || undefined })}
                  keyboardType="numeric"
                  maxLength={10}
                />
              </Input>
            </VStack>
          </HStack>

          {/* Clear Filters */}
          <Button
            action="secondary"
            variant="outline"
            size="sm"
            onPress={() =>
              onFiltersChange({
                payment_status: undefined,
                transaction_type: undefined,
                date_from: undefined,
                date_to: undefined,
              })
            }
          >
            <ButtonText>Clear Filters</ButtonText>
          </Button>
        </VStack>
      )}
    </VStack>
  );
}

/**
 * Main Transaction History Component
 */
export function TransactionHistory({
  transactions,
  loading,
  error,
  filters,
  onFiltersChange,
  onRefresh,
  onLoadMore,
  searchQuery,
  onSearchChange,
}: TransactionHistoryProps) {
  if (loading && !transactions) {
    return (
      <VStack space="lg" className="items-center py-12">
        <Spinner size="large" />
        <Text className="text-typography-600">Loading transaction history...</Text>
      </VStack>
    );
  }

  if (error) {
    return (
      <Card className="p-6 border-error-200">
        <VStack space="md" className="items-center">
          <Icon as={AlertTriangle} size="xl" className="text-error-500" />
          <VStack space="sm" className="items-center">
            <Heading size="sm" className="text-error-900">
              Unable to Load Transactions
            </Heading>
            <Text className="text-error-700 text-sm text-center">{error}</Text>
          </VStack>
          <Button action="secondary" variant="outline" size="sm" onPress={onRefresh}>
            <ButtonIcon as={RefreshCw} />
            <ButtonText>Try Again</ButtonText>
          </Button>
        </VStack>
      </Card>
    );
  }

  return (
    <VStack space="lg">
      {/* Header */}
      <HStack className="items-center justify-between">
        <VStack space="xs">
          <Heading size="lg" className="text-typography-900">
            Transaction History
          </Heading>
          {transactions && (
            <Text className="text-sm text-typography-600">
              {transactions.count} total transactions
            </Text>
          )}
        </VStack>

        <Button
          action="secondary"
          variant="outline"
          size="sm"
          onPress={onRefresh}
          disabled={loading}
        >
          <ButtonIcon as={RefreshCw} />
          <ButtonText>Refresh</ButtonText>
        </Button>
      </HStack>

      {/* Filters */}
      <Card className="p-4">
        <TransactionFilters filters={filters} onFiltersChange={onFiltersChange} />
      </Card>

      {/* Transaction List */}
      {transactions && transactions.results.length > 0 ? (
        <VStack space="md">
          {transactions.results.map(transaction => (
            <TransactionItem
              key={`${transaction.id}-${transaction.transaction_id}`}
              transaction={transaction}
            />
          ))}

          {/* Load More Button */}
          {transactions.next && (
            <Card className="p-4">
              <Button
                action="secondary"
                variant="outline"
                size="md"
                onPress={onLoadMore}
                disabled={loading}
                className="w-full"
              >
                {loading ? (
                  <>
                    <Spinner size="sm" />
                    <ButtonText className="ml-2">Loading...</ButtonText>
                  </>
                ) : (
                  <ButtonText>Load More Transactions</ButtonText>
                )}
              </Button>
            </Card>
          )}
        </VStack>
      ) : (
        <Card className="p-8">
          <VStack space="md" className="items-center">
            <Icon as={History} size="xl" className="text-typography-300" />
            <VStack space="xs" className="items-center">
              <Text className="font-medium text-typography-600">No Transactions Found</Text>
              <Text className="text-sm text-typography-500 text-center">
                {searchQuery || Object.keys(filters).length > 0
                  ? 'Try adjusting your search or filters'
                  : 'Your transaction history will appear here once you make purchases'}
              </Text>
            </VStack>
          </VStack>
        </Card>
      )}
    </VStack>
  );
}
