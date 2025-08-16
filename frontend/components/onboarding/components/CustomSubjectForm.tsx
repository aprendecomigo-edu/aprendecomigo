import React, { useState } from 'react';

import { RateInputField } from './RateInputField';

import { CustomSubject } from '../hooks/useCourseManager';

import {
  AlertDialog,
  AlertDialogBackdrop,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogBody,
  AlertDialogFooter,
} from '@/components/ui/alert-dialog';
import { Button, ButtonText } from '@/components/ui/button';
import {
  FormControl,
  FormControlLabel,
  FormControlLabelText,
  FormControlError,
  FormControlErrorText,
} from '@/components/ui/form-control';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Input, InputField } from '@/components/ui/input';
import { Pressable } from '@/components/ui/pressable';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

interface CustomSubjectFormProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (subject: Omit<CustomSubject, 'id' | 'priority_order'>) => void;
  defaultRate: number;
  currency: string;
}

export const CustomSubjectForm: React.FC<CustomSubjectFormProps> = ({
  isOpen,
  onClose,
  onSubmit,
  defaultRate,
  currency,
}) => {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    subject_area: '',
    grade_levels: [] as string[],
    hourly_rate: defaultRate,
    is_featured: false,
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const subjectAreas = [
    'Mathematics',
    'Sciences',
    'Languages',
    'Arts',
    'Technology',
    'Social Studies',
    'Music',
    'Sports',
    'Life Skills',
    'Other',
  ];

  const gradeLevels = [
    'Elementary',
    'Middle School',
    'High School',
    'University',
    'Adult Education',
    'Professional Development',
  ];

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Subject name is required';
    }

    if (!formData.subject_area) {
      newErrors.subject_area = 'Subject area is required';
    }

    if (formData.grade_levels.length === 0) {
      newErrors.grade_levels = 'At least one grade level is required';
    }

    if (formData.hourly_rate <= 0) {
      newErrors.hourly_rate = 'Rate must be greater than 0';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = () => {
    if (validateForm()) {
      onSubmit(formData);
      setFormData({
        name: '',
        description: '',
        subject_area: '',
        grade_levels: [],
        hourly_rate: defaultRate,
        is_featured: false,
      });
      onClose();
    }
  };

  const handleClose = () => {
    setFormData({
      name: '',
      description: '',
      subject_area: '',
      grade_levels: [],
      hourly_rate: defaultRate,
      is_featured: false,
    });
    setErrors({});
    onClose();
  };

  return (
    <AlertDialog isOpen={isOpen} onClose={handleClose} size="lg">
      <AlertDialogBackdrop />
      <AlertDialogContent className="max-w-2xl">
        <AlertDialogHeader className="border-b border-gray-200">
          <Heading size="lg" className="text-gray-900">
            Add Custom Subject
          </Heading>
        </AlertDialogHeader>

        <AlertDialogBody className="py-6">
          <VStack space="lg">
            <FormControl isInvalid={!!errors.name}>
              <FormControlLabel>
                <FormControlLabelText>Subject Name</FormControlLabelText>
              </FormControlLabel>
              <Input>
                <InputField
                  value={formData.name}
                  onChangeText={text => setFormData(prev => ({ ...prev, name: text }))}
                  placeholder="e.g., Advanced Piano, Web Development, Creative Writing"
                />
              </Input>
              {errors.name && (
                <FormControlError>
                  <FormControlErrorText>{errors.name}</FormControlErrorText>
                </FormControlError>
              )}
            </FormControl>

            <FormControl>
              <FormControlLabel>
                <FormControlLabelText>Description (Optional)</FormControlLabelText>
              </FormControlLabel>
              <Input>
                <InputField
                  value={formData.description}
                  onChangeText={text => setFormData(prev => ({ ...prev, description: text }))}
                  placeholder="Brief description of what you'll teach"
                  multiline
                  numberOfLines={3}
                />
              </Input>
            </FormControl>

            <FormControl isInvalid={!!errors.subject_area}>
              <FormControlLabel>
                <FormControlLabelText>Subject Area</FormControlLabelText>
              </FormControlLabel>
              <VStack space="sm">
                <HStack space="xs" className="flex-wrap">
                  {subjectAreas.map(area => (
                    <Pressable
                      key={area}
                      onPress={() => setFormData(prev => ({ ...prev, subject_area: area }))}
                      className={`px-3 py-2 rounded-md border ${
                        formData.subject_area === area
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 bg-white'
                      }`}
                    >
                      <Text
                        className={`text-sm ${
                          formData.subject_area === area ? 'text-blue-700' : 'text-gray-600'
                        }`}
                      >
                        {area}
                      </Text>
                    </Pressable>
                  ))}
                </HStack>
              </VStack>
              {errors.subject_area && (
                <FormControlError>
                  <FormControlErrorText>{errors.subject_area}</FormControlErrorText>
                </FormControlError>
              )}
            </FormControl>

            <FormControl isInvalid={!!errors.grade_levels}>
              <FormControlLabel>
                <FormControlLabelText>Grade Levels</FormControlLabelText>
              </FormControlLabel>
              <VStack space="sm">
                <HStack space="xs" className="flex-wrap">
                  {gradeLevels.map(level => (
                    <Pressable
                      key={level}
                      onPress={() => {
                        setFormData(prev => ({
                          ...prev,
                          grade_levels: prev.grade_levels.includes(level)
                            ? prev.grade_levels.filter(l => l !== level)
                            : [...prev.grade_levels, level],
                        }));
                      }}
                      className={`px-3 py-2 rounded-md border ${
                        formData.grade_levels.includes(level)
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 bg-white'
                      }`}
                    >
                      <Text
                        className={`text-sm ${
                          formData.grade_levels.includes(level) ? 'text-blue-700' : 'text-gray-600'
                        }`}
                      >
                        {level}
                      </Text>
                    </Pressable>
                  ))}
                </HStack>
              </VStack>
              {errors.grade_levels && (
                <FormControlError>
                  <FormControlErrorText>{errors.grade_levels}</FormControlErrorText>
                </FormControlError>
              )}
            </FormControl>

            <FormControl isInvalid={!!errors.hourly_rate}>
              <FormControlLabel>
                <FormControlLabelText>Hourly Rate</FormControlLabelText>
              </FormControlLabel>
              <RateInputField
                value={formData.hourly_rate}
                onChange={rate => setFormData(prev => ({ ...prev, hourly_rate: rate }))}
                currency={currency}
                error={errors.hourly_rate}
              />
            </FormControl>
          </VStack>
        </AlertDialogBody>

        <AlertDialogFooter className="border-t border-gray-200">
          <HStack space="sm" className="w-full justify-end">
            <Button variant="outline" onPress={handleClose}>
              <ButtonText>Cancel</ButtonText>
            </Button>
            <Button onPress={handleSubmit} className="bg-blue-600">
              <ButtonText className="text-white">Add Subject</ButtonText>
            </Button>
          </HStack>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
};