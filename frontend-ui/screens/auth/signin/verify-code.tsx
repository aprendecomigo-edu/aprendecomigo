import { zodResolver } from '@hookform/resolvers/zod';
import Link from '@unitools/link';
import useRouter from '@unitools/router';
import { useLocalSearchParams } from 'expo-router';
import { AlertTriangle, Check } from 'lucide-react-native';
import React, { useState, useEffect } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { Keyboard, Platform } from 'react-native';
import { z } from 'zod';

import { AuthLayout } from '../layout';

import { verifyEmailCode, requestEmailCode } from '@/api/authApi';
import { useAuth } from '@/api/authContext';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Checkbox, CheckboxIcon, CheckboxIndicator, CheckboxLabel } from '@/components/ui/checkbox';
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
const verifyCodeSchema = z.object({
  contact: z.string().min(1, 'Contact information is required'),
  contactType: z.enum(['email', 'phone']),
  code: z.string().min(1, 'Verification code is required'),
});

type VerifyCodeSchemaType = z.infer<typeof verifyCodeSchema>;

const VerifyCodeForm = () => {
  const toast = useToast();
  const router = useRouter();
  const { contact, contactType, email } = useLocalSearchParams<{
    contact: string;
    contactType: 'email' | 'phone';
    email: string;
  }>();
  const [isVerifying, setIsVerifying] = useState(false);
  const [isResending, setIsResending] = useState(false);
  const { checkAuthStatus } = useAuth();

  // Verify code form
  const verifyCodeForm = useForm<VerifyCodeSchemaType>({
    resolver: zodResolver(verifyCodeSchema),
    defaultValues: {
      contact: contact || email || '',
      contactType: (contactType as 'email' | 'phone') || 'email',
      code: '',
    },
  });

  // Update form when params change
  useEffect(() => {
    // Handle both 'contact' and 'email' parameters for backward compatibility
    const contactValue = contact || email || '';
    const contactTypeValue = contactType || 'email'; // Default to email

    console.log('URL params:', { contact, email, contactType });
    console.log('Using contact value:', contactValue);

    if (contactValue) {
      verifyCodeForm.setValue('contact', contactValue);
    }
    verifyCodeForm.setValue('contactType', contactTypeValue as 'email' | 'phone');

    // Force form validation
    verifyCodeForm.trigger();
  }, [contact, contactType, email, verifyCodeForm]);

  // Handle verify code submit
  const onVerifyCode = async (data: VerifyCodeSchemaType) => {
    try {
      setIsVerifying(true);
      console.log('Verifying code with data:', data);

      // Call the API to verify the code
      // Adapt this to handle both email and phone verification
      const params =
        data.contactType === 'email'
          ? { email: data.contact, code: data.code }
          : { phone: data.contact, code: data.code };

      console.log('Verification API params:', params);
      const response = await verifyEmailCode(params);
      console.log('Verification response:', response);

      // Successfully verified - now explicitly update auth state
      await checkAuthStatus();

      toast.showToast('success', 'Verification successful!');

      // Navigate to root after verification - auth context will handle redirect
      router.replace('/');
    } catch (error) {
      console.error('Verification error:', error);
      toast.showToast('error', 'Invalid verification code. Please try again.');
    } finally {
      setIsVerifying(false);
    }
  };

  // Handle resending verification code
  const handleResendCode = async () => {
    try {
      setIsResending(true);

      // Get current values from form
      const currentContact = verifyCodeForm.getValues('contact');
      const currentContactType = verifyCodeForm.getValues('contactType');

      // Call the API to request a new verification code
      const params =
        currentContactType === 'email' ? { email: currentContact } : { phone: currentContact };

      await requestEmailCode(params);

      toast.showToast('success', `New verification code sent to your ${currentContactType}!`);

      // Reset the code field
      verifyCodeForm.setValue('code', '');
    } catch (error) {
      console.error('Error resending verification code:', error);
      toast.showToast('error', 'Failed to send new verification code. Please try again.');
    } finally {
      setIsResending(false);
    }
  };

  const handleVerifyKeyPress = () => {
    Keyboard.dismiss();
    verifyCodeForm.handleSubmit(onVerifyCode)();
  };

  // Get the contact value to display
  const watchedContact = verifyCodeForm.watch('contact');
  const watchedContactType = verifyCodeForm.watch('contactType');

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
            Verify Code
          </Heading>
          <Text className="md:text-center">
            Enter the verification code sent to{' '}
            {watchedContact ? (
              <Text className="font-medium">{watchedContact}</Text>
            ) : (
              `your ${watchedContactType}`
            )}
          </Text>
        </VStack>
      </VStack>
      <VStack className="w-full">
        <VStack space="xl" className="w-full">
          <FormControl isInvalid={!!verifyCodeForm.formState.errors?.code} className="w-full">
            <FormControlLabel>
              <FormControlLabelText>Verification Code</FormControlLabelText>
            </FormControlLabel>
            <Controller
              name="code"
              control={verifyCodeForm.control}
              render={({ field: { onChange, onBlur, value } }) => (
                <Input>
                  <InputField
                    placeholder="Enter the verification code"
                    value={value}
                    onChangeText={onChange}
                    onBlur={onBlur}
                    onSubmitEditing={handleVerifyKeyPress}
                    returnKeyType="done"
                    keyboardType="number-pad"
                    maxLength={6}
                  />
                </Input>
              )}
            />
            <FormControlError>
              <FormControlErrorIcon as={AlertTriangle} />
              <FormControlErrorText>
                {verifyCodeForm.formState.errors?.code?.message}
              </FormControlErrorText>
            </FormControlError>
          </FormControl>

          <VStack className="w-full my-7" space="lg">
            <Button
              className="w-full"
              onPress={() => {
                console.log('Verify button clicked');
                console.log('Form values:', verifyCodeForm.getValues());
                console.log('Form errors:', verifyCodeForm.formState.errors);
                verifyCodeForm.handleSubmit(onVerifyCode)();
              }}
              isDisabled={isVerifying}
            >
              <ButtonText className="font-medium">
                {isVerifying ? 'Verifying...' : 'Verify Code'}
              </ButtonText>
            </Button>
            <Button
              variant="outline"
              action="secondary"
              className="w-full"
              onPress={handleResendCode}
              isDisabled={isResending}
              testID="resend-code-button"
            >
              <ButtonText className="font-medium">
                {isResending ? 'Sending...' : 'Try Again'}
              </ButtonText>
            </Button>
          </VStack>
        </VStack>
        <HStack className="self-center" space="sm">
          <Text size="md">Need help?</Text>
          <Link href="/auth/signin">
            <LinkText
              className="font-medium text-primary-700 group-hover/link:text-primary-600 group-hover/pressed:text-primary-700"
              size="md"
            >
              Contact Support
            </LinkText>
          </Link>
        </HStack>
      </VStack>
    </VStack>
  );
};

export const VerifyCode = () => {
  return (
    <AuthLayout>
      <VerifyCodeForm />
    </AuthLayout>
  );
};
