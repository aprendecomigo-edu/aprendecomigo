import {
  Search,
  BookOpen,
  ChevronRight,
  ChevronDown,
  Plus,
  Check,
  Filter,
  X,
  Globe,
  GraduationCap,
  Users,
} from 'lucide-react-native';
import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { FlatList, SectionList } from 'react-native';

import { Badge, BadgeText } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Input, InputField } from '@/components/ui/input';
import {
  Modal,
  ModalBackdrop,
  ModalContent,
  ModalHeader,
  ModalCloseButton,
  ModalBody,
  ModalFooter,
} from '@/components/ui/modal';
import { Pressable } from '@/components/ui/pressable';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

// Course interface matching backend structure
export interface Course {
  id: number;
  name: string;
  code: string;
  description?: string;
  education_level: string;
  educational_system: number;
  subject_area?: string;
  difficulty_level?: 'beginner' | 'intermediate' | 'advanced';
  estimated_hours?: number;
  is_active: boolean;
  prerequisites?: string[];
  learning_objectives?: string[];
}

// Education level configuration
const EDUCATION_LEVELS = {
  ensino_basico_1: {
    name: '1st Cycle Basic Education',
    shortName: '1st Cycle',
    description: 'Ages 6-10 (Grades 1-4)',
    color: 'bg-green-100 text-green-700',
    order: 1,
  },
  ensino_basico_2: {
    name: '2nd Cycle Basic Education',
    shortName: '2nd Cycle',
    description: 'Ages 10-12 (Grades 5-6)',
    color: 'bg-blue-100 text-blue-700',
    order: 2,
  },
  ensino_basico_3: {
    name: '3rd Cycle Basic Education',
    shortName: '3rd Cycle',
    description: 'Ages 12-15 (Grades 7-9)',
    color: 'bg-purple-100 text-purple-700',
    order: 3,
  },
  ensino_secundario: {
    name: 'Secondary Education',
    shortName: 'Secondary',
    description: 'Ages 15-18 (Grades 10-12)',
    color: 'bg-orange-100 text-orange-700',
    order: 4,
  },
  ensino_superior: {
    name: 'Higher Education',
    shortName: 'Higher Ed',
    description: 'University/College Level',
    color: 'bg-red-100 text-red-700',
    order: 5,
  },
  custom: {
    name: 'Custom/Other',
    shortName: 'Custom',
    description: 'Specialized or custom subjects',
    color: 'bg-gray-100 text-gray-700',
    order: 6,
  },
} as const;

// Subject area colors
const SUBJECT_COLORS = [
  'bg-red-100 text-red-700',
  'bg-blue-100 text-blue-700',
  'bg-green-100 text-green-700',
  'bg-yellow-100 text-yellow-700',
  'bg-purple-100 text-purple-700',
  'bg-pink-100 text-pink-700',
  'bg-indigo-100 text-indigo-700',
  'bg-teal-100 text-teal-700',
];

interface CourseGroup {
  title: string;
  data: Course[];
  level: string;
}

interface CourseCatalogBrowserProps {
  courses: Course[];
  selectedCourseIds: number[];
  onCourseToggle: (course: Course) => void;
  onSelectionComplete?: () => void;
  isLoading?: boolean;
  educationalSystemName?: string;
  maxSelections?: number;
  showSelectionLimit?: boolean;
  allowMultiSelect?: boolean;
  title?: string;
  subtitle?: string;
}

