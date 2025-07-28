/**
 * Student Information Form Component
 * 
 * Collects and validates student information for purchase process.
 * Supports both authenticated and guest user flows with comprehensive validation.
 */

import React, { useState, useEffect } from 'react';
import { User, Mail, AlertCircle, CheckCircle } from 'lucide-react-native';
import { Alert } from '@/components/ui/alert';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { FormControl } from '@/components/ui/form-control';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Input, InputField } from '@/components/ui/input';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { useAuthContext } from '@/api/authContext';
import type { PricingPlan } from '@/types/purchase';

interface StudentInfoFormProps {
  selectedPlan: PricingPlan;
  studentName: string;
  studentEmail: string;
  errors: Record<string, string>;
  onInfoChange: (name: string, email: string) => void;
  onSubmit: () => void;
  onBack: () => void;
  disabled?: boolean;
  className?: string;
}

/**
 * Component for collecting student information with validation and authentication integration.
 */
export function StudentInfoForm({
  selectedPlan,
  studentName,
  studentEmail,
  errors,
  onInfoChange,
  onSubmit,
  onBack,
  disabled = false,
  className = '',
}: StudentInfoFormProps) {
  const { user } = useAuthContext();
  const [localName, setLocalName] = useState(studentName);
  const [localEmail, setLocalEmail] = useState(studentEmail);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  // Initialize form with authenticated user data if available
  useEffect(() => {
    if (user && !studentName && !studentEmail) {
      const userName = user.name || '';
      const userEmail = user.email || '';
      setLocalName(userName);
      setLocalEmail(userEmail);
      onInfoChange(userName, userEmail);
    }
  }, [user, studentName, studentEmail, onInfoChange]);

  // Track unsaved changes
  useEffect(() => {
    const hasChanges = localName !== studentName || localEmail !== studentEmail;
    setHasUnsavedChanges(hasChanges);
  }, [localName, localEmail, studentName, studentEmail]);

  const handleNameChange = (value: string) => {
    setLocalName(value);
    onInfoChange(value, localEmail);
  };

  const handleEmailChange = (value: string) => {
    setLocalEmail(value);
    onInfoChange(localName, value);
  };

  const handleSubmit = () => {
    if (!disabled && isFormValid()) {
      onSubmit();
    }
  };

  const isFormValid = () => {
    return (
      localName.trim().length >= 2 &&
      localEmail.trim().length > 0 &&
      isValidEmail(localEmail.trim()) &&
      Object.keys(errors).length === 0
    );
  };

  const isValidEmail = (email: string) => {
    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    return emailRegex.test(email);
  };

  // Format price for display
  const formatPrice = (price: string) => {
    const numPrice = parseFloat(price);
    return numPrice % 1 === 0 ? numPrice.toString() : numPrice.toFixed(2);
  };

  return (
    <Card className={`p-6 ${className}`}>
      <VStack space="lg">
        {/* Form header */}
        <VStack space="sm">
          <HStack space="sm" className="items-center">
            <Icon as={User} size="lg" className="text-primary-600" />
            <Heading size="lg" className="text-typography-900">
              Student Information
            </Heading>
          </HStack>
          
          <Text className="text-typography-600">
            Please provide the student information for this tutoring package.
          </Text>
        </VStack>

        {/* Selected plan summary */}
        <Card className="p-4 bg-primary-50 border border-primary-200">
          <VStack space="sm">
            <HStack className="items-center justify-between">
              <Text className="font-semibold text-primary-800">
                Selected Plan: {selectedPlan.name}
              </Text>
              <Text className="font-bold text-primary-900">
                €{formatPrice(selectedPlan.price_eur)}
              </Text>
            </HStack>
            <Text className="text-sm text-primary-700">
              {selectedPlan.hours_included} hours • {selectedPlan.plan_type_display}
            </Text>
          </VStack>
        </Card>

        {/* Authentication status */}
        {user ? (
          <Alert action="success" variant="outline">
            <Icon as={CheckCircle} className="text-success-600" />
            <VStack space="xs" className="flex-1">
              <Text className="text-success-800 font-medium">
                Signed in as {user.name || user.email}
              </Text>
              <Text className="text-success-700 text-sm">
                You can modify the information below if needed.
              </Text>
            </VStack>
          </Alert>
        ) : (
          <Alert action="info" variant="outline">
            <Icon as={User} className="text-info-600" />
            <VStack space="xs" className="flex-1">
              <Text className="text-info-800 font-medium">
                Guest Purchase
              </Text>
              <Text className="text-info-700 text-sm">
                You're purchasing as a guest. An account will be created for you.
              </Text>
            </VStack>
          </Alert>
        )}

        {/* Form fields */}
        <VStack space="md">
          {/* Name field */}
          <FormControl 
            isInvalid={!!errors.name}
            isRequired
          >
            <VStack space="xs">
              <Text className="font-medium text-typography-800">
                Student Name *
              </Text>
              <Input
                variant="outline"
                size="lg"
                className={errors.name ? 'border-error-300' : ''}
              >
                <InputField
                  placeholder="Enter student's full name"
                  value={localName}
                  onChangeText={handleNameChange}
                  autoCapitalize="words"
                  textContentType="name"
                  autoComplete="name"
                  editable={!disabled}
                />
              </Input>
              {errors.name && (
                <HStack space="xs" className="items-center">
                  <Icon as={AlertCircle} size="xs" className="text-error-500" />
                  <Text className="text-sm text-error-600">
                    {errors.name}
                  </Text>
                </HStack>
              )}
            </VStack>
          </FormControl>

          {/* Email field */}
          <FormControl 
            isInvalid={!!errors.email}
            isRequired
          >
            <VStack space="xs">
              <Text className="font-medium text-typography-800">
                Email Address *
              </Text>
              <Input
                variant="outline"
                size="lg"
                className={errors.email ? 'border-error-300' : ''}
              >
                <InputField
                  placeholder="Enter email address"
                  value={localEmail}
                  onChangeText={handleEmailChange}
                  keyboardType="email-address"
                  textContentType="emailAddress"
                  autoComplete="email"
                  autoCapitalize="none"
                  editable={!disabled}
                />
              </Input>
              {errors.email && (
                <HStack space="xs" className="items-center">
                  <Icon as={AlertCircle} size="xs" className="text-error-500" />
                  <Text className="text-sm text-error-600">
                    {errors.email}
                  </Text>
                </HStack>
              )}
              {!errors.email && localEmail && (
                <Text className="text-xs text-typography-500">
                  We'll send purchase confirmation and access instructions to this email.
                </Text>
              )}
            </VStack>
          </FormControl>
        </VStack>

        {/* Form validation summary */}
        {Object.keys(errors).length > 0 && (
          <Alert action="error" variant="outline">
            <Icon as={AlertCircle} className="text-error-600" />
            <VStack space="xs" className="flex-1">
              <Text className="text-error-800 font-medium">
                Please correct the following errors:
              </Text>
              <VStack space="xs">
                {Object.entries(errors).map(([field, message]) => (
                  <Text key={field} className="text-sm text-error-700">
                    • {message}
                  </Text>
                ))}
              </VStack>
            </VStack>
          </Alert>
        )}

        {/* Action buttons */}
        <VStack space="sm">
          <Button
            action="primary"
            variant="solid"
            size="lg"
            className="w-full"
            onPress={handleSubmit}
            disabled={disabled || !isFormValid()}
          >
            <ButtonText>
              Continue to Payment
            </ButtonText>
          </Button>

          <Button
            action="secondary"
            variant="outline"
            size="md"
            className="w-full"
            onPress={onBack}
            disabled={disabled}
          >
            <ButtonText>
              Back to Plan Selection
            </ButtonText>
          </Button>
        </VStack>

        {/* Help text */}
        <VStack space="xs" className="items-center">
          <Text className="text-xs text-typography-500 text-center">
            By continuing, you agree to our Terms of Service and Privacy Policy.
          </Text>
          {!user && (
            <Text className="text-xs text-typography-400 text-center">
              Already have an account? Sign in after purchase to link your hours.
            </Text>
          )}
        </VStack>
      </VStack>
    </Card>
  );
}