/**
 * Purchase History Component
 * 
 * Displays detailed purchase history with consumption tracking,
 * package details, and expiration information.
 */

import React, { useState } from 'react';
import { 
  Calendar,
  ChevronDown,
  ChevronRight,
  Clock,
  Filter,
  Package,
  RefreshCw,
  User,
  BookOpen,
  AlertTriangle,
  CheckCircle,
  XCircle,
  TrendingUp,
  TrendingDown
} from 'lucide-react-native';

import { Badge } from '@/components/ui/badge';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Divider } from '@/components/ui/divider';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Input, InputField } from '@/components/ui/input';
import { Pressable } from '@/components/ui/pressable';
import { Select, SelectBackdrop, SelectContent, SelectDragIndicator, SelectDragIndicatorWrapper, SelectItem, SelectPortal, SelectTrigger } from '@/components/ui/select';
import { Spinner } from '@/components/ui/spinner';
import { Switch } from '@/components/ui/switch';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import type { 
  PaginatedPurchaseHistory, 
  PurchaseHistoryItem, 
  PurchaseFilterOptions,
  ConsumptionRecord
} from '@/types/purchase';
import { ReceiptDownloadButton } from '@/components/student/receipts/ReceiptDownloadButton';
import { ReceiptPreviewModal } from '@/components/student/receipts/ReceiptPreviewModal';
import { useReceipts } from '@/hooks/useReceipts';

interface PurchaseHistoryProps {
  purchases: PaginatedPurchaseHistory | null;
  loading: boolean;
  error: string | null;
  filters: PurchaseFilterOptions;
  onFiltersChange: (filters: Partial<PurchaseFilterOptions>) => void;
  onRefresh: () => Promise<void>;
  onLoadMore: () => Promise<void>;
  searchQuery: string;
  onSearchChange: (query: string) => void;
}

/**
 * Purchase status configuration
 */
const PAYMENT_STATUS_CONFIG = {
  pending: {
    icon: Clock,
    color: 'warning',
    label: 'Pending'
  },
  succeeded: {
    icon: CheckCircle,
    color: 'success',
    label: 'Completed'
  },
  failed: {
    icon: XCircle,
    color: 'error',
    label: 'Failed'
  },
  refunded: {
    icon: TrendingDown,
    color: 'secondary',
    label: 'Refunded'
  }
};

/**
 * Consumption record item component
 */
function ConsumptionItem({ 
  consumption 
}: { 
  consumption: ConsumptionRecord 
}) {
  return (
    <HStack className="items-center justify-between p-3 bg-background-50 rounded-md">
      <HStack space="sm" className="items-center flex-1">
        <Icon 
          as={consumption.session_type === 'group' ? User : BookOpen} 
          size="sm" 
          className="text-primary-600" 
        />
        <VStack space="0" className="flex-1">
          <Text className="text-sm font-medium text-typography-800">
            {consumption.session_type === 'group' ? 'Group Session' : 'Individual Session'}
          </Text>
          <Text className="text-xs text-typography-600">
            {consumption.description}
          </Text>
          {consumption.teacher_name && (
            <Text className="text-xs text-typography-500">
              with {consumption.teacher_name}
            </Text>
          )}
        </VStack>
      </HStack>
      
      <VStack space="0" className="items-end">
        <Text className="text-sm font-semibold text-error-600">
          -{parseFloat(consumption.hours_consumed).toFixed(1)}h
        </Text>
        <Text className="text-xs text-typography-500">
          {new Date(consumption.session_date).toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric'
          })}
        </Text>
      </VStack>
    </HStack>
  );
}

/**
 * Individual purchase item component
 */
