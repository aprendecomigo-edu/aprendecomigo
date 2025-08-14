import {
  Eye,
  Edit,
  Star,
  MapPin,
  Globe,
  Clock,
  DollarSign,
  BookOpen,
  GraduationCap,
  Users,
  Calendar,
  Award,
  CheckCircle2,
  AlertTriangle,
  ExternalLink,
  Share2,
  Smartphone,
  Monitor,
  TrendingUp,
  Target,
  MessageCircle,
  Video,
} from 'lucide-react-native';
import React, { useState } from 'react';
import { Platform, Dimensions } from 'react-native';

import { Avatar, AvatarFallbackText, AvatarImage } from '@/components/ui/avatar';
import { Badge, BadgeText } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Pressable } from '@/components/ui/pressable';
import { Progress, ProgressFilledTrack } from '@/components/ui/progress';
import { ScrollView } from '@/components/ui/scroll-view';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

interface ProfilePreviewStepProps {
  formData: any; // Complete wizard form data
  onFormDataChange: (data: any) => void;
  validationErrors?: Record<string, string[]>;
  isLoading?: boolean;
  completionData?: any;
  onStepNavigation?: (stepIndex: number) => void;
}

const { width: screenWidth } = Dimensions.get('window');
const isMobile = Platform.OS !== 'web' || screenWidth < 768;

const STEP_INDICES = {
  'basic-info': 0,
  biography: 1,
  education: 2,
  subjects: 3,
  rates: 4,
  availability: 5,
};

