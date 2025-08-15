import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react';

import { markFirstLoginCompleted } from '../../api/authApi';

import { TutorialConfig, TutorialState, TutorialContextType } from './types';

const initialState: TutorialState = {
  isActive: false,
  currentStep: 0,
  config: null,
  completedTutorials: [],
  skippedTutorials: [],
};

type TutorialAction =
  | { type: 'START_TUTORIAL'; config: TutorialConfig }
  | { type: 'NEXT_STEP' }
  | { type: 'PREV_STEP' }
  | { type: 'SKIP_TUTORIAL' }
  | { type: 'COMPLETE_TUTORIAL' }
  | { type: 'RESET_TUTORIAL' }
  | { type: 'SET_COMPLETED_TUTORIALS'; tutorials: string[] }
  | { type: 'SET_SKIPPED_TUTORIALS'; tutorials: string[] };

const tutorialReducer = (state: TutorialState, action: TutorialAction): TutorialState => {
  switch (action.type) {
    case 'START_TUTORIAL':
      return {
        ...state,
        isActive: true,
        currentStep: 0,
        config: action.config,
      };
    case 'NEXT_STEP':
      const nextStep = state.currentStep + 1;
      if (state.config && nextStep >= state.config.steps.length) {
        return {
          ...state,
          isActive: false,
          currentStep: 0,
          config: null,
          completedTutorials: state.config
            ? [...state.completedTutorials, state.config.id]
            : state.completedTutorials,
        };
      }
      return {
        ...state,
        currentStep: nextStep,
      };
    case 'PREV_STEP':
      return {
        ...state,
        currentStep: Math.max(0, state.currentStep - 1),
      };
    case 'SKIP_TUTORIAL':
      return {
        ...state,
        isActive: false,
        currentStep: 0,
        config: null,
        skippedTutorials: state.config
          ? [...state.skippedTutorials, state.config.id]
          : state.skippedTutorials,
      };
    case 'COMPLETE_TUTORIAL':
      return {
        ...state,
        isActive: false,
        currentStep: 0,
        config: null,
        completedTutorials: state.config
          ? [...state.completedTutorials, state.config.id]
          : state.completedTutorials,
      };
    case 'RESET_TUTORIAL':
      return {
        ...state,
        isActive: false,
        currentStep: 0,
        config: null,
      };
    case 'SET_COMPLETED_TUTORIALS':
      return {
        ...state,
        completedTutorials: action.tutorials,
      };
    case 'SET_SKIPPED_TUTORIALS':
      return {
        ...state,
        skippedTutorials: action.tutorials,
      };
    default:
      return state;
  }
};

const TutorialContext = createContext<TutorialContextType | null>(null);

export const useTutorial = () => {
  const context = useContext(TutorialContext);
  if (!context) {
    throw new Error('useTutorial must be used within a TutorialProvider');
  }
  return context;
};

interface TutorialProviderProps {
  children: ReactNode;
}

export const TutorialProvider: React.FC<TutorialProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(tutorialReducer, initialState);

  const startTutorial = (config: TutorialConfig) => {
    dispatch({ type: 'START_TUTORIAL', config });
  };

  const nextStep = () => {
    dispatch({ type: 'NEXT_STEP' });
  };

  const prevStep = () => {
    dispatch({ type: 'PREV_STEP' });
  };

  const skipTutorial = async () => {
    dispatch({ type: 'SKIP_TUTORIAL' });
    // Mark first login as completed when tutorial is skipped
    try {
      await markFirstLoginCompleted();
    } catch (error) {
      if (__DEV__) {
        console.error('Failed to mark first login as completed:', error); // TODO: Review for sensitive data
      }
    }
  };

  const completeTutorial = async () => {
    dispatch({ type: 'COMPLETE_TUTORIAL' });
    // Mark first login as completed when tutorial is completed
    try {
      await markFirstLoginCompleted();
    } catch (error) {
      if (__DEV__) {
        console.error('Failed to mark first login as completed:', error); // TODO: Review for sensitive data
      }
    }
  };

  const resetTutorial = () => {
    dispatch({ type: 'RESET_TUTORIAL' });
  };

  const isTutorialCompleted = (tutorialId: string) => {
    return state.completedTutorials.includes(tutorialId);
  };

  const isTutorialSkipped = (tutorialId: string) => {
    return state.skippedTutorials.includes(tutorialId);
  };

  const contextValue: TutorialContextType = {
    state,
    startTutorial,
    nextStep,
    prevStep,
    skipTutorial,
    completeTutorial,
    resetTutorial,
    isTutorialCompleted,
    isTutorialSkipped,
  };

  return <TutorialContext.Provider value={contextValue}>{children}</TutorialContext.Provider>;
};
