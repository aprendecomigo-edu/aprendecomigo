import React, { useState } from 'react';
import { FlatList, Keyboard } from 'react-native';
import { Box } from '@/components/ui/box';
import { Heading } from '@/components/ui/heading';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Avatar, AvatarFallbackText } from '@/components/ui/avatar';
import {
  Hash,
  FileText,
  Pin,
  Users,
  PlusIcon,
  ThumbsUp,
  Heart,
  Smile,
  Paperclip,
  Image,
  Send,
  AtSign
} from 'lucide-react-native';
import { Channel } from '@/api/channelApi';
import { Input, InputField, InputIcon } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { Divider } from '@/components/ui/divider';
import { Button, ButtonText } from '@/components/ui/button';
import { Pressable } from '@/components/ui/pressable';
import { KeyboardAvoidingView } from '@/components/ui/keyboard-avoiding-view';

interface ChannelContentProps {
  channel?: Channel;
  isLoading: boolean;
}

// Message type definition
interface Message {
  id: string;
  user: string;
  avatar: string;
  time: string;
  date: string;
  content: string;
  reactions?: Reaction[];
  hasLink?: boolean;
  linkPreview?: LinkPreview;
}

interface Reaction {
  emoji: React.ReactNode;
  count: number;
}

interface LinkPreview {
  title: string;
  description: string;
  url: string;
}

// Date separator component
const DateSeparator = ({ date }: { date: string }) => (
  <Box className="py-4 relative">
    <Divider className="bg-gray-200" />
    <Box className="absolute top-0 left-0 right-0 flex items-center justify-center">
      <Text className="bg-white px-2 text-xs text-gray-500">{date}</Text>
    </Box>
  </Box>
);

// Message component
const MessageItem = ({ message }: { message: Message }) => {
  return (
    <HStack space="sm" className="mb-4 pt-1">
      <Avatar className="bg-blue-100 h-10 w-10 rounded-md">
        <AvatarFallbackText>{message.avatar}</AvatarFallbackText>
      </Avatar>
      <VStack className="flex-1">
        <HStack space="sm" className="items-center">
          <Text className="font-bold">{message.user}</Text>
          <Text className="text-xs text-gray-500">{message.time}</Text>
        </HStack>
        <Text className="text-gray-800 mb-1">{message.content}</Text>

        {/* Link preview */}
        {message.hasLink && message.linkPreview && (
          <Card className="mt-1 mb-2 border-l-4 border-l-blue-500 pl-2">
            <Text className="font-bold">{message.linkPreview.title}</Text>
            <Text className="text-sm text-gray-600">{message.linkPreview.description}</Text>
            <Text className="text-xs text-blue-500">{message.linkPreview.url}</Text>
          </Card>
        )}

        {/* Reactions */}
        {message.reactions && message.reactions.length > 0 && (
          <HStack space="xs" className="mt-1">
            {message.reactions.map((reaction, index) => (
              <HStack
                key={index}
                className="bg-gray-100 rounded-md px-1.5 py-0.5 items-center"
                space="xs"
              >
                <Box>{reaction.emoji}</Box>
                <Text className="text-xs">{reaction.count}</Text>
              </HStack>
            ))}
          </HStack>
        )}
      </VStack>
    </HStack>
  );
};

// Define a simple IconButton since it's missing
const IconButton = ({ icon, onPress, className, variant }: {
  icon: React.ReactNode;
  onPress?: () => void;
  className?: string;
  variant?: string;
}) => {
  return (
    <Pressable onPress={onPress} className={className || ''}>
      {icon}
    </Pressable>
  );
};

