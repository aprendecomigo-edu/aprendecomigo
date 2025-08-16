import { useState, useEffect, useCallback } from 'react';
import { Alert } from 'react-native';

import CommunicationApi, {
  TeacherOnboardingProgress,
  FAQ,
  FAQCategory,
} from '@/api/communicationApi';

export const useTeacherOnboarding = (teacherId?: number, autoFetch = true) => {
  const [progress, setProgress] = useState<TeacherOnboardingProgress | null>(null);
  const [loading, setLoading] = useState(false);
  const [updating, setUpdating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchProgress = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const progressData = await CommunicationApi.getOnboardingProgress(teacherId);
      setProgress(progressData);
    } catch (err: any) {
      const errorMessage =
        err.response?.data?.detail || err.message || 'Failed to fetch onboarding progress';
      setError(errorMessage);
      console.error('Error fetching onboarding progress:', err);
    } finally {
      setLoading(false);
    }
  }, [teacherId]);

  const updateProgress = useCallback(async (step: number, data?: Record<string, any>) => {
    try {
      setUpdating(true);
      setError(null);

      const updatedProgress = await CommunicationApi.updateOnboardingProgress(step, data);
      setProgress(updatedProgress);

      return updatedProgress;
    } catch (err: any) {
      const errorMessage =
        err.response?.data?.detail || err.message || 'Failed to update onboarding progress';
      setError(errorMessage);
      console.error('Error updating onboarding progress:', err);
      throw err;
    } finally {
      setUpdating(false);
    }
  }, []);

  const markMilestoneAchieved = useCallback(async (milestone: string) => {
    try {
      setUpdating(true);
      setError(null);

      const updatedProgress = await CommunicationApi.markMilestoneAchieved(milestone);
      setProgress(updatedProgress);

      // Show celebration
      Alert.alert('🎉 Milestone Achieved!', `Congratulations! You've completed: ${milestone}`, [
        { text: 'Continue', style: 'default' },
      ]);

      return updatedProgress;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to mark milestone';
      setError(errorMessage);
      console.error('Error marking milestone:', err);
      throw err;
    } finally {
      setUpdating(false);
    }
  }, []);

  const nextStep = useCallback(
    async (stepData?: Record<string, any>) => {
      if (!progress) return false;

      const nextStepNumber = progress.current_step + 1;
      if (nextStepNumber > progress.total_steps) return false;

      try {
        await updateProgress(nextStepNumber, stepData);
        return true;
      } catch (error) {
        return false;
      }
    },
    [progress, updateProgress],
  );

  const previousStep = useCallback(async () => {
    if (!progress) return false;

    const prevStepNumber = progress.current_step - 1;
    if (prevStepNumber < 1) return false;

    try {
      await updateProgress(prevStepNumber);
      return true;
    } catch (error) {
      return false;
    }
  }, [progress, updateProgress]);

  const goToStep = useCallback(
    async (stepNumber: number) => {
      if (!progress || stepNumber < 1 || stepNumber > progress.total_steps) return false;

      try {
        await updateProgress(stepNumber);
        return true;
      } catch (error) {
        return false;
      }
    },
    [progress, updateProgress],
  );

  useEffect(() => {
    if (autoFetch) {
      fetchProgress();
    }
  }, [autoFetch, fetchProgress]);

  return {
    progress,
    loading,
    updating,
    error,
    fetchProgress,
    updateProgress,
    markMilestoneAchieved,
    nextStep,
    previousStep,
    goToStep,
    // Computed properties
    isCompleted: progress?.completed_at !== null,
    progressPercentage: progress
      ? (progress.completed_steps.length / progress.total_steps) * 100
      : 0,
    canGoNext: progress ? progress.current_step < progress.total_steps : false,
    canGoPrevious: progress ? progress.current_step > 1 : false,
    clearError: () => setError(null),
  };
};

