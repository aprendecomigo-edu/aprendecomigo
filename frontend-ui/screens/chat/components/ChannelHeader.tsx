import React from 'react';
import { Box } from '@/components/ui/box';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Pressable } from '@/components/ui/pressable';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { Input, InputField } from '@/components/ui/input';
import { Avatar, AvatarFallbackText } from '@/components/ui/avatar';
import { MenuIcon, SearchIcon, PlusCircleIcon } from 'lucide-react-native';
import { useAuth } from '@/api/authContext';

interface ChannelHeaderProps {
  toggleDrawer: () => void;
  searchTerm: string;
  onSearchChange: (text: string) => void;
}

export const ChannelHeader = ({ toggleDrawer, searchTerm, onSearchChange }: ChannelHeaderProps) => {
  const { userProfile } = useAuth();
  const userName = userProfile?.name;
  const userInitials = userName?.split(' ').map(name => name[0]).join('').slice(0, 2).toUpperCase();

  return (
    <VStack space="md" className="bg-white border-b border-gray-200 p-4">
      <HStack className="items-center justify-between">
        <HStack space="md" className="items-center">
          <Pressable onPress={toggleDrawer} className="p-1">
            <Icon as={MenuIcon} size="md" className="text-gray-700" />
          </Pressable>
          <Text className="font-bold text-xl">Mensagens</Text>
        </HStack>

        <HStack space="md" className="items-center">
          <Pressable className="bg-gray-100 p-2 rounded-full">
            <Icon as={PlusCircleIcon} size="sm" className="text-gray-700" />
          </Pressable>
          <Avatar className="bg-blue-500 h-8 w-8">
            <AvatarFallbackText>{userInitials}</AvatarFallbackText>
          </Avatar>
        </HStack>
      </HStack>

      <HStack className="bg-gray-100 rounded-lg items-center px-3">
        <Icon as={SearchIcon} size="sm" className="text-gray-500 mr-2" />
        <Input className="flex-1 h-10 bg-transparent border-0">
          <InputField
            placeholder="Buscar conversas..."
            value={searchTerm}
            onChangeText={onSearchChange}
          />
        </Input>
      </HStack>
    </VStack>
  );
};
