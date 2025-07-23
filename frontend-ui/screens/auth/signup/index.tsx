import { zodResolver } from '@hookform/resolvers/zod';
import useRouter from '@unitools/router';
import { useLocalSearchParams } from 'expo-router';
import { AlertTriangle, GraduationCap, School } from 'lucide-react-native';
import React, { useState, useEffect } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { Keyboard, ScrollView } from 'react-native';
import { z } from 'zod';

import { AuthLayout } from '../layout';

import { createUser } from '@/api/authApi';
import { useAuth } from '@/api/authContext';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Divider } from '@/components/ui/divider';
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
import { Heading } from '@/components/ui/heading';
import { ArrowLeftIcon, Icon } from '@/components/ui/icon';
import { Input, InputField } from '@/components/ui/input';
import { Pressable } from '@/components/ui/pressable';
import { Radio, RadioGroup, RadioIcon, RadioIndicator, RadioLabel } from '@/components/ui/radio';
import { Text } from '@/components/ui/text';
import { useToast } from '@/components/ui/toast';
import { VStack } from '@/components/ui/vstack';
import { HStack } from '@/components/ui/hstack';

// Define the form schema based on user type
const createOnboardingSchema = (userType: string) => z.object({
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
    .refine(
      val => !/.*\+.*/.test(val.substring(1)),
      'Plus sign (+) can only appear at the beginning'
    ),

  // School information - conditional based on user type
  schoolName: userType === 'school' 
    ? z.string()
        .min(1, 'School name is required')
        .max(150, 'School name must be 150 characters or less')
    : z.string().optional(),
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

type OnboardingSchemaType = z.infer<ReturnType<typeof createOnboardingSchema>>;

const OnboardingForm = () => {
  const toast = useToast();
  const router = useRouter();
  const { type } = useLocalSearchParams<{ type: string }>();
  const userType = type || 'tutor'; // Default to tutor if no type specified
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { checkAuthStatus, userProfile } = useAuth();

  // Generate auto school name for tutors
  const generateSchoolName = (userName: string) => {
    if (!userName) return '';
    return `${userName}'s Tutoring Practice`;
  };

  const {
    control,
    handleSubmit,
    formState: { errors },
    setValue,
    watch,
  } = useForm<OnboardingSchemaType>({
    resolver: zodResolver(createOnboardingSchema(userType)),
    defaultValues: {
      userName: userProfile?.name || '',
      userEmail: userProfile?.email || '',
      userPhone: userProfile?.phone_number || '',
      schoolName: userType === 'tutor' ? generateSchoolName(userProfile?.name || '') : '',
      schoolAddress: '',
      schoolWebsite: '',
      primaryContact: 'email',
    },
  });

  // Watch form values for dynamic UI updates
  const primaryContact = watch('primaryContact');
  const userName = watch('userName');

  // Update form with user profile data when available
  useEffect(() => {
    if (userProfile) {
      setValue('userName', userProfile.name || '');
      setValue('userEmail', userProfile.email || '');
      setValue('userPhone', userProfile.phone_number || '');
      
      // Auto-generate school name for tutors
      if (userType === 'tutor' && userProfile.name) {
        setValue('schoolName', generateSchoolName(userProfile.name));
      }
    }
  }, [userProfile, setValue, userType]);

  // Update school name when tutor changes their name
  useEffect(() => {
    if (userType === 'tutor' && userName) {
      setValue('schoolName', generateSchoolName(userName));
    }
  }, [userName, userType, setValue]);

  const onSubmit = async (data: OnboardingSchemaType) => {
    try {
      setIsSubmitting(true);

      // Convert form data to API request format that matches the backend serializer
      const schoolName = userType === 'tutor' 
        ? generateSchoolName(data.userName)
        : data.schoolName || 'Untitled School';

      const onboardingData = {
        name: data.userName,
        email: data.userEmail,
        phone_number: data.userPhone,
        primary_contact: data.primaryContact,
        school: {
          name: schoolName,
          address: data.schoolAddress || undefined,
          website: data.schoolWebsite || undefined,
        },
      };

      // Call the API to create user
      await createUser(onboardingData);

      // Update auth state
      await checkAuthStatus();

      toast.showToast(
        'success',
        `Registration successful! Please verify your ${
          data.primaryContact === 'email' ? 'email' : 'phone'
        }.`
      );

      // Navigate to verification screen - fix type issue by using proper navigation
      router.replace(
        `/auth/verify-code?contact=${encodeURIComponent(
          data.primaryContact === 'email' ? data.userEmail : data.userPhone
        )}&contactType=${data.primaryContact}`
      );
    } catch (error) {
      console.error('Error during registration:', error);
      toast.showToast('error', 'Failed to complete registration. Please try again.');
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
        
        {/* User Type Indicator */}
        <HStack space="md" className="items-center justify-center mb-2">
          <Box className={`w-12 h-12 rounded-full items-center justify-center ${
            userType === 'tutor' ? 'bg-blue-100' : 'bg-green-100'
          }`}>
            <Icon 
              as={userType === 'tutor' ? GraduationCap : School} 
              className={userType === 'tutor' ? 'text-blue-600' : 'text-green-600'} 
              size="lg" 
            />
          </Box>
          <VStack>
            <Text className="text-sm text-gray-500 uppercase tracking-wide font-medium">
              {userType === 'tutor' ? 'Individual Tutor' : 'School/Institution'}
            </Text>
          </VStack>
        </HStack>

        <VStack>
          <Heading className="md:text-center text-3xl font-bold" size="3xl">
            {userType === 'tutor' ? 'Set Up Your Tutoring Practice' : 'Register Your School'}
          </Heading>
          <Text className="md:text-center text-base opacity-80 mt-1">
            {userType === 'tutor' 
              ? 'Create your professional tutoring account with Aprende Comigo'
              : 'Register your school or institution with Aprende Comigo'
            }
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

              <FormControl isInvalid={!!errors.userEmail} className="md:flex-1">
                <FormControlLabel>
                  <FormControlLabelText>Email Address</FormControlLabelText>
                </FormControlLabel>
                <Controller
                  name="userEmail"
                  control={control}
                  render={({ field: { onChange, onBlur, value } }) => (
                    <Input>
                      <InputField
                        placeholder="Enter your email address"
                        value={value}
                        onChangeText={onChange}
                        onBlur={onBlur}
                        keyboardType="email-address"
                        returnKeyType="next"
                        autoCapitalize="none"
                      />
                    </Input>
                  )}
                />
                <FormControlError>
                  <FormControlErrorIcon as={AlertTriangle} />
                  <FormControlErrorText>{errors.userEmail?.message}</FormControlErrorText>
                </FormControlError>
              </FormControl>
            </VStack>

            <FormControl isInvalid={!!errors.userPhone}>
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
                      onChangeText={text => {
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
                  A verification code will be sent to your{' '}
                  {primaryContact === 'email' ? 'email address' : 'phone number'}
                </FormControlHelperText>
              </FormControlHelper>
            </FormControl>
          </VStack>

          <Divider className="my-2" />

          {/* School Information Section */}
          <VStack space="md" className="mt-2">
            <Heading size="lg" className="mb-1">
              {userType === 'tutor' ? 'Practice Information' : 'School Information'}
            </Heading>
            <Text className="text-sm opacity-70 mb-2">
              {userType === 'tutor' 
                ? 'Your practice name will be auto-generated from your name. You can customize it later.'
                : 'Only school name is required. You can add more details later.'
              }
            </Text>

            <FormControl isInvalid={!!errors.schoolName}>
              <FormControlLabel>
                <FormControlLabelText>
                  {userType === 'tutor' ? 'Practice Name' : 'School Name'}
                </FormControlLabelText>
              </FormControlLabel>
              <Controller
                name="schoolName"
                control={control}
                render={({ field: { onChange, onBlur, value } }) => (
                  <Input>
                    <InputField
                      placeholder={userType === 'tutor' 
                        ? "Your practice name (auto-generated)"
                        : "Enter your school name"
                      }
                      value={value}
                      onChangeText={onChange}
                      onBlur={onBlur}
                      returnKeyType="next"
                      editable={userType === 'school'}
                      className={userType === 'tutor' ? 'bg-gray-50 text-gray-600' : ''}
                    />
                  </Input>
                )}
              />
              <FormControlError>
                <FormControlErrorIcon as={AlertTriangle} />
                <FormControlErrorText>{errors.schoolName?.message}</FormControlErrorText>
              </FormControlError>
              {userType === 'tutor' && (
                <FormControlHelper>
                  <FormControlHelperText>
                    This will be automatically generated from your name. You can change it later in settings.
                  </FormControlHelperText>
                </FormControlHelper>
              )}
            </FormControl>

            {userType === 'school' && (
              <>
                <FormControl isInvalid={!!errors.schoolAddress}>
                  <FormControlLabel>
                    <FormControlLabelText>School Address (Optional)</FormControlLabelText>
                  </FormControlLabel>
                  <Controller
                    name="schoolAddress"
                    control={control}
                    render={({ field: { onChange, onBlur, value } }) => (
                      <Input>
                        <InputField
                          placeholder="Enter your school address"
                          value={value}
                          onChangeText={onChange}
                          onBlur={onBlur}
                          returnKeyType="next"
                          multiline
                          numberOfLines={2}
                        />
                      </Input>
                    )}
                  />
                  <FormControlError>
                    <FormControlErrorIcon as={AlertTriangle} />
                    <FormControlErrorText>{errors.schoolAddress?.message}</FormControlErrorText>
                  </FormControlError>
                </FormControl>

                <FormControl isInvalid={!!errors.schoolWebsite}>
                  <FormControlLabel>
                    <FormControlLabelText>School Website (Optional)</FormControlLabelText>
                  </FormControlLabel>
                  <Controller
                    name="schoolWebsite"
                    control={control}
                    render={({ field: { onChange, onBlur, value } }) => (
                      <Input>
                        <InputField
                          placeholder="https://example.com"
                          value={value}
                          onChangeText={onChange}
                          onBlur={onBlur}
                          keyboardType="url"
                          returnKeyType="done"
                          autoCapitalize="none"
                        />
                      </Input>
                    )}
                  />
                  <FormControlError>
                    <FormControlErrorIcon as={AlertTriangle} />
                    <FormControlErrorText>{errors.schoolWebsite?.message}</FormControlErrorText>
                  </FormControlError>
                </FormControl>
              </>
            )}
          </VStack>

          <Button
            size="lg"
            className="w-full mt-6"
            onPress={handleSubmit(onSubmit)}
            disabled={isSubmitting}
          >
            <ButtonText className="text-white">
              {isSubmitting ? 'Creating Account...' : 'Create Account'}
            </ButtonText>
          </Button>
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