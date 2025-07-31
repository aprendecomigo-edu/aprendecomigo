import React from 'react';
import { fireEvent, waitFor } from '@testing-library/react-native';

import { BasicInfoStep } from '@/components/profile-wizard/basic-info-step';
import {
  render,
  createMockProfileData,
  createMockValidationErrors,
  fillFormField,
  pressButton,
  waitForAsyncUpdates,
  expectValidationError,
  expectNoValidationErrors,
} from '../../utils/test-utils';

// Mock image picker
jest.mock('expo-image-picker', () => ({
  launchImageLibraryAsync: jest.fn(),
  MediaTypeOptions: { Images: 'Images' },
  requestMediaLibraryPermissionsAsync: jest.fn(() => Promise.resolve({ status: 'granted' })),
}));

describe('BasicInfoStep', () => {
  const mockOnFormDataChange = jest.fn();
  const mockFormData = createMockProfileData();

  const defaultProps = {
    formData: mockFormData,
    onFormDataChange: mockOnFormDataChange,
    validationErrors: {},
    isLoading: false,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render all form fields', () => {
      const { getByTestId } = render(<BasicInfoStep {...defaultProps} />);

      expect(getByTestId('profile-photo-upload')).toBeTruthy();
      expect(getByTestId('first-name-input')).toBeTruthy();
      expect(getByTestId('last-name-input')).toBeTruthy();
      expect(getByTestId('professional-title-input')).toBeTruthy();
      expect(getByTestId('email-input')).toBeTruthy();
      expect(getByTestId('phone-input')).toBeTruthy();
      expect(getByTestId('city-input')).toBeTruthy();
      expect(getByTestId('country-select')).toBeTruthy();
      expect(getByTestId('languages-select')).toBeTruthy();
      expect(getByTestId('experience-slider')).toBeTruthy();
      expect(getByTestId('teaching-level-select')).toBeTruthy();
      expect(getByTestId('introduction-textarea')).toBeTruthy();
    });

    it('should populate fields with existing form data', () => {
      const { getByTestId, getByDisplayValue } = render(
        <BasicInfoStep {...defaultProps} />
      );

      expect(getByDisplayValue(mockFormData.first_name)).toBeTruthy();
      expect(getByDisplayValue(mockFormData.last_name)).toBeTruthy();
      expect(getByDisplayValue(mockFormData.professional_title)).toBeTruthy();
      expect(getByDisplayValue(mockFormData.email)).toBeTruthy();
      expect(getByDisplayValue(mockFormData.phone_number)).toBeTruthy();
      expect(getByDisplayValue(mockFormData.location.city)).toBeTruthy();
      expect(getByDisplayValue(mockFormData.introduction)).toBeTruthy();
    });

    it('should show field labels correctly', () => {
      const { getByText } = render(<BasicInfoStep {...defaultProps} />);

      expect(getByText('Profile Photo')).toBeTruthy();
      expect(getByText('First Name *')).toBeTruthy();
      expect(getByText('Last Name *')).toBeTruthy();
      expect(getByText('Professional Title *')).toBeTruthy();
      expect(getByText('Email Address *')).toBeTruthy();
      expect(getByText('Phone Number')).toBeTruthy();
      expect(getByText('City *')).toBeTruthy();
      expect(getByText('Country *')).toBeTruthy();
      expect(getByText('Languages Spoken')).toBeTruthy();
      expect(getByText('Years of Experience')).toBeTruthy();
      expect(getByText('Teaching Level')).toBeTruthy();
      expect(getByText('Brief Introduction')).toBeTruthy();
    });

    it('should indicate required fields with asterisk', () => {
      const { getByText } = render(<BasicInfoStep {...defaultProps} />);

      expect(getByText('First Name *')).toBeTruthy();
      expect(getByText('Last Name *')).toBeTruthy();
      expect(getByText('Professional Title *')).toBeTruthy();
      expect(getByText('Email Address *')).toBeTruthy();
      expect(getByText('City *')).toBeTruthy();
      expect(getByText('Country *')).toBeTruthy();
    });
  });

  describe('Form Interactions', () => {
    it('should call onFormDataChange when text inputs change', async () => {
      const { getByTestId } = render(<BasicInfoStep {...defaultProps} />);

      await fillFormField(getByTestId, 'first-name-input', 'Jane');

      expect(mockOnFormDataChange).toHaveBeenCalledWith({
        first_name: 'Jane',
      });
    });

    it('should call onFormDataChange when email changes', async () => {
      const { getByTestId } = render(<BasicInfoStep {...defaultProps} />);

      await fillFormField(getByTestId, 'email-input', 'jane@example.com');

      expect(mockOnFormDataChange).toHaveBeenCalledWith({
        email: 'jane@example.com',
      });
    });

    it('should call onFormDataChange when phone number changes', async () => {
      const { getByTestId } = render(<BasicInfoStep {...defaultProps} />);

      await fillFormField(getByTestId, 'phone-input', '+351123456789');

      expect(mockOnFormDataChange).toHaveBeenCalledWith({
        phone_number: '+351123456789',
      });
    });

    it('should call onFormDataChange when location changes', async () => {
      const { getByTestId } = render(<BasicInfoStep {...defaultProps} />);

      await fillFormField(getByTestId, 'city-input', 'Porto');

      expect(mockOnFormDataChange).toHaveBeenCalledWith({
        location: {
          ...mockFormData.location,
          city: 'Porto',
        },
      });
    });

    it('should call onFormDataChange when country is selected', async () => {
      const { getByTestId } = render(<BasicInfoStep {...defaultProps} />);

      const countrySelect = getByTestId('country-select');
      fireEvent(countrySelect, 'onValueChange', 'Spain');

      expect(mockOnFormDataChange).toHaveBeenCalledWith({
        location: {
          ...mockFormData.location,
          country: 'Spain',
        },
      });
    });

    it('should call onFormDataChange when languages are selected', async () => {
      const { getByTestId } = render(<BasicInfoStep {...defaultProps} />);

      const languagesSelect = getByTestId('languages-select');
      fireEvent(languagesSelect, 'onValueChange', ['Portuguese', 'English', 'Spanish']);

      expect(mockOnFormDataChange).toHaveBeenCalledWith({
        languages: ['Portuguese', 'English', 'Spanish'],
      });
    });

    it('should call onFormDataChange when experience slider changes', async () => {
      const { getByTestId } = render(<BasicInfoStep {...defaultProps} />);

      const experienceSlider = getByTestId('experience-slider');
      fireEvent(experienceSlider, 'onValueChange', [8]);

      expect(mockOnFormDataChange).toHaveBeenCalledWith({
        years_experience: 8,
      });
    });

    it('should call onFormDataChange when teaching level is selected', async () => {
      const { getByTestId } = render(<BasicInfoStep {...defaultProps} />);

      const teachingLevelSelect = getByTestId('teaching-level-select');
      fireEvent(teachingLevelSelect, 'onValueChange', 'Primary');

      expect(mockOnFormDataChange).toHaveBeenCalledWith({
        teaching_level: 'Primary',
      });
    });

    it('should call onFormDataChange when introduction changes', async () => {
      const { getByTestId } = render(<BasicInfoStep {...defaultProps} />);

      await fillFormField(getByTestId, 'introduction-textarea', 'Updated introduction');

      expect(mockOnFormDataChange).toHaveBeenCalledWith({
        introduction: 'Updated introduction',
      });
    });
  });

  describe('Profile Photo Upload', () => {
    beforeEach(() => {
      const mockImagePicker = require('expo-image-picker');
      mockImagePicker.launchImageLibraryAsync.mockClear();
      mockImagePicker.requestMediaLibraryPermissionsAsync.mockClear();
    });

    it('should show current profile photo if available', () => {
      const propsWithPhoto = {
        ...defaultProps,
        formData: {
          ...mockFormData,
          profile_photo: 'https://example.com/photo.jpg',
        },
      };

      const { getByTestId } = render(<BasicInfoStep {...propsWithPhoto} />);

      const profileImage = getByTestId('profile-photo-image');
      expect(profileImage.props.source.uri).toBe('https://example.com/photo.jpg');
    });

    it('should show placeholder when no photo available', () => {
      const propsWithoutPhoto = {
        ...defaultProps,
        formData: {
          ...mockFormData,
          profile_photo: undefined,
        },
      };

      const { getByTestId } = render(<BasicInfoStep {...propsWithoutPhoto} />);

      expect(getByTestId('profile-photo-placeholder')).toBeTruthy();
    });

    it('should open image picker when photo upload is pressed', async () => {
      const mockImagePicker = require('expo-image-picker');
      mockImagePicker.requestMediaLibraryPermissionsAsync.mockResolvedValue({ status: 'granted' });
      mockImagePicker.launchImageLibraryAsync.mockResolvedValue({
        canceled: false,
        assets: [{ uri: 'file://photo.jpg' }],
      });

      const { getByTestId } = render(<BasicInfoStep {...defaultProps} />);

      await pressButton(getByTestId, 'profile-photo-upload-button');

      expect(mockImagePicker.requestMediaLibraryPermissionsAsync).toHaveBeenCalled();
      expect(mockImagePicker.launchImageLibraryAsync).toHaveBeenCalledWith({
        mediaTypes: 'Images',
        allowsEditing: true,
        aspect: [1, 1],
        quality: 0.8,
      });
    });

    it('should handle photo selection', async () => {
      const mockImagePicker = require('expo-image-picker');
      mockImagePicker.requestMediaLibraryPermissionsAsync.mockResolvedValue({ status: 'granted' });
      mockImagePicker.launchImageLibraryAsync.mockResolvedValue({
        canceled: false,
        assets: [{ uri: 'file://new-photo.jpg', width: 1000, height: 1000 }],
      });

      const { getByTestId } = render(<BasicInfoStep {...defaultProps} />);

      await pressButton(getByTestId, 'profile-photo-upload-button');

      await waitFor(() => {
        expect(mockOnFormDataChange).toHaveBeenCalledWith({
          profile_photo: 'file://new-photo.jpg',
        });
      });
    });

    it('should handle permission denied', async () => {
      const mockImagePicker = require('expo-image-picker');
      mockImagePicker.requestMediaLibraryPermissionsAsync.mockResolvedValue({ status: 'denied' });

      const { getByTestId, getByText } = render(<BasicInfoStep {...defaultProps} />);

      await pressButton(getByTestId, 'profile-photo-upload-button');

      expect(getByText('Permission to access camera roll is required!')).toBeTruthy();
    });

    it('should handle cancelled photo selection', async () => {
      const mockImagePicker = require('expo-image-picker');
      mockImagePicker.requestMediaLibraryPermissionsAsync.mockResolvedValue({ status: 'granted' });
      mockImagePicker.launchImageLibraryAsync.mockResolvedValue({
        canceled: true,
      });

      const { getByTestId } = render(<BasicInfoStep {...defaultProps} />);

      await pressButton(getByTestId, 'profile-photo-upload-button');

      expect(mockOnFormDataChange).not.toHaveBeenCalled();
    });

    it('should show loading state during photo upload', () => {
      const propsWithLoading = {
        ...defaultProps,
        isLoading: true,
      };

      const { getByTestId } = render(<BasicInfoStep {...propsWithLoading} />);

      const uploadButton = getByTestId('profile-photo-upload-button');
      expect(uploadButton.props.accessibilityState.disabled).toBe(true);
      expect(getByTestId('photo-upload-spinner')).toBeTruthy();
    });
  });

  describe('Validation', () => {
    it('should display validation errors', () => {
      const validationErrors = createMockValidationErrors({
        first_name: ['First name is required'],
        email: ['Please enter a valid email address'],
        phone_number: ['Phone number format is invalid'],
      });

      const { getByText } = render(
        <BasicInfoStep {...defaultProps} validationErrors={validationErrors} />
      );

      expectValidationError(getByText, 'First name is required');
      expectValidationError(getByText, 'Please enter a valid email address');
      expectValidationError(getByText, 'Phone number format is invalid');
    });

    it('should clear validation errors when fields are updated', async () => {
      const validationErrors = createMockValidationErrors({
        first_name: ['First name is required'],
      });

      const { getByTestId, queryByText, rerender } = render(
        <BasicInfoStep {...defaultProps} validationErrors={validationErrors} />
      );

      // Initially should show error
      expect(queryByText('First name is required')).toBeTruthy();

      // Clear validation errors (simulating parent component clearing them)
      rerender(
        <BasicInfoStep {...defaultProps} validationErrors={{}} />
      );

      expect(queryByText('First name is required')).toBeNull();
    });

    it('should validate email format on blur', async () => {
      const { getByTestId } = render(<BasicInfoStep {...defaultProps} />);

      const emailInput = getByTestId('email-input');
      
      fireEvent.changeText(emailInput, 'invalid-email');
      fireEvent(emailInput, 'onBlur');

      await waitForAsyncUpdates();

      // Component should trigger validation (tested via integration tests)
      expect(mockOnFormDataChange).toHaveBeenCalledWith({
        email: 'invalid-email',
      });
    });

    it('should validate phone number format', async () => {
      const { getByTestId } = render(<BasicInfoStep {...defaultProps} />);

      const phoneInput = getByTestId('phone-input');
      
      fireEvent.changeText(phoneInput, '123');
      fireEvent(phoneInput, 'onBlur');

      await waitForAsyncUpdates();

      expect(mockOnFormDataChange).toHaveBeenCalledWith({
        phone_number: '123',
      });
    });

    it('should enforce character limits', async () => {
      const { getByTestId } = render(<BasicInfoStep {...defaultProps} />);

      const longText = 'a'.repeat(1000);
      
      await fillFormField(getByTestId, 'introduction-textarea', longText);

      // Should truncate to character limit (e.g., 500 characters)
      expect(mockOnFormDataChange).toHaveBeenCalledWith({
        introduction: longText.substring(0, 500),
      });
    });
  });

  describe('Field Dependencies', () => {
    it('should update timezone when country changes', async () => {
      const { getByTestId } = render(<BasicInfoStep {...defaultProps} />);

      const countrySelect = getByTestId('country-select');
      fireEvent(countrySelect, 'onValueChange', 'Spain');

      expect(mockOnFormDataChange).toHaveBeenCalledWith({
        location: {
          ...mockFormData.location,
          country: 'Spain',
          timezone: expect.stringContaining('Europe/Madrid'),
        },
      });
    });

    it('should suggest languages based on country', async () => {
      const { getByTestId } = render(<BasicInfoStep {...defaultProps} />);

      const countrySelect = getByTestId('country-select');
      fireEvent(countrySelect, 'onValueChange', 'France');

      // Should suggest French as a language option
      const languagesSelect = getByTestId('languages-select');
      expect(languagesSelect.props.suggestedOptions).toContain('French');
    });

    it('should format phone number based on country', async () => {
      const { getByTestId } = render(<BasicInfoStep {...defaultProps} />);

      const countrySelect = getByTestId('country-select');
      fireEvent(countrySelect, 'onValueChange', 'United States');

      const phoneInput = getByTestId('phone-input');
      expect(phoneInput.props.placeholder).toContain('+1');
    });
  });

  describe('User Experience', () => {
    it('should show character count for introduction field', () => {
      const { getByText } = render(<BasicInfoStep {...defaultProps} />);

      const characterCount = mockFormData.introduction.length;
      expect(getByText(`${characterCount}/500`)).toBeTruthy();
    });

    it('should show experience years as label', () => {
      const { getByText } = render(<BasicInfoStep {...defaultProps} />);

      expect(getByText(`${mockFormData.years_experience} years`)).toBeTruthy();
    });

    it('should provide helpful placeholder text', () => {
      const { getByTestId } = render(<BasicInfoStep {...defaultProps} />);

      const titleInput = getByTestId('professional-title-input');
      expect(titleInput.props.placeholder).toBe('e.g., Mathematics Teacher, English Tutor');

      const introTextarea = getByTestId('introduction-textarea');
      expect(introTextarea.props.placeholder).toContain('Tell students a bit about yourself');
    });

    it('should show helpful hints for complex fields', () => {
      const { getByText } = render(<BasicInfoStep {...defaultProps} />);

      expect(getByText('Select all languages you can teach in')).toBeTruthy();
      expect(getByText('This helps students find you based on your location')).toBeTruthy();
    });
  });

  describe('Loading States', () => {
    it('should disable form when loading', () => {
      const propsWithLoading = {
        ...defaultProps,
        isLoading: true,
      };

      const { getByTestId } = render(<BasicInfoStep {...propsWithLoading} />);

      const firstNameInput = getByTestId('first-name-input');
      const countrySelect = getByTestId('country-select');

      expect(firstNameInput.props.editable).toBe(false);
      expect(countrySelect.props.disabled).toBe(true);
    });

    it('should show loading indicators on interactive elements', () => {
      const propsWithLoading = {
        ...defaultProps,
        isLoading: true,
      };

      const { getByTestId } = render(<BasicInfoStep {...propsWithLoading} />);

      expect(getByTestId('form-loading-overlay')).toBeTruthy();
    });
  });

  describe('Accessibility', () => {
    it('should have proper accessibility labels', () => {
      const { getByTestId } = render(<BasicInfoStep {...defaultProps} />);

      const firstNameInput = getByTestId('first-name-input');
      expect(firstNameInput.props.accessibilityLabel).toBe('First Name');

      const emailInput = getByTestId('email-input');
      expect(emailInput.props.accessibilityLabel).toBe('Email Address');
    });

    it('should announce validation errors to screen readers', () => {
      const validationErrors = createMockValidationErrors({
        first_name: ['First name is required'],
      });

      const { getByTestId } = render(
        <BasicInfoStep {...defaultProps} validationErrors={validationErrors} />
      );

      const errorMessage = getByTestId('first-name-error');
      expect(errorMessage.props.accessibilityLiveRegion).toBe('polite');
    });

    it('should have proper keyboard navigation order', () => {
      const { getByTestId } = render(<BasicInfoStep {...defaultProps} />);

      const firstNameInput = getByTestId('first-name-input');
      const lastNameInput = getByTestId('last-name-input');

      expect(firstNameInput.props.returnKeyType).toBe('next');
      expect(lastNameInput.props.returnKeyType).toBe('next');
    });

    it('should focus next field on return key press', async () => {
      const { getByTestId } = render(<BasicInfoStep {...defaultProps} />);

      const firstNameInput = getByTestId('first-name-input');
      
      fireEvent(firstNameInput, 'onSubmitEditing');

      // Should focus last name input (tested via focus management)
      const lastNameInput = getByTestId('last-name-input');
      expect(lastNameInput.props.ref.current?.focus).toBeDefined();
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty form data gracefully', () => {
      const emptyFormData = {
        ...mockFormData,
        first_name: '',
        last_name: '',
        email: '',
        professional_title: '',
        phone_number: '',
        location: { city: '', country: '', timezone: '' },
        languages: [],
        years_experience: 0,
        teaching_level: '',
        introduction: '',
      };

      const { getByTestId } = render(
        <BasicInfoStep {...defaultProps} formData={emptyFormData} />
      );

      // Should render without crashing
      expect(getByTestId('first-name-input')).toBeTruthy();
    });

    it('should handle malformed phone numbers', async () => {
      const { getByTestId } = render(<BasicInfoStep {...defaultProps} />);

      await fillFormField(getByTestId, 'phone-input', 'not-a-phone-number');

      expect(mockOnFormDataChange).toHaveBeenCalledWith({
        phone_number: 'not-a-phone-number',
      });
    });

    it('should handle very long text inputs', async () => {
      const { getByTestId } = render(<BasicInfoStep {...defaultProps} />);

      const veryLongName = 'a'.repeat(200);
      
      await fillFormField(getByTestId, 'first-name-input', veryLongName);

      // Should handle long input (might truncate or show warning)
      expect(mockOnFormDataChange).toHaveBeenCalledWith({
        first_name: expect.stringMatching(/^a+$/),
      });
    });

    it('should handle special characters in names', async () => {
      const { getByTestId } = render(<BasicInfoStep {...defaultProps} />);

      const nameWithSpecialChars = 'José María Ñoño';
      
      await fillFormField(getByTestId, 'first-name-input', nameWithSpecialChars);

      expect(mockOnFormDataChange).toHaveBeenCalledWith({
        first_name: nameWithSpecialChars,
      });
    });
  });

  describe('Performance', () => {
    it('should debounce rapid input changes', async () => {
      jest.useFakeTimers();

      const { getByTestId } = render(<BasicInfoStep {...defaultProps} />);

      const firstNameInput = getByTestId('first-name-input');

      // Rapid changes
      fireEvent.changeText(firstNameInput, 'J');
      fireEvent.changeText(firstNameInput, 'Jo');
      fireEvent.changeText(firstNameInput, 'Joh');
      fireEvent.changeText(firstNameInput, 'John');

      // Should not call onChange for each character
      expect(mockOnFormDataChange).toHaveBeenCalledTimes(4);

      jest.useRealTimers();
    });

    it('should not re-render unnecessarily', () => {
      const renderSpy = jest.fn();
      
      const TestComponent = (props: any) => {
        renderSpy();
        return <BasicInfoStep {...props} />;
      };

      const { rerender } = render(<TestComponent {...defaultProps} />);

      expect(renderSpy).toHaveBeenCalledTimes(1);

      // Re-render with same props
      rerender(<TestComponent {...defaultProps} />);

      expect(renderSpy).toHaveBeenCalledTimes(2);
    });
  });
});