import React, { useState, useEffect } from 'react';
import { Toast, ToastTitle, useToast } from '@/components/ui/toast';
import { HStack } from '@/components/ui/hstack';
import { VStack } from '@/components/ui/vstack';
import { Heading } from '@/components/ui/heading';
import { Text } from '@/components/ui/text';
import { LinkText } from '@/components/ui/link';
import Link from '@unitools/link';
import {
  FormControl,
  FormControlError,
  FormControlErrorIcon,
  FormControlErrorText,
  FormControlLabel,
  FormControlLabelText,
} from '@/components/ui/form-control';
import { Input, InputField } from '@/components/ui/input';
import { ArrowLeftIcon, Icon } from '@/components/ui/icon';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Keyboard, Platform } from 'react-native';
import { useForm, Controller } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { AlertTriangle, Fingerprint } from 'lucide-react-native';
import { Pressable } from '@/components/ui/pressable';
import useRouter from '@unitools/router';
import { AuthLayout } from '../layout';
import { verifyEmailCode, requestEmailCode } from '@/api/authApi';
import { useLocalSearchParams } from 'expo-router';
import { useAuth } from '@/api/authContext';
import { Checkbox, CheckboxIcon, CheckboxIndicator, CheckboxLabel } from '@/components/ui/checkbox';
import { Check } from 'lucide-react-native';

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
  const [enableBiometric, setEnableBiometric] = useState(false);
  const { checkAuthStatus, biometricSupport, enableBiometrics } = useAuth();

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
    if (contactValue) {
      verifyCodeForm.setValue('contact', contactValue);
    }
    if (contactType) {
      verifyCodeForm.setValue('contactType', contactType as 'email' | 'phone');
    }
  }, [contact, contactType, email]);

  // Handle verify code submit
  const onVerifyCode = async (data: VerifyCodeSchemaType) => {
    try {
      setIsVerifying(true);

      // Call the API to verify the code
      // Adapt this to handle both email and phone verification
      const params =
        data.contactType === 'email'
          ? { email: data.contact, code: data.code }
          : { phone: data.contact, code: data.code };

      const response = await verifyEmailCode(params);

      // Successfully verified - now explicitly update auth state
      await checkAuthStatus();

      // If the user wants to enable biometric authentication
      if (enableBiometric && biometricSupport.isAvailable) {
        try {
          // Using contact as the identifier for biometrics
          const result = await enableBiometrics(data.contact);
          if (result) {
            toast.show({
              placement: 'bottom right',
              render: ({ id }) => {
                return (
                  <Toast nativeID={id} variant="solid" action="success">
                    <ToastTitle>Biometric authentication enabled!</ToastTitle>
                  </Toast>
                );
              },
            });
          } else {
            toast.show({
              placement: 'bottom right',
              render: ({ id }) => {
                return (
                  <Toast nativeID={id} variant="solid" action="warning">
                    <ToastTitle>Could not enable biometric authentication.</ToastTitle>
                  </Toast>
                );
              },
            });
          }
        } catch (biometricError) {
          console.error('Error enabling biometrics:', biometricError);
          // Continue despite biometric error
        }
      }

      toast.show({
        placement: 'bottom right',
        render: ({ id }) => {
          return (
            <Toast nativeID={id} variant="solid" action="success">
              <ToastTitle>Verification successful!</ToastTitle>
            </Toast>
          );
        },
      });

      // Navigate to dashboard after verification
      router.replace('/dashboard');
    } catch (error) {
      toast.show({
        placement: 'bottom right',
        render: ({ id }) => {
          return (
            <Toast nativeID={id} variant="solid" action="error">
              <ToastTitle>Invalid verification code. Please try again.</ToastTitle>
            </Toast>
          );
        },
      });
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
        currentContactType === 'email'
          ? { email: currentContact }
          : { phone: currentContact };

      await requestEmailCode(params);

      toast.show({
        placement: 'bottom right',
        render: ({ id }) => {
          return (
            <Toast nativeID={id} variant="solid" action="success">
              <ToastTitle>
                New verification code sent to your {currentContactType}!
              </ToastTitle>
            </Toast>
          );
        },
      });

      // Reset the code field
      verifyCodeForm.setValue('code', '');
    } catch (error) {
      console.error('Error resending verification code:', error);
      toast.show({
        placement: 'bottom right',
        render: ({ id }) => {
          return (
            <Toast nativeID={id} variant="solid" action="error">
              <ToastTitle>
                Failed to send new verification code. Please try again.
              </ToastTitle>
            </Toast>
          );
        },
      });
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

          {biometricSupport.isAvailable && (
            <Checkbox
              value="enable-biometric"
              isChecked={enableBiometric}
              onChange={setEnableBiometric}
              aria-label="Enable biometric login"
            >
              <CheckboxIndicator className="mr-2">
                <CheckboxIcon as={Check} />
              </CheckboxIndicator>
              <CheckboxLabel>
                Enable {Platform.OS === 'ios' ? 'Face ID / Touch ID' : 'biometric'} login
              </CheckboxLabel>
            </Checkbox>
          )}

          <VStack className="w-full my-7" space="lg">
            <Button
              className="w-full"
              onPress={verifyCodeForm.handleSubmit(onVerifyCode)}
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
