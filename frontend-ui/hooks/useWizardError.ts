import { useState, useCallback, useRef } from 'react';

export interface WizardError {
  id: string;
  message: string;
  type: 'validation' | 'network' | 'server' | 'client' | 'unknown';
  severity: 'low' | 'medium' | 'high' | 'critical';
  context?: string;
  step?: number;
  field?: string;
  timestamp: number;
  recoverable: boolean;
  retryable: boolean;
  suggestions: string[];
}

interface ErrorHandlerOptions {
  maxErrors?: number;
  autoClean?: boolean;
  autoCleanDelay?: number;
  logErrors?: boolean;
  reportErrors?: boolean;
}

interface ErrorContext {
  step?: number;
  field?: string;
  action?: string;
  additionalInfo?: Record<string, any>;
}

/**
 * Custom hook for consistent error handling throughout the wizard
 * Provides error categorization, recovery suggestions, and cleanup
 */
export function useWizardError(options: ErrorHandlerOptions = {}) {
  const {
    maxErrors = 10,
    autoClean = true,
    autoCleanDelay = 10000, // 10 seconds
    logErrors = true,
    reportErrors = false,
  } = options;

  const [errors, setErrors] = useState<WizardError[]>([]);
  const errorTimeouts = useRef<Map<string, NodeJS.Timeout>>(new Map());

  const generateErrorId = useCallback(() => {
    return `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }, []);

  const categorizeError = useCallback((error: Error | string, context?: ErrorContext): Partial<WizardError> => {
    const message = typeof error === 'string' ? error : error.message;
    const lowerMessage = message.toLowerCase();

    // Network errors
    if (lowerMessage.includes('network') || 
        lowerMessage.includes('fetch') || 
        lowerMessage.includes('connection') ||
        lowerMessage.includes('timeout')) {
      return {
        type: 'network',
        severity: 'high',
        recoverable: true,
        retryable: true,
        suggestions: [
          'Check your internet connection',
          'Try again in a few moments',
          'Save your work and continue later'
        ]
      };
    }

    // Server errors
    if (lowerMessage.includes('server') || 
        lowerMessage.includes('500') || 
        lowerMessage.includes('503') ||
        lowerMessage.includes('internal')) {
      return {
        type: 'server',
        severity: 'high',
        recoverable: true,
        retryable: true,
        suggestions: [
          'The server is temporarily unavailable',
          'Try again in a few minutes',
          'Contact support if the problem persists'
        ]
      };
    }

    // Validation errors
    if (lowerMessage.includes('validation') || 
        lowerMessage.includes('invalid') || 
        lowerMessage.includes('required') ||
        lowerMessage.includes('format')) {
      return {
        type: 'validation',
        severity: 'medium',
        recoverable: true,
        retryable: false,
        suggestions: [
          'Please check your input',
          'Make sure all required fields are filled',
          'Follow the specified format guidelines'
        ]
      };
    }

    // Client-side errors
    if (lowerMessage.includes('component') || 
        lowerMessage.includes('render') || 
        lowerMessage.includes('hook') ||
        lowerMessage.includes('undefined')) {
      return {
        type: 'client',
        severity: 'medium',
        recoverable: true,
        retryable: true,
        suggestions: [
          'Try refreshing the page',
          'Clear your browser cache',
          'Update your browser to the latest version'
        ]
      };
    }

    // Default unknown error
    return {
      type: 'unknown',
      severity: 'medium',
      recoverable: true,
      retryable: true,
      suggestions: [
        'Please try again',
        'Save your work and continue',
        'Contact support if the problem continues'
      ]
    };
  }, []);

  const logError = useCallback((wizardError: WizardError) => {
    if (!logErrors) return;

    const logData = {
      id: wizardError.id,
      message: wizardError.message,
      type: wizardError.type,
      severity: wizardError.severity,
      context: wizardError.context,
      step: wizardError.step,
      field: wizardError.field,
      timestamp: wizardError.timestamp,
      userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : 'unknown',
      url: typeof window !== 'undefined' ? window.location.href : 'unknown',
    };

    if (__DEV__) {
      console.group(`🚨 Wizard Error [${wizardError.severity.toUpperCase()}]`);
      console.error('Message:', wizardError.message);
      console.error('Type:', wizardError.type);
      console.error('Context:', wizardError.context);
      console.error('Full Error:', logData);
      console.groupEnd();
    }

    // In production, send to error reporting service
    if (reportErrors && !__DEV__) {
      try {
        // Example: Send to error reporting service
        // errorReportingService.report(logData);
      } catch (reportingError) {
        console.error('Failed to report error:', reportingError);
      }
    }
  }, [logErrors, reportErrors]);

  const showError = useCallback((
    error: Error | string,
    context?: ErrorContext
  ): string => {
    const errorId = generateErrorId();
    const errorDetails = categorizeError(error, context);
    const message = typeof error === 'string' ? error : error.message;

    const wizardError: WizardError = {
      id: errorId,
      message,
      timestamp: Date.now(),
      context: context?.action,
      step: context?.step,
      field: context?.field,
      ...errorDetails,
    } as WizardError;

    // Log the error
    logError(wizardError);

    // Add to errors list
    setErrors(prev => {
      const newErrors = [wizardError, ...prev];
      // Limit maximum number of errors
      return newErrors.slice(0, maxErrors);
    });

    // Auto-clean error after delay
    if (autoClean) {
      const timeout = setTimeout(() => {
        clearError(errorId);
        errorTimeouts.current.delete(errorId);
      }, autoCleanDelay);
      
      errorTimeouts.current.set(errorId, timeout);
    }

    return errorId;
  }, [generateErrorId, categorizeError, logError, maxErrors, autoClean, autoCleanDelay]);

  const clearError = useCallback((errorId: string) => {
    // Clear timeout if exists
    const timeout = errorTimeouts.current.get(errorId);
    if (timeout) {
      clearTimeout(timeout);
      errorTimeouts.current.delete(errorId);
    }

    // Remove error from list
    setErrors(prev => prev.filter(error => error.id !== errorId));
  }, []);

  const clearAllErrors = useCallback(() => {
    // Clear all timeouts
    errorTimeouts.current.forEach(timeout => clearTimeout(timeout));
    errorTimeouts.current.clear();
    
    // Clear all errors
    setErrors([]);
  }, []);

  const clearErrorsByType = useCallback((type: WizardError['type']) => {
    setErrors(prev => {
      const errorsToRemove = prev.filter(error => error.type === type);
      
      // Clear timeouts for removed errors
      errorsToRemove.forEach(error => {
        const timeout = errorTimeouts.current.get(error.id);
        if (timeout) {
          clearTimeout(timeout);
          errorTimeouts.current.delete(error.id);
        }
      });

      return prev.filter(error => error.type !== type);
    });
  }, []);

  const clearErrorsByStep = useCallback((step: number) => {
    setErrors(prev => {
      const errorsToRemove = prev.filter(error => error.step === step);
      
      // Clear timeouts for removed errors
      errorsToRemove.forEach(error => {
        const timeout = errorTimeouts.current.get(error.id);
        if (timeout) {
          clearTimeout(timeout);
          errorTimeouts.current.delete(error.id);
        }
      });

      return prev.filter(error => error.step !== step);
    });
  }, []);

  const getErrorsByType = useCallback((type: WizardError['type']) => {
    return errors.filter(error => error.type === type);
  }, [errors]);

  const getErrorsByStep = useCallback((step: number) => {
    return errors.filter(error => error.step === step);
  }, [errors]);

  const getErrorsBySeverity = useCallback((severity: WizardError['severity']) => {
    return errors.filter(error => error.severity === severity);
  }, [errors]);

  const hasErrors = errors.length > 0;
  const hasCriticalErrors = errors.some(error => error.severity === 'critical');
  const hasRetryableErrors = errors.some(error => error.retryable);

  // Cleanup on unmount
  React.useEffect(() => {
    return () => {
      errorTimeouts.current.forEach(timeout => clearTimeout(timeout));
      errorTimeouts.current.clear();
    };
  }, []);

  return {
    // Error state
    errors,
    hasErrors,
    hasCriticalErrors,
    hasRetryableErrors,
    
    // Error management
    showError,
    clearError,
    clearAllErrors,
    clearErrorsByType,
    clearErrorsByStep,
    
    // Error queries
    getErrorsByType,
    getErrorsByStep,
    getErrorsBySeverity,
  };
}

/**
 * Hook for handling form validation errors specifically
 */
export function useValidationErrors() {
  const [validationErrors, setValidationErrors] = useState<Record<string, string[]>>({});

  const setFieldError = useCallback((field: string, errors: string[]) => {
    setValidationErrors(prev => ({
      ...prev,
      [field]: errors,
    }));
  }, []);

  const clearFieldError = useCallback((field: string) => {
    setValidationErrors(prev => {
      const newErrors = { ...prev };
      delete newErrors[field];
      return newErrors;
    });
  }, []);

  const clearAllValidationErrors = useCallback(() => {
    setValidationErrors({});
  }, []);

  const hasValidationErrors = Object.keys(validationErrors).length > 0;
  const getFieldErrors = useCallback((field: string) => validationErrors[field] || [], [validationErrors]);

  return {
    validationErrors,
    hasValidationErrors,
    setFieldError,
    clearFieldError,
    clearAllValidationErrors,
    getFieldErrors,
  };
}

// Import React for useEffect
import React from 'react';