const CourseCard = React.memo<{
  course: Course;
  isSelected: boolean;
  canSelect: boolean;
  onToggle: (course: Course) => void;
  allowMultiSelect: boolean;
}>(({ course, isSelected, canSelect, onToggle, allowMultiSelect }) => {
  const levelConfig = EDUCATION_LEVELS[course.education_level as keyof typeof EDUCATION_LEVELS];
  const subjectColorIndex = course.subject_area
    ? course.subject_area.charCodeAt(0) % SUBJECT_COLORS.length
    : 0;
  const subjectColor = SUBJECT_COLORS[subjectColorIndex];

  return (
    <Pressable
      onPress={() => canSelect && onToggle(course)}
      className={`w-full ${isSelected ? 'opacity-100' : canSelect ? 'opacity-100' : 'opacity-50'}`}
      accessibilityRole="button"
      accessibilityLabel={`${isSelected ? 'Deselect' : 'Select'} ${course.name}`}
      accessibilityHint={course.description}
      accessibilityState={{ selected: isSelected, disabled: !canSelect }}
    >
      <Card
        className={`
          border-2 transition-all duration-200 mb-3
          ${
            isSelected
              ? 'border-blue-500 bg-blue-50 shadow-md'
              : canSelect
                ? 'border-gray-200 bg-white hover:border-blue-300 hover:bg-blue-50'
                : 'border-gray-100 bg-gray-50'
          }
        `}
      >
        <CardHeader className="pb-2">
          <HStack className="items-start justify-between">
            <HStack space="sm" className="items-start flex-1">
              {allowMultiSelect && (
                <Box className="mt-1">
                  <Box
                    className={`
                      w-5 h-5 rounded border-2 items-center justify-center
                      ${
                        isSelected
                          ? 'bg-blue-600 border-blue-600'
                          : canSelect
                            ? 'border-gray-300 bg-white'
                            : 'border-gray-200 bg-gray-100'
                      }
                    `}
                  >
                    {isSelected && <Icon as={Check} className="text-white" size="xs" />}
                  </Box>
                </Box>
              )}

              <VStack className="flex-1" space="xs">
                <VStack space="xs">
                  <Heading size="sm" className="text-gray-900 leading-tight">
                    {course.name}
                  </Heading>
                  {course.code && (
                    <Text className="text-gray-500 text-xs font-mono">{course.code}</Text>
                  )}
                </VStack>

                <HStack space="xs" className="flex-wrap">
                  {levelConfig && (
                    <Badge className={levelConfig.color}>
                      <BadgeText className="text-xs">{levelConfig.shortName}</BadgeText>
                    </Badge>
                  )}

                  {course.subject_area && (
                    <Badge className={subjectColor}>
                      <BadgeText className="text-xs">{course.subject_area}</BadgeText>
                    </Badge>
                  )}

                  {course.difficulty_level && (
                    <Badge className="bg-gray-100 text-gray-700">
                      <BadgeText className="text-xs capitalize">
                        {course.difficulty_level}
                      </BadgeText>
                    </Badge>
                  )}
                </HStack>

                {course.description && (
                  <Text className="text-gray-600 text-sm leading-relaxed">
                    {course.description}
                  </Text>
                )}

                {course.estimated_hours && (
                  <HStack space="xs" className="items-center">
                    <Icon as={GraduationCap} className="text-gray-400" size="xs" />
                    <Text className="text-gray-500 text-xs">
                      ~{course.estimated_hours}h curriculum
                    </Text>
                  </HStack>
                )}
              </VStack>
            </HStack>

            {!allowMultiSelect && isSelected && (
              <Box className="w-6 h-6 rounded-full bg-blue-600 items-center justify-center ml-2">
                <Icon as={Check} className="text-white" size="sm" />
              </Box>
            )}
          </HStack>
        </CardHeader>

        {(course.prerequisites?.length || course.learning_objectives?.length) && (
          <CardContent className="pt-0">
            {course.prerequisites?.length && (
              <VStack space="xs" className="mb-2">
                <Text className="text-gray-700 text-xs font-medium">Prerequisites:</Text>
                <Text className="text-gray-600 text-xs">{course.prerequisites.join(', ')}</Text>
              </VStack>
            )}

            {course.learning_objectives?.length && (
              <VStack space="xs">
                <Text className="text-gray-700 text-xs font-medium">Learning Objectives:</Text>
                <VStack space="xs">
                  {course.learning_objectives.slice(0, 2).map((objective, index) => (
                    <HStack key={index} space="xs" className="items-start">
                      <Text className="text-gray-400 text-xs">•</Text>
                      <Text className="text-gray-600 text-xs flex-1">{objective}</Text>
                    </HStack>
                  ))}
                  {course.learning_objectives.length > 2 && (
                    <Text className="text-gray-500 text-xs">
                      +{course.learning_objectives.length - 2} more objectives
                    </Text>
                  )}
                </VStack>
              </VStack>
            )}
          </CardContent>
        )}
      </Card>
    </Pressable>
  );
});

