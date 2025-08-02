import {
  Plus,
  Minus,
  DollarSign,
  ChevronDown,
  ChevronUp,
  Star,
  TrendingUp,
  Users,
  AlertCircle,
  Info,
  Trash2,
  GripVertical,
  BookOpen,
} from 'lucide-react-native';
import React, { useState, useEffect, useMemo } from 'react';
import { Platform } from 'react-native';

import { CourseCatalogBrowser } from './course-catalog-browser';

import { EnhancedCourse } from '@/api/tutorApi';
import {
  AlertDialog,
  AlertDialogBackdrop,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogBody,
  AlertDialogFooter,
} from '@/components/ui/alert-dialog';
import { Badge, BadgeText } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import {
  FormControl,
  FormControlLabel,
  FormControlLabelText,
  FormControlError,
  FormControlErrorText,
  FormControlHelper,
  FormControlHelperText,
} from '@/components/ui/form-control';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Input, InputField } from '@/components/ui/input';
import { Pressable } from '@/components/ui/pressable';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

// Selected course with tutor-specific configuration
export interface SelectedCourse {
  id: string;
  course: EnhancedCourse;
  hourly_rate: number;
  expertise_level: 'beginner' | 'intermediate' | 'advanced' | 'expert';
  description?: string;
  is_featured: boolean;
  priority_order: number;
}

// Custom subject for tutors who want to teach non-standard courses
export interface CustomSubject {
  id: string;
  name: string;
  description: string;
  grade_levels: string[];
  hourly_rate: number;
  subject_area: string;
  is_featured: boolean;
  priority_order: number;
}

interface CourseSelectionManagerProps {
  selectedCourses: SelectedCourse[];
  customSubjects: CustomSubject[];
  onSelectionChange: (courses: SelectedCourse[], customSubjects: CustomSubject[]) => void;
  availableCourses: EnhancedCourse[];
  isLoadingCourses?: boolean;
  educationalSystemId?: number;
  educationalSystemName?: string;
  maxSelections?: number;
  defaultRate?: number;
  currency?: string;
  title?: string;
  subtitle?: string;
  onContinue?: () => void;
  showContinueButton?: boolean;
}

