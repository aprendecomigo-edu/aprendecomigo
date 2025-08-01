import { useState, useCallback, useEffect } from 'react';
import { Alert } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

import {
  TeacherProfileData,
  ContactPreferences,
  SubjectExpertise,
  GradeLevel,
  WeeklySchedule,
  PaymentPreferences,
  EducationEntry,
  ExperienceEntry,
  CertificationFile,
} from '@/api/invitationApi';

// Form validation errors
export interface InvitationWizardValidationErrors {
  [stepNumber: number]: {
    [fieldName: string]: string;
  };
}

// Default empty profile data for invitation acceptance
const getDefaultProfileData = (): TeacherProfileData => ({
  // Step 1: Basic Information
  contact_preferences: {
    email_notifications: true,
    sms_notifications: false,
    call_notifications: false,
    preferred_contact_method: 'email',
  },
  introduction: '',
  
  // Step 2: Teaching Subjects
  teaching_subjects: [],
  custom_subjects: [],
  
  // Step 3: Grade Level Preferences
  grade_levels: [],
  
  // Step 4: Availability & Scheduling
  timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC',
  availability_notes: '',
  
  // Step 5: Rates & Compensation
  hourly_rate: 25,
  rate_negotiable: true,
  payment_preferences: {
    preferred_payment_method: 'bank_transfer',
    invoice_frequency: 'monthly',
    tax_information_provided: false,
  },
  
  // Step 6: Credentials & Experience
  education_background: [],
  teaching_experience: [],
  certifications: [],
  
  // Step 7: Profile Marketing
  teaching_philosophy: '',
  teaching_approach: '',
  specializations: [],
  achievements: [],
});

// Common teaching subjects for quick selection
export const COMMON_SUBJECTS = [
  'Matemática',
  'Português',
  'Inglês',
  'Ciências',
  'História',
  'Geografia',
  'Física',
  'Química',
  'Biologia',
  'Filosofia',
  'Sociologia',
  'Arte',
  'Educação Física',
  'Música',
  'Informática',
];

// Timezone options
export const TIMEZONE_OPTIONS = [
  { label: 'Lisboa (WET/WEST)', value: 'Europe/Lisbon' },
  { label: 'Madrid (CET/CEST)', value: 'Europe/Madrid' },
  { label: 'São Paulo (BRT)', value: 'America/Sao_Paulo' },
  { label: 'Rio de Janeiro (BRT)', value: 'America/Sao_Paulo' },
  { label: 'UTC', value: 'UTC' },
];

