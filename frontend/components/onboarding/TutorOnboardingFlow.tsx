import { useRouter } from 'expo-router';
import { AlertCircle, ArrowLeft } from 'lucide-react-native';
import React, { useState, useEffect, useCallback } from 'react';
import { Platform } from 'react-native';

import { CourseCatalogBrowser, Course } from './CourseCatalogBrowser';
import { CourseSelectionManager } from './CourseSelectionManager';
import { EducationalSystemSelector, EducationalSystem } from './EducationalSystemSelector';
import { OnboardingSuccessScreen } from './OnboardingSuccessScreen';
import { RateConfigurationManager } from './RateConfigurationManager';
import {
  TutorOnboardingProgress,
  TutorOnboardingData,
  DEFAULT_TUTOR_ONBOARDING_STEPS,
} from './tutor-onboarding-progress';

import { useAuth, useUserProfile } from '@/api/auth';
import {
  createTutorSchool,
  getCourseCatalog,
  getEducationalSystems,
  saveTutorOnboardingProgress,
  completeTutorOnboarding,
  type TutorSchoolData,
  type TutorOnboardingData as ApiTutorOnboardingData,
  type ProfilePublishingOptions,
} from '@/api/tutorApi';
import { TutorSchoolCreationModal } from '@/components/modals/TutorSchoolCreationModal';
import {
  AlertDialog,
  AlertDialogBackdrop,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogBody,
  AlertDialogFooter,
} from '@/components/ui/alert-dialog';
import { Box } from '@/components/ui/box';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Pressable } from '@/components/ui/pressable';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { useToast } from '@/components/ui/toast';
import { VStack } from '@/components/ui/vstack';

// API client imports

// Onboarding step IDs
export type TutorOnboardingStep =
  | 'school-setup'
  | 'educational-system'
  | 'subject-selection'
  | 'rate-configuration'
  | 'teacher-profile'
  | 'success';

interface TutorOnboardingFlowProps {
  initialStep?: TutorOnboardingStep;
  onComplete?: () => void;
  onExit?: () => void;
  userName?: string;
  userEmail?: string;
}

interface OnboardingState {
  currentStep: TutorOnboardingStep;
  schoolData?: {
    schoolName: string;
    description?: string;
    website?: string;
  };
  selectedEducationalSystem?: EducationalSystem;
  availableCourses: Course[];
  selectedCourses: Course[];
  courseRates: Array<{
    courseId: number;
    rate: number;
    currency: string;
    isCustom: boolean;
  }>;
  isLoading: boolean;
  error?: string;
}

// Load courses from API based on educational system

