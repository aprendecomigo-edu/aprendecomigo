import { render, RenderOptions } from '@testing-library/react-native';
import React, { ReactElement } from 'react';

import { GluestackUIProvider } from '@/components/ui/gluestack-ui-provider';
import { config } from '@/components/ui/gluestack-ui-provider/config';

// Mock data factories for testing
export const createMockProfileData = (overrides = {}) => ({
  first_name: 'John',
  last_name: 'Doe',
  professional_title: 'Mathematics Teacher',
  email: 'john.doe@example.com',
  phone_number: '+351987654321',
  location: {
    city: 'Lisbon',
    country: 'Portugal',
    timezone: 'Europe/Lisbon',
  },
  languages: ['Portuguese', 'English'],
  years_experience: 5,
  teaching_level: 'Secondary',
  introduction: 'Experienced math teacher',
  professional_bio: 'I have been teaching mathematics for over 5 years...',
  teaching_philosophy: 'I believe in making math accessible to all students',
  specializations: ['Algebra', 'Geometry'],
  achievements: ['Best Teacher Award 2023'],
  teaching_approach: 'Interactive and engaging',
  student_outcomes: 'High success rates',
  degrees: [
    {
      id: '1',
      degree_type: 'Bachelor',
      field_of_study: 'Mathematics',
      institution: 'University of Lisbon',
      location: 'Lisbon, Portugal',
      graduation_year: 2018,
      gpa: '3.8',
      honors: 'Magna Cum Laude',
      description: 'Focus on pure mathematics',
    },
  ],
  certifications: [
    {
      id: '1',
      name: 'Teaching Certification',
      issuing_organization: 'Ministry of Education',
      issue_date: '2019-06-01',
      expiration_date: '2029-06-01',
      credential_id: 'TC123456',
      verification_url: 'https://example.com/verify',
    },
  ],
  additional_training: ['Online Teaching Methods', 'Child Psychology'],
  teaching_subjects: [
    {
      id: '1',
      subject: 'Mathematics',
      grade_levels: ['Grade 7', 'Grade 8', 'Grade 9'],
      expertise_level: 'expert' as const,
      years_teaching: 5,
      description: 'Comprehensive math education',
    },
  ],
  subject_categories: ['STEM'],
  rate_structure: {
    individual_rate: 25,
    group_rate: 20,
    trial_lesson_rate: 15,
    currency: 'EUR',
    package_deals: [
      {
        id: '1',
        name: '10-Lesson Package',
        sessions: 10,
        price: 200,
        discount_percentage: 20,
      },
    ],
  },
  payment_methods: ['Credit Card', 'PayPal'],
  cancellation_policy: '24 hours notice required',
  weekly_availability: {
    monday: [
      {
        start_time: '09:00',
        end_time: '17:00',
        timezone: 'Europe/Lisbon',
      },
    ],
    tuesday: [
      {
        start_time: '09:00',
        end_time: '17:00',
        timezone: 'Europe/Lisbon',
      },
    ],
  },
  booking_preferences: {
    min_notice_hours: 24,
    max_advance_days: 30,
    session_duration_options: [60, 90],
    auto_accept_bookings: false,
  },
  time_zone: 'Europe/Lisbon',
  ...overrides,
});

export const createMockCompletionData = (overrides = {}) => ({
  completion_percentage: 75,
  missing_critical: ['rate_structure'],
  missing_optional: ['additional_training'],
  is_complete: false,
  step_completion: {
    'basic-info': {
      is_complete: true,
      completion_percentage: 100,
      missing_fields: [],
    },
    biography: {
      is_complete: true,
      completion_percentage: 100,
      missing_fields: [],
    },
    education: {
      is_complete: false,
      completion_percentage: 50,
      missing_fields: ['certifications'],
    },
    subjects: {
      is_complete: true,
      completion_percentage: 100,
      missing_fields: [],
    },
    rates: {
      is_complete: false,
      completion_percentage: 60,
      missing_fields: ['payment_methods'],
    },
    availability: {
      is_complete: true,
      completion_percentage: 100,
      missing_fields: [],
    },
  },
  recommendations: [
    {
      text: 'Add at least one certification to improve credibility',
      priority: 'high' as const,
    },
  ],
  ...overrides,
});

export const createMockValidationErrors = (overrides = {}) => ({
  first_name: ['First name is required'],
  email: ['Please enter a valid email address'],
  ...overrides,
});

