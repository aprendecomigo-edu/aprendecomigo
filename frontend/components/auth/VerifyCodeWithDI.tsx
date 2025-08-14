/**
 * VerifyCode Component with Dependency Injection
 *
 * This is a migrated version of the VerifyCode component that uses dependency injection
 * for better testability and separation of concerns.
 */

import React, { useState } from 'react';

import { Box } from '@/components/ui/box';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { useDependencies } from '@/services/di';

export const VerifyCodeWithDI: React.FC = () => {
  const [code, setCode] = useState('');
  const [isVerifying, setIsVerifying] = useState(false);

  const { authApi, toastService, routerService, authContextService, onboardingApiService } =
    useDependencies();

  const handleVerifyCode = async () => {
    if (!code || code.length !== 6) {
      toastService.showToast('error', 'Please enter a valid 6-digit code.');
      return;
    }

    setIsVerifying(true);

    try {
      // Get email/phone from URL params (simplified for this example)
      const verifyParams = {
        email: 'test@example.com', // In real implementation, get from URL params
        code,
      };

      const response = await authApi.verifyEmailCode(verifyParams);

      // Update auth context with user profile
      if (authContextService.setUserProfile && response.user) {
        await authContextService.setUserProfile(response.user);
      }

      await authContextService.checkAuthStatus();

      toastService.showToast('success', 'Verification successful!');

      // Handle navigation based on user type and onboarding status
      if (response.is_new_user || !response.user.first_login_completed) {
        // Check onboarding preferences
        const navPrefs = await onboardingApiService.getNavigationPreferences();
        const progress = await onboardingApiService.getOnboardingProgress();

        if (navPrefs.show_onboarding || progress.completion_percentage === 0) {
          routerService.replace('/onboarding/welcome');
          return;
        }
      }

      // Navigate to dashboard for returning users
      routerService.replace('/dashboard');
    } catch (error: any) {
      console.error('Failed to verify code:', error);
      toastService.showToast('error', 'Invalid verification code. Please try again.');
    } finally {
      setIsVerifying(false);
    }
  };

  return (
    <Box className="flex-1 justify-center px-6">
      <VStack space="lg" className="max-w-md mx-auto w-full">
        <Text className="text-2xl font-bold text-center mb-8">Enter Verification Code</Text>

        <Text className="text-center text-gray-600 mb-6">
          We sent a 6-digit code to your email. Enter it below to continue.
        </Text>

        <VStack space="md">
          <Input
            placeholder="Enter the verification code"
            value={code}
            onChangeText={setCode}
            keyboardType="number-pad"
            maxLength={6}
            className="w-full text-center text-2xl tracking-wider"
          />

          <Button
            onPress={handleVerifyCode}
            disabled={isVerifying || code.length !== 6}
            className="w-full"
          >
            <Text className="text-white font-semibold">
              {isVerifying ? 'Verifying...' : 'Verify Code'}
            </Text>
          </Button>
        </VStack>
      </VStack>
    </Box>
  );
};