function PurchaseItem({ 
  purchase 
}: { 
  purchase: PurchaseHistoryItem 
}) {
  const { receipts } = useReceipts();
  const [showConsumption, setShowConsumption] = useState(false);
  const [previewReceiptId, setPreviewReceiptId] = useState<string | null>(null);
  
  // Find existing receipt for this purchase
  const existingReceipt = receipts.find(r => r.transaction_id === purchase.transaction_id);
  
  const statusConfig = PAYMENT_STATUS_CONFIG[purchase.payment_status] || PAYMENT_STATUS_CONFIG.pending;
  const hoursRemaining = parseFloat(purchase.hours_remaining);
  const hoursIncluded = parseFloat(purchase.hours_included);
  const usagePercentage = ((hoursIncluded - hoursRemaining) / hoursIncluded) * 100;
  
  const getStatusColor = () => {
    if (purchase.is_expired) return 'error';
    if (!purchase.is_active) return 'secondary';
    if (purchase.days_until_expiry && purchase.days_until_expiry <= 7) return 'warning';
    return 'success';
  };

  const getStatusLabel = () => {
    if (purchase.is_expired) return 'Expired';
    if (!purchase.is_active) return 'Inactive';
    if (purchase.days_until_expiry && purchase.days_until_expiry <= 7) {
      return `${purchase.days_until_expiry} days left`;
    }
    return 'Active';
  };

  return (
    <>
    <Card className="p-4">
      <VStack space="sm">
        {/* Header */}
        <HStack className="items-center justify-between">
          <HStack space="sm" className="items-center flex-1">
            <Icon as={Package} size="sm" className="text-primary-600" />
            <VStack space="0" className="flex-1">
              <Text className="font-semibold text-typography-900">
                {purchase.plan_name}
              </Text>
              <Text className="text-xs text-typography-600">
                {purchase.plan_type === 'package' ? 'Package' : 'Subscription'} • ID: {purchase.transaction_id}
              </Text>
            </VStack>
          </HStack>
          
          <VStack space="xs" className="items-end">
            <Badge 
              variant="solid" 
              action={statusConfig.color} 
              size="sm"
            >
              <Icon as={statusConfig.icon} size="xs" />
              <Text className="text-xs ml-1">
                {statusConfig.label}
              </Text>
            </Badge>
            
            <Badge 
              variant="outline" 
              action={getStatusColor()} 
              size="sm"
            >
              <Text className="text-xs">
                {getStatusLabel()}
              </Text>
            </Badge>
          </VStack>
        </HStack>

        {/* Progress Bar */}
        <VStack space="xs">
          <HStack className="items-center justify-between">
            <Text className="text-sm text-typography-700">
              Usage Progress
            </Text>
            <Text className="text-sm text-typography-600">
              {usagePercentage.toFixed(0)}%
            </Text>
          </HStack>
          
          <div className="w-full bg-background-200 rounded-full h-2">
            <div 
              className={`h-2 rounded-full ${
                usagePercentage >= 90 ? 'bg-error-500' : 
                usagePercentage >= 70 ? 'bg-warning-500' : 
                'bg-success-500'
              }`}
              style={{ width: `${Math.min(usagePercentage, 100)}%` }}
            />
          </div>
        </VStack>

        {/* Details Grid */}
        <VStack space="xs">
          <HStack className="items-center justify-between">
            <Text className="text-sm text-typography-700">
              Hours Included:
            </Text>
            <Text className="text-sm font-semibold text-typography-900">
              {hoursIncluded.toFixed(1)}h
            </Text>
          </HStack>
          
          <HStack className="items-center justify-between">
            <Text className="text-sm text-typography-700">
              Hours Used:
            </Text>
            <Text className="text-sm font-semibold text-error-600">
              {parseFloat(purchase.hours_consumed).toFixed(1)}h
            </Text>
          </HStack>
          
          <HStack className="items-center justify-between">
            <Text className="text-sm text-typography-700">
              Hours Remaining:
            </Text>
            <Text className={`text-sm font-semibold ${
              hoursRemaining > 0 ? 'text-success-600' : 'text-error-600'
            }`}>
              {hoursRemaining.toFixed(1)}h
            </Text>
          </HStack>
          
          <HStack className="items-center justify-between">
            <Text className="text-sm text-typography-700">
              Amount Paid:
            </Text>
            <Text className="text-sm font-semibold text-typography-900">
              €{parseFloat(purchase.amount_paid).toFixed(2)}
            </Text>
          </HStack>
          
          {purchase.expires_at && (
            <HStack className="items-center justify-between">
              <Text className="text-sm text-typography-700">
                Expires:
              </Text>
              <Text className={`text-sm font-semibold ${
                purchase.is_expired ? 'text-error-600' : 
                purchase.days_until_expiry && purchase.days_until_expiry <= 7 ? 'text-warning-600' :
                'text-typography-600'
              }`}>
                {new Date(purchase.expires_at).toLocaleDateString('en-US', {
                  year: 'numeric',
                  month: 'short',
                  day: 'numeric'
                })}
              </Text>
            </HStack>
          )}
        </VStack>

        <Divider />

        {/* Consumption History Toggle */}
        {purchase.consumption_history && purchase.consumption_history.length > 0 && (
          <Pressable
            onPress={() => setShowConsumption(!showConsumption)}
            className="flex-row items-center justify-between"
          >
            <HStack space="sm" className="items-center">
              <Icon as={Clock} size="sm" className="text-typography-600" />
              <Text className="text-sm font-medium text-typography-800">
                Usage History ({purchase.consumption_history.length} sessions)
              </Text>
            </HStack>
            <Icon 
              as={showConsumption ? ChevronDown : ChevronRight} 
              size="sm" 
              className="text-typography-600"
            />
          </Pressable>
        )}

        {/* Consumption History */}
        {showConsumption && purchase.consumption_history && (
          <VStack space="xs">
            {purchase.consumption_history.map((consumption) => (
              <ConsumptionItem
                key={consumption.id}
                consumption={consumption}
              />
            ))}
          </VStack>
        )}

        {/* Footer with Receipt */}
        <VStack space="sm">
          <HStack className="items-center justify-between">
            <Text className="text-xs text-typography-500">
              Purchased: {new Date(purchase.purchase_date).toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric'
              })}
            </Text>
            
            {purchase.consumption_history && purchase.consumption_history.length === 0 && (
              <Text className="text-xs text-typography-500">
                No usage yet
              </Text>
            )}
          </HStack>

          {/* Receipt Download Section */}
          {purchase.payment_status === 'succeeded' && (
            <ReceiptDownloadButton
              transactionId={purchase.transaction_id}
              existingReceipt={existingReceipt}
              planName={purchase.plan_name}
              amount={purchase.amount_paid}
              size="sm"
              variant="outline"
              onPreview={(receiptId) => setPreviewReceiptId(receiptId)}
              className="self-start"
            />
          )}
        </VStack>
      </VStack>
    </Card>
    
    {/* Receipt Preview Modal */}
    {previewReceiptId && existingReceipt && (
      <ReceiptPreviewModal
        isOpen={!!previewReceiptId}
        receiptId={previewReceiptId}
        receiptNumber={existingReceipt.receipt_number}
        onClose={() => setPreviewReceiptId(null)}
      />
    )}
  </>
  );
}

