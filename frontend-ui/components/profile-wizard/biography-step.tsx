import React, { useState } from 'react';
import { Lightbulb, Users, Target, Sparkles, BookOpen, Heart, X, CheckCircle2 } from 'lucide-react-native';

import { Box } from '@/components/ui/box';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { FormControl, FormControlLabel, FormControlHelper, FormControlError } from '@/components/ui/form-control';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Input, InputField } from '@/components/ui/input';
import { ScrollView } from '@/components/ui/scroll-view';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { Badge, BadgeText } from '@/components/ui/badge';

import { BioEditor } from '@/components/editors/bio-editor';

interface BiographyFormData {
  professional_bio: string;
  teaching_philosophy: string;
  specializations: string[];
  achievements: string[];
  teaching_approach: string;
  student_outcomes: string;
}

interface BiographyStepProps {
  formData: BiographyFormData;
  onFormDataChange: (data: Partial<BiographyFormData>) => void;
  validationErrors?: Record<string, string[]>;
  isLoading?: boolean;
}

const TEACHING_APPROACHES = [
  { 
    id: 'interactive', 
    label: 'Interactive Learning', 
    description: 'Engaging students through hands-on activities and discussions',
    icon: Users 
  },
  { 
    id: 'personalized', 
    label: 'Personalized Instruction', 
    description: 'Adapting lessons to individual learning styles and needs',
    icon: Target 
  },
  { 
    id: 'creative', 
    label: 'Creative Teaching', 
    description: 'Using innovative methods to make learning fun and memorable',
    icon: Sparkles 
  },
  { 
    id: 'structured', 
    label: 'Structured Learning', 
    description: 'Clear objectives, step-by-step progression, and regular assessments',
    icon: BookOpen 
  },
  { 
    id: 'supportive', 
    label: 'Supportive Environment', 
    description: 'Building confidence and providing emotional support for learning',
    icon: Heart 
  },
];

const COMMON_SPECIALIZATIONS = [
  'Exam Preparation', 'Test Prep', 'Homework Help', 'Advanced Placement',
  'IB Program', 'Special Needs', 'ESL/EFL', 'Adult Learning',
  'Online Teaching', 'Group Classes', 'One-on-One Tutoring',
  'Curriculum Development', 'Assessment Design', 'Learning Disabilities'
];

