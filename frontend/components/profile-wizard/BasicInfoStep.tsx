import {
  Camera,
  Upload,
  User,
  Mail,
  Phone,
  MapPin,
  Globe,
  AlertCircle,
  CheckCircle2,
  X,
} from 'lucide-react-native';
import React, { useState } from 'react';
import { Platform } from 'react-native';

import { Avatar, AvatarFallbackText, AvatarImage } from '@/components/ui/avatar';
import { Badge, BadgeText } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import {
  FormControl,
  FormControlLabel,
  FormControlHelper,
  FormControlError,
} from '@/components/ui/form-control';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Image } from '@/components/ui/image';
import { Input, InputField } from '@/components/ui/input';
import { ScrollView } from '@/components/ui/scroll-view';
import {
  Select,
  SelectTrigger,
  SelectInput,
  SelectContent,
  SelectItem,
} from '@/components/ui/select';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

interface BasicInfoFormData {
  profile_photo?: string;
  first_name: string;
  last_name: string;
  professional_title: string;
  email: string;
  phone_number: string;
  location: {
    city: string;
    country: string;
    timezone: string;
  };
  languages: string[];
  years_experience: number;
  teaching_level: string;
  introduction: string;
}

interface BasicInfoStepProps {
  formData: BasicInfoFormData;
  onFormDataChange: (data: Partial<BasicInfoFormData>) => void;
  onFieldChange?: (update: { field: keyof BasicInfoFormData; value: any }) => void;
  validationErrors?: Record<string, string[]>;
  isLoading?: boolean;
}

const EXPERIENCE_LEVELS = [
  { value: '0-1', label: 'New Teacher (0-1 years)' },
  { value: '2-5', label: 'Early Career (2-5 years)' },
  { value: '6-10', label: 'Experienced (6-10 years)' },
  { value: '11-15', label: 'Senior (11-15 years)' },
  { value: '16+', label: 'Veteran (16+ years)' },
];

const TEACHING_LEVELS = [
  { value: 'elementary', label: 'Elementary (K-5)' },
  { value: 'middle', label: 'Middle School (6-8)' },
  { value: 'high', label: 'High School (9-12)' },
  { value: 'university', label: 'University Level' },
  { value: 'adult', label: 'Adult Education' },
  { value: 'all', label: 'All Levels' },
];

const COMMON_LANGUAGES = [
  'Portuguese',
  'English',
  'Spanish',
  'French',
  'German',
  'Italian',
  'Chinese',
  'Japanese',
];

const TIMEZONES = [
  'Europe/Lisbon',
  'Europe/London',
  'Europe/Madrid',
  'Europe/Paris',
  'America/New_York',
  'America/Los_Angeles',
  'America/Sao_Paulo',
  'Asia/Tokyo',
  'Asia/Shanghai',
  'Australia/Sydney',
];

