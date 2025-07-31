import { zodResolver } from '@hookform/resolvers/zod';
import Link from '@unitools/link';
import useRouter from '@unitools/router';
import { AlertTriangle } from 'lucide-react-native';
import React, { useState, useEffect } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { Keyboard, Platform } from 'react-native';
import { z } from 'zod';

import { AuthLayout } from '../layout';

import { requestEmailCode } from '@/api/authApi';
import { useAuth } from '@/api/authContext';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Divider } from '@/components/ui/divider';
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
  const {} = useAuth();
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
    <VStack className="max-w-[440px] w-full" space="md">
      <VStack className="md:items-center" space="md">
        <Pressable
          onPress={() => {
            router.back();
          }}
        >
          <Icon as={ArrowLeftIcon} className="md:hidden text-background-800" size="xl" />
        </Pressable>
        <VStack>
          <Heading className="md:text-center" size="3xl">
            Log in
          </Heading>
          <Text>Enter your email to receive a login code</Text>
        </VStack>
      </VStack>
      <VStack className="w-full">
        <VStack space="xl" className="w-full">
          <FormControl isInvalid={!!requestCodeForm.formState.errors?.email} className="w-full">
            <FormControlLabel>
              <FormControlLabelText>Email</FormControlLabelText>
            </FormControlLabel>
            <Controller
              defaultValue=""
              name="email"
              control={requestCodeForm.control}
              render={({ field: { onChange, onBlur, value } }) => (
                <Input>
                  <InputField
                    type="email"
                    testID="email-input"
                    placeholder="Enter email"
                    value={value}
                    onChangeText={onChange}
                    onBlur={onBlur}
                    onSubmitEditing={handleRequestKeyPress}
                    returnKeyType="done"
                  />
                </Input>
              )}
            />
            <FormControlError>
              <FormControlErrorIcon as={AlertTriangle} />
              <FormControlErrorText>
                {requestCodeForm.formState.errors?.email?.message}
              </FormControlErrorText>
            </FormControlError>
          </FormControl>
          <VStack className="w-full my-7" space="lg">
            <Button
              className="w-full"
              onPress={requestCodeForm.handleSubmit(onRequestCode)}
              isDisabled={isRequesting}
            >
              <ButtonText className="font-medium">
                {isRequesting ? 'Sending Code...' : 'Request Login Code'}
              </ButtonText>
            </Button>
          </VStack>
        </VStack>
        <HStack className="self-center" space="sm">
          <Text size="md">Don't have an account?</Text>
          <Link href="/auth/user-type-selection">
            <LinkText
              className="font-medium text-primary-700 group-hover/link:text-primary-600 group-hover/pressed:text-primary-700"
              size="md"
            >
              Sign up
            </LinkText>
          </Link>
        </HStack>
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
