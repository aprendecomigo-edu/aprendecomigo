/**
 * Pure UI Component for Sign-In Form
 *
 * This component contains ONLY UI rendering logic and event handlers.
 * All business logic is handled externally and passed via props.
 * This separation makes the component highly testable and reusable.
 */

import { zodResolver } from '@hookform/resolvers/zod';
import { Link } from 'expo-router';
import { AlertTriangle } from 'lucide-react-native';
import React from 'react';
import { useForm, Controller } from 'react-hook-form';
import { Keyboard } from 'react-native';
import { z } from 'zod';

import {
  FormControl,
  FormControlError,
  FormControlErrorIcon,
  FormControlErrorText,
  FormControlLabel,
  FormControlLabelText,
} from '@/components/ui/form-control';
import { Heading } from '@/components/ui/heading';
import { ArrowLeftIcon, Icon } from '@/components/ui/icon';
import { Input, InputField } from '@/components/ui/input';
import { Pressable } from '@/components/ui/pressable';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

// Form validation schema
const signInSchema = z.object({
  email: z.string().min(1, 'Email is required').email(),
});

type SignInFormData = z.infer<typeof signInSchema>;

export interface SignInFormProps {
  isRequesting: boolean;
  error: Error | null;
  onSubmitEmail: (email: string) => void | Promise<void>;
  onKeyPress: () => void;
  onBackPress?: () => void;
}

export const SignInForm: React.FC<SignInFormProps> = ({
  isRequesting,
  error,
  onSubmitEmail,
  onKeyPress,
  onBackPress,
}) => {
  // Form handling
  const form = useForm<SignInFormData>({
    resolver: zodResolver(signInSchema),
    defaultValues: {
      email: '',
    },
  });

  // Handle form submission
  const onSubmit = async (data: SignInFormData) => {
    await onSubmitEmail(data.email);
  };

  // Handle keyboard submission
  const handleKeyPress = () => {
    Keyboard.dismiss();
    onKeyPress();
    form.handleSubmit(onSubmit)();
  };

  return (
    <VStack className="w-full" space="lg">
      {/* Header with modern typography and gradient text */}
      <VStack className="items-center" space="md">
        {onBackPress && (
          <Pressable
            onPress={onBackPress}
            className="md:hidden self-start mb-4"
            testID="back-button"
          >
            <Icon as={ArrowLeftIcon} className="text-typography-700" size="xl" />
          </Pressable>
        )}

        {/* Brand logo */}
        <VStack className="items-center mb-2">
          <Text
            testID="brand-logo"
            className="text-center text-gradient-primary font-brand text-md"
          >
            aprendecomigo
          </Text>
        </VStack>

        <VStack className="items-center" space="sm">
          <Heading testID="login-heading" className="text-center font-primary" size="3xl">
            <Text testID="login-title" className="color-primary font-primary">
              Login
            </Text>
          </Heading>
          <Text className="text-center text-typography-600 font-body text-base leading-relaxed"></Text>
        </VStack>
      </VStack>

      {/* Form with glass inputs */}
      <VStack className="w-full" space="xl">
        <FormControl isInvalid={!!form.formState.errors?.email} className="w-full">
          <FormControlLabel className="mb-2">
            <FormControlLabelText
              testID="email-label"
              className="font-primary font-medium text-typography-700"
            >
              Email
            </FormControlLabelText>
          </FormControlLabel>
          <Controller
            name="email"
            control={form.control}
            render={({ field: { onChange, onBlur, value } }) => (
              <VStack className="glass-light rounded-xl p-4">
                <Input className="border-0">
                  <InputField
                    type="email"
                    testID="email-input"
                    placeholder="your_email@example.com"
                    value={value}
                    onChangeText={onChange}
                    onBlur={onBlur}
                    onSubmitEditing={handleKeyPress}
                    returnKeyType="done"
                    className="bg-transparent font-body text-base"
                    placeholderTextColor="#94A3B8"
                    keyboardType="email-address"
                    autoCapitalize="none"
                    autoComplete="email"
                  />
                </Input>
              </VStack>
            )}
          />
          <FormControlError>
            <FormControlErrorIcon as={AlertTriangle} />
            <FormControlErrorText className="font-body">
              {form.formState.errors?.email?.message}
            </FormControlErrorText>
          </FormControlError>
        </FormControl>

        {/* Actions with generous spacing */}
        <VStack className="w-full mt-8" space="lg">
          <Pressable
            className="w-full bg-gradient-primary py-4 rounded-xl active:scale-98 transition-all shadow-lg"
            onPress={form.handleSubmit(onSubmit)}
            disabled={isRequesting}
          >
            <Text
              testID="submit-button-text"
              className="text-white text-center font-bold font-primary text-base"
            >
              {isRequesting ? 'Sending Code...' : 'Send Login Code'}
            </Text>
          </Pressable>
        </VStack>
      </VStack>

      {/* Footer with clean typography */}
      <VStack className="items-center mt-8" space="sm">
        <Text testID="signup-prompt" className="text-center text-typography-600 font-body text-sm">
          Don't have an account?
        </Text>
        <Link href="/auth/signup">
          <Text
            testID="signup-link"
            className="text-white text-sm font-bold py-1 px-1 rounded-xl font-primary bg-black"
          >
            Create your account
          </Text>
        </Link>
      </VStack>
    </VStack>
  );
};
