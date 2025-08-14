/**
 * Pure UI Component for Code Verification Form
 *
 * This component contains ONLY UI rendering logic and event handlers.
 * All business logic is handled by the injected logic hook.
 * This separation makes the component highly testable and reusable.
 */

import { zodResolver } from '@hookform/resolvers/zod';
import Link from '@unitools/link';
import { AlertTriangle } from 'lucide-react-native';
import React from 'react';
import { useForm, Controller } from 'react-hook-form';
import { Keyboard } from 'react-native';
import { z } from 'zod';

import { Button, ButtonText } from '@/components/ui/button';
import {
  FormControl,
  FormControlError,
  FormControlErrorIcon,
  FormControlErrorText,
  FormControlLabel,
  FormControlLabelText,
} from '@/components/ui/form-control';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { ArrowLeftIcon, Icon } from '@/components/ui/icon';
import { Input, InputField } from '@/components/ui/input';
import { LinkText } from '@/components/ui/link';
import { Pressable } from '@/components/ui/pressable';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { UseVerifyCodeLogicReturn } from '@/hooks/auth/useVerifyCodeLogic';

// Form validation schema
const verifyCodeSchema = z.object({
  code: z
    .string()
    .min(1, 'Verification code is required')
    .regex(/^\d{6}$/, 'Verification code must be 6 digits'),
});

type VerifyCodeFormData = z.infer<typeof verifyCodeSchema>;

export interface VerifyCodeFormProps {
  logic: UseVerifyCodeLogicReturn;
  onBack?: () => void;
}

export const VerifyCodeForm: React.FC<VerifyCodeFormProps> = ({ logic, onBack }) => {
  // Form handling
  const form = useForm<VerifyCodeFormData>({
    resolver: zodResolver(verifyCodeSchema),
    defaultValues: {
      code: '',
    },
  });

  // Handle form submission
  const onSubmit = async (data: VerifyCodeFormData) => {
    const sanitizedCode = data.code.replace(/\D/g, ''); // Remove non-digits
    await logic.submitVerification(sanitizedCode);
  };

  // Handle keyboard submission
  const handleKeyPress = () => {
    Keyboard.dismiss();
    form.handleSubmit(onSubmit)();
  };

  // Handle code input - sanitize and limit to 6 digits
  const handleCodeChange = (text: string) => {
    const sanitized = text.replace(/\D/g, '').slice(0, 6);
    return sanitized;
  };

  // Format contact display
  const formatContactDisplay = (contact: string, contactType: 'email' | 'phone') => {
    if (contactType === 'email') {
      return contact;
    }

    // Format phone number for display
    if (contactType === 'phone') {
      return contact.replace(/(\+\d)(\d{3})(\d{3})(\d{3})/, (match, g1, g2, g3, g4) => {
        return `${g1} ${g2} ${g3} ${g4}`;
      });
    }

    return contact;
  };

  const displayContact = formatContactDisplay(logic.contact, logic.contactType);

  return (
    <VStack className="w-full" space="lg">
      {/* Header */}
      <VStack className="items-center" space="md">
        {onBack && (
          <Pressable onPress={onBack} className="md:hidden self-start mb-4">
            <Icon as={ArrowLeftIcon} className="text-typography-700" size="xl" />
          </Pressable>
        )}

        {/* Brand logo */}
        <VStack className="items-center mb-2">
          <Text className="text-center text-gradient-primary font-brand text-md">
            aprendecomigo
          </Text>
        </VStack>

        <VStack className="items-center" space="sm">
          <Heading className="text-center font-primary" size="3xl">
            <Text className="color-primary font-primary">Verify Code</Text>
          </Heading>
          <Text className="text-center text-typography-600 font-body text-base leading-relaxed">
            Enter the 6-digit verification code sent to
          </Text>
          <Text className="text-center font-medium text-typography-900 font-body text-base">
            {displayContact}
          </Text>
        </VStack>
      </VStack>

      {/* Form */}
      <VStack className="w-full" space="xl">
        <FormControl isInvalid={!!form.formState.errors?.code} className="w-full">
          <FormControlLabel className="mb-2">
            <FormControlLabelText className="font-primary font-medium text-typography-700">
              Verification Code
            </FormControlLabelText>
          </FormControlLabel>
          <Controller
            name="code"
            control={form.control}
            render={({ field: { onChange, onBlur, value } }) => (
              <VStack className="glass-light rounded-xl p-4">
                <Input className="border-0">
                  <InputField
                    testID="code-input"
                    placeholder="000000"
                    value={value}
                    onChangeText={text => {
                      const sanitized = handleCodeChange(text);
                      onChange(sanitized);
                    }}
                    onBlur={onBlur}
                    onSubmitEditing={handleKeyPress}
                    returnKeyType="done"
                    className="bg-transparent font-body text-base text-center tracking-widest"
                    placeholderTextColor="#94A3B8"
                    keyboardType="numeric"
                    maxLength={6}
                    autoComplete="sms-otp"
                  />
                </Input>
              </VStack>
            )}
          />
          <FormControlError>
            <FormControlErrorIcon as={AlertTriangle} />
            <FormControlErrorText className="font-body">
              {form.formState.errors?.code?.message}
            </FormControlErrorText>
          </FormControlError>
        </FormControl>

        {/* Verify Button */}
        <VStack className="w-full mt-8" space="lg">
          <Pressable
            className="w-full bg-gradient-primary py-4 rounded-xl active:scale-98 transition-all shadow-lg"
            onPress={form.handleSubmit(onSubmit)}
            disabled={logic.isVerifying}
          >
            <Text className="text-white text-center font-bold font-primary text-base">
              {logic.isVerifying ? 'Verifying...' : 'Verify Code'}
            </Text>
          </Pressable>
        </VStack>
      </VStack>

      {/* Resend Section */}
      <VStack className="items-center mt-8" space="sm">
        <Text className="text-center text-typography-600 font-body text-sm">
          Didn't receive the code?
        </Text>

        <Pressable onPress={logic.resendCode} disabled={logic.isResending} className="py-2 px-4">
          <Text className="text-primary-600 text-sm font-medium">
            {logic.isResending ? 'Sending...' : 'Resend Code'}
          </Text>
        </Pressable>

        <Link href="/auth/signin">
          <Text className="text-typography-500 text-sm">Back to Sign In</Text>
        </Link>
      </VStack>
    </VStack>
  );
};
