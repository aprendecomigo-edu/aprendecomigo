import { isWeb } from '@/utils/platform';
import {
  BoldIcon,
  ItalicIcon,
  UnderlineIcon,
  LinkIcon,
  ListIcon,
  AlignLeftIcon,
  AlignCenterIcon,
  AlignRightIcon,
  EyeIcon,
  TypeIcon,
  CodeIcon,
  VariableIcon,
  CheckIcon,
  XIcon,
} from 'lucide-react-native';
import React, { useState, useCallback, useMemo, useEffect } from 'react';
import { TextInput } from 'react-native';

import { SchoolEmailTemplate } from '@/api/communicationApi';
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
import { Text } from '@/components/ui/text';
import { Textarea, TextareaInput } from '@/components/ui/textarea';
import { VStack } from '@/components/ui/vstack';
import { useTemplatePreview } from '@/hooks/useCommunicationTemplates';
import { useSchoolBranding } from '@/hooks/useSchoolBranding';

interface RichTextTemplateEditorProps {
  template?: Partial<SchoolEmailTemplate>;
  onChange: (field: keyof SchoolEmailTemplate, value: any) => void;
  availableVariables?: Record<string, Record<string, string>>;
  onPreview?: () => void;
  validation?: {
    errors: string[];
    warnings: string[];
    variables_used: string[];
    missing_variables: string[];
  };
}

interface Variable {
  key: string;
  description: string;
  category: string;
}

