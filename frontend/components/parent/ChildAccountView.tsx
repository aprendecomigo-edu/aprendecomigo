/**
 * ChildAccountView Component
 *
 * Detailed view of a specific child's account showing their progress,
 * balance, activity history, and parent management options.
 */

import { useRouter } from 'expo-router';
import {
  ArrowLeft,
  User,
  CreditCard,
  History,
  Settings,
  AlertCircle,
  TrendingUp,
  Clock,
  Activity,
  Shield,
} from 'lucide-react-native';
import React, { useMemo } from 'react';
import { Platform, RefreshControl } from 'react-native';

import { BudgetControlSettings } from './BudgetControlSettings';

import { Badge } from '@/components/ui/badge';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Divider } from '@/components/ui/divider';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Pressable } from '@/components/ui/pressable';
import { SafeAreaView } from '@/components/ui/safe-area-view';
import { ScrollView } from '@/components/ui/scroll-view';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { useChildAccount } from '@/hooks/useChildAccount';

interface ChildAccountViewProps {
  childId: string;
}

export const ChildAccountView: React.FC<ChildAccountViewProps> = ({ childId }) => {
  const router = useRouter();
  const { childData, isLoading, error, isRefreshing, actions } = useChildAccount(childId);

  // Memoized child status
  const childStatus = useMemo(() => {
    if (!childData.balance) return 'inactive';

    const balance = parseFloat(childData.balance.current_balance || '0');
    if (balance <= 0) return 'low_balance';
    if (balance < 5) return 'warning';
    return 'active';
  }, [childData.balance]);

  const getStatusInfo = (status: string) => {
    switch (status) {
      case 'active':
        return {
          color: 'text-green-600',
          bgColor: 'bg-green-100',
          label: 'Active',
          badgeAction: 'success' as const,
        };
      case 'warning':
        return {
          color: 'text-yellow-600',
          bgColor: 'bg-yellow-100',
          label: 'Low Balance',
          badgeAction: 'warning' as const,
        };
      case 'low_balance':
        return {
          color: 'text-red-600',
          bgColor: 'bg-red-100',
          label: 'No Balance',
          badgeAction: 'error' as const,
        };
      default:
        return {
          color: 'text-gray-600',
          bgColor: 'bg-gray-100',
          label: 'Inactive',
          badgeAction: 'secondary' as const,
        };
    }
  };

  const statusInfo = getStatusInfo(childStatus);

  if (isLoading && !childData.profile) {
    return (
      <SafeAreaView className="flex-1 bg-gray-50">
        <VStack className="flex-1 justify-center items-center p-6">
          <Spinner size="large" color="#3b82f6" />
          <Text className="mt-4 text-gray-600 text-center">Loading child account...</Text>
        </VStack>
      </SafeAreaView>
    );
  }

  if (error && !childData.profile) {
    return (
      <SafeAreaView className="flex-1 bg-gray-50">
        <VStack className="flex-1 justify-center items-center p-6">
          <Icon as={AlertCircle} size={48} className="text-red-500 mb-4" />
          <Heading size="lg" className="text-gray-900 text-center mb-2">
            Unable to Load Account
          </Heading>
          <Text className="text-gray-600 text-center mb-6">{error}</Text>
          <Button action="primary" onPress={actions.refreshChildData} className="w-full max-w-xs">
            <ButtonText>Try Again</ButtonText>
          </Button>
        </VStack>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView className="flex-1 bg-gray-50">
      <ScrollView
        className="flex-1"
        refreshControl={
          <RefreshControl
            refreshing={isRefreshing}
            onRefresh={actions.refreshChildData}
            colors={['#3b82f6']}
            tintColor="#3b82f6"
          />
        }
      >
        {/* Header */}
        <VStack className="bg-white border-b border-gray-200 px-4 py-6">
          <HStack className="justify-between items-center mb-4">
            <HStack className="flex-1 space-x-3">
              <Pressable
                onPress={() => router.back()}
                className="items-center justify-center w-10 h-10 rounded-full bg-gray-100 active:bg-gray-200"
              >
                <Icon as={ArrowLeft} size={20} className="text-gray-600" />
              </Pressable>

              <VStack className="flex-1">
                <Heading size="xl" className="text-gray-900">
                  {childData.profile?.child_user.name || 'Child Account'}
                </Heading>
                <Text className="text-gray-600">{childData.profile?.child_user.email}</Text>
              </VStack>
            </HStack>

            <Badge variant="solid" action={statusInfo.badgeAction}>
              <Text className="text-xs font-medium">{statusInfo.label}</Text>
            </Badge>
          </HStack>
        </VStack>

        {/* Content */}
        <VStack className="p-4 space-y-6">
          {/* Account Overview */}
          {childData.balance && (
            <Card className="bg-white">
              <CardHeader className="pb-3">
                <Heading size="md" className="text-gray-900">
                  Account Overview
                </Heading>
              </CardHeader>
              <CardContent>
                <VStack className="space-y-4">
                  {/* Balance Info */}
                  <HStack className="justify-between items-center p-4 bg-blue-50 rounded-lg">
                    <VStack>
                      <Text className="text-sm text-blue-700 font-medium">Current Balance</Text>
                      <Text className="text-2xl font-bold text-blue-900">
                        {Math.floor(parseFloat(childData.balance.current_balance || '0'))}h
                      </Text>
                    </VStack>
                    <Icon as={CreditCard} size={32} className="text-blue-600" />
                  </HStack>

                  {/* Quick Stats */}
                  <HStack className="space-x-4">
                    <VStack className="flex-1 items-center p-3 bg-gray-50 rounded-lg">
                      <Icon as={Clock} size={20} className="text-gray-600 mb-1" />
                      <Text className="text-sm font-medium text-gray-900">
                        {childData.balance.hours_consumed_this_month || 0}h
                      </Text>
                      <Text className="text-xs text-gray-600">This Month</Text>
                    </VStack>

                    <VStack className="flex-1 items-center p-3 bg-gray-50 rounded-lg">
                      <Icon as={Activity} size={20} className="text-gray-600 mb-1" />
                      <Text className="text-sm font-medium text-gray-900">
                        {childData.transactionHistory.length}
                      </Text>
                      <Text className="text-xs text-gray-600">Transactions</Text>
                    </VStack>

                    <VStack className="flex-1 items-center p-3 bg-gray-50 rounded-lg">
                      <Icon as={TrendingUp} size={20} className="text-gray-600 mb-1" />
                      <Text className="text-sm font-medium text-gray-900">
                        {childData.purchaseHistory.length}
                      </Text>
                      <Text className="text-xs text-gray-600">Purchases</Text>
                    </VStack>
                  </HStack>
                </VStack>
              </CardContent>
            </Card>
          )}

          {/* Budget Controls */}
          <BudgetControlSettings
            childId={childId}
            budgetControl={childData.budgetControl}
            onUpdate={actions.updateChildBudget}
          />

          {/* Recent Transactions */}
          {childData.transactionHistory.length > 0 && (
            <Card className="bg-white">
              <CardHeader className="pb-3">
                <HStack className="justify-between items-center">
                  <Heading size="md" className="text-gray-900">
                    Recent Activity
                  </Heading>
                  <Button variant="outline" size="sm">
                    <ButtonText>View All</ButtonText>
                  </Button>
                </HStack>
              </CardHeader>
              <CardContent>
                <VStack className="space-y-3">
                  {childData.transactionHistory.slice(0, 5).map((transaction, index) => (
                    <HStack key={index} className="justify-between items-center py-2">
                      <HStack className="flex-1 space-x-3">
                        <VStack className="w-8 h-8 bg-gray-100 rounded-full items-center justify-center">
                          <Icon as={History} size={14} className="text-gray-600" />
                        </VStack>
                        <VStack className="flex-1">
                          <Text className="text-gray-900 font-medium">
                            {transaction.description || 'Transaction'}
                          </Text>
                          <Text className="text-xs text-gray-600">
                            {new Date(transaction.created_at).toLocaleDateString()}
                          </Text>
                        </VStack>
                      </HStack>
                      <Text
                        className={`text-sm font-medium ${
                          transaction.transaction_type === 'debit'
                            ? 'text-red-600'
                            : 'text-green-600'
                        }`}
                      >
                        {transaction.transaction_type === 'debit' ? '-' : '+'}
                        {transaction.hours}h
                      </Text>
                    </HStack>
                  ))}
                </VStack>
              </CardContent>
            </Card>
          )}

          {/* Purchase History */}
          {childData.purchaseHistory.length > 0 && (
            <Card className="bg-white">
              <CardHeader className="pb-3">
                <HStack className="justify-between items-center">
                  <Heading size="md" className="text-gray-900">
                    Purchase History
                  </Heading>
                  <Button variant="outline" size="sm">
                    <ButtonText>View All</ButtonText>
                  </Button>
                </HStack>
              </CardHeader>
              <CardContent>
                <VStack className="space-y-3">
                  {childData.purchaseHistory.slice(0, 3).map((purchase, index) => (
                    <HStack
                      key={index}
                      className="justify-between items-center py-3 border-b border-gray-100 last:border-b-0"
                    >
                      <HStack className="flex-1 space-x-3">
                        <VStack className="w-8 h-8 bg-green-100 rounded-full items-center justify-center">
                          <Icon as={CreditCard} size={14} className="text-green-600" />
                        </VStack>
                        <VStack className="flex-1">
                          <Text className="text-gray-900 font-medium">
                            {purchase.pricing_plan?.name || 'Hour Package'}
                          </Text>
                          <Text className="text-xs text-gray-600">
                            {new Date(purchase.created_at).toLocaleDateString()}
                          </Text>
                        </VStack>
                      </HStack>
                      <VStack className="items-end">
                        <Text className="text-sm font-medium text-gray-900">
                          €{purchase.amount}
                        </Text>
                        <Text className="text-xs text-green-600">+{purchase.hours_purchased}h</Text>
                      </VStack>
                    </HStack>
                  ))}
                </VStack>
              </CardContent>
            </Card>
          )}

          {/* Empty States */}
          {childData.transactionHistory.length === 0 && childData.purchaseHistory.length === 0 && (
            <Card className="bg-white">
              <CardContent className="py-12">
                <VStack className="items-center space-y-4">
                  <Icon as={Activity} size={48} className="text-gray-400" />
                  <Heading size="lg" className="text-gray-900 text-center">
                    No Activity Yet
                  </Heading>
                  <Text className="text-gray-600 text-center max-w-sm">
                    This child hasn't made any purchases or consumed hours yet.
                  </Text>
                </VStack>
              </CardContent>
            </Card>
          )}
        </VStack>
      </ScrollView>
    </SafeAreaView>
  );
};