export const useFAQSystem = (autoFetch = true) => {
  const [faqs, setFaqs] = useState<FAQ[]>([]);
  const [categories, setCategories] = useState<FAQCategory[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('');

  const fetchFAQs = useCallback(
    async (params?: { category?: string; search?: string; is_active?: boolean }) => {
      try {
        setLoading(true);
        setError(null);

        const faqsData = await CommunicationApi.getFAQs({
          is_active: true,
          ...params,
        });
        setFaqs(faqsData);
      } catch (err: any) {
        const errorMessage = err.response?.data?.detail || err.message || 'Failed to fetch FAQs';
        setError(errorMessage);
        console.error('Error fetching FAQs:', err);
      } finally {
        setLoading(false);
      }
    },
    [],
  );

  const fetchCategories = useCallback(async () => {
    try {
      const categoriesData = await CommunicationApi.getFAQCategories();
      setCategories(categoriesData);
    } catch (err: any) {
      console.error('Error fetching FAQ categories:', err);
    }
  }, []);

  const searchFAQs = useCallback(
    async (query: string) => {
      if (!query.trim()) {
        fetchFAQs();
        return;
      }

      try {
        setLoading(true);
        setError(null);

        const searchResults = await CommunicationApi.searchFAQs(query);
        setFaqs(searchResults);
        setSearchQuery(query);
      } catch (err: any) {
        const errorMessage = err.response?.data?.detail || err.message || 'Failed to search FAQs';
        setError(errorMessage);
        console.error('Error searching FAQs:', err);
      } finally {
        setLoading(false);
      }
    },
    [fetchFAQs],
  );

  const markFAQHelpful = useCallback(async (faqId: number, helpful: boolean) => {
    try {
      await CommunicationApi.markFAQHelpful(faqId, helpful);

      // Update FAQ in local state
      setFaqs(prevFaqs =>
        prevFaqs.map(faq =>
          faq.id === faqId
            ? {
                ...faq,
                helpful_count: helpful ? faq.helpful_count + 1 : Math.max(0, faq.helpful_count - 1),
              }
            : faq,
        ),
      );
    } catch (err: any) {
      console.error('Error marking FAQ as helpful:', err);
    }
  }, []);

  const filterByCategory = useCallback(
    (category: string) => {
      setSelectedCategory(category);
      fetchFAQs({
        category: category || undefined,
        search: searchQuery || undefined,
      });
    },
    [fetchFAQs, searchQuery],
  );

  const clearFilters = useCallback(() => {
    setSearchQuery('');
    setSelectedCategory('');
    fetchFAQs();
  }, [fetchFAQs]);

  useEffect(() => {
    if (autoFetch) {
      fetchFAQs();
      fetchCategories();
    }
  }, [autoFetch, fetchFAQs, fetchCategories]);

  return {
    faqs,
    categories,
    loading,
    error,
    searchQuery,
    selectedCategory,
    fetchFAQs,
    searchFAQs,
    markFAQHelpful,
    filterByCategory,
    clearFilters,
    setSearchQuery,
    clearError: () => setError(null),
  };
};

export const useContextualHelp = () => {
  const [contextualFAQs, setContextualFAQs] = useState<FAQ[]>([]);
  const [loading, setLoading] = useState(false);
  const [currentContext, setCurrentContext] = useState<string>('');

  const getContextualHelp = useCallback(async (context: string, step?: number) => {
    try {
      setLoading(true);
      setCurrentContext(context);

      const contextualData = await CommunicationApi.getContextualFAQs(context, step);
      setContextualFAQs(contextualData);
    } catch (err: any) {
      console.error('Error fetching contextual help:', err);
      setContextualFAQs([]);
    } finally {
      setLoading(false);
    }
  }, []);

  const clearContextualHelp = useCallback(() => {
    setContextualFAQs([]);
    setCurrentContext('');
  }, []);

  return {
    contextualFAQs,
    loading,
    currentContext,
    getContextualHelp,
    clearContextualHelp,
  };
};

export const useOnboardingCelebrations = () => {
  const [showCelebration, setShowCelebration] = useState(false);
  const [celebrationData, setCelebrationData] = useState<{
    type: 'milestone' | 'completion' | 'step';
    title: string;
    message: string;
    animation?: string;
  } | null>(null);

  const celebrateMilestone = useCallback((milestone: string) => {
    setCelebrationData({
      type: 'milestone',
      title: '🎉 Milestone Achieved!',
      message: `Congratulations! You've completed: ${milestone}`,
      animation: 'confetti',
    });
    setShowCelebration(true);
  }, []);

  const celebrateCompletion = useCallback(() => {
    setCelebrationData({
      type: 'completion',
      title: '🚀 Profile Complete!',
      message: 'Amazing work! Your teacher profile is now complete and ready to go.',
      animation: 'fireworks',
    });
    setShowCelebration(true);
  }, []);

  const celebrateStep = useCallback((stepName: string) => {
    setCelebrationData({
      type: 'step',
      title: '✅ Step Complete!',
      message: `Great job completing: ${stepName}`,
      animation: 'checkmark',
    });
    setShowCelebration(true);
  }, []);

  const closeCelebration = useCallback(() => {
    setShowCelebration(false);
    setCelebrationData(null);
  }, []);

  return {
    showCelebration,
    celebrationData,
    celebrateMilestone,
    celebrateCompletion,
    celebrateStep,
    closeCelebration,
  };
};

export const useOnboardingHelpers = () => {
  const getStepName = useCallback((step: number): string => {
    const stepNames = {
      1: 'Basic Information',
      2: 'Teaching Subjects',
      3: 'Grade Levels',
      4: 'Availability',
      5: 'Rates & Compensation',
      6: 'Credentials',
      7: 'Profile Marketing',
      8: 'Review & Submit',
    };

    return stepNames[step as keyof typeof stepNames] || `Step ${step}`;
  }, []);

  const getMilestoneMessage = useCallback((milestone: string): string => {
    const milestoneMessages = {
      basic_info_complete: "You've provided your basic information!",
      subjects_selected: "You've selected your teaching subjects!",
      availability_set: "You've set your availability preferences!",
      credentials_added: "You've added your teaching credentials!",
      profile_complete: 'Your profile is now complete!',
    };

    return milestoneMessages[milestone as keyof typeof milestoneMessages] || milestone;
  }, []);

  const getProgressMessage = useCallback((progress: TeacherOnboardingProgress): string => {
    const completedPercentage = (progress.completed_steps.length / progress.total_steps) * 100;

    if (completedPercentage === 0) {
      return "Let's get started with your teacher profile!";
    } else if (completedPercentage < 50) {
      return "You're making great progress!";
    } else if (completedPercentage < 100) {
      return "You're almost there!";
    } else {
      return 'Congratulations! Your profile is complete!';
    }
  }, []);

  const getNextStepHint = useCallback((currentStep: number): string => {
    const hints = {
      1: "Next, you'll select the subjects you teach.",
      2: 'Coming up: choose the grade levels you work with.',
      3: 'Next, set your availability preferences.',
      4: "You'll then set your rates and compensation.",
      5: 'After this, add your teaching credentials.',
      6: 'Almost done! Create your profile marketing content.',
      7: 'Finally, review and submit your complete profile.',
    };

    return hints[currentStep as keyof typeof hints] || 'Continue with the next step.';
  }, []);

  return {
    getStepName,
    getMilestoneMessage,
    getProgressMessage,
    getNextStepHint,
  };
};
