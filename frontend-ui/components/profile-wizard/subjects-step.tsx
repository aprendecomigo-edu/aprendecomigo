import {
  BookOpen,
  Plus,
  X,
  Search,
  Star,
  Award,
  TrendingUp,
  Users,
  Calendar,
  CheckCircle2,
  AlertCircle,
} from 'lucide-react-native';
import React, { useState } from 'react';
import { Platform } from 'react-native';

import {
  AlertDialog,
  AlertDialogBackdrop,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogFooter,
  AlertDialogBody,
} from '@/components/ui/alert-dialog';
import { Badge, BadgeText } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import {
  FormControl,
  FormControlLabel,
  FormControlHelper,
  FormControlError,
} from '@/components/ui/form-control';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Input, InputField } from '@/components/ui/input';
import { Pressable } from '@/components/ui/pressable';
import { ScrollView } from '@/components/ui/scroll-view';
import {
  Select,
  SelectTrigger,
  SelectInput,
  SelectContent,
  SelectItem,
} from '@/components/ui/select';
import { Text } from '@/components/ui/text';
import { Textarea, TextareaInput } from '@/components/ui/textarea';
import { VStack } from '@/components/ui/vstack';

interface TeachingSubject {
  id: string;
  subject: string;
  grade_levels: string[];
  expertise_level: 'beginner' | 'intermediate' | 'advanced' | 'expert';
  years_teaching: number;
  description?: string;
}

interface SubjectsFormData {
  teaching_subjects: TeachingSubject[];
  subject_categories: string[];
}

interface SubjectsStepProps {
  formData: SubjectsFormData;
  onFormDataChange: (data: Partial<SubjectsFormData>) => void;
  validationErrors?: Record<string, string[]>;
  isLoading?: boolean;
}

const PREDEFINED_SUBJECTS = [
  // STEM
  'Mathematics',
  'Physics',
  'Chemistry',
  'Biology',
  'Computer Science',
  'Statistics',
  'Calculus',
  'Algebra',
  'Geometry',
  'Data Science',
  'Programming',

  // Languages
  'Portuguese',
  'English',
  'Spanish',
  'French',
  'German',
  'Italian',
  'Chinese',
  'Japanese',

  // Humanities
  'History',
  'Geography',
  'Philosophy',
  'Psychology',
  'Sociology',
  'Literature',
  'Writing',
  'Essay Writing',
  'Creative Writing',

  // Arts
  'Music',
  'Art',
  'Drama',
  'Dance',
  'Fine Arts',
  'Digital Art',

  // Business & Economics
  'Economics',
  'Business Studies',
  'Accounting',
  'Finance',
  'Marketing',
  'Management',

  // Test Preparation
  'SAT Prep',
  'ACT Prep',
  'TOEFL',
  'IELTS',
  'GRE',
  'GMAT',

  // Other
  'Study Skills',
  'Special Needs Education',
  'ESL/EFL',
  'Tutoring',
];

const SUBJECT_CATEGORIES = [
  'STEM',
  'Languages',
  'Humanities',
  'Arts',
  'Business',
  'Test Preparation',
  'Special Education',
];

const GRADE_LEVELS = [
  { value: 'elementary', label: 'Elementary (K-5)' },
  { value: 'middle', label: 'Middle School (6-8)' },
  { value: 'high', label: 'High School (9-12)' },
  { value: 'university', label: 'University Level' },
  { value: 'adult', label: 'Adult Education' },
  { value: 'professional', label: 'Professional Development' },
];

const EXPERTISE_LEVELS = [
  { value: 'beginner', label: 'Beginner', description: 'New to teaching this subject' },
  { value: 'intermediate', label: 'Intermediate', description: '1-3 years teaching experience' },
  { value: 'advanced', label: 'Advanced', description: '4-8 years teaching experience' },
  { value: 'expert', label: 'Expert', description: '9+ years or specialized certification' },
];

const YEARS_TEACHING_OPTIONS = [
  { value: 0, label: 'New to this subject' },
  { value: 1, label: '1 year' },
  { value: 2, label: '2 years' },
  { value: 3, label: '3 years' },
  { value: 5, label: '4-5 years' },
  { value: 8, label: '6-8 years' },
  { value: 10, label: '9-10 years' },
  { value: 15, label: '11-15 years' },
  { value: 20, label: '16-20 years' },
  { value: 25, label: '20+ years' },
];

export const SubjectsStep: React.FC<SubjectsStepProps> = ({
  formData,
  onFormDataChange,
  validationErrors = {},
  isLoading = false,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [showAddSubject, setShowAddSubject] = useState(false);
  const [editingSubject, setEditingSubject] = useState<TeachingSubject | null>(null);
  const [showDeleteDialog, setShowDeleteDialog] = useState<string | null>(null);

  // New subject form state
  const [newSubject, setNewSubject] = useState<Partial<TeachingSubject>>({
    subject: '',
    grade_levels: [],
    expertise_level: 'intermediate',
    years_teaching: 1,
    description: '',
  });

  const filteredSubjects = PREDEFINED_SUBJECTS.filter(
    subject =>
      subject.toLowerCase().includes(searchTerm.toLowerCase()) &&
      !formData.teaching_subjects.some(ts => ts.subject === subject)
  );

  const handleFieldChange = (field: keyof SubjectsFormData, value: any) => {
    onFormDataChange({ [field]: value });
  };

  const handleAddQuickSubject = (subjectName: string) => {
    const subject: TeachingSubject = {
      id: Date.now().toString(),
      subject: subjectName,
      grade_levels: ['high'],
      expertise_level: 'intermediate',
      years_teaching: 1,
    };

    handleFieldChange('teaching_subjects', [...formData.teaching_subjects, subject]);
    setSearchTerm('');
  };

  const handleSaveSubject = () => {
    if (!newSubject.subject || newSubject.grade_levels?.length === 0) {
      return;
    }

    const subject: TeachingSubject = {
      id: editingSubject?.id || Date.now().toString(),
      subject: newSubject.subject!,
      grade_levels: newSubject.grade_levels!,
      expertise_level: newSubject.expertise_level!,
      years_teaching: newSubject.years_teaching!,
      description: newSubject.description,
    };

    let updatedSubjects;
    if (editingSubject) {
      updatedSubjects = formData.teaching_subjects.map(s =>
        s.id === editingSubject.id ? subject : s
      );
    } else {
      updatedSubjects = [...formData.teaching_subjects, subject];
    }

    handleFieldChange('teaching_subjects', updatedSubjects);
    resetSubjectForm();
  };

  const handleEditSubject = (subject: TeachingSubject) => {
    setNewSubject(subject);
    setEditingSubject(subject);
    setShowAddSubject(true);
  };

  const handleDeleteSubject = (subjectId: string) => {
    const updatedSubjects = formData.teaching_subjects.filter(s => s.id !== subjectId);
    handleFieldChange('teaching_subjects', updatedSubjects);
    setShowDeleteDialog(null);
  };

  const resetSubjectForm = () => {
    setNewSubject({
      subject: '',
      grade_levels: [],
      expertise_level: 'intermediate',
      years_teaching: 1,
      description: '',
    });
    setEditingSubject(null);
    setShowAddSubject(false);
  };

  const handleGradeLevelToggle = (level: string, checked: boolean) => {
    const currentLevels = newSubject.grade_levels || [];
    const updatedLevels = checked
      ? [...currentLevels, level]
      : currentLevels.filter(l => l !== level);

    setNewSubject(prev => ({ ...prev, grade_levels: updatedLevels }));
  };

  const handleCategoryToggle = (category: string, checked: boolean) => {
    const currentCategories = formData.subject_categories || [];
    const updatedCategories = checked
      ? [...currentCategories, category]
      : currentCategories.filter(c => c !== category);

    handleFieldChange('subject_categories', updatedCategories);
  };

  const getExpertiseColor = (level: string) => {
    switch (level) {
      case 'beginner':
        return 'bg-blue-100 text-blue-800';
      case 'intermediate':
        return 'bg-yellow-100 text-yellow-800';
      case 'advanced':
        return 'bg-orange-100 text-orange-800';
      case 'expert':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getFieldError = (fieldName: string): string | undefined => {
    return validationErrors[fieldName]?.[0];
  };

  const hasFieldError = (fieldName: string): boolean => {
    return !!validationErrors[fieldName]?.length;
  };

  return (
    <ScrollView className="flex-1">
      <Box className="p-6 max-w-4xl mx-auto">
        <VStack space="lg">
          {/* Header */}
          <VStack space="sm">
            <Heading size="xl" className="text-gray-900">
              Teaching Subjects & Expertise
            </Heading>
            <Text className="text-gray-600">
              Add the subjects you teach, your expertise level, and the grade levels you work with.
              This helps students find the right tutor for their needs.
            </Text>
          </VStack>

          {/* Subject Categories */}
          <Card>
            <VStack space="md" className="p-6">
              <Heading size="md" className="text-gray-900">
                Subject Categories
              </Heading>
              <Text className="text-gray-600 text-sm">
                Select the broad categories that best describe your teaching areas.
              </Text>

              <HStack space="sm" className="flex-wrap">
                {SUBJECT_CATEGORIES.map(category => (
                  <Pressable
                    key={category}
                    onPress={() =>
                      handleCategoryToggle(
                        category,
                        !formData.subject_categories?.includes(category)
                      )
                    }
                    className="mb-2"
                  >
                    <Badge
                      className={
                        formData.subject_categories?.includes(category)
                          ? 'bg-blue-600'
                          : 'bg-gray-100 border border-gray-300'
                      }
                    >
                      <BadgeText
                        className={
                          formData.subject_categories?.includes(category)
                            ? 'text-white'
                            : 'text-gray-700'
                        }
                      >
                        {category}
                      </BadgeText>
                    </Badge>
                  </Pressable>
                ))}
              </HStack>
            </VStack>
          </Card>

          {/* Current Subjects */}
          {formData.teaching_subjects.length > 0 && (
            <Card>
              <VStack space="md" className="p-6">
                <HStack className="items-center justify-between">
                  <Heading size="md" className="text-gray-900">
                    Your Teaching Subjects ({formData.teaching_subjects.length})
                  </Heading>
                </HStack>

                <VStack space="sm">
                  {formData.teaching_subjects.map((subject, index) => (
                    <Card key={subject.id} className="bg-gray-50">
                      <VStack space="sm" className="p-4">
                        <HStack className="items-start justify-between">
                          <VStack space="xs" className="flex-1">
                            <HStack space="sm" className="items-center">
                              <Text className="font-semibold text-gray-900 text-lg">
                                {subject.subject}
                              </Text>
                              <Badge className={getExpertiseColor(subject.expertise_level)}>
                                <BadgeText className="capitalize">
                                  {subject.expertise_level}
                                </BadgeText>
                              </Badge>
                            </HStack>

                            <HStack space="md" className="items-center">
                              <HStack space="xs" className="items-center">
                                <Icon as={Users} size={14} className="text-gray-500" />
                                <Text className="text-sm text-gray-600">
                                  {subject.grade_levels
                                    .map(
                                      level =>
                                        GRADE_LEVELS.find(gl => gl.value === level)?.label || level
                                    )
                                    .join(', ')}
                                </Text>
                              </HStack>

                              <HStack space="xs" className="items-center">
                                <Icon as={Calendar} size={14} className="text-gray-500" />
                                <Text className="text-sm text-gray-600">
                                  {subject.years_teaching === 0
                                    ? 'New to subject'
                                    : `${subject.years_teaching}+ years`}
                                </Text>
                              </HStack>
                            </HStack>

                            {subject.description && (
                              <Text className="text-sm text-gray-600 mt-1">
                                {subject.description}
                              </Text>
                            )}
                          </VStack>

                          <HStack space="xs">
                            <Button
                              size="sm"
                              variant="ghost"
                              onPress={() => handleEditSubject(subject)}
                            >
                              <ButtonText className="text-blue-600">Edit</ButtonText>
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              onPress={() => setShowDeleteDialog(subject.id)}
                            >
                              <ButtonIcon as={X} className="text-red-500" />
                            </Button>
                          </HStack>
                        </HStack>
                      </VStack>
                    </Card>
                  ))}
                </VStack>
              </VStack>
            </Card>
          )}

          {/* Add New Subject */}
          <Card>
            <VStack space="md" className="p-6">
              <HStack className="items-center justify-between">
                <Heading size="md" className="text-gray-900">
                  Add Teaching Subject
                </Heading>
                <Button onPress={() => setShowAddSubject(true)} className="bg-blue-600">
                  <ButtonIcon as={Plus} className="text-white mr-2" />
                  <ButtonText className="text-white">Add Subject</ButtonText>
                </Button>
              </HStack>

              {/* Quick Add from Search */}
              <VStack space="sm">
                <FormControl>
                  <FormControlLabel>
                    <Text>Search & Quick Add</Text>
                  </FormControlLabel>
                  <Input>
                    <InputField
                      value={searchTerm}
                      onChangeText={setSearchTerm}
                      placeholder="Search for subjects to add quickly..."
                    />
                  </Input>
                  <FormControlHelper>
                    <Text>Search and tap to quickly add common subjects</Text>
                  </FormControlHelper>
                </FormControl>

                {searchTerm && filteredSubjects.length > 0 && (
                  <VStack space="xs">
                    <Text className="text-sm font-medium text-gray-700">
                      Quick Add Suggestions:
                    </Text>
                    <HStack space="xs" className="flex-wrap">
                      {filteredSubjects.slice(0, 8).map(subject => (
                        <Button
                          key={subject}
                          variant="outline"
                          size="sm"
                          onPress={() => handleAddQuickSubject(subject)}
                          className="mb-2"
                        >
                          <ButtonIcon as={Plus} className="text-gray-600 mr-1" size={14} />
                          <ButtonText>{subject}</ButtonText>
                        </Button>
                      ))}
                    </HStack>
                  </VStack>
                )}
              </VStack>
            </VStack>
          </Card>

          {/* Validation Error */}
          {hasFieldError('teaching_subjects') && (
            <Box className="bg-red-50 border-l-4 border-red-400 p-4">
              <HStack space="sm" className="items-center">
                <Icon as={AlertCircle} size={20} className="text-red-500" />
                <Text className="text-red-700">{getFieldError('teaching_subjects')}</Text>
              </HStack>
            </Box>
          )}
        </VStack>
      </Box>

      {/* Add/Edit Subject Modal */}
      <AlertDialog isOpen={showAddSubject} onClose={resetSubjectForm}>
        <AlertDialogBackdrop />
        <AlertDialogContent className="max-w-2xl">
          <AlertDialogHeader>
            <Heading size="lg" className="text-gray-900">
              {editingSubject ? 'Edit Subject' : 'Add New Subject'}
            </Heading>
          </AlertDialogHeader>
          <AlertDialogBody>
            <VStack space="md">
              {/* Subject Name */}
              <FormControl>
                <FormControlLabel>
                  <Text>Subject Name *</Text>
                </FormControlLabel>
                <Input>
                  <InputField
                    value={newSubject.subject || ''}
                    onChangeText={value => setNewSubject(prev => ({ ...prev, subject: value }))}
                    placeholder="e.g., Mathematics, Physics, Portuguese"
                  />
                </Input>
              </FormControl>

              {/* Grade Levels */}
              <FormControl>
                <FormControlLabel>
                  <Text>Grade Levels *</Text>
                </FormControlLabel>
                <VStack space="xs">
                  {GRADE_LEVELS.map(level => (
                    <HStack key={level.value} space="sm" className="items-center">
                      <Checkbox
                        value={level.value}
                        isChecked={newSubject.grade_levels?.includes(level.value) || false}
                        onChange={checked => handleGradeLevelToggle(level.value, checked)}
                      />
                      <Text className="flex-1">{level.label}</Text>
                    </HStack>
                  ))}
                </VStack>
                <FormControlHelper>
                  <Text>Select all grade levels you're comfortable teaching</Text>
                </FormControlHelper>
              </FormControl>

              {/* Expertise Level and Years */}
              <HStack space="md">
                <VStack className="flex-1">
                  <FormControl>
                    <FormControlLabel>
                      <Text>Expertise Level *</Text>
                    </FormControlLabel>
                    <Select
                      selectedValue={newSubject.expertise_level || 'intermediate'}
                      onValueChange={value =>
                        setNewSubject(prev => ({
                          ...prev,
                          expertise_level: value as any,
                        }))
                      }
                    >
                      <SelectTrigger>
                        <SelectInput placeholder="Select expertise level" />
                      </SelectTrigger>
                      <SelectContent>
                        {EXPERTISE_LEVELS.map(level => (
                          <SelectItem
                            key={level.value}
                            label={`${level.label} - ${level.description}`}
                            value={level.value}
                          />
                        ))}
                      </SelectContent>
                    </Select>
                  </FormControl>
                </VStack>

                <VStack className="flex-1">
                  <FormControl>
                    <FormControlLabel>
                      <Text>Years Teaching This Subject</Text>
                    </FormControlLabel>
                    <Select
                      selectedValue={newSubject.years_teaching?.toString() || '1'}
                      onValueChange={value =>
                        setNewSubject(prev => ({
                          ...prev,
                          years_teaching: parseInt(value),
                        }))
                      }
                    >
                      <SelectTrigger>
                        <SelectInput placeholder="Select years" />
                      </SelectTrigger>
                      <SelectContent>
                        {YEARS_TEACHING_OPTIONS.map(option => (
                          <SelectItem
                            key={option.value}
                            label={option.label}
                            value={option.value.toString()}
                          />
                        ))}
                      </SelectContent>
                    </Select>
                  </FormControl>
                </VStack>
              </HStack>

              {/* Description */}
              <FormControl>
                <FormControlLabel>
                  <Text>Subject Description (Optional)</Text>
                </FormControlLabel>
                <Textarea>
                  <TextareaInput
                    value={newSubject.description || ''}
                    onChangeText={value => setNewSubject(prev => ({ ...prev, description: value }))}
                    placeholder="Describe your approach, specializations, or what makes you unique in teaching this subject..."
                    numberOfLines={3}
                  />
                </Textarea>
                <FormControlHelper>
                  <Text>Help students understand your teaching style and expertise</Text>
                </FormControlHelper>
              </FormControl>
            </VStack>
          </AlertDialogBody>
          <AlertDialogFooter>
            <HStack space="sm" className="w-full">
              <Button variant="outline" onPress={resetSubjectForm} className="flex-1">
                <ButtonText>Cancel</ButtonText>
              </Button>
              <Button
                onPress={handleSaveSubject}
                className="flex-1 bg-blue-600"
                isDisabled={!newSubject.subject || !newSubject.grade_levels?.length}
              >
                <ButtonText>{editingSubject ? 'Update Subject' : 'Add Subject'}</ButtonText>
              </Button>
            </HStack>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Delete Confirmation Dialog */}
      <AlertDialog isOpen={!!showDeleteDialog} onClose={() => setShowDeleteDialog(null)}>
        <AlertDialogBackdrop />
        <AlertDialogContent>
          <AlertDialogHeader>
            <Heading size="lg" className="text-gray-900">
              Remove Subject?
            </Heading>
          </AlertDialogHeader>
          <AlertDialogBody>
            <Text className="text-gray-600">
              Are you sure you want to remove this subject from your teaching profile? This action
              cannot be undone.
            </Text>
          </AlertDialogBody>
          <AlertDialogFooter>
            <HStack space="sm" className="w-full">
              <Button
                variant="outline"
                onPress={() => setShowDeleteDialog(null)}
                className="flex-1"
              >
                <ButtonText>Cancel</ButtonText>
              </Button>
              <Button
                onPress={() => showDeleteDialog && handleDeleteSubject(showDeleteDialog)}
                className="flex-1 bg-red-600"
              >
                <ButtonText>Remove</ButtonText>
              </Button>
            </HStack>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </ScrollView>
  );
};