const ExpertiseLevelBadge: React.FC<{ level: string }> = ({ level }) => {
  const getExpertiseColor = (level: string) => {
    switch (level) {
      case 'expert':
        return 'bg-purple-100 text-purple-700';
      case 'advanced':
        return 'bg-blue-100 text-blue-700';
      case 'intermediate':
        return 'bg-green-100 text-green-700';
      case 'beginner':
        return 'bg-gray-100 text-gray-700';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  };

  const getExpertiseIcon = (level: string) => {
    switch (level) {
      case 'expert':
        return 4;
      case 'advanced':
        return 3;
      case 'intermediate':
        return 2;
      case 'beginner':
        return 1;
      default:
        return 1;
    }
  };

  const stars = getExpertiseIcon(level);

  return (
    <Badge className={getExpertiseColor(level)}>
      <HStack space="xs" className="items-center">
        <HStack space="0">
          {Array.from({ length: stars }).map((_, i) => (
            <Icon key={i} as={Star} className="text-current" size="xs" />
          ))}
        </HStack>
        <BadgeText className="text-xs capitalize">{level}</BadgeText>
      </HStack>
    </Badge>
  );
};

const RateInputField: React.FC<{
  value: number;
  onChange: (value: number) => void;
  currency: string;
  suggestedRate?: { min: number; max: number; average: number };
  placeholder?: string;
  error?: string;
}> = ({ value, onChange, currency, suggestedRate, placeholder, error }) => {
  const [focused, setFocused] = useState(false);

  return (
    <VStack space="xs">
      <HStack space="sm" className="items-center">
        <Box className="flex-1">
          <HStack space="xs" className="items-center">
            <Icon as={DollarSign} className="text-gray-500" size="sm" />
            <Input className={`flex-1 ${error ? 'border-red-300' : ''}`}>
              <InputField
                value={value.toString()}
                onChangeText={text => {
                  const numValue = parseFloat(text) || 0;
                  onChange(numValue);
                }}
                onFocus={() => setFocused(true)}
                onBlur={() => setFocused(false)}
                placeholder={placeholder || '0'}
                keyboardType="numeric"
                className="text-right"
              />
            </Input>
            <Text className="text-gray-600 text-sm">{currency}/h</Text>
          </HStack>
        </Box>
      </HStack>

      {focused && suggestedRate && (
        <HStack space="xs" className="items-center">
          <Icon as={TrendingUp} className="text-blue-500" size="xs" />
          <Text className="text-blue-600 text-xs">
            Market: {suggestedRate.min}-{suggestedRate.max}
            {currency} (avg. {suggestedRate.average}
            {currency})
          </Text>
        </HStack>
      )}

      {error && (
        <HStack space="xs" className="items-center">
          <Icon as={AlertCircle} className="text-red-500" size="xs" />
          <Text className="text-red-600 text-xs">{error}</Text>
        </HStack>
      )}
    </VStack>
  );
};

const SelectedCourseCard: React.FC<{
  item: SelectedCourse | CustomSubject;
  index: number;
  onUpdate: (updates: Partial<SelectedCourse | CustomSubject>) => void;
  onRemove: () => void;
  currency: string;
  isDragDisabled?: boolean;
}> = ({ item, index, onUpdate, onRemove, currency, isDragDisabled }) => {
  const [expanded, setExpanded] = useState(false);
  const [showRemoveDialog, setShowRemoveDialog] = useState(false);

  const isCustomSubject = 'subject_area' in item && !('course' in item);
  const course = isCustomSubject ? null : (item as SelectedCourse).course;
  const name = isCustomSubject ? item.name : course?.name || '';
  const description = isCustomSubject ? item.description : course?.description || '';

  return (
    <>
      <Card
        className={`
          border transition-all duration-200 mb-3
          ${
            item.is_featured
              ? 'ring-2 ring-blue-200 border-blue-300'
              : 'border-gray-200 hover:border-gray-300'
          }
        `}
      >
        <CardHeader className="pb-3">
          <HStack className="items-start justify-between">
            <HStack space="sm" className="items-start flex-1">
              {/* Drag Handle */}
              {!isDragDisabled && Platform.OS === 'web' && (
                <Box className="mt-1 p-1 hover:bg-gray-100 rounded cursor-grab active:cursor-grabbing">
                  <Icon as={GripVertical} className="text-gray-400" size="sm" />
                </Box>
              )}

              <VStack className="flex-1" space="xs">
                <HStack className="items-start justify-between">
                  <VStack space="xs" className="flex-1">
                    <HStack space="sm" className="items-center">
                      <Heading size="sm" className="text-gray-900 flex-1">
                        {name}
                      </Heading>

                      {item.is_featured && (
                        <Badge className="bg-yellow-100">
                          <HStack space="xs" className="items-center">
                            <Icon as={Star} className="text-yellow-600" size="xs" />
                            <BadgeText className="text-yellow-700 text-xs">Featured</BadgeText>
                          </HStack>
                        </Badge>
                      )}
                    </HStack>

                    {!isCustomSubject && course && (
                      <HStack space="xs" className="flex-wrap">
                        <Badge className="bg-blue-100">
                          <BadgeText className="text-blue-700 text-xs">
                            {course.education_level}
                          </BadgeText>
                        </Badge>

                        {course.subject_area && (
                          <Badge className="bg-green-100">
                            <BadgeText className="text-green-700 text-xs">
                              {course.subject_area}
                            </BadgeText>
                          </Badge>
                        )}
                      </HStack>
                    )}

                    {isCustomSubject && (
                      <HStack space="xs" className="flex-wrap">
                        <Badge className="bg-purple-100">
                          <BadgeText className="text-purple-700 text-xs">Custom</BadgeText>
                        </Badge>

                        <Badge className="bg-green-100">
                          <BadgeText className="text-green-700 text-xs">
                            {(item as CustomSubject).subject_area}
                          </BadgeText>
                        </Badge>
                      </HStack>
                    )}
                  </VStack>
                </HStack>

                <HStack className="items-center justify-between">
                  <HStack space="sm" className="items-center">
                    <Text className="text-gray-600 text-sm font-medium">
                      {item.hourly_rate}
                      {currency}/hour
                    </Text>

                    {!isCustomSubject && (
                      <ExpertiseLevelBadge level={(item as SelectedCourse).expertise_level} />
                    )}
                  </HStack>

                  <HStack space="xs">
                    <Pressable
                      onPress={() => setExpanded(!expanded)}
                      className="p-1 hover:bg-gray-100 rounded"
                      accessibilityLabel={expanded ? 'Collapse' : 'Expand'}
                    >
                      <Icon
                        as={expanded ? ChevronUp : ChevronDown}
                        className="text-gray-500"
                        size="sm"
                      />
                    </Pressable>

                    <Pressable
                      onPress={() => setShowRemoveDialog(true)}
                      className="p-1 hover:bg-red-100 rounded"
                      accessibilityLabel="Remove course"
                    >
                      <Icon as={Trash2} className="text-red-500" size="sm" />
                    </Pressable>
                  </HStack>
                </HStack>
              </VStack>
            </HStack>
          </HStack>
        </CardHeader>

        {expanded && (
          <CardContent className="pt-0">
            <VStack space="md">
              {description && (
                <Text className="text-gray-600 text-sm leading-relaxed">{description}</Text>
              )}

              <VStack space="sm">
                <Heading size="xs" className="text-gray-700">
                  Configuration
                </Heading>

                <HStack space="md" className="items-start">
                  <VStack space="xs" className="flex-1">
                    <FormControl>
                      <FormControlLabel>
                        <FormControlLabelText className="text-xs">Hourly Rate</FormControlLabelText>
                      </FormControlLabel>
                      <RateInputField
                        value={item.hourly_rate}
                        onChange={rate => onUpdate({ hourly_rate: rate })}
                        currency={currency}
                        suggestedRate={course?.rate_suggestions}
                      />
                    </FormControl>
                  </VStack>

                  {!isCustomSubject && (
                    <VStack space="xs" className="flex-1">
                      <FormControl>
                        <FormControlLabel>
                          <FormControlLabelText className="text-xs">
                            Expertise Level
                          </FormControlLabelText>
                        </FormControlLabel>
                        <HStack space="xs" className="flex-wrap">
                          {['beginner', 'intermediate', 'advanced', 'expert'].map(level => (
                            <Pressable
                              key={level}
                              onPress={() => onUpdate({ expertise_level: level as any })}
                              className={`px-2 py-1 rounded-md border ${
                                (item as SelectedCourse).expertise_level === level
                                  ? 'border-blue-500 bg-blue-50'
                                  : 'border-gray-200 bg-white'
                              }`}
                            >
                              <Text
                                className={`text-xs capitalize ${
                                  (item as SelectedCourse).expertise_level === level
                                    ? 'text-blue-700'
                                    : 'text-gray-600'
                                }`}
                              >
                                {level}
                              </Text>
                            </Pressable>
                          ))}
                        </HStack>
                      </FormControl>
                    </VStack>
                  )}
                </HStack>

                <HStack space="xs" className="items-center">
                  <Pressable
                    onPress={() => onUpdate({ is_featured: !item.is_featured })}
                    className={`w-4 h-4 rounded border-2 items-center justify-center ${
                      item.is_featured ? 'bg-blue-600 border-blue-600' : 'border-gray-300 bg-white'
                    }`}
                  >
                    {item.is_featured && <Icon as={Star} className="text-white" size="xs" />}
                  </Pressable>
                  <Text className="text-gray-700 text-sm">Feature this subject in my profile</Text>
                  <Pressable className="p-1">
                    <Icon as={Info} className="text-gray-400" size="xs" />
                  </Pressable>
                </HStack>
              </VStack>
            </VStack>
          </CardContent>
        )}
      </Card>

      {/* Remove Confirmation Dialog */}
      <AlertDialog isOpen={showRemoveDialog} onClose={() => setShowRemoveDialog(false)}>
        <AlertDialogBackdrop />
        <AlertDialogContent className="max-w-md">
          <AlertDialogHeader>
            <Heading size="lg" className="text-gray-900">
              Remove Subject
            </Heading>
          </AlertDialogHeader>
          <AlertDialogBody>
            <Text className="text-gray-600">
              Are you sure you want to remove "{name}" from your teaching subjects?
            </Text>
          </AlertDialogBody>
          <AlertDialogFooter>
            <HStack space="sm" className="w-full justify-end">
              <Button variant="outline" onPress={() => setShowRemoveDialog(false)}>
                <ButtonText>Cancel</ButtonText>
              </Button>
              <Button
                onPress={() => {
                  onRemove();
                  setShowRemoveDialog(false);
                }}
                className="bg-red-600"
              >
                <ButtonText className="text-white">Remove</ButtonText>
              </Button>
            </HStack>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
};

const CustomSubjectForm: React.FC<{
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (subject: Omit<CustomSubject, 'id' | 'priority_order'>) => void;
  defaultRate: number;
  currency: string;
}> = ({ isOpen, onClose, onSubmit, defaultRate, currency }) => {
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

export const CourseSelectionManager: React.FC<CourseSelectionManagerProps> = ({
  selectedCourses,
  customSubjects,
  onSelectionChange,
  availableCourses,
  isLoadingCourses = false,
  educationalSystemId,
  educationalSystemName = 'Educational System',
  maxSelections = 20,
  defaultRate = 15,
  currency = '€',
  title = 'Configure Your Teaching Subjects',
  subtitle = 'Set rates and expertise levels for your selected courses',
  onContinue,
  showContinueButton = true,
}) => {
  const [showCourseBrowser, setShowCourseBrowser] = useState(false);
  const [showCustomForm, setShowCustomForm] = useState(false);

  const allSelectedItems = useMemo(() => {
    const courseItems: (SelectedCourse | CustomSubject)[] = [...selectedCourses];
    const customItems: (SelectedCourse | CustomSubject)[] = [...customSubjects];

    return [...courseItems, ...customItems].sort((a, b) => a.priority_order - b.priority_order);
  }, [selectedCourses, customSubjects]);

  const selectedCourseIds = useMemo(() => selectedCourses.map(c => c.course.id), [selectedCourses]);

  const handleCourseToggle = (course: EnhancedCourse) => {
    const isSelected = selectedCourseIds.includes(course.id);

    if (isSelected) {
      // Remove course
      const updatedCourses = selectedCourses.filter(c => c.course.id !== course.id);
      onSelectionChange(updatedCourses, customSubjects);
    } else {
      // Add course
      const newSelectedCourse: SelectedCourse = {
        id: `course-${course.id}`,
        course,
        hourly_rate: course.rate_suggestions?.average || defaultRate,
        expertise_level: 'intermediate',
        is_featured: false,
        priority_order: allSelectedItems.length,
      };

      onSelectionChange([...selectedCourses, newSelectedCourse], customSubjects);
    }
  };

  const handleAddCustomSubject = (subjectData: Omit<CustomSubject, 'id' | 'priority_order'>) => {
    const newSubject: CustomSubject = {
      ...subjectData,
      id: `custom-${Date.now()}`,
      priority_order: allSelectedItems.length,
    };

    onSelectionChange(selectedCourses, [...customSubjects, newSubject]);
  };

  const handleItemUpdate = (itemId: string, updates: Partial<SelectedCourse | CustomSubject>) => {
    const isCustom = itemId.startsWith('custom-');

    if (isCustom) {
      const updatedCustomSubjects = customSubjects.map(item =>
        item.id === itemId ? { ...item, ...updates } : item
      );
      onSelectionChange(selectedCourses, updatedCustomSubjects);
    } else {
      const updatedCourses = selectedCourses.map(item =>
        item.id === itemId ? { ...item, ...updates } : item
      );
      onSelectionChange(updatedCourses, customSubjects);
    }
  };

  const handleItemRemove = (itemId: string) => {
    const isCustom = itemId.startsWith('custom-');

    if (isCustom) {
      const updatedCustomSubjects = customSubjects.filter(item => item.id !== itemId);
      onSelectionChange(selectedCourses, updatedCustomSubjects);
    } else {
      const updatedCourses = selectedCourses.filter(item => item.id !== itemId);
      onSelectionChange(updatedCourses, customSubjects);
    }
  };

  const totalSelections = selectedCourses.length + customSubjects.length;
  const canAddMore = totalSelections < maxSelections;
  const canContinue = totalSelections > 0;

  return (
    <VStack className="flex-1 bg-gray-50" space="md">
      {/* Header */}
      <Box className="bg-white px-6 py-6 border-b border-gray-200">
        <VStack className="items-center text-center" space="md">
          <Box className="w-16 h-16 rounded-full bg-blue-100 items-center justify-center">
            <Icon as={BookOpen} className="text-blue-600" size="xl" />
          </Box>

          <VStack space="sm">
            <Heading size="xl" className="text-gray-900 text-center">
              {title}
            </Heading>
            <Text className="text-gray-600 text-center max-w-md">{subtitle}</Text>
          </VStack>

          <HStack space="md" className="items-center">
            <Badge className="bg-blue-100">
              <BadgeText className="text-blue-700">{totalSelections} selected</BadgeText>
            </Badge>

            <Badge className="bg-gray-100">
              <BadgeText className="text-gray-700">
                {maxSelections - totalSelections} remaining
              </BadgeText>
            </Badge>
          </HStack>
        </VStack>
      </Box>

      {/* Selection Management */}
      <Box className="flex-1 px-6">
        <VStack space="md">
          {/* Add Buttons */}
          <HStack space="sm">
            <Button
              variant="outline"
              onPress={() => setShowCourseBrowser(true)}
              disabled={!canAddMore}
              className="flex-1"
            >
              <ButtonIcon as={Plus} className="text-gray-600 mr-2" />
              <ButtonText className="text-gray-700">Add from {educationalSystemName}</ButtonText>
            </Button>

            <Button
              variant="outline"
              onPress={() => setShowCustomForm(true)}
              disabled={!canAddMore}
              className="flex-1"
            >
              <ButtonIcon as={Plus} className="text-gray-600 mr-2" />
              <ButtonText className="text-gray-700">Add Custom Subject</ButtonText>
            </Button>
          </HStack>

          {/* Selected Items */}
          {totalSelections === 0 ? (
            <VStack className="items-center justify-center py-12" space="md">
              <Icon as={BookOpen} className="text-gray-400" size="xl" />
              <Text className="text-gray-600 text-center">
                No subjects selected yet. Add courses from the catalog or create custom subjects.
              </Text>
            </VStack>
          ) : (
            <VStack space="sm">
              <HStack className="items-center justify-between">
                <Heading size="sm" className="text-gray-900">
                  Your Teaching Subjects ({totalSelections})
                </Heading>
                {Platform.OS === 'web' && (
                  <Text className="text-gray-500 text-xs">Drag to reorder priority</Text>
                )}
              </HStack>

              <VStack space="sm">
                {allSelectedItems.map((item, index) => (
                  <SelectedCourseCard
                    key={item.id}
                    item={item}
                    index={index}
                    onUpdate={updates => handleItemUpdate(item.id, updates)}
                    onRemove={() => handleItemRemove(item.id)}
                    currency={currency}
                    isDragDisabled={Platform.OS !== 'web'}
                  />
                ))}
              </VStack>
            </VStack>
          )}
        </VStack>
      </Box>

      {/* Continue Button */}
      {showContinueButton && onContinue && (
        <Box className="bg-white px-6 py-4 border-t border-gray-200">
          <Button
            onPress={onContinue}
            disabled={!canContinue}
            className={`w-full ${canContinue ? 'bg-blue-600 hover:bg-blue-700' : 'bg-gray-300'}`}
          >
            <ButtonText className={canContinue ? 'text-white' : 'text-gray-500'}>
              Continue with {totalSelections} Subject{totalSelections !== 1 ? 's' : ''}
            </ButtonText>
          </Button>
        </Box>
      )}

      {/* Course Browser Modal */}
      <AlertDialog
        isOpen={showCourseBrowser}
        onClose={() => setShowCourseBrowser(false)}
        size="full"
      >
        <AlertDialogBackdrop />
        <AlertDialogContent className="max-w-4xl max-h-[90vh]">
          <CourseCatalogBrowser
            courses={availableCourses}
            selectedCourseIds={selectedCourseIds}
            onCourseToggle={handleCourseToggle}
            onSelectionComplete={() => setShowCourseBrowser(false)}
            isLoading={isLoadingCourses}
            educationalSystemName={educationalSystemName}
            maxSelections={maxSelections - customSubjects.length}
            allowMultiSelect={true}
            title="Add Courses to Your Profile"
            subtitle="Select courses you'd like to teach from the official curriculum"
          />
        </AlertDialogContent>
      </AlertDialog>

      {/* Custom Subject Form */}
      <CustomSubjectForm
        isOpen={showCustomForm}
        onClose={() => setShowCustomForm(false)}
        onSubmit={handleAddCustomSubject}
        defaultRate={defaultRate}
        currency={currency}
      />
    </VStack>
  );
};
