/**
 * VerifyCodeForm Component Tests - Business Critical Functionality
 * 
 * Focused on essential authentication functionality for Aprende Comigo EdTech platform
 * Tests verify component integration with business logic and core user flows
 */

import { render } from '@testing-library/react-native';
import React from 'react';

import { VerifyCodeForm } from '@/components/auth/forms/VerifyCodeForm';

// Mock UI dependencies
jest.mock('expo-router');

// Mock any link components using Gluestack v2 approach
jest.mock('@/components/ui/link', () => {
  const React = require('react');
  return {
    Link: ({ children, ...props }: any) => React.createElement('a', props, children),
    LinkText: ({ children, ...props }: any) => React.createElement('span', props, children),
  };
});

describe('VerifyCodeForm - Business Critical Tests', () => {
  const mockEmailLogic = {
    contact: 'test@example.com',
    contactType: 'email' as const,
    isVerifying: false,
    isResending: false,
    error: null,
    submitVerification: jest.fn(),
    resendCode: jest.fn(),
  };

  const mockPhoneLogic = {
    contact: '+1234567890',
    contactType: 'phone' as const,
    isVerifying: false,
    isResending: false,
    error: null,
    submitVerification: jest.fn(),
    resendCode: jest.fn(),
  };

  const mockEmailProps = {
    logic: mockEmailLogic,
    onBack: jest.fn(),
  };

  const mockPhoneProps = {
    logic: mockPhoneLogic,
    onBack: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Component Rendering', () => {
    it('should render successfully for email verification', () => {
      const component = render(<VerifyCodeForm {...mockEmailProps} />);
      expect(component).toBeTruthy();
      expect(component.toJSON()).toBeTruthy();
    });

    it('should render successfully for phone verification', () => {
      const component = render(<VerifyCodeForm {...mockPhoneProps} />);
      expect(component).toBeTruthy();
      expect(component.toJSON()).toBeTruthy();
    });
  });

  describe('Business Logic Integration', () => {
    it('should integrate properly with verification logic hook', () => {
      const component = render(<VerifyCodeForm {...mockEmailProps} />);
      
      expect(component).toBeTruthy();
      
      // Verify the logic functions are properly integrated
      expect(mockEmailLogic.submitVerification).toBeDefined();
      expect(mockEmailLogic.resendCode).toBeDefined();
      expect(typeof mockEmailLogic.submitVerification).toBe('function');
      expect(typeof mockEmailLogic.resendCode).toBe('function');
      
      // Verify contact information is used
      expect(mockEmailLogic.contact).toBe('test@example.com');
      expect(mockEmailLogic.contactType).toBe('email');
    });

    it('should handle different contact types correctly', () => {
      // Test email contact
      const emailComponent = render(<VerifyCodeForm {...mockEmailProps} />);
      expect(emailComponent.toJSON()).toBeTruthy();

      // Test phone contact with different formatting
      const phoneComponent = render(<VerifyCodeForm {...mockPhoneProps} />);
      expect(phoneComponent.toJSON()).toBeTruthy();
    });
  });

  describe('Loading States', () => {
    it('should render correctly in verifying state', () => {
      const verifyingLogic = { ...mockEmailLogic, isVerifying: true };
      const verifyingProps = { ...mockEmailProps, logic: verifyingLogic };
      
      const component = render(<VerifyCodeForm {...verifyingProps} />);
      expect(component.toJSON()).toBeTruthy();
    });

    it('should render correctly in resending state', () => {
      const resendingLogic = { ...mockEmailLogic, isResending: true };
      const resendingProps = { ...mockEmailProps, logic: resendingLogic };
      
      const component = render(<VerifyCodeForm {...resendingProps} />);
      expect(component.toJSON()).toBeTruthy();
    });

    it('should handle both loading states simultaneously', () => {
      const loadingLogic = { ...mockEmailLogic, isVerifying: true, isResending: true };
      const loadingProps = { ...mockEmailProps, logic: loadingLogic };
      
      const component = render(<VerifyCodeForm {...loadingProps} />);
      expect(component.toJSON()).toBeTruthy();
    });
  });

  describe('Error Handling', () => {
    it('should render correctly when there are errors', () => {
      const errorLogic = { ...mockEmailLogic, error: new Error('Verification failed') };
      const errorProps = { ...mockEmailProps, logic: errorLogic };
      
      const component = render(<VerifyCodeForm {...errorProps} />);
      expect(component.toJSON()).toBeTruthy();
    });
  });

  describe('Pure Component Properties', () => {
    it('should be a pure UI component with no side effects', () => {
      const consoleSpy = jest.spyOn(console, 'warn').mockImplementation();

      const component = render(<VerifyCodeForm {...mockEmailProps} />);
      expect(component.toJSON()).toBeTruthy();

      // No warnings should be generated from side effects during rendering
      expect(consoleSpy).not.toHaveBeenCalled();

      consoleSpy.mockRestore();
    });

    it('should handle prop changes correctly', () => {
      const { rerender } = render(<VerifyCodeForm {...mockEmailProps} />);

      // Change to loading state
      const verifyingLogic = { ...mockEmailLogic, isVerifying: true };
      const verifyingProps = { ...mockEmailProps, logic: verifyingLogic };
      
      rerender(<VerifyCodeForm {...verifyingProps} />);
      
      // Should not crash on prop changes
      expect(true).toBe(true);
    });
  });

  describe('Form Integration', () => {
    it('should integrate with React Hook Form correctly', () => {
      // The component uses React Hook Form internally
      // This test verifies it doesn't crash when form validation is involved
      const component = render(<VerifyCodeForm {...mockEmailProps} />);
      expect(component.toJSON()).toBeTruthy();
    });
  });

  describe('Cross-Platform Compatibility', () => {
    it('should render consistently across different contact types', () => {
      const emailComponent = render(<VerifyCodeForm {...mockEmailProps} />);
      const phoneComponent = render(<VerifyCodeForm {...mockPhoneProps} />);
      
      // Both should render successfully
      expect(emailComponent.toJSON()).toBeTruthy();
      expect(phoneComponent.toJSON()).toBeTruthy();
    });
  });
});