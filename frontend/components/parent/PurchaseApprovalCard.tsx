/**
 * PurchaseApprovalCard Component
 *
 * Individual purchase approval request card with approve/reject actions
 * and detailed information about the purchase request.
 */

import {
  CreditCard,
  Clock,
  User,
  CheckCircle,
  XCircle,
  AlertCircle,
  MessageSquare,
  Calendar,
} from 'lucide-react-native';
import React, { useState } from 'react';

import { PurchaseApprovalRequest } from '@/api/parentApi';
import { Badge } from '@/components/ui/badge';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Divider } from '@/components/ui/divider';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Input, InputField } from '@/components/ui/input';
import { Pressable } from '@/components/ui/pressable';
import { Text } from '@/components/ui/text';
import { Textarea, TextareaInput } from '@/components/ui/textarea';
import { VStack } from '@/components/ui/vstack';

interface PurchaseApprovalCardProps {
  approval: PurchaseApprovalRequest;
  onApprove: (notes?: string) => Promise<void>;
  onReject: (notes?: string) => Promise<void>;
  showActions?: boolean;
  compact?: boolean;
}

export const PurchaseApprovalCard: React.FC<PurchaseApprovalCardProps> = ({
  approval,
  onApprove,
  onReject,
  showActions = true,
  compact = false,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [responseNotes, setResponseNotes] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);

  // Format date
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-GB', {
      day: 'numeric',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  // Calculate time until expiry
  const getTimeUntilExpiry = (expiryString: string) => {
    const expiry = new Date(expiryString);
    const now = new Date();
    const diffInHours = Math.floor((expiry.getTime() - now.getTime()) / (1000 * 60 * 60));

    if (diffInHours <= 0) return 'Expired';
    if (diffInHours < 24) return `${diffInHours}h remaining`;
    return `${Math.floor(diffInHours / 24)}d remaining`;
  };

  // Get urgency level
  const getUrgencyLevel = (expiryString: string) => {
    const expiry = new Date(expiryString);
    const now = new Date();
    const diffInHours = Math.floor((expiry.getTime() - now.getTime()) / (1000 * 60 * 60));

    if (diffInHours <= 0) return 'expired';
    if (diffInHours <= 24) return 'urgent';
    if (diffInHours <= 72) return 'soon';
    return 'normal';
  };

  const urgencyLevel = getUrgencyLevel(approval.expires_at);

  // Handle approve
  const handleApprove = async () => {
    try {
      setIsProcessing(true);
      await onApprove(responseNotes || undefined);
      setResponseNotes('');
      setIsExpanded(false);
    } catch (error) {
      console.error('Error approving purchase:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  // Handle reject
  const handleReject = async () => {
    try {
      setIsProcessing(true);
      await onReject(responseNotes || undefined);
      setResponseNotes('');
      setIsExpanded(false);
    } catch (error) {
      console.error('Error rejecting purchase:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <Card className="bg-white border border-gray-200">
      <CardContent className="p-4">
        <Pressable
          onPress={() => !compact && setIsExpanded(!isExpanded)}
          className="active:opacity-70"
        >
          {/* Header */}
          <HStack className="justify-between items-start mb-3">
            <HStack className="flex-1 space-x-3">
              <VStack
                className={`
                  items-center justify-center w-10 h-10 rounded-full
                  ${
                    urgencyLevel === 'expired'
                      ? 'bg-red-100'
                      : urgencyLevel === 'urgent'
                        ? 'bg-orange-100'
                        : 'bg-blue-100'
                  }
                `}
              >
                <Icon
                  as={urgencyLevel === 'expired' ? AlertCircle : CreditCard}
                  size={20}
                  className={
                    urgencyLevel === 'expired'
                      ? 'text-red-600'
                      : urgencyLevel === 'urgent'
                        ? 'text-orange-600'
                        : 'text-blue-600'
                  }
                />
              </VStack>

              <VStack className="flex-1">
                <Text className="text-gray-900 font-semibold">{approval.pricing_plan.name}</Text>
                <Text className="text-sm text-gray-600">
                  {approval.pricing_plan.hours} hours • €{approval.amount}
                </Text>
              </VStack>
            </HStack>

            <VStack className="items-end space-y-1">
              <Badge
                variant="solid"
                action={
                  urgencyLevel === 'expired'
                    ? 'error'
                    : urgencyLevel === 'urgent'
                      ? 'warning'
                      : 'info'
                }
                size="sm"
              >
                <Text className="text-xs font-medium">
                  {getTimeUntilExpiry(approval.expires_at)}
                </Text>
              </Badge>

              <Text className="text-xs text-gray-500">{formatDate(approval.requested_at)}</Text>
            </VStack>
          </HStack>

          {/* Details */}
          {(isExpanded || compact) && (
            <VStack className="space-y-3">
              <Divider />

              {/* Request Details */}
              <VStack className="space-y-2">
                <HStack className="justify-between items-center">
                  <Text className="text-sm text-gray-600">Package Details</Text>
                  <Text className="text-sm font-medium text-gray-900">
                    {approval.pricing_plan.hours} tutoring hours
                  </Text>
                </HStack>

                <HStack className="justify-between items-center">
                  <Text className="text-sm text-gray-600">Total Cost</Text>
                  <Text className="text-sm font-medium text-gray-900">€{approval.amount}</Text>
                </HStack>

                <HStack className="justify-between items-center">
                  <Text className="text-sm text-gray-600">Expires</Text>
                  <Text className="text-sm font-medium text-gray-900">
                    {formatDate(approval.expires_at)}
                  </Text>
                </HStack>
              </VStack>

              {/* Response Notes Input */}
              {showActions && (
                <VStack className="space-y-2">
                  <Text className="text-sm font-medium text-gray-700">Add a note (optional)</Text>
                  <Textarea className="min-h-20">
                    <TextareaInput
                      placeholder="Any comments for your child..."
                      value={responseNotes}
                      onChangeText={setResponseNotes}
                      multiline
                    />
                  </Textarea>
                </VStack>
              )}
            </VStack>
          )}
        </Pressable>

        {/* Action Buttons */}
        {showActions && (isExpanded || compact) && (
          <>
            <Divider className="my-3" />

            <HStack className="space-x-3">
              <Button
                action="secondary"
                variant="outline"
                size="sm"
                className="flex-1"
                onPress={handleReject}
                disabled={isProcessing || urgencyLevel === 'expired'}
              >
                <ButtonIcon as={XCircle} size={16} />
                <ButtonText className="ml-1">Reject</ButtonText>
              </Button>

              <Button
                action="primary"
                size="sm"
                className="flex-1"
                onPress={handleApprove}
                disabled={isProcessing || urgencyLevel === 'expired'}
              >
                <ButtonIcon as={CheckCircle} size={16} />
                <ButtonText className="ml-1">
                  {isProcessing ? 'Processing...' : 'Approve'}
                </ButtonText>
              </Button>
            </HStack>
          </>
        )}

        {/* Compact Action Buttons */}
        {showActions && !isExpanded && !compact && (
          <>
            <Divider className="my-3" />

            <HStack className="justify-between items-center">
              <Button variant="ghost" size="sm" onPress={() => setIsExpanded(true)}>
                <ButtonText className="text-blue-600">View Details</ButtonText>
              </Button>

              <HStack className="space-x-2">
                <Button
                  action="secondary"
                  variant="outline"
                  size="sm"
                  onPress={handleReject}
                  disabled={isProcessing || urgencyLevel === 'expired'}
                >
                  <ButtonIcon as={XCircle} size={14} />
                </Button>

                <Button
                  action="primary"
                  size="sm"
                  onPress={handleApprove}
                  disabled={isProcessing || urgencyLevel === 'expired'}
                >
                  <ButtonIcon as={CheckCircle} size={14} />
                </Button>
              </HStack>
            </HStack>
          </>
        )}

        {/* Expired State */}
        {urgencyLevel === 'expired' && (
          <VStack className="mt-3 p-3 bg-red-50 rounded-lg border border-red-200">
            <HStack className="items-center space-x-2">
              <Icon as={AlertCircle} size={16} className="text-red-600" />
              <Text className="text-sm text-red-800 font-medium">This request has expired</Text>
            </HStack>
            <Text className="text-xs text-red-700 mt-1">
              The child will need to submit a new purchase request.
            </Text>
          </VStack>
        )}
      </CardContent>
    </Card>
  );
};
