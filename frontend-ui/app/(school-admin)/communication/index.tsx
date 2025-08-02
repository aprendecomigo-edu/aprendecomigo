import { isWeb } from '@gluestack-ui/nativewind-utils/IsWeb';
import { router } from 'expo-router';
import {
  MailIcon,
  TemplateIcon,
  PaletteIcon,
  BarChart3Icon,
  SettingsIcon,
  PlusIcon,
  TrendingUpIcon,
  UsersIcon,
  SendIcon,
} from 'lucide-react-native';
import React, { useCallback, useEffect, useState } from 'react';

import { useAuth } from '@/api/authContext';
import MainLayout from '@/components/layouts/main-layout';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Center } from '@/components/ui/center';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Pressable } from '@/components/ui/pressable';
import { ScrollView } from '@/components/ui/scroll-view';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { useCommunicationTemplates } from '@/hooks/useCommunicationTemplates';
import { useEmailAnalytics } from '@/hooks/useEmailAnalytics';
import { useSchoolBranding } from '@/hooks/useSchoolBranding';

const CommunicationDashboard = () => {
  const { userProfile } = useAuth();
  const [refreshing, setRefreshing] = useState(false);

  // Hooks for data fetching
  const { analytics, loading: analyticsLoading, refreshAnalytics } = useEmailAnalytics();
  const { templates, loading: templatesLoading, refreshTemplates } = useCommunicationTemplates();
  const { branding, loading: brandingLoading, fetchBranding } = useSchoolBranding();

  // Quick action handlers
  const handleCreateTemplate = useCallback(() => {
    router.push('/(school-admin)/communication/templates/new');
  }, []);

  const handleManageTemplates = useCallback(() => {
    router.push('/(school-admin)/communication/templates');
  }, []);

  const handleManageBranding = useCallback(() => {
    router.push('/(school-admin)/communication/branding');
  }, []);

  const handleViewAnalytics = useCallback(() => {
    router.push('/(school-admin)/communication/analytics');
  }, []);

  const handleCommunicationSettings = useCallback(() => {
    router.push('/(school-admin)/communication/settings');
  }, []);

  const handleRefreshAll = useCallback(async () => {
    setRefreshing(true);
    try {
      await Promise.all([refreshAnalytics(), refreshTemplates(), fetchBranding()]);
    } catch (error) {
      console.error('Error refreshing data:', error);
    } finally {
      setRefreshing(false);
    }
  }, [refreshAnalytics, refreshTemplates, fetchBranding]);

  // Loading state
  const isLoading = analyticsLoading || templatesLoading || brandingLoading;

  // Welcome message
  const welcomeMessage = React.useMemo(() => {
    const name = userProfile?.name?.split(' ')[0] || 'Admin';
    const currentHour = new Date().getHours();

    if (currentHour < 12) {
      return `Good morning, ${name}!`;
    } else if (currentHour < 18) {
      return `Good afternoon, ${name}!`;
    } else {
      return `Good evening, ${name}!`;
    }
  }, [userProfile]);

  return (
    <ScrollView
      showsVerticalScrollIndicator={false}
      contentContainerStyle={{
        paddingBottom: isWeb ? 0 : 100,
        flexGrow: 1,
      }}
      className="flex-1 bg-gray-50"
    >
      <VStack className="p-6" space="lg">
        {/* Header Section */}
        <VStack space="sm">
          <HStack className="justify-between items-start">
            <VStack space="xs" className="flex-1">
              <Heading size="xl" className="text-gray-900">
                {welcomeMessage}
              </Heading>
              <Text className="text-gray-600">
                Manage your school's teacher communication system
              </Text>
            </VStack>

            <Button
              onPress={handleRefreshAll}
              disabled={refreshing}
              variant="outline"
              className="px-3 py-2"
            >
              <Icon
                as={refreshing ? TrendingUpIcon : BarChart3Icon}
                size="sm"
                className={`text-gray-600 ${refreshing ? 'animate-spin' : ''}`}
              />
            </Button>
          </HStack>

          {/* Date */}
          <Text className="text-sm text-gray-500">
            {new Date().toLocaleDateString('en-US', {
              weekday: 'long',
              day: '2-digit',
              month: 'long',
              year: 'numeric',
            })}
          </Text>
        </VStack>

        {/* Quick Stats Overview */}
        {analytics && !isLoading && (
          <Box className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl p-6 shadow-lg">
            <VStack space="md">
              <Text className="text-white font-semibold text-lg">Communication Overview</Text>
              <HStack space="lg" className="flex-wrap">
                <VStack className="items-center">
                  <Text className="text-2xl font-bold text-white">{analytics.total_sent}</Text>
                  <Text className="text-blue-100 text-sm">Emails Sent</Text>
                </VStack>
                <VStack className="items-center">
                  <Text className="text-2xl font-bold text-white">
                    {Math.round(analytics.delivery_rate * 100)}%
                  </Text>
                  <Text className="text-blue-100 text-sm">Delivery Rate</Text>
                </VStack>
                <VStack className="items-center">
                  <Text className="text-2xl font-bold text-white">
                    {Math.round(analytics.open_rate * 100)}%
                  </Text>
                  <Text className="text-blue-100 text-sm">Open Rate</Text>
                </VStack>
                <VStack className="items-center">
                  <Text className="text-2xl font-bold text-white">{templates.length}</Text>
                  <Text className="text-blue-100 text-sm">Templates</Text>
                </VStack>
              </HStack>
            </VStack>
          </Box>
        )}

        {/* Quick Actions Panel */}
        <Card className="p-6">
          <VStack space="md">
            <Heading size="md" className="text-gray-900">
              Quick Actions
            </Heading>

            <VStack space="sm" className={isWeb ? 'lg:grid lg:grid-cols-2 lg:gap-4' : ''}>
              {/* Create New Template */}
              <Pressable
                onPress={handleCreateTemplate}
                className="flex-row items-center p-4 bg-blue-50 border border-blue-200 rounded-lg hover:bg-blue-100 active:bg-blue-100"
              >
                <Box className="mr-4 p-2 bg-blue-500 rounded-full">
                  <Icon as={PlusIcon} size="sm" className="text-white" />
                </Box>
                <VStack className="flex-1">
                  <Text className="font-semibold text-gray-900">Create New Template</Text>
                  <Text className="text-sm text-gray-600">
                    Design custom email templates with your school branding
                  </Text>
                </VStack>
              </Pressable>

              {/* Manage Templates */}
              <Pressable
                onPress={handleManageTemplates}
                className="flex-row items-center p-4 bg-green-50 border border-green-200 rounded-lg hover:bg-green-100 active:bg-green-100"
              >
                <Box className="mr-4 p-2 bg-green-500 rounded-full">
                  <Icon as={TemplateIcon} size="sm" className="text-white" />
                </Box>
                <VStack className="flex-1">
                  <Text className="font-semibold text-gray-900">Manage Templates</Text>
                  <Text className="text-sm text-gray-600">
                    Edit, duplicate, or organize your email templates
                  </Text>
                </VStack>
              </Pressable>

              {/* School Branding */}
              <Pressable
                onPress={handleManageBranding}
                className="flex-row items-center p-4 bg-purple-50 border border-purple-200 rounded-lg hover:bg-purple-100 active:bg-purple-100"
              >
                <Box className="mr-4 p-2 bg-purple-500 rounded-full">
                  <Icon as={PaletteIcon} size="sm" className="text-white" />
                </Box>
                <VStack className="flex-1">
                  <Text className="font-semibold text-gray-900">School Branding</Text>
                  <Text className="text-sm text-gray-600">
                    Customize colors, logo, and messaging for your emails
                  </Text>
                </VStack>
              </Pressable>

              {/* Analytics Dashboard */}
              <Pressable
                onPress={handleViewAnalytics}
                className="flex-row items-center p-4 bg-orange-50 border border-orange-200 rounded-lg hover:bg-orange-100 active:bg-orange-100"
              >
                <Box className="mr-4 p-2 bg-orange-500 rounded-full">
                  <Icon as={BarChart3Icon} size="sm" className="text-white" />
                </Box>
                <VStack className="flex-1">
                  <Text className="font-semibold text-gray-900">View Analytics</Text>
                  <Text className="text-sm text-gray-600">
                    Track email performance and engagement metrics
                  </Text>
                </VStack>
              </Pressable>
            </VStack>
          </VStack>
        </Card>

        {/* Main Dashboard Content */}
        <VStack space="lg" className={isWeb ? 'lg:grid lg:grid-cols-2 lg:gap-6' : ''}>
          {/* Recent Templates */}
          <Card className="p-6">
            <VStack space="md">
              <HStack className="justify-between items-center">
                <Heading size="md" className="text-gray-900">
                  Recent Templates
                </Heading>
                <Button onPress={handleManageTemplates} variant="link" size="sm">
                  <ButtonText>View All</ButtonText>
                </Button>
              </HStack>

              {templatesLoading ? (
                <Center className="py-8">
                  <Text className="text-gray-500">Loading templates...</Text>
                </Center>
              ) : templates.length > 0 ? (
                <VStack space="sm">
                  {templates.slice(0, 3).map(template => (
                    <Pressable
                      key={template.id}
                      onPress={() =>
                        router.push(`/(school-admin)/communication/templates/${template.id}`)
                      }
                      className="flex-row items-center p-3 bg-gray-50 rounded-lg hover:bg-gray-100 active:bg-gray-100"
                    >
                      <Box className="mr-3 p-2 bg-blue-100 rounded-full">
                        <Icon as={MailIcon} size="xs" className="text-blue-600" />
                      </Box>
                      <VStack className="flex-1">
                        <Text className="font-medium text-gray-900">{template.name}</Text>
                        <Text className="text-xs text-gray-500">
                          {template.template_type
                            .replace('_', ' ')
                            .replace(/\b\w/g, l => l.toUpperCase())}{' '}
                          •{template.is_active ? ' Active' : ' Inactive'}
                        </Text>
                      </VStack>
                    </Pressable>
                  ))}
                </VStack>
              ) : (
                <Center className="py-8">
                  <VStack space="sm" className="items-center">
                    <Icon as={TemplateIcon} size="lg" className="text-gray-400" />
                    <Text className="text-gray-500 text-center">No templates created yet</Text>
                    <Button onPress={handleCreateTemplate} size="sm">
                      <ButtonText>Create First Template</ButtonText>
                    </Button>
                  </VStack>
                </Center>
              )}
            </VStack>
          </Card>

          {/* Communication Stats */}
          <Card className="p-6">
            <VStack space="md">
              <HStack className="justify-between items-center">
                <Heading size="md" className="text-gray-900">
                  Performance Stats
                </Heading>
                <Button onPress={handleViewAnalytics} variant="link" size="sm">
                  <ButtonText>View Details</ButtonText>
                </Button>
              </HStack>

              {analyticsLoading ? (
                <Center className="py-8">
                  <Text className="text-gray-500">Loading analytics...</Text>
                </Center>
              ) : analytics ? (
                <VStack space="md">
                  {/* Delivery Rate */}
                  <HStack className="justify-between items-center">
                    <HStack space="sm" className="items-center">
                      <Icon as={SendIcon} size="sm" className="text-green-600" />
                      <Text className="text-gray-700">Delivery Rate</Text>
                    </HStack>
                    <Text
                      className={`font-semibold ${
                        analytics.delivery_rate >= 0.95
                          ? 'text-green-600'
                          : analytics.delivery_rate >= 0.85
                          ? 'text-yellow-600'
                          : 'text-red-600'
                      }`}
                    >
                      {Math.round(analytics.delivery_rate * 100)}%
                    </Text>
                  </HStack>

                  {/* Open Rate */}
                  <HStack className="justify-between items-center">
                    <HStack space="sm" className="items-center">
                      <Icon as={MailIcon} size="sm" className="text-blue-600" />
                      <Text className="text-gray-700">Open Rate</Text>
                    </HStack>
                    <Text
                      className={`font-semibold ${
                        analytics.open_rate >= 0.25
                          ? 'text-green-600'
                          : analytics.open_rate >= 0.15
                          ? 'text-yellow-600'
                          : 'text-red-600'
                      }`}
                    >
                      {Math.round(analytics.open_rate * 100)}%
                    </Text>
                  </HStack>

                  {/* Click Rate */}
                  <HStack className="justify-between items-center">
                    <HStack space="sm" className="items-center">
                      <Icon as={TrendingUpIcon} size="sm" className="text-purple-600" />
                      <Text className="text-gray-700">Click Rate</Text>
                    </HStack>
                    <Text
                      className={`font-semibold ${
                        analytics.click_rate >= 0.05
                          ? 'text-green-600'
                          : analytics.click_rate >= 0.02
                          ? 'text-yellow-600'
                          : 'text-red-600'
                      }`}
                    >
                      {Math.round(analytics.click_rate * 100)}%
                    </Text>
                  </HStack>

                  {/* Total Communications */}
                  <HStack className="justify-between items-center">
                    <HStack space="sm" className="items-center">
                      <Icon as={UsersIcon} size="sm" className="text-gray-600" />
                      <Text className="text-gray-700">Total Sent</Text>
                    </HStack>
                    <Text className="font-semibold text-gray-900">
                      {analytics.total_sent.toLocaleString()}
                    </Text>
                  </HStack>
                </VStack>
              ) : (
                <Center className="py-8">
                  <VStack space="sm" className="items-center">
                    <Icon as={BarChart3Icon} size="lg" className="text-gray-400" />
                    <Text className="text-gray-500 text-center">No data available yet</Text>
                    <Text className="text-xs text-gray-400 text-center">
                      Start sending emails to see performance metrics
                    </Text>
                  </VStack>
                </Center>
              )}
            </VStack>
          </Card>
        </VStack>

        {/* Settings and Help */}
        <Card className="p-6">
          <VStack space="md">
            <Heading size="md" className="text-gray-900">
              Settings & Support
            </Heading>

            <HStack space="md" className="flex-wrap">
              <Button
                onPress={handleCommunicationSettings}
                variant="outline"
                className="flex-1 min-w-0"
              >
                <HStack space="xs" className="items-center">
                  <Icon as={SettingsIcon} size="xs" className="text-gray-600" />
                  <ButtonText>Settings</ButtonText>
                </HStack>
              </Button>

              <Button
                onPress={() => router.push('/(school-admin)/communication/help')}
                variant="outline"
                className="flex-1 min-w-0"
              >
                <ButtonText>Help & Guides</ButtonText>
              </Button>
            </HStack>
          </VStack>
        </Card>

        {/* Getting Started Guide for New Users */}
        {(!analytics || analytics.total_sent === 0) && (
          <Box className="bg-gradient-to-r from-green-50 to-blue-50 border-2 border-dashed border-green-200 rounded-xl p-8 text-center">
            <VStack space="md" className="items-center">
              <Text className="text-xl font-bold text-gray-900">
                Welcome to Teacher Communications! 🎉
              </Text>
              <Text className="text-gray-600 max-w-md">
                Get started by creating your first email template and customizing your school's
                branding. This will help you maintain consistent, professional communication with
                your teachers.
              </Text>
              <HStack space="md" className="flex-wrap justify-center">
                <Button onPress={handleCreateTemplate} variant="solid">
                  <ButtonText>Create Template</ButtonText>
                </Button>
                <Button onPress={handleManageBranding} variant="outline">
                  <ButtonText>Setup Branding</ButtonText>
                </Button>
              </HStack>
            </VStack>
          </Box>
        )}
      </VStack>
    </ScrollView>
  );
};

// Export wrapped with MainLayout
const CommunicationDashboardPage = () => {
  return (
    <MainLayout _title="Communication Dashboard">
      <CommunicationDashboard />
    </MainLayout>
  );
};

export default CommunicationDashboardPage;
