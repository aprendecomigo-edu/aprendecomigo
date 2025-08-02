import useRouter from '@unitools/router';
import {
  CheckCircle,
  Star,
  Users,
  BookOpen,
  DollarSign,
  Calendar,
  ArrowRight,
  Share2,
  Settings,
  Eye,
  Sparkles,
  Trophy,
} from 'lucide-react-native';
import React, { useEffect, useState } from 'react';
import { Animated, Dimensions } from 'react-native';

import { Badge, BadgeText } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Pressable } from '@/components/ui/pressable';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

const { width: screenWidth } = Dimensions.get('window');

interface TutorProfileSummary {
  schoolName: string;
  educationalSystem: string;
  subjectCount: number;
  averageRate: number;
  currency: string;
  completionScore: number;
}

interface OnboardingSuccessScreenProps {
  profileSummary: TutorProfileSummary;
  onContinueToDashboard?: () => void;
  onViewProfile?: () => void;
  onShareProfile?: () => void;
  onCustomizeProfile?: () => void;
  showCelebration?: boolean;
  userName?: string;
}

// Next steps suggestions for new tutors
const NEXT_STEPS = [
  {
    id: 'view-profile',
    title: 'View Your Profile',
    description: 'See how your profile appears to potential students',
    icon: Eye,
    color: 'bg-blue-100 text-blue-600',
    action: 'view',
  },
  {
    id: 'customize-profile',
    title: 'Customize Your Profile',
    description: 'Add more details, photos, and teaching materials',
    icon: Settings,
    color: 'bg-purple-100 text-purple-600',
    action: 'customize',
  },
  {
    id: 'share-profile',
    title: 'Share Your Profile',
    description: 'Share with friends and potential students',
    icon: Share2,
    color: 'bg-green-100 text-green-600',
    action: 'share',
  },
  {
    id: 'schedule-availability',
    title: 'Set Your Availability',
    description: 'Configure your teaching schedule and booking preferences',
    icon: Calendar,
    color: 'bg-orange-100 text-orange-600',
    action: 'schedule',
  },
];

// Achievement badges based on profile completion
const ACHIEVEMENT_BADGES = [
  {
    id: 'profile-complete',
    title: 'Profile Master',
    description: 'Completed full tutor profile setup',
    icon: CheckCircle,
    color: 'bg-green-100 text-green-600',
    requirement: 'Profile completion',
  },
  {
    id: 'multi-subject',
    title: 'Subject Expert',
    description: 'Teaching multiple subjects',
    icon: BookOpen,
    color: 'bg-blue-100 text-blue-600',
    requirement: '3+ subjects',
    check: (summary: TutorProfileSummary) => summary.subjectCount >= 3,
  },
  {
    id: 'competitive-rates',
    title: 'Market Ready',
    description: 'Competitive pricing setup',
    icon: DollarSign,
    color: 'bg-yellow-100 text-yellow-600',
    requirement: 'Rate configuration',
  },
  {
    id: 'quality-profile',
    title: 'Quality Tutor',
    description: 'High-quality profile score',
    icon: Star,
    color: 'bg-purple-100 text-purple-600',
    requirement: '80%+ completion',
    check: (summary: TutorProfileSummary) => summary.completionScore >= 80,
  },
];

const AnimatedSuccessIcon: React.FC = () => {
  const [scaleAnim] = useState(new Animated.Value(0));
  const [rotateAnim] = useState(new Animated.Value(0));

  useEffect(() => {
    // Scale animation
    Animated.sequence([
      Animated.spring(scaleAnim, {
        toValue: 1.2,
        useNativeDriver: true,
        tension: 100,
        friction: 8,
      }),
      Animated.spring(scaleAnim, {
        toValue: 1,
        useNativeDriver: true,
        tension: 100,
        friction: 8,
      }),
    ]).start();

    // Rotation animation
    Animated.timing(rotateAnim, {
      toValue: 1,
      duration: 1000,
      useNativeDriver: true,
    }).start();
  }, []);

  const rotateInterpolate = rotateAnim.interpolate({
    inputRange: [0, 1],
    outputRange: ['0deg', '360deg'],
  });

  return (
    <Box className="items-center justify-center relative">
      <Animated.View
        style={{
          transform: [{ scale: scaleAnim }, { rotate: rotateInterpolate }],
        }}
      >
        <Box className="w-24 h-24 rounded-full bg-green-100 items-center justify-center">
          <Icon as={CheckCircle} className="text-green-600" size="3xl" />
        </Box>
      </Animated.View>

      {/* Sparkle effects */}
      <Box className="absolute -top-2 -right-2">
        <Icon as={Sparkles} className="text-yellow-500" size="lg" />
      </Box>
      <Box className="absolute -bottom-2 -left-2">
        <Icon as={Sparkles} className="text-blue-500" size="md" />
      </Box>
    </Box>
  );
};

