import { router } from 'expo-router';
import { AlertTriangle, X, Wifi } from 'lucide-react-native';
import React, { useEffect, useRef } from 'react';

import { useAuth } from '@/api/authContext';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Center } from '@/components/ui/center';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Pressable } from '@/components/ui/pressable';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

interface AuthGuardProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export const AuthGuard: React.FC<AuthGuardProps> = ({ children, fallback }) => {
  const { isLoggedIn, isLoading, serverError, serverAlert, clearServerAlert, logout } = useAuth();
  const hasRedirectedRef = useRef(false);

  // Handle authentication redirects
  useEffect(() => {
    const handleAuth = async () => {
      // If still loading, wait
      if (isLoading) {
        return;
      }

      // If server error, don't redirect (show error instead)
      if (serverError) {
        return;
      }

      // If not logged in and haven't redirected yet, redirect to signin
      if (!isLoggedIn && !hasRedirectedRef.current) {
        hasRedirectedRef.current = true;
        await logout(); // Clean up any invalid tokens
        router.replace('/auth/signin');
        return;
      }

      // If logged in, allow access
      if (isLoggedIn) {
        hasRedirectedRef.current = false; // Reset for future use
      }
    };

    handleAuth();
  }, [isLoggedIn, isLoading, serverError, logout]);

  // Reset redirect flag when user logs out
  useEffect(() => {
    if (!isLoggedIn) {
      hasRedirectedRef.current = false;
    }
  }, [isLoggedIn]);

  // Alert Banner Component
  const AlertBanner = () => {
    if (!serverAlert) return null;

    const bgColor = serverAlert.type === 'error' ? 'bg-red-50' : 'bg-yellow-50';
    const textColor = serverAlert.type === 'error' ? 'text-red-800' : 'text-yellow-800';
    const iconColor = serverAlert.type === 'error' ? 'text-red-500' : 'text-yellow-500';

    return (
      <Box
        className={`${bgColor} border-l-4 ${
          serverAlert.type === 'error' ? 'border-red-400' : 'border-yellow-400'
        } p-4 mb-4`}
      >
        <HStack className="items-start" space="sm">
          <Icon
            as={serverAlert.type === 'error' ? Wifi : AlertTriangle}
            size="sm"
            className={iconColor}
          />
          <VStack className="flex-1" space="xs">
            <Text className={`font-medium ${textColor}`}>
              {serverAlert.type === 'error' ? 'Connection Error' : 'Server Warning'}
            </Text>
            <Text className={`text-sm ${textColor}`}>{serverAlert.message}</Text>
          </VStack>
          <Pressable onPress={clearServerAlert} className="p-1">
            <Icon as={X} size="sm" className={iconColor} />
          </Pressable>
        </HStack>
      </Box>
    );
  };

  // Show server error page (for complete server down)
  if (serverError) {
    return (
      <Box className="flex-1 bg-gray-50">
        <Center className="flex-1">
          <VStack className="items-center max-w-sm mx-auto px-6" space="lg">
            <Icon as={Wifi} size="xl" className="text-red-500" />
            <VStack className="items-center" space="sm">
              <Heading size="lg" className="text-gray-900 text-center">
                Server Unavailable
              </Heading>
              <Text className="text-gray-600 text-center">{serverError}</Text>
            </VStack>
            <Button
              onPress={() => {
                logout();
                router.replace('/auth/signin');
              }}
              className="w-full bg-primary-600"
            >
              <ButtonText>Back to Login</ButtonText>
            </Button>
          </VStack>
        </Center>
      </Box>
    );
  }

  // Show loading state during auth check
  if (isLoading) {
    return (
      fallback || (
        <Center className="h-full w-full">
          <VStack className="items-center" space="md">
            <Spinner size="large" />
            <Text className="text-gray-500">Checking authentication...</Text>
          </VStack>
        </Center>
      )
    );
  }

  // If not authenticated, show nothing (redirect will happen)
  if (!isLoggedIn) {
    return null;
  }

  // User is authenticated, render children with alert banner
  return (
    <VStack className="flex-1">
      <AlertBanner />
      {children}
    </VStack>
  );
};