// Custom render function with providers
const AllTheProviders = ({ children }: { children: React.ReactNode }) => {
  return <GluestackUIProvider config={config}>{children}</GluestackUIProvider>;
};

const customRender = (ui: ReactElement, options?: Omit<RenderOptions, 'wrapper'>) =>
  render(ui, { wrapper: AllTheProviders, ...options });

// Re-export everything
export * from '@testing-library/react-native';
export { customRender as render };

// Test helper functions
export const waitForAsyncUpdates = () => new Promise(resolve => setTimeout(resolve, 0));

export const flushPromises = () => new Promise(resolve => setImmediate(resolve));

export const mockApiResponse = (data: any, isError = false) => {
  if (isError) {
    return Promise.reject(new Error(data.message || 'API Error'));
  }
  return Promise.resolve({ data: { data } });
};

export const mockApiClient = {
  get: jest.fn(),
  post: jest.fn(),
  put: jest.fn(),
  delete: jest.fn(),
};

// Mock hook return values
export const createMockUseProfileWizard = (overrides = {}) => ({
  currentStep: 0,
  formData: createMockProfileData(),
  completionData: createMockCompletionData(),
  isLoading: false,
  isSaving: false,
  error: null,
  validationErrors: {},
  hasUnsavedChanges: false,
  setCurrentStep: jest.fn(),
  updateFormData: jest.fn(),
  updateFormField: jest.fn(),
  validateStep: jest.fn(() => Promise.resolve(true)),
  saveProgress: jest.fn(() => Promise.resolve()),
  submitProfile: jest.fn(() => Promise.resolve()),
  loadProgress: jest.fn(() => Promise.resolve()),
  getRateSuggestions: jest.fn(() => Promise.resolve(null)),
  uploadProfilePhoto: jest.fn(() => Promise.resolve('photo-url')),
  resetWizard: jest.fn(() => Promise.resolve()),
  ...overrides,
});

// Form interaction helpers
export const fillFormField = async (getByTestId: any, testId: string, value: string) => {
  const field = getByTestId(testId);
  fireEvent.changeText(field, value);
  await waitForAsyncUpdates();
};

export const pressButton = async (getByTestId: any, testId: string) => {
  const button = getByTestId(testId);
  fireEvent.press(button);
  await waitForAsyncUpdates();
};

// Wizard navigation helpers
export const navigateToStep = async (getByTestId: any, stepIndex: number) => {
  for (let i = 0; i < stepIndex; i++) {
    await pressButton(getByTestId, 'next-button');
  }
};

// Validation test helpers
export const expectValidationError = (getByText: any, errorMessage: string) => {
  expect(getByText(errorMessage)).toBeTruthy();
};

export const expectNoValidationErrors = (queryByTestId: any) => {
  expect(queryByTestId('validation-error')).toBeNull();
};

// Step completion test helpers
export const expectStepComplete = (getByTestId: any, stepId: string) => {
  expect(getByTestId(`step-${stepId}-complete`)).toBeTruthy();
};

export const expectStepIncomplete = (getByTestId: any, stepId: string) => {
  expect(getByTestId(`step-${stepId}-incomplete`)).toBeTruthy();
};

// Mock timers for auto-save testing
export const advanceTimersByTime = (ms: number) => {
  jest.advanceTimersByTime(ms);
};

export const runAllTimers = () => {
  jest.runAllTimers();
};

// Async storage test helpers
export const mockAsyncStorage = {
  setItem: jest.fn(() => Promise.resolve()),
  getItem: jest.fn(() => Promise.resolve(null)),
  removeItem: jest.fn(() => Promise.resolve()),
  clear: jest.fn(() => Promise.resolve()),
};

// Network request mocking
export const mockNetworkError = () => {
  const error = new Error('Network Error');
  (error as any).isAxiosError = true;
  return error;
};

export const mockValidationError = (errors: Record<string, string[]>) => {
  const error = new Error('Validation Error');
  (error as any).response = {
    status: 400,
    data: { errors },
  };
  return error;
};

// Component prop helpers
export const createMockProps = (overrides = {}) => ({
  onComplete: jest.fn(),
  onExit: jest.fn(),
  resumeFromStep: 0,
  ...overrides,
});

// Error boundary testing
export const throwError = (message = 'Test error') => {
  throw new Error(message);
};

export const expectErrorBoundary = (getByText: any, errorMessage: string) => {
  expect(getByText(errorMessage)).toBeTruthy();
};
