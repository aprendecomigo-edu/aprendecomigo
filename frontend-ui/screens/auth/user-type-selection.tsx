import React from 'react';
import useRouter from '@unitools/router';
import { GraduationCap, School, Building2, ArrowRight } from 'lucide-react-native';

import { AuthLayout } from './layout';

import { Box } from '@/components/ui/box';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
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
    icon: GraduationCap,
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
    icon: School,
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
    <Pressable
      onPress={() => onSelect(option.type)}
      className={`w-full ${option.hoverColor} transition-colors duration-200`}
      accessibilityRole="button"
      accessibilityLabel={`Select ${option.title}`}
      accessibilityHint={option.description}
    >
      <Card className={`border-2 ${option.borderColor} bg-white shadow-sm`}>
        <CardHeader className="pb-3">
          <HStack space="md" className="items-center">
            <Box className={`w-16 h-16 rounded-full items-center justify-center ${option.backgroundColor}`}>
              <Icon 
                as={option.icon} 
                className={option.iconColor} 
                size="xl"
                accessibilityLabel={`${option.title} icon`}
              />
            </Box>
            <VStack className="flex-1" space="xs">
              <Heading size="lg" className="text-gray-900">
                {option.title}
              </Heading>
              <Text className="text-blue-600 font-medium text-base">
                {option.subtitle}
              </Text>
            </VStack>
            <Icon 
              as={ArrowRight} 
              className="text-gray-400" 
              size="lg"
              accessibilityLabel="Select option"
            />
          </HStack>
        </CardHeader>
        
        <CardContent className="pt-0">
          <VStack space="md">
            <Text className="text-gray-600 leading-relaxed">
              {option.description}
            </Text>
            
            <VStack space="xs">
              {option.features.map((feature, index) => (
                <HStack key={index} space="sm" className="items-center">
                  <Box className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                  <Text className="text-gray-700 text-sm">{feature}</Text>
                </HStack>
              ))}
            </VStack>
            
            <Button
              className="mt-4 w-full bg-gray-900 hover:bg-gray-800"
              onPress={() => onSelect(option.type)}
              accessibilityLabel={`${option.ctaText} - ${option.description}`}
            >
              <ButtonText className="text-white font-medium">
                {option.ctaText}
              </ButtonText>
              <ButtonIcon as={ArrowRight} className="text-white ml-2" />
            </Button>
          </VStack>
        </CardContent>
      </Card>
    </Pressable>
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