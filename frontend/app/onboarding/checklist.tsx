import useRouter from '@unitools/router';
import React, { useState } from 'react';
import { Platform } from 'react-native';

import {
  AddFirstTeacherFlow,
  AddFirstStudentFlow,
  SchoolProfileFlow,
} from '@/components/onboarding/GuidedFlows';
import { OnboardingChecklist } from '@/components/onboarding/OnboardingChecklist';
import { OnboardingTutorial } from '@/components/onboarding/OnboardingTutorial';
import { Box } from '@/components/ui/box';
import { VStack } from '@/components/ui/vstack';

export default function OnboardingChecklistPage() {
  const router = useRouter();
  const [activeFlow, setActiveFlow] = useState<string | null>(null);

  const handleStepAction = (stepId: string, action: 'start' | 'skip') => {
    if (action === 'start') {
      switch (stepId) {
        case 'invite_first_teacher':
          setActiveFlow('teacher');
          break;
        case 'add_first_student':
          setActiveFlow('student');
          break;
        case 'complete_school_profile':
          setActiveFlow('profile');
          break;
        default:
          // Handle other steps with direct navigation
          break;
      }
    }
  };

  const handleFlowComplete = () => {
    setActiveFlow(null);
  };

  const handleFlowClose = () => {
    setActiveFlow(null);
  };

  return (
    <Box className="flex-1 bg-gray-50">
      <VStack className="flex-1 p-4 max-w-4xl mx-auto">
        <OnboardingChecklist onStepAction={handleStepAction} showProgress={true} />
      </VStack>

      {/* Guided Flow Modals */}
      <AddFirstTeacherFlow
        isOpen={activeFlow === 'teacher'}
        onClose={handleFlowClose}
        onComplete={handleFlowComplete}
      />

      <AddFirstStudentFlow
        isOpen={activeFlow === 'student'}
        onClose={handleFlowClose}
        onComplete={handleFlowComplete}
      />

      <SchoolProfileFlow
        isOpen={activeFlow === 'profile'}
        onClose={handleFlowClose}
        onComplete={handleFlowComplete}
      />

      {/* Tutorial Controller */}
      <OnboardingTutorial
        autoStart={false}
        onComplete={() => {
          if (__DEV__) {
            console.log('Tutorial completed');
          }
        }}
        onSkip={() => {
          if (__DEV__) {
            console.log('Tutorial skipped');
          }
        }}
      />
    </Box>
  );
}
