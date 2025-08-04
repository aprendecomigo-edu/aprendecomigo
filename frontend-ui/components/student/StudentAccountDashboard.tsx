/**
 * Student Account Dashboard Component
 *
 * Comprehensive dashboard providing students with complete visibility into
 * their tutoring hour balances, purchase history, consumption tracking,
 * and account management features.
 */

import useRouter from '@unitools/router';
import {
  CreditCard,
  History,
  Package,
  Settings,
  ShoppingCart,
  AlertTriangle,
  TrendingUp,
  Clock,
  RefreshCw,
  Search,
  Plus,
  Bell,
} from 'lucide-react-native';
import React, { useMemo } from 'react';
import { Platform } from 'react-native';

import { BalanceAlertProvider } from './balance/BalanceAlertProvider';
import { NotificationCenter } from './balance/NotificationCenter';
import { AccountSettings } from './dashboard/AccountSettings';
import { DashboardOverview } from './dashboard/DashboardOverview';
import { PurchaseHistory } from './dashboard/PurchaseHistory';
import { TransactionHistory } from './dashboard/TransactionHistory';

import { useUserProfile } from '@/api/auth';
import { StudentBalanceCard } from '@/components/purchase';
import { Badge } from '@/components/ui/badge';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
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
import { useStudentDashboard } from '@/hooks/useStudentDashboard';

// Import dashboard sections

interface StudentAccountDashboardProps {
  email?: string;
  className?: string;
}

/**
 * Tab navigation configuration
 */
const DASHBOARD_TABS = [
  {
    id: 'overview' as const,
    label: 'Overview',
    icon: TrendingUp,
    description: 'Account summary and quick actions',
  },
  {
    id: 'transactions' as const,
    label: 'Transactions',
    icon: History,
    description: 'Transaction history and payments',
  },
  {
    id: 'purchases' as const,
    label: 'Purchases',
    icon: Package,
    description: 'Purchase history and consumption',
  },
  {
    id: 'notifications' as const,
    label: 'Notifications',
    icon: Bell,
    description: 'Balance alerts and important updates',
  },
  {
    id: 'settings' as const,
    label: 'Settings',
    icon: Settings,
    description: 'Account and profile settings',
  },
];

/**
 * Main Student Account Dashboard Component
 */
