import React from 'react';
import { Clock, Mail, Users } from 'lucide-react-native';

import { Box } from '@/components/ui/box';
import { Card, CardBody, CardHeader } from '@/components/ui/card';
import { Center } from '@/components/ui/center';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Skeleton } from '@/components/ui/skeleton';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

interface InvitationLoadingStateProps {
  type?: 'basic' | 'detailed' | 'skeleton';
  message?: string;
  showProgress?: boolean;
  progress?: number;
}

export const InvitationLoadingState: React.FC<InvitationLoadingStateProps> = ({
  type = 'basic',
  message = 'Carregando convite...',
  showProgress = false,
  progress = 0,
}) => {
  if (type === 'skeleton') {
    return (
      <Box className="flex-1 bg-gray-50 p-6">
        <Center className="flex-1">
          <Box className="w-full max-w-md">
            <Card variant="elevated" className="bg-white shadow-lg">
              <CardHeader className="text-center">
                <VStack space="md" className="items-center">
                  <Skeleton className="w-16 h-16 rounded-full" />
                  <VStack space="xs" className="items-center">
                    <Skeleton className="w-48 h-6 rounded" />
                    <Skeleton className="w-32 h-4 rounded" />
                  </VStack>
                </VStack>
              </CardHeader>

              <CardBody>
                <VStack space="lg">
                  {/* Invitation Details Skeleton */}
                  <Box className="p-4 bg-gray-50 rounded-lg">
                    <VStack space="sm">
                      {[1, 2, 3, 4, 5].map((i) => (
                        <HStack key={i} className="justify-between">
                          <Skeleton className="w-20 h-4 rounded" />
                          <Skeleton className="w-32 h-4 rounded" />
                        </HStack>
                      ))}
                    </VStack>
                  </Box>

                  {/* Message Skeleton */}
                  <Box className="p-4 bg-blue-50 rounded-lg border-l-4 border-blue-400">
                    <VStack space="xs">
                      <Skeleton className="w-28 h-4 rounded" />
                      <Skeleton className="w-full h-8 rounded" />
                    </VStack>
                  </Box>

                  {/* Action Buttons Skeleton */}
                  <VStack space="sm">
                    <Skeleton className="w-full h-12 rounded" />
                    <Skeleton className="w-full h-12 rounded" />
                    <Skeleton className="w-full h-12 rounded" />
                  </VStack>
                </VStack>
              </CardBody>
            </Card>
          </Box>
        </Center>
      </Box>
    );
  }

  if (type === 'detailed') {
    return (
      <Center className="flex-1 p-6">
        <VStack space="lg" className="items-center max-w-md">
          {/* Animated Loading Icons */}
          <HStack space="md" className="items-center">
            <Box className="relative">
              <Icon as={Mail} size="lg" className="text-blue-400" />
              <Box className="absolute -top-1 -right-1">
                <Spinner size="small" />
              </Box>
            </Box>
            <Icon as={Users} size="lg" className="text-green-400" />
            <Icon as={Clock} size="lg" className="text-yellow-400" />
          </HStack>

          {/* Loading Message */}
          <VStack space="sm" className="items-center">
            <Text className="text-lg font-medium text-gray-900">
              {message}
            </Text>
            <Text className="text-center text-gray-600">
              Verificando detalhes da escola e validando permissões...
            </Text>
          </VStack>

          {/* Progress Bar */}
          {showProgress && (
            <Box className="w-full">
              <Box className="w-full bg-gray-200 rounded-full h-2">
                <Box 
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${Math.min(progress, 100)}%` }}
                />
              </Box>
              <Text className="text-sm text-gray-500 text-center mt-2">
                {Math.round(progress)}% concluído
              </Text>
            </Box>
          )}

          {/* Loading Steps */}
          <VStack space="xs" className="w-full">
            <HStack space="sm" className="items-center">
              <Box className="w-2 h-2 bg-green-500 rounded-full" />
              <Text className="text-sm text-gray-600">Convite localizado</Text>
            </HStack>
            <HStack space="sm" className="items-center">
              <Spinner size="small" />
              <Text className="text-sm text-gray-600">Verificando permissões</Text>
            </HStack>
            <HStack space="sm" className="items-center">
              <Box className="w-2 h-2 bg-gray-300 rounded-full" />
              <Text className="text-sm text-gray-400">Carregando detalhes da escola</Text>
            </HStack>
          </VStack>
        </VStack>
      </Center>
    );
  }

  // Basic loading state
  return (
    <Center className="flex-1">
      <VStack space="md" className="items-center">
        <Spinner size="large" />
        <Text className="text-gray-600">{message}</Text>
        {showProgress && (
          <Text className="text-sm text-gray-500">
            {Math.round(progress)}%
          </Text>
        )}
      </VStack>
    </Center>
  );
};

export default InvitationLoadingState;