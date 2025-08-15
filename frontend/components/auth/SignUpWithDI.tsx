/**
 * SignUp Component with Dependency Injection
 *
 * This is a migrated version of the SignUp component that uses dependency injection
 * for better testability and separation of concerns.
 */

import React, { useState } from 'react';

import { Box } from '@/components/ui/box';
import { Button } from '@/components/ui/button';
import { HStack } from '@/components/ui/hstack';
import { Input } from '@/components/ui/input';
import { Pressable } from '@/components/ui/pressable';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { useDependencies } from '@/services/di';

export const SignUpWithDI: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'tutor' | 'school'>('tutor');
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone_number: '',
    school_name: '',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { authApi, toastService, routerService, authContextService } = useDependencies();

  const handleCreateAccount = async () => {
    if (!formData.name || !formData.email) {
      toastService.showToast('error', 'Please fill in all required fields.');
      return;
    }

    setIsSubmitting(true);

    try {
      let userData: any = {
        name: formData.name,
        email: formData.email,
        phone_number: formData.phone_number,
        user_type: activeTab,
      };

      if (activeTab === 'tutor') {
        // For tutors, create a personal school
        userData.school = {
          name: `${formData.name}'s Tutoring Practice`,
        };
      } else {
        // For schools, use the provided school name
        userData.school = {
          name: formData.school_name || 'New School',
        };
      }

      // Use user profile from context if available
      if (authContextService.userProfile) {
        userData = {
          ...userData,
          name: authContextService.userProfile.name || userData.name,
          email: authContextService.userProfile.email || userData.email,
          phone_number: authContextService.userProfile.phone_number || userData.phone_number,
        };
      }

      await authApi.createUser(userData);

      toastService.showToast('success', 'Account created successfully!');
      routerService.push('/dashboard');
    } catch (error: any) {
      if (__DEV__) {
        console.error('Failed to create account:', error); // TODO: Review for sensitive data
      }
      toastService.showToast('error', 'Failed to create account. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const updateFormData = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  return (
    <Box className="flex-1 justify-center px-6">
      <VStack space="lg" className="max-w-md mx-auto w-full">
        <Text className="text-2xl font-bold text-center mb-8">Create Account</Text>

        {/* Tab Selection */}
        <HStack space="sm" className="w-full mb-6">
          <Pressable
            className={`flex-1 py-3 px-4 rounded-lg border ${
              activeTab === 'tutor' ? 'bg-primary border-primary' : 'bg-white border-gray-300'
            }`}
            onPress={() => setActiveTab('tutor')}
          >
            <Text
              className={`text-center font-medium ${
                activeTab === 'tutor' ? 'text-white' : 'text-gray-700'
              }`}
            >
              Individual Tutor
            </Text>
          </Pressable>

          <Pressable
            className={`flex-1 py-3 px-4 rounded-lg border ${
              activeTab === 'school' ? 'bg-primary border-primary' : 'bg-white border-gray-300'
            }`}
            onPress={() => setActiveTab('school')}
          >
            <Text
              className={`text-center font-medium ${
                activeTab === 'school' ? 'text-white' : 'text-gray-700'
              }`}
            >
              School
            </Text>
          </Pressable>
        </HStack>

        <VStack space="md">
          <Input
            placeholder="Enter your full name"
            value={formData.name}
            onChangeText={value => updateFormData('name', value)}
            className="w-full"
          />

          <Input
            placeholder="Enter your email address"
            value={formData.email}
            onChangeText={value => updateFormData('email', value)}
            keyboardType="email-address"
            autoCapitalize="none"
            className="w-full"
          />

          <Input
            placeholder="Enter your phone number"
            value={formData.phone_number}
            onChangeText={value => updateFormData('phone_number', value)}
            keyboardType="phone-pad"
            className="w-full"
          />

          {activeTab === 'school' && (
            <Input
              placeholder="Enter your school name"
              value={formData.school_name}
              onChangeText={value => updateFormData('school_name', value)}
              className="w-full"
            />
          )}

          <Button onPress={handleCreateAccount} disabled={isSubmitting} className="w-full mt-4">
            <Text className="text-white font-semibold">
              {isSubmitting ? 'Creating...' : 'Create Account'}
            </Text>
          </Button>
        </VStack>
      </VStack>
    </Box>
  );
};
