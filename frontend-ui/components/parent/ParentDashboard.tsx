/**
 * ParentDashboard Component
 *
 * Main parent dashboard providing overview of all children's accounts,
 * family metrics, purchase approvals, and quick actions for parent users.
 */

import {
  Users,
  Bell,
  CreditCard,
  Settings,
  AlertCircle,
  TrendingUp,
  Clock,
  CheckCircle,
  XCircle,
  Search,
  Filter,
} from 'lucide-react-native';
import React, { useMemo } from 'react';
import { Platform, RefreshControl } from 'react-native';

import { ChildAccountCard } from './ChildAccountCard';
import { ChildAccountSelector } from './ChildAccountSelector';
import { FamilyMetricsOverview } from './FamilyMetricsOverview';
import { ParentQuickActions } from './ParentQuickActions';
import { PurchaseApprovalCard } from './PurchaseApprovalCard';

import { useAuth } from '@/api/authContext';
import { Badge } from '@/components/ui/badge';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Divider } from '@/components/ui/divider';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Input, InputField, InputIcon, InputSlot } from '@/components/ui/input';
import { Pressable } from '@/components/ui/pressable';
import { SafeAreaView } from '@/components/ui/safe-area-view';
import { ScrollView } from '@/components/ui/scroll-view';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { useParentDashboard } from '@/hooks/useParentDashboard';

