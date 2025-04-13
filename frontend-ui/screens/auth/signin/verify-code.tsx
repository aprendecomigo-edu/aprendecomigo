import React, { useState, useEffect } from "react";
import { Toast, ToastTitle, useToast } from "@/components/ui/toast";
import { HStack } from "@/components/ui/hstack";
import { VStack } from "@/components/ui/vstack";
import { Heading } from "@/components/ui/heading";
import { Text } from "@/components/ui/text";
import { LinkText } from "@/components/ui/link";
import Link from "@unitools/link";
import {
  FormControl,
  FormControlError,
  FormControlErrorIcon,
  FormControlErrorText,
  FormControlLabel,
  FormControlLabelText,
} from "@/components/ui/form-control";
import { Input, InputField } from "@/components/ui/input";
import { ArrowLeftIcon, Icon } from "@/components/ui/icon";
import { Button, ButtonText } from "@/components/ui/button";
import { Keyboard } from "react-native";
import { useForm, Controller } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { AlertTriangle } from "lucide-react-native";
import { Pressable } from "@/components/ui/pressable";
import useRouter from "@unitools/router";
import { AuthLayout } from "../layout";
import { verifyEmailCode } from "@/api/authApi";
import { useLocalSearchParams } from "expo-router";
import { useAuth } from "@/api/authContext";

// Define the form schema
const verifyCodeSchema = z.object({
  email: z.string().min(1, "Email is required").email(),
  code: z.string().min(1, "Verification code is required"),
});

type VerifyCodeSchemaType = z.infer<typeof verifyCodeSchema>;

const VerifyCodeForm = () => {
  const toast = useToast();
  const router = useRouter();
  const { email } = useLocalSearchParams<{ email: string }>();
  const [isVerifying, setIsVerifying] = useState(false);
  const { checkAuthStatus } = useAuth();

  // Verify code form
  const verifyCodeForm = useForm<VerifyCodeSchemaType>({
    resolver: zodResolver(verifyCodeSchema),
    defaultValues: {
      email: email || '',
      code: '',
    }
  });

  // Update form when email param changes
  useEffect(() => {
    if (email) {
      verifyCodeForm.setValue('email', email);
    }
  }, [email]);

  // Handle verify code submit
  const onVerifyCode = async (data: VerifyCodeSchemaType) => {
    try {
      setIsVerifying(true);
      await verifyEmailCode({ email: data.email, code: data.code });
      
      // Successfully verified - now explicitly update auth state
      await checkAuthStatus();
      
      toast.show({
        placement: "bottom right",
        render: ({ id }) => {
          return (
            <Toast nativeID={id} variant="accent" action="success">
              <ToastTitle>Logged in successfully!</ToastTitle>
            </Toast>
          );
        },
      });
      
      // Navigate to dashboard with error handling
      try {
        console.log('Attempting to navigate to dashboard...');
        router.replace('/dashboard');
      } catch (navigationError) {
        console.error('Navigation error:', navigationError);
        toast.show({
          placement: "bottom right",
          render: ({ id }) => {
            return (
              <Toast nativeID={id} variant="accent" action="error">
                <ToastTitle>Error loading dashboard. The component might be missing or invalid.</ToastTitle>
              </Toast>
            );
          },
        });
      }
    } catch (error) {
      toast.show({
        placement: "bottom right",
        render: ({ id }) => {
          return (
            <Toast nativeID={id} variant="accent" action="error">
              <ToastTitle>Invalid verification code. Please try again.</ToastTitle>
            </Toast>
          );
        },
      });
    } finally {
      setIsVerifying(false);
    }
  };

  const handleVerifyKeyPress = () => {
    Keyboard.dismiss();
    verifyCodeForm.handleSubmit(onVerifyCode)();
  };

  return (
    <VStack className="max-w-[440px] w-full" space="md">
      <VStack className="md:items-center" space="md">
        <Pressable
          onPress={() => {
            router.back();
          }}
        >
          <Icon
            as={ArrowLeftIcon}
            className="md:hidden text-background-800"
            size="xl"
          />
        </Pressable>
        <VStack>
          <Heading className="md:text-center" size="3xl">
            Verify Code
          </Heading>
          <Text>
            Enter the verification code sent to {email}
          </Text>
        </VStack>
      </VStack>
      <VStack className="w-full">
        <VStack space="xl" className="w-full">
          <FormControl
            isInvalid={!!verifyCodeForm.formState.errors?.code}
            className="w-full"
          >
            <FormControlLabel>
              <FormControlLabelText>Verification Code</FormControlLabelText>
            </FormControlLabel>
            <Controller
              defaultValue=""
              name="code"
              control={verifyCodeForm.control}
              render={({ field: { onChange, onBlur, value } }) => (
                <Input>
                  <InputField
                    placeholder="Enter the 6-digit verification code"
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
              onPress={() => {
                router.back();
              }}
            >
              <ButtonText className="font-medium">
                Try Different Email
              </ButtonText>
            </Button>
          </VStack>
        </VStack>
        <HStack className="self-center" space="sm">
          <Text size="md">Don't have an account?</Text>
          <Link href="/auth/signup">
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

export const VerifyCode = () => {
  return (
    <AuthLayout>
      <VerifyCodeForm />
    </AuthLayout>
  );
}; 