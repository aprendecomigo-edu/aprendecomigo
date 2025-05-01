import React, { useState, useEffect } from 'react';
import { Toast, ToastTitle, useToast } from '@/components/ui/toast';
import { VStack } from '@/components/ui/vstack';
import { Heading } from '@/components/ui/heading';
import { Text } from '@/components/ui/text';
import {
  FormControl,
  FormControlError,
  FormControlErrorIcon,
  FormControlErrorText,
  FormControlLabel,
  FormControlLabelText,
  FormControlHelper,
  FormControlHelperText,
} from '@/components/ui/form-control';
import { Input, InputField } from '@/components/ui/input';
import { ArrowLeftIcon, Icon } from '@/components/ui/icon';
import { Button, ButtonText } from '@/components/ui/button';
import { Keyboard, ScrollView } from 'react-native';
import { useForm, Controller } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { AlertTriangle } from 'lucide-react-native';
import { Pressable } from '@/components/ui/pressable';
import useRouter from '@unitools/router';
import { AuthLayout } from '../layout';
import { createUser, OnboardingData } from '@/api/authApi';
import { useAuth } from '@/api/authContext';
import { Box } from '@/components/ui/box';
import { Divider } from '@/components/ui/divider';
import { Radio, RadioGroup, RadioIcon, RadioIndicator, RadioLabel } from '@/components/ui/radio';

// Define the form schema
const onboardingSchema = z.object({
  // User information
  userName: z.string().min(1, 'Name is required').max(150, 'Name must be 150 characters or less'),
  userEmail: z
    .string()
    .email('Please enter a valid email')
    .min(1, 'Email is required')
    .max(150, 'Email must be 150 characters or less'),
  userPhone: z
    .string()
    .min(4, 'Phone number is required')
    .max(20, 'Phone number must be 20 characters or less')
    .regex(/^[+\d\s]+$/, 'Phone number can only contain digits, spaces, and + sign')
    .refine(val => /\d/.test(val), 'Phone number must contain at least one digit')
    .refine(val => !val.startsWith(' '), 'Phone number cannot start with a space')
    .refine(val => !/\s{2,}/.test(val), 'No consecutive spaces allowed')
    .refine(val => !/.*\+.*/.test(val.substring(1)), 'Plus sign (+) can only appear at the beginning'),

  // School information
  schoolName: z
    .string()
    .min(1, 'School name is required')
    .max(150, 'School name must be 150 characters or less'),
  schoolAddress: z.string().optional(),
  schoolWebsite: z
    .string()
    .url('Please enter a valid URL')
    .max(200, 'Website URL must be 200 characters or less')
    .optional()
    .or(z.literal('')),
  primaryContact: z.enum(['email', 'phone'], {
    required_error: 'Please select a primary contact method',
  }),
});

type OnboardingSchemaType = z.infer<typeof onboardingSchema>;

