/**
 * SignIn Component with Dependency Injection
 *
 * This is a migrated version of the SignIn component that uses dependency injection
 * for better testability and separation of concerns.
 */

import React, { useState } from 'react';
import { Alert } from 'react-native';

import { Box } from '@/components/ui/box';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { useDependencies } from '@/services/di';

export const SignInWithDI: React.FC = () => {
  const [email, setEmail] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { authApi, toastService, routerService, analyticsService } = useDependencies();

  const handleSubmitEmail = async () => {
    if (!email) {
      toastService.showToast('error', 'Please enter your email address.');
      return;
    }

    setIsSubmitting(true);

    try {
      await authApi.requestEmailCode({ email });

      // Track analytics
      analyticsService.track('auth_email_submitted', {
        email_domain: email.split('@')[1],
      });

      toastService.showToast('success', 'Verification code sent to your email!');
      routerService.push(`/auth/verify-code?email=${encodeURIComponent(email)}`);
    } catch (error: any) {
      if (__DEV__) {
        console.error('Failed to request email code:', error); // TODO: Review for sensitive data // TODO: Review for sensitive data // TODO: Review for sensitive data
      }
      toastService.showToast('error', 'Failed to send verification code. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Box className="flex-1 justify-center px-6">
      <VStack space="lg" className="max-w-md mx-auto w-full">
        <Text className="text-2xl font-bold text-center mb-8">Sign In to Aprende Comigo</Text>

        <VStack space="md">
          <Input
            placeholder="your_email@example.com"
            value={email}
            onChangeText={setEmail}
            keyboardType="email-address"
            autoCapitalize="none"
            autoComplete="email"
            className="w-full"
          />

          <Button onPress={handleSubmitEmail} disabled={isSubmitting} className="w-full">
            <Text className="text-white font-semibold">
              {isSubmitting ? 'Sending...' : 'Send Login Code'}
            </Text>
          </Button>
        </VStack>
      </VStack>
    </Box>
  );
};
