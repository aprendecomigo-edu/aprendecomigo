import { isWeb } from '@gluestack-ui/nativewind-utils/IsWeb';
import { router, useLocalSearchParams } from 'expo-router';
import { ArrowLeftIcon, SaveIcon, EyeIcon, SendIcon, TrashIcon, CopyIcon } from 'lucide-react-native';
import React, { useState, useCallback, useEffect } from 'react';
import { Alert } from 'react-native';

import { SchoolEmailTemplate, UpdateTemplateRequest } from '@/api/communicationApi';
import RichTextTemplateEditor from '@/components/communication/RichTextTemplateEditor';
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
import { Switch } from '@/components/ui/switch';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { useTemplateEditor, useTemplatePreview } from '@/hooks/useCommunicationTemplates';

const EditTemplatePage = () => {
  const { id } = useLocalSearchParams<{ id: string }>();
  const templateId = parseInt(id as string, 10);

  // State
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [validation, setValidation] = useState<{
    errors: string[];
    warnings: string[];
    variables_used: string[];
    missing_variables: string[];
  } | null>(null);

  // Hooks
  const {
    currentTemplate,
    loading,
    saving,
    error,
    availableVariables,
    loadTemplate,
    updateTemplate,
    deleteTemplate,
    duplicateTemplate,
    updateTemplateField,
    clearError,
  } = useTemplateEditor();

  const { 
    validateTemplate,
    sendTestEmail,
    loading: validationLoading 
  } = useTemplatePreview();

  // Load template on mount
  useEffect(() => {
    if (templateId) {
      loadTemplate(templateId);
    }
  }, [templateId, loadTemplate]);

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

  // Update template field and mark as changed
  const handleUpdateField = useCallback((field: keyof SchoolEmailTemplate, value: any) => {
    updateTemplateField(field, value);
    setHasUnsavedChanges(true);
    clearError();
  }, [updateTemplateField, clearError]);

  // Validate template content
  const handleValidateTemplate = useCallback(async () => {
    if (!currentTemplate?.subject_template || !currentTemplate?.html_content) {
      Alert.alert('Validation Error', 'Please add subject and content before validating');
      return;
    }

    try {
      const validationResult = await validateTemplate({
        subject_template: currentTemplate.subject_template,
        html_content: currentTemplate.html_content,
        text_content: currentTemplate.text_content || '',
      });

      setValidation(validationResult);
    } catch (err) {
      console.error('Validation error:', err);
    }
  }, [currentTemplate, validateTemplate]);

  // Auto-validate when content changes
  useEffect(() => {
    if (!currentTemplate) return;

    const timer = setTimeout(() => {
      if (currentTemplate.subject_template && currentTemplate.html_content) {
        handleValidateTemplate();
      }
    }, 1000);

    return () => clearTimeout(timer);
  }, [currentTemplate?.subject_template, currentTemplate?.html_content, handleValidateTemplate]);

  // Save template
  const handleSaveTemplate = useCallback(async () => {
    if (!currentTemplate) return;

    // Validation
    if (!currentTemplate.name?.trim()) {
      Alert.alert('Validation Error', 'Please enter a template name');
      return;
    }

    if (!currentTemplate.subject_template?.trim()) {
      Alert.alert('Validation Error', 'Please enter an email subject');
      return;
    }

    if (!currentTemplate.html_content?.trim()) {
      Alert.alert('Validation Error', 'Please enter email content');
      return;
    }

    try {
      const updateData: UpdateTemplateRequest = {
        name: currentTemplate.name,
        subject_template: currentTemplate.subject_template,
        html_content: currentTemplate.html_content,
        text_content: currentTemplate.text_content,
        use_school_branding: currentTemplate.use_school_branding,
        custom_css: currentTemplate.custom_css,
        is_active: currentTemplate.is_active,
      };

      await updateTemplate(templateId, updateData);
      setHasUnsavedChanges(false);
    } catch (err) {
      console.error('Error updating template:', err);
    }
  }, [currentTemplate, templateId, updateTemplate]);

  // Delete template
  const handleDeleteTemplate = useCallback(() => {
    if (!currentTemplate) return;

    Alert.alert(
      'Delete Template',
      `Are you sure you want to delete "${currentTemplate.name}"? This action cannot be undone.`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              await deleteTemplate(templateId);
              router.push('/(school-admin)/communication/templates');
            } catch (err) {
              console.error('Error deleting template:', err);
            }
          },
        },
      ]
    );
  }, [currentTemplate, templateId, deleteTemplate]);

  // Duplicate template
  const handleDuplicateTemplate = useCallback(() => {
    if (!currentTemplate) return;

    Alert.prompt(
      'Duplicate Template',
      'Enter a name for the duplicated template:',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Duplicate',
          onPress: async (newName) => {
            if (!newName?.trim()) {
              Alert.alert('Error', 'Please enter a valid name');
              return;
            }

            try {
              const duplicatedTemplate = await duplicateTemplate(templateId, newName);
              router.push(`/(school-admin)/communication/templates/${duplicatedTemplate.id}/edit`);
            } catch (err) {
              console.error('Error duplicating template:', err);
            }
          },
        },
      ],
      'plain-text',
      `${currentTemplate.name} (Copy)`
    );
  }, [currentTemplate, templateId, duplicateTemplate]);

  // Preview template
  const handlePreviewTemplate = useCallback(() => {
    if (!currentTemplate?.subject_template || !currentTemplate?.html_content) {
      Alert.alert('Preview Error', 'Please add subject and content before previewing');
      return;
    }
    router.push(`/(school-admin)/communication/templates/${templateId}/preview`);
  }, [currentTemplate, templateId]);

  // Send test email
  const handleSendTestEmail = useCallback(() => {
    if (!currentTemplate) return;
    router.push(`/(school-admin)/communication/templates/${templateId}/test`);
  }, [currentTemplate, templateId]);

  // Go back with unsaved changes check
  const handleGoBack = useCallback(() => {
    if (hasUnsavedChanges) {
      Alert.alert(
        'Unsaved Changes',
        'You have unsaved changes. What would you like to do?',
        [
          { text: 'Cancel', style: 'cancel' },
          { 
            text: 'Discard Changes', 
            style: 'destructive',
            onPress: () => router.back() 
          },
          {
            text: 'Save & Exit',
            onPress: async () => {
              try {
                await handleSaveTemplate();
                router.back();
              } catch (err) {
                console.error('Error saving before exit:', err);
              }
            }
          },
        ]
      );
    } else {
      router.back();
    }
  }, [hasUnsavedChanges, handleSaveTemplate]);

  // Generate auto text content from HTML
  const generateTextContent = useCallback(() => {
    if (currentTemplate?.html_content) {
      const textContent = currentTemplate.html_content
        .replace(/<[^>]*>/g, '') // Remove HTML tags
        .replace(/\s+/g, ' ') // Normalize whitespace
        .trim();
      
      handleUpdateField('text_content', textContent);
    }
  }, [currentTemplate?.html_content, handleUpdateField]);

  // Loading state
  if (loading) {
    return (
      <MainLayout _title="Edit Template">
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
  if (error && !currentTemplate) {
    return (
      <MainLayout _title="Edit Template">
        <Center className="flex-1">
          <VStack space="md" className="items-center max-w-md">
            <Text className="text-red-600 font-semibold text-center">Error Loading Template</Text>
            <Text className="text-gray-600 text-center">{error}</Text>
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
      <MainLayout _title="Edit Template">
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
              onPress={handleGoBack}
              variant="outline"
              size="sm"
              className="p-2"
            >
              <Icon as={ArrowLeftIcon} size="sm" className="text-gray-600" />
            </Button>

            <VStack space="xs" className="flex-1">
              <HStack space="sm" className="items-center flex-wrap">
                <Heading size="xl" className="text-gray-900">
                  Edit Template
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
                {hasUnsavedChanges && (
                  <Badge className="bg-orange-100 text-orange-800">
                    <Text className="text-xs font-medium">Unsaved Changes</Text>
                  </Badge>
                )}
              </HStack>
              <Text className="text-gray-600">
                Last updated {new Date(currentTemplate.updated_at).toLocaleDateString()}
              </Text>
            </VStack>
          </HStack>

          <HStack space="sm" className="flex-wrap">
            <Button
              onPress={handlePreviewTemplate}
              variant="outline"
              size="sm"
              disabled={!currentTemplate.subject_template || !currentTemplate.html_content}
            >
              <HStack space="xs" className="items-center">
                <Icon as={EyeIcon} size="sm" className="text-gray-600" />
                <ButtonText>Preview</ButtonText>
              </HStack>
            </Button>

            <Button
              onPress={handleSendTestEmail}
              variant="outline"
              size="sm"
              disabled={!currentTemplate.subject_template || !currentTemplate.html_content}
            >
              <HStack space="xs" className="items-center">
                <Icon as={SendIcon} size="sm" className="text-gray-600" />
                <ButtonText>Test</ButtonText>
              </HStack>
            </Button>

            <Button
              onPress={handleSaveTemplate}
              disabled={saving || !hasUnsavedChanges}
              className="bg-blue-600"
            >
              <HStack space="xs" className="items-center">
                <Icon as={SaveIcon} size="sm" className="text-white" />
                <ButtonText className="text-white">
                  {saving ? 'Saving...' : 'Save'}
                </ButtonText>
              </HStack>
            </Button>
          </HStack>
        </HStack>

        {/* Error Display */}
        {error && (
          <Card className="p-4 bg-red-50 border-red-200">
            <HStack space="sm" className="items-start">
              <Icon as={ArrowLeftIcon} size="sm" className="text-red-600 mt-0.5" />
              <VStack space="xs" className="flex-1">
                <Text className="font-medium text-red-800">Error Updating Template</Text>
                <Text className="text-sm text-red-600">{error}</Text>
              </VStack>
            </HStack>
          </Card>
        )}

        {/* Template Configuration */}
        <Card className="p-6">
          <VStack space="lg">
            <Heading size="md" className="text-gray-900">
              Template Configuration
            </Heading>

            {/* Template Name */}
            <VStack space="sm">
              <Text className="font-medium text-gray-900">Template Name</Text>
              <Input>
                <InputField
                  placeholder="e.g., Teacher Welcome Email"
                  value={currentTemplate.name || ''}
                  onChangeText={(value) => handleUpdateField('name', value)}
                />
              </Input>
            </VStack>

            {/* Template Status */}
            <HStack className="justify-between items-center">
              <VStack space="xs" className="flex-1">
                <Text className="font-medium text-gray-900">Template Status</Text>
                <Text className="text-xs text-gray-500">
                  Active templates can be used in email sequences and manual sends
                </Text>
              </VStack>
              <Switch
                value={currentTemplate.is_active}
                onValueChange={(value) => handleUpdateField('is_active', value)}
              />
            </HStack>

            {/* School Branding */}
            <HStack className="justify-between items-center">
              <VStack space="xs" className="flex-1">
                <Text className="font-medium text-gray-900">Use School Branding</Text>
                <Text className="text-xs text-gray-500">
                  Apply your school's colors, logo, and styling to this template
                </Text>
              </VStack>
              <Switch
                value={currentTemplate.use_school_branding}
                onValueChange={(value) => handleUpdateField('use_school_branding', value)}
              />
            </HStack>
          </VStack>
        </Card>

        {/* Template Editor */}
        <RichTextTemplateEditor
          template={currentTemplate}
          onChange={handleUpdateField}
          availableVariables={availableVariables}
          onPreview={handlePreviewTemplate}
          validation={validation}
        />

        {/* Text Content Generator */}
        {currentTemplate.html_content && !currentTemplate.text_content && (
          <Card className="p-4 bg-blue-50 border-blue-200">
            <VStack space="sm">
              <HStack className="justify-between items-center">
                <VStack space="xs" className="flex-1">
                  <Text className="font-medium text-blue-900">Generate Plain Text Version</Text>
                  <Text className="text-xs text-blue-700">
                    Create a plain text version of your HTML content for better email compatibility
                  </Text>
                </VStack>
                <Button
                  onPress={generateTextContent}
                  size="sm"
                  variant="outline"
                  className="border-blue-300"
                >
                  <ButtonText>Generate</ButtonText>
                </Button>
              </HStack>
            </VStack>
          </Card>
        )}

        {/* Actions */}
        <Card className="p-6">
          <VStack space="md">
            <Text className="font-medium text-gray-900">Template Actions</Text>
            
            <HStack space="sm" className="flex-wrap">
              <Button
                onPress={handleValidateTemplate}
                variant="outline"
                size="sm"
                disabled={validationLoading || !currentTemplate.subject_template || !currentTemplate.html_content}
              >
                <ButtonText>{validationLoading ? 'Validating...' : 'Validate'}</ButtonText>
              </Button>

              <Button
                onPress={handleDuplicateTemplate}
                variant="outline"
                size="sm"
              >
                <HStack space="xs" className="items-center">
                  <Icon as={CopyIcon} size="xs" className="text-gray-600" />
                  <ButtonText>Duplicate</ButtonText>
                </HStack>
              </Button>

              <Button
                onPress={handleDeleteTemplate}
                variant="outline"
                size="sm"
                className="border-red-200 hover:bg-red-50"
              >
                <HStack space="xs" className="items-center">
                  <Icon as={TrashIcon} size="xs" className="text-red-600" />
                  <ButtonText className="text-red-600">Delete</ButtonText>
                </HStack>
              </Button>
            </HStack>
          </VStack>
        </Card>

        {/* Save Section */}
        {hasUnsavedChanges && (
          <Card className="p-6 bg-orange-50 border-orange-200">
            <VStack space="md">
              <HStack space="sm" className="items-center">
                <Icon as={SaveIcon} size="sm" className="text-orange-600" />
                <Text className="font-medium text-orange-800">You have unsaved changes</Text>
              </HStack>
              
              <HStack space="sm">
                <Button
                  onPress={handleSaveTemplate}
                  disabled={saving}
                  className="bg-orange-600"
                >
                  <ButtonText className="text-white">
                    {saving ? 'Saving...' : 'Save Changes'}
                  </ButtonText>
                </Button>

                <Button
                  onPress={() => {
                    loadTemplate(templateId);
                    setHasUnsavedChanges(false);
                  }}
                  variant="outline"
                  className="border-orange-300"
                >
                  <ButtonText>Discard Changes</ButtonText>
                </Button>
              </HStack>
            </VStack>
          </Card>
        )}
      </VStack>
    </ScrollView>
  );
};

const EditTemplatePageWrapper = () => {
  return (
    <MainLayout _title="Edit Template">
      <EditTemplatePage />
    </MainLayout>
  );
};

export default EditTemplatePageWrapper;