import React, { useState, useEffect } from "react";
import { HStack, VStack } from "@/components/ui/stack";
import { Text } from "@/components/ui/text";
import { Switch } from "@/components/ui/switch";
import { Platform } from "react-native";
import { useAuth } from "@/api/authContext";
import { Toast, ToastTitle, useToast } from "@/components/ui/toast";
import { Heading } from "@/components/ui/heading";
import { Card, CardHeader, CardContent, CardFooter } from "@/components/ui/card";
import { Divider } from "@/components/ui/divider";
import { Button, ButtonText } from "@/components/ui/button";
import useRouter from "@unitools/router";

export const BiometricSettings = () => {
  const toast = useToast();
  const router = useRouter();
  const { biometricSupport, enableBiometrics, disableBiometrics, userProfile } = useAuth();
  const [isLoading, setIsLoading] = useState(false);

  // Handle toggle biometric authentication
  const handleToggleBiometrics = async (enabled: boolean) => {
    try {
      setIsLoading(true);

      if (enabled) {
        // Enable biometrics if user has a profile and email
        if (userProfile?.email) {
          const success = await enableBiometrics(userProfile.email);

          if (success) {
            toast.show({
              placement: "bottom right",
              render: ({ id }) => {
                return (
                  <Toast nativeID={id} variant="accent" action="success">
                    <ToastTitle>Biometric authentication enabled!</ToastTitle>
                  </Toast>
                );
              },
            });
          } else {
            toast.show({
              placement: "bottom right",
              render: ({ id }) => {
                return (
                  <Toast nativeID={id} variant="accent" action="error">
                    <ToastTitle>Could not enable biometric authentication.</ToastTitle>
                  </Toast>
                );
              },
            });
          }
        } else {
          toast.show({
            placement: "bottom right",
            render: ({ id }) => {
              return (
                <Toast nativeID={id} variant="accent" action="error">
                  <ToastTitle>User profile not available.</ToastTitle>
                </Toast>
              );
            },
          });
        }
      } else {
        // Disable biometrics
        const success = await disableBiometrics();

        if (success) {
          toast.show({
            placement: "bottom right",
            render: ({ id }) => {
              return (
                <Toast nativeID={id} variant="accent" action="success">
                  <ToastTitle>Biometric authentication disabled.</ToastTitle>
                </Toast>
              );
            },
          });
        } else {
          toast.show({
            placement: "bottom right",
            render: ({ id }) => {
              return (
                <Toast nativeID={id} variant="accent" action="error">
                  <ToastTitle>Could not disable biometric authentication.</ToastTitle>
                </Toast>
              );
            },
          });
        }
      }
    } catch (error) {
      console.error('Error toggling biometric authentication:', error);
      toast.show({
        placement: "bottom right",
        render: ({ id }) => {
          return (
            <Toast nativeID={id} variant="accent" action="error">
              <ToastTitle>An error occurred. Please try again.</ToastTitle>
            </Toast>
          );
        },
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <VStack className="w-full p-4" space="lg">
      <Heading size="xl">Security Settings</Heading>

      <Card className="w-full">
        <CardHeader>
          <Heading size="md">Biometric Authentication</Heading>
        </CardHeader>

        <CardContent>
          <VStack space="md">
            {biometricSupport.isAvailable ? (
              <VStack space="lg">
                <Text>
                  Use {Platform.OS === 'ios' ? 'Face ID / Touch ID' : 'biometric authentication'} to log in
                  without entering your verification code.
                </Text>

                <HStack justifyContent="space-between" alignItems="center">
                  <Text fontWeight="$medium">
                    Enable {Platform.OS === 'ios' ? 'Face ID / Touch ID' : 'biometric'} login
                  </Text>
                  <Switch
                    isDisabled={isLoading}
                    value={biometricSupport.isEnabled}
                    onValueChange={handleToggleBiometrics}
                  />
                </HStack>

                <Divider />

                <Text size="sm" className="text-background-600">
                  When enabled, you'll be able to log in with your biometric data instead of entering
                  a verification code. Your biometric data is never shared with us and stays securely
                  on your device.
                </Text>
              </VStack>
            ) : (
              <Text>
                Biometric authentication is not available on this device. Please ensure you have set up
                biometric authentication in your device settings.
              </Text>
            )}
          </VStack>
        </CardContent>

        <CardFooter>
          <Button
            variant="outline"
            action="secondary"
            className="mt-4"
            onPress={() => router.back()}
          >
            <ButtonText>Back</ButtonText>
          </Button>
        </CardFooter>
      </Card>
    </VStack>
  );
};
