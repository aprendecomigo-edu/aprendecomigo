/**
 * PurchaseApprovalModal Component
 * 
 * Detailed modal for purchase approval/rejection with:
 * - Full purchase context and reasoning
 * - Child information and purchase history
 * - Parent notes and response options
 * - Budget impact analysis
 * - Mobile-optimized interaction
 */

import React, { useState, useEffect } from 'react';
import { 
  CheckCircle, 
  XCircle, 
  Clock, 
  User,
  CreditCard,
  MessageSquare,
  AlertCircle,
  TrendingUp,
  Calendar,
  Euro,
  BookOpen,
  Target,
  X,
  Send
} from 'lucide-react-native';

import { Badge } from '@/components/ui/badge';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Modal, ModalBackdrop, ModalContent, ModalHeader, ModalBody, ModalFooter } from '@/components/ui/modal';
import { Pressable } from '@/components/ui/pressable';
import { Progress } from '@/components/ui/progress';
import { ScrollView } from '@/components/ui/scroll-view';
import { Text } from '@/components/ui/text';
import { Textarea, TextareaInput } from '@/components/ui/textarea';
import { VStack } from '@/components/ui/vstack';
import { Divider } from '@/components/ui/divider';

import { PurchaseApprovalRequest, FamilyBudgetControl } from '@/api/parentApi';

interface PurchaseApprovalModalProps {
  isOpen: boolean;
  onClose: () => void;
  approval: PurchaseApprovalRequest | null;
  onApprove: (requestId: string, notes?: string) => Promise<void>;
  onReject: (requestId: string, notes?: string) => Promise<void>;
  budgetControl?: FamilyBudgetControl;
  childSpendingHistory?: {
    monthly_spent: number;
    weekly_spent: number;
    last_purchases: Array<{
      date: string;
      amount: string;
      plan_name: string;
    }>;
  };
}

