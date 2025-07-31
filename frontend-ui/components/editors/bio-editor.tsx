import React, { useState, useEffect } from 'react';
import { Platform } from 'react-native';
import { 
  Bold, 
  Italic, 
  List, 
  ListOrdered, 
  Quote, 
  Undo, 
  Redo,
  Eye,
  Edit3,
  AlertCircle,
  CheckCircle2
} from 'lucide-react-native';

import { Box } from '@/components/ui/box';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Text } from '@/components/ui/text';
import { Textarea } from '@/components/ui/textarea';
import { VStack } from '@/components/ui/vstack';
import { Badge, BadgeText } from '@/components/ui/badge';

interface BioEditorProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  maxWords?: number;
  minWords?: number;
  showTemplates?: boolean;
  className?: string;
}

// Predefined bio templates
const BIO_TEMPLATES = [
  {
    id: 'experienced',
    title: 'Experienced Educator',
    content: `With over [X] years of teaching experience, I am passionate about helping students reach their full potential. I specialize in [Subject] and have worked with students from [Grade levels]. My teaching approach focuses on making complex concepts accessible and engaging through [Teaching method].

I hold a [Degree] from [University] and am certified in [Certifications]. I believe that every student learns differently, so I adapt my teaching style to meet individual needs and learning preferences.

In my classes, students can expect a supportive environment where questions are encouraged and mistakes are seen as learning opportunities. I'm committed to helping you achieve your academic goals and build confidence in [Subject].`,
  },
  {
    id: 'passionate',
    title: 'Passionate Teacher',
    content: `Welcome to my teaching profile! I'm [Name], and I'm absolutely passionate about [Subject]. What excites me most about teaching is seeing that "aha!" moment when a concept finally clicks for a student.

My background includes [Education/Experience], and I've had the privilege of working with students of all ages and skill levels. Whether you're just starting out or looking to master advanced topics, I'm here to guide you every step of the way.

My teaching philosophy centers around creating a comfortable, encouraging environment where students feel safe to explore, ask questions, and make mistakes. I use a variety of teaching methods including [Methods] to ensure that learning is both effective and enjoyable.

Let's work together to achieve your learning goals!`,
  },
  {
    id: 'results-focused',
    title: 'Results-Focused Tutor',
    content: `I'm a dedicated [Subject] tutor with a proven track record of helping students improve their grades and understanding. My students typically see [Results] within [Timeframe].

My qualifications include [Qualifications], and I have [X] years of experience working with students at [Levels]. I specialize in [Specializations] and have helped students prepare for [Exams/Tests].

My approach is systematic and personalized. I start by assessing each student's current level and learning style, then create a customized study plan that addresses their specific needs and goals. I provide regular progress updates and adjust my teaching methods as needed.

I'm committed to your success and will work tirelessly to help you achieve your academic objectives. Let's discuss how I can help you reach your goals!`,
  },
];