export const TutorOnboardingFlow: React.FC<TutorOnboardingFlowProps> = ({
  initialStep = 'school-setup',
  onComplete,
  onExit,
  userName = '',
  userEmail = '',
}) => {
  const router = useRouter();
  const toast = useToast();
  const { checkAuthStatus } = useAuth();
  const { userProfile } = useUserProfile();

  const [state, setState] = useState<OnboardingState>({
    currentStep: initialStep,
    availableCourses: [],
    selectedCourses: [],
    courseRates: [],
    isLoading: false,
  });

  const [showExitDialog, setShowExitDialog] = useState(false);
  const [showSchoolModal, setShowSchoolModal] = useState(false);

  // Generate onboarding progress data
  const generateOnboardingData = useCallback((): TutorOnboardingData => {
    const steps = DEFAULT_TUTOR_ONBOARDING_STEPS.map((step, index) => ({
      ...step,
      isCompleted: getStepIndex(state.currentStep) > index,
      canAccess: getStepIndex(state.currentStep) >= index,
      completedAt: getStepIndex(state.currentStep) > index ? new Date() : undefined,
    }));

    const completedSteps = steps.filter(step => step.isCompleted).length;
    const totalSteps = steps.length;
    const overallProgress = (completedSteps / totalSteps) * 100;
    const estimatedTimeRemaining = steps
      .filter(step => !step.isCompleted)
      .reduce((total, step) => total + step.estimatedTime, 0);

    return {
      steps,
      currentStepId: mapStepToId(state.currentStep),
      overallProgress,
      completedSteps,
      totalSteps,
      estimatedTimeRemaining,
      startedAt: new Date(),
    };
  }, [state.currentStep]);

  // Helper functions
  const getStepIndex = (step: TutorOnboardingStep): number => {
    const stepOrder: TutorOnboardingStep[] = [
      'school-setup',
      'educational-system',
      'subject-selection',
      'rate-configuration',
      'teacher-profile',
      'success',
    ];
    return stepOrder.indexOf(step);
  };

  const mapStepToId = (step: TutorOnboardingStep): string => {
    const mapping: Record<TutorOnboardingStep, string> = {
      'school-setup': 'school-setup',
      'educational-system': 'educational-system',
      'subject-selection': 'subject-selection',
      'rate-configuration': 'rate-configuration',
      'teacher-profile': 'teacher-profile',
      success: 'profile-review',
    };
    return mapping[step];
  };

  // Load courses when educational system is selected
  useEffect(() => {
    const loadCourses = async () => {
      if (!state.selectedEducationalSystem) return;

      try {
        setState(prev => ({ ...prev, isLoading: true, error: undefined }));

        const coursesResponse = await getCourseCatalog({
          educational_system: state.selectedEducationalSystem.id,
          with_market_data: true,
          page_size: 100, // Load all courses for the system
        });

        setState(prev => ({
          ...prev,
          availableCourses: coursesResponse.results,
          isLoading: false,
        }));
      } catch (error: any) {
        console.error('Error loading courses:', error);
        setState(prev => ({
          ...prev,
          availableCourses: [],
          isLoading: false,
          error: 'Failed to load courses. Please try again.',
        }));

        toast.showToast('error', 'Failed to load courses. Please try again.');
      }
    };

    loadCourses();
  }, [state.selectedEducationalSystem, toast]);

  // Step navigation handlers
  const handleNext = () => {
    const stepOrder: TutorOnboardingStep[] = [
      'school-setup',
      'educational-system',
      'subject-selection',
      'rate-configuration',
      'teacher-profile',
      'success',
    ];

    const currentIndex = stepOrder.indexOf(state.currentStep);
    if (currentIndex < stepOrder.length - 1) {
      setState(prev => ({
        ...prev,
        currentStep: stepOrder[currentIndex + 1],
      }));
    }
  };

  const handlePrevious = () => {
    const stepOrder: TutorOnboardingStep[] = [
      'school-setup',
      'educational-system',
      'subject-selection',
      'rate-configuration',
      'teacher-profile',
      'success',
    ];

    const currentIndex = stepOrder.indexOf(state.currentStep);
    if (currentIndex > 0) {
      setState(prev => ({
        ...prev,
        currentStep: stepOrder[currentIndex - 1],
      }));
    }
  };

  const handleStepJump = (stepId: string) => {
    const stepMapping: Record<string, TutorOnboardingStep> = {
      'school-setup': 'school-setup',
      'educational-system': 'educational-system',
      'subject-selection': 'subject-selection',
      'rate-configuration': 'rate-configuration',
      'teacher-profile': 'teacher-profile',
      'profile-review': 'success',
    };

    const step = stepMapping[stepId];
    if (step) {
      setState(prev => ({ ...prev, currentStep: step }));
    }
  };

  // Step-specific handlers
  const handleSchoolCreation = async (schoolData: TutorSchoolData) => {
    try {
      setState(prev => ({ ...prev, isLoading: true, error: undefined }));

      const response = await createTutorSchool(schoolData);

      if (response.success) {
        setState(prev => ({
          ...prev,
          schoolData,
          isLoading: false,
        }));

        setShowSchoolModal(false);
        handleNext();

        toast.showToast('success', 'Tutoring practice created successfully!');
      } else {
        throw new Error(response.message || 'Failed to create practice');
      }
    } catch (error: any) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error.message || 'Failed to create practice',
      }));

      toast.showToast('error', 'Failed to create tutoring practice. Please try again.');
    }
  };

  const handleEducationalSystemSelect = (system: EducationalSystem) => {
    setState(prev => ({
      ...prev,
      selectedEducationalSystem: system,
      selectedCourses: [], // Reset course selection
      courseRates: [], // Reset rates
    }));
  };

  const handleCourseSelectionChange = (courses: Course[]) => {
    setState(prev => ({
      ...prev,
      selectedCourses: courses,
      // Initialize rates for new courses
      courseRates: courses.map(course => ({
        courseId: course.id,
        rate: 30, // Default rate
        currency: 'EUR',
        isCustom: false,
      })),
    }));
  };

  const handleRateConfigurationChange = (rates: any[]) => {
    setState(prev => ({
      ...prev,
      courseRates: rates,
    }));
  };

  const handleCompleteOnboarding = async () => {
    try {
      setState(prev => ({ ...prev, isLoading: true }));

      // Prepare onboarding data in the format expected by the API
      const onboardingData: Partial<ApiTutorOnboardingData> = {
        business_profile: {
          practice_name: state.schoolData?.schoolName || 'My Tutoring Practice',
          description: state.schoolData?.description,
          website: state.schoolData?.website,
          specializations: state.selectedCourses.map(course => course.subject_area || course.name),
          target_students: ['individual', 'group'], // Default values
          teaching_approach: 'Personalized and interactive learning approach', // Default
        },
        course_selection: {
          educational_system_id: state.selectedEducationalSystem?.id || 1,
          selected_courses: state.selectedCourses.map(course => {
            const courseRate = state.courseRates.find(rate => rate.courseId === course.id);
            return {
              course_id: course.id,
              hourly_rate: courseRate?.rate || 30,
              expertise_level: course.difficulty_level || 'intermediate',
              description: course.description,
            };
          }),
        },
        pricing: {
          default_rate:
            state.courseRates.length > 0
              ? state.courseRates.reduce((sum, rate) => sum + rate.rate, 0) /
                state.courseRates.length
              : 30,
          currency: state.courseRates.length > 0 ? state.courseRates[0].currency : 'EUR',
          payment_methods: ['stripe', 'paypal'], // Default
          cancellation_policy: 'Standard 24-hour cancellation policy', // Default
        },
      };

      const publishingOptions: ProfilePublishingOptions = {
        make_discoverable: true,
        auto_accept_bookings: false,
        notification_preferences: {
          email_notifications: true,
          sms_notifications: false,
          booking_confirmations: true,
          student_messages: true,
        },
        marketing_consent: {
          promotional_emails: true,
          feature_updates: true,
          educational_content: true,
        },
      };

      const response = await completeTutorOnboarding({
        final_data: onboardingData as ApiTutorOnboardingData,
        publishing_options: publishingOptions,
      });

      if (response.success) {
        setState(prev => ({
          ...prev,
          currentStep: 'success',
          isLoading: false,
        }));

        // Update auth status
        await checkAuthStatus();

        toast.showToast('success', 'Tutor profile completed successfully!');
      } else {
        throw new Error('Failed to complete profile');
      }
    } catch (error: any) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error.message || 'Failed to complete profile',
      }));

      toast.showToast('error', 'Failed to complete profile. Please try again.');
    }
  };

  const handleExit = () => {
    if (onExit) {
      onExit();
    } else {
      router.back();
    }
  };

  const handleComplete = () => {
    if (onComplete) {
      onComplete();
    } else {
      router.push('/home');
    }
  };

  // Render current step
  const renderCurrentStep = () => {
    switch (state.currentStep) {
      case 'school-setup':
        return (
          <VStack className="flex-1 items-center justify-center p-4" space="lg">
            <VStack className="items-center text-center" space="md">
              <Heading size="xl" className="text-gray-900">
                Set Up Your Tutoring Practice
              </Heading>
              <Text className="text-gray-600 max-w-md text-center">
                Create your professional tutoring business profile to get started
              </Text>
            </VStack>

            <Button
              onPress={() => setShowSchoolModal(true)}
              className="bg-blue-600 hover:bg-blue-700"
              size="lg"
              disabled={state.isLoading}
            >
              <ButtonText className="text-white">Create My Practice</ButtonText>
            </Button>
          </VStack>
        );

      case 'educational-system':
        return (
          <EducationalSystemSelector
            selectedSystemId={state.selectedEducationalSystem?.id}
            onSystemSelect={handleEducationalSystemSelect}
            onContinue={handleNext}
            isLoading={state.isLoading}
          />
        );

      case 'subject-selection':
        if (!state.selectedEducationalSystem) {
          return (
            <VStack className="flex-1 items-center justify-center p-4" space="md">
              <Icon as={AlertCircle} className="text-orange-500" size="xl" />
              <Text className="text-gray-600 text-center">
                Please select an educational system first
              </Text>
              <Button variant="outline" onPress={handlePrevious}>
                <ButtonText>Go Back</ButtonText>
              </Button>
            </VStack>
          );
        }

        return (
          <CourseSelectionManager
            educationalSystem={state.selectedEducationalSystem}
            availableCourses={state.availableCourses}
            selectedCourses={state.selectedCourses}
            onCoursesChange={handleCourseSelectionChange}
            onContinue={handleNext}
            isLoading={state.isLoading}
            minSelections={1}
            maxSelections={10}
          />
        );

      case 'rate-configuration':
        if (state.selectedCourses.length === 0) {
          return (
            <VStack className="flex-1 items-center justify-center p-4" space="md">
              <Icon as={AlertCircle} className="text-orange-500" size="xl" />
              <Text className="text-gray-600 text-center">
                Please select your teaching subjects first
              </Text>
              <Button variant="outline" onPress={handlePrevious}>
                <ButtonText>Go Back</ButtonText>
              </Button>
            </VStack>
          );
        }

        return (
          <RateConfigurationManager
            courses={state.selectedCourses}
            initialRates={state.courseRates}
            onRatesChange={handleRateConfigurationChange}
            onContinue={handleNext}
            isLoading={state.isLoading}
          />
        );

      case 'teacher-profile':
        return (
          <VStack className="flex-1 items-center justify-center p-4" space="lg">
            <VStack className="items-center text-center" space="md">
              <Heading size="xl" className="text-gray-900">
                Complete Your Teacher Profile
              </Heading>
              <Text className="text-gray-600 max-w-md text-center">
                Add your professional details, experience, and teaching approach
              </Text>
            </VStack>

            <VStack space="sm">
              <Button
                onPress={handleCompleteOnboarding}
                className="bg-green-600 hover:bg-green-700"
                size="lg"
                disabled={state.isLoading}
              >
                {state.isLoading ? (
                  <>
                    <Spinner size="small" className="text-white mr-2" />
                    <ButtonText className="text-white">Completing...</ButtonText>
                  </>
                ) : (
                  <ButtonText className="text-white">Complete Teacher Profile</ButtonText>
                )}
              </Button>

              <Text className="text-center text-gray-500 text-sm">
                This will integrate with the existing Teacher Profile Wizard
              </Text>
            </VStack>
          </VStack>
        );

      case 'success':
        const profileSummary = {
          schoolName: state.schoolData?.schoolName || 'My Tutoring Practice',
          educationalSystem: state.selectedEducationalSystem?.name || 'Educational System',
          subjectCount: state.selectedCourses.length,
          averageRate:
            state.courseRates.length > 0
              ? state.courseRates.reduce((sum, rate) => sum + rate.rate, 0) /
                state.courseRates.length
              : 30,
          currency: state.courseRates.length > 0 ? state.courseRates[0].currency : 'EUR',
          completionScore: 95,
        };

        return (
          <OnboardingSuccessScreen
            profileSummary={profileSummary}
            onContinueToDashboard={handleComplete}
            userName={userName || userProfile?.name || 'Tutor'}
          />
        );

      default:
        return (
          <VStack className="flex-1 items-center justify-center p-4" space="md">
            <Icon as={AlertCircle} className="text-red-500" size="xl" />
            <Text className="text-gray-600 text-center">Unknown step: {state.currentStep}</Text>
          </VStack>
        );
    }
  };

  if (state.isLoading && state.currentStep !== 'teacher-profile') {
    return (
      <VStack className="flex-1 items-center justify-center" space="md">
        <Spinner size="large" />
        <Text className="text-gray-600">Setting up your tutoring profile...</Text>
      </VStack>
    );
  }

  return (
    <Box className="flex-1 bg-gray-50">
      {/* Header */}
      {state.currentStep !== 'success' && (
        <Box className="bg-white border-b border-gray-200 px-4 py-4">
          <HStack className="items-center justify-between">
            <Pressable onPress={() => setShowExitDialog(true)}>
              <HStack space="sm" className="items-center">
                <Icon as={ArrowLeft} className="text-gray-600" size="lg" />
                <Text className="text-gray-600">Exit Setup</Text>
              </HStack>
            </Pressable>

            <Text className="text-gray-600 text-sm">Individual Tutor Onboarding</Text>
          </HStack>
        </Box>
      )}

      {/* Progress Indicator (for non-success steps) */}
      {state.currentStep !== 'success' && state.currentStep !== 'school-setup' && (
        <Box className="bg-white border-b border-gray-200 px-4 py-3">
          <TutorOnboardingProgress
            onboarding={generateOnboardingData()}
            onStepClick={handleStepJump}
            compact={true}
            showTimeEstimates={false}
          />
        </Box>
      )}

      {/* Step Content */}
      <Box className="flex-1">
        {state.error && (
          <Box className="bg-red-50 border-l-4 border-red-400 p-4 mx-4 mt-4">
            <HStack space="sm" className="items-center">
              <Icon as={AlertCircle} size={20} className="text-red-500" />
              <Text className="text-red-700">{state.error}</Text>
            </HStack>
          </Box>
        )}

        {renderCurrentStep()}
      </Box>

      {/* Navigation Footer */}
      {state.currentStep !== 'success' && state.currentStep !== 'school-setup' && (
        <Box className="bg-white border-t border-gray-200 px-4 py-4">
          <HStack className="items-center justify-between">
            <Button
              variant="outline"
              onPress={handlePrevious}
              disabled={getStepIndex(state.currentStep) === 0 || state.isLoading}
            >
              <ButtonIcon as={ArrowLeft} className="text-gray-600 mr-1" />
              <ButtonText className="text-gray-600">Previous</ButtonText>
            </Button>

            {/* Step info */}
            <Text className="text-gray-500 text-sm">
              Step {getStepIndex(state.currentStep) + 1} of 6
            </Text>
          </HStack>
        </Box>
      )}

      {/* Modals */}
      <TutorSchoolCreationModal
        isOpen={showSchoolModal}
        onClose={() => setShowSchoolModal(false)}
        onSubmit={handleSchoolCreation}
        userName={userName || userProfile?.name || ''}
        isLoading={state.isLoading}
      />

      {/* Exit Confirmation Dialog */}
      <AlertDialog isOpen={showExitDialog} onClose={() => setShowExitDialog(false)}>
        <AlertDialogBackdrop />
        <AlertDialogContent>
          <AlertDialogHeader>
            <Heading size="lg" className="text-gray-900">
              Exit Onboarding?
            </Heading>
          </AlertDialogHeader>
          <AlertDialogBody>
            <Text className="text-gray-600">
              Your progress will be saved, but you'll need to complete the setup later to start
              teaching and accepting students.
            </Text>
          </AlertDialogBody>
          <AlertDialogFooter>
            <HStack space="sm" className="w-full">
              <Button variant="outline" onPress={() => setShowExitDialog(false)} className="flex-1">
                <ButtonText>Continue Setup</ButtonText>
              </Button>
              <Button onPress={handleExit} className="flex-1 bg-gray-600">
                <ButtonText className="text-white">Exit</ButtonText>
              </Button>
            </HStack>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </Box>
  );
};