const RichTextTemplateEditor: React.FC<RichTextTemplateEditorProps> = ({
  template = {},
  onChange,
  availableVariables = {},
  onPreview,
  validation,
}) => {
  const [activeTab, setActiveTab] = useState<'html' | 'text' | 'preview'>('html');
  const [showVariables, setShowVariables] = useState(false);
  const [selectedText, setSelectedText] = useState('');
  const [cursorPosition, setCursorPosition] = useState(0);

  const { branding } = useSchoolBranding();
  const { preview, generatePreview, loading: previewLoading } = useTemplatePreview();

  // Flatten available variables for easier use
  const flatVariables = useMemo(() => {
    const variables: Variable[] = [];
    Object.entries(availableVariables).forEach(([category, vars]) => {
      Object.entries(vars).forEach(([key, description]) => {
        variables.push({ key, description, category });
      });
    });
    return variables;
  }, [availableVariables]);

  // Group variables by category
  const variablesByCategory = useMemo(() => {
    const grouped: Record<string, Variable[]> = {};
    flatVariables.forEach(variable => {
      if (!grouped[variable.category]) {
        grouped[variable.category] = [];
      }
      grouped[variable.category].push(variable);
    });
    return grouped;
  }, [flatVariables]);

  // Generate preview when template content changes
  useEffect(() => {
    if (activeTab === 'preview' && template.subject_template && template.html_content) {
      generatePreview({
        subject_template: template.subject_template,
        html_content: template.html_content,
        text_content: template.text_content || '',
        template_type: template.template_type,
      });
    }
  }, [activeTab, template, generatePreview]);

  // Insert variable at cursor position
  const insertVariable = useCallback(
    (variableKey: string) => {
      const htmlContent = template.html_content || '';
      const variable = `{{${variableKey}}}`;

      const newContent =
        htmlContent.slice(0, cursorPosition) + variable + htmlContent.slice(cursorPosition);

      onChange('html_content', newContent);

      // Update cursor position to after the inserted variable
      setCursorPosition(cursorPosition + variable.length);
      setShowVariables(false);
    },
    [template.html_content, cursorPosition, onChange],
  );

  // Format text with HTML tags
  const formatText = useCallback(
    (tag: string) => {
      if (!selectedText) return;

      const htmlContent = template.html_content || '';
      const openTag = `<${tag}>`;
      const closeTag = `</${tag}>`;
      const formattedText = `${openTag}${selectedText}${closeTag}`;

      const newContent = htmlContent.replace(selectedText, formattedText);
      onChange('html_content', newContent);
    },
    [selectedText, template.html_content, onChange],
  );

  // Insert HTML element
  const insertElement = useCallback(
    (element: string) => {
      const htmlContent = template.html_content || '';
      let elementHtml = '';

      switch (element) {
        case 'link':
          elementHtml = '<a href="{{link_url}}">{{link_text}}</a>';
          break;
        case 'list':
          elementHtml = '<ul><li>{{list_item_1}}</li><li>{{list_item_2}}</li></ul>';
          break;
        case 'button':
          elementHtml =
            '<button style="background-color: {{button_color}}; color: white; padding: 10px 20px; border: none; border-radius: 5px;">{{button_text}}</button>';
          break;
        default:
          return;
      }

      const newContent =
        htmlContent.slice(0, cursorPosition) + elementHtml + htmlContent.slice(cursorPosition);

      onChange('html_content', newContent);
    },
    [template.html_content, cursorPosition, onChange],
  );

  // Get validation status color
  const getValidationColor = (type: 'error' | 'warning' | 'success') => {
    switch (type) {
      case 'error':
        return 'text-red-600';
      case 'warning':
        return 'text-yellow-600';
      case 'success':
        return 'text-green-600';
      default:
        return 'text-gray-600';
    }
  };

  const tabs = [
    { id: 'html', label: 'HTML Editor', icon: CodeIcon },
    { id: 'text', label: 'Plain Text', icon: TypeIcon },
    { id: 'preview', label: 'Preview', icon: EyeIcon },
  ] as const;

  return (
    <VStack space="md" className="flex-1">
      {/* Subject Template */}
      <Card className="p-4">
        <VStack space="sm">
          <Heading size="sm" className="text-gray-900">
            Email Subject
          </Heading>
          <Input>
            <InputField
              placeholder="Enter email subject template..."
              value={template.subject_template || ''}
              onChangeText={value => onChange('subject_template', value)}
            />
          </Input>
          <Text className="text-xs text-gray-500">
            Use variables like {'{{teacher_name}}'} or {'{{school_name}}'} in your subject
          </Text>
        </VStack>
      </Card>

      {/* Editor Tabs */}
      <Card className="flex-1">
        <VStack space="md" className="h-full">
          {/* Tab Headers */}
          <HStack className="border-b border-gray-200">
            {tabs.map(tab => (
              <Pressable
                key={tab.id}
                onPress={() => setActiveTab(tab.id)}
                className={`flex-1 p-3 border-b-2 ${
                  activeTab === tab.id
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-transparent hover:bg-gray-50'
                }`}
              >
                <HStack space="xs" className="items-center justify-center">
                  <Icon
                    as={tab.icon}
                    size="sm"
                    className={activeTab === tab.id ? 'text-blue-600' : 'text-gray-600'}
                  />
                  <Text
                    className={`text-sm font-medium ${
                      activeTab === tab.id ? 'text-blue-600' : 'text-gray-600'
                    }`}
                  >
                    {tab.label}
                  </Text>
                </HStack>
              </Pressable>
            ))}
          </HStack>

          {/* Tab Content */}
          <Box className="flex-1 p-4">
            {activeTab === 'html' && (
              <VStack space="md" className="h-full">
                {/* Formatting Toolbar */}
                <HStack space="sm" className="flex-wrap">
                  <Button
                    size="sm"
                    variant="outline"
                    onPress={() => formatText('strong')}
                    disabled={!selectedText}
                  >
                    <Icon as={BoldIcon} size="xs" className="text-gray-600" />
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onPress={() => formatText('em')}
                    disabled={!selectedText}
                  >
                    <Icon as={ItalicIcon} size="xs" className="text-gray-600" />
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onPress={() => formatText('u')}
                    disabled={!selectedText}
                  >
                    <Icon as={UnderlineIcon} size="xs" className="text-gray-600" />
                  </Button>
                  <Button size="sm" variant="outline" onPress={() => insertElement('link')}>
                    <Icon as={LinkIcon} size="xs" className="text-gray-600" />
                  </Button>
                  <Button size="sm" variant="outline" onPress={() => insertElement('list')}>
                    <Icon as={ListIcon} size="xs" className="text-gray-600" />
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onPress={() => setShowVariables(!showVariables)}
                    className={showVariables ? 'bg-blue-100 border-blue-300' : ''}
                  >
                    <HStack space="xs" className="items-center">
                      <Icon as={VariableIcon} size="xs" className="text-gray-600" />
                      <ButtonText className="text-xs">Variables</ButtonText>
                    </HStack>
                  </Button>
                </HStack>

                {/* Variables Panel */}
                {showVariables && (
                  <Card className="p-3 bg-blue-50 border-blue-200">
                    <VStack space="sm">
                      <Text className="text-sm font-medium text-blue-900">Available Variables</Text>
                      <ScrollView className="max-h-32">
                        <VStack space="xs">
                          {Object.entries(variablesByCategory).map(([category, vars]) => (
                            <VStack key={category} space="xs">
                              <Text className="text-xs font-medium text-blue-800 uppercase">
                                {category.replace('_', ' ')}
                              </Text>
                              <HStack space="xs" className="flex-wrap">
                                {vars.map(variable => (
                                  <Pressable
                                    key={variable.key}
                                    onPress={() => insertVariable(variable.key)}
                                    className="px-2 py-1 bg-white border border-blue-300 rounded hover:bg-blue-100 active:bg-blue-100"
                                  >
                                    <Text className="text-xs text-blue-700">
                                      {'{{' + variable.key + '}}'}
                                    </Text>
                                  </Pressable>
                                ))}
                              </HStack>
                            </VStack>
                          ))}
                        </VStack>
                      </ScrollView>
                    </VStack>
                  </Card>
                )}

                {/* HTML Editor */}
                <VStack space="sm" className="flex-1">
                  <Textarea className="flex-1 min-h-64">
                    <TextareaInput
                      placeholder="Enter your HTML email content here..."
                      value={template.html_content || ''}
                      onChangeText={value => onChange('html_content', value)}
                      onSelectionChange={event => {
                        setCursorPosition(event.nativeEvent.selection.start);
                      }}
                      multiline
                      className="h-full"
                    />
                  </Textarea>

                  {/* HTML Hints */}
                  <Text className="text-xs text-gray-500">
                    Use HTML tags for formatting. Variables should be in the format{' '}
                    {'{{variable_name}}'}
                  </Text>
                </VStack>
              </VStack>
            )}

            {activeTab === 'text' && (
              <VStack space="sm" className="h-full">
                <Textarea className="flex-1 min-h-64">
                  <TextareaInput
                    placeholder="Enter the plain text version of your email..."
                    value={template.text_content || ''}
                    onChangeText={value => onChange('text_content', value)}
                    multiline
                    className="h-full"
                  />
                </Textarea>
                <Text className="text-xs text-gray-500">
                  Plain text version for email clients that don't support HTML
                </Text>
              </VStack>
            )}

            {activeTab === 'preview' && (
              <VStack space="md" className="h-full">
                {previewLoading ? (
                  <Box className="flex-1 flex items-center justify-center">
                    <Text className="text-gray-500">Generating preview...</Text>
                  </Box>
                ) : preview ? (
                  <ScrollView className="flex-1">
                    <VStack space="md">
                      {/* Subject Preview */}
                      <Card className="p-3 bg-gray-50">
                        <VStack space="xs">
                          <Text className="text-xs font-medium text-gray-600">SUBJECT</Text>
                          <Text className="font-medium">{preview.subject}</Text>
                        </VStack>
                      </Card>

                      {/* Email Content Preview */}
                      <Card className="p-4">
                        <VStack space="sm">
                          <Text className="text-xs font-medium text-gray-600">EMAIL CONTENT</Text>
                          {isWeb ? (
                            <div
                              dangerouslySetInnerHTML={{ __html: preview.html_content }}
                              style={{
                                minHeight: '200px',
                                border: '1px solid #e5e7eb',
                                borderRadius: '8px',
                                padding: '16px',
                                backgroundColor: 'white',
                              }}
                            />
                          ) : (
                            <Box className="min-h-48 border border-gray-200 rounded-lg p-4 bg-white">
                              <Text className="text-gray-600">
                                HTML preview not available on mobile. Use web version for full
                                preview.
                              </Text>
                            </Box>
                          )}
                        </VStack>
                      </Card>

                      {/* Variables Used */}
                      {preview.variables_used.length > 0 && (
                        <Card className="p-3 bg-green-50 border-green-200">
                          <VStack space="xs">
                            <Text className="text-sm font-medium text-green-800">
                              Variables Used
                            </Text>
                            <HStack space="xs" className="flex-wrap">
                              {preview.variables_used.map(variable => (
                                <Badge key={variable} className="bg-green-100 text-green-800">
                                  <Text className="text-xs">{'{{' + variable + '}}'}</Text>
                                </Badge>
                              ))}
                            </HStack>
                          </VStack>
                        </Card>
                      )}

                      {/* Missing Variables Warning */}
                      {preview.missing_variables.length > 0 && (
                        <Card className="p-3 bg-yellow-50 border-yellow-200">
                          <VStack space="xs">
                            <Text className="text-sm font-medium text-yellow-800">
                              Missing Variables
                            </Text>
                            <HStack space="xs" className="flex-wrap">
                              {preview.missing_variables.map(variable => (
                                <Badge key={variable} className="bg-yellow-100 text-yellow-800">
                                  <Text className="text-xs">{'{{' + variable + '}}'}</Text>
                                </Badge>
                              ))}
                            </HStack>
                            <Text className="text-xs text-yellow-700">
                              These variables are not defined and will appear as placeholders
                            </Text>
                          </VStack>
                        </Card>
                      )}
                    </VStack>
                  </ScrollView>
                ) : (
                  <Box className="flex-1 flex items-center justify-center">
                    <VStack space="sm" className="items-center">
                      <Icon as={EyeIcon} size="xl" className="text-gray-400" />
                      <Text className="text-gray-500 text-center">
                        Add subject and content to see preview
                      </Text>
                      {onPreview && (
                        <Button onPress={onPreview} size="sm">
                          <ButtonText>Generate Preview</ButtonText>
                        </Button>
                      )}
                    </VStack>
                  </Box>
                )}
              </VStack>
            )}
          </Box>
        </VStack>
      </Card>

      {/* Validation Status */}
      {validation && (
        <Card className="p-3">
          <VStack space="sm">
            <Text className="text-sm font-medium text-gray-900">Validation Status</Text>

            {validation.errors.length > 0 && (
              <HStack space="xs" className="items-start">
                <Icon as={XIcon} size="sm" className="text-red-600 mt-0.5" />
                <VStack space="xs" className="flex-1">
                  {validation.errors.map((error, index) => (
                    <Text key={index} className="text-sm text-red-600">
                      {error}
                    </Text>
                  ))}
                </VStack>
              </HStack>
            )}

            {validation.warnings.length > 0 && (
              <HStack space="xs" className="items-start">
                <Icon as={XIcon} size="sm" className="text-yellow-600 mt-0.5" />
                <VStack space="xs" className="flex-1">
                  {validation.warnings.map((warning, index) => (
                    <Text key={index} className="text-sm text-yellow-600">
                      {warning}
                    </Text>
                  ))}
                </VStack>
              </HStack>
            )}

            {validation.errors.length === 0 && validation.warnings.length === 0 && (
              <HStack space="xs" className="items-center">
                <Icon as={CheckIcon} size="sm" className="text-green-600" />
                <Text className="text-sm text-green-600">Template is valid</Text>
              </HStack>
            )}
          </VStack>
        </Card>
      )}
    </VStack>
  );
};

export default RichTextTemplateEditor;