export const BiographyStep: React.FC<BiographyStepProps> = ({
  formData,
  onFormDataChange,
  validationErrors = {},
  isLoading = false,
}) => {
  const [showSpecializationInput, setShowSpecializationInput] = useState(false);
  const [newSpecialization, setNewSpecialization] = useState('');
  const [showAchievementInput, setShowAchievementInput] = useState(false);
  const [newAchievement, setNewAchievement] = useState('');

  const handleFieldChange = (field: string, value: any) => {
    onFormDataChange({ [field]: value });
  };

  const addSpecialization = (specialization: string) => {
    if (specialization && !formData.specializations.includes(specialization)) {
      handleFieldChange('specializations', [...formData.specializations, specialization]);
    }
    setNewSpecialization('');
    setShowSpecializationInput(false);
  };

  const removeSpecialization = (specialization: string) => {
    handleFieldChange('specializations', formData.specializations.filter(s => s !== specialization));
  };

  const addAchievement = (achievement: string) => {
    if (achievement.trim()) {
      handleFieldChange('achievements', [...formData.achievements, achievement.trim()]);
    }
    setNewAchievement('');
    setShowAchievementInput(false);
  };

  const removeAchievement = (index: number) => {
    const newAchievements = [...formData.achievements];
    newAchievements.splice(index, 1);
    handleFieldChange('achievements', newAchievements);
  };

  const toggleTeachingApproach = (approach: string) => {
    handleFieldChange('teaching_approach', approach);
  };

  const getFieldError = (fieldName: string): string | undefined => {
    return validationErrors[fieldName]?.[0];
  };

  const hasFieldError = (fieldName: string): boolean => {
    return !!validationErrors[fieldName]?.length;
  };

  const wordCount = formData.professional_bio ? formData.professional_bio.trim().split(/\s+/).length : 0;

  return (
    <ScrollView className="flex-1">
      <Box className="p-6 max-w-3xl mx-auto">
        <VStack space="lg">
          {/* Header */}
          <VStack space="sm">
            <Heading size="xl" className="text-gray-900">
              Professional Biography
            </Heading>
            <Text className="text-gray-600">
              Tell your story! Help students understand who you are as an educator and what makes you unique.
            </Text>
          </VStack>

          {/* Professional Bio Editor */}
          <Card>
            <VStack space="md" className="p-6">
              <HStack className="items-center justify-between">
                <Heading size="md" className="text-gray-900">
                  Your Teaching Story
                </Heading>
                <Badge className={`${
                  wordCount < 50 ? 'bg-red-100' :
                  wordCount > 500 ? 'bg-red-100' :
                  wordCount > 400 ? 'bg-yellow-100' :
                  'bg-green-100'
                }`}>
                  <BadgeText className={`${
                    wordCount < 50 ? 'text-red-700' :
                    wordCount > 500 ? 'text-red-700' :
                    wordCount > 400 ? 'text-yellow-700' :
                    'text-green-700'
                  }`}>
                    {wordCount} / 500 words
                  </BadgeText>
                </Badge>
              </HStack>

              <FormControl isInvalid={hasFieldError('professional_bio')}>
                <BioEditor
                  value={formData.professional_bio}
                  onChange={(value) => handleFieldChange('professional_bio', value)}
                  maxWords={500}
                  minWords={50}
                  showTemplates={true}
                />
                {hasFieldError('professional_bio') && (
                  <FormControlError>
                    <Text>{getFieldError('professional_bio')}</Text>
                  </FormControlError>
                )}
              </FormControl>
            </VStack>
          </Card>

          {/* Teaching Philosophy */}
          <Card>
            <VStack space="md" className="p-6">
              <HStack space="sm" className="items-center">
                <Icon as={Lightbulb} size={20} className="text-yellow-600" />
                <Heading size="md" className="text-gray-900">
                  Teaching Philosophy
                </Heading>
              </HStack>
              
              <Text className="text-gray-600">
                What drives you as an educator? What do you believe about learning?
              </Text>

              <FormControl isInvalid={hasFieldError('teaching_philosophy')}>
                <FormControlLabel>
                  <Text>Your Teaching Philosophy</Text>
                </FormControlLabel>
                <Box className="bg-gray-50 rounded-lg p-4">
                  <Text className="text-sm text-gray-700 mb-3">
                    💡 Consider addressing these questions:
                  </Text>
                  <VStack space="xs">
                    <Text className="text-sm text-gray-600">• What do you believe about how students learn best?</Text>
                    <Text className="text-sm text-gray-600">• How do you create an effective learning environment?</Text>
                    <Text className="text-sm text-gray-600">• What role do you play in your students' success?</Text>
                    <Text className="text-sm text-gray-600">• How do you handle different learning styles?</Text>
                  </VStack>
                </Box>
                <Input>
                  <InputField
                    value={formData.teaching_philosophy}
                    onChangeText={(value) => handleFieldChange('teaching_philosophy', value)}
                    placeholder="e.g., I believe every student has unique potential that can be unlocked through personalized, patient guidance and creating a safe space for exploration..."
                    multiline
                    numberOfLines={4}
                    isDisabled={isLoading}
                  />
                </Input>
                <FormControlHelper>
                  <Text>Share your core beliefs about teaching and learning (2-3 sentences)</Text>
                </FormControlHelper>
                {hasFieldError('teaching_philosophy') && (
                  <FormControlError>
                    <Text>{getFieldError('teaching_philosophy')}</Text>
                  </FormControlError>
                )}
              </FormControl>
            </VStack>
          </Card>

          {/* Teaching Approach */}
          <Card>
            <VStack space="md" className="p-6">
              <Heading size="md" className="text-gray-900">
                Teaching Approach
              </Heading>
              
              <Text className="text-gray-600">
                Select the approach that best describes your teaching style:
              </Text>

              <VStack space="sm">
                {TEACHING_APPROACHES.map((approach) => (
                  <Button
                    key={approach.id}
                    variant={formData.teaching_approach === approach.id ? "solid" : "outline"}
                    onPress={() => toggleTeachingApproach(approach.id)}
                    className={`p-4 ${
                      formData.teaching_approach === approach.id 
                        ? 'bg-blue-600 border-blue-600' 
                        : 'bg-white border-gray-200 hover:border-blue-300'
                    }`}
                  >
                    <HStack space="sm" className="items-center w-full">
                      <Icon 
                        as={approach.icon} 
                        size={20} 
                        className={formData.teaching_approach === approach.id ? 'text-white' : 'text-blue-600'} 
                      />
                      <VStack className="flex-1 items-start">
                        <Text className={`font-medium ${
                          formData.teaching_approach === approach.id ? 'text-white' : 'text-gray-900'
                        }`}>
                          {approach.label}
                        </Text>
                        <Text className={`text-sm ${
                          formData.teaching_approach === approach.id ? 'text-blue-100' : 'text-gray-600'
                        }`}>
                          {approach.description}
                        </Text>
                      </VStack>
                    </HStack>
                  </Button>
                ))}
              </VStack>
            </VStack>
          </Card>

          {/* Specializations */}
          <Card>
            <VStack space="md" className="p-6">
              <HStack className="items-center justify-between">
                <Heading size="md" className="text-gray-900">
                  Specializations & Areas of Expertise
                </Heading>
                <Button
                  variant="outline"
                  size="sm"
                  onPress={() => setShowSpecializationInput(true)}
                >
                  <ButtonText>Add Specialization</ButtonText>
                </Button>
              </HStack>
              
              <Text className="text-gray-600">
                What specific areas do you excel in? This helps students find you for their specific needs.
              </Text>

              {formData.specializations.length > 0 && (
                <HStack space="xs" className="flex-wrap">
                  {formData.specializations.map((spec) => (
                    <Badge key={spec} className="bg-blue-100 mb-2">
                      <BadgeText className="text-blue-800">{spec}</BadgeText>
                      <Button
                        size="xs"
                        variant="ghost"
                        onPress={() => removeSpecialization(spec)}
                        className="ml-1 p-0 w-4 h-4"
                      >
                        <ButtonIcon as={X} size={12} className="text-blue-600" />
                      </Button>
                    </Badge>
                  ))}
                </HStack>
              )}

              {showSpecializationInput && (
                <VStack space="sm">
                  <Text className="text-sm font-medium text-gray-700">
                    Common Specializations:
                  </Text>
                  <HStack space="xs" className="flex-wrap">
                    {COMMON_SPECIALIZATIONS
                      .filter(spec => !formData.specializations.includes(spec))
                      .map((spec) => (
                        <Button
                          key={spec}
                          variant="outline"
                          size="sm"
                          onPress={() => addSpecialization(spec)}
                          className="mb-2"
                        >
                          <ButtonText>{spec}</ButtonText>
                        </Button>
                      ))}
                  </HStack>
                  
                  <HStack space="sm">
                    <VStack className="flex-1">
                      <Input>
                        <InputField
                          value={newSpecialization}
                          onChangeText={setNewSpecialization}
                          placeholder="Or type a custom specialization"
                        />
                      </Input>
                    </VStack>
                    <Button
                      onPress={() => addSpecialization(newSpecialization)}
                      isDisabled={!newSpecialization.trim()}
                    >
                      <ButtonText>Add</ButtonText>
                    </Button>
                  </HStack>
                  
                  <Button
                    variant="ghost"
                    size="sm"
                    onPress={() => setShowSpecializationInput(false)}
                  >
                    <ButtonText>Done</ButtonText>
                  </Button>
                </VStack>
              )}
            </VStack>
          </Card>

          {/* Achievements & Recognition */}
          <Card>
            <VStack space="md" className="p-6">
              <HStack className="items-center justify-between">
                <Heading size="md" className="text-gray-900">
                  Achievements & Recognition
                </Heading>
                <Button
                  variant="outline"
                  size="sm"
                  onPress={() => setShowAchievementInput(true)}
                >
                  <ButtonText>Add Achievement</ButtonText>
                </Button>
              </HStack>
              
              <Text className="text-gray-600">
                Share any awards, certifications, or notable accomplishments that demonstrate your expertise.
              </Text>

              {formData.achievements.length > 0 && (
                <VStack space="sm">
                  {formData.achievements.map((achievement, index) => (
                    <HStack key={index} space="sm" className="items-start p-3 bg-green-50 rounded-lg">
                      <Icon as={CheckCircle2} size={16} className="text-green-600 mt-0.5" />
                      <Text className="flex-1 text-green-800">{achievement}</Text>
                      <Button
                        size="xs"
                        variant="ghost"
                        onPress={() => removeAchievement(index)}
                        className="p-1"
                      >
                        <ButtonIcon as={X} size={12} className="text-green-600" />
                      </Button>
                    </HStack>
                  ))}
                </VStack>
              )}

              {showAchievementInput && (
                <VStack space="sm">
                  <Box className="p-3 bg-blue-50 rounded-lg">
                    <Text className="text-sm font-medium text-blue-900 mb-2">
                      💡 Examples of achievements:
                    </Text>
                    <VStack space="xs">
                      <Text className="text-sm text-blue-800">• Teacher of the Year Award (2023)</Text>
                      <Text className="text-sm text-blue-800">• 95% of students improved by at least one grade level</Text>
                      <Text className="text-sm text-blue-800">• Certified in [Specific Teaching Method]</Text>
                      <Text className="text-sm text-blue-800">• Published researcher in educational methodology</Text>
                    </VStack>
                  </Box>
                  
                  <HStack space="sm">
                    <VStack className="flex-1">
                      <Input>
                        <InputField
                          value={newAchievement}
                          onChangeText={setNewAchievement}
                          placeholder="Describe an achievement or recognition"
                          multiline
                          numberOfLines={2}
                        />
                      </Input>
                    </VStack>
                    <Button
                      onPress={() => addAchievement(newAchievement)}
                      isDisabled={!newAchievement.trim()}
                    >
                      <ButtonText>Add</ButtonText>
                    </Button>
                  </HStack>
                  
                  <Button
                    variant="ghost"
                    size="sm"
                    onPress={() => setShowAchievementInput(false)}
                  >
                    <ButtonText>Done</ButtonText>
                  </Button>
                </VStack>
              )}
            </VStack>
          </Card>

          {/* Student Outcomes */}
          <Card>
            <VStack space="md" className="p-6">
              <Heading size="md" className="text-gray-900">
                Student Success Stories
              </Heading>
              
              <Text className="text-gray-600">
                What kind of results do your students typically achieve? Share some success stories (without naming specific students).
              </Text>

              <FormControl isInvalid={hasFieldError('student_outcomes')}>
                <Box className="bg-yellow-50 rounded-lg p-4 mb-3">
                  <Text className="text-sm font-medium text-yellow-900 mb-2">
                    💡 Examples of student outcomes:
                  </Text>
                  <VStack space="xs">
                    <Text className="text-sm text-yellow-800">• "Students typically improve their grades by 1-2 letter grades within 3 months"</Text>
                    <Text className="text-sm text-yellow-800">• "Helped 20+ students gain acceptance into their top-choice universities"</Text>
                    <Text className="text-sm text-yellow-800">• "85% of my SAT prep students improved their scores by 200+ points"</Text>
                  </VStack>
                </Box>
                
                <Input>
                  <InputField
                    value={formData.student_outcomes}
                    onChangeText={(value) => handleFieldChange('student_outcomes', value)}
                    placeholder="Share some typical outcomes your students achieve..."
                    multiline
                    numberOfLines={3}
                    isDisabled={isLoading}
                  />
                </Input>
                <FormControlHelper>
                  <Text>Focus on measurable results and positive transformations</Text>
                </FormControlHelper>
                {hasFieldError('student_outcomes') && (
                  <FormControlError>
                    <Text>{getFieldError('student_outcomes')}</Text>
                  </FormControlError>
                )}
              </FormControl>
            </VStack>
          </Card>
        </VStack>
      </Box>
    </ScrollView>
  );
};