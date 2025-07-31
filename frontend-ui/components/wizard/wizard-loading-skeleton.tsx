import React from 'react';

import { Box } from '@/components/ui/box';
import { Card } from '@/components/ui/card';
import { VStack } from '@/components/ui/vstack';
import { HStack } from '@/components/ui/hstack';
import { Skeleton } from '@/components/ui/skeleton';

interface WizardLoadingSkeletonProps {
  showNavigation?: boolean;
  animated?: boolean;
}

const NavigationSkeleton: React.FC<{ animated: boolean }> = ({ animated }) => (
  <Box className="bg-white border-r border-gray-200 w-80">
    <VStack space="xs" className="p-4">
      {/* Header */}
      <Skeleton className={`h-4 w-32 mb-2 ${animated ? 'animate-pulse' : ''}`} />
      
      {/* Navigation Steps */}
      {Array.from({ length: 7 }).map((_, index) => (
        <Box key={index} className="w-full">
          <Card className="p-3 border-gray-200">
            <HStack space="sm" className="items-start">
              {/* Step Icon */}
              <Skeleton className={`h-5 w-5 rounded-full mt-0.5 ${animated ? 'animate-pulse' : ''}`} />
              
              {/* Step Content */}
              <VStack space="xs" className="flex-1">
                <HStack className="items-center justify-between w-full">
                  <Skeleton className={`h-4 w-24 ${animated ? 'animate-pulse' : ''}`} />
                  <Skeleton className={`h-2 w-2 rounded-full ${animated ? 'animate-pulse' : ''}`} />
                </HStack>
                <Skeleton className={`h-3 w-full ${animated ? 'animate-pulse' : ''}`} />
                
                {/* Progress Bar */}
                {index % 3 === 1 && (
                  <Box className="w-full bg-gray-200 rounded-full h-1.5 mt-1">
                    <Skeleton className={`h-1.5 rounded-full w-2/3 ${animated ? 'animate-pulse' : ''}`} />
                  </Box>
                )}
              </VStack>
            </HStack>
          </Card>
          
          {/* Connector Line */}
          {index < 6 && (
            <Box className="ml-8 my-1">
              <Skeleton className={`h-6 w-px ${animated ? 'animate-pulse' : ''}`} />
            </Box>
          )}
        </Box>
      ))}
      
      {/* Progress Summary */}
      <Card className="p-3 bg-gray-50 mt-4 w-full">
        <VStack space="xs">
          <HStack className="items-center justify-between">
            <Skeleton className={`h-4 w-20 ${animated ? 'animate-pulse' : ''}`} />
            <Skeleton className={`h-4 w-8 ${animated ? 'animate-pulse' : ''}`} />
          </HStack>
          <Skeleton className={`h-2 w-full rounded-full ${animated ? 'animate-pulse' : ''}`} />
        </VStack>
      </Card>
    </VStack>
  </Box>
);

const HeaderSkeleton: React.FC<{ animated: boolean }> = ({ animated }) => (
  <Box className="bg-white border-b border-gray-200 px-4 py-4">
    <VStack space="md">
      {/* Top Navigation */}
      <HStack className="items-center justify-between">
        <HStack space="sm" className="items-center">
          <Skeleton className={`h-5 w-5 ${animated ? 'animate-pulse' : ''}`} />
          <Skeleton className={`h-4 w-12 ${animated ? 'animate-pulse' : ''}`} />
        </HStack>
        
        <HStack space="sm" className="items-center">
          <Skeleton className={`h-8 w-20 rounded ${animated ? 'animate-pulse' : ''}`} />
          <Skeleton className={`h-8 w-8 rounded-full ${animated ? 'animate-pulse' : ''}`} />
        </HStack>
      </HStack>

      {/* Progress Bar */}
      <VStack space="xs">
        <HStack className="items-center justify-between">
          <Skeleton className={`h-4 w-20 ${animated ? 'animate-pulse' : ''}`} />
          <Skeleton className={`h-4 w-16 ${animated ? 'animate-pulse' : ''}`} />
        </HStack>
        <Skeleton className={`h-2 w-full rounded-full ${animated ? 'animate-pulse' : ''}`} />
      </VStack>

      {/* Current Step Info */}
      <VStack space="xs">
        <HStack space="sm" className="items-center">
          <Skeleton className={`h-5 w-5 ${animated ? 'animate-pulse' : ''}`} />
          <Skeleton className={`h-6 w-40 ${animated ? 'animate-pulse' : ''}`} />
          <Skeleton className={`h-5 w-12 rounded-full ${animated ? 'animate-pulse' : ''}`} />
        </HStack>
        <Skeleton className={`h-4 w-3/4 ${animated ? 'animate-pulse' : ''}`} />
      </VStack>
    </VStack>
  </Box>
);

const ContentSkeleton: React.FC<{ animated: boolean }> = ({ animated }) => (
  <Box className="flex-1 p-6">
    <VStack space="lg">
      {/* Form Section */}
      <VStack space="md">
        {/* Section Header */}
        <VStack space="xs">
          <Skeleton className={`h-5 w-32 ${animated ? 'animate-pulse' : ''}`} />
          <Skeleton className={`h-4 w-full ${animated ? 'animate-pulse' : ''}`} />
        </VStack>

        {/* Form Fields */}
        <VStack space="md">
          {Array.from({ length: 4 }).map((_, index) => (
            <VStack key={index} space="xs">
              <Skeleton className={`h-4 w-24 ${animated ? 'animate-pulse' : ''}`} />
              <Skeleton className={`h-10 w-full rounded-lg ${animated ? 'animate-pulse' : ''}`} />
            </VStack>
          ))}
        </VStack>
      </VStack>

      {/* Additional Content */}
      <VStack space="sm">
        {Array.from({ length: 3 }).map((_, index) => (
          <Card key={index} className="p-4">
            <HStack space="sm" className="items-center">
              <Skeleton className={`h-8 w-8 rounded ${animated ? 'animate-pulse' : ''}`} />
              <VStack space="xs" className="flex-1">
                <Skeleton className={`h-4 w-full ${animated ? 'animate-pulse' : ''}`} />
                <Skeleton className={`h-3 w-2/3 ${animated ? 'animate-pulse' : ''}`} />
              </VStack>
              <Skeleton className={`h-6 w-16 rounded ${animated ? 'animate-pulse' : ''}`} />
            </HStack>
          </Card>
        ))}
      </VStack>
    </VStack>
  </Box>
);

const FooterSkeleton: React.FC<{ animated: boolean }> = ({ animated }) => (
  <Box className="bg-white border-t border-gray-200 px-4 py-4">
    <HStack className="items-center justify-between">
      <Skeleton className={`h-10 w-24 rounded-lg ${animated ? 'animate-pulse' : ''}`} />
      <HStack space="sm">
        <Skeleton className={`h-10 w-20 rounded-lg ${animated ? 'animate-pulse' : ''}`} />
        <Skeleton className={`h-10 w-28 rounded-lg ${animated ? 'animate-pulse' : ''}`} />
      </HStack>
    </HStack>
  </Box>
);

export const WizardLoadingSkeleton: React.FC<WizardLoadingSkeletonProps> = ({
  showNavigation = true,
  animated = true,
}) => (
  <Box className="flex-1 bg-gray-50">
    <HStack className="flex-1">
      {/* Sidebar Navigation */}
      {showNavigation && <NavigationSkeleton animated={animated} />}
      
      {/* Main Content */}
      <VStack className="flex-1">
        {/* Header */}
        <HeaderSkeleton animated={animated} />
        
        {/* Content */}
        <ContentSkeleton animated={animated} />
        
        {/* Footer */}
        <FooterSkeleton animated={animated} />
      </VStack>
    </HStack>
  </Box>
);

export default WizardLoadingSkeleton;