import {
  BoldIcon,
  ItalicIcon,
  LinkIcon,
  PaletteIcon,
  EyeIcon,
  SaveIcon,
  TypeIcon,
  CodeIcon,
  WandIcon,
} from 'lucide-react-native';
import React, { useState, useCallback, useEffect } from 'react';
import { Alert } from 'react-native';

import {
  SchoolEmailTemplate,
  EmailTemplateType,
  CreateTemplateRequest,
  UpdateTemplateRequest,
} from '@/api/communicationApi';
import { Badge } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Input, InputField } from '@/components/ui/input';
import { Pressable } from '@/components/ui/pressable';
import { ScrollView } from '@/components/ui/scroll-view';
import { Select, SelectContent, SelectItem, SelectTrigger } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Text } from '@/components/ui/text';
import { Textarea, TextareaInput } from '@/components/ui/textarea';
import { VStack } from '@/components/ui/vstack';
import { useTemplateEditor, useTemplatePreview } from '@/hooks/useCommunicationTemplates';
import { useSchoolBranding } from '@/hooks/useSchoolBranding';

interface TemplateEditorProps {
  templateId?: number;
  onSave?: (template: SchoolEmailTemplate) => void;
  onCancel?: () => void;
}

const TemplateEditor: React.FC<TemplateEditorProps> = ({ templateId, onSave, onCancel }) => {
  const [activeTab, setActiveTab] = useState<'content' | 'design' | 'preview'>('content');
  const [showVariables, setShowVariables] = useState(false);
  const [testEmail, setTestEmail] = useState('');

  const {
    currentTemplate,
    loading,
    saving,
    error,
    hasUnsavedChanges,
    availableVariables,
    loadTemplate,
    createTemplate,
    updateTemplate,
    updateTemplateField,
    clearError,
  } = useTemplateEditor();

  const {
    preview,
    loading: previewLoading,
    generatePreview,
    sendTestEmail,
    validateTemplate,
  } = useTemplatePreview();

  const { branding } = useSchoolBranding();

  // Load template if editing existing
  useEffect(() => {
    if (templateId) {
      loadTemplate(templateId);
    }
  }, [templateId, loadTemplate]);

  // Template type options
  const templateTypeOptions = [
    { label: 'Invitation', value: 'invitation' },
    { label: 'Reminder', value: 'reminder' },
    { label: 'Welcome', value: 'welcome' },
    { label: 'Profile Reminder', value: 'profile_reminder' },
    { label: 'Completion Celebration', value: 'completion_celebration' },
    { label: 'Ongoing Support', value: 'ongoing_support' },
  ];

  // Save handlers
  const handleSave = useCallback(async () => {
    if (!currentTemplate) return;

    try {
      // Validate template first
      const validation = await validateTemplate({
        subject_template: currentTemplate.subject_template,
        html_content: currentTemplate.html_content,
        text_content: currentTemplate.text_content,
      });

      if (!validation.is_valid && validation.errors.length > 0) {
        Alert.alert('Template Validation Failed', validation.errors.join('\n'), [{ text: 'OK' }]);
        return;
      }

      let savedTemplate: SchoolEmailTemplate;

      if (templateId) {
        // Update existing template
        const updateData: UpdateTemplateRequest = {
          name: currentTemplate.name,
          subject_template: currentTemplate.subject_template,
          html_content: currentTemplate.html_content,
          text_content: currentTemplate.text_content,
          use_school_branding: currentTemplate.use_school_branding,
          custom_css: currentTemplate.custom_css,
        };
        savedTemplate = await updateTemplate(templateId, updateData);
      } else {
        // Create new template
        const createData: CreateTemplateRequest = {
          template_type: currentTemplate.template_type,
          name: currentTemplate.name,
          subject_template: currentTemplate.subject_template,
          html_content: currentTemplate.html_content,
          text_content: currentTemplate.text_content,
          use_school_branding: currentTemplate.use_school_branding,
          custom_css: currentTemplate.custom_css,
        };
        savedTemplate = await createTemplate(createData);
      }

      onSave?.(savedTemplate);
    } catch (error) {
      if (__DEV__) {
        console.error('Error saving template:', error);
      }
    }
  }, [currentTemplate, templateId, validateTemplate, updateTemplate, createTemplate, onSave]);

  const handleCancel = useCallback(() => {
    if (hasUnsavedChanges) {
      Alert.alert('Unsaved Changes', 'You have unsaved changes. Are you sure you want to cancel?', [
        { text: 'Keep Editing', style: 'cancel' },
        { text: 'Cancel', style: 'destructive', onPress: onCancel },
      ]);
    } else {
      onCancel?.();
    }
  }, [hasUnsavedChanges, onCancel]);

  // Preview handlers
  const handleGeneratePreview = useCallback(async () => {
    if (!currentTemplate) return;

    try {
      await generatePreview({
        subject_template: currentTemplate.subject_template,
        html_content: currentTemplate.html_content,
        text_content: currentTemplate.text_content,
        context_variables: {
          teacher_name: 'John Doe',
          school_name: branding?.school || 'Your School',
          invitation_url: 'https://example.com/invitation',
        },
      });
      setActiveTab('preview');
    } catch (error) {
      if (__DEV__) {
        console.error('Error generating preview:', error);
      }
    }
  }, [currentTemplate, generatePreview, branding]);

  const handleSendTest = useCallback(async () => {
    if (!testEmail || !templateId) return;

    try {
      await sendTestEmail(templateId, testEmail);
      setTestEmail('');
    } catch (error) {
      if (__DEV__) {
        console.error('Error sending test email:', error); // TODO: Review for sensitive data // TODO: Review for sensitive data // TODO: Review for sensitive data
      }
    }
  }, [testEmail, templateId, sendTestEmail]);

  // Variable insertion
  const insertVariable = useCallback(
    (variable: string) => {
      if (!currentTemplate) return;

      const cursorPosition = 0; // In a real implementation, you'd track cursor position
      const currentText = currentTemplate.html_content;
      const newText =
        currentText.slice(0, cursorPosition) +
        `{{ ${variable} }}` +
        currentText.slice(cursorPosition);

      updateTemplateField('html_content', newText);
    },
    [currentTemplate, updateTemplateField]
  );

  if (loading) {
    return (
      <Box className="flex-1 justify-center items-center p-6">
        <Text className="text-gray-600">Loading template editor...</Text>
      </Box>
    );
  }

  if (!currentTemplate) {
    return (
      <Box className="flex-1 justify-center items-center p-6">
        <Text className="text-red-600">Failed to load template</Text>
      </Box>
    );
  }

  return (
    <VStack className="flex-1" space="lg">
      {/* Header */}
      <Card className="p-4">
        <VStack space="md">
          <HStack className="justify-between items-center">
            <VStack space="xs">
              <Heading size="lg" className="text-gray-900">
                {templateId ? 'Edit Template' : 'Create New Template'}
              </Heading>
              <Text className="text-gray-600">
                Design professional email templates for your school
              </Text>
            </VStack>

            <HStack space="sm">
              {hasUnsavedChanges && (
                <Badge className="bg-yellow-100 text-yellow-800">
                  <Text className="text-xs">Unsaved Changes</Text>
                </Badge>
              )}
              <Button onPress={handleCancel} variant="outline">
                <ButtonText>Cancel</ButtonText>
              </Button>
              <Button onPress={handleSave} disabled={saving} className="bg-blue-600">
                <HStack space="xs" className="items-center">
                  <Icon as={SaveIcon} size="sm" className="text-white" />
                  <ButtonText className="text-white">
                    {saving ? 'Saving...' : 'Save Template'}
                  </ButtonText>
                </HStack>
              </Button>
            </HStack>
          </HStack>

          {/* Tab Navigation */}
          <HStack space="sm">
            <Pressable
              onPress={() => setActiveTab('content')}
              className={`px-4 py-2 rounded-lg ${
                activeTab === 'content' ? 'bg-blue-100 border border-blue-200' : 'bg-gray-100'
              }`}
            >
              <Text
                className={`text-sm font-medium ${
                  activeTab === 'content' ? 'text-blue-700' : 'text-gray-600'
                }`}
              >
                Content
              </Text>
            </Pressable>

            <Pressable
              onPress={() => setActiveTab('design')}
              className={`px-4 py-2 rounded-lg ${
                activeTab === 'design' ? 'bg-blue-100 border border-blue-200' : 'bg-gray-100'
              }`}
            >
              <Text
                className={`text-sm font-medium ${
                  activeTab === 'design' ? 'text-blue-700' : 'text-gray-600'
                }`}
              >
                Design
              </Text>
            </Pressable>

            <Pressable
              onPress={() => setActiveTab('preview')}
              className={`px-4 py-2 rounded-lg ${
                activeTab === 'preview' ? 'bg-blue-100 border border-blue-200' : 'bg-gray-100'
              }`}
            >
              <Text
                className={`text-sm font-medium ${
                  activeTab === 'preview' ? 'text-blue-700' : 'text-gray-600'
                }`}
              >
                Preview
              </Text>
            </Pressable>
          </HStack>
        </VStack>
      </Card>

      <ScrollView className="flex-1">
        <VStack space="lg" className="p-4">
          {/* Content Tab */}
          {activeTab === 'content' && (
            <VStack space="lg">
              {/* Basic Template Information */}
              <Card className="p-4">
                <VStack space="md">
                  <Heading size="md" className="text-gray-900">
                    Template Information
                  </Heading>

                  <VStack space="sm">
                    <VStack space="xs">
                      <Text className="text-sm font-medium text-gray-700">Template Name</Text>
                      <Input>
                        <InputField
                          value={currentTemplate.name}
                          onChangeText={text => updateTemplateField('name', text)}
                          placeholder="Enter template name..."
                        />
                      </Input>
                    </VStack>

                    <VStack space="xs">
                      <Text className="text-sm font-medium text-gray-700">Template Type</Text>
                      <Select
                        value={currentTemplate.template_type}
                        onValueChange={value => updateTemplateField('template_type', value)}
                      >
                        <SelectTrigger>
                          <Text>
                            {templateTypeOptions.find(
                              opt => opt.value === currentTemplate.template_type
                            )?.label || 'Select type'}
                          </Text>
                        </SelectTrigger>
                        <SelectContent>
                          {templateTypeOptions.map(option => (
                            <SelectItem
                              key={option.value}
                              value={option.value}
                              label={option.label}
                            />
                          ))}
                        </SelectContent>
                      </Select>
                    </VStack>
                  </VStack>
                </VStack>
              </Card>

              {/* Email Subject */}
              <Card className="p-4">
                <VStack space="md">
                  <HStack className="justify-between items-center">
                    <Heading size="md" className="text-gray-900">
                      Email Subject
                    </Heading>
                    <Button
                      size="sm"
                      variant="outline"
                      onPress={() => setShowVariables(!showVariables)}
                    >
                      <HStack space="xs" className="items-center">
                        <Icon as={WandIcon} size="xs" className="text-gray-600" />
                        <ButtonText>Variables</ButtonText>
                      </HStack>
                    </Button>
                  </HStack>

                  <Input>
                    <InputField
                      value={currentTemplate.subject_template}
                      onChangeText={text => updateTemplateField('subject_template', text)}
                      placeholder="Enter email subject..."
                    />
                  </Input>
                </VStack>
              </Card>

              {/* Email Content */}
              <Card className="p-4">
                <VStack space="md">
                  <Heading size="md" className="text-gray-900">
                    HTML Content
                  </Heading>

                  {/* Rich Text Toolbar */}
                  <HStack space="sm" className="flex-wrap">
                    <Button size="sm" variant="outline">
                      <Icon as={BoldIcon} size="xs" className="text-gray-600" />
                    </Button>
                    <Button size="sm" variant="outline">
                      <Icon as={ItalicIcon} size="xs" className="text-gray-600" />
                    </Button>
                    <Button size="sm" variant="outline">
                      <Icon as={LinkIcon} size="xs" className="text-gray-600" />
                    </Button>
                    <Button size="sm" variant="outline">
                      <Icon as={PaletteIcon} size="xs" className="text-gray-600" />
                    </Button>
                  </HStack>

                  <Textarea className="min-h-64">
                    <TextareaInput
                      value={currentTemplate.html_content}
                      onChangeText={text => updateTemplateField('html_content', text)}
                      placeholder="Enter HTML content..."
                    />
                  </Textarea>
                </VStack>
              </Card>

              {/* Plain Text Content */}
              <Card className="p-4">
                <VStack space="md">
                  <Heading size="md" className="text-gray-900">
                    Plain Text Content
                  </Heading>

                  <Textarea className="min-h-32">
                    <TextareaInput
                      value={currentTemplate.text_content}
                      onChangeText={text => updateTemplateField('text_content', text)}
                      placeholder="Enter plain text version..."
                    />
                  </Textarea>
                </VStack>
              </Card>

              {/* Variables Panel */}
              {showVariables && (
                <Card className="p-4">
                  <VStack space="md">
                    <Heading size="md" className="text-gray-900">
                      Available Variables
                    </Heading>

                    <VStack space="sm">
                      {Object.entries(availableVariables).map(([category, variables]) => (
                        <VStack key={category} space="xs">
                          <Text className="text-sm font-medium text-gray-700 capitalize">
                            {category.replace('_', ' ')} Variables
                          </Text>
                          <HStack space="xs" className="flex-wrap">
                            {Object.entries(variables).map(([variable, description]) => (
                              <Pressable
                                key={variable}
                                onPress={() => insertVariable(variable)}
                                className="px-2 py-1 bg-blue-50 border border-blue-200 rounded"
                              >
                                <Text className="text-xs text-blue-700">{variable}</Text>
                              </Pressable>
                            ))}
                          </HStack>
                        </VStack>
                      ))}
                    </VStack>
                  </VStack>
                </Card>
              )}
            </VStack>
          )}

          {/* Design Tab */}
          {activeTab === 'design' && (
            <VStack space="lg">
              <Card className="p-4">
                <VStack space="md">
                  <Heading size="md" className="text-gray-900">
                    Design Settings
                  </Heading>

                  <HStack className="justify-between items-center">
                    <VStack space="xs">
                      <Text className="font-medium text-gray-700">Use School Branding</Text>
                      <Text className="text-sm text-gray-600">
                        Apply your school's colors and logo automatically
                      </Text>
                    </VStack>
                    <Switch
                      value={currentTemplate.use_school_branding}
                      onValueChange={value => updateTemplateField('use_school_branding', value)}
                    />
                  </HStack>

                  <VStack space="xs">
                    <Text className="text-sm font-medium text-gray-700">Custom CSS</Text>
                    <Textarea className="min-h-32">
                      <TextareaInput
                        value={currentTemplate.custom_css || ''}
                        onChangeText={text => updateTemplateField('custom_css', text)}
                        placeholder="Add custom CSS styles..."
                      />
                    </Textarea>
                  </VStack>
                </VStack>
              </Card>
            </VStack>
          )}

          {/* Preview Tab */}
          {activeTab === 'preview' && (
            <VStack space="lg">
              <Card className="p-4">
                <VStack space="md">
                  <HStack className="justify-between items-center">
                    <Heading size="md" className="text-gray-900">
                      Template Preview
                    </Heading>
                    <Button onPress={handleGeneratePreview} disabled={previewLoading} size="sm">
                      <HStack space="xs" className="items-center">
                        <Icon as={EyeIcon} size="xs" className="text-white" />
                        <ButtonText>
                          {previewLoading ? 'Generating...' : 'Refresh Preview'}
                        </ButtonText>
                      </HStack>
                    </Button>
                  </HStack>

                  {preview ? (
                    <VStack space="md">
                      <VStack space="xs">
                        <Text className="text-sm font-medium text-gray-700">Subject</Text>
                        <Box className="p-3 bg-gray-50 rounded border">
                          <Text className="text-gray-900">{preview.subject}</Text>
                        </Box>
                      </VStack>

                      <VStack space="xs">
                        <Text className="text-sm font-medium text-gray-700">HTML Preview</Text>
                        <Box className="p-4 bg-white border rounded min-h-48">
                          {/* In a real implementation, you'd render the HTML safely */}
                          <Text className="text-gray-600 text-sm">
                            HTML preview would be rendered here
                          </Text>
                        </Box>
                      </VStack>
                    </VStack>
                  ) : (
                    <Box className="py-8 text-center">
                      <Text className="text-gray-500">
                        Click "Refresh Preview" to see how your template will look
                      </Text>
                    </Box>
                  )}
                </VStack>
              </Card>

              {/* Test Email */}
              {templateId && (
                <Card className="p-4">
                  <VStack space="md">
                    <Heading size="md" className="text-gray-900">
                      Send Test Email
                    </Heading>

                    <HStack space="sm">
                      <Box className="flex-1">
                        <Input>
                          <InputField
                            value={testEmail}
                            onChangeText={setTestEmail}
                            placeholder="Enter test email address..."
                            keyboardType="email-address"
                          />
                        </Input>
                      </Box>
                      <Button
                        onPress={handleSendTest}
                        disabled={!testEmail || previewLoading}
                        size="sm"
                      >
                        <ButtonText>Send Test</ButtonText>
                      </Button>
                    </HStack>
                  </VStack>
                </Card>
              )}
            </VStack>
          )}
        </VStack>
      </ScrollView>

      {/* Error Display */}
      {error && (
        <Card className="mx-4 mb-4 p-4 bg-red-50 border border-red-200">
          <HStack className="justify-between items-start">
            <Text className="text-red-700 flex-1">{error}</Text>
            <Button size="sm" variant="link" onPress={clearError}>
              <ButtonText className="text-red-600">Dismiss</ButtonText>
            </Button>
          </HStack>
        </Card>
      )}
    </VStack>
  );
};

export default TemplateEditor;