export const BasicInfoStep: React.FC<BasicInfoStepProps> = ({
  formData,
  onFormDataChange,
  validationErrors = {},
  isLoading = false,
}) => {
  const [showLanguageInput, setShowLanguageInput] = useState(false);
  const [newLanguage, setNewLanguage] = useState('');

  const handleFieldChange = (field: string, value: any) => {
    if (field.includes('.')) {
      // Handle nested fields like location.city
      const [parent, child] = field.split('.');
      onFormDataChange({
        [parent]: {
          ...formData[parent as keyof BasicInfoFormData],
          [child]: value,
        },
      });
    } else {
      onFormDataChange({ [field]: value });
    }
  };

  const handleImageUpload = async () => {
    // This would integrate with image picker/camera
    // For now, just a placeholder
    if (__DEV__) {
      console.log('Image upload triggered');
    }
  };

  const addLanguage = (language: string) => {
    if (language && !formData.languages.includes(language)) {
      handleFieldChange('languages', [...formData.languages, language]);
    }
    setNewLanguage('');
    setShowLanguageInput(false);
  };

  const removeLanguage = (language: string) => {
    handleFieldChange(
      'languages',
      formData.languages.filter(l => l !== language),
    );
  };

  const getFieldError = (fieldName: string): string | undefined => {
    return validationErrors[fieldName]?.[0];
  };

  const hasFieldError = (fieldName: string): boolean => {
    return !!validationErrors[fieldName]?.length;
  };

  return (
    <ScrollView className="flex-1">
      <Box className="p-6 max-w-2xl mx-auto">
        <VStack space="lg">
          {/* Header */}
          <VStack space="sm">
            <Heading size="xl" className="text-gray-900">
              Basic Information
            </Heading>
            <Text className="text-gray-600">
              Start by adding your essential profile information. This helps students get to know
              you better.
            </Text>
          </VStack>

          {/* Profile Photo Section */}
          <Card>
            <VStack space="md" className="p-6">
              <Heading size="md" className="text-gray-900">
                Profile Photo
              </Heading>

              <HStack space="md" className="items-center">
                <Box className="relative">
                  <Avatar size="xl">
                    {formData.profile_photo ? (
                      <AvatarImage source={{ uri: formData.profile_photo }} alt="Profile photo" />
                    ) : (
                      <AvatarFallbackText>
                        {`${formData.first_name || 'F'} ${formData.last_name || 'L'}`}
                      </AvatarFallbackText>
                    )}
                  </Avatar>

                  <Button
                    size="sm"
                    className="absolute -bottom-2 -right-2 bg-blue-600 rounded-full w-8 h-8"
                    onPress={handleImageUpload}
                  >
                    <ButtonIcon as={Camera} className="text-white" size={16} />
                  </Button>
                </Box>

                <VStack space="xs" className="flex-1">
                  <Text className="font-medium text-gray-900">Add a professional photo</Text>
                  <Text className="text-sm text-gray-600">
                    Students are more likely to book with teachers who have clear, professional
                    photos.
                  </Text>
                  <Button
                    variant="outline"
                    size="sm"
                    onPress={handleImageUpload}
                    className="self-start mt-2"
                  >
                    <ButtonIcon as={Upload} className="text-gray-600 mr-2" />
                    <ButtonText>Upload Photo</ButtonText>
                  </Button>
                </VStack>
              </HStack>
            </VStack>
          </Card>

          {/* Personal Information */}
          <Card>
            <VStack space="md" className="p-6">
              <Heading size="md" className="text-gray-900">
                Personal Information
              </Heading>

              <HStack space="md">
                <VStack className="flex-1">
                  <FormControl isInvalid={hasFieldError('first_name')}>
                    <FormControlLabel>
                      <Text>First Name *</Text>
                    </FormControlLabel>
                    <Input>
                      <InputField
                        value={formData.first_name}
                        onChangeText={value => handleFieldChange('first_name', value)}
                        placeholder="Your first name"
                        isDisabled={isLoading}
                      />
                    </Input>
                    {hasFieldError('first_name') && (
                      <FormControlError>
                        <Text>{getFieldError('first_name')}</Text>
                      </FormControlError>
                    )}
                  </FormControl>
                </VStack>

                <VStack className="flex-1">
                  <FormControl isInvalid={hasFieldError('last_name')}>
                    <FormControlLabel>
                      <Text>Last Name *</Text>
                    </FormControlLabel>
                    <Input>
                      <InputField
                        value={formData.last_name}
                        onChangeText={value => handleFieldChange('last_name', value)}
                        placeholder="Your last name"
                        isDisabled={isLoading}
                      />
                    </Input>
                    {hasFieldError('last_name') && (
                      <FormControlError>
                        <Text>{getFieldError('last_name')}</Text>
                      </FormControlError>
                    )}
                  </FormControl>
                </VStack>
              </HStack>

              <FormControl isInvalid={hasFieldError('professional_title')}>
                <FormControlLabel>
                  <Text>Professional Title *</Text>
                </FormControlLabel>
                <Input>
                  <InputField
                    value={formData.professional_title}
                    onChangeText={value => handleFieldChange('professional_title', value)}
                    placeholder="e.g., Mathematics Teacher, English Tutor, Science Educator"
                    isDisabled={isLoading}
                  />
                </Input>
                <FormControlHelper>
                  <Text>This appears as your main title on your profile</Text>
                </FormControlHelper>
                {hasFieldError('professional_title') && (
                  <FormControlError>
                    <Text>{getFieldError('professional_title')}</Text>
                  </FormControlError>
                )}
              </FormControl>
            </VStack>
          </Card>

          {/* Contact Information */}
          <Card>
            <VStack space="md" className="p-6">
              <Heading size="md" className="text-gray-900">
                Contact Information
              </Heading>

              <FormControl isInvalid={hasFieldError('email')}>
                <FormControlLabel>
                  <Text>Email Address *</Text>
                </FormControlLabel>
                <Input>
                  <InputField
                    value={formData.email}
                    onChangeText={value => handleFieldChange('email', value)}
                    placeholder="your.email@example.com"
                    keyboardType="email-address"
                    autoCapitalize="none"
                    isDisabled={isLoading}
                  />
                </Input>
                {hasFieldError('email') && (
                  <FormControlError>
                    <Text>{getFieldError('email')}</Text>
                  </FormControlError>
                )}
              </FormControl>

              <FormControl isInvalid={hasFieldError('phone_number')}>
                <FormControlLabel>
                  <Text>Phone Number</Text>
                </FormControlLabel>
                <Input>
                  <InputField
                    value={formData.phone_number}
                    onChangeText={value => handleFieldChange('phone_number', value)}
                    placeholder="+1 (555) 123-4567"
                    keyboardType="phone-pad"
                    isDisabled={isLoading}
                  />
                </Input>
                <FormControlHelper>
                  <Text>Optional - for direct communication with students</Text>
                </FormControlHelper>
                {hasFieldError('phone_number') && (
                  <FormControlError>
                    <Text>{getFieldError('phone_number')}</Text>
                  </FormControlError>
                )}
              </FormControl>
            </VStack>
          </Card>

          {/* Location Information */}
          <Card>
            <VStack space="md" className="p-6">
              <Heading size="md" className="text-gray-900">
                Location & Timezone
              </Heading>

              <HStack space="md">
                <VStack className="flex-1">
                  <FormControl isInvalid={hasFieldError('location.city')}>
                    <FormControlLabel>
                      <Text>City *</Text>
                    </FormControlLabel>
                    <Input>
                      <InputField
                        value={formData.location?.city || ''}
                        onChangeText={value => handleFieldChange('location.city', value)}
                        placeholder="Your city"
                        isDisabled={isLoading}
                      />
                    </Input>
                    {hasFieldError('location.city') && (
                      <FormControlError>
                        <Text>{getFieldError('location.city')}</Text>
                      </FormControlError>
                    )}
                  </FormControl>
                </VStack>

                <VStack className="flex-1">
                  <FormControl isInvalid={hasFieldError('location.country')}>
                    <FormControlLabel>
                      <Text>Country *</Text>
                    </FormControlLabel>
                    <Input>
                      <InputField
                        value={formData.location?.country || ''}
                        onChangeText={value => handleFieldChange('location.country', value)}
                        placeholder="Your country"
                        isDisabled={isLoading}
                      />
                    </Input>
                    {hasFieldError('location.country') && (
                      <FormControlError>
                        <Text>{getFieldError('location.country')}</Text>
                      </FormControlError>
                    )}
                  </FormControl>
                </VStack>
              </HStack>

              <FormControl isInvalid={hasFieldError('location.timezone')}>
                <FormControlLabel>
                  <Text>Timezone *</Text>
                </FormControlLabel>
                <Select
                  selectedValue={formData.location?.timezone || ''}
                  onValueChange={value => handleFieldChange('location.timezone', value)}
                  isDisabled={isLoading}
                >
                  <SelectTrigger>
                    <SelectInput placeholder="Select your timezone" />
                  </SelectTrigger>
                  <SelectContent>
                    {TIMEZONES.map(timezone => (
                      <SelectItem key={timezone} label={timezone} value={timezone} />
                    ))}
                  </SelectContent>
                </Select>
                <FormControlHelper>
                  <Text>This helps students book sessions at the right time</Text>
                </FormControlHelper>
                {hasFieldError('location.timezone') && (
                  <FormControlError>
                    <Text>{getFieldError('location.timezone')}</Text>
                  </FormControlError>
                )}
              </FormControl>
            </VStack>
          </Card>

          {/* Languages */}
          <Card>
            <VStack space="md" className="p-6">
              <HStack className="items-center justify-between">
                <Heading size="md" className="text-gray-900">
                  Languages Spoken
                </Heading>
                <Button variant="outline" size="sm" onPress={() => setShowLanguageInput(true)}>
                  <ButtonText>Add Language</ButtonText>
                </Button>
              </HStack>

              {formData.languages.length > 0 && (
                <HStack space="xs" className="flex-wrap">
                  {formData.languages.map(language => (
                    <Badge key={language} className="bg-blue-100 mb-2">
                      <BadgeText className="text-blue-800">{language}</BadgeText>
                      <Button
                        size="xs"
                        variant="ghost"
                        onPress={() => removeLanguage(language)}
                        className="ml-1 p-0 w-4 h-4"
                      >
                        <ButtonIcon as={X} size={12} className="text-blue-600" />
                      </Button>
                    </Badge>
                  ))}
                </HStack>
              )}

              {showLanguageInput && (
                <VStack space="sm">
                  <Text className="text-sm font-medium text-gray-700">Common Languages:</Text>
                  <HStack space="xs" className="flex-wrap">
                    {COMMON_LANGUAGES.filter(lang => !formData.languages.includes(lang)).map(
                      language => (
                        <Button
                          key={language}
                          variant="outline"
                          size="sm"
                          onPress={() => addLanguage(language)}
                          className="mb-2"
                        >
                          <ButtonText>{language}</ButtonText>
                        </Button>
                      ),
                    )}
                  </HStack>

                  <HStack space="sm">
                    <VStack className="flex-1">
                      <Input>
                        <InputField
                          value={newLanguage}
                          onChangeText={setNewLanguage}
                          placeholder="Or type a language"
                        />
                      </Input>
                    </VStack>
                    <Button
                      onPress={() => addLanguage(newLanguage)}
                      isDisabled={!newLanguage.trim()}
                    >
                      <ButtonText>Add</ButtonText>
                    </Button>
                  </HStack>

                  <Button variant="ghost" size="sm" onPress={() => setShowLanguageInput(false)}>
                    <ButtonText>Done</ButtonText>
                  </Button>
                </VStack>
              )}
            </VStack>
          </Card>

          {/* Teaching Experience */}
          <Card>
            <VStack space="md" className="p-6">
              <Heading size="md" className="text-gray-900">
                Teaching Experience
              </Heading>

              <HStack space="md">
                <VStack className="flex-1">
                  <FormControl isInvalid={hasFieldError('years_experience')}>
                    <FormControlLabel>
                      <Text>Years of Experience *</Text>
                    </FormControlLabel>
                    <Select
                      selectedValue={formData.years_experience?.toString() || ''}
                      onValueChange={value =>
                        handleFieldChange('years_experience', parseInt(value))
                      }
                      isDisabled={isLoading}
                    >
                      <SelectTrigger>
                        <SelectInput placeholder="Select experience level" />
                      </SelectTrigger>
                      <SelectContent>
                        {EXPERIENCE_LEVELS.map(level => (
                          <SelectItem key={level.value} label={level.label} value={level.value} />
                        ))}
                      </SelectContent>
                    </Select>
                    {hasFieldError('years_experience') && (
                      <FormControlError>
                        <Text>{getFieldError('years_experience')}</Text>
                      </FormControlError>
                    )}
                  </FormControl>
                </VStack>

                <VStack className="flex-1">
                  <FormControl isInvalid={hasFieldError('teaching_level')}>
                    <FormControlLabel>
                      <Text>Primary Teaching Level *</Text>
                    </FormControlLabel>
                    <Select
                      selectedValue={formData.teaching_level || ''}
                      onValueChange={value => handleFieldChange('teaching_level', value)}
                      isDisabled={isLoading}
                    >
                      <SelectTrigger>
                        <SelectInput placeholder="Select teaching level" />
                      </SelectTrigger>
                      <SelectContent>
                        {TEACHING_LEVELS.map(level => (
                          <SelectItem key={level.value} label={level.label} value={level.value} />
                        ))}
                      </SelectContent>
                    </Select>
                    {hasFieldError('teaching_level') && (
                      <FormControlError>
                        <Text>{getFieldError('teaching_level')}</Text>
                      </FormControlError>
                    )}
                  </FormControl>
                </VStack>
              </HStack>
            </VStack>
          </Card>

          {/* Brief Introduction */}
          <Card>
            <VStack space="md" className="p-6">
              <Heading size="md" className="text-gray-900">
                Brief Introduction
              </Heading>

              <FormControl isInvalid={hasFieldError('introduction')}>
                <FormControlLabel>
                  <Text>One-line introduction *</Text>
                </FormControlLabel>
                <Input>
                  <InputField
                    value={formData.introduction}
                    onChangeText={value => handleFieldChange('introduction', value)}
                    placeholder="e.g., Passionate math teacher with 5 years experience helping students excel"
                    multiline
                    numberOfLines={2}
                    isDisabled={isLoading}
                  />
                </Input>
                <FormControlHelper>
                  <Text>This appears as a preview on your profile card (max 120 characters)</Text>
                </FormControlHelper>
                {hasFieldError('introduction') && (
                  <FormControlError>
                    <Text>{getFieldError('introduction')}</Text>
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