export const BioEditor: React.FC<BioEditorProps> = ({
  value,
  onChange,
  placeholder = "Tell students about your teaching approach, experience, and what makes you unique as an educator...",
  maxWords = 500,
  minWords = 50,
  showTemplates = true,
  className = '',
}) => {
  const [isPreview, setIsPreview] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null);
  const [showTemplatesPanel, setShowTemplatesPanel] = useState(false);
  
  // Calculate word count
  const wordCount = value.trim() ? value.trim().split(/\s+/).length : 0;
  const isOverLimit = wordCount > maxWords;
  const isUnderMinimum = wordCount < minWords;
  
  // Character count
  const charCount = value.length;
  
  // Get word count status
  const getWordCountStatus = () => {
    if (isOverLimit) return { color: 'text-red-600', bg: 'bg-red-100' };
    if (isUnderMinimum) return { color: 'text-yellow-600', bg: 'bg-yellow-100' };
    if (wordCount > maxWords * 0.8) return { color: 'text-blue-600', bg: 'bg-blue-100' };
    return { color: 'text-green-600', bg: 'bg-green-100' };
  };

  const wordCountStatus = getWordCountStatus();

  // Apply template
  const applyTemplate = (template: typeof BIO_TEMPLATES[0]) => {
    onChange(template.content);
    setSelectedTemplate(template.id);
    setShowTemplatesPanel(false);
  };

  // Format text (basic markdown-like formatting)
  const formatText = (format: string) => {
    // This is a simplified implementation
    // In a real app, you'd want a more robust rich text editor
    const textarea = document.getElementById('bio-textarea') as HTMLTextAreaElement;
    if (!textarea) return;

    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const selectedText = value.substring(start, end);
    
    if (!selectedText) return;

    let formattedText = '';
    switch (format) {
      case 'bold':
        formattedText = `**${selectedText}**`;
        break;
      case 'italic':
        formattedText = `*${selectedText}*`;
        break;
      case 'quote':
        formattedText = `> ${selectedText}`;
        break;
      default:
        return;
    }

    const newValue = value.substring(0, start) + formattedText + value.substring(end);
    onChange(newValue);
  };

  // Render formatted preview
  const renderPreview = () => {
    return value
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/^> (.*?)$/gm, '<blockquote>$1</blockquote>')
      .split('\n')
      .map((line, index) => (
        <Text key={index} className="text-gray-700 mb-2">
          {line || ' '}
        </Text>
      ));
  };

  return (
    <Box className={className}>
      {/* Templates Panel */}
      {showTemplates && (
        <Card className="mb-4">
          <VStack space="md" className="p-4">
            <HStack className="items-center justify-between">
              <Text className="font-semibold text-gray-900">
                Bio Templates
              </Text>
              <Button
                variant="ghost"
                size="sm"
                onPress={() => setShowTemplatesPanel(!showTemplatesPanel)}
              >
                <ButtonText className="text-blue-600">
                  {showTemplatesPanel ? 'Hide' : 'Show'} Templates
                </ButtonText>
              </Button>
            </HStack>
            
            {showTemplatesPanel && (
              <VStack space="sm">
                {BIO_TEMPLATES.map((template) => (
                  <Card 
                    key={template.id}
                    className={`p-3 border cursor-pointer transition-colors ${
                      selectedTemplate === template.id 
                        ? 'border-blue-300 bg-blue-50' 
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <VStack space="xs">
                      <Text className="font-medium text-gray-900">
                        {template.title}
                      </Text>
                      <Text className="text-sm text-gray-600" numberOfLines={2}>
                        {template.content.substring(0, 120)}...
                      </Text>
                      <HStack className="items-center justify-between mt-2">
                        <Text className="text-xs text-gray-500">
                          ~{template.content.trim().split(/\s+/).length} words
                        </Text>
                        <Button
                          size="sm"
                          variant="outline"
                          onPress={() => applyTemplate(template)}
                        >
                          <ButtonText>Use Template</ButtonText>
                        </Button>
                      </HStack>
                    </VStack>
                  </Card>
                ))}
              </VStack>
            )}
          </VStack>
        </Card>
      )}

      {/* Editor Toolbar */}
      <Card className="mb-2">
        <HStack className="items-center justify-between p-3 border-b border-gray-200">
          <HStack space="xs">
            {Platform.OS === 'web' && (
              <>
                <Button
                  variant="ghost"
                  size="sm"
                  onPress={() => formatText('bold')}
                  className="p-2"
                >
                  <ButtonIcon as={Bold} className="text-gray-600" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onPress={() => formatText('italic')}
                  className="p-2"
                >
                  <ButtonIcon as={Italic} className="text-gray-600" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onPress={() => formatText('quote')}
                  className="p-2"
                >
                  <ButtonIcon as={Quote} className="text-gray-600" />
                </Button>
              </>
            )}
          </HStack>

          <HStack space="xs">
            <Button
              variant="ghost"
              size="sm"
              onPress={() => setIsPreview(!isPreview)}
              className="flex-row items-center"
            >
              <ButtonIcon 
                as={isPreview ? Edit3 : Eye} 
                className="text-gray-600 mr-1" 
              />
              <ButtonText className="text-gray-600">
                {isPreview ? 'Edit' : 'Preview'}
              </ButtonText>
            </Button>
          </HStack>
        </HStack>

        {/* Word Count and Status */}
        <HStack className="items-center justify-between p-3">
          <HStack space="sm" className="items-center">
            <Badge className={wordCountStatus.bg}>
              <BadgeText className={wordCountStatus.color}>
                {wordCount} / {maxWords} words
              </BadgeText>
            </Badge>
            
            {isOverLimit && (
              <HStack space="xs" className="items-center">
                <Icon as={AlertCircle} size={16} className="text-red-500" />
                <Text className="text-sm text-red-600">
                  Reduce by {wordCount - maxWords} words
                </Text>
              </HStack>
            )}
            
            {isUnderMinimum && wordCount > 0 && (
              <HStack space="xs" className="items-center">
                <Icon as={AlertCircle} size={16} className="text-yellow-500" />
                <Text className="text-sm text-yellow-600">
                  Add {minWords - wordCount} more words
                </Text>
              </HStack>
            )}
            
            {!isOverLimit && !isUnderMinimum && wordCount >= minWords && (
              <HStack space="xs" className="items-center">
                <Icon as={CheckCircle2} size={16} className="text-green-500" />
                <Text className="text-sm text-green-600">
                  Perfect length!
                </Text>
              </HStack>
            )}
          </HStack>

          <Text className="text-sm text-gray-500">
            {charCount} characters
          </Text>
        </HStack>
      </Card>

      {/* Editor/Preview Content */}
      <Card>
        <Box className="p-4">
          {isPreview ? (
            <VStack space="md">
              <Text className="font-medium text-gray-900 mb-2">
                Preview:
              </Text>
              <Box className="min-h-48 p-4 bg-gray-50 rounded-lg">
                {value ? renderPreview() : (
                  <Text className="text-gray-500 italic">
                    Nothing to preview yet. Write your bio to see how it looks!
                  </Text>
                )}
              </Box>
            </VStack>
          ) : (
            <VStack space="sm">
              <Text className="font-medium text-gray-900">
                Your Professional Biography
              </Text>
              <Textarea
                id="bio-textarea"
                value={value}
                onChangeText={onChange}
                placeholder={placeholder}
                className={`min-h-48 ${isOverLimit ? 'border-red-300' : ''}`}
                multiline
                numberOfLines={8}
              />
              
              {/* Tips */}
              <Box className="p-3 bg-blue-50 rounded-lg mt-2">
                <Text className="text-sm font-medium text-blue-900 mb-1">
                  💡 Tips for a great bio:
                </Text>
                <VStack space="xs">
                  <Text className="text-sm text-blue-800">
                    • Share your teaching philosophy and approach
                  </Text>
                  <Text className="text-sm text-blue-800">
                    • Highlight your qualifications and experience
                  </Text>
                  <Text className="text-sm text-blue-800">
                    • Mention what makes you unique as an educator
                  </Text>
                  <Text className="text-sm text-blue-800">
                    • Keep it personal and engaging for students
                  </Text>
                </VStack>
              </Box>
            </VStack>
          )}
        </Box>
      </Card>
    </Box>
  );
};