const FilterModal: React.FC<{
  isOpen: boolean;
  onClose: () => void;
  filters: {
    levels: string[];
    subjects: string[];
    difficulty: string[];
  };
  onFiltersChange: (filters: any) => void;
  availableFilters: {
    levels: string[];
    subjects: string[];
  };
}> = ({ isOpen, onClose, filters, onFiltersChange, availableFilters }) => {
  const [localFilters, setLocalFilters] = useState(filters);

  useEffect(() => {
    setLocalFilters(filters);
  }, [filters]);

  const handleApplyFilters = () => {
    onFiltersChange(localFilters);
    onClose();
  };

  const handleClearFilters = () => {
    const clearedFilters = { levels: [], subjects: [], difficulty: [] };
    setLocalFilters(clearedFilters);
    onFiltersChange(clearedFilters);
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="lg">
      <ModalBackdrop />
      <ModalContent className="max-w-lg">
        <ModalHeader className="border-b border-gray-200">
          <HStack className="items-center justify-between w-full">
            <Heading size="lg">Filter Courses</Heading>
            <ModalCloseButton onPress={onClose}>
              <Icon as={X} className="text-gray-500" />
            </ModalCloseButton>
          </HStack>
        </ModalHeader>

        <ModalBody className="p-6">
          <VStack space="lg">
            {/* Education Levels */}
            <VStack space="md">
              <Heading size="sm" className="text-gray-900">
                Education Levels
              </Heading>
              <VStack space="sm">
                {availableFilters.levels.map(level => {
                  const levelConfig = EDUCATION_LEVELS[level as keyof typeof EDUCATION_LEVELS];
                  if (!levelConfig) return null;

                  const isSelected = localFilters.levels.includes(level);

                  return (
                    <Pressable
                      key={level}
                      onPress={() => {
                        setLocalFilters(prev => ({
                          ...prev,
                          levels: isSelected
                            ? prev.levels.filter(l => l !== level)
                            : [...prev.levels, level],
                        }));
                      }}
                      className="w-full"
                    >
                      <HStack space="sm" className="items-center p-2 rounded-md hover:bg-gray-50">
                        <Box
                          className={`
                            w-4 h-4 rounded border-2 items-center justify-center
                            ${isSelected ? 'bg-blue-600 border-blue-600' : 'border-gray-300'}
                          `}
                        >
                          {isSelected && <Icon as={Check} className="text-white" size="xs" />}
                        </Box>
                        <VStack className="flex-1">
                          <Text className="text-gray-900 text-sm font-medium">
                            {levelConfig.name}
                          </Text>
                          <Text className="text-gray-600 text-xs">{levelConfig.description}</Text>
                        </VStack>
                      </HStack>
                    </Pressable>
                  );
                })}
              </VStack>
            </VStack>

            {/* Subject Areas */}
            {availableFilters.subjects.length > 0 && (
              <VStack space="md">
                <Heading size="sm" className="text-gray-900">
                  Subject Areas
                </Heading>
                <VStack space="sm">
                  {availableFilters.subjects.map(subject => {
                    const isSelected = localFilters.subjects.includes(subject);

                    return (
                      <Pressable
                        key={subject}
                        onPress={() => {
                          setLocalFilters(prev => ({
                            ...prev,
                            subjects: isSelected
                              ? prev.subjects.filter(s => s !== subject)
                              : [...prev.subjects, subject],
                          }));
                        }}
                        className="w-full"
                      >
                        <HStack space="sm" className="items-center p-2 rounded-md hover:bg-gray-50">
                          <Box
                            className={`
                              w-4 h-4 rounded border-2 items-center justify-center
                              ${isSelected ? 'bg-blue-600 border-blue-600' : 'border-gray-300'}
                            `}
                          >
                            {isSelected && <Icon as={Check} className="text-white" size="xs" />}
                          </Box>
                          <Text className="text-gray-900 text-sm flex-1">{subject}</Text>
                        </HStack>
                      </Pressable>
                    );
                  })}
                </VStack>
              </VStack>
            )}

            {/* Difficulty Levels */}
            <VStack space="md">
              <Heading size="sm" className="text-gray-900">
                Difficulty Level
              </Heading>
              <VStack space="sm">
                {['beginner', 'intermediate', 'advanced'].map(difficulty => {
                  const isSelected = localFilters.difficulty.includes(difficulty);

                  return (
                    <Pressable
                      key={difficulty}
                      onPress={() => {
                        setLocalFilters(prev => ({
                          ...prev,
                          difficulty: isSelected
                            ? prev.difficulty.filter(d => d !== difficulty)
                            : [...prev.difficulty, difficulty],
                        }));
                      }}
                      className="w-full"
                    >
                      <HStack space="sm" className="items-center p-2 rounded-md hover:bg-gray-50">
                        <Box
                          className={`
                            w-4 h-4 rounded border-2 items-center justify-center
                            ${isSelected ? 'bg-blue-600 border-blue-600' : 'border-gray-300'}
                          `}
                        >
                          {isSelected && <Icon as={Check} className="text-white" size="xs" />}
                        </Box>
                        <Text className="text-gray-900 text-sm capitalize flex-1">
                          {difficulty}
                        </Text>
                      </HStack>
                    </Pressable>
                  );
                })}
              </VStack>
            </VStack>
          </VStack>
        </ModalBody>

        <ModalFooter className="border-t border-gray-200 p-4">
          <HStack space="sm" className="w-full justify-end">
            <Button variant="outline" onPress={handleClearFilters}>
              <ButtonText>Clear All</ButtonText>
            </Button>
            <Button onPress={handleApplyFilters} className="bg-blue-600">
              <ButtonText className="text-white">Apply Filters</ButtonText>
            </Button>
          </HStack>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};

export const CourseCatalogBrowser: React.FC<CourseCatalogBrowserProps> = ({
  courses,
  selectedCourseIds,
  onCourseToggle,
  onSelectionComplete,
  isLoading = false,
  educationalSystemName = 'Educational System',
  maxSelections,
  showSelectionLimit = true,
  allowMultiSelect = true,
  title = 'Select Your Teaching Subjects',
  subtitle = "Choose the courses and subjects you'd like to teach",
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [viewMode, setViewMode] = useState<'list' | 'grouped'>('grouped');
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState({
    levels: [] as string[],
    subjects: [] as string[],
    difficulty: [] as string[],
  });

  // Create available filter options from courses
  const availableFilters = useMemo(() => {
    const levels = [...new Set(courses.map(c => c.education_level))];
    const subjects = [...new Set(courses.map(c => c.subject_area).filter(Boolean))];

    return { levels, subjects };
  }, [courses]);

  // Filter and search courses
  const filteredCourses = useMemo(() => {
    let filtered = courses.filter(course => course.is_active);

    // Apply search
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        course =>
          course.name.toLowerCase().includes(query) ||
          course.code.toLowerCase().includes(query) ||
          course.description?.toLowerCase().includes(query) ||
          course.subject_area?.toLowerCase().includes(query),
      );
    }

    // Apply filters
    if (filters.levels.length > 0) {
      filtered = filtered.filter(course => filters.levels.includes(course.education_level));
    }

    if (filters.subjects.length > 0) {
      filtered = filtered.filter(
        course => course.subject_area && filters.subjects.includes(course.subject_area),
      );
    }

    if (filters.difficulty.length > 0) {
      filtered = filtered.filter(
        course => course.difficulty_level && filters.difficulty.includes(course.difficulty_level),
      );
    }

    return filtered;
  }, [courses, searchQuery, filters]);

  // Group courses by education level
  const groupedCourses = useMemo((): CourseGroup[] => {
    const groups: { [key: string]: Course[] } = {};

    filteredCourses.forEach(course => {
      const level = course.education_level;
      if (!groups[level]) {
        groups[level] = [];
      }
      groups[level].push(course);
    });

    return Object.entries(groups)
      .map(([level, coursesInLevel]) => ({
        title: EDUCATION_LEVELS[level as keyof typeof EDUCATION_LEVELS]?.name || level,
        data: coursesInLevel.sort((a, b) => a.name.localeCompare(b.name)),
        level,
      }))
      .sort((a, b) => {
        const orderA = EDUCATION_LEVELS[a.level as keyof typeof EDUCATION_LEVELS]?.order || 999;
        const orderB = EDUCATION_LEVELS[b.level as keyof typeof EDUCATION_LEVELS]?.order || 999;
        return orderA - orderB;
      });
  }, [filteredCourses]);

  const canSelectMore = !maxSelections || selectedCourseIds.length < maxSelections;
  const hasActiveFilters =
    filters.levels.length > 0 || filters.subjects.length > 0 || filters.difficulty.length > 0;

  const renderCourseItem = useCallback(({ item }: { item: Course }) => (
    <CourseCard
      course={item}
      isSelected={selectedCourseIds.includes(item.id)}
      canSelect={canSelectMore || selectedCourseIds.includes(item.id)}
      onToggle={onCourseToggle}
      allowMultiSelect={allowMultiSelect}
    />
  ), [selectedCourseIds, canSelectMore, onCourseToggle, allowMultiSelect]);

  const renderSectionHeader = useCallback(({ section }: { section: CourseGroup }) => (
    <Box className="bg-gray-100 px-4 py-2 mb-2 rounded-md">
      <HStack className="items-center justify-between">
        <Heading size="sm" className="text-gray-900">
          {section.title}
        </Heading>
        <Badge className="bg-blue-100">
          <BadgeText className="text-blue-700 text-xs">
            {section.data.length} course{section.data.length !== 1 ? 's' : ''}
          </BadgeText>
        </Badge>
      </HStack>
    </Box>
  ), []);

  return (
    <VStack className="flex-1 bg-gray-50" space="md">
      {/* Header */}
      <Box className="bg-white px-4 py-6 border-b border-gray-200">
        <VStack space="md">
          <VStack className="items-center text-center" space="sm">
            <Box className="w-12 h-12 rounded-full bg-blue-100 items-center justify-center">
              <Icon as={BookOpen} className="text-blue-600" size="lg" />
            </Box>
            <VStack space="xs">
              <Heading size="xl" className="text-gray-900 text-center">
                {title}
              </Heading>
              <Text className="text-gray-600 text-center">{subtitle}</Text>
              <Text className="text-blue-600 text-sm font-medium">{educationalSystemName}</Text>
            </VStack>
          </VStack>

          {/* Selection Counter */}
          {allowMultiSelect && showSelectionLimit && (
            <HStack className="items-center justify-center" space="xs">
              <Icon as={Users} className="text-gray-500" size="sm" />
              <Text className="text-gray-600 text-sm">
                {selectedCourseIds.length} selected
                {maxSelections && ` of ${maxSelections} max`}
              </Text>
            </HStack>
          )}
        </VStack>
      </Box>

      {/* Search and Filters */}
      <Box className="px-4">
        <VStack space="sm">
          <HStack space="sm" className="items-center">
            <Box className="flex-1">
              <Input className="bg-white">
                <InputField
                  placeholder="Search courses..."
                  value={searchQuery}
                  onChangeText={setSearchQuery}
                  returnKeyType="search"
                />
              </Input>
            </Box>
            <Button
              variant="outline"
              onPress={() => setShowFilters(true)}
              className={`px-3 ${hasActiveFilters ? 'border-blue-500 bg-blue-50' : ''}`}
            >
              <ButtonIcon
                as={Filter}
                className={hasActiveFilters ? 'text-blue-600' : 'text-gray-600'}
              />
            </Button>
          </HStack>

          {hasActiveFilters && (
            <HStack space="xs" className="flex-wrap">
              <Text className="text-gray-600 text-sm">Active filters:</Text>
              {filters.levels.map(level => (
                <Badge key={level} className="bg-blue-100">
                  <BadgeText className="text-blue-700 text-xs">
                    {EDUCATION_LEVELS[level as keyof typeof EDUCATION_LEVELS]?.shortName || level}
                  </BadgeText>
                </Badge>
              ))}
              {filters.subjects.map(subject => (
                <Badge key={subject} className="bg-green-100">
                  <BadgeText className="text-green-700 text-xs">{subject}</BadgeText>
                </Badge>
              ))}
              {filters.difficulty.map(diff => (
                <Badge key={diff} className="bg-purple-100">
                  <BadgeText className="text-purple-700 text-xs capitalize">{diff}</BadgeText>
                </Badge>
              ))}
            </HStack>
          )}
        </VStack>
      </Box>

      {/* Course List */}
      <Box className="flex-1 px-4">
        {isLoading ? (
          <VStack className="flex-1 items-center justify-center" space="md">
            <Spinner size="large" />
            <Text className="text-gray-600">Loading courses...</Text>
          </VStack>
        ) : filteredCourses.length === 0 ? (
          <VStack className="flex-1 items-center justify-center" space="md">
            <Icon as={Search} className="text-gray-400" size="xl" />
            <VStack space="xs" className="items-center">
              <Text className="text-gray-600 text-center font-medium">No courses found</Text>
              <Text className="text-gray-500 text-center text-sm">
                {searchQuery.trim() || hasActiveFilters
                  ? 'Try adjusting your search or filters'
                  : 'No courses available for this educational system'}
              </Text>
            </VStack>
            {(searchQuery.trim() || hasActiveFilters) && (
              <VStack space="sm">
                {searchQuery.trim() && (
                  <Button variant="outline" size="sm" onPress={() => setSearchQuery('')}>
                    <ButtonText>Clear search</ButtonText>
                  </Button>
                )}
                {hasActiveFilters && (
                  <Button
                    variant="outline"
                    size="sm"
                    onPress={() => setFilters({ levels: [], subjects: [], difficulty: [] })}
                  >
                    <ButtonText>Clear filters</ButtonText>
                  </Button>
                )}
              </VStack>
            )}
          </VStack>
        ) : viewMode === 'grouped' ? (
          <SectionList
            sections={groupedCourses}
            renderItem={renderCourseItem}
            renderSectionHeader={renderSectionHeader}
            keyExtractor={item => item.id.toString()}
            showsVerticalScrollIndicator={false}
            contentContainerStyle={{ paddingBottom: 100 }}
          />
        ) : (
          <FlatList
            data={filteredCourses}
            renderItem={renderCourseItem}
            keyExtractor={item => item.id.toString()}
            showsVerticalScrollIndicator={false}
            contentContainerStyle={{ paddingBottom: 100 }}
          />
        )}
      </Box>

      {/* Continue Button */}
      {selectedCourseIds.length > 0 && onSelectionComplete && (
        <Box className="bg-white px-4 py-4 border-t border-gray-200">
          <Button onPress={onSelectionComplete} className="w-full bg-blue-600 hover:bg-blue-700">
            <ButtonText className="text-white font-medium">
              Continue with {selectedCourseIds.length} course
              {selectedCourseIds.length !== 1 ? 's' : ''}
            </ButtonText>
          </Button>
        </Box>
      )}

      {/* Filter Modal */}
      <FilterModal
        isOpen={showFilters}
        onClose={() => setShowFilters(false)}
        filters={filters}
        onFiltersChange={setFilters}
        availableFilters={availableFilters}
      />
    </VStack>
  );
};