/**
 * Filter controls component
 */
function PurchaseFilters({
  filters,
  onFiltersChange
}: {
  filters: PurchaseFilterOptions;
  onFiltersChange: (filters: Partial<PurchaseFilterOptions>) => void;
}) {
  const [showFilters, setShowFilters] = useState(false);

  return (
    <VStack space="md">
      <HStack className="items-center justify-between">
        <Heading size="md" className="text-typography-900">
          Filters
        </Heading>
        <Pressable
          onPress={() => setShowFilters(!showFilters)}
          className="flex-row items-center"
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
          {/* Active Only Toggle */}
          <HStack className="items-center justify-between">
            <Text className="text-sm font-medium text-typography-800">
              Show Active Only
            </Text>
            <Switch
              size="sm"
              isChecked={filters.active_only || false}
              onToggle={(checked) => onFiltersChange({ active_only: checked })}
            />
          </HStack>

          {/* Include Consumption Toggle */}
          <HStack className="items-center justify-between">
            <Text className="text-sm font-medium text-typography-800">
              Include Usage History
            </Text>
            <Switch
              size="sm"
              isChecked={filters.include_consumption || false}
              onToggle={(checked) => onFiltersChange({ include_consumption: checked })}
            />
          </HStack>

          {/* Date Range Filters */}
          <HStack space="md">
            <VStack space="xs" className="flex-1">
              <Text className="text-sm font-medium text-typography-800">
                From Date
              </Text>
              <Input>
                <InputField
                  placeholder="YYYY-MM-DD"
                  value={filters.date_from || ''}
                  onChangeText={(value) => onFiltersChange({ date_from: value || undefined })}
                />
              </Input>
            </VStack>
            
            <VStack space="xs" className="flex-1">
              <Text className="text-sm font-medium text-typography-800">
                To Date
              </Text>
              <Input>
                <InputField
                  placeholder="YYYY-MM-DD"
                  value={filters.date_to || ''}
                  onChangeText={(value) => onFiltersChange({ date_to: value || undefined })}
                />
              </Input>
            </VStack>
          </HStack>

          {/* Clear Filters */}
          <Button
            action="secondary"
            variant="outline"
            size="sm"
            onPress={() => onFiltersChange({
              active_only: undefined,
              include_consumption: true,
              date_from: undefined,
              date_to: undefined,
            })}
          >
            <ButtonText>Clear Filters</ButtonText>
          </Button>
        </VStack>
      )}
    </VStack>
  );
}