const ProfileSummaryCard: React.FC<{
  summary: TutorProfileSummary;
}> = ({ summary }) => {
  const getCurrencySymbol = (currency: string) => {
    const symbols: Record<string, string> = {
      EUR: '€',
      USD: '$',
      GBP: '£',
      BRL: 'R$',
    };
    return symbols[currency] || currency;
  };

  return (
    <Card className="bg-white border border-gray-200 shadow-sm">
      <CardHeader className="pb-2">
        <Heading size="md" className="text-gray-900">
          Your Tutoring Profile
        </Heading>
      </CardHeader>
      <CardContent className="pt-0">
        <VStack space="md">
          <VStack space="sm">
            <HStack className="items-center justify-between">
              <Text className="text-gray-600 text-sm">Practice Name</Text>
              <Text className="text-gray-900 font-medium">{summary.schoolName}</Text>
            </HStack>

            <HStack className="items-center justify-between">
              <Text className="text-gray-600 text-sm">Education System</Text>
              <Text className="text-gray-900 font-medium">{summary.educationalSystem}</Text>
            </HStack>

            <HStack className="items-center justify-between">
              <Text className="text-gray-600 text-sm">Teaching Subjects</Text>
              <Badge className="bg-blue-100">
                <BadgeText className="text-blue-700">
                  {summary.subjectCount} subject{summary.subjectCount !== 1 ? 's' : ''}
                </BadgeText>
              </Badge>
            </HStack>

            <HStack className="items-center justify-between">
              <Text className="text-gray-600 text-sm">Average Rate</Text>
              <Text className="text-gray-900 font-medium">
                {getCurrencySymbol(summary.currency)}
                {summary.averageRate}/hour
              </Text>
            </HStack>
          </VStack>

          <Box className="border-t border-gray-200 pt-3">
            <HStack className="items-center justify-between">
              <Text className="text-gray-600 text-sm">Profile Completion</Text>
              <HStack space="xs" className="items-center">
                <Box className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
                  <Box
                    className="h-full bg-green-600 transition-all duration-500"
                    style={{ width: `${summary.completionScore}%` }}
                  />
                </Box>
                <Text className="text-green-600 font-bold text-sm">
                  {Math.round(summary.completionScore)}%
                </Text>
              </HStack>
            </HStack>
          </Box>
        </VStack>
      </CardContent>
    </Card>
  );
};

const AchievementBadges: React.FC<{
  summary: TutorProfileSummary;
}> = ({ summary }) => {
  const earnedBadges = ACHIEVEMENT_BADGES.filter(badge => {
    if (badge.check) {
      return badge.check(summary);
    }
    return true; // Default badges are always earned
  });

  return (
    <VStack space="md">
      <Heading size="md" className="text-gray-900">
        Achievements Unlocked
      </Heading>

      <VStack space="sm">
        {earnedBadges.map(badge => {
          const BadgeIcon = badge.icon;

          return (
            <Card key={badge.id} className="bg-white border border-gray-200">
              <CardContent className="p-3">
                <HStack space="sm" className="items-center">
                  <Box
                    className={`w-10 h-10 rounded-full items-center justify-center ${badge.color}`}
                  >
                    <Icon as={BadgeIcon} className={badge.color.split(' ')[1]} size="md" />
                  </Box>

                  <VStack className="flex-1" space="xs">
                    <Text className="text-gray-900 font-medium text-sm">{badge.title}</Text>
                    <Text className="text-gray-600 text-xs">{badge.description}</Text>
                  </VStack>

                  <Icon as={Trophy} className="text-yellow-500" size="sm" />
                </HStack>
              </CardContent>
            </Card>
          );
        })}
      </VStack>
    </VStack>
  );
};

const NextStepsGrid: React.FC<{
  onStepClick: (action: string) => void;
}> = ({ onStepClick }) => {
  return (
    <VStack space="md">
      <Heading size="md" className="text-gray-900">
        Recommended Next Steps
      </Heading>

      <VStack space="sm">
        {NEXT_STEPS.map(step => {
          const StepIcon = step.icon;

          return (
            <Pressable
              key={step.id}
              onPress={() => onStepClick(step.action)}
              className="w-full"
              accessibilityRole="button"
              accessibilityLabel={step.title}
              accessibilityHint={step.description}
            >
              <Card className="bg-white border border-gray-200 hover:border-blue-300 hover:bg-blue-50 transition-all duration-200">
                <CardContent className="p-4">
                  <HStack className="items-center justify-between">
                    <HStack space="sm" className="items-center flex-1">
                      <Box
                        className={`w-10 h-10 rounded-full items-center justify-center ${step.color}`}
                      >
                        <Icon as={StepIcon} className={step.color.split(' ')[1]} size="md" />
                      </Box>

                      <VStack className="flex-1" space="xs">
                        <Text className="text-gray-900 font-medium">{step.title}</Text>
                        <Text className="text-gray-600 text-sm">{step.description}</Text>
                      </VStack>
                    </HStack>

                    <Icon as={ArrowRight} className="text-gray-400" size="md" />
                  </HStack>
                </CardContent>
              </Card>
            </Pressable>
          );
        })}
      </VStack>
    </VStack>
  );
};

export const OnboardingSuccessScreen: React.FC<OnboardingSuccessScreenProps> = ({
  profileSummary,
  onContinueToDashboard,
  onViewProfile,
  onShareProfile,
  onCustomizeProfile,
  showCelebration = true,
  userName = 'Tutor',
}) => {
  const router = useRouter();

  const handleNextStepClick = (action: string) => {
    switch (action) {
      case 'view':
        if (onViewProfile) {
          onViewProfile();
        } else {
          router.push('/profile');
        }
        break;
      case 'customize':
        if (onCustomizeProfile) {
          onCustomizeProfile();
        } else {
          router.push('/onboarding/teacher-profile');
        }
        break;
      case 'share':
        if (onShareProfile) {
          onShareProfile();
        }
        break;
      case 'schedule':
        router.push('/settings?tab=availability');
        break;
      default:
        break;
    }
  };

  const handleContinueToDashboard = () => {
    if (onContinueToDashboard) {
      onContinueToDashboard();
    } else {
      router.push('/home');
    }
  };

  return (
    <VStack className="flex-1 bg-gray-50 p-4" space="xl">
      {/* Header Section */}
      <VStack className="items-center text-center" space="lg">
        {showCelebration && <AnimatedSuccessIcon />}

        <VStack space="sm" className="items-center">
          <Heading size="2xl" className="text-gray-900 text-center">
            Congratulations, {userName}!
          </Heading>
          <Text className="text-xl text-gray-600 text-center max-w-md">
            Your tutoring profile is complete and ready to attract students
          </Text>
        </VStack>

        <Box className="bg-green-50 border border-green-200 p-4 rounded-lg">
          <HStack space="sm" className="items-center justify-center">
            <Icon as={Users} className="text-green-600" size="sm" />
            <Text className="text-green-800 font-medium">
              Your profile is now live and discoverable by students!
            </Text>
          </HStack>
        </Box>
      </VStack>

      {/* Profile Summary */}
      <ProfileSummaryCard summary={profileSummary} />

      {/* Achievement Badges */}
      <AchievementBadges summary={profileSummary} />

      {/* Next Steps */}
      <NextStepsGrid onStepClick={handleNextStepClick} />

      {/* Main Action Button */}
      <VStack space="sm">
        <Button
          onPress={handleContinueToDashboard}
          className="w-full bg-blue-600 hover:bg-blue-700"
          size="lg"
        >
          <ButtonText className="text-white font-medium text-lg">Go to Dashboard</ButtonText>
          <ButtonIcon as={ArrowRight} className="text-white ml-2" />
        </Button>

        <Text className="text-center text-gray-500 text-sm">
          You can modify your profile settings anytime from your dashboard
        </Text>
      </VStack>
    </VStack>
  );
};
