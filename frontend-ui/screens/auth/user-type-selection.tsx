import React from 'react';
import useRouter from '@unitools/router';

import { AuthLayout } from './layout';

import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Pressable } from '@/components/ui/pressable';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

// User type options configuration with enhanced descriptions
const USER_TYPE_OPTIONS = [
  {
    type: 'tutor' as const,
    title: 'Individual Tutor',
    subtitle: 'Start Your Own Tutoring Business',
    description: 'Create your personal tutoring practice and teach students directly',
    features: [
      'Set your own rates and schedule',
      'Choose your teaching subjects',
      'Build your student base',
      'Manage your own business'
    ],
    icon: '🎓',
    iconColor: 'text-blue-600',
    backgroundColor: 'bg-blue-100',
    borderColor: 'border-blue-200',
    hoverColor: 'hover:bg-blue-50',
    ctaText: 'Start Tutoring Business',
  },
  {
    type: 'school' as const,
    title: 'School or Institution',
    subtitle: 'Manage Multiple Teachers & Students',
    description: 'Register your school to manage teachers, students, and educational programs',
    features: [
      'Invite and manage teachers',
      'Organize students by classes',
      'Monitor educational progress',
      'Institutional oversight tools'
    ],
    icon: '🏫',
    iconColor: 'text-green-600',
    backgroundColor: 'bg-green-100',
    borderColor: 'border-green-200',
    hoverColor: 'hover:bg-green-50',
    ctaText: 'Register School',
  },
] as const;

type UserTypeOption = typeof USER_TYPE_OPTIONS[number]['type'];

interface UserTypeSelectionProps {
  onTypeSelect?: (type: UserTypeOption) => void;
}

const UserTypeCard: React.FC<{
  option: typeof USER_TYPE_OPTIONS[number];
  onSelect: (type: UserTypeOption) => void;
}> = ({ option, onSelect }) => {
  return (
    <Box className="p-4 border rounded">
      <Text>{option.title}</Text>
      <Text>{option.description}</Text>
      <Text onPress={() => onSelect(option.type)}>
        Select {option.type}
      </Text>
    </Box>
  );
};

const UserTypeSelectionForm: React.FC<UserTypeSelectionProps> = ({ onTypeSelect }) => {
  const router = useRouter();

  const handleTypeSelect = (type: UserTypeOption) => {
    if (onTypeSelect) {
      onTypeSelect(type);
    } else {
      // Navigate to signup with type parameter
      router.push(`/auth/signup?type=${type}`);
    }
  };

  return (
    <VStack className="w-full max-w-4xl mx-auto" space="xl">
      {/* Header */}
      <VStack className="items-center text-center" space="md">
        <Heading className="text-4xl font-bold text-gray-900" size="4xl">
          Join Aprende Comigo
        </Heading>
        <Text className="text-xl text-gray-600 max-w-2xl">
          Choose how you'd like to use our platform to enhance education and connect with learners
        </Text>
      </VStack>

      {/* User Type Options */}
      <VStack className="w-full" space="lg">
        {USER_TYPE_OPTIONS.map((option) => (
          <UserTypeCard
            key={option.type}
            option={option}
            onSelect={handleTypeSelect}
          />
        ))}
      </VStack>

      {/* Additional Info */}
      <VStack className="items-center text-center" space="md">
        <Text className="text-gray-500 text-sm max-w-lg">
          Both options include full access to our tutoring platform, real-time communication tools, 
          and comprehensive student management features.
        </Text>
        
        <HStack space="sm" className="items-center">
          <Text className="text-gray-600">Already have an account?</Text>
          <Pressable onPress={() => router.push('/auth/signin')}>
            <Text className="text-blue-600 font-medium underline">
              Sign in here
            </Text>
          </Pressable>
        </HStack>
      </VStack>
    </VStack>
  );
};

export const UserTypeSelection: React.FC<UserTypeSelectionProps> = (props) => {
  return (
    <AuthLayout>
      <UserTypeSelectionForm {...props} />
    </AuthLayout>
  );
};