/**
 * Main Purchase History Component
 */
export function PurchaseHistory({
  purchases,
  loading,
  error,
  filters,
  onFiltersChange,
  onRefresh,
  onLoadMore,
  searchQuery,
  onSearchChange,
}: PurchaseHistoryProps) {
  if (loading && !purchases) {
    return (
      <VStack space="lg" className="items-center py-12">
        <Spinner size="large" />
        <Text className="text-typography-600">Loading purchase history...</Text>
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
              Unable to Load Purchases
            </Heading>
            <Text className="text-error-700 text-sm text-center">
              {error}
            </Text>
          </VStack>
          <Button
            action="secondary"
            variant="outline"
            size="sm"
            onPress={onRefresh}
          >
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
            Purchase History
          </Heading>
          {purchases && (
            <Text className="text-sm text-typography-600">
              {purchases.count} total purchases
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
        <PurchaseFilters
          filters={filters}
          onFiltersChange={onFiltersChange}
        />
      </Card>

      {/* Purchase List */}
      {purchases && purchases.results.length > 0 ? (
        <VStack space="md">
          {purchases.results.map((purchase) => (
            <PurchaseItem
              key={`${purchase.id}-${purchase.transaction_id}`}
              purchase={purchase}
            />
          ))}

          {/* Load More Button */}
          {purchases.next && (
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
                  <ButtonText>Load More Purchases</ButtonText>
                )}
              </Button>
            </Card>
          )}
        </VStack>
      ) : (
        <Card className="p-8">
          <VStack space="md" className="items-center">
            <Icon as={Package} size="xl" className="text-typography-300" />
            <VStack space="xs" className="items-center">
              <Text className="font-medium text-typography-600">
                No Purchases Found
              </Text>
              <Text className="text-sm text-typography-500 text-center">
                {searchQuery || Object.keys(filters).length > 0 
                  ? "Try adjusting your search or filters"
                  : "Your purchase history will appear here once you buy tutoring packages"
                }
              </Text>
            </VStack>
          </VStack>
        </Card>
      )}
    </VStack>
  );
}