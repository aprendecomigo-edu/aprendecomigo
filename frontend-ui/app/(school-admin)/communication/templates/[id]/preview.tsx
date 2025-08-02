import { isWeb } from '@gluestack-ui/nativewind-utils/IsWeb';
import { router, useLocalSearchParams } from 'expo-router';
import {
  ArrowLeftIcon,
  EyeIcon,
  SendIcon,
  EditIcon,
  SmartphoneIcon,
  MonitorIcon,
  TabletIcon,
  RefreshCwIcon,
} from 'lucide-react-native';
import React, { useState, useCallback, useEffect } from 'react';
import { Alert } from 'react-native';

import { SchoolEmailTemplate } from '@/api/communicationApi';
import MainLayout from '@/components/layouts/main-layout';
import { Badge } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Center } from '@/components/ui/center';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Pressable } from '@/components/ui/pressable';
import { ScrollView } from '@/components/ui/scroll-view';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { useTemplateEditor, useTemplatePreview } from '@/hooks/useCommunicationTemplates';
import { useSchoolBranding } from '@/hooks/useSchoolBranding';

type PreviewMode = 'desktop' | 'tablet' | 'mobile';

const TemplatePreviewPage = () => {
  const { id } = useLocalSearchParams<{ id: string }>();
  const templateId = parseInt(id as string, 10);

  // State
  const [previewMode, setPreviewMode] = useState<PreviewMode>('desktop');
  const [contextVariables, setContextVariables] = useState<Record<string, any>>({
    teacher_name: 'John Smith',
    school_name: 'Example School',
    invitation_link: 'https://aprendecomigo.com/accept/abc123',
    deadline: '2025-08-15',
    contact_email: 'admin@example.com',
    school_address: '123 Education St, Learning City',
  });

  // Hooks
  const {
    currentTemplate,
    loading: templateLoading,
    error: templateError,
    loadTemplate,
  } = useTemplateEditor();

  const { 
    preview,
    loading: previewLoading,
    error: previewError,
    generatePreview,
    sendTestEmail,
  } = useTemplatePreview();

  const { branding } = useSchoolBranding();

  // Load template on mount
  useEffect(() => {
    if (templateId) {
      loadTemplate(templateId);
    }
  }, [templateId, loadTemplate]);

  // Generate preview when template or context changes
  useEffect(() => {
    if (currentTemplate) {
      generatePreview({
        template_id: currentTemplate.id,
        context_variables: contextVariables,
      });
    }
  }, [currentTemplate, contextVariables, generatePreview]);

  // Preview dimensions for different modes
  const getPreviewDimensions = useCallback(() => {
    switch (previewMode) {
      case 'mobile':
        return { width: '375px', height: '667px' };
      case 'tablet':
        return { width: '768px', height: '1024px' };
      case 'desktop':
      default:
        return { width: '100%', height: 'auto' };
    }
  }, [previewMode]);

  // Template type info
  const templateTypeOptions = [
    { value: 'invitation', label: 'Teacher Invitation', color: 'bg-blue-100 text-blue-800' },
    { value: 'reminder', label: 'Reminder', color: 'bg-yellow-100 text-yellow-800' },
    { value: 'welcome', label: 'Welcome', color: 'bg-green-100 text-green-800' },
    { value: 'profile_reminder', label: 'Profile Reminder', color: 'bg-orange-100 text-orange-800' },
    { value: 'completion_celebration', label: 'Completion Celebration', color: 'bg-purple-100 text-purple-800' },
    { value: 'ongoing_support', label: 'Ongoing Support', color: 'bg-gray-100 text-gray-800' },
  ];

  const currentTemplateType = templateTypeOptions.find(
    option => option.value === currentTemplate?.template_type
  );

  // Handle test email
  const handleSendTestEmail = useCallback(() => {
    if (!currentTemplate) return;
    router.push(`/(school-admin)/communication/templates/${templateId}/test`);
  }, [currentTemplate, templateId]);

  // Handle edit template
  const handleEditTemplate = useCallback(() => {
    if (!currentTemplate) return;
    router.push(`/(school-admin)/communication/templates/${templateId}/edit`);
  }, [currentTemplate, templateId]);

  // Refresh preview
  const handleRefreshPreview = useCallback(() => {
    if (currentTemplate) {
      generatePreview({
        template_id: currentTemplate.id,
        context_variables: contextVariables,
      });
    }
  }, [currentTemplate, contextVariables, generatePreview]);

  // Update context variable
  const updateContextVariable = useCallback((key: string, value: string) => {
    setContextVariables(prev => ({
      ...prev,
      [key]: value,
    }));
  }, []);

  // Loading state
  if (templateLoading) {
    return (
      <MainLayout _title="Preview Template">
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
      <MainLayout _title="Preview Template">
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
      <MainLayout _title="Preview Template">
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
            <Button
              onPress={() => router.back()}
              variant="outline"
              size="sm"
              className="p-2"
            >
              <Icon as={ArrowLeftIcon} size="sm" className="text-gray-600" />
            </Button>

            <VStack space="xs" className="flex-1">
              <HStack space="sm" className="items-center flex-wrap">
                <Heading size="xl" className="text-gray-900">
                  Preview Template
                </Heading>
                {currentTemplateType && (
                  <Badge className={currentTemplateType.color}>
                    <Text className="text-xs font-medium">
                      {currentTemplateType.label}
                    </Text>
                  </Badge>
                )}
                <Badge
                  className={
                    currentTemplate.is_active
                      ? 'bg-green-100 text-green-800'
                      : 'bg-gray-100 text-gray-800'
                  }
                >
                  <Text className="text-xs font-medium">
                    {currentTemplate.is_active ? 'Active' : 'Inactive'}
                  </Text>
                </Badge>
              </HStack>
              <Text className="text-gray-600">{currentTemplate.name}</Text>
            </VStack>
          </HStack>

          <HStack space="sm" className="flex-wrap">
            <Button
              onPress={handleRefreshPreview}
              variant="outline"
              size="sm"
              disabled={previewLoading}
            >
              <HStack space="xs" className="items-center">
                <Icon 
                  as={RefreshCwIcon} 
                  size="sm" 
                  className={`text-gray-600 ${previewLoading ? 'animate-spin' : ''}`} 
                />
                <ButtonText>Refresh</ButtonText>
              </HStack>
            </Button>

            <Button
              onPress={handleSendTestEmail}
              variant="outline"
              size="sm"
            >
              <HStack space="xs" className="items-center">
                <Icon as={SendIcon} size="sm" className="text-gray-600" />
                <ButtonText>Send Test</ButtonText>
              </HStack>
            </Button>

            <Button
              onPress={handleEditTemplate}
              className="bg-blue-600"
            >
              <HStack space="xs" className="items-center">
                <Icon as={EditIcon} size="sm" className="text-white" />
                <ButtonText className="text-white">Edit</ButtonText>
              </HStack>
            </Button>
          </HStack>
        </HStack>

        {/* Preview Mode Selector */}
        <Card className="p-4">
          <VStack space="md">
            <Text className="font-medium text-gray-900">Preview Mode</Text>
            
            <HStack space="sm" className="items-center">
              <Pressable
                onPress={() => setPreviewMode('desktop')}
                className={`flex-row items-center p-3 rounded-lg border-2 ${
                  previewMode === 'desktop'
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:bg-gray-50'
                }`}
              >
                <Icon
                  as={MonitorIcon}
                  size="sm"
                  className={previewMode === 'desktop' ? 'text-blue-600' : 'text-gray-600'}
                />
                <Text
                  className={`ml-2 text-sm font-medium ${
                    previewMode === 'desktop' ? 'text-blue-600' : 'text-gray-600'
                  }`}
                >
                  Desktop
                </Text>
              </Pressable>

              <Pressable
                onPress={() => setPreviewMode('tablet')}
                className={`flex-row items-center p-3 rounded-lg border-2 ${
                  previewMode === 'tablet'
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:bg-gray-50'
                }`}
              >
                <Icon
                  as={TabletIcon}
                  size="sm"
                  className={previewMode === 'tablet' ? 'text-blue-600' : 'text-gray-600'}
                />
                <Text
                  className={`ml-2 text-sm font-medium ${
                    previewMode === 'tablet' ? 'text-blue-600' : 'text-gray-600'
                  }`}
                >
                  Tablet
                </Text>
              </Pressable>

              <Pressable
                onPress={() => setPreviewMode('mobile')}
                className={`flex-row items-center p-3 rounded-lg border-2 ${
                  previewMode === 'mobile'
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:bg-gray-50'
                }`}
              >
                <Icon
                  as={SmartphoneIcon}
                  size="sm"
                  className={previewMode === 'mobile' ? 'text-blue-600' : 'text-gray-600'}
                />
                <Text
                  className={`ml-2 text-sm font-medium ${
                    previewMode === 'mobile' ? 'text-blue-600' : 'text-gray-600'
                  }`}
                >
                  Mobile
                </Text>
              </Pressable>
            </HStack>
          </VStack>
        </Card>

        <HStack space="lg" className={isWeb ? 'lg:flex-row' : 'flex-col'}>
          {/* Context Variables Panel */}
          <Card className={`p-6 ${isWeb ? 'lg:w-1/3' : 'w-full'}`}>
            <VStack space="lg">
              <Heading size="md" className="text-gray-900">Preview Context</Heading>
              <Text className="text-sm text-gray-600">
                Adjust these values to see how your template will look with different data
              </Text>

              <VStack space="md">
                {Object.entries(contextVariables).map(([key, value]) => (
                  <VStack key={key} space="xs">
                    <Text className="text-sm font-medium text-gray-900">
                      {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </Text>
                    <Box className="bg-gray-100 rounded-lg p-3">
                      <Text className="text-sm text-gray-700" style={{ fontFamily: 'monospace' }}>
                        {'{{' + key + '}}'}
                      </Text>
                    </Box>
                    <Text
                      className="text-sm text-blue-600"
                      onPress={() => {
                        Alert.prompt(
                          'Update Variable',
                          `Enter new value for ${key}:`,
                          [
                            { text: 'Cancel', style: 'cancel' },
                            {
                              text: 'Update',
                              onPress: (newValue) => {
                                if (newValue !== undefined) {
                                  updateContextVariable(key, newValue);
                                }
                              },
                            },
                          ],
                          'plain-text',
                          value.toString()
                        );
                      }}
                    >
                      Current: {value.toString()}
                    </Text>
                  </VStack>
                ))}
              </VStack>

              <Button
                onPress={() => {
                  setContextVariables({
                    teacher_name: 'John Smith',
                    school_name: 'Example School',
                    invitation_link: 'https://aprendecomigo.com/accept/abc123',
                    deadline: '2025-08-15',
                    contact_email: 'admin@example.com',
                    school_address: '123 Education St, Learning City',
                  });
                }}
                variant="outline"
                size="sm"
              >
                <ButtonText>Reset to Defaults</ButtonText>
              </Button>
            </VStack>
          </Card>

          {/* Preview Panel */}
          <Card className={`p-6 ${isWeb ? 'lg:w-2/3' : 'w-full'}`}>
            <VStack space="lg">
              <HStack className="justify-between items-center">
                <Heading size="md" className="text-gray-900">Email Preview</Heading>
                <HStack space="sm" className="items-center">
                  {previewLoading && <Spinner size="small" />}
                  <Text className="text-sm text-gray-500">
                    {previewMode.charAt(0).toUpperCase() + previewMode.slice(1)} View
                  </Text>
                </HStack>
              </HStack>

              {previewError && (
                <Card className="p-4 bg-red-50 border-red-200">
                  <Text className="text-red-600 text-sm">{previewError}</Text>
                </Card>
              )}

              {preview ? (
                <VStack space="md">
                  {/* Subject Preview */}
                  <Card className="p-4 bg-gray-50">
                    <VStack space="xs">
                      <Text className="text-xs font-medium text-gray-600 uppercase">Subject Line</Text>
                      <Text className="font-medium text-gray-900">{preview.subject}</Text>
                    </VStack>
                  </Card>

                  {/* Email Content Preview */}
                  <VStack space="sm">
                    <Text className="text-xs font-medium text-gray-600 uppercase">Email Content</Text>
                    
                    {isWeb ? (
                      <Box
                        className="border border-gray-300 rounded-lg overflow-hidden"
                        style={getPreviewDimensions()}
                      >
                        <div
                          dangerouslySetInnerHTML={{ __html: preview.html_content }}
                          style={{
                            minHeight: previewMode === 'desktop' ? '500px' : getPreviewDimensions().height,
                            padding: '0',
                            margin: '0',
                            fontFamily: 'Arial, sans-serif',
                            lineHeight: '1.6',
                            backgroundColor: '#ffffff',
                          }}
                        />
                      </Box>
                    ) : (
                      <Card className="p-6 bg-white border border-gray-200">
                        <VStack space="sm" className="items-center">
                          <Icon as={EyeIcon} size="xl" className="text-gray-400" />
                          <Text className="text-gray-600 text-center">
                            HTML email preview is only available on web. Use the web version to see the full preview with styling.
                          </Text>
                          <Button onPress={() => router.push(`/(school-admin)/communication/templates/${templateId}/edit`)}>
                            <ButtonText>Edit Template</ButtonText>
                          </Button>
                        </VStack>
                      </Card>
                    )}
                  </VStack>

                  {/* Plain Text Preview */}
                  {preview.text_content && (
                    <VStack space="sm">
                      <Text className="text-xs font-medium text-gray-600 uppercase">Plain Text Version</Text>
                      <Card className="p-4 bg-gray-50">
                        <Text className="text-sm text-gray-800" style={{ fontFamily: 'monospace', whiteSpace: 'pre-wrap' }}>
                          {preview.text_content}
                        </Text>
                      </Card>
                    </VStack>
                  )}

                  {/* Variables Status */}
                  <VStack space="md">
                    {preview.variables_used.length > 0 && (
                      <VStack space="sm">
                        <Text className="text-xs font-medium text-gray-600 uppercase">Variables Used</Text>
                        <HStack space="xs" className="flex-wrap">
                          {preview.variables_used.map((variable) => (
                            <Badge key={variable} className="bg-green-100 text-green-800">
                              <Text className="text-xs">{'{{' + variable + '}}'}</Text>
                            </Badge>
                          ))}
                        </HStack>
                      </VStack>
                    )}

                    {preview.missing_variables.length > 0 && (
                      <VStack space="sm">
                        <Text className="text-xs font-medium text-gray-600 uppercase">Missing Variables</Text>
                        <HStack space="xs" className="flex-wrap">
                          {preview.missing_variables.map((variable) => (
                            <Badge key={variable} className="bg-yellow-100 text-yellow-800">
                              <Text className="text-xs">{'{{' + variable + '}}'}</Text>
                            </Badge>
                          ))}
                        </HStack>
                        <Text className="text-xs text-yellow-700">
                          These variables will appear as placeholders in the actual email
                        </Text>
                      </VStack>
                    )}
                  </VStack>
                </VStack>
              ) : (
                <Card className="p-12 bg-gray-50">
                  <Center>
                    <VStack space="md" className="items-center">
                      <Icon as={EyeIcon} size="xl" className="text-gray-400" />
                      <Text className="text-gray-600 text-center">
                        {previewLoading ? 'Generating preview...' : 'No preview available'}
                      </Text>
                      {!previewLoading && (
                        <Button onPress={handleRefreshPreview} size="sm">
                          <ButtonText>Generate Preview</ButtonText>
                        </Button>
                      )}
                    </VStack>
                  </Center>
                </Card>
              )}
            </VStack>
          </Card>
        </HStack>

        {/* Actions */}
        <Card className="p-6">
          <VStack space="md">
            <Text className="font-medium text-gray-900">Next Steps</Text>
            
            <HStack space="sm" className="flex-wrap">
              <Button
                onPress={handleSendTestEmail}
                className="bg-blue-600 flex-1"
              >
                <HStack space="xs" className="items-center">
                  <Icon as={SendIcon} size="sm" className="text-white" />
                  <ButtonText className="text-white">Send Test Email</ButtonText>
                </HStack>
              </Button>

              <Button
                onPress={handleEditTemplate}
                variant="outline"
                className="flex-1"
              >
                <HStack space="xs" className="items-center">
                  <Icon as={EditIcon} size="sm" className="text-gray-600" />
                  <ButtonText>Edit Template</ButtonText>
                </HStack>
              </Button>
            </HStack>

            <Text className="text-xs text-gray-500 text-center">
              Send a test email to verify the template works correctly before using it in sequences
            </Text>
          </VStack>
        </Card>
      </VStack>
    </ScrollView>
  );
};

const TemplatePreviewPageWrapper = () => {
  return (
    <MainLayout _title="Template Preview">
      <TemplatePreviewPage />
    </MainLayout>
  );
};

export default TemplatePreviewPageWrapper;