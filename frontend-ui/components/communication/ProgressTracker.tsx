import React, { useMemo } from 'react';
import { 
  CheckCircleIcon, 
  CircleIcon, 
  TrophyIcon, 
  StarIcon,
  ArrowRightIcon,
  ClockIcon
} from 'lucide-react-native';

import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { Badge } from '@/components/ui/badge';

import { useTeacherOnboarding, useOnboardingHelpers } from '@/hooks/useTeacherOnboarding';
import { TeacherOnboardingProgress } from '@/api/communicationApi';

interface ProgressTrackerProps {
  progress?: TeacherOnboardingProgress;
  showMilestones?: boolean;
  showNextSteps?: boolean;
  onStepClick?: (step: number) => void;
  compact?: boolean;
}

const ProgressTracker: React.FC<ProgressTrackerProps> = ({
  progress,
  showMilestones = true,
  showNextSteps = true,
  onStepClick,
  compact = false,
}) => {
  const { getStepName, getMilestoneMessage, getProgressMessage, getNextStepHint } = useOnboardingHelpers();

  const steps = useMemo(() => [
    { number: 1, name: 'Basic Information', description: 'Name, contact details, and profile photo' },
    { number: 2, name: 'Teaching Subjects', description: 'Select the subjects you teach' },
    { number: 3, name: 'Grade Levels', description: 'Choose the grade levels you work with' },
    { number: 4, name: 'Availability', description: 'Set your teaching schedule and preferences' },
    { number: 5, name: 'Rates & Compensation', description: 'Define your hourly rates and payment terms' },
    { number: 6, name: 'Credentials', description: 'Add your education and teaching experience' },
    { number: 7, name: 'Profile Marketing', description: 'Create your bio and teaching philosophy' },
    { number: 8, name: 'Review & Submit', description: 'Final review and profile activation' },
  ], []);

  const milestones = useMemo(() => [
    { 
      id: 'basic_info_complete', 
      name: 'Profile Foundation', 
      description: 'Basic information completed',
      requiredSteps: [1],
      icon: 'user'
    },
    { 
      id: 'subjects_selected', 
      name: 'Teaching Expertise', 
      description: 'Subjects and grade levels defined',
      requiredSteps: [2, 3],
      icon: 'book'
    },
    { 
      id: 'availability_set', 
      name: 'Schedule Ready', 
      description: 'Availability and rates configured',
      requiredSteps: [4, 5],
      icon: 'calendar'
    },
    { 
      id: 'credentials_added', 
      name: 'Credentials Verified', 
      description: 'Education and experience documented',
      requiredSteps: [6],
      icon: 'award'
    },
    { 
      id: 'profile_complete', 
      name: 'Profile Master', 
      description: 'Complete teacher profile ready',
      requiredSteps: [7, 8],
      icon: 'star'
    },
  ], []);

  const getStepStatus = (stepNumber: number) => {
    if (!progress) return 'pending';
    
    if (progress.completed_steps.includes(stepNumber)) return 'completed';
    if (progress.current_step === stepNumber) return 'current';
    if (stepNumber < progress.current_step) return 'completed';
    return 'pending';
  };

  const getMilestoneStatus = (milestone: typeof milestones[0]) => {
    if (!progress) return 'locked';
    
    if (progress.milestones_achieved.includes(milestone.id)) return 'achieved';
    
    const allRequiredCompleted = milestone.requiredSteps.every(step => 
      progress.completed_steps.includes(step)
    );
    
    if (allRequiredCompleted) return 'available';
    return 'locked';
  };

  const progressPercentage = progress ? (progress.completed_steps.length / progress.total_steps) * 100 : 0;

  if (compact) {
    return (
      <Card className="p-4">
        <VStack space="sm">
          <HStack className="justify-between items-center">
            <Text className="font-semibold text-gray-900">Profile Progress</Text>
            <Text className="text-sm text-gray-600">
              {Math.round(progressPercentage)}% Complete
            </Text>
          </HStack>
          
          <Box className="w-full bg-gray-200 rounded-full h-2">
            <Box 
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progressPercentage}%` }}
            />
          </Box>
          
          {progress && (
            <Text className="text-xs text-gray-500">
              Step {progress.current_step} of {progress.total_steps}: {getStepName(progress.current_step)}
            </Text>
          )}
        </VStack>
      </Card>
    );
  }

  return (
    <VStack space="lg">
      {/* Overall Progress */}
      <Card className="p-6">
        <VStack space="md">
          <HStack className="justify-between items-center">
            <Heading size="lg" className="text-gray-900">
              Profile Setup Progress
            </Heading>
            <Badge className={`${
              progressPercentage === 100 ? 'bg-green-100 text-green-800' :
              progressPercentage >= 50 ? 'bg-blue-100 text-blue-800' :
              'bg-yellow-100 text-yellow-800'
            }`}>
              <Text className="font-semibold">
                {Math.round(progressPercentage)}% Complete
              </Text>
            </Badge>
          </HStack>
          
          <Box className="w-full bg-gray-200 rounded-full h-3">
            <Box 
              className="bg-gradient-to-r from-blue-500 to-purple-600 h-3 rounded-full transition-all duration-500"
              style={{ width: `${progressPercentage}%` }}
            />
          </Box>
          
          {progress && (
            <Text className="text-gray-600 text-center">
              {getProgressMessage(progress)}
            </Text>
          )}
        </VStack>
      </Card>

      {/* Step Progress */}
      <Card className="p-6">
        <VStack space="md">
          <Heading size="md" className="text-gray-900">
            Setup Steps
          </Heading>
          
          <VStack space="sm">
            {steps.map((step) => {
              const status = getStepStatus(step.number);
              const isClickable = onStepClick && (status === 'completed' || status === 'current');
              
              return (
                <Box
                  key={step.number}
                  className={`p-4 rounded-lg border transition-all ${
                    status === 'current' ? 'border-blue-200 bg-blue-50' :
                    status === 'completed' ? 'border-green-200 bg-green-50' :
                    'border-gray-200 bg-gray-50'
                  } ${isClickable ? 'hover:shadow-md cursor-pointer' : ''}`}
                  onTouchEnd={isClickable ? () => onStepClick!(step.number) : undefined}
                >
                  <HStack space="md" className="items-center">
                    <Box className="flex-shrink-0">
                      {status === 'completed' ? (
                        <Icon as={CheckCircleIcon} size="md" className="text-green-600" />
                      ) : status === 'current' ? (
                        <Box className="w-6 h-6 border-2 border-blue-600 rounded-full bg-blue-100 items-center justify-center">
                          <Text className="text-xs font-bold text-blue-600">
                            {step.number}
                          </Text>
                        </Box>
                      ) : (
                        <Icon as={CircleIcon} size="md" className="text-gray-400" />
                      )}
                    </Box>
                    
                    <VStack space="xs" className="flex-1">
                      <HStack className="justify-between items-center">
                        <Text className={`font-semibold ${
                          status === 'current' ? 'text-blue-900' :
                          status === 'completed' ? 'text-green-900' :
                          'text-gray-600'
                        }`}>
                          {step.name}
                        </Text>
                        
                        {status === 'current' && (
                          <Badge className="bg-blue-100 text-blue-800">
                            <Text className="text-xs">Current</Text>
                          </Badge>
                        )}
                      </HStack>
                      
                      <Text className={`text-sm ${
                        status === 'current' ? 'text-blue-700' :
                        status === 'completed' ? 'text-green-700' :
                        'text-gray-500'
                      }`}>
                        {step.description}
                      </Text>
                    </VStack>
                    
                    {isClickable && (
                      <Icon as={ArrowRightIcon} size="sm" className="text-gray-400" />
                    )}
                  </HStack>
                </Box>
              );
            })}
          </VStack>
        </VStack>
      </Card>

      {/* Milestones */}
      {showMilestones && (
        <Card className="p-6">
          <VStack space="md">
            <HStack space="sm" className="items-center">
              <Icon as={TrophyIcon} size="sm" className="text-yellow-600" />
              <Heading size="md" className="text-gray-900">
                Achievement Milestones
              </Heading>
            </HStack>
            
            <VStack space="sm">
              {milestones.map((milestone) => {
                const status = getMilestoneStatus(milestone);
                
                return (
                  <HStack
                    key={milestone.id}
                    space="md"
                    className={`p-3 rounded-lg border ${
                      status === 'achieved' ? 'border-yellow-200 bg-yellow-50' :
                      status === 'available' ? 'border-blue-200 bg-blue-50' :
                      'border-gray-200 bg-gray-50'
                    }`}
                  >
                    <Box className="flex-shrink-0">
                      {status === 'achieved' ? (
                        <Icon as={StarIcon} size="sm" className="text-yellow-600" />
                      ) : status === 'available' ? (
                        <Icon as={TrophyIcon} size="sm" className="text-blue-600" />
                      ) : (
                        <Icon as={ClockIcon} size="sm" className="text-gray-400" />
                      )}
                    </Box>
                    
                    <VStack space="xs" className="flex-1">
                      <Text className={`font-medium ${
                        status === 'achieved' ? 'text-yellow-900' :
                        status === 'available' ? 'text-blue-900' :
                        'text-gray-600'
                      }`}>
                        {milestone.name}
                      </Text>
                      
                      <Text className={`text-sm ${
                        status === 'achieved' ? 'text-yellow-700' :
                        status === 'available' ? 'text-blue-700' :
                        'text-gray-500'
                      }`}>
                        {milestone.description}
                      </Text>
                    </VStack>
                    
                    {status === 'achieved' && (
                      <Badge className="bg-yellow-100 text-yellow-800">
                        <Text className="text-xs">Achieved!</Text>
                      </Badge>
                    )}
                  </HStack>
                );
              })}
            </VStack>
          </VStack>
        </Card>
      )}

      {/* Next Steps */}
      {showNextSteps && progress && progress.current_step <= progress.total_steps && (
        <Card className="p-6 bg-gradient-to-r from-blue-50 to-purple-50 border-blue-200">
          <VStack space="md">
            <HStack space="sm" className="items-center">
              <Icon as={ArrowRightIcon} size="sm" className="text-blue-600" />
              <Heading size="md" className="text-blue-900">
                Next Steps
              </Heading>
            </HStack>
            
            <VStack space="sm">
              <Text className="text-blue-800 font-medium">
                Complete: {getStepName(progress.current_step)}
              </Text>
              
              <Text className="text-blue-700 text-sm">
                {getNextStepHint(progress.current_step)}
              </Text>
              
              {onStepClick && (
                <Button 
                  onPress={() => onStepClick(progress.current_step)}
                  className="bg-blue-600 mt-2"
                  size="sm"
                >
                  <ButtonText className="text-white">Continue Setup</ButtonText>
                </Button>
              )}
            </VStack>
          </VStack>
        </Card>
      )}
    </VStack>
  );
};

export default ProgressTracker;