// MessageInput component
const MessageInput = ({ channel }: { channel: Channel }) => {
  const [message, setMessage] = useState('');

  const handleSend = () => {
    if (message.trim()) {
      console.log('Sending message:', message);
      setMessage('');
    }
  };

  return (
    <Box>
      <VStack className="border-t border-gray-200 bg-white">
        {/* Input with plus button */}
        <Box className="px-4 pt-3">
          <Input className="bg-gray-100 rounded-lg w-full">
            <HStack className="w-full items-center px-3">
              <InputField
                placeholder={`Enviar mensagem para ${channel.type === 'channel' ? '#' + channel.name : channel.name}`}
                className="flex-1 py-2"
                value={message}
                onChangeText={setMessage}
              />
              <Box>
                <Icon as={PlusIcon} size="sm" className="text-gray-600" />
              </Box>
            </HStack>
          </Input>
        </Box>

        {/* Action buttons row */}
        <HStack className="px-4 py-2 justify-between">
          <HStack space="md">
            <Box>
              <Icon as={Paperclip} size="sm" className="text-gray-600" />
            </Box>
            <Box>
              <Icon as={Image} size="sm" className="text-gray-600" />
            </Box>
            <Box>
              <Icon as={Smile} size="sm" className="text-gray-600" />
            </Box>
          </HStack>

          <Button
            size="sm"
            variant={message.trim() ? "solid" : "outline"}
            className={message.trim() ? "bg-blue-500" : "border-gray-300"}
            onPress={handleSend}
            isDisabled={!message.trim()}
          >
            <ButtonText className={message.trim() ? "text-white" : "text-gray-400"}>
              Enviar
            </ButtonText>
          </Button>
        </HStack>
      </VStack>
    </Box>
  );
};

const ChannelContent = ({ channel, isLoading }: ChannelContentProps) => {
  if (isLoading || !channel) {
    return (
      <VStack className="flex-1 justify-center items-center">
        <Text>Carregando canal...</Text>
      </VStack>
    );
  }

  // Sample messages for demo with dates and reactions
  const messages = [
    {
      id: '1',
      user: 'João Silva',
      avatar: 'JS',
      date: 'Hoje',
      time: '10:30',
      content: 'Olá, pessoal! Alguém pode me ajudar com a tarefa de matemática?',
      reactions: [
        { emoji: <Icon as={ThumbsUp} size="xs" className="text-blue-500" />, count: 3 },
        { emoji: <Icon as={Heart} size="xs" className="text-red-500" />, count: 1 }
      ]
    },
    {
      id: '2',
      user: 'Maria Oliveira',
      avatar: 'MO',
      date: 'Hoje',
      time: '10:35',
      content: 'Claro, João! Em qual exercício você está com dificuldade?',
      reactions: [
        { emoji: <Icon as={Smile} size="xs" className="text-yellow-500" />, count: 2 }
      ]
    },
    {
      id: '3',
      user: 'Pedro Santos',
      avatar: 'PS',
      date: 'Ontem',
      time: '10:40',
      content: 'Eu também estou com dúvidas na página 42. Vamos estudar juntos.',
      hasLink: true,
      linkPreview: {
        title: 'Exercícios de Matemática - PDF',
        description: 'Material de estudo para o exame final de matemática',
        url: 'https://escola.edu/matematica/exercicios.pdf'
      }
    }
  ];

  // Group messages by date
  const groupedMessages = messages.reduce((groups: Record<string, Message[]>, message) => {
    if (!groups[message.date]) {
      groups[message.date] = [];
    }
    groups[message.date].push(message);
    return groups;
  }, {});

  // Convert grouped messages to flat list with date separators
  const messagesWithSeparators = Object.entries(groupedMessages).flatMap(([date, msgs], index) => {
    return [
      { id: `date-${index}`, type: 'date', date },
      ...msgs.map(msg => ({ ...msg, type: 'message' }))
    ];
  });

  const renderItem = ({ item }: { item: any }) => {
    if (item.type === 'date') {
      return <DateSeparator date={item.date} />;
    }
    return <MessageItem message={item} />;
  };

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
      <FlatList
        data={messagesWithSeparators}
        renderItem={renderItem}
        keyExtractor={item => item.id}
        contentContainerStyle={{ padding: 16 }}
        className="flex-1"
      />

      {/* Message Input */}
      <MessageInput channel={channel} />
    </Box>
  );
};

export default ChannelContent;
