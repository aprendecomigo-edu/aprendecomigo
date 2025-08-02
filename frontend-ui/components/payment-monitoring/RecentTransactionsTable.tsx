/**
 * Recent Transactions Table Component - GitHub Issue #117
 * 
 * Displays recent transaction activity with status indicators,
 * quick actions, and real-time updates.
 */

import React from 'react';
import { ScrollView } from 'react-native';
import { VStack } from '@/components/ui/vstack';
import { HStack } from '@/components/ui/hstack';
import { Text } from '@/components/ui/text';
import { Box } from '@/components/ui/box';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Icon } from '@/components/ui/icon';
import { Pressable } from '@/components/ui/pressable';
import { Skeleton } from '@/components/ui/skeleton';
import { Table, TableBody, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { 
  Eye, 
  MoreHorizontal, 
  CreditCard, 
  AlertTriangle, 
  CheckCircle, 
  Clock,
  ExternalLink
} from 'lucide-react-native';
import type { TransactionMonitoring } from '@/types/paymentMonitoring';

interface RecentTransactionsTableProps {
  transactions: TransactionMonitoring[];
  loading?: boolean;
  onViewTransaction?: (transaction: TransactionMonitoring) => void;
  onRefundTransaction?: (transaction: TransactionMonitoring) => void;
  maxRows?: number;
}

interface TransactionRowProps {
  transaction: TransactionMonitoring;
  onView?: (transaction: TransactionMonitoring) => void;
  onRefund?: (transaction: TransactionMonitoring) => void;
}

function TransactionRow({ transaction, onView, onRefund }: TransactionRowProps) {
  const getStatusInfo = () => {
    switch (transaction.status) {
      case 'succeeded':
        return {
          icon: CheckCircle,
          color: 'text-success-600',
          bgColor: 'bg-success-50',
          variant: 'success' as const,
          label: 'Success'
        };
      case 'processing':
        return {
          icon: Clock,
          color: 'text-warning-600',
          bgColor: 'bg-warning-50',
          variant: 'warning' as const,
          label: 'Processing'
        };
      case 'requires_action':
      case 'requires_confirmation':
      case 'requires_payment_method':
        return {
          icon: AlertTriangle,
          color: 'text-warning-600',
          bgColor: 'bg-warning-50',
          variant: 'warning' as const,
          label: 'Action Required'
        };
      case 'canceled':
        return {
          icon: AlertTriangle,
          color: 'text-error-600',
          bgColor: 'bg-error-50',
          variant: 'error' as const,
          label: 'Canceled'
        };
      default:
        return {
          icon: Clock,
          color: 'text-typography-500',
          bgColor: 'bg-background-50',
          variant: 'info' as const,
          label: transaction.status_display || transaction.status
        };
    }
  };

  const statusInfo = getStatusInfo();
  const IconComponent = statusInfo.icon;

  const formatAmount = (amount: string, currency: string) => {
    const num = parseFloat(amount);
    return `${currency === 'eur' ? '€' : currency.toUpperCase()}${num.toLocaleString(undefined, { 
      minimumFractionDigits: 2, 
      maximumFractionDigits: 2 
    })}`;
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString([], {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getRiskBadge = () => {
    if (!transaction.risk_score) return null;
    
    if (transaction.risk_score >= 80) {
      return <Badge variant="error" size="sm"><Text size="xs">High Risk</Text></Badge>;
    } else if (transaction.risk_score >= 50) {
      return <Badge variant="warning" size="sm"><Text size="xs">Medium Risk</Text></Badge>;
    } else if (transaction.risk_score >= 30) {
      return <Badge variant="info" size="sm"><Text size="xs">Low Risk</Text></Badge>;
    }
    return null;
  };

  return (
    <TableRow className="hover:bg-background-50">
      {/* Transaction ID & Customer */}
      <Box className="p-4">
        <VStack space="xs">
          <Text size="sm" className="font-medium text-typography-900">
            {transaction.payment_intent_id.slice(-8)}
          </Text>
          <Text size="xs" className="text-typography-500">
            {transaction.customer_email}
          </Text>
        </VStack>
      </Box>

      {/* Amount */}
      <Box className="p-4">
        <Text size="sm" className="font-medium text-typography-900">
          {formatAmount(transaction.amount, transaction.currency)}
        </Text>
      </Box>

      {/* Status */}
      <Box className="p-4">
        <VStack space="xs">
          <Badge variant={statusInfo.variant} size="sm" className="self-start">
            <HStack space="xs" className="items-center">
              <Icon as={IconComponent} size="xs" />
              <Text size="xs">{statusInfo.label}</Text>
            </HStack>
          </Badge>
          {getRiskBadge()}
        </VStack>
      </Box>

      {/* Payment Method */}
      <Box className="p-4">
        <HStack space="xs" className="items-center">
          <Icon as={CreditCard} size="xs" className="text-typography-500" />
          <Text size="sm" className="text-typography-600">
            {transaction.payment_method_type || 'Card'}
          </Text>
        </HStack>
      </Box>

      {/* Date */}
      <Box className="p-4">
        <Text size="sm" className="text-typography-600">
          {formatDate(transaction.created_at)}
        </Text>
      </Box>

      {/* Actions */}
      <Box className="p-4">
        <HStack space="xs">
          <Button
            variant="outline"
            size="sm"
            onPress={() => onView?.(transaction)}
          >
            <Icon as={Eye} size="xs" />
          </Button>
          
          {transaction.status === 'succeeded' && onRefund && (
            <Button
              variant="outline"
              size="sm"
              onPress={() => onRefund(transaction)}
            >
              <Text size="xs">Refund</Text>
            </Button>
          )}
        </HStack>
      </Box>
    </TableRow>
  );
}

function LoadingRow() {
  return (
    <TableRow>
      {[...Array(6)].map((_, i) => (
        <Box key={i} className="p-4">
          <Skeleton className="h-4 w-full" />
        </Box>
      ))}
    </TableRow>
  );
}

export default function RecentTransactionsTable({ 
  transactions, 
  loading, 
  onViewTransaction,
  onRefundTransaction,
  maxRows = 10 
}: RecentTransactionsTableProps) {
  const displayTransactions = transactions.slice(0, maxRows);

  return (
    <Card className="p-6">
      <VStack space="lg">
        {/* Header */}
        <HStack className="justify-between items-center">
          <VStack space="xs">
            <Text size="lg" className="font-semibold text-typography-900">
              Recent Transactions
            </Text>
            <Text size="sm" className="text-typography-500">
              Latest payment activity
            </Text>
          </VStack>

          <Button variant="outline" size="sm">
            <Icon as={ExternalLink} size="xs" />
            <Text size="sm" className="ml-1">View All</Text>
          </Button>
        </HStack>

        {/* Table */}
        <Box className="border border-border-200 rounded-lg overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow className="bg-background-50">
                <TableHead className="p-4">
                  <Text size="sm" className="font-semibold text-typography-700">
                    Transaction
                  </Text>
                </TableHead>
                <TableHead className="p-4">
                  <Text size="sm" className="font-semibold text-typography-700">
                    Amount
                  </Text>
                </TableHead>
                <TableHead className="p-4">
                  <Text size="sm" className="font-semibold text-typography-700">
                    Status
                  </Text>
                </TableHead>
                <TableHead className="p-4">
                  <Text size="sm" className="font-semibold text-typography-700">
                    Method
                  </Text>
                </TableHead>
                <TableHead className="p-4">
                  <Text size="sm" className="font-semibold text-typography-700">
                    Date
                  </Text>
                </TableHead>
                <TableHead className="p-4">
                  <Text size="sm" className="font-semibold text-typography-700">
                    Actions
                  </Text>
                </TableHead>
              </TableRow>
            </TableHeader>
            
            <TableBody>
              {loading ? (
                [...Array(5)].map((_, i) => <LoadingRow key={i} />)
              ) : displayTransactions.length === 0 ? (
                <TableRow>
                  <Box className="p-8 text-center" colSpan={6}>
                    <Icon as={CreditCard} size="lg" className="text-typography-400 mx-auto mb-3" />
                    <Text className="text-typography-500">No recent transactions</Text>
                  </Box>
                </TableRow>
              ) : (
                displayTransactions.map((transaction) => (
                  <TransactionRow
                    key={transaction.id}
                    transaction={transaction}
                    onView={onViewTransaction}
                    onRefund={onRefundTransaction}
                  />
                ))
              )}
            </TableBody>
          </Table>
        </Box>

        {/* Footer */}
        {!loading && transactions.length > maxRows && (
          <HStack className="justify-center pt-4 border-t border-border-100">
            <Text size="sm" className="text-typography-500">
              Showing {maxRows} of {transactions.length} transactions
            </Text>
          </HStack>
        )}
      </VStack>
    </Card>
  );
}