export function StudentAccountDashboard({ email, className = '' }: StudentAccountDashboardProps) {
  const router = useRouter();
  const { userProfile } = useUserProfile();
  const dashboard = useStudentDashboard(email);

  // Quick stats from balance data
  const quickStats = useMemo(() => {
    if (!dashboard.balance) return null;

    const balance = dashboard.balance.balance_summary;
    const packages = dashboard.balance.package_status.active_packages;
    const expirations = dashboard.balance.upcoming_expirations;

    return {
      remainingHours: parseFloat(balance.remaining_hours),
      totalPurchased: parseFloat(balance.hours_purchased),
      totalConsumed: parseFloat(balance.hours_consumed),
      activePackages: packages.length,
      expiringSoon: expirations.filter(exp => exp.days_until_expiry && exp.days_until_expiry <= 7)
        .length,
    };
  }, [dashboard.balance]);

  const handlePurchaseMore = () => {
    router.push('/purchase');
  };

  const handleRefreshAll = async () => {
    await dashboard.actions.refreshAll();
  };

  const renderTabContent = () => {
    try {
      switch (dashboard.state.activeTab) {
        case 'overview':
          return (
            <DashboardOverview
              balance={dashboard.balance}
              loading={dashboard.balanceLoading}
              error={dashboard.balanceError}
              onRefresh={dashboard.actions.refreshBalance}
              onPurchase={handlePurchaseMore}
              onTabChange={dashboard.actions.setActiveTab}
            />
          );

        case 'transactions':
          return (
            <TransactionHistory
              transactions={dashboard.transactions}
              loading={dashboard.transactionsLoading}
              error={dashboard.transactionsError}
              filters={dashboard.state.transactionFilters}
              onFiltersChange={dashboard.actions.setTransactionFilters}
              onRefresh={() => dashboard.actions.refreshTransactions(1)}
              onLoadMore={dashboard.actions.loadMoreTransactions}
              searchQuery={dashboard.state.searchQuery}
              onSearchChange={dashboard.actions.setSearchQuery}
            />
          );

        case 'purchases':
          return (
            <PurchaseHistory
              purchases={dashboard.purchases}
              loading={dashboard.purchasesLoading}
              error={dashboard.purchasesError}
              filters={dashboard.state.purchaseFilters}
              onFiltersChange={dashboard.actions.setPurchaseFilters}
              onRefresh={() => dashboard.actions.refreshPurchases(1)}
              onLoadMore={dashboard.actions.loadMorePurchases}
              searchQuery={dashboard.state.searchQuery}
              onSearchChange={dashboard.actions.setSearchQuery}
            />
          );

        case 'notifications':
          return (
            <NotificationCenter showSettings={true} showFilters={true} maxNotifications={50} />
          );

        case 'settings':
          return (
            <AccountSettings
              userProfile={userProfile}
              balance={dashboard.balance}
              onRefresh={dashboard.actions.refreshBalance}
            />
          );

        default:
          return null;
      }
    } catch (error) {
      console.error('Error rendering dashboard tab:', error);
      return (
        <Card className="p-6 border-error-200">
          <VStack space="md" className="items-center">
            <Icon as={AlertTriangle} size="xl" className="text-error-500" />
            <VStack space="sm" className="items-center">
              <Heading size="sm" className="text-error-900">
                Something went wrong
              </Heading>
              <Text className="text-error-700 text-sm text-center">
                Unable to load this section. Please try refreshing or switching tabs.
              </Text>
            </VStack>
            <Button action="secondary" variant="outline" size="sm" onPress={handleRefreshAll}>
              <ButtonIcon as={RefreshCw} />
              <ButtonText>Refresh Dashboard</ButtonText>
            </Button>
          </VStack>
        </Card>
      );
    }
  };

  return (
    <BalanceAlertProvider enableMonitoring={true} pollingInterval={30000}>
      <SafeAreaView className={`flex-1 bg-background-50 ${className}`}>
        <ScrollView className="flex-1" showsVerticalScrollIndicator={false}>
          <VStack className="flex-1 px-4 py-6 max-w-6xl mx-auto w-full" space="lg">
            {/* Header */}
            <VStack space="sm">
              <HStack className="items-center justify-between">
                <VStack space="xs" className="flex-1">
                  <Heading size="3xl" className="text-typography-900">
                    Account Dashboard
                  </Heading>
                  <Text className="text-lg text-typography-600">
                    Manage your tutoring hours and account settings
                  </Text>
                </VStack>

                <HStack space="sm">
                  <Button
                    action="secondary"
                    variant="outline"
                    size="md"
                    onPress={handleRefreshAll}
                    className="min-w-24"
                  >
                    <ButtonIcon as={RefreshCw} />
                    <ButtonText className="hidden sm:flex">Refresh</ButtonText>
                  </Button>

                  <Button
                    action="primary"
                    variant="solid"
                    size="md"
                    onPress={handlePurchaseMore}
                    className="min-w-32"
                  >
                    <ButtonIcon as={Plus} />
                    <ButtonText>Purchase Hours</ButtonText>
                  </Button>
                </HStack>
              </HStack>

              {/* Quick Stats Cards */}
              {quickStats && (
                <HStack space="md" className="flex-wrap lg:flex-nowrap">
                  <Card className="flex-1 min-w-36 sm:min-w-32 p-4">
                    <VStack space="xs" className="items-center">
                      <Text className="text-2xl font-bold text-primary-600">
                        {quickStats.remainingHours.toFixed(1)}
                      </Text>
                      <Text className="text-xs text-typography-500 text-center">
                        Hours Remaining
                      </Text>
                    </VStack>
                  </Card>

                  <Card className="flex-1 min-w-36 sm:min-w-32 p-4">
                    <VStack space="xs" className="items-center">
                      <Text className="text-lg font-semibold text-typography-700">
                        {quickStats.activePackages}
                      </Text>
                      <Text className="text-xs text-typography-500 text-center">
                        Active Packages
                      </Text>
                    </VStack>
                  </Card>

                  {quickStats.expiringSoon > 0 && (
                    <Card className="flex-1 min-w-36 sm:min-w-32 p-4 border-warning-300">
                      <VStack space="xs" className="items-center">
                        <HStack space="xs" className="items-center">
                          <Icon as={AlertTriangle} size="sm" className="text-warning-600" />
                          <Text className="text-lg font-semibold text-warning-700">
                            {quickStats.expiringSoon}
                          </Text>
                        </HStack>
                        <Text className="text-xs text-typography-500 text-center">
                          Expiring Soon
                        </Text>
                      </VStack>
                    </Card>
                  )}
                </HStack>
              )}
            </VStack>

            {/* Tab Navigation */}
            <Card className="p-1">
              <HStack space="xs" className="flex-wrap lg:flex-nowrap">
                {DASHBOARD_TABS.map(tab => {
                  const isActive = dashboard.state.activeTab === tab.id;

                  return (
                    <Pressable
                      key={tab.id}
                      className={`flex-1 min-w-20 sm:min-w-24 p-3 rounded-md transition-colors ${
                        isActive
                          ? 'bg-primary-600'
                          : `bg-transparent ${
                              Platform.OS === 'web' ? 'hover:bg-background-100' : ''
                            } active:bg-background-200`
                      }`}
                      onPress={() => dashboard.actions.setActiveTab(tab.id)}
                      accessibilityRole="tab"
                      accessibilityState={{ selected: isActive }}
                      accessibilityLabel={`${tab.label} - ${tab.description}`}
                    >
                      <VStack space="xs" className="items-center">
                        <Icon
                          as={tab.icon}
                          size="sm"
                          className={isActive ? 'text-white' : 'text-typography-600'}
                        />
                        <Text
                          className={`text-xs font-medium text-center ${
                            isActive ? 'text-white' : 'text-typography-700'
                          }`}
                          numberOfLines={1}
                        >
                          {tab.label}
                        </Text>
                      </VStack>
                    </Pressable>
                  );
                })}
              </HStack>
            </Card>

            {/* Search Bar (shown for transactions and purchases tabs) */}
            {(dashboard.state.activeTab === 'transactions' ||
              dashboard.state.activeTab === 'purchases') && (
              <Card className="p-4">
                <Input className="w-full">
                  <InputSlot className="pl-3">
                    <InputIcon as={Search} className="text-typography-400" />
                  </InputSlot>
                  <InputField
                    placeholder={`Search ${dashboard.state.activeTab}...`}
                    value={dashboard.state.searchQuery}
                    onChangeText={dashboard.actions.setSearchQuery}
                    className="pl-10"
                  />
                </Input>
              </Card>
            )}

            {/* Tab Content */}
            <VStack className="flex-1" space="lg">
              {renderTabContent()}
            </VStack>
          </VStack>
        </ScrollView>
      </SafeAreaView>
    </BalanceAlertProvider>
  );
}