export const useInvitationProfileWizard = (invitationToken: string) => {
  const [currentStep, setCurrentStep] = useState(1);
  const [profileData, setProfileData] = useState<TeacherProfileData>(getDefaultProfileData());
  const [validationErrors, setValidationErrors] = useState<InvitationWizardValidationErrors>({});
  const [loading, setLoading] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  const totalSteps = 8;
  const storageKey = `invitation_profile_wizard_${invitationToken}`;

  // Load saved data from storage on initialization
  useEffect(() => {
    loadSavedData();
  }, [invitationToken]);

  // Auto-save data whenever profileData changes (debounced)
  useEffect(() => {
    if (hasUnsavedChanges) {
      const timeoutId = setTimeout(() => {
        saveDataToStorage();
      }, 1000);
      
      return () => clearTimeout(timeoutId);
    }
  }, [profileData, hasUnsavedChanges]);

  const loadSavedData = async () => {
    try {
      setLoading(true);
      const savedData = await AsyncStorage.getItem(storageKey);
      if (savedData) {
        const parsedData = JSON.parse(savedData);
        setProfileData({ ...getDefaultProfileData(), ...parsedData.profileData });
        setCurrentStep(parsedData.currentStep || 1);
      }
    } catch (error) {
      console.warn('Failed to load saved profile data:', error);
    } finally {
      setLoading(false);
    }
  };

  const saveDataToStorage = async () => {
    try {
      const dataToSave = {
        profileData,
        currentStep,
        lastSaved: new Date().toISOString(),
      };
      await AsyncStorage.setItem(storageKey, JSON.stringify(dataToSave));
      setHasUnsavedChanges(false);
    } catch (error) {
      console.warn('Failed to save profile data:', error);
    }
  };

  const clearSavedData = async () => {
    try {
      await AsyncStorage.removeItem(storageKey);
    } catch (error) {
      console.warn('Failed to clear saved profile data:', error);
    }
  };

  // Update profile data for a specific field
  const updateProfileData = useCallback((updates: Partial<TeacherProfileData>) => {
    setProfileData(prev => ({ ...prev, ...updates }));
    setHasUnsavedChanges(true);
    
    // Clear validation errors for updated fields
    const updatedFields = Object.keys(updates);
    setValidationErrors(prev => {
      const newErrors = { ...prev };
      Object.keys(newErrors).forEach(stepKey => {
        const stepNum = parseInt(stepKey);
        updatedFields.forEach(field => {
          if (newErrors[stepNum] && newErrors[stepNum][field]) {
            delete newErrors[stepNum][field];
          }
        });
      });
      return newErrors;
    });
  }, []);

  // Validate current step
  const validateStep = useCallback((stepNumber: number): boolean => {
    const errors: { [key: string]: string } = {};

    switch (stepNumber) {
      case 1: // Basic Information
        if (!profileData.introduction?.trim()) {
          errors.introduction = 'Uma breve introdução é obrigatória';
        }
        break;

      case 2: // Teaching Subjects
        if (profileData.teaching_subjects.length === 0) {
          errors.teaching_subjects = 'Selecione pelo menos uma matéria de ensino';
        }
        profileData.teaching_subjects.forEach((subject, index) => {
          if (!subject.subject.trim()) {
            errors[`teaching_subjects_${index}_subject`] = 'Nome da matéria é obrigatório';
          }
        });
        break;

      case 3: // Grade Levels
        if (profileData.grade_levels.length === 0) {
          errors.grade_levels = 'Selecione pelo menos um nível de ensino';
        }
        break;

      case 4: // Availability - optional for now
        if (!profileData.timezone) {
          errors.timezone = 'Selecione seu fuso horário';
        }
        break;

      case 5: // Rates & Compensation
        if (!profileData.hourly_rate || profileData.hourly_rate <= 0) {
          errors.hourly_rate = 'Valor da hora/aula deve ser maior que zero';
        }
        if (profileData.hourly_rate > 1000) {
          errors.hourly_rate = 'Valor da hora/aula muito alto (máximo €1000)';
        }
        break;

      case 6: // Credentials
        if (profileData.education_background.length === 0) {
          errors.education_background = 'Adicione pelo menos uma formação acadêmica';
        }
        profileData.education_background.forEach((edu, index) => {
          if (!edu.degree.trim()) {
            errors[`education_${index}_degree`] = 'Grau/Título é obrigatório';
          }
          if (!edu.field_of_study.trim()) {
            errors[`education_${index}_field`] = 'Área de estudo é obrigatória';
          }
          if (!edu.institution.trim()) {
            errors[`education_${index}_institution`] = 'Instituição é obrigatória';
          }
          if (!edu.graduation_year || edu.graduation_year < 1950 || edu.graduation_year > new Date().getFullYear()) {
            errors[`education_${index}_year`] = 'Ano de formação inválido';
          }
        });
        break;

      case 7: // Profile Marketing
        if (!profileData.teaching_philosophy?.trim()) {
          errors.teaching_philosophy = 'Filosofia de ensino é obrigatória';
        }
        if (!profileData.teaching_approach?.trim()) {
          errors.teaching_approach = 'Abordagem de ensino é obrigatória';
        }
        if (profileData.specializations.length === 0) {
          errors.specializations = 'Adicione pelo menos uma especialização';
        }
        break;

      case 8: // Preview & Submit - validate all previous steps
        for (let i = 1; i < 8; i++) {
          if (!validateStep(i)) {
            errors.overall = `Por favor, complete todos os campos obrigatórios na Etapa ${i}`;
            break;
          }
        }
        break;
    }

    // Update validation errors
    setValidationErrors(prev => ({
      ...prev,
      [stepNumber]: errors,
    }));

    return Object.keys(errors).length === 0;
  }, [profileData]);

  // Navigate to next step
  const nextStep = useCallback(() => {
    if (validateStep(currentStep)) {
      if (currentStep < totalSteps) {
        setCurrentStep(prev => prev + 1);
        saveDataToStorage();
      }
      return true;
    }
    return false;
  }, [currentStep, validateStep]);

  // Navigate to previous step
  const previousStep = useCallback(() => {
    if (currentStep > 1) {
      setCurrentStep(prev => prev - 1);
      saveDataToStorage();
    }
  }, [currentStep]);

  // Go to specific step
  const goToStep = useCallback((stepNumber: number) => {
    if (stepNumber >= 1 && stepNumber <= totalSteps) {
      setCurrentStep(stepNumber);
      saveDataToStorage();
    }
  }, []);

  // Get validation errors for current step
  const getCurrentStepErrors = useCallback(() => {
    return validationErrors[currentStep] || {};
  }, [validationErrors, currentStep]);

  // Check if step is completed (has no validation errors)
  const isStepCompleted = useCallback((stepNumber: number) => {
    return validateStep(stepNumber);
  }, [validateStep]);

  // Get progress percentage
  const getProgress = useCallback(() => {
    return (currentStep / totalSteps) * 100;
  }, [currentStep]);

  // Reset wizard to initial state
  const resetWizard = useCallback(() => {
    setCurrentStep(1);
    setProfileData(getDefaultProfileData());
    setValidationErrors({});
    setHasUnsavedChanges(false);
    clearSavedData();
  }, []);

  // Helper functions for specific data updates
  const addTeachingSubject = useCallback((subject: Omit<SubjectExpertise, 'subject'> & { subject: string }) => {
    const newSubjects = [...profileData.teaching_subjects, subject];
    updateProfileData({ teaching_subjects: newSubjects });
  }, [profileData.teaching_subjects, updateProfileData]);

  const removeTeachingSubject = useCallback((index: number) => {
    const newSubjects = profileData.teaching_subjects.filter((_, i) => i !== index);
    updateProfileData({ teaching_subjects: newSubjects });
  }, [profileData.teaching_subjects, updateProfileData]);

  const addEducationEntry = useCallback((education: EducationEntry) => {
    const newEducation = [...profileData.education_background, education];
    updateProfileData({ education_background: newEducation });
  }, [profileData.education_background, updateProfileData]);

  const removeEducationEntry = useCallback((index: number) => {
    const newEducation = profileData.education_background.filter((_, i) => i !== index);
    updateProfileData({ education_background: newEducation });
  }, [profileData.education_background, updateProfileData]);

  const addExperienceEntry = useCallback((experience: ExperienceEntry) => {
    const newExperience = [...profileData.teaching_experience, experience];
    updateProfileData({ teaching_experience: newExperience });
  }, [profileData.teaching_experience, updateProfileData]);

  const removeExperienceEntry = useCallback((index: number) => {
    const newExperience = profileData.teaching_experience.filter((_, i) => i !== index);
    updateProfileData({ teaching_experience: newExperience });
  }, [profileData.teaching_experience, updateProfileData]);

  const addCertification = useCallback((certification: CertificationFile) => {
    const newCertifications = [...profileData.certifications, certification];
    updateProfileData({ certifications: newCertifications });
  }, [profileData.certifications, updateProfileData]);

  const removeCertification = useCallback((index: number) => {
    const newCertifications = profileData.certifications.filter((_, i) => i !== index);
    updateProfileData({ certifications: newCertifications });
  }, [profileData.certifications, updateProfileData]);

  return {
    // State
    currentStep,
    totalSteps,
    profileData,
    validationErrors,
    loading,
    hasUnsavedChanges,

    // Navigation
    nextStep,
    previousStep,
    goToStep,

    // Data management
    updateProfileData,
    validateStep,
    resetWizard,
    saveDataToStorage,
    clearSavedData,

    // Helper functions
    addTeachingSubject,
    removeTeachingSubject,
    addEducationEntry,
    removeEducationEntry,
    addExperienceEntry,
    removeExperienceEntry,
    addCertification,
    removeCertification,

    // Computed values
    getCurrentStepErrors,
    isStepCompleted,
    getProgress,
    canGoNext: currentStep < totalSteps,
    canGoPrevious: currentStep > 1,
    isLastStep: currentStep === totalSteps,
  };
};