import { renderHook, act, waitFor } from '@testing-library/react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';

import { useProfileWizard } from '@/hooks/useProfileWizard';
import apiClient from '@/api/apiClient';
import {
  createMockProfileData,
  createMockCompletionData,
  mockApiResponse,
  flushPromises,
  advanceTimersByTime,
} from '../utils/test-utils';

// Mock dependencies
jest.mock('@/api/apiClient');
jest.mock('@react-native-async-storage/async-storage');

const mockApiClient = apiClient as jest.Mocked<typeof apiClient>;
const mockAsyncStorage = AsyncStorage as jest.Mocked<typeof AsyncStorage>;

describe('useProfileWizard', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.clearAllTimers();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  describe('Initialization', () => {
    it('should initialize with default state', () => {
      const { result } = renderHook(() => useProfileWizard());

      expect(result.current.currentStep).toBe(0);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.isSaving).toBe(false);
      expect(result.current.error).toBeNull();
      expect(result.current.validationErrors).toEqual({});
      expect(result.current.hasUnsavedChanges).toBe(false);
      expect(result.current.formData).toBeDefined();
      expect(result.current.completionData).toBeNull();
    });

    it('should load cached state from AsyncStorage', async () => {
      const cachedState = {
        currentStep: 2,
        formData: createMockProfileData({ first_name: 'Cached' }),
        completionData: createMockCompletionData(),
      };

      mockAsyncStorage.getItem.mockResolvedValue(JSON.stringify(cachedState));
      mockApiClient.get.mockResolvedValue(mockApiResponse({}));

      const { result } = renderHook(() => useProfileWizard());

      await act(async () => {
        await result.current.loadProgress();
      });

      expect(result.current.currentStep).toBe(2);
      expect(result.current.formData.first_name).toBe('Cached');
      expect(result.current.completionData).toEqual(cachedState.completionData);
    });

    it('should handle AsyncStorage errors gracefully', async () => {
      mockAsyncStorage.getItem.mockRejectedValue(new Error('Storage error'));
      mockApiClient.get.mockResolvedValue(mockApiResponse({}));

      const { result } = renderHook(() => useProfileWizard());

      await act(async () => {
        await result.current.loadProgress();
      });

      // Should not crash and should have loaded API data
      expect(result.current.error).toBeNull();
      expect(result.current.isLoading).toBe(false);
    });
  });

  describe('Data Loading', () => {
    it('should load profile data from API successfully', async () => {
      const mockProfileData = createMockProfileData();
      const mockCompletionData = createMockCompletionData();

      mockApiClient.get
        .mockResolvedValueOnce(mockApiResponse({ user: { name: 'John Doe', email: 'john@example.com' } }))
        .mockResolvedValueOnce(mockApiResponse(mockCompletionData));

      const { result } = renderHook(() => useProfileWizard());

      await act(async () => {
        await result.current.loadProgress();
      });

      expect(result.current.isLoading).toBe(false);
      expect(result.current.formData.first_name).toBe('John');
      expect(result.current.formData.last_name).toBe('Doe');
      expect(result.current.formData.email).toBe('john@example.com');
      expect(result.current.completionData).toEqual(mockCompletionData);
      expect(result.current.error).toBeNull();
    });

    it('should handle API errors when loading data', async () => {
      mockApiClient.get.mockRejectedValue(new Error('API Error'));

      const { result } = renderHook(() => useProfileWizard());

      await act(async () => {
        await result.current.loadProgress();
      });

      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBe('API Error');
    });

    it('should cancel ongoing requests when component unmounts', async () => {
      const cancelSpy = jest.fn();
      const mockCancelToken = { cancel: cancelSpy };
      
      // Mock axios cancel token
      (axios.CancelToken.source as jest.Mock) = jest.fn(() => ({
        token: 'mock-token',
        cancel: cancelSpy,
      }));

      mockApiClient.get.mockImplementation(() => new Promise(() => {})); // Never resolves

      const { result, unmount } = renderHook(() => useProfileWizard());

      act(() => {
        result.current.loadProgress();
      });

      unmount();

      expect(cancelSpy).toHaveBeenCalledWith('Component unmounted');
    });
  });

  describe('Form Data Updates', () => {
    it('should update form data correctly', async () => {
      const { result } = renderHook(() => useProfileWizard());

      const updates = { first_name: 'Jane', last_name: 'Smith' };

      await act(async () => {
        result.current.updateFormData(updates);
      });

      expect(result.current.formData.first_name).toBe('Jane');
      expect(result.current.formData.last_name).toBe('Smith');
      expect(result.current.hasUnsavedChanges).toBe(true);
      expect(result.current.validationErrors).toEqual({});
    });

    it('should update individual form fields', async () => {
      const { result } = renderHook(() => useProfileWizard());

      await act(async () => {
        result.current.updateFormField({
          field: 'professional_title',
          value: 'Senior Mathematics Teacher',
        });
      });

      expect(result.current.formData.professional_title).toBe('Senior Mathematics Teacher');
      expect(result.current.hasUnsavedChanges).toBe(true);
    });

    it('should cache updated state to AsyncStorage', async () => {
      const { result } = renderHook(() => useProfileWizard());

      await act(async () => {
        result.current.updateFormData({ first_name: 'John' });
      });

      await flushPromises();

      expect(mockAsyncStorage.setItem).toHaveBeenCalledWith(
        '@teacher_profile_wizard',
        expect.stringContaining('"first_name":"John"')
      );
    });

    it('should clear field-specific validation errors on update', async () => {
      const { result } = renderHook(() => useProfileWizard());

      // Set initial validation errors
      await act(async () => {
        result.current.validateStep(0);
      });

      mockApiClient.post.mockResolvedValue(mockApiResponse({
        is_valid: false,
        errors: { first_name: ['Required'] },
      }));

      await act(async () => {
        await result.current.validateStep(0);
      });

      expect(result.current.validationErrors.first_name).toEqual(['Required']);

      // Update the field
      await act(async () => {
        result.current.updateFormField({
          field: 'first_name',
          value: 'John',
        });
      });

      expect(result.current.validationErrors.first_name).toEqual([]);
    });
  });

  describe('Step Navigation', () => {
    it('should set current step with bounds checking', async () => {
      const { result } = renderHook(() => useProfileWizard());

      await act(async () => {
        result.current.setCurrentStep(3);
      });

      expect(result.current.currentStep).toBe(3);

      // Test upper bound
      await act(async () => {
        result.current.setCurrentStep(10);
      });

      expect(result.current.currentStep).toBe(6); // Clamped to max

      // Test lower bound
      await act(async () => {
        result.current.setCurrentStep(-1);
      });

      expect(result.current.currentStep).toBe(0); // Clamped to min
    });

    it('should cache step changes to AsyncStorage', async () => {
      const { result } = renderHook(() => useProfileWizard());

      await act(async () => {
        result.current.setCurrentStep(2);
      });

      await flushPromises();

      expect(mockAsyncStorage.setItem).toHaveBeenCalledWith(
        '@teacher_profile_wizard',
        expect.stringContaining('"currentStep":2')
      );
    });
  });

  describe('Validation', () => {
    it('should validate step successfully', async () => {
      mockApiClient.post.mockResolvedValue(mockApiResponse({
        is_valid: true,
      }));

      const { result } = renderHook(() => useProfileWizard());

      let isValid;
      await act(async () => {
        isValid = await result.current.validateStep(0);
      });

      expect(isValid).toBe(true);
      expect(result.current.validationErrors).toEqual({});
      expect(mockApiClient.post).toHaveBeenCalledWith(
        '/accounts/teachers/profile-wizard/validate-step/',
        {
          step: 0,
          data: result.current.formData,
        }
      );
    });

    it('should handle validation errors', async () => {
      const validationErrors = {
        first_name: ['First name is required'],
        email: ['Invalid email format'],
      };

      mockApiClient.post.mockResolvedValue(mockApiResponse({
        is_valid: false,
        errors: validationErrors,
      }));

      const { result } = renderHook(() => useProfileWizard());

      let isValid;
      await act(async () => {
        isValid = await result.current.validateStep(0);
      });

      expect(isValid).toBe(false);
      expect(result.current.validationErrors).toEqual(validationErrors);
    });

    it('should handle validation API errors', async () => {
      mockApiClient.post.mockRejectedValue(new Error('Validation API Error'));

      const { result } = renderHook(() => useProfileWizard());

      let isValid;
      await act(async () => {
        isValid = await result.current.validateStep(0);
      });

      expect(isValid).toBe(false);
      expect(result.current.error).toBe('Validation failed. Please check your input and try again.');
    });
  });

  describe('Progress Saving', () => {
    it('should save progress successfully', async () => {
      const mockSaveResponse = {
        success: true,
        completion_data: createMockCompletionData(),
      };

      mockApiClient.post.mockResolvedValue(mockApiResponse(mockSaveResponse));

      const { result } = renderHook(() => useProfileWizard());

      await act(async () => {
        await result.current.saveProgress();
      });

      expect(result.current.isSaving).toBe(false);
      expect(result.current.hasUnsavedChanges).toBe(false);
      expect(result.current.completionData).toEqual(mockSaveResponse.completion_data);
      expect(result.current.error).toBeNull();
    });

    it('should handle save progress errors', async () => {
      mockApiClient.post.mockRejectedValue(new Error('Save failed'));

      const { result } = renderHook(() => useProfileWizard());

      await act(async () => {
        try {
          await result.current.saveProgress();
        } catch (error) {
          // Expected to throw
        }
      });

      expect(result.current.isSaving).toBe(false);
      expect(result.current.error).toBe('Save failed');
    });

    it('should set saving state during save operation', async () => {
      let resolveSave: (value: any) => void;
      const savePromise = new Promise(resolve => {
        resolveSave = resolve;
      });

      mockApiClient.post.mockReturnValue(savePromise);

      const { result } = renderHook(() => useProfileWizard());

      act(() => {
        result.current.saveProgress();
      });

      expect(result.current.isSaving).toBe(true);

      await act(async () => {
        resolveSave(mockApiResponse({}));
        await savePromise;
      });

      expect(result.current.isSaving).toBe(false);
    });
  });

  describe('Profile Submission', () => {
    it('should submit profile successfully', async () => {
      mockApiClient.post.mockResolvedValue(mockApiResponse({}));

      const { result } = renderHook(() => useProfileWizard());

      await act(async () => {
        await result.current.submitProfile();
      });

      expect(result.current.isSaving).toBe(false);
      expect(result.current.hasUnsavedChanges).toBe(false);
      expect(result.current.error).toBeNull();
      expect(mockAsyncStorage.removeItem).toHaveBeenCalledWith('@teacher_profile_wizard');
    });

    it('should handle profile submission errors', async () => {
      mockApiClient.post.mockRejectedValue(new Error('Submission failed'));

      const { result } = renderHook(() => useProfileWizard());

      await act(async () => {
        try {
          await result.current.submitProfile();
        } catch (error) {
          // Expected to throw
        }
      });

      expect(result.current.isSaving).toBe(false);
      expect(result.current.error).toBe('Submission failed');
    });
  });

  describe('Photo Upload', () => {
    it('should upload profile photo successfully', async () => {
      const mockPhotoUrl = 'https://example.com/photo.jpg';
      mockApiClient.post.mockResolvedValue(mockApiResponse({
        photo_url: mockPhotoUrl,
      }));

      const { result } = renderHook(() => useProfileWizard());

      let photoUrl;
      await act(async () => {
        photoUrl = await result.current.uploadProfilePhoto('file://local-photo.jpg');
      });

      expect(photoUrl).toBe(mockPhotoUrl);
      expect(result.current.formData.profile_photo).toBe(mockPhotoUrl);
      expect(mockApiClient.post).toHaveBeenCalledWith(
        '/accounts/teachers/profile/photo/',
        expect.any(FormData),
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );
    });

    it('should handle photo upload errors', async () => {
      mockApiClient.post.mockRejectedValue(new Error('Upload failed'));

      const { result } = renderHook(() => useProfileWizard());

      await act(async () => {
        await expect(result.current.uploadProfilePhoto('file://photo.jpg'))
          .rejects.toThrow('Upload failed');
      });
    });
  });

  describe('Rate Suggestions', () => {
    it('should fetch rate suggestions successfully', async () => {
      const mockSuggestions = {
        min_rate: 20,
        max_rate: 40,
        average_rate: 30,
      };

      mockApiClient.get.mockResolvedValue(mockApiResponse(mockSuggestions));

      const { result } = renderHook(() => useProfileWizard());

      let suggestions;
      await act(async () => {
        suggestions = await result.current.getRateSuggestions('Mathematics', 'Lisbon');
      });

      expect(suggestions).toEqual(mockSuggestions);
      expect(mockApiClient.get).toHaveBeenCalledWith(
        '/accounts/teachers/rate-suggestions/',
        {
          params: { subject: 'Mathematics', location: 'Lisbon' },
        }
      );
    });

    it('should handle rate suggestions errors gracefully', async () => {
      mockApiClient.get.mockRejectedValue(new Error('API Error'));

      const { result } = renderHook(() => useProfileWizard());

      let suggestions;
      await act(async () => {
        suggestions = await result.current.getRateSuggestions('Mathematics', 'Lisbon');
      });

      expect(suggestions).toBeNull();
    });
  });

  describe('Wizard Reset', () => {
    it('should reset wizard state completely', async () => {
      const { result } = renderHook(() => useProfileWizard());

      // Set some state first
      await act(async () => {
        result.current.setCurrentStep(3);
        result.current.updateFormData({ first_name: 'Test' });
      });

      expect(result.current.currentStep).toBe(3);
      expect(result.current.formData.first_name).toBe('Test');

      // Reset wizard
      await act(async () => {
        await result.current.resetWizard();
      });

      expect(result.current.currentStep).toBe(0);
      expect(result.current.formData.first_name).toBe('');
      expect(result.current.hasUnsavedChanges).toBe(false);
      expect(mockAsyncStorage.removeItem).toHaveBeenCalledWith('@teacher_profile_wizard');
    });
  });

  describe('Memory Management', () => {
    it('should cleanup resources on unmount', () => {
      const { unmount } = renderHook(() => useProfileWizard());

      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

      unmount();

      // Should not cause memory leaks or errors
      expect(consoleSpy).not.toHaveBeenCalled();
      consoleSpy.mockRestore();
    });

    it('should not update state after component unmounts', async () => {
      mockApiClient.get.mockImplementation(() => 
        new Promise(resolve => 
          setTimeout(() => resolve(mockApiResponse({})), 100)
        )
      );

      const { result, unmount } = renderHook(() => useProfileWizard());

      act(() => {
        result.current.loadProgress();
      });

      unmount();

      // Advance timers to trigger the delayed response
      advanceTimersByTime(150);

      // Should not crash or update state
      expect(result.current.isLoading).toBe(false);
    });
  });

  describe('Edge Cases', () => {
    it('should handle malformed cached data', async () => {
      mockAsyncStorage.getItem.mockResolvedValue('invalid-json');
      mockApiClient.get.mockResolvedValue(mockApiResponse({}));

      const { result } = renderHook(() => useProfileWizard());

      await act(async () => {
        await result.current.loadProgress();
      });

      // Should not crash and should continue with API loading
      expect(result.current.error).toBeNull();
      expect(result.current.isLoading).toBe(false);
    });

    it('should handle concurrent API requests gracefully', async () => {
      let resolveFirst: (value: any) => void;
      let resolveSecond: (value: any) => void;

      const firstPromise = new Promise(resolve => {
        resolveFirst = resolve;
      });
      const secondPromise = new Promise(resolve => {
        resolveSecond = resolve;
      });

      mockApiClient.get
        .mockReturnValueOnce(firstPromise)
        .mockReturnValueOnce(firstPromise)
        .mockReturnValueOnce(secondPromise)
        .mockReturnValueOnce(secondPromise);

      const { result } = renderHook(() => useProfileWizard());

      // Start first request
      act(() => {
        result.current.loadProgress();
      });

      // Start second request before first completes
      act(() => {
        result.current.loadProgress();
      });

      // Resolve second request first
      await act(async () => {
        resolveSecond(mockApiResponse({ user: { name: 'Second' } }));
        await secondPromise;
      });

      // Then resolve first request
      await act(async () => {
        resolveFirst(mockApiResponse({ user: { name: 'First' } }));
        await firstPromise;
      });

      // Should use the second (latest) request result
      expect(result.current.formData.first_name).toBe('Second');
    });

    it('should handle network cancellation errors', async () => {
      const cancelError = new Error('Request cancelled');
      (cancelError as any).isCancel = true;
      
      mockApiClient.get.mockRejectedValue(cancelError);
      
      // Mock axios.isCancel
      (axios.isCancel as jest.Mock) = jest.fn(() => true);

      const { result } = renderHook(() => useProfileWizard());

      await act(async () => {
        await result.current.loadProgress();
      });

      // Should not set error state for cancelled requests
      expect(result.current.error).toBeNull();
      expect(result.current.isLoading).toBe(false);
    });
  });
});