export const ProfilePreviewStep: React.FC<ProfilePreviewStepProps> = ({
  formData,
  onFormDataChange,
  validationErrors = {},
  isLoading = false,
  completionData,
  onStepNavigation,
}) => {
  const [previewMode, setPreviewMode] = useState<'desktop' | 'mobile'>('desktop');
  const [showCompletionDetails, setShowCompletionDetails] = useState(false);

  const currency = formData.rate_structure?.currency === 'EUR' ? '€' : '$';

  const handleEditSection = (section: string) => {
    const stepIndex = STEP_INDICES[section as keyof typeof STEP_INDICES];
    if (onStepNavigation && stepIndex !== undefined) {
      onStepNavigation(stepIndex);
    }
  };

  const getExpertiseColor = (level: string) => {
    switch (level) {
      case 'beginner':
        return 'bg-blue-100 text-blue-800';
      case 'intermediate':
        return 'bg-yellow-100 text-yellow-800';
      case 'advanced':
        return 'bg-orange-100 text-orange-800';
      case 'expert':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getTotalWeeklyHours = () => {
    if (!formData.weekly_availability) return 0;

    let totalMinutes = 0;
    Object.values(formData.weekly_availability).forEach((daySlots: any) => {
      daySlots.forEach((slot: any) => {
        const start = new Date(`2000-01-01T${slot.start_time}`);
        const end = new Date(`2000-01-01T${slot.end_time}`);
        const diffMs = end.getTime() - start.getTime();
        totalMinutes += diffMs / (1000 * 60);
      });
    });

    return Math.round((totalMinutes / 60) * 10) / 10;
  };

  const getCompletionScore = () => {
    return completionData?.completion_percentage || 0;
  };

  const getMissingCritical = () => {
    return completionData?.missing_critical || [];
  };

  const ProfileCard = () => (
    <Card className="overflow-hidden">
      {/* Header with Photo and Basic Info */}
      <Box className="bg-gradient-to-r from-blue-600 to-blue-700 p-6">
        <VStack space="md">
          <HStack space="md" className="items-start">
            <Avatar size="xl" className="border-4 border-white">
              {formData.profile_photo ? (
                <AvatarImage source={{ uri: formData.profile_photo }} alt="Profile photo" />
              ) : (
                <AvatarFallbackText className="text-white">
                  {`${formData.first_name?.[0] || 'T'} ${formData.last_name?.[0] || 'T'}`}
                </AvatarFallbackText>
              )}
            </Avatar>

            <VStack space="xs" className="flex-1">
              <Heading size="lg" className="text-white">
                {formData.first_name} {formData.last_name}
              </Heading>

              <Text className="text-blue-100 font-medium">{formData.professional_title}</Text>

              <HStack space="md" className="items-center mt-2">
                <HStack space="xs" className="items-center">
                  <Icon as={MapPin} size={14} className="text-blue-200" />
                  <Text className="text-blue-100 text-sm">
                    {formData.location?.city}, {formData.location?.country}
                  </Text>
                </HStack>

                <HStack space="xs" className="items-center">
                  <Icon as={Globe} size={14} className="text-blue-200" />
                  <Text className="text-blue-100 text-sm">
                    {formData.languages?.join(', ') || 'Languages not set'}
                  </Text>
                </HStack>
              </HStack>

              <HStack space="xs" className="items-center mt-1">
                {[...Array(5)].map((_, i) => (
                  <Icon
                    key={i}
                    as={Star}
                    size={14}
                    className="text-yellow-300"
                    fill="currentColor"
                  />
                ))}
                <Text className="text-blue-100 text-sm ml-2">5.0 (New tutor)</Text>
              </HStack>
            </VStack>

            <VStack space="xs" className="items-end">
              <HStack space="xs" className="items-center">
                <Text className="text-2xl font-bold text-white">
                  {currency}
                  {formData.rate_structure?.individual_rate || 0}
                </Text>
                <Text className="text-blue-200">/hour</Text>
              </HStack>

              {formData.rate_structure?.trial_lesson_rate && (
                <Badge className="bg-yellow-400">
                  <BadgeText className="text-yellow-900 text-xs">
                    Trial: {currency}
                    {formData.rate_structure.trial_lesson_rate}
                  </BadgeText>
                </Badge>
              )}
            </VStack>
          </HStack>

          <Text className="text-blue-100 leading-relaxed">
            {formData.introduction || 'Introduction not set'}
          </Text>
        </VStack>
      </Box>

      {/* Quick Stats */}
      <Box className="border-b border-gray-200 p-4">
        <HStack space="md" className="justify-around">
          <VStack space="xs" className="items-center">
            <Icon as={Clock} size={20} className="text-gray-600" />
            <Text className="text-sm font-medium text-gray-900">{getTotalWeeklyHours()}h</Text>
            <Text className="text-xs text-gray-500">Available</Text>
          </VStack>

          <VStack space="xs" className="items-center">
            <Icon as={BookOpen} size={20} className="text-gray-600" />
            <Text className="text-sm font-medium text-gray-900">
              {formData.teaching_subjects?.length || 0}
            </Text>
            <Text className="text-xs text-gray-500">Subjects</Text>
          </VStack>

          <VStack space="xs" className="items-center">
            <Icon as={GraduationCap} size={20} className="text-gray-600" />
            <Text className="text-sm font-medium text-gray-900">
              {formData.degrees?.length || 0}
            </Text>
            <Text className="text-xs text-gray-500">Degrees</Text>
          </VStack>

          <VStack space="xs" className="items-center">
            <Icon as={Calendar} size={20} className="text-gray-600" />
            <Text className="text-sm font-medium text-gray-900">
              {formData.years_experience || 0}+
            </Text>
            <Text className="text-xs text-gray-500">Years</Text>
          </VStack>
        </HStack>
      </Box>

      {/* Action Buttons */}
      <Box className="p-4">
        <HStack space="sm">
          <Button className="flex-1 bg-blue-600">
            <ButtonIcon as={MessageCircle} className="text-white mr-2" />
            <ButtonText className="text-white">Send Message</ButtonText>
          </Button>

          <Button variant="outline" className="flex-1">
            <ButtonIcon as={Video} className="text-gray-600 mr-2" />
            <ButtonText>Book Trial</ButtonText>
          </Button>
        </HStack>
      </Box>
    </Card>
  );

  return (
    <ScrollView className="flex-1">
      <Box className="p-6 max-w-6xl mx-auto">
        <VStack space="lg">
          {/* Header */}
          <VStack space="sm">
            <Heading size="xl" className="text-gray-900">
              Profile Preview
            </Heading>
            <Text className="text-gray-600">
              See how your profile appears to students. You can make changes by editing individual
              sections.
            </Text>
          </VStack>

          {/* Completion Score */}
          <Card
            className={`border-l-4 ${
              getCompletionScore() >= 90
                ? 'border-l-green-500 bg-green-50'
                : getCompletionScore() >= 70
                ? 'border-l-yellow-500 bg-yellow-50'
                : 'border-l-red-500 bg-red-50'
            }`}
          >
            <VStack space="md" className="p-6">
              <HStack className="items-center justify-between">
                <HStack space="sm" className="items-center">
                  <Icon
                    as={getCompletionScore() >= 90 ? CheckCircle2 : AlertTriangle}
                    size={20}
                    className={
                      getCompletionScore() >= 90
                        ? 'text-green-600'
                        : getCompletionScore() >= 70
                        ? 'text-yellow-600'
                        : 'text-red-600'
                    }
                  />
                  <Heading
                    size="md"
                    className={
                      getCompletionScore() >= 90
                        ? 'text-green-900'
                        : getCompletionScore() >= 70
                        ? 'text-yellow-900'
                        : 'text-red-900'
                    }
                  >
                    Profile Completion: {getCompletionScore()}%
                  </Heading>
                </HStack>

                <Button
                  size="sm"
                  variant="ghost"
                  onPress={() => setShowCompletionDetails(!showCompletionDetails)}
                >
                  <ButtonText>{showCompletionDetails ? 'Hide' : 'Show'} Details</ButtonText>
                </Button>
              </HStack>

              <Progress value={getCompletionScore()} className="h-3">
                <ProgressFilledTrack
                  className={
                    getCompletionScore() >= 90
                      ? 'bg-green-600'
                      : getCompletionScore() >= 70
                      ? 'bg-yellow-600'
                      : 'bg-red-600'
                  }
                />
              </Progress>

              {showCompletionDetails && (
                <VStack space="sm" className="mt-4">
                  {getMissingCritical().length > 0 && (
                    <VStack space="xs">
                      <Text className="font-medium text-red-800">
                        Critical Missing Information:
                      </Text>
                      {getMissingCritical().map((item: string, index: number) => (
                        <Text key={index} className="text-red-700 text-sm">
                          • {item}
                        </Text>
                      ))}
                    </VStack>
                  )}

                  {completionData?.recommendations && (
                    <VStack space="xs">
                      <Text className="font-medium text-gray-800">Recommendations:</Text>
                      {completionData.recommendations.map((rec: any, index: number) => (
                        <Text key={index} className="text-gray-700 text-sm">
                          • {rec.text}
                        </Text>
                      ))}
                    </VStack>
                  )}
                </VStack>
              )}
            </VStack>
          </Card>

          {/* Preview Mode Toggle */}
          <Card>
            <VStack space="md" className="p-6">
              <HStack className="items-center justify-between">
                <Heading size="md" className="text-gray-900">
                  Preview Mode
                </Heading>

                <HStack space="sm">
                  <Button
                    size="sm"
                    variant={previewMode === 'desktop' ? 'solid' : 'outline'}
                    onPress={() => setPreviewMode('desktop')}
                  >
                    <ButtonIcon
                      as={Monitor}
                      className={
                        previewMode === 'desktop' ? 'text-white mr-2' : 'text-gray-600 mr-2'
                      }
                    />
                    <ButtonText
                      className={previewMode === 'desktop' ? 'text-white' : 'text-gray-600'}
                    >
                      Desktop
                    </ButtonText>
                  </Button>

                  <Button
                    size="sm"
                    variant={previewMode === 'mobile' ? 'solid' : 'outline'}
                    onPress={() => setPreviewMode('mobile')}
                  >
                    <ButtonIcon
                      as={Smartphone}
                      className={
                        previewMode === 'mobile' ? 'text-white mr-2' : 'text-gray-600 mr-2'
                      }
                    />
                    <ButtonText
                      className={previewMode === 'mobile' ? 'text-white' : 'text-gray-600'}
                    >
                      Mobile
                    </ButtonText>
                  </Button>
                </HStack>
              </HStack>

              <Text className="text-gray-600 text-sm">
                See how your profile looks on different devices
              </Text>
            </VStack>
          </Card>

          {/* Profile Preview */}
          <Box className={`mx-auto ${previewMode === 'mobile' ? 'max-w-sm' : 'max-w-2xl w-full'}`}>
            <ProfileCard />
          </Box>

          {/* Detailed Sections with Edit Options */}
          <VStack space="md">
            {/* About Section */}
            <Card>
              <VStack space="md" className="p-6">
                <HStack className="items-center justify-between">
                  <Heading size="md" className="text-gray-900">
                    About {formData.first_name}
                  </Heading>
                  <Button
                    size="sm"
                    variant="outline"
                    onPress={() => handleEditSection('biography')}
                  >
                    <ButtonIcon as={Edit} className="text-gray-600 mr-1" />
                    <ButtonText>Edit</ButtonText>
                  </Button>
                </HStack>

                <Text className="text-gray-700 leading-relaxed">
                  {formData.professional_bio || 'Professional biography not set'}
                </Text>

                {formData.teaching_philosophy && (
                  <VStack space="xs">
                    <Text className="font-medium text-gray-900">Teaching Philosophy:</Text>
                    <Text className="text-gray-700">{formData.teaching_philosophy}</Text>
                  </VStack>
                )}
              </VStack>
            </Card>

            {/* Teaching Subjects */}
            <Card>
              <VStack space="md" className="p-6">
                <HStack className="items-center justify-between">
                  <Heading size="md" className="text-gray-900">
                    Teaching Subjects
                  </Heading>
                  <Button size="sm" variant="outline" onPress={() => handleEditSection('subjects')}>
                    <ButtonIcon as={Edit} className="text-gray-600 mr-1" />
                    <ButtonText>Edit</ButtonText>
                  </Button>
                </HStack>

                {formData.teaching_subjects?.length > 0 ? (
                  <VStack space="sm">
                    {formData.teaching_subjects.map((subject: any, index: number) => (
                      <Card key={index} className="bg-gray-50">
                        <VStack space="sm" className="p-4">
                          <HStack className="items-center justify-between">
                            <Text className="font-semibold text-gray-900">{subject.subject}</Text>
                            <Badge className={getExpertiseColor(subject.expertise_level)}>
                              <BadgeText className="capitalize">
                                {subject.expertise_level}
                              </BadgeText>
                            </Badge>
                          </HStack>

                          <HStack space="md" className="items-center">
                            <HStack space="xs" className="items-center">
                              <Icon as={Users} size={14} className="text-gray-500" />
                              <Text className="text-sm text-gray-600">
                                {subject.grade_levels?.join(', ')}
                              </Text>
                            </HStack>

                            <HStack space="xs" className="items-center">
                              <Icon as={Calendar} size={14} className="text-gray-500" />
                              <Text className="text-sm text-gray-600">
                                {subject.years_teaching}+ years
                              </Text>
                            </HStack>
                          </HStack>
                        </VStack>
                      </Card>
                    ))}
                  </VStack>
                ) : (
                  <Text className="text-gray-600 italic">No subjects added yet</Text>
                )}
              </VStack>
            </Card>

            {/* Education */}
            <Card>
              <VStack space="md" className="p-6">
                <HStack className="items-center justify-between">
                  <Heading size="md" className="text-gray-900">
                    Education & Qualifications
                  </Heading>
                  <Button
                    size="sm"
                    variant="outline"
                    onPress={() => handleEditSection('education')}
                  >
                    <ButtonIcon as={Edit} className="text-gray-600 mr-1" />
                    <ButtonText>Edit</ButtonText>
                  </Button>
                </HStack>

                {formData.degrees?.length > 0 ? (
                  <VStack space="sm">
                    {formData.degrees.map((degree: any, index: number) => (
                      <HStack key={index} space="sm" className="items-start">
                        <Icon as={GraduationCap} size={20} className="text-blue-600 mt-1" />
                        <VStack space="xs" className="flex-1">
                          <Text className="font-semibold text-gray-900">
                            {degree.degree_type} in {degree.field_of_study}
                          </Text>
                          <Text className="text-gray-600">
                            {degree.institution} • {degree.graduation_year}
                          </Text>
                        </VStack>
                      </HStack>
                    ))}
                  </VStack>
                ) : (
                  <Text className="text-gray-600 italic">No education information added yet</Text>
                )}
              </VStack>
            </Card>

            {/* Pricing */}
            <Card>
              <VStack space="md" className="p-6">
                <HStack className="items-center justify-between">
                  <Heading size="md" className="text-gray-900">
                    Pricing & Packages
                  </Heading>
                  <Button size="sm" variant="outline" onPress={() => handleEditSection('rates')}>
                    <ButtonIcon as={Edit} className="text-gray-600 mr-1" />
                    <ButtonText>Edit</ButtonText>
                  </Button>
                </HStack>

                <VStack space="sm">
                  <HStack className="items-center justify-between">
                    <Text className="text-gray-700">Individual lessons:</Text>
                    <Text className="font-semibold text-gray-900">
                      {currency}
                      {formData.rate_structure?.individual_rate || 0}/hour
                    </Text>
                  </HStack>

                  {formData.rate_structure?.trial_lesson_rate && (
                    <HStack className="items-center justify-between">
                      <Text className="text-gray-700">Trial lesson:</Text>
                      <Text className="font-semibold text-gray-900">
                        {currency}
                        {formData.rate_structure.trial_lesson_rate}/hour
                      </Text>
                    </HStack>
                  )}

                  {formData.rate_structure?.group_rate && (
                    <HStack className="items-center justify-between">
                      <Text className="text-gray-700">Group lessons:</Text>
                      <Text className="font-semibold text-gray-900">
                        {currency}
                        {formData.rate_structure.group_rate}/student/hour
                      </Text>
                    </HStack>
                  )}
                </VStack>

                {formData.rate_structure?.package_deals?.length > 0 && (
                  <VStack space="sm" className="mt-4">
                    <Text className="font-medium text-gray-900">Package Deals:</Text>
                    {formData.rate_structure.package_deals.map(
                      (packageDeal: any, index: number) => (
                        <HStack
                          key={index}
                          className="items-center justify-between bg-gray-50 p-3 rounded-lg"
                        >
                          <VStack space="xs">
                            <Text className="font-medium text-gray-900">{packageDeal.name}</Text>
                            <Text className="text-sm text-gray-600">
                              {packageDeal.sessions} sessions
                            </Text>
                          </VStack>
                          <VStack space="xs" className="items-end">
                            <Text className="font-semibold text-gray-900">
                              {currency}
                              {packageDeal.price}
                            </Text>
                            <Badge className="bg-green-100">
                              <BadgeText className="text-green-800 text-xs">
                                {packageDeal.discount_percentage}% OFF
                              </BadgeText>
                            </Badge>
                          </VStack>
                        </HStack>
                      )
                    )}
                  </VStack>
                )}
              </VStack>
            </Card>

            {/* Availability */}
            <Card>
              <VStack space="md" className="p-6">
                <HStack className="items-center justify-between">
                  <Heading size="md" className="text-gray-900">
                    Availability
                  </Heading>
                  <Button
                    size="sm"
                    variant="outline"
                    onPress={() => handleEditSection('availability')}
                  >
                    <ButtonIcon as={Edit} className="text-gray-600 mr-1" />
                    <ButtonText>Edit</ButtonText>
                  </Button>
                </HStack>

                <HStack className="items-center justify-between">
                  <Text className="text-gray-700">Total weekly hours:</Text>
                  <Text className="font-semibold text-gray-900">{getTotalWeeklyHours()} hours</Text>
                </HStack>

                <HStack className="items-center justify-between">
                  <Text className="text-gray-700">Timezone:</Text>
                  <Text className="font-semibold text-gray-900">
                    {formData.time_zone || 'Not set'}
                  </Text>
                </HStack>

                <HStack className="items-center justify-between">
                  <Text className="text-gray-700">Booking notice:</Text>
                  <Text className="font-semibold text-gray-900">
                    {formData.booking_preferences?.min_notice_hours
                      ? `${formData.booking_preferences.min_notice_hours} hours`
                      : 'Not set'}
                  </Text>
                </HStack>
              </VStack>
            </Card>
          </VStack>

          {/* SEO Preview */}
          <Card>
            <VStack space="md" className="p-6">
              <HStack className="items-center justify-between">
                <Heading size="md" className="text-gray-900">
                  Search Preview
                </Heading>
                <Icon as={TrendingUp} size={20} className="text-blue-600" />
              </HStack>

              <Text className="text-gray-600 text-sm">
                How your profile might appear in search results
              </Text>

              <Card className="bg-gray-50 border-l-4 border-l-blue-500">
                <VStack space="sm" className="p-4">
                  <Text className="text-blue-600 text-lg font-medium">
                    {formData.first_name} {formData.last_name} - {formData.professional_title}
                  </Text>
                  <Text className="text-green-700 text-sm">
                    aprende-comigo.com/school/{formData.first_name?.toLowerCase()}-
                    {formData.last_name?.toLowerCase()}
                  </Text>
                  <Text className="text-gray-700 text-sm">
                    {formData.introduction ||
                      formData.professional_bio?.substring(0, 160) ||
                      'Professional tutor offering personalized learning experiences...'}
                  </Text>
                  <HStack space="sm" className="mt-2">
                    <Badge className="bg-blue-100">
                      <BadgeText className="text-blue-800">
                        {currency}
                        {formData.rate_structure?.individual_rate}/hr
                      </BadgeText>
                    </Badge>
                    <Badge className="bg-gray-100">
                      <BadgeText className="text-gray-800">
                        {formData.teaching_subjects?.length || 0} subjects
                      </BadgeText>
                    </Badge>
                    <Badge className="bg-yellow-100">
                      <BadgeText className="text-yellow-800">⭐ 5.0 (New)</BadgeText>
                    </Badge>
                  </HStack>
                </VStack>
              </Card>
            </VStack>
          </Card>

          {/* Final Actions */}
          <Card className="border-l-4 border-l-green-500 bg-green-50">
            <VStack space="md" className="p-6">
              <HStack space="sm" className="items-center">
                <Icon as={Target} size={20} className="text-green-600" />
                <Heading size="md" className="text-green-900">
                  Ready to Go Live?
                </Heading>
              </HStack>

              <Text className="text-green-800">
                Your profile looks great! When you complete the wizard, your profile will be
                published and students will be able to find and book sessions with you.
              </Text>

              <HStack space="sm">
                <Button variant="outline" className="flex-1">
                  <ButtonIcon as={Share2} className="text-gray-600 mr-2" />
                  <ButtonText>Share Preview</ButtonText>
                </Button>

                <Button className="flex-1 bg-green-600">
                  <ButtonIcon as={CheckCircle2} className="text-white mr-2" />
                  <ButtonText className="text-white">Publish Profile</ButtonText>
                </Button>
              </HStack>
            </VStack>
          </Card>
        </VStack>
      </Box>
    </ScrollView>
  );
};
