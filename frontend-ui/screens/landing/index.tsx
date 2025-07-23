import useRouter from '@unitools/router';
import { GraduationCap, School, Users, Calendar, CreditCard, Globe } from 'lucide-react-native';
import React from 'react';
import { ScrollView } from 'react-native';

import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { ErrorBoundary } from '@/components/ErrorBoundary';

// Constants for better maintainability
const TUTOR_FEATURES = [
  "Professional scheduling system",
  "Automated billing and invoicing",
  "Student progress tracking",
  "Cross-platform accessibility (web, iOS, Android)",
  "Secure payment processing"
];

const SCHOOL_FEATURES = [
  "Multi-teacher management",
  "Advanced role-based permissions",
  "Institutional billing settings",
  "Bulk student management",
  "Enterprise-grade features"
];

const PLATFORM_FEATURES = [
  {
    icon: Calendar,
    title: "Smart Scheduling",
    description: "Automated booking system with conflict prevention, recurring classes, and availability management"
  },
  {
    icon: CreditCard,
    title: "Professional Billing",
    description: "Automated invoicing, payment tracking, and comprehensive financial reporting for tax purposes"
  },
  {
    icon: Users,
    title: "Student Management",
    description: "Complete student profiles, progress tracking, and parent communication tools"
  },
  {
    icon: Globe,
    title: "Cross-Platform Access",
    description: "Works seamlessly on web browsers, iOS, and Android devices with synchronized data"
  }
];

// User type configuration for consistency
const USER_TYPE_CONFIG = {
  tutor: {
    icon: GraduationCap,
    title: "Individual Tutor",
    subtitle: "Set up your tutoring practice",
    features: TUTOR_FEATURES,
    buttonText: "Start Your Tutoring Practice",
    isPrimary: true,
  },
  school: {
    icon: School,
    title: "School or Institution",
    subtitle: "Manage your educational organization",
    features: SCHOOL_FEATURES,
    buttonText: "Register Your Institution",
    isPrimary: false,
  },
} as const;

const FeatureCard = ({ 
  icon, 
  title, 
  description 
}: { 
  icon: React.ComponentType; 
  title: string; 
  description: string; 
}) => (
  <Card className="p-6 mb-4 bg-white border border-gray-200" accessibilityRole="article">
    <VStack space="md">
      <Box className="w-12 h-12 bg-blue-100 rounded-lg items-center justify-center">
        <Icon 
          as={icon} 
          size="lg" 
          className="text-blue-600" 
          accessibilityLabel={`${title} feature icon`}
        />
      </Box>
      <VStack space="sm">
        <Heading size="md" className="text-gray-900" accessibilityRole="header">{title}</Heading>
        <Text size="sm" className="text-gray-600 leading-5">{description}</Text>
      </VStack>
    </VStack>
  </Card>
);

const UserTypeCard = ({ 
  userType,
  onPress
}: { 
  userType: 'tutor' | 'school';
  onPress: () => void;
}) => {
  const config = USER_TYPE_CONFIG[userType];
  
  return (
    <Card 
      className={`p-8 mb-6 ${config.isPrimary ? 'bg-blue-50 border-2 border-blue-200' : 'bg-white border border-gray-200'}`}
      accessibilityRole="button"
      accessibilityLabel={`${config.title} registration option`}
      accessibilityHint={`Tap to ${config.buttonText.toLowerCase()}`}
    >
      <VStack space="lg">
        <VStack space="md" className="items-center">
          <Box className={`w-16 h-16 ${config.isPrimary ? 'bg-blue-600' : 'bg-gray-100'} rounded-full items-center justify-center`}>
            <Icon 
              as={config.icon} 
              size="xl" 
              className={config.isPrimary ? 'text-white' : 'text-gray-600'} 
              accessibilityLabel={`${config.title} icon`}
            />
          </Box>
          <VStack space="xs" className="items-center">
            <Heading size="xl" className="text-gray-900 text-center" accessibilityRole="header">{config.title}</Heading>
            <Text size="md" className="text-gray-600 text-center">{config.subtitle}</Text>
          </VStack>
        </VStack>
        
        <VStack space="sm" accessibilityRole="list">
          {config.features.map((feature, index) => (
            <HStack key={index} space="sm" className="items-center" accessibilityRole="listitem">
              <Box className="w-2 h-2 bg-green-500 rounded-full" accessibilityLabel="Feature bullet point" />
              <Text size="sm" className="text-gray-700 flex-1">{feature}</Text>
            </HStack>
          ))}
        </VStack>
        
        <Button 
          onPress={onPress}
          className={`w-full ${config.isPrimary ? 'bg-blue-600' : 'bg-gray-800'}`}
          accessibilityLabel={config.buttonText}
          accessibilityHint={`Navigate to ${userType} registration form`}
        >
          <ButtonText className="text-white font-medium">{config.buttonText}</ButtonText>
        </Button>
      </VStack>
    </Card>
  );
};

