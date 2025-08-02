/**
 * Custom hook for managing the complete purchase flow.
 *
 * Handles state management for the entire purchase process from
 * plan selection through payment completion, including error handling
 * and Stripe integration.
 */

import { useState, useCallback, useEffect } from 'react';
import { Alert } from 'react-native';

import { PurchaseApiClient } from '@/api/purchaseApi';
import type {
  PurchaseFlowState,
  UsePurchaseFlowResult,
  PricingPlan,
  StripeInstance,
  StripeElements,
} from '@/types/purchase';

const initialState: PurchaseFlowState = {
  step: 'plan-selection',
  formData: {
    selectedPlan: null,
    studentName: '',
    studentEmail: '',
    isProcessing: false,
    errors: {},
  },
  stripeConfig: null,
  paymentIntentSecret: null,
  transactionId: null,
  errorMessage: null,
};

/**
 * Hook for managing the complete purchase flow with comprehensive state management.
 *
 * @returns Object containing state, actions, and computed properties
 */
export function usePurchaseFlow(): UsePurchaseFlowResult {
  const [state, setState] = useState<PurchaseFlowState>(initialState);

  // Load Stripe configuration on mount
  useEffect(() => {
    const loadStripeConfig = async () => {
      try {
        const config = await PurchaseApiClient.getStripeConfig();
        setState(prev => ({
          ...prev,
          stripeConfig: config,
        }));
      } catch (error: any) {
        console.error('Failed to load Stripe config:', error);
        setState(prev => ({
          ...prev,
          errorMessage: error.message || 'Failed to load payment configuration',
        }));
      }
    };

    loadStripeConfig();
  }, []);

  const selectPlan = useCallback((plan: PricingPlan) => {
    setState(prev => ({
      ...prev,
      formData: {
        ...prev.formData,
        selectedPlan: plan,
        errors: {},
      },
      step: 'user-info',
      errorMessage: null,
    }));
  }, []);

  const updateStudentInfo = useCallback((name: string, email: string) => {
    setState(prev => ({
      ...prev,
      formData: {
        ...prev.formData,
        studentName: name.trim(),
        studentEmail: email.trim().toLowerCase(),
        errors: {
          ...prev.formData.errors,
          ...(name.trim() ? {} : { name: 'Name is required' }),
          ...(email.trim() ? {} : { email: 'Email is required' }),
          ...(email.trim() && isValidEmail(email.trim())
            ? {}
            : { email: 'Please enter a valid email address' }),
        },
      },
    }));
  }, []);

  const validateForm = useCallback((): boolean => {
    const { selectedPlan, studentName, studentEmail } = state.formData;
    const errors: Record<string, string> = {};

    if (!selectedPlan) {
      errors.plan = 'Please select a pricing plan';
    }

    if (!studentName.trim()) {
      errors.name = 'Name is required';
    } else if (studentName.trim().length < 2) {
      errors.name = 'Name must be at least 2 characters long';
    }

    if (!studentEmail.trim()) {
      errors.email = 'Email is required';
    } else if (!isValidEmail(studentEmail.trim())) {
      errors.email = 'Please enter a valid email address';
    }

    setState(prev => ({
      ...prev,
      formData: {
        ...prev.formData,
        errors,
      },
    }));

    return Object.keys(errors).length === 0;
  }, [state.formData]);

  const initiatePurchase = useCallback(async () => {
    if (!validateForm()) {
      return;
    }

    const { selectedPlan, studentName, studentEmail } = state.formData;

    if (!selectedPlan) {
      setError('No plan selected');
      return;
    }

    setState(prev => ({
      ...prev,
      formData: {
        ...prev.formData,
        isProcessing: true,
      },
      errorMessage: null,
    }));

    try {
      const response = await PurchaseApiClient.initiatePurchase({
        plan_id: selectedPlan.id,
        student_info: {
          name: studentName,
          email: studentEmail,
        },
      });

      if (response.success && response.client_secret) {
        setState(prev => ({
          ...prev,
          paymentIntentSecret: response.client_secret!,
          transactionId: response.transaction_id!,
          step: 'payment',
          formData: {
            ...prev.formData,
            isProcessing: false,
          },
        }));
      } else {
        // Handle validation errors from backend
        const errors: Record<string, string> = {};
        if (response.field_errors) {
          Object.entries(response.field_errors).forEach(([field, messages]) => {
            if (Array.isArray(messages) && messages.length > 0) {
              // Handle nested field errors like student_info.email
              const fieldKey = field.includes('.') ? field.split('.').pop() || field : field;
              errors[fieldKey] = messages[0];
            }
          });
        }

        setState(prev => ({
          ...prev,
          formData: {
            ...prev.formData,
            isProcessing: false,
            errors,
          },
          errorMessage: response.message || 'Failed to initiate purchase',
        }));
      }
    } catch (error: any) {
      console.error('Purchase initiation failed:', error);
      setState(prev => ({
        ...prev,
        formData: {
          ...prev.formData,
          isProcessing: false,
        },
        errorMessage: error.message || 'Failed to initiate purchase',
      }));
    }
  }, [state.formData, validateForm]);

  const confirmPayment = useCallback(
    async (stripe: StripeInstance, elements: StripeElements) => {
      if (!state.paymentIntentSecret) {
        setError('No payment intent available');
        return;
      }

      setState(prev => ({
        ...prev,
        formData: {
          ...prev.formData,
          isProcessing: true,
        },
        errorMessage: null,
      }));

      try {
        const { error, paymentIntent } = await stripe.confirmPayment({
          elements,
          confirmParams: {
            return_url: `${window.location.origin}/purchase/success`,
          },
          redirect: 'if_required',
        });

        if (error) {
          console.error('Payment confirmation failed:', error);
          setState(prev => ({
            ...prev,
            formData: {
              ...prev.formData,
              isProcessing: false,
            },
            errorMessage: error.message || 'Payment failed',
            step: 'error',
          }));
        } else if (paymentIntent?.status === 'succeeded') {
          setState(prev => ({
            ...prev,
            formData: {
              ...prev.formData,
              isProcessing: false,
            },
            step: 'success',
          }));
        } else {
          setState(prev => ({
            ...prev,
            formData: {
              ...prev.formData,
              isProcessing: false,
            },
            errorMessage: 'Payment processing incomplete',
            step: 'error',
          }));
        }
      } catch (error: any) {
        console.error('Payment confirmation error:', error);
        setState(prev => ({
          ...prev,
          formData: {
            ...prev.formData,
            isProcessing: false,
          },
          errorMessage: error.message || 'Payment processing failed',
          step: 'error',
        }));
      }
    },
    [state.paymentIntentSecret]
  );

  const resetFlow = useCallback(() => {
    setState(initialState);
  }, []);

  const setError = useCallback((message: string) => {
    setState(prev => ({
      ...prev,
      errorMessage: message,
      step: 'error',
      formData: {
        ...prev.formData,
        isProcessing: false,
      },
    }));
  }, []);

  // Computed properties
  const isLoading = state.formData.isProcessing;
  const canProceed = (() => {
    switch (state.step) {
      case 'plan-selection':
        return !!state.formData.selectedPlan;
      case 'user-info':
        return (
          !!state.formData.selectedPlan &&
          !!state.formData.studentName.trim() &&
          !!state.formData.studentEmail.trim() &&
          isValidEmail(state.formData.studentEmail.trim()) &&
          Object.keys(state.formData.errors).length === 0
        );
      case 'payment':
        return !!state.paymentIntentSecret && !!state.stripeConfig;
      default:
        return false;
    }
  })();

  return {
    state,
    actions: {
      selectPlan,
      updateStudentInfo,
      initiatePurchase,
      confirmPayment,
      resetFlow,
      setError,
    },
    isLoading,
    canProceed,
  };
}

/**
 * Simple email validation helper function.
 *
 * @param email Email string to validate
 * @returns Boolean indicating if email format is valid
 */
function isValidEmail(email: string): boolean {
  const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
  return emailRegex.test(email);
}