export const ParentDashboard: React.FC = () => {
  const { userProfile } = useAuth();
  const {
    dashboardData,
    familyMetrics,
    children,
    selectedChild,
    pendingApprovals,
    recentApprovals,
    isLoading,
    error,
    isRefreshing,
    timeframe,
    actions,
  } = useParentDashboard();

  // Memoized dashboard sections
  const dashboardSections = useMemo(() => {
    if (!dashboardData || !familyMetrics) return [];

    return [
      {
        id: 'overview',
        title: 'Family Overview',
        priority: 1,
        hasData: true,
      },
      {
        id: 'approvals',
        title: 'Purchase Approvals',
        priority: 2,
        hasData: pendingApprovals.length > 0,
        badge: pendingApprovals.length > 0 ? pendingApprovals.length.toString() : null,
      },
      {
        id: 'children',
        title: 'Children Accounts',
        priority: 3,
        hasData: children.length > 0,
      },
      {
        id: 'recent',
        title: 'Recent Activity',
        priority: 4,
        hasData: recentApprovals.length > 0,
      },
    ];
  }, [
    dashboardData,
    familyMetrics,
    pendingApprovals.length,
    recentApprovals.length,
    children.length,
  ]);

  if (isLoading && !dashboardData) {
    return (
      <SafeAreaView className="flex-1 bg-gray-50">
        <VStack className="flex-1 justify-center items-center p-6">
          <Spinner size="large" color="#3b82f6" />
          <Text className="mt-4 text-gray-600 text-center">Loading your family dashboard...</Text>
        </VStack>
      </SafeAreaView>
    );
  }

  if (error && !dashboardData) {
    return (
      <SafeAreaView className="flex-1 bg-gray-50">
        <VStack className="flex-1 justify-center items-center p-6">
          <Icon as={AlertCircle} size={48} className="text-red-500 mb-4" />
          <Heading size="lg" className="text-gray-900 text-center mb-2">
            Unable to Load Dashboard
          </Heading>
          <Text className="text-gray-600 text-center mb-6">{error}</Text>
          <Button action="primary" onPress={actions.refreshDashboard} className="w-full max-w-xs">
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
            onRefresh={actions.refreshDashboard}
            colors={['#3b82f6']}
            tintColor="#3b82f6"
          />
        }
      >
        {/* Header */}
        <VStack className="bg-white border-b border-gray-200 px-4 py-6">
          <HStack className="justify-between items-center mb-4">
            <VStack>
              <Heading size="xl" className="text-gray-900">
                Family Dashboard
              </Heading>
              <Text className="text-gray-600">Welcome back, {userProfile?.name || 'Parent'}</Text>
            </VStack>

            <HStack className="space-x-2">
              {pendingApprovals.length > 0 && (
                <Pressable className="relative">
                  <Icon as={Bell} size={24} className="text-gray-600" />
                  <Badge
                    size="sm"
                    variant="solid"
                    action="error"
                    className="absolute -top-2 -right-2 min-w-5 h-5"
                  >
                    <Text className="text-xs text-white font-medium">
                      {pendingApprovals.length}
                    </Text>
                  </Badge>
                </Pressable>
              )}

              <Pressable>
                <Icon as={Settings} size={24} className="text-gray-600" />
              </Pressable>
            </HStack>
          </HStack>

          {/* Child Account Selector */}
          {children.length > 1 && (
            <ChildAccountSelector
              children={children}
              selectedChildId={selectedChild?.id.toString() || null}
              onSelectChild={actions.selectChild}
            />
          )}
        </VStack>

        {/* Dashboard Content */}
        <VStack className="p-4 space-y-6">
          {/* Family Metrics Overview */}
          {familyMetrics && (
            <FamilyMetricsOverview
              metrics={familyMetrics}
              timeframe={timeframe}
              onTimeframeChange={actions.setTimeframe}
            />
          )}

          {/* Quick Actions */}
          <ParentQuickActions
            pendingApprovalsCount={pendingApprovals.length}
            childrenCount={children.length}
            onRefresh={actions.refreshDashboard}
          />

          {/* Pending Purchase Approvals */}
          {pendingApprovals.length > 0 && (
            <Card className="bg-white">
              <CardHeader className="pb-3">
                <HStack className="justify-between items-center">
                  <Heading size="md" className="text-gray-900">
                    Pending Approvals
                  </Heading>
                  <Badge variant="solid" action="warning">
                    <Text className="text-xs font-medium">{pendingApprovals.length} pending</Text>
                  </Badge>
                </HStack>
              </CardHeader>
              <CardContent>
                <VStack className="space-y-3">
                  {pendingApprovals.slice(0, 3).map(approval => (
                    <PurchaseApprovalCard
                      key={approval.id}
                      approval={approval}
                      onApprove={notes => actions.approvePurchase(approval.id.toString(), notes)}
                      onReject={notes => actions.rejectPurchase(approval.id.toString(), notes)}
                    />
                  ))}

                  {pendingApprovals.length > 3 && (
                    <Button variant="outline" size="sm" className="w-full">
                      <ButtonText>View All {pendingApprovals.length} Approvals</ButtonText>
                    </Button>
                  )}
                </VStack>
              </CardContent>
            </Card>
          )}

          {/* Children Account Cards */}
          {children.length > 0 && (
            <Card className="bg-white">
              <CardHeader className="pb-3">
                <HStack className="justify-between items-center">
                  <Heading size="md" className="text-gray-900">
                    Children Accounts
                  </Heading>
                  <HStack className="space-x-2">
                    <Button variant="outline" size="sm">
                      <ButtonIcon as={Search} size={16} />
                    </Button>
                    <Button variant="outline" size="sm">
                      <ButtonIcon as={Filter} size={16} />
                    </Button>
                  </HStack>
                </HStack>
              </CardHeader>
              <CardContent>
                <VStack className="space-y-4">
                  {children.map(child => {
                    const childMetrics = familyMetrics?.children_summary.find(
                      c => c.child_id === child.id
                    );

                    return (
                      <ChildAccountCard
                        key={child.id}
                        child={child}
                        metrics={childMetrics}
                        isSelected={selectedChild?.id === child.id}
                        onSelect={() => actions.selectChild(child.id.toString())}
                      />
                    );
                  })}
                </VStack>
              </CardContent>
            </Card>
          )}

          {/* Recent Activity */}
          {recentApprovals.length > 0 && (
            <Card className="bg-white">
              <CardHeader className="pb-3">
                <Heading size="md" className="text-gray-900">
                  Recent Decisions
                </Heading>
              </CardHeader>
              <CardContent>
                <VStack className="space-y-3">
                  {recentApprovals.slice(0, 5).map(approval => (
                    <HStack key={approval.id} className="justify-between items-center py-2">
                      <HStack className="flex-1 space-x-3">
                        <Icon
                          as={approval.status === 'approved' ? CheckCircle : XCircle}
                          size={20}
                          className={
                            approval.status === 'approved' ? 'text-green-600' : 'text-red-600'
                          }
                        />
                        <VStack className="flex-1">
                          <Text className="text-gray-900 font-medium">
                            {approval.pricing_plan.name}
                          </Text>
                          <Text className="text-sm text-gray-600">
                            €{approval.amount} •{' '}
                            {new Date(approval.responded_at || '').toLocaleDateString()}
                          </Text>
                        </VStack>
                      </HStack>
                      <Badge
                        variant="solid"
                        action={approval.status === 'approved' ? 'success' : 'error'}
                      >
                        <Text className="text-xs font-medium capitalize">{approval.status}</Text>
                      </Badge>
                    </HStack>
                  ))}
                </VStack>
              </CardContent>
            </Card>
          )}

          {/* Empty State for No Children */}
          {children.length === 0 && (
            <Card className="bg-white">
              <CardContent className="py-12">
                <VStack className="items-center space-y-4">
                  <Icon as={Users} size={48} className="text-gray-400" />
                  <Heading size="lg" className="text-gray-900 text-center">
                    No Children Added Yet
                  </Heading>
                  <Text className="text-gray-600 text-center max-w-sm">
                    Add your children's accounts to start managing their tutoring experience and
                    purchases.
                  </Text>
                  <Button action="primary" className="mt-4">
                    <ButtonText>Add Child Account</ButtonText>
                  </Button>
                </VStack>
              </CardContent>
            </Card>
          )}
        </VStack>
      </ScrollView>
    </SafeAreaView>
  );
};
