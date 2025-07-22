export interface TutorialStep {
  id: string;
  title: string;
  content: string;
  targetElement?: string;
  position?: 'top' | 'bottom' | 'left' | 'right' | 'center';
  action?: {
    label: string;
    onPress: () => void;
  };
  highlight?: boolean;
  skippable?: boolean;
}

export interface TutorialConfig {
  id: string;
  title: string;
  description: string;
  steps: TutorialStep[];
  canSkip?: boolean;
  autoStart?: boolean;
  showProgress?: boolean;
}

export interface TutorialState {
  isActive: boolean;
  currentStep: number;
  config: TutorialConfig | null;
  completedTutorials: string[];
  skippedTutorials: string[];
}

export interface TutorialContextType {
  state: TutorialState;
  startTutorial: (config: TutorialConfig) => void;
  nextStep: () => void;
  prevStep: () => void;
  skipTutorial: () => void;
  completeTutorial: () => void;
  resetTutorial: () => void;
  isTutorialCompleted: (tutorialId: string) => boolean;
  isTutorialSkipped: (tutorialId: string) => boolean;
}
