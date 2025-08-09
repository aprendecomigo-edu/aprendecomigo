import { zodResolver } from '@hookform/resolvers/zod';
import Link from '@unitools/link';
import useRouter from '@unitools/router';
import { AlertTriangle } from 'lucide-react-native';
import React, { useState } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { Keyboard } from 'react-native';
import { z } from 'zod';

import { AuthLayout } from './AuthLayout';

import { requestEmailCode } from '@/api/authApi';
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
import { useToast } from '@/components/ui/toast';
import { VStack } from '@/components/ui/vstack';

// Define the form schema
const requestCodeSchema = z.object({
  email: z.string().min(1, 'Email is required').email(),
});

type RequestCodeSchemaType = z.infer<typeof requestCodeSchema>;

const LoginForm = () => {
  const toast = useToast();
  const router = useRouter();
  const [isRequesting, setIsRequesting] = useState(false);

  // Request code form
  const requestCodeForm = useForm<RequestCodeSchemaType>({
    resolver: zodResolver(requestCodeSchema),
  });

  // Handle request code submit
  const onRequestCode = async (data: RequestCodeSchemaType) => {
    try {
      setIsRequesting(true);
      await requestEmailCode({ email: data.email });

      toast.showToast('success', 'Verification code sent to your email!');

      // Navigate to verify code screen with email as parameter
      router.push(`/auth/verify-code?email=${encodeURIComponent(data.email)}`);
    } catch (error) {
      toast.showToast('error', 'Failed to send verification code. Please try again.');
    } finally {
      setIsRequesting(false);
    }
  };

  const handleRequestKeyPress = () => {
    Keyboard.dismiss();
    requestCodeForm.handleSubmit(onRequestCode)();
  };

  return (
    <VStack className="w-full" space="lg">
      {/* Header with modern typography and gradient text */}
      <VStack className="items-center" space="md">
        <Pressable
          onPress={() => {
            router.back();
          }}
          className="md:hidden self-start mb-4"
        >
          <Icon as={ArrowLeftIcon} className="text-typography-700" size="xl" />
        </Pressable>

        {/* Brand logo */}
        <VStack className="items-center mb-2">
          <Text className="text-center text-gradient-primary font-brand text-md">
            aprendecomigo
          </Text>
        </VStack>

        <VStack className="items-center" space="sm">
          <Heading className="text-center font-primary" size="3xl">
            <Text className="color-primary font-primary">Login</Text>
          </Heading>
          <Text className="text-center text-typography-600 font-body text-base leading-relaxed"></Text>
        </VStack>
      </VStack>

      {/* Form with glass inputs */}
      <VStack className="w-full" space="xl">
        <FormControl isInvalid={!!requestCodeForm.formState.errors?.email} className="w-full">
          <FormControlLabel className="mb-2">
            <FormControlLabelText className="font-primary font-medium text-typography-700">
              Email
            </FormControlLabelText>
          </FormControlLabel>
          <Controller
            defaultValue=""
            name="email"
            control={requestCodeForm.control}
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
                    onSubmitEditing={handleRequestKeyPress}
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
              {requestCodeForm.formState.errors?.email?.message}
            </FormControlErrorText>
          </FormControlError>
        </FormControl>

        {/* Actions with generous spacing */}
        <VStack className="w-full mt-8" space="lg">
          <Pressable
            className="w-full bg-gradient-primary py-4 rounded-xl active:scale-98 transition-all shadow-lg"
            onPress={requestCodeForm.handleSubmit(onRequestCode)}
            disabled={isRequesting}
          >
            <Text className="text-white text-center font-bold font-primary text-base">
              {isRequesting ? 'Sending Code...' : 'Send Login Code'}
            </Text>
          </Pressable>
        </VStack>
      </VStack>

      {/* Footer with clean typography */}
      <VStack className="items-center mt-8" space="sm">
        <Text className="text-center text-typography-600 font-body text-sm">
          Don't have an account?
        </Text>
        <Link href="/auth/signup">
          <Text className="text-white text-sm font-bold py-1 px-1 rounded-xl font-primary bg-black">
            Create your account
          </Text>
        </Link>
      </VStack>
    </VStack>
  );
};

export const SignIn = () => {
  return (
    <AuthLayout>
      <LoginForm />
    </AuthLayout>
  );
};