const OnboardingForm = () => {
  const toast = useToast();
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { checkAuthStatus, userProfile } = useAuth();

  const {
    control,
    handleSubmit,
    formState: { errors },
    setValue,
    watch,
  } = useForm<OnboardingSchemaType>({
    resolver: zodResolver(onboardingSchema),
    defaultValues: {
      userName: userProfile?.name || '',
      userEmail: userProfile?.email || '',
      userPhone: userProfile?.phone_number || '',
      schoolName: '',
      schoolAddress: '',
      schoolWebsite: '',
      primaryContact: 'email',
    },
  });

  // Watch primary contact selection
  const primaryContact = watch('primaryContact');

  // Update form with user profile data when available
  useEffect(() => {
    if (userProfile) {
      setValue('userName', userProfile.name || '');
      setValue('userEmail', userProfile.email || '');
      setValue('userPhone', userProfile.phone_number || '');
    }
  }, [userProfile, setValue]);

  const onSubmit = async (data: OnboardingSchemaType) => {
    try {
      setIsSubmitting(true);

      // Convert form data to API request format that matches the backend serializer
      const onboardingData = {
        name: data.userName,
        email: data.userEmail,
        phone_number: data.userPhone,
        primary_contact: data.primaryContact,
        school: {
          name: data.schoolName,
          address: data.schoolAddress || undefined,
          website: data.schoolWebsite || undefined,
        },
      };

      // Call the API to create user
      await createUser(onboardingData);

      // Update auth state
      await checkAuthStatus();

      toast.show({
        placement: 'bottom right',
        render: ({ id }) => {
          return (
            <Toast nativeID={id} variant="solid" action="success">
              <ToastTitle>
                Registration successful! Please verify your{' '}
                {data.primaryContact === 'email' ? 'email' : 'phone'}.
              </ToastTitle>
            </Toast>
          );
        },
      });

      // Navigate to verification screen - fix type issue by using proper navigation
      router.replace(
        `/auth/verify-code?contact=${encodeURIComponent(
          data.primaryContact === 'email' ? data.userEmail : data.userPhone
        )}&contactType=${data.primaryContact}`
      );
    } catch (error) {
      console.error('Error during registration:', error);
      toast.show({
        placement: 'bottom right',
        render: ({ id }) => {
          return (
            <Toast nativeID={id} variant="solid" action="error">
              <ToastTitle>Failed to complete registration. Please try again.</ToastTitle>
            </Toast>
          );
        },
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleKeyboardDismiss = () => {
    Keyboard.dismiss();
  };

  return (
    <VStack className="w-full md:max-w-3xl mx-auto" space="md">
      <VStack className="md:items-center" space="md">
        <Pressable
          onPress={() => {
            router.back();
          }}
        >
          <Icon as={ArrowLeftIcon} className="md:hidden text-background-800" size="xl" />
        </Pressable>
        <VStack>
          <Heading className="md:text-center text-3xl font-bold" size="3xl">
            Create Your Account
          </Heading>
          <Text className="md:text-center text-base opacity-80 mt-1">
            Register your school with Aprende Comigo
          </Text>
        </VStack>
      </VStack>

      <ScrollView showsVerticalScrollIndicator={false}>
        <VStack className="w-full pb-10" space="xl">
          {/* Personal Information Section */}
          <VStack space="md" className="mt-4">
            <Heading size="lg" className="mb-1">
              Personal Information
            </Heading>

            <VStack space="md" className="md:flex-row md:space-x-4">
              <FormControl isInvalid={!!errors.userName} className="md:flex-1">
                <FormControlLabel>
                  <FormControlLabelText>Full Name</FormControlLabelText>
                </FormControlLabel>
                <Controller
                  name="userName"
                  control={control}
                  render={({ field: { onChange, onBlur, value } }) => (
                    <Input>
                      <InputField
                        placeholder="Enter your full name"
                        value={value}
                        onChangeText={onChange}
                        onBlur={onBlur}
                        returnKeyType="next"
                      />
                    </Input>
                  )}
                />
                <FormControlError>
                  <FormControlErrorIcon as={AlertTriangle} />
                  <FormControlErrorText>{errors.userName?.message}</FormControlErrorText>
                </FormControlError>
              </FormControl>
            </VStack>

            <VStack space="md" className="md:flex-row md:space-x-4">
              <FormControl isInvalid={!!errors.userEmail} className="md:flex-1">
                <FormControlLabel>
                  <FormControlLabelText>Email</FormControlLabelText>
                </FormControlLabel>
                <Controller
                  name="userEmail"
                  control={control}
                  render={({ field: { onChange, onBlur, value } }) => (
                    <Input>
                      <InputField
                        placeholder="Enter your email"
                        value={value}
                        onChangeText={onChange}
                        onBlur={onBlur}
                        keyboardType="email-address"
                        returnKeyType="next"
                      />
                    </Input>
                  )}
                />
                <FormControlError>
                  <FormControlErrorIcon as={AlertTriangle} />
                  <FormControlErrorText>{errors.userEmail?.message}</FormControlErrorText>
                </FormControlError>
              </FormControl>

              <FormControl isInvalid={!!errors.userPhone} className="md:flex-1">
                <FormControlLabel>
                  <FormControlLabelText>Phone Number</FormControlLabelText>
                </FormControlLabel>
                <Controller
                  name="userPhone"
                  control={control}
                  render={({ field: { onChange, onBlur, value } }) => (
                    <Input>
                      <InputField
                        placeholder="Enter your phone number"
                        value={value}
                        onChangeText={(text) => {
                          // Allow only digits, spaces, and + sign
                          const sanitizedValue = text.replace(/[^\d\s+]/g, '');
                          onChange(sanitizedValue);
                        }}
                        onBlur={onBlur}
                        keyboardType="phone-pad"
                        returnKeyType="next"
                      />
                    </Input>
                  )}
                />
                <FormControlError>
                  <FormControlErrorIcon as={AlertTriangle} />
                  <FormControlErrorText>{errors.userPhone?.message}</FormControlErrorText>
                </FormControlError>
              </FormControl>
            </VStack>

            <FormControl isInvalid={!!errors.primaryContact}>
              <FormControlLabel>
                <FormControlLabelText>Primary Contact Method</FormControlLabelText>
              </FormControlLabel>
              <Controller
                name="primaryContact"
                control={control}
                render={({ field: { onChange, value } }) => (
                  <RadioGroup value={value} onChange={onChange}>
                    <VStack space="sm" className="md:flex-row md:space-x-6">
                      <Radio
                        value="email"
                        size="lg"
                        className="border-2 border-transparent rounded-full active:border-primary-600 p-1"
                      >
                        <RadioIndicator className="bg-transparent border-2 border-gray-400 _checked:border-primary-600 _checked:bg-primary-200">
                          <RadioIcon className="bg-primary-600" />
                        </RadioIndicator>
                        <RadioLabel>Email</RadioLabel>
                      </Radio>
                      <Radio
                        value="phone"
                        size="lg"
                        className="border-2 border-transparent rounded-full active:border-primary-600 p-1"
                      >
                        <RadioIndicator className="bg-transparent border-2 border-gray-400 _checked:border-primary-600 _checked:bg-primary-200">
                          <RadioIcon className="bg-primary-600" />
                        </RadioIndicator>
                        <RadioLabel>Phone</RadioLabel>
                      </Radio>
                    </VStack>
                  </RadioGroup>
                )}
              />
              <FormControlError>
                <FormControlErrorIcon as={AlertTriangle} />
                <FormControlErrorText>{errors.primaryContact?.message}</FormControlErrorText>
              </FormControlError>
              <FormControlHelper>
                <FormControlHelperText>
                  A verification code will be sent to your primary contact method
                </FormControlHelperText>
              </FormControlHelper>
            </FormControl>
          </VStack>

          <Divider className="my-2" />

          {/* School Information Section */}
          <VStack space="md" className="mt-2">
            <Heading size="lg" className="mb-1">
              School Information
            </Heading>
            <Text className="text-sm opacity-70 mb-2">
              Only school name is required. You can add more details later.
            </Text>

            <FormControl isInvalid={!!errors.schoolName}>
              <FormControlLabel>
                <FormControlLabelText>School Name</FormControlLabelText>
              </FormControlLabel>
              <Controller
                name="schoolName"
                control={control}
                render={({ field: { onChange, onBlur, value } }) => (
                  <Input>
                    <InputField
                      placeholder="Enter your school name"
                      value={value}
                      onChangeText={onChange}
                      onBlur={onBlur}
                      returnKeyType="next"
                    />
                  </Input>
                )}
              />
              <FormControlError>
                <FormControlErrorIcon as={AlertTriangle} />
                <FormControlErrorText>{errors.schoolName?.message}</FormControlErrorText>
              </FormControlError>
            </FormControl>

            <VStack space="md" className="md:flex-row md:space-x-4">
              <FormControl isInvalid={!!errors.schoolAddress} className="md:flex-1">
                <FormControlLabel>
                  <FormControlLabelText>School Address (Optional)</FormControlLabelText>
                </FormControlLabel>
                <Controller
                  name="schoolAddress"
                  control={control}
                  render={({ field: { onChange, onBlur, value } }) => (
                    <Input>
                      <InputField
                        placeholder="Enter school address"
                        value={value}
                        onChangeText={onChange}
                        onBlur={onBlur}
                        returnKeyType="next"
                      />
                    </Input>
                  )}
                />
                <FormControlError>
                  <FormControlErrorIcon as={AlertTriangle} />
                  <FormControlErrorText>{errors.schoolAddress?.message}</FormControlErrorText>
                </FormControlError>
              </FormControl>

              <FormControl isInvalid={!!errors.schoolWebsite} className="md:flex-1">
                <FormControlLabel>
                  <FormControlLabelText>Website (Optional)</FormControlLabelText>
                </FormControlLabel>
                <Controller
                  name="schoolWebsite"
                  control={control}
                  render={({ field: { onChange, onBlur, value } }) => (
                    <Input>
                      <InputField
                        placeholder="Enter school website URL"
                        value={value}
                        onChangeText={onChange}
                        onBlur={onBlur}
                        keyboardType="url"
                        returnKeyType="next"
                        onSubmitEditing={handleKeyboardDismiss}
                      />
                    </Input>
                  )}
                />
                <FormControlError>
                  <FormControlErrorIcon as={AlertTriangle} />
                  <FormControlErrorText>{errors.schoolWebsite?.message}</FormControlErrorText>
                </FormControlError>
              </FormControl>
            </VStack>
          </VStack>

          <Box className="w-full mt-6">
            <Button
              className="w-full py-3"
              onPress={handleSubmit(onSubmit)}
              isDisabled={isSubmitting}
            >
              <ButtonText>{isSubmitting ? 'Submitting...' : 'Create Account'}</ButtonText>
            </Button>
          </Box>
        </VStack>
      </ScrollView>
    </VStack>
  );
};

export const SignUp = () => {
  return (
    <AuthLayout>
      <OnboardingForm />
    </AuthLayout>
  );
};
