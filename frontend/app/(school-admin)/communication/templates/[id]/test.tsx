import { isWeb } from '@gluestack-ui/nativewind-utils/IsWeb';
import { router, useLocalSearchParams } from 'expo-router';
import {
  ArrowLeftIcon,
  SendIcon,
  MailIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  AlertTriangleIcon,
} from 'lucide-react-native';
import React, { useState, useCallback, useEffect } from 'react';
import { Alert } from 'react-native';

import { SchoolEmailTemplate } from '@/api/communicationApi';
import MainLayout from '@/components/layouts/MainLayout';
import { Badge } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Center } from '@/components/ui/center';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Input, InputField } from '@/components/ui/input';
import { ScrollView } from '@/components/ui/scroll-view';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { Textarea, TextareaInput } from '@/components/ui/textarea';
import { VStack } from '@/components/ui/vstack';
import { useTemplateEditor, useTemplatePreview } from '@/hooks/useCommunicationTemplates';

interface TestEmailHistory {
  id: string;
  email: string;
  sent_at: string;
  status: 'sending' | 'sent' | 'delivered' | 'failed';
  error_message?: string;
}

const TestEmailPage = () => {
  const { id } = useLocalSearchParams<{ id: string }>();
  const templateId = parseInt(id as string, 10);

  // State
  const [testEmail, setTestEmail] = useState('');
  const [customVariables, setCustomVariables] = useState<Record<string, string>>({
    teacher_name: 'Test Teacher',
    school_name: 'Test School',
    invitation_link: 'https://aprendecomigo.com/test',
    deadline: '2025-12-31',
    contact_email: 'test@school.com',
  });
  const [testHistory, setTestHistory] = useState<TestEmailHistory[]>([]);
  const [emailValidation, setEmailValidation] = useState<{
    isValid: boolean;
    message?: string;
  }>({ isValid: false });

  // Hooks
  const {
    currentTemplate,
    loading: templateLoading,
    error: templateError,
    loadTemplate,
  } = useTemplateEditor();

  const { sendTestEmail, loading: sendingEmail, error: sendError } = useTemplatePreview();

  // Load template on mount
  useEffect(() => {
    if (templateId) {
      loadTemplate(templateId);
    }
  }, [templateId, loadTemplate]);

  // Email validation
  useEffect(() => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const isValid = emailRegex.test(testEmail);

    setEmailValidation({
      isValid,
      message: testEmail && !isValid ? 'Please enter a valid email address' : undefined,
    });
  }, [testEmail]);

  // Template type info
  const templateTypeOptions = [
    { value: 'invitation', label: 'Teacher Invitation', color: 'bg-blue-100 text-blue-800' },
    { value: 'reminder', label: 'Reminder', color: 'bg-yellow-100 text-yellow-800' },
    { value: 'welcome', label: 'Welcome', color: 'bg-green-100 text-green-800' },
    {
      value: 'profile_reminder',
      label: 'Profile Reminder',
      color: 'bg-orange-100 text-orange-800',
    },
    {
      value: 'completion_celebration',
      label: 'Completion Celebration',
      color: 'bg-purple-100 text-purple-800',
    },
    { value: 'ongoing_support', label: 'Ongoing Support', color: 'bg-gray-100 text-gray-800' },
  ];

  const currentTemplateType = templateTypeOptions.find(
    option => option.value === currentTemplate?.template_type,
  );

  // Send test email
  const handleSendTestEmail = useCallback(async () => {
    if (!currentTemplate || !emailValidation.isValid) return;

    try {
      // Add to history immediately with sending status
      const testId = Date.now().toString();
      const newTest: TestEmailHistory = {
        id: testId,
        email: testEmail,
        sent_at: new Date().toISOString(),
        status: 'sending',
      };
      setTestHistory(prev => [newTest, ...prev]);

      // Send the email
      const result = await sendTestEmail(templateId, testEmail);

      // Update the status
      setTestHistory(prev =>
        prev.map(test =>
          test.id === testId
            ? { ...test, status: result.success ? 'sent' : 'failed', error_message: result.message }
            : test,
        ),
      );

      // Show success message
      if (result.success) {
        Alert.alert(
          'Test Email Sent',
          `A test email has been sent to ${testEmail}. Check your inbox to see how the template looks.`,
          [{ text: 'OK' }],
        );
      }

      // Clear the email input
      setTestEmail('');
    } catch (err: any) {
      // Update the failed test in history
      setTestHistory(prev =>
        prev.map(test =>
          test.email === testEmail && test.status === 'sending'
            ? { ...test, status: 'failed', error_message: err.message }
            : test,
        ),
      );
      if (__DEV__) {
        console.error('Error sending test email:', err); // TODO: Review for sensitive data // TODO: Review for sensitive data // TODO: Review for sensitive data
      }
    }
  }, [currentTemplate, emailValidation.isValid, testEmail, templateId, sendTestEmail]);

  // Update custom variable
  const updateCustomVariable = useCallback((key: string, value: string) => {
    setCustomVariables(prev => ({
      ...prev,
      [key]: value,
    }));
  }, []);

  // Get status icon and color
  const getStatusInfo = useCallback((status: TestEmailHistory['status']) => {
    switch (status) {
      case 'sending':
        return { icon: ClockIcon, color: 'text-yellow-600', bg: 'bg-yellow-100' };
      case 'sent':
      case 'delivered':
        return { icon: CheckCircleIcon, color: 'text-green-600', bg: 'bg-green-100' };
      case 'failed':
        return { icon: XCircleIcon, color: 'text-red-600', bg: 'bg-red-100' };
      default:
        return { icon: MailIcon, color: 'text-gray-600', bg: 'bg-gray-100' };
    }
  }, []);

  // Loading state
  if (templateLoading) {
    return (
      <MainLayout _title="Test Email">
        <Center className="flex-1">
          <VStack space="md" className="items-center">
            <Spinner size="large" />
            <Text className="text-gray-600">Loading template...</Text>
          </VStack>
        </Center>
      </MainLayout>
    );
  }

  // Error state
  if (templateError && !currentTemplate) {
    return (
      <MainLayout _title="Test Email">
        <Center className="flex-1">
          <VStack space="md" className="items-center max-w-md">
            <Text className="text-red-600 font-semibold text-center">Error Loading Template</Text>
            <Text className="text-gray-600 text-center">{templateError}</Text>
            <HStack space="sm">
              <Button onPress={() => loadTemplate(templateId)} variant="outline">
                <ButtonText>Try Again</ButtonText>
              </Button>
              <Button onPress={() => router.back()}>
                <ButtonText>Go Back</ButtonText>
              </Button>
            </HStack>
          </VStack>
        </Center>
      </MainLayout>
    );
  }

  // No template found
  if (!currentTemplate) {
    return (
      <MainLayout _title="Test Email">
        <Center className="flex-1">
          <VStack space="md" className="items-center max-w-md">
            <Text className="text-gray-600 font-semibold text-center">Template Not Found</Text>
            <Text className="text-gray-500 text-center">
              The template you're looking for doesn't exist or has been deleted.
            </Text>
            <Button onPress={() => router.push('/(school-admin)/communication/templates')}>
              <ButtonText>View All Templates</ButtonText>
            </Button>
          </VStack>
        </Center>
      </MainLayout>
    );
  }

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
        {/* Header */}
        <HStack className="justify-between items-center">
          <HStack space="md" className="items-center flex-1">
            <Button onPress={() => router.back()} variant="outline" size="sm" className="p-2">
              <Icon as={ArrowLeftIcon} size="sm" className="text-gray-600" />
            </Button>

            <VStack space="xs" className="flex-1">
              <HStack space="sm" className="items-center flex-wrap">
                <Heading size="xl" className="text-gray-900">
                  Send Test Email
                </Heading>
                {currentTemplateType && (
                  <Badge className={currentTemplateType.color}>
                    <Text className="text-xs font-medium">{currentTemplateType.label}</Text>
                  </Badge>
                )}
              </HStack>
              <Text className="text-gray-600">{currentTemplate.name}</Text>
            </VStack>
          </HStack>
        </HStack>

        {/* Send Error */}
        {sendError && (
          <Card className="p-4 bg-red-50 border-red-200">
            <HStack space="sm" className="items-start">
              <Icon as={XCircleIcon} size="sm" className="text-red-600 mt-0.5" />
              <VStack space="xs" className="flex-1">
                <Text className="font-medium text-red-800">Error Sending Test Email</Text>
                <Text className="text-sm text-red-600">{sendError}</Text>
              </VStack>
            </HStack>
          </Card>
        )}

        {/* Send Test Email Form */}
        <Card className="p-6">
          <VStack space="lg">
            <VStack space="xs">
              <Heading size="md" className="text-gray-900">
                Send Test Email
              </Heading>
              <Text className="text-gray-600">
                Send a test email to see how your template will look in an actual email client
              </Text>
            </VStack>

            {/* Email Input */}
            <VStack space="sm">
              <Text className="font-medium text-gray-900">Test Email Address</Text>
              <Input>
                <InputField
                  placeholder="your.email@example.com"
                  value={testEmail}
                  onChangeText={setTestEmail}
                  keyboardType="email-address"
                  autoCapitalize="none"
                  autoCorrect={false}
                />
              </Input>
              {emailValidation.message && (
                <Text className="text-sm text-red-600">{emailValidation.message}</Text>
              )}
              <Text className="text-xs text-gray-500">
                Enter the email address where you want to receive the test email
              </Text>
            </VStack>

            {/* Custom Variables */}
            <VStack space="md">
              <Text className="font-medium text-gray-900">Test Data</Text>
              <Text className="text-sm text-gray-600">
                Customize the data used in the test email to see different scenarios
              </Text>

              <VStack space="sm">
                {Object.entries(customVariables).map(([key, value]) => (
                  <VStack key={key} space="xs">
                    <Text className="text-sm font-medium text-gray-700">
                      {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </Text>
                    <Input>
                      <InputField
                        placeholder={`Enter ${key.replace(/_/g, ' ')}`}
                        value={value}
                        onChangeText={text => updateCustomVariable(key, text)}
                      />
                    </Input>
                  </VStack>
                ))}
              </VStack>

              <Button
                onPress={() => {
                  setCustomVariables({
                    teacher_name: 'Test Teacher',
                    school_name: 'Test School',
                    invitation_link: 'https://aprendecomigo.com/test',
                    deadline: '2025-12-31',
                    contact_email: 'test@school.com',
                  });
                }}
                variant="outline"
                size="sm"
                className="self-start"
              >
                <ButtonText>Reset to Defaults</ButtonText>
              </Button>
            </VStack>

            {/* Send Button */}
            <VStack space="sm">
              <Button
                onPress={handleSendTestEmail}
                disabled={!emailValidation.isValid || sendingEmail}
                className="bg-blue-600"
              >
                <HStack space="xs" className="items-center">
                  <Icon as={SendIcon} size="sm" className="text-white" />
                  <ButtonText className="text-white">
                    {sendingEmail ? 'Sending...' : 'Send Test Email'}
                  </ButtonText>
                </HStack>
              </Button>

              <Text className="text-xs text-gray-500 text-center">
                The test email will be sent using your current school branding and the data above
              </Text>
            </VStack>
          </VStack>
        </Card>

        {/* Important Notes */}
        <Card className="p-6 bg-blue-50 border-blue-200">
          <VStack space="md">
            <HStack space="sm" className="items-start">
              <Icon as={AlertTriangleIcon} size="sm" className="text-blue-600 mt-0.5" />
              <VStack space="xs" className="flex-1">
                <Text className="font-medium text-blue-800">Important Notes</Text>
                <VStack space="xs">
                  <Text className="text-sm text-blue-700">
                    • Test emails are sent immediately and don't follow any sequence timing
                  </Text>
                  <Text className="text-sm text-blue-700">
                    • Check your spam folder if you don't receive the email within a few minutes
                  </Text>
                  <Text className="text-sm text-blue-700">
                    • Test emails include all tracking pixels and links for accurate testing
                  </Text>
                  <Text className="text-sm text-blue-700">
                    • Template must be active to send test emails successfully
                  </Text>
                </VStack>
              </VStack>
            </HStack>
          </VStack>
        </Card>

        {/* Test History */}
        {testHistory.length > 0 && (
          <Card className="p-6">
            <VStack space="lg">
              <VStack space="xs">
                <Heading size="md" className="text-gray-900">
                  Test Email History
                </Heading>
                <Text className="text-gray-600">Recent test emails sent for this template</Text>
              </VStack>

              <VStack space="md">
                {testHistory.map(test => {
                  const statusInfo = getStatusInfo(test.status);
                  return (
                    <Card key={test.id} className="p-4 bg-gray-50">
                      <HStack className="justify-between items-start">
                        <VStack space="xs" className="flex-1">
                          <HStack space="sm" className="items-center">
                            <Badge className={`${statusInfo.bg} ${statusInfo.color}`}>
                              <HStack space="xs" className="items-center">
                                <Icon as={statusInfo.icon} size="xs" />
                                <Text className="text-xs font-medium capitalize">
                                  {test.status}
                                </Text>
                              </HStack>
                            </Badge>
                            <Text className="font-medium text-gray-900">{test.email}</Text>
                          </HStack>

                          <Text className="text-sm text-gray-600">
                            {new Date(test.sent_at).toLocaleString()}
                          </Text>

                          {test.error_message && (
                            <Text className="text-sm text-red-600">
                              Error: {test.error_message}
                            </Text>
                          )}
                        </VStack>

                        {test.status === 'sending' && <Spinner size="small" />}
                      </HStack>
                    </Card>
                  );
                })}
              </VStack>

              {testHistory.length > 5 && (
                <Button
                  onPress={() => setTestHistory(prev => prev.slice(0, 5))}
                  variant="outline"
                  size="sm"
                  className="self-center"
                >
                  <ButtonText>Show Less</ButtonText>
                </Button>
              )}
            </VStack>
          </Card>
        )}

        {/* Actions */}
        <Card className="p-6">
          <VStack space="md">
            <Text className="font-medium text-gray-900">Next Steps</Text>

            <HStack space="sm" className="flex-wrap">
              <Button
                onPress={() =>
                  router.push(`/(school-admin)/communication/templates/${templateId}/preview`)
                }
                variant="outline"
                className="flex-1"
              >
                <ButtonText>View Preview</ButtonText>
              </Button>

              <Button
                onPress={() =>
                  router.push(`/(school-admin)/communication/templates/${templateId}/edit`)
                }
                variant="outline"
                className="flex-1"
              >
                <ButtonText>Edit Template</ButtonText>
              </Button>

              <Button
                onPress={() => router.push('/(school-admin)/communication/templates')}
                variant="outline"
                className="flex-1"
              >
                <ButtonText>All Templates</ButtonText>
              </Button>
            </HStack>

            <Text className="text-xs text-gray-500 text-center">
              Once you're satisfied with the template, you can activate it for use in email
              sequences
            </Text>
          </VStack>
        </Card>
      </VStack>
    </ScrollView>
  );
};

const TestEmailPageWrapper = () => {
  return (
    <MainLayout _title="Send Test Email">
      <TestEmailPage />
    </MainLayout>
  );
};

export default TestEmailPageWrapper;