export const PurchaseApprovalModal: React.FC<PurchaseApprovalModalProps> = ({
  isOpen,
  onClose,
  approval,
  onApprove,
  onReject,
  budgetControl,
  childSpendingHistory,
}) => {
  const [responseNotes, setResponseNotes] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [selectedAction, setSelectedAction] = useState<'approve' | 'reject' | null>(null);

  // Reset state when modal opens/closes
  useEffect(() => {
    if (isOpen) {
      setResponseNotes('');
      setSelectedAction(null);
      setIsProcessing(false);
    }
  }, [isOpen]);

  if (!approval) return null;

  // Calculate urgency level
  const getUrgencyLevel = (expiryString: string) => {
    const expiry = new Date(expiryString);
    const now = new Date();
    const diffInHours = Math.floor((expiry.getTime() - now.getTime()) / (1000 * 60 * 60));
    
    if (diffInHours <= 0) return 'expired';
    if (diffInHours <= 24) return 'urgent';
    if (diffInHours <= 72) return 'soon';
    return 'normal';
  };

  const urgency = getUrgencyLevel(approval.expires_at);

  // Format date
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-GB', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  // Calculate budget impact
  const getBudgetImpact = () => {
    if (!budgetControl || !childSpendingHistory) return null;

    const purchaseAmount = parseFloat(approval.amount);
    const monthlySpent = childSpendingHistory.monthly_spent;
    const weeklySpent = childSpendingHistory.weekly_spent;

    const impacts = [];

    if (budgetControl.monthly_limit) {
      const monthlyLimit = parseFloat(budgetControl.monthly_limit);
      const newMonthlyTotal = monthlySpent + purchaseAmount;
      const percentage = (newMonthlyTotal / monthlyLimit) * 100;
      
      impacts.push({
        type: 'Monthly',
        current: monthlySpent,
        newTotal: newMonthlyTotal,
        limit: monthlyLimit,
        percentage,
        exceeds: newMonthlyTotal > monthlyLimit,
      });
    }

    if (budgetControl.weekly_limit) {
      const weeklyLimit = parseFloat(budgetControl.weekly_limit);
      const newWeeklyTotal = weeklySpent + purchaseAmount;
      const percentage = (newWeeklyTotal / weeklyLimit) * 100;
      
      impacts.push({
        type: 'Weekly',
        current: weeklySpent,
        newTotal: newWeeklyTotal,
        limit: weeklyLimit,
        percentage,
        exceeds: newWeeklyTotal > weeklyLimit,
      });
    }

    return impacts;
  };

  const budgetImpacts = getBudgetImpact();

  // Handle approval action
  const handleApprove = async () => {
    try {
      setIsProcessing(true);
      await onApprove(approval.id.toString(), responseNotes || undefined);
      onClose();
    } catch (error) {
      console.error('Error approving purchase:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  // Handle rejection action
  const handleReject = async () => {
    try {
      setIsProcessing(true);
      await onReject(approval.id.toString(), responseNotes || undefined);
      onClose();
    } catch (error) {
      console.error('Error rejecting purchase:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  // Get suggested response templates
  const getSuggestedResponses = (action: 'approve' | 'reject') => {
    if (action === 'approve') {
      return [
        "Approved! Keep up the great work with your studies.",
        "Go ahead! This looks like a good investment in your learning.",
        "Approved. Please use your tutoring hours wisely.",
      ];
    } else {
      return [
        "Let's discuss your tutoring needs first before purchasing more hours.",
        "You still have unused hours. Please use them before buying more.",
        "This would exceed our monthly budget. Let's wait until next month.",
      ];
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="lg">
      <ModalBackdrop />
      <ModalContent className="max-h-[90vh]">
        <ModalHeader>
          <HStack className="justify-between items-center w-full">
            <HStack className="space-x-3">
              <Icon 
                as={urgency === 'expired' ? AlertCircle : CreditCard} 
                size={24}
                className={
                  urgency === 'expired' ? 'text-red-600' : 
                  urgency === 'urgent' ? 'text-orange-600' : 
                  'text-blue-600'
                }
              />
              <VStack>
                <Heading size="lg" className="text-gray-900">
                  Purchase Approval
                </Heading>
                <Text className="text-sm text-gray-600">
                  {approval.pricing_plan.name}
                </Text>
              </VStack>
            </HStack>
            
            <Button
              variant="ghost"
              size="sm"
              onPress={onClose}
            >
              <ButtonIcon as={X} size={20} />
            </Button>
          </HStack>
        </ModalHeader>

        <ModalBody>
          <ScrollView>
            <VStack className="space-y-6">
              {/* Request Overview */}
              <Card className="bg-gray-50">
                <CardContent className="p-4">
                  <VStack className="space-y-3">
                    <HStack className="justify-between items-start">
                      <VStack className="flex-1">
                        <Text className="text-lg font-semibold text-gray-900">
                          €{approval.amount}
                        </Text>
                        <Text className="text-sm text-gray-600">
                          {approval.pricing_plan.hours} tutoring hours
                        </Text>
                      </VStack>
                      
                      <Badge 
                        variant="solid" 
                        action={
                          urgency === 'expired' ? 'error' : 
                          urgency === 'urgent' ? 'warning' : 
                          'info'
                        }
                        size="md"
                      >
                        <Text className="text-sm font-medium">
                          {urgency === 'expired' ? 'Expired' :
                           urgency === 'urgent' ? 'Urgent' :
                           urgency === 'soon' ? 'Soon' : 'Normal'}
                        </Text>
                      </Badge>
                    </HStack>

                    <HStack className="space-x-4">
                      <HStack className="items-center space-x-2">
                        <Icon as={Calendar} size={16} className="text-gray-500" />
                        <Text className="text-sm text-gray-600">
                          Requested {formatDate(approval.requested_at)}
                        </Text>
                      </HStack>
                      
                      <HStack className="items-center space-x-2">
                        <Icon as={Clock} size={16} className="text-gray-500" />
                        <Text className="text-sm text-gray-600">
                          Expires {formatDate(approval.expires_at)}
                        </Text>
                      </HStack>
                    </HStack>
                  </VStack>
                </CardContent>
              </Card>

              {/* Budget Impact Analysis */}
              {budgetImpacts && budgetImpacts.length > 0 && (
                <VStack className="space-y-3">
                  <HStack className="items-center space-x-2">
                    <Icon as={TrendingUp} size={20} className="text-blue-600" />
                    <Heading size="md" className="text-gray-900">
                      Budget Impact
                    </Heading>
                  </HStack>

                  {budgetImpacts.map((impact) => (
                    <Card key={impact.type} className={`border ${impact.exceeds ? 'border-red-200 bg-red-50' : 'border-gray-200'}`}>
                      <CardContent className="p-3">
                        <VStack className="space-y-2">
                          <HStack className="justify-between items-center">
                            <Text className="text-sm font-medium text-gray-900">
                              {impact.type} Budget
                            </Text>
                            <Text className={`text-sm font-semibold ${impact.exceeds ? 'text-red-600' : 'text-gray-900'}`}>
                              €{impact.newTotal.toFixed(2)} / €{impact.limit.toFixed(2)}
                            </Text>
                          </HStack>
                          
                          <Progress 
                            value={Math.min(impact.percentage, 100)} 
                            className="h-2"
                          />
                          
                          <HStack className="justify-between items-center">
                            <Text className="text-xs text-gray-600">
                              Currently: €{impact.current.toFixed(2)}
                            </Text>
                            <Text className={`text-xs font-medium ${impact.exceeds ? 'text-red-600' : 'text-gray-600'}`}>
                              {Math.round(impact.percentage)}%
                              {impact.exceeds && ' (Over Budget)'}
                            </Text>
                          </HStack>
                        </VStack>
                      </CardContent>
                    </Card>
                  ))}
                </VStack>
              )}

              {/* Recent Purchase History */}
              {childSpendingHistory?.last_purchases && childSpendingHistory.last_purchases.length > 0 && (
                <VStack className="space-y-3">
                  <HStack className="items-center space-x-2">
                    <Icon as={BookOpen} size={20} className="text-blue-600" />
                    <Heading size="md" className="text-gray-900">
                      Recent Purchases
                    </Heading>
                  </HStack>

                  <VStack className="space-y-2">
                    {childSpendingHistory.last_purchases.slice(0, 3).map((purchase, index) => (
                      <HStack key={index} className="justify-between items-center p-3 bg-gray-50 rounded-lg">
                        <VStack>
                          <Text className="text-sm font-medium text-gray-900">
                            {purchase.plan_name}
                          </Text>
                          <Text className="text-xs text-gray-600">
                            {formatDate(purchase.date)}
                          </Text>
                        </VStack>
                        <Text className="text-sm font-semibold text-gray-900">
                          €{purchase.amount}
                        </Text>
                      </HStack>
                    ))}
                  </VStack>
                </VStack>
              )}

              {/* Response Notes */}
              <VStack className="space-y-3">
                <HStack className="items-center space-x-2">
                  <Icon as={MessageSquare} size={20} className="text-blue-600" />
                  <Heading size="md" className="text-gray-900">
                    Add a Note (Optional)
                  </Heading>
                </HStack>

                <Textarea className="min-h-24">
                  <TextareaInput
                    placeholder="Write a message to your child about this decision..."
                    value={responseNotes}
                    onChangeText={setResponseNotes}
                    multiline
                  />
                </Textarea>

                {/* Suggested Responses */}
                {selectedAction && (
                  <VStack className="space-y-2">
                    <Text className="text-sm text-gray-700">Suggested responses:</Text>
                    <VStack className="space-y-1">
                      {getSuggestedResponses(selectedAction).map((suggestion, index) => (
                        <Pressable
                          key={index}
                          className="p-2 bg-blue-50 rounded-lg active:bg-blue-100"
                          onPress={() => setResponseNotes(suggestion)}
                        >
                          <Text className="text-sm text-blue-800">
                            "{suggestion}"
                          </Text>
                        </Pressable>
                      ))}
                    </VStack>
                  </VStack>
                )}
              </VStack>

              {/* Warnings */}
              {urgency === 'expired' && (
                <Card className="bg-red-50 border border-red-200">
                  <CardContent className="p-3">
                    <HStack className="items-center space-x-2">
                      <Icon as={AlertCircle} size={20} className="text-red-600" />
                      <VStack className="flex-1">
                        <Text className="text-sm font-medium text-red-800">
                          This request has expired
                        </Text>
                        <Text className="text-xs text-red-700">
                          The child will need to submit a new purchase request.
                        </Text>
                      </VStack>
                    </HStack>
                  </CardContent>
                </Card>
              )}

              {budgetImpacts?.some(impact => impact.exceeds) && (
                <Card className="bg-orange-50 border border-orange-200">
                  <CardContent className="p-3">
                    <HStack className="items-center space-x-2">
                      <Icon as={AlertCircle} size={20} className="text-orange-600" />
                      <VStack className="flex-1">
                        <Text className="text-sm font-medium text-orange-800">
                          Budget limit exceeded
                        </Text>
                        <Text className="text-xs text-orange-700">
                          This purchase would exceed your set budget limits.
                        </Text>
                      </VStack>
                    </HStack>
                  </CardContent>
                </Card>
              )}
            </VStack>
          </ScrollView>
        </ModalBody>

        <ModalFooter>
          <HStack className="space-x-3 w-full">
            <Button
              action="secondary"
              variant="outline"
              size="md"
              className="flex-1"
              onPress={() => {
                setSelectedAction('reject');
                handleReject();
              }}
              disabled={isProcessing || urgency === 'expired'}
            >
              <ButtonIcon as={XCircle} size={18} />
              <ButtonText className="ml-2">
                {isProcessing && selectedAction === 'reject' ? 'Rejecting...' : 'Reject'}
              </ButtonText>
            </Button>
            
            <Button
              action="primary"
              size="md"
              className="flex-1"
              onPress={() => {
                setSelectedAction('approve');
                handleApprove();
              }}
              disabled={isProcessing || urgency === 'expired'}
            >
              <ButtonIcon as={CheckCircle} size={18} />
              <ButtonText className="ml-2">
                {isProcessing && selectedAction === 'approve' ? 'Approving...' : 'Approve'}
              </ButtonText>
            </Button>
          </HStack>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};