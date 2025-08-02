import { isWeb } from '@gluestack-ui/nativewind-utils/IsWeb';
import { router } from 'expo-router';
import { ArrowLeftIcon, SaveIcon, EyeIcon, SendIcon } from 'lucide-react-native';
import React, { useState, useCallback, useEffect } from 'react';
import { Alert } from 'react-native';

import { EmailTemplateType, CreateTemplateRequest } from '@/api/communicationApi';
import RichTextTemplateEditor from '@/components/communication/RichTextTemplateEditor';
import MainLayout from '@/components/layouts/MainLayout';
import { Badge } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Input, InputField } from '@/components/ui/input';
import { ScrollView } from '@/components/ui/scroll-view';
import { Select, SelectContent, SelectItem, SelectTrigger } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { useTemplateEditor, useTemplatePreview } from '@/hooks/useCommunicationTemplates';

const CreateTemplatePage = () => {
  // Form state
  const [templateData, setTemplateData] = useState<Partial<CreateTemplateRequest>>({
    template_type: 'invitation',
    name: '',
    subject_template: '',
    html_content: '',
    text_content: '',
    use_school_branding: true,
    custom_css: '',
  });

  const [validation, setValidation] = useState<{
    errors: string[];
    warnings: string[];
    variables_used: string[];
    missing_variables: string[];
  } | null>(null);

  const [showPreview, setShowPreview] = useState(false);

  // Hooks
  const {
    createTemplate,
    saving,
    error,
    availableVariables,
    clearError,
  } = useTemplateEditor();

  const { 
    validateTemplate,
    sendTestEmail,
    loading: validationLoading 
  } = useTemplatePreview();

  // Template type options
  const templateTypeOptions = [
    {
      value: 'invitation',
      label: 'Teacher Invitation',
      description: 'Initial invitation emails sent to teachers',
      color: 'bg-blue-100 text-blue-800',
    },
    {
      value: 'reminder',
      label: 'Reminder',
      description: 'Follow-up reminders for pending actions',
      color: 'bg-yellow-100 text-yellow-800',
    },
    {
      value: 'welcome',
      label: 'Welcome',
      description: 'Welcome emails for new teachers who joined',
      color: 'bg-green-100 text-green-800',
    },
    {
      value: 'profile_reminder',
      label: 'Profile Reminder',
      description: 'Reminders to complete teacher profile',
      color: 'bg-orange-100 text-orange-800',
    },
    {
      value: 'completion_celebration',
      label: 'Completion Celebration',
      description: 'Congratulations for completing onboarding',
      color: 'bg-purple-100 text-purple-800',
    },
    {
      value: 'ongoing_support',
      label: 'Ongoing Support',
      description: 'Support and resources for existing teachers',
      color: 'bg-gray-100 text-gray-800',
    },
  ];

  // Get current template type info
  const currentTemplateType = templateTypeOptions.find(
    option => option.value === templateData.template_type
  );

  // Update template field
  const updateField = useCallback((field: keyof CreateTemplateRequest, value: any) => {
    setTemplateData(prev => ({
      ...prev,
      [field]: value,
    }));
    clearError();
  }, [clearError]);

  // Validate template content
  const handleValidateTemplate = useCallback(async () => {
    if (!templateData.subject_template || !templateData.html_content) {
      Alert.alert('Validation Error', 'Please add subject and content before validating');
      return;
    }

    try {
      const validationResult = await validateTemplate({
        subject_template: templateData.subject_template,
        html_content: templateData.html_content,
        text_content: templateData.text_content || '',
      });

      setValidation(validationResult);
    } catch (err) {
      console.error('Validation error:', err);
    }
  }, [templateData, validateTemplate]);

  // Auto-validate when content changes
  useEffect(() => {
    const timer = setTimeout(() => {
      if (templateData.subject_template && templateData.html_content) {
        handleValidateTemplate();
      }
    }, 1000);

    return () => clearTimeout(timer);
  }, [templateData.subject_template, templateData.html_content, handleValidateTemplate]);

  // Save template
  const handleSaveTemplate = useCallback(async () => {
    // Validation
    if (!templateData.name?.trim()) {
      Alert.alert('Validation Error', 'Please enter a template name');
      return;
    }

    if (!templateData.subject_template?.trim()) {
      Alert.alert('Validation Error', 'Please enter an email subject');
      return;
    }

    if (!templateData.html_content?.trim()) {
      Alert.alert('Validation Error', 'Please enter email content');
      return;
    }

    try {
      const template = await createTemplate(templateData as CreateTemplateRequest);
      
      Alert.alert(
        'Template Created',
        'Your email template has been created successfully. What would you like to do next?',
        [
          {
            text: 'View Templates',
            onPress: () => router.push('/(school-admin)/communication/templates'),
          },
          {
            text: 'Edit Template',
            onPress: () => router.push(`/(school-admin)/communication/templates/${template.id}/edit`),
          },
          {
            text: 'Send Test Email',
            onPress: () => router.push(`/(school-admin)/communication/templates/${template.id}/test`),
          },
        ]
      );
    } catch (err) {
      console.error('Error creating template:', err);
    }
  }, [templateData, createTemplate]);

  // Preview template
  const handlePreviewTemplate = useCallback(() => {
    if (!templateData.subject_template || !templateData.html_content) {
      Alert.alert('Preview Error', 'Please add subject and content before previewing');
      return;
    }
    setShowPreview(!showPreview);
  }, [templateData, showPreview]);

  // Go back
  const handleGoBack = useCallback(() => {
    if (templateData.name || templateData.subject_template || templateData.html_content) {
      Alert.alert(
        'Unsaved Changes',
        'You have unsaved changes. Are you sure you want to go back?',
        [
          { text: 'Stay', style: 'cancel' },
          { 
            text: 'Go Back', 
            style: 'destructive',
            onPress: () => router.back() 
          },
        ]
      );
    } else {
      router.back();
    }
  }, [templateData]);

  // Generate auto text content from HTML
  const generateTextContent = useCallback(() => {
    if (templateData.html_content) {
      // Simple HTML to text conversion
      const textContent = templateData.html_content
        .replace(/<[^>]*>/g, '') // Remove HTML tags
        .replace(/\s+/g, ' ') // Normalize whitespace
        .trim();
      
      updateField('text_content', textContent);
    }
  }, [templateData.html_content, updateField]);

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
              <Heading size="xl" className="text-gray-900">
                Create Email Template
              </Heading>
              <Text className="text-gray-600">
                Design a new email template for teacher communications
              </Text>
            </VStack>
          </HStack>

          <HStack space="sm">
            <Button
              onPress={handlePreviewTemplate}
              variant="outline"
              disabled={!templateData.subject_template || !templateData.html_content}
            >
              <HStack space="xs" className="items-center">
                <Icon as={EyeIcon} size="sm" className="text-gray-600" />
                <ButtonText>Preview</ButtonText>
              </HStack>
            </Button>

            <Button
              onPress={handleSaveTemplate}
              disabled={saving || !templateData.name || !templateData.subject_template || !templateData.html_content}
              className="bg-blue-600"
            >
              <HStack space="xs" className="items-center">
                <Icon as={SaveIcon} size="sm" className="text-white" />
                <ButtonText className="text-white">
                  {saving ? 'Saving...' : 'Save Template'}
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
                <Text className="font-medium text-red-800">Error Creating Template</Text>
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
                  value={templateData.name || ''}
                  onChangeText={(value) => updateField('name', value)}
                />
              </Input>
              <Text className="text-xs text-gray-500">
                Give your template a descriptive name for easy identification
              </Text>
            </VStack>

            {/* Template Type */}
            <VStack space="sm">
              <Text className="font-medium text-gray-900">Template Type</Text>
              <Select 
                value={templateData.template_type} 
                onValueChange={(value) => updateField('template_type', value)}
              >
                <SelectTrigger>
                  <HStack space="sm" className="items-center">
                    {currentTemplateType && (
                      <Badge className={currentTemplateType.color}>
                        <Text className="text-xs font-medium">
                          {currentTemplateType.label}
                        </Text>
                      </Badge>
                    )}
                  </HStack>
                </SelectTrigger>
                <SelectContent>
                  {templateTypeOptions.map(option => (
                    <SelectItem key={option.value} value={option.value} label={option.label} />
                  ))}
                </SelectContent>
              </Select>
              {currentTemplateType && (
                <Text className="text-xs text-gray-500">
                  {currentTemplateType.description}
                </Text>
              )}
            </VStack>

            {/* Template Options */}
            <VStack space="md">
              <Text className="font-medium text-gray-900">Template Options</Text>
              
              <HStack className="justify-between items-center">
                <VStack space="xs" className="flex-1">
                  <Text className="text-gray-900">Use School Branding</Text>
                  <Text className="text-xs text-gray-500">
                    Apply your school's colors, logo, and styling to this template
                  </Text>
                </VStack>
                <Switch
                  value={templateData.use_school_branding}
                  onValueChange={(value) => updateField('use_school_branding', value)}
                />
              </HStack>
            </VStack>
          </VStack>
        </Card>

        {/* Template Editor */}
        <RichTextTemplateEditor
          template={templateData}
          onChange={updateField}
          availableVariables={availableVariables}
          onPreview={handlePreviewTemplate}
          validation={validation}
        />

        {/* Text Content Generator */}
        {templateData.html_content && !templateData.text_content && (
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

        {/* Quick Actions */}
        <Card className="p-4">
          <VStack space="md">
            <Text className="font-medium text-gray-900">Quick Actions</Text>
            
            <HStack space="sm" className="flex-wrap">
              <Button
                onPress={handleValidateTemplate}
                variant="outline"
                size="sm"
                disabled={validationLoading || !templateData.subject_template || !templateData.html_content}
              >
                <ButtonText>{validationLoading ? 'Validating...' : 'Validate Template'}</ButtonText>
              </Button>

              <Button
                onPress={() => {
                  Alert.alert(
                    'Template Help',
                    'Need help creating your template? Check our documentation for examples and best practices.',
                    [
                      { text: 'Later', style: 'cancel' },
                      { 
                        text: 'View Help',
                        onPress: () => router.push('/(school-admin)/communication/help')
                      },
                    ]
                  );
                }}
                variant="outline"
                size="sm"
              >
                <ButtonText>Get Help</ButtonText>
              </Button>
            </HStack>
          </VStack>
        </Card>

        {/* Save Actions */}
        <Card className="p-6">
          <VStack space="md">
            <Text className="font-medium text-gray-900">Save & Next Steps</Text>
            
            <VStack space="sm">
              <Button
                onPress={handleSaveTemplate}
                disabled={saving || !templateData.name || !templateData.subject_template || !templateData.html_content}
                className="bg-blue-600"
              >
                <ButtonText className="text-white">
                  {saving ? 'Creating Template...' : 'Create Template'}
                </ButtonText>
              </Button>

              <Text className="text-xs text-gray-500 text-center">
                After creating, you can test your template by sending preview emails
              </Text>
            </VStack>
          </VStack>
        </Card>
      </VStack>
    </ScrollView>
  );
};

const CreateTemplatePageWrapper = () => {
  return (
    <MainLayout _title="Create Email Template">
      <CreateTemplatePage />
    </MainLayout>
  );
};

export default CreateTemplatePageWrapper;