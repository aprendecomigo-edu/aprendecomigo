import useRouter from '@unitools/router';
import {
  User,
  FileText,
  GraduationCap,
  BookOpen,
  DollarSign,
  Calendar,
  Eye,
  ArrowLeft,
  ArrowRight,
  Save,
  AlertCircle,
  CheckCircle2,
} from 'lucide-react-native';
import React, { useState, useEffect, useRef } from 'react';

import { AvailabilityStep } from '@/components/profile-wizard/AvailabilityStep';
import { BasicInfoStep } from '@/components/profile-wizard/BasicInfoStep';
import { BiographyStep } from '@/components/profile-wizard/BiographyStep';
import { EducationStep } from '@/components/profile-wizard/EducationStep';
import { ProfileCompletionTracker } from '@/components/profile-wizard/ProfileCompletionTracker';
import { ProfilePreviewStep } from '@/components/profile-wizard/ProfilePreviewStep';
import { RatesStep } from '@/components/profile-wizard/RatesStep';
import { SubjectsStep } from '@/components/profile-wizard/SubjectsStep';
import WizardErrorBoundary from '@/components/wizard/WizardErrorBoundary';
import { useProfileWizard } from '@/hooks/useProfileWizard';

// Wizard step configuration
export const WIZARD_STEPS = [
  {
    id: 'basic-info',
    title: 'Basic Information',
    description: 'Profile photo, name, title, and contact details',
    icon: User,
    component: BasicInfoStep,
    isRequired: true,
  },
  {
    id: 'biography',
    title: 'Professional Biography',
    description: 'Tell students about your teaching approach and experience',
    icon: FileText,
    component: BiographyStep,
    isRequired: true,
  },
  {
    id: 'education',
    title: 'Education Background',
    description: 'Degrees, certifications, and qualifications',
    icon: GraduationCap,
    component: EducationStep,
    isRequired: true,
  },
  {
    id: 'subjects',
    title: 'Teaching Subjects',
    description: 'Subjects you teach and grade levels you work with',
    icon: BookOpen,
    component: SubjectsStep,
    isRequired: true,
  },
  {
    id: 'rates',
    title: 'Rates & Pricing',
    description: 'Set your hourly rates and package options',
    icon: DollarSign,
    component: RatesStep,
    isRequired: true,
  },
  {
    id: 'availability',
    title: 'Availability',
    description: 'Weekly schedule and booking preferences',
    icon: Calendar,
    component: AvailabilityStep,
    isRequired: true,
  },
  {
    id: 'preview',
    title: 'Profile Preview',
    description: 'Review how your profile appears to students',
    icon: Eye,
    component: ProfilePreviewStep,
    isRequired: false,
  },
];

export interface TeacherProfileWizardProps {
  onComplete?: () => void;
  onExit?: () => void;
  resumeFromStep?: number;
}

// Shared icons for export
export const WizardIcons = {
  User,
  FileText,
  GraduationCap,
  BookOpen,
  DollarSign,
  Calendar,
  Eye,
  ArrowLeft,
  ArrowRight,
  Save,
  AlertCircle,
  CheckCircle2,
};

// Custom hook for teacher profile wizard business logic
export function useTeacherProfileWizard({
  onComplete,
  onExit,
  resumeFromStep = 0,
}: TeacherProfileWizardProps) {
  const router = useRouter();
  const autoSaveInterval = useRef<NodeJS.Timeout | null>(null);

  const {
    currentStep,
    formData,
    completionData,
    isLoading,
    isSaving,
    error,
    validationErrors,
    setCurrentStep,
    updateFormData,
    validateStep,
    saveProgress,
    submitProfile,
    loadProgress,
  } = useProfileWizard();

  const [showExitDialog, setShowExitDialog] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  // Computed state values
  const isAutoSaving = isSaving && hasUnsavedChanges;
  const hasCriticalErrors = error !== null && !isLoading;

  // Initialize wizard
  useEffect(() => {
    const initializeWizard = async () => {
      try {
        await loadProgress();
        if (resumeFromStep > 0) {
          setCurrentStep(resumeFromStep);
        }
      } catch (error) {
        console.error('Error initializing wizard:', error);
      }
    };

    initializeWizard();
  }, [loadProgress, resumeFromStep, setCurrentStep]);

  // Auto-save functionality
  useEffect(() => {
    if (hasUnsavedChanges && !isSaving) {
      // Clear existing timeout
      if (autoSaveInterval.current) {
        clearTimeout(autoSaveInterval.current);
      }

      // Set new timeout for auto-save
      autoSaveInterval.current = setTimeout(async () => {
        try {
          await saveProgress();
          setHasUnsavedChanges(false);
        } catch (error) {
          console.error('Auto-save failed:', error);
        }
      }, 30000); // Auto-save every 30 seconds
    }

    return () => {
      if (autoSaveInterval.current) {
        clearTimeout(autoSaveInterval.current);
      }
    };
  }, [hasUnsavedChanges, isSaving, saveProgress]);

  // Handle form data changes
  const handleFormDataChange = (stepData: any) => {
    updateFormData(stepData);
    setHasUnsavedChanges(true);
  };

  // Handle next step
  const handleNextStep = async () => {
    try {
      const isValid = await validateStep(currentStep);
      if (!isValid) {
        return;
      }

      // Save progress before moving to next step
      await saveProgress();
      setHasUnsavedChanges(false);

      if (currentStep < WIZARD_STEPS.length - 1) {
        setCurrentStep(currentStep + 1);
      } else {
        // Final step - submit profile
        await handleComplete();
      }
    } catch (error) {
      console.error('Error moving to next step:', error);
    }
  };

  // Handle previous step
  const handlePreviousStep = async () => {
    if (hasUnsavedChanges) {
      await saveProgress();
      setHasUnsavedChanges(false);
    }

    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  // Handle manual save
  const handleSaveProgress = async () => {
    try {
      await saveProgress();
      setHasUnsavedChanges(false);
    } catch (error) {
      console.error('Error saving progress:', error);
    }
  };

  // Handle wizard completion
  const handleComplete = async () => {
    try {
      await submitProfile();

      if (onComplete) {
        onComplete();
      } else {
        // Default navigation to dashboard
        router.push('/(school-admin)/dashboard');
      }
    } catch (error) {
      console.error('Error completing profile wizard:', error);
    }
  };

  // Handle exit wizard
  const handleExitWizard = () => {
    if (hasUnsavedChanges) {
      setShowExitDialog(true);
    } else {
      if (onExit) {
        onExit();
      } else {
        router.back();
      }
    }
  };

  // Confirm exit without saving
  const confirmExit = () => {
    setShowExitDialog(false);
    if (onExit) {
      onExit();
    } else {
      router.back();
    }
  };

  // Save and exit
  const saveAndExit = async () => {
    try {
      await saveProgress();
      setShowExitDialog(false);
      if (onExit) {
        onExit();
      } else {
        router.back();
      }
    } catch (error) {
      console.error('Error saving before exit:', error);
    }
  };

  // Error boundary handlers
  const handleErrorBoundaryReset = () => {
    // Clear local state and try to reload from the hook
    setHasUnsavedChanges(false);
    setShowExitDialog(false);
    loadProgress().catch(console.error);
  };

  const handleErrorBoundarySaveAndExit = async () => {
    try {
      // Attempt to save current progress before exiting
      await saveProgress();
    } catch (error) {
      console.error('Failed to save progress during error recovery:', error);
    } finally {
      // Exit regardless of save success
      if (onExit) {
        onExit();
      } else {
        router.back();
      }
    }
  };

  const handleErrorBoundaryGoToDashboard = () => {
    // Navigate to dashboard without saving
    router.push('/(school-admin)/dashboard');
  };

  const currentStepConfig = WIZARD_STEPS[currentStep];
  const StepComponent = currentStepConfig?.component;
  const progressPercentage = ((currentStep + 1) / WIZARD_STEPS.length) * 100;

  return {
    // State
    currentStep,
    formData,
    completionData,
    isLoading,
    isSaving,
    error,
    validationErrors,
    showExitDialog,
    setShowExitDialog,
    hasUnsavedChanges,
    isAutoSaving,
    hasCriticalErrors,
    currentStepConfig,
    StepComponent,
    progressPercentage,

    // Handlers
    handleFormDataChange,
    handleNextStep,
    handlePreviousStep,
    handleSaveProgress,
    handleComplete,
    handleExitWizard,
    confirmExit,
    saveAndExit,
    handleErrorBoundaryReset,
    handleErrorBoundarySaveAndExit,
    handleErrorBoundaryGoToDashboard,

    // Direct access to hook actions
    setCurrentStep,
  };
}