const LandingContent = () => {
  const router = useRouter();

  const handleTutorSignup = () => {
    router.push('/auth/signup?type=tutor');
  };

  const handleSchoolSignup = () => {
    router.push('/auth/signup?type=school');
  };

  const handleSignIn = () => {
    router.push('/auth/signin');
  };

  return (
    <ScrollView className="flex-1 bg-gray-50">
      <VStack space="xl" className="px-6 py-8">
        {/* Header */}
        <VStack space="lg" className="items-center py-8">
          <Heading 
            size="3xl" 
            className="text-gray-900 text-center font-bold"
            accessibilityRole="header"
            accessibilityLevel={1}
          >
            Aprende Comigo
          </Heading>
          <Text size="xl" className="text-gray-600 text-center leading-7 max-w-md">
            Professional tutoring platform connecting educators with students across Portugal
          </Text>
          
          <HStack space="md" className="mt-4">
            <Button 
              variant="outline" 
              onPress={handleSignIn}
              accessibilityLabel="Sign in to your account"
              accessibilityHint="Navigate to the sign in page for existing users"
            >
              <ButtonText className="text-gray-700">Sign In</ButtonText>
            </Button>
          </HStack>
        </VStack>

        {/* User Type Selection */}
        <VStack space="lg">
          <VStack space="sm" className="items-center">
            <Heading size="2xl" className="text-gray-900 text-center">
              Get Started
            </Heading>
            <Text size="lg" className="text-gray-600 text-center">
              Choose the option that best describes you
            </Text>
          </VStack>

          <UserTypeCard
            userType="tutor"
            onPress={handleTutorSignup}
          />

          <UserTypeCard
            userType="school"
            onPress={handleSchoolSignup}
          />
        </VStack>

        {/* Platform Features */}
        <VStack space="lg" className="mt-8">
          <VStack space="sm" className="items-center">
            <Heading size="2xl" className="text-gray-900 text-center">
              Why Choose Aprende Comigo?
            </Heading>
            <Text size="lg" className="text-gray-600 text-center">
              Built specifically for the Portuguese education market
            </Text>
          </VStack>

          {PLATFORM_FEATURES.map((feature, index) => (
            <FeatureCard
              key={index}
              icon={feature.icon}
              title={feature.title}
              description={feature.description}
            />
          ))}
        </VStack>

        {/* Footer */}
        <VStack space="md" className="items-center py-8 mt-8">
          <Text size="sm" className="text-gray-500 text-center">
            Already have an account?
          </Text>
          <Button variant="link" onPress={handleSignIn}>
            <ButtonText className="text-blue-600 font-medium">Sign in here</ButtonText>
          </Button>
        </VStack>
      </VStack>
    </ScrollView>
  );
};

export const Landing = () => (
  <ErrorBoundary
    onError={(error, errorInfo) => {
      // Log error for analytics/monitoring
      console.error('Landing page error:', error, errorInfo);
    }}
  >
    <LandingContent />
  </ErrorBoundary>
);