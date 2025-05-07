import React from 'react';
import { ScrollView } from 'react-native';
import { Box } from '@/components/ui/box';
import { Heading } from '@/components/ui/heading';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Avatar, AvatarFallbackText } from '@/components/ui/avatar';
import { Hash, FileText, Pin, Users, PlusIcon } from 'lucide-react-native';
import { Channel } from '@/api/channelApi';
import { Input, InputField } from '@/components/ui/input';

interface ChannelContentProps {
  channel?: Channel;
  isLoading: boolean;
}

const ChannelContent = ({ channel, isLoading }: ChannelContentProps) => {
  if (isLoading || !channel) {
    return (
      <VStack className="flex-1 justify-center items-center">
        <Text>Carregando canal...</Text>
      </VStack>
    );
  }

  // Sample messages for demo
  const messages = [
    {
      id: '1',
      user: 'João Silva',
      avatar: 'JS',
      time: '10:30',
      content: 'Olá, pessoal! Alguém pode me ajudar com a tarefa de matemática?'
    },
    {
      id: '2',
      user: 'Maria Oliveira',
      avatar: 'MO',
      time: '10:35',
      content: 'Claro, João! Em qual exercício você está com dificuldade?'
    },
    {
      id: '3',
      user: 'Pedro Santos',
      avatar: 'PS',
      time: '10:40',
      content: 'Eu também estou com dúvidas na página 42. Vamos estudar juntos.'
    }
  ];

  return (
    <Box className="flex-1 flex-col bg-white">
      {/* Channel Header */}
      <HStack className="px-4 py-3 border-b border-gray-200 items-center justify-between">
        <HStack space="md" className="items-center">
          <Icon as={Hash} size="md" className="text-gray-600" />
          <Heading className="text-lg font-bold">{channel.name}</Heading>
        </HStack>
        <HStack space="sm">
          <Icon as={Users} size="sm" className="text-gray-600" />
          <Icon as={Pin} size="sm" className="text-gray-600" />
          <Icon as={FileText} size="sm" className="text-gray-600" />
        </HStack>
      </HStack>

      {/* Channel Messages */}
      <ScrollView className="flex-1 p-4">
        <VStack space="md">
          {messages.map(message => (
            <HStack key={message.id} space="sm" className="mb-4">
              <Avatar className="bg-blue-100 h-10 w-10">
                <AvatarFallbackText>{message.avatar}</AvatarFallbackText>
              </Avatar>
              <VStack className="flex-1">
                <HStack space="sm" className="items-center">
                  <Text className="font-bold">{message.user}</Text>
                  <Text className="text-xs text-gray-500">{message.time}</Text>
                </HStack>
                <Text className="text-gray-800">{message.content}</Text>
              </VStack>
            </HStack>
          ))}
        </VStack>
      </ScrollView>

      {/* Message Input */}
      <Box className="p-4 border-t border-gray-200">
        <Input className="bg-gray-100 rounded-lg">
          <HStack className="w-full items-center px-3">
            <InputField
              placeholder={`Enviar mensagem para ${channel.type === 'channel' ? '#' + channel.name : channel.name}`}
              className="flex-1 h-12"
            />
            <Icon as={PlusIcon} size="sm" className="text-gray-600 ml-2" />
          </HStack>
        </Input>
      </Box>
    </Box>
  );
};

export default ChannelContent;
