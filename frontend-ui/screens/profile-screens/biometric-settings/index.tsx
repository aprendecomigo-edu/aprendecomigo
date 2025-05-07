import useRouter from '@unitools/router';
import React, { useState, useEffect } from 'react';
import { Platform, ActivityIndicator } from 'react-native';

import { useAuth } from '@/api/authContext';
import { Button, ButtonText } from '@/components/ui/button';
import { Card, CardHeader, CardBody } from '@/components/ui/card';
import { Divider } from '@/components/ui/divider';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Switch } from '@/components/ui/switch';
import { Text } from '@/components/ui/text';
import { Toast, ToastTitle, useToast } from '@/components/ui/toast';
import { VStack } from '@/components/ui/vstack';
import MainLayout from '@/components/layouts/main-layout';

// Main BiometricSettings content component
const BiometricSettingsContent = () => {
  const toast = useToast();
  const router = useRouter();
  const { biometricSupport, enableBiometrics, disableBiometrics, userProfile } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [isChecking, setIsChecking] = useState(true);

  // Check biometric status on mount
  useEffect(() => {
    const checkStatus = async () => {
      try {
        setIsChecking(true);
        // The check is handled by the auth context
      } catch (error) {
        console.error('Error checking biometric status:', error);
        toast.show({
          placement: 'bottom right',
          render: ({ id }) => (
            <Toast nativeID={id} variant="solid" action="error">
              <ToastTitle>Error checking biometric status</ToastTitle>
            </Toast>
          ),
        });
      } finally {
        setIsChecking(false);
      }
    };

    checkStatus();
  }, []);

  // Handle toggle biometric authentication
  const handleToggleBiometrics = async (enabled: boolean) => {
    try {
      setIsLoading(true);

      if (enabled) {
        if (!userProfile?.email) {
          toast.show({
            placement: 'bottom right',
            render: ({ id }) => (
              <Toast nativeID={id} variant="solid" action="error">
                <ToastTitle>User profile not available</ToastTitle>
              </Toast>
            ),
          });
          return;
        }

        const success = await enableBiometrics(userProfile.email);
        if (success) {
          toast.show({
            placement: 'bottom right',
            render: ({ id }) => (
              <Toast nativeID={id} variant="solid" action="success">
                <ToastTitle>Biometric authentication enabled!</ToastTitle>
              </Toast>
            ),
          });
        } else {
          toast.show({
            placement: 'bottom right',
            render: ({ id }) => (
              <Toast nativeID={id} variant="solid" action="error">
                <ToastTitle>Could not enable biometric authentication</ToastTitle>
              </Toast>
            ),
          });
        }
      } else {
        const success = await disableBiometrics();
        if (success) {
          toast.show({
            placement: 'bottom right',
            render: ({ id }) => (
              <Toast nativeID={id} variant="solid" action="success">
                <ToastTitle>Biometric authentication disabled</ToastTitle>
              </Toast>
            ),
          });
        } else {
          toast.show({
            placement: 'bottom right',
            render: ({ id }) => (
              <Toast nativeID={id} variant="solid" action="error">
                <ToastTitle>Could not disable biometric authentication</ToastTitle>
              </Toast>
            ),
          });
        }
      }
    } catch (error) {
      console.error('Error toggling biometric authentication:', error);
      toast.show({
        placement: 'bottom right',
        render: ({ id }) => (
          <Toast nativeID={id} variant="solid" action="error">
            <ToastTitle>An error occurred. Please try again</ToastTitle>
          </Toast>
        ),
      });
    } finally {
      setIsLoading(false);
    }
  };

  if (isChecking) {
    return (
      <VStack
        className="w-full p-4"
        space="lg"
        style={{ alignItems: 'center', justifyContent: 'center' }}
      >
        <ActivityIndicator size="large" />
        <Text>Checking biometric status...</Text>
      </VStack>
    );
  }

  return (
    <VStack className="w-full p-4" space="lg">
      <Heading size="xl">Security Settings</Heading>

      <Card className="w-full">
        <CardHeader>
          <Heading size="md">Biometric Authentication</Heading>
        </CardHeader>

        <CardBody>
          <VStack space="md">
            {biometricSupport.isAvailable ? (
              <VStack space="lg">
                <Text>
                  Use {Platform.OS === 'ios' ? 'Face ID / Touch ID' : 'biometric authentication'} to
                  log in without entering your verification code.
                </Text>

                <HStack className="justify-between items-center">
                  <Text bold>
                    Enable {Platform.OS === 'ios' ? 'Face ID / Touch ID' : 'biometric'} login
                  </Text>
                  {isLoading ? (
                    <ActivityIndicator size="small" />
                  ) : (
                    <Switch
                      isDisabled={isLoading}
                      value={biometricSupport.isEnabled}
                      onValueChange={handleToggleBiometrics}
                    />
                  )}
                </HStack>

                <Divider />

                <Text size="sm" className="text-background-600">
                  When enabled, you'll be able to log in with your biometric data instead of
                  entering a verification code. Your biometric data is never shared with us and
                  stays securely on your device.
                </Text>
              </VStack>
            ) : (
              <Text>
                Biometric authentication is not available on this device. Please ensure you have set
                up biometric authentication in your device settings.
              </Text>
            )}
          </VStack>
        </CardBody>

        <VStack className="px-4 py-3">
          <Button
            variant="outline"
            action="secondary"
            className="mt-4"
            onPress={() => router.back()}
            isDisabled={isLoading}
          >
            <ButtonText>Back</ButtonText>
          </Button>
        </VStack>
      </Card>
    </VStack>
  );
};

// Wrap with MainLayout
export const BiometricSettings = () => {
  return (
    <MainLayout title="Security Settings">
      <BiometricSettingsContent />
    </MainLayout>
  );
};
