import React from 'react';

import { useUserProfile } from '@/api/auth';
import MainLayout from '@/components/layouts/MainLayout';
import { Avatar, AvatarFallbackText } from '@/components/ui/avatar';
import { Box } from '@/components/ui/box';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

const ProfileContent = () => {
  const { userProfile } = useUserProfile();
  const userName = userProfile?.name || 'User';
  const userEmail = userProfile?.email || '';
  const userInitials = userName
    .split(' ')
    .map(n => n[0])
    .join('')
    .slice(0, 2)
    .toUpperCase();

  return (
    <VStack className="p-6 flex-1" space="lg">
      {/* Profile Header */}
      <VStack space="md" className="items-center">
        <Avatar className="bg-blue-600 h-24 w-24">
          <AvatarFallbackText className="text-white font-bold text-xl">
            {userInitials}
          </AvatarFallbackText>
        </Avatar>
        <VStack className="items-center">
          <Heading size="xl" className="text-gray-900">
            {userName}
          </Heading>
          <Text className="text-gray-600">{userEmail}</Text>
        </VStack>
      </VStack>

      {/* Profile Content */}
      <VStack space="md" className="mt-8">
        <Box className="bg-white rounded-lg border border-gray-200 p-6">
          <VStack space="md">
            <Heading size="lg" className="text-gray-900">
              Profile Information
            </Heading>
            <VStack space="sm">
              <HStack className="justify-between">
                <Text className="font-medium text-gray-700">Name:</Text>
                <Text className="text-gray-600">{userName}</Text>
              </HStack>
              <HStack className="justify-between">
                <Text className="font-medium text-gray-700">Email:</Text>
                <Text className="text-gray-600">{userEmail}</Text>
              </HStack>
              {userProfile?.phone_number && (
                <HStack className="justify-between">
                  <Text className="font-medium text-gray-700">Phone:</Text>
                  <Text className="text-gray-600">{userProfile.phone_number}</Text>
                </HStack>
              )}
            </VStack>
          </VStack>
        </Box>
      </VStack>
    </VStack>
  );
};

export const Profile = () => {
  return (
    <MainLayout _title="Profile">
      <ProfileContent />
    </MainLayout>
  );
};
