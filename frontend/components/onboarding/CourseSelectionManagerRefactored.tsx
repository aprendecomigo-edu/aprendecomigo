import { Plus, BookOpen } from 'lucide-react-native';
import React from 'react';
import { Platform } from 'react-native';

import { CustomSubjectForm } from './components/CustomSubjectForm';
import { SelectedCourseCard } from './components/SelectedCourseCard';
import { useCourseManager, SelectedCourse, CustomSubject } from './hooks/useCourseManager';

import { CourseCatalogBrowser } from './CourseCatalogBrowser';

import { EnhancedCourse } from '@/api/tutorApi';
import {
  AlertDialog,
  AlertDialogBackdrop,
  AlertDialogContent,
} from '@/components/ui/alert-dialog';
import { Badge, BadgeText } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

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
  const {
    showCourseBrowser,
    setShowCourseBrowser,
    showCustomForm,
    setShowCustomForm,
    allSelectedItems,
    selectedCourseIds,
    totalSelections,
    canAddMore,
    canContinue,
    handleCourseToggle,
    handleAddCustomSubject,
    handleItemUpdate,
    handleItemRemove,
  } = useCourseManager({
    selectedCourses,
    customSubjects,
    onSelectionChange,
    availableCourses,
    maxSelections,
    defaultRate,
  });

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