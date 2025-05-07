import React from 'react';
import { useAuth } from '@/api/authContext';
import { Avatar, AvatarFallbackText } from '@/components/ui/avatar';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Pressable } from '@/components/ui/pressable';
import { SafeAreaView } from '@/components/ui/safe-area-view';
import { ScrollView } from '@/components/ui/scroll-view';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { isWeb } from '@gluestack-ui/nativewind-utils/IsWeb';
import { SearchIcon, PlusCircleIcon } from 'lucide-react-native';
import { useRouter } from 'expo-router';

// Sample mock data for channels/chats
interface Channel {
  id: string;
  name: string;
  lastMessage: string;
  time: string;
  unreadCount: number;
  avatarText: string;
}

const sampleChannels: Channel[] = [
  {
    id: '1',
    name: '9° Ano A',
    lastMessage: 'Dúvida sobre a lição de casa',
    time: '10:30',
    unreadCount: 3,
    avatarText: '9A',
  },
  {
    id: '2',
    name: 'Professores de Matemática',
    lastMessage: 'Reunião amanhã às 14h',
    time: '09:15',
    unreadCount: 0,
    avatarText: 'PM',
  },
  {
    id: '3',
    name: 'Coordenação Pedagógica',
    lastMessage: 'Relatórios do bimestre',
    time: 'Ontem',
    unreadCount: 5,
    avatarText: 'CP',
  },
  {
    id: '4',
    name: 'Prof. Maria Silva',
    lastMessage: 'Pode me enviar o planejamento?',
    time: 'Ontem',
    unreadCount: 0,
    avatarText: 'MS',
  },
  {
    id: '5',
    name: 'Pais 10° Ano B',
    lastMessage: 'Informações sobre a feira de ciências',
    time: '23/05',
    unreadCount: 1,
    avatarText: 'PB',
  },
];

const ChannelListScreen = () => {
  const { userProfile } = useAuth();
  const userName = userProfile?.name || 'Usuário';
  const router = useRouter();

  return (
    <Box className="flex-1 bg-gray-50">
      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={{
          paddingBottom: isWeb ? 0 : 100,
          flexGrow: 1,
        }}
        className="flex-1 mb-20 md:mb-2"
      >
        <VStack className="p-4 pb-0 md:px-6 md:pt-6 w-full" space="xl">
          {/* Header */}
          <HStack className="bg-blue-600 rounded-lg p-4 items-center justify-between">
            <VStack>
              <Text className="text-white font-bold text-xl">Mensagens</Text>
              <Text className="text-white">Suas conversas</Text>
            </VStack>
            <Pressable>
              <Box className="bg-blue-500 h-9 w-9 rounded-full items-center justify-center">
                <Icon as={PlusCircleIcon} size="sm" color="white" />
              </Box>
            </Pressable>
          </HStack>

          {/* Search */}
          <HStack className="bg-white rounded-lg border border-gray-200 p-2 mb-2 items-center">
            <Icon as={SearchIcon} size="sm" className="text-gray-500 mr-2" />
            <Text className="text-gray-400">Buscar conversas...</Text>
          </HStack>

          {/* Channel List */}
          <VStack space="sm" className="mb-4">
            <Heading className="text-lg font-bold mb-2">Conversas Recentes</Heading>

            {sampleChannels.map((channel) => (
              <Pressable key={channel.id} onPress={() => {}}>
                <HStack className="bg-white p-4 rounded-lg border border-gray-100 items-center mb-2">
                  <Avatar className="bg-blue-100 h-12 w-12 mr-3">
                    <AvatarFallbackText>{channel.avatarText}</AvatarFallbackText>
                  </Avatar>
                  <VStack className="flex-1">
                    <HStack className="justify-between items-center">
                      <Text className="font-bold">{channel.name}</Text>
                      <Text className="text-xs text-gray-500">{channel.time}</Text>
                    </HStack>
                    <HStack className="justify-between items-center">
                      <Text className="text-sm text-gray-600 flex-1" numberOfLines={1}>
                        {channel.lastMessage}
                      </Text>
                      {channel.unreadCount > 0 && (
                        <Box className="bg-blue-500 rounded-full h-5 w-5 items-center justify-center ml-2">
                          <Text className="text-xs text-white">{channel.unreadCount}</Text>
                        </Box>
                      )}
                    </HStack>
                  </VStack>
                </HStack>
              </Pressable>
            ))}
          </VStack>

          {/* Create New Chat Button */}
          <Button className="bg-blue-600 mb-4">
            <ButtonText>Nova Conversa</ButtonText>
          </Button>
        </VStack>
      </ScrollView>
    </Box>
  );
};

export const ChannelListScreenPage = () => {
  return <ChannelListScreen />;
};

export default ChannelListScreenPage;
