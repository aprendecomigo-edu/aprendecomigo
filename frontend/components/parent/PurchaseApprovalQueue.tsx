/**
 * PurchaseApprovalQueue Component
 *
 * List component for managing pending purchase approval requests with:
 * - Quick approve/reject actions
 * - Batch operations
 * - Real-time updates
 * - Mobile-optimized touch interactions
 */

import {
  CheckCircle2,
  XCircle,
  Clock,
  Filter,
  ChevronDown,
  ChevronRight,
  AlertTriangle,
  MessageSquare,
  CreditCard,
  Users,
  Eye,
  MoreHorizontal,
} from 'lucide-react-native';
import React, { useState, useCallback, useMemo } from 'react';

import { PurchaseApprovalCard } from './PurchaseApprovalCard';

import { PurchaseApprovalRequest } from '@/api/parentApi';
import { Badge } from '@/components/ui/badge';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { Divider } from '@/components/ui/divider';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Pressable } from '@/components/ui/pressable';
import { ScrollView } from '@/components/ui/scroll-view';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

interface PurchaseApprovalQueueProps {
  approvals: PurchaseApprovalRequest[];
  onApprove: (requestId: string, notes?: string) => Promise<void>;
  onReject: (requestId: string, notes?: string) => Promise<void>;
  onBatchApprove: (requestIds: string[], notes?: string) => Promise<void>;
  onBatchReject: (requestIds: string[], notes?: string) => Promise<void>;
  onViewDetails: (approval: PurchaseApprovalRequest) => void;
  isLoading?: boolean;
  showFilters?: boolean;
}

type FilterOption = 'all' | 'urgent' | 'soon' | 'normal';
type ViewMode = 'list' | 'compact' | 'cards';

export const PurchaseApprovalQueue: React.FC<PurchaseApprovalQueueProps> = ({
  approvals,
  onApprove,
  onReject,
  onBatchApprove,
  onBatchReject,
  onViewDetails,
  isLoading = false,
  showFilters = true,
}) => {
  const [selectedRequests, setSelectedRequests] = useState<Set<string>>(new Set());
  const [currentFilter, setCurrentFilter] = useState<FilterOption>('all');
  const [viewMode, setViewMode] = useState<ViewMode>('list');
  const [isProcessing, setIsProcessing] = useState(false);

  // Get urgency level for sorting and filtering
  const getUrgencyLevel = useCallback((expiryString: string) => {
    const expiry = new Date(expiryString);
    const now = new Date();
    const diffInHours = Math.floor((expiry.getTime() - now.getTime()) / (1000 * 60 * 60));

    if (diffInHours <= 0) return 'expired';
    if (diffInHours <= 24) return 'urgent';
    if (diffInHours <= 72) return 'soon';
    return 'normal';
  }, []);

  // Filter and sort approvals
  const filteredApprovals = useMemo(() => {
    const filtered = approvals.filter(approval => {
      if (currentFilter === 'all') return true;
      const urgency = getUrgencyLevel(approval.expires_at);
      return urgency === currentFilter;
    });

    // Sort by urgency and time
    return filtered.sort((a, b) => {
      const urgencyA = getUrgencyLevel(a.expires_at);
      const urgencyB = getUrgencyLevel(b.expires_at);

      const urgencyOrder = { expired: 0, urgent: 1, soon: 2, normal: 3 };
      const orderA = urgencyOrder[urgencyA as keyof typeof urgencyOrder];
      const orderB = urgencyOrder[urgencyB as keyof typeof urgencyOrder];

      if (orderA !== orderB) return orderA - orderB;

      // Sort by request time (newest first)
      return new Date(b.requested_at).getTime() - new Date(a.requested_at).getTime();
    });
  }, [approvals, currentFilter, getUrgencyLevel]);

  // Get filter counts
  const filterCounts = useMemo(() => {
    const counts = { all: approvals.length, urgent: 0, soon: 0, normal: 0 };
    approvals.forEach(approval => {
      const urgency = getUrgencyLevel(approval.expires_at);
      if (urgency === 'urgent') counts.urgent++;
      else if (urgency === 'soon') counts.soon++;
      else if (urgency === 'normal') counts.normal++;
    });
    return counts;
  }, [approvals, getUrgencyLevel]);

  // Handle selection
  const handleSelectRequest = (requestId: string) => {
    const newSelected = new Set(selectedRequests);
    if (newSelected.has(requestId)) {
      newSelected.delete(requestId);
    } else {
      newSelected.add(requestId);
    }
    setSelectedRequests(newSelected);
  };

  const handleSelectAll = () => {
    if (selectedRequests.size === filteredApprovals.length) {
      setSelectedRequests(new Set());
    } else {
      setSelectedRequests(new Set(filteredApprovals.map(a => a.id.toString())));
    }
  };

  // Handle batch operations
  const handleBatchApprove = async () => {
    if (selectedRequests.size === 0) return;

    try {
      setIsProcessing(true);
      await onBatchApprove(Array.from(selectedRequests));
      setSelectedRequests(new Set());
    } catch (error) {
      console.error('Error batch approving:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleBatchReject = async () => {
    if (selectedRequests.size === 0) return;

    try {
      setIsProcessing(true);
      await onBatchReject(Array.from(selectedRequests));
      setSelectedRequests(new Set());
    } catch (error) {
      console.error('Error batch rejecting:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  // Handle individual actions
  const handleIndividualApprove = async (requestId: string, notes?: string) => {
    await onApprove(requestId, notes);
    // Remove from selection if it was selected
    const newSelected = new Set(selectedRequests);
    newSelected.delete(requestId);
    setSelectedRequests(newSelected);
  };

  const handleIndividualReject = async (requestId: string, notes?: string) => {
    await onReject(requestId, notes);
    // Remove from selection if it was selected
    const newSelected = new Set(selectedRequests);
    newSelected.delete(requestId);
    setSelectedRequests(newSelected);
  };

  // Format time until expiry
  const formatTimeUntilExpiry = (expiryString: string) => {
    const expiry = new Date(expiryString);
    const now = new Date();
    const diffInHours = Math.floor((expiry.getTime() - now.getTime()) / (1000 * 60 * 60));

    if (diffInHours <= 0) return 'Expired';
    if (diffInHours < 24) return `${diffInHours}h`;
    return `${Math.floor(diffInHours / 24)}d`;
  };

  if (isLoading) {
    return (
      <Card className="bg-white">
        <CardContent className="p-6">
          <VStack className="items-center space-y-4">
            <Icon as={Clock} size={32} className="text-gray-400" />
            <Text className="text-gray-600">Loading approval requests...</Text>
          </VStack>
        </CardContent>
      </Card>
    );
  }

  if (approvals.length === 0) {
    return (
      <Card className="bg-white">
        <CardContent className="p-6">
          <VStack className="items-center space-y-4">
            <Icon as={CheckCircle2} size={48} className="text-green-500" />
            <Heading size="sm" className="text-gray-900">
              All caught up!
            </Heading>
            <Text className="text-gray-600 text-center">
              No pending approval requests at the moment.
            </Text>
          </VStack>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-white">
      <CardHeader className="pb-3">
        <HStack className="justify-between items-center">
          <HStack className="space-x-2">
            <Icon as={CreditCard} size={20} className="text-blue-600" />
            <Heading size="md" className="text-gray-900">
              Purchase Approvals
            </Heading>
            <Badge variant="solid" action="info" size="sm">
              <Text className="text-xs font-medium">{filteredApprovals.length}</Text>
            </Badge>
          </HStack>

          {/* View Mode Toggle */}
          <HStack className="space-x-1">
            <Button
              variant={viewMode === 'compact' ? 'solid' : 'outline'}
              size="sm"
              onPress={() => setViewMode('compact')}
            >
              <ButtonText className="text-xs">Compact</ButtonText>
            </Button>
            <Button
              variant={viewMode === 'cards' ? 'solid' : 'outline'}
              size="sm"
              onPress={() => setViewMode('cards')}
            >
              <ButtonText className="text-xs">Cards</ButtonText>
            </Button>
          </HStack>
        </HStack>

        {/* Filters */}
        {showFilters && (
          <HStack className="mt-3 space-x-2">
            <ScrollView horizontal showsHorizontalScrollIndicator={false}>
              <HStack className="space-x-2">
                {[
                  { key: 'all' as FilterOption, label: 'All', count: filterCounts.all },
                  { key: 'urgent' as FilterOption, label: 'Urgent', count: filterCounts.urgent },
                  { key: 'soon' as FilterOption, label: 'Soon', count: filterCounts.soon },
                  { key: 'normal' as FilterOption, label: 'Normal', count: filterCounts.normal },
                ].map(filter => (
                  <Button
                    key={filter.key}
                    variant={currentFilter === filter.key ? 'solid' : 'outline'}
                    size="sm"
                    onPress={() => setCurrentFilter(filter.key)}
                    disabled={filter.count === 0}
                  >
                    <ButtonText className="text-xs">
                      {filter.label} ({filter.count})
                    </ButtonText>
                  </Button>
                ))}
              </HStack>
            </ScrollView>
          </HStack>
        )}

        {/* Batch Actions */}
        {selectedRequests.size > 0 && (
          <HStack className="mt-3 p-3 bg-blue-50 rounded-lg justify-between items-center">
            <HStack className="space-x-2">
              <Icon as={Users} size={16} className="text-blue-600" />
              <Text className="text-sm font-medium text-blue-900">
                {selectedRequests.size} selected
              </Text>
            </HStack>

            <HStack className="space-x-2">
              <Button
                action="secondary"
                variant="outline"
                size="sm"
                onPress={handleBatchReject}
                disabled={isProcessing}
              >
                <ButtonIcon as={XCircle} size={14} />
                <ButtonText className="ml-1 text-xs">Reject All</ButtonText>
              </Button>

              <Button
                action="primary"
                size="sm"
                onPress={handleBatchApprove}
                disabled={isProcessing}
              >
                <ButtonIcon as={CheckCircle2} size={14} />
                <ButtonText className="ml-1 text-xs">
                  {isProcessing ? 'Processing...' : 'Approve All'}
                </ButtonText>
              </Button>
            </HStack>
          </HStack>
        )}
      </CardHeader>

      <CardContent>
        <VStack className="space-y-3">
          {/* Select All Header */}
          {filteredApprovals.length > 1 && (
            <HStack className="justify-between items-center p-2 bg-gray-50 rounded-lg">
              <HStack className="items-center space-x-2">
                <Checkbox
                  value={selectedRequests.size === filteredApprovals.length}
                  onValueChange={handleSelectAll}
                />
                <Text className="text-sm text-gray-700">
                  Select all {filteredApprovals.length} requests
                </Text>
              </HStack>
            </HStack>
          )}

          {/* Approval List */}
          {viewMode === 'cards'
            ? // Card View
              filteredApprovals.map(approval => (
                <VStack key={approval.id} className="space-y-2">
                  {filteredApprovals.length > 1 && (
                    <HStack className="items-center space-x-2">
                      <Checkbox
                        value={selectedRequests.has(approval.id.toString())}
                        onValueChange={() => handleSelectRequest(approval.id.toString())}
                      />
                    </HStack>
                  )}
                  <PurchaseApprovalCard
                    approval={approval}
                    onApprove={notes => handleIndividualApprove(approval.id.toString(), notes)}
                    onReject={notes => handleIndividualReject(approval.id.toString(), notes)}
                    compact={false}
                  />
                </VStack>
              ))
            : // List/Compact View
              filteredApprovals.map(approval => {
                const urgency = getUrgencyLevel(approval.expires_at);
                const urgencyColor =
                  urgency === 'urgent'
                    ? 'text-red-600'
                    : urgency === 'soon'
                      ? 'text-orange-600'
                      : 'text-blue-600';

                return (
                  <Pressable
                    key={approval.id}
                    className="active:opacity-70"
                    onPress={() => onViewDetails(approval)}
                  >
                    <HStack className="p-3 bg-gray-50 rounded-lg space-x-3 items-center">
                      {/* Selection Checkbox */}
                      <Checkbox
                        value={selectedRequests.has(approval.id.toString())}
                        onValueChange={() => handleSelectRequest(approval.id.toString())}
                      />

                      {/* Urgency Indicator */}
                      <VStack
                        className={`w-1 h-12 rounded-full ${
                          urgency === 'urgent'
                            ? 'bg-red-500'
                            : urgency === 'soon'
                              ? 'bg-orange-500'
                              : 'bg-blue-500'
                        }`}
                      />

                      {/* Request Info */}
                      <VStack className="flex-1 space-y-1">
                        <HStack className="justify-between items-start">
                          <Text className="text-sm font-medium text-gray-900">
                            {approval.pricing_plan.name}
                          </Text>
                          <Text className="text-sm font-bold text-gray-900">
                            €{approval.amount}
                          </Text>
                        </HStack>

                        <HStack className="justify-between items-center">
                          <Text className="text-xs text-gray-600">
                            {approval.pricing_plan.hours} hours
                          </Text>
                          <Badge
                            variant="outline"
                            action={
                              urgency === 'urgent'
                                ? 'error'
                                : urgency === 'soon'
                                  ? 'warning'
                                  : 'info'
                            }
                            size="sm"
                          >
                            <Text className="text-xs">
                              {formatTimeUntilExpiry(approval.expires_at)}
                            </Text>
                          </Badge>
                        </HStack>
                      </VStack>

                      {/* Quick Actions */}
                      <HStack className="space-x-1">
                        <Button
                          action="secondary"
                          variant="outline"
                          size="sm"
                          onPress={() => handleIndividualReject(approval.id.toString())}
                          disabled={isProcessing || urgency === 'expired'}
                        >
                          <ButtonIcon as={XCircle} size={16} />
                        </Button>

                        <Button
                          action="primary"
                          size="sm"
                          onPress={() => handleIndividualApprove(approval.id.toString())}
                          disabled={isProcessing || urgency === 'expired'}
                        >
                          <ButtonIcon as={CheckCircle2} size={16} />
                        </Button>
                      </HStack>
                    </HStack>
                  </Pressable>
                );
              })}
        </VStack>
      </CardContent>
    </Card>
  );
};
