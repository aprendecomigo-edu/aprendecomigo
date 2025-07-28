import apiClient from './apiClient';

export interface OnboardingStep {
  id: string;
  name: string;
  completed: boolean;
  completed_at?: string;
}

export interface OnboardingProgress {
  id: number;
  user: number;
  completed_steps: string[];
  skipped_steps: string[];
  total_steps: number;
  completion_percentage: number;
  created_at: string;
  updated_at: string;
  steps: OnboardingStep[];
}

export interface NavigationPreferences {
  id: number;
  user: number;
  show_onboarding: boolean;
  show_tutorial: boolean;
  preferred_dashboard: 'full' | 'minimal';
  sidebar_collapsed: boolean;
  theme: 'light' | 'dark' | 'auto';
  created_at: string;
  updated_at: string;
}

export interface UpdateOnboardingProgressData {
  completed_steps?: string[];
  skipped_steps?: string[];
}

export interface UpdateNavigationPreferencesData {
  show_onboarding?: boolean;
  show_tutorial?: boolean;
  preferred_dashboard?: 'full' | 'minimal';
  sidebar_collapsed?: boolean;
  theme?: 'light' | 'dark' | 'auto';
}

class OnboardingApi {
  async getOnboardingProgress(): Promise<OnboardingProgress> {
    const response = await apiClient.get('/accounts/onboarding_progress/');
    return response.data;
  }

  async updateOnboardingProgress(data: UpdateOnboardingProgressData): Promise<OnboardingProgress> {
    const response = await apiClient.post('/accounts/onboarding_progress/', data);
    return response.data;
  }

  async completeOnboardingStep(stepId: string): Promise<OnboardingProgress> {
    const response = await apiClient.post('/accounts/onboarding_progress/', {
      completed_steps: [stepId]
    });
    return response.data;
  }

  async skipOnboardingStep(stepId: string): Promise<OnboardingProgress> {
    const response = await apiClient.post('/accounts/onboarding_progress/', {
      skipped_steps: [stepId]
    });
    return response.data;
  }

  async getNavigationPreferences(): Promise<NavigationPreferences> {
    const response = await apiClient.get('/accounts/navigation_preferences/');
    return response.data;
  }

  async updateNavigationPreferences(data: UpdateNavigationPreferencesData): Promise<NavigationPreferences> {
    const response = await apiClient.post('/accounts/navigation_preferences/', data);
    return response.data;
  }

  async skipOnboarding(): Promise<NavigationPreferences> {
    const response = await apiClient.post('/accounts/navigation_preferences/', {
      show_onboarding: false
    });
    return response.data;
  }

  async enableOnboarding(): Promise<NavigationPreferences> {
    const response = await apiClient.post('/accounts/navigation_preferences/', {
      show_onboarding: true
    });
    return response.data;
  }
}

export const onboardingApi = new OnboardingApi();