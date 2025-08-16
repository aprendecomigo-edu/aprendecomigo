import { useState, useMemo } from 'react';

import { EnhancedCourse } from '@/api/tutorApi';

export interface SelectedCourse {
  id: string;
  course: EnhancedCourse;
  hourly_rate: number;
  expertise_level: 'beginner' | 'intermediate' | 'advanced' | 'expert';
  description?: string;
  is_featured: boolean;
  priority_order: number;
}

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

interface UseCourseManagerProps {
  selectedCourses: SelectedCourse[];
  customSubjects: CustomSubject[];
  onSelectionChange: (courses: SelectedCourse[], customSubjects: CustomSubject[]) => void;
  availableCourses: EnhancedCourse[];
  maxSelections?: number;
  defaultRate?: number;
}

export function useCourseManager({
  selectedCourses,
  customSubjects,
  onSelectionChange,
  availableCourses,
  maxSelections = 20,
  defaultRate = 15,
}: UseCourseManagerProps) {
  const [showCourseBrowser, setShowCourseBrowser] = useState(false);
  const [showCustomForm, setShowCustomForm] = useState(false);

  const allSelectedItems = useMemo(() => {
    const courseItems: (SelectedCourse | CustomSubject)[] = [...selectedCourses];
    const customItems: (SelectedCourse | CustomSubject)[] = [...customSubjects];

    return [...courseItems, ...customItems].sort((a, b) => a.priority_order - b.priority_order);
  }, [selectedCourses, customSubjects]);

  const selectedCourseIds = useMemo(() => selectedCourses.map(c => c.course.id), [selectedCourses]);

  const totalSelections = selectedCourses.length + customSubjects.length;
  const canAddMore = totalSelections < maxSelections;
  const canContinue = totalSelections > 0;

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
        item.id === itemId ? { ...item, ...updates } : item,
      );
      onSelectionChange(selectedCourses, updatedCustomSubjects);
    } else {
      const updatedCourses = selectedCourses.map(item =>
        item.id === itemId ? { ...item, ...updates } : item,
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

  return {
    // State
    showCourseBrowser,
    setShowCourseBrowser,
    showCustomForm,
    setShowCustomForm,
    
    // Computed values
    allSelectedItems,
    selectedCourseIds,
    totalSelections,
    canAddMore,
    canContinue,
    
    // Handlers
    handleCourseToggle,
    handleAddCustomSubject,
    handleItemUpdate,
    handleItemRemove,
  };
}