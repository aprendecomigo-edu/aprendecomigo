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
  AtSign,
} from 'lucide-react-native';
import React, { useState, useEffect } from 'react';
import { FlatList, Keyboard } from 'react-native';

import { useAuth } from '@/api/authContext';
import { Channel, Message, fetchMessages, sendMessage } from '@/api/channelApi';
import { Avatar, AvatarFallbackText } from '@/components/ui/avatar';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Divider } from '@/components/ui/divider';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Input, InputField, InputIcon } from '@/components/ui/input';
import { KeyboardAvoidingView } from '@/components/ui/keyboard-avoiding-view';
import { Pressable } from '@/components/ui/pressable';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { API_URL } from '@/constants/api';
import { useWebSocket } from '@/hooks/useWebSocket';

interface ChannelContentProps {
  channel?: Channel;
  isLoading: boolean;
}

// Legacy message interface for displaying messages
interface DisplayMessage {
  id: number;
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
const MessageItem = ({ message }: { message: DisplayMessage }) => {
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
const IconButton = ({
  icon,
  onPress,
  className,
  variant,
}: {
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
const MessageInput = ({
  channel,
  onMessageSent,
}: {
  channel: Channel;
  onMessageSent?: () => void;
}) => {
  const [message, setMessage] = useState('');
  const [sending, setSending] = useState(false);

  const handleSend = async () => {
    if (message.trim() && !sending) {
      setSending(true);
      try {
        await sendMessage(channel.id, message.trim());
        setMessage('');
        onMessageSent?.();
      } catch (error) {
        console.error('Error sending message:', error);
      } finally {
        setSending(false);
      }
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
                placeholder={`Enviar mensagem para ${
                  channel.is_direct ? 'conversa direta' : '#' + channel.name
                }`}
                className="flex-1 py-2"
                value={message}
                onChangeText={setMessage}
                onSubmitEditing={handleSend}
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
            variant={message.trim() ? 'solid' : 'outline'}
            className={message.trim() ? 'bg-blue-500' : 'border-gray-300'}
            onPress={handleSend}
            isDisabled={!message.trim() || sending}
          >
            <ButtonText className={message.trim() ? 'text-white' : 'text-gray-400'}>
              {sending ? 'Enviando...' : 'Enviar'}
            </ButtonText>
          </Button>
        </HStack>
      </VStack>
    </Box>
  );
};

const ChannelContent = ({ channel, isLoading }: ChannelContentProps) => {
  const [messages, setMessages] = useState<DisplayMessage[]>([]);
  const [loadingMessages, setLoadingMessages] = useState(true);
  const { userProfile } = useAuth();

  // WebSocket connection for real-time messaging
  const wsUrl = API_URL.replace('http', 'ws').replace('/api', `/ws/chat/${channel?.name || ''}/`);
  const { isConnected, sendMessage: sendWsMessage } = useWebSocket({
    url: wsUrl,
    channelName: channel?.name || '',
    shouldConnect: !!channel,
    onMessage: message => {
      console.log('WebSocket message received:', message);
      if (message.type === 'chat_message') {
        // Add new message to the list
        const apiMessage = message.message as Message;
        const newDisplayMessage = convertToDisplayMessage(apiMessage);
        setMessages(prev => [...prev, newDisplayMessage]);
      }
    },
    onOpen: () => {
      console.log('WebSocket connected for channel:', channel?.name);
    },
    onClose: () => {
      console.log('WebSocket disconnected for channel:', channel?.name);
    },
    onError: error => {
      console.error('WebSocket error for channel:', channel?.name, error);
    },
  });

  // Load messages when channel changes
  useEffect(() => {
    if (channel) {
      loadMessages();
    }
  }, [channel]);

  // Helper function to convert API message to display format
  const convertToDisplayMessage = (msg: Message): DisplayMessage => {
    const messageDate = new Date(msg.timestamp);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    let dateLabel = 'Hoje';
    if (messageDate.toDateString() === yesterday.toDateString()) {
      dateLabel = 'Ontem';
    } else if (messageDate.toDateString() !== today.toDateString()) {
      dateLabel = messageDate.toLocaleDateString('pt-BR');
    }

    return {
      id: msg.id,
      user: `${msg.sender.first_name} ${msg.sender.last_name}`,
      avatar: `${msg.sender.first_name[0]}${msg.sender.last_name[0]}`,
      date: dateLabel,
      time: messageDate.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }),
      content: msg.content,
      reactions: msg.reactions || [],
    };
  };

  const loadMessages = async () => {
    if (!channel) return;

    setLoadingMessages(true);
    try {
      const apiMessages = await fetchMessages(channel.id);

      // Convert API messages to display format
      const displayMessages: DisplayMessage[] = apiMessages.map(convertToDisplayMessage);

      setMessages(displayMessages);
    } catch (error) {
      console.error('Error loading messages:', error);
    } finally {
      setLoadingMessages(false);
    }
  };

  const handleMessageSent = () => {
    // Messages will be updated via WebSocket, no need to reload
    // But we can add a fallback in case WebSocket fails
    if (!isConnected) {
      loadMessages();
    }
  };

  if (isLoading || !channel) {
    return (
      <VStack className="flex-1 justify-center items-center">
        <Text>Carregando canal...</Text>
      </VStack>
    );
  }

  if (loadingMessages) {
    return (
      <VStack className="flex-1 justify-center items-center">
        <Text>Carregando mensagens...</Text>
      </VStack>
    );
  }

  // Group messages by date
  const groupedMessages = messages.reduce((groups: Record<string, DisplayMessage[]>, message) => {
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
      ...msgs.map(msg => ({ ...msg, type: 'message' })),
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
          {channel.is_direct ? (
            <Box className="relative">
              <Avatar className="bg-purple-100 h-6 w-6">
                <AvatarFallbackText>
                  {channel.participants.find(p => p.id !== userProfile?.id)?.first_name[0]}
                  {channel.participants.find(p => p.id !== userProfile?.id)?.last_name[0]}
                </AvatarFallbackText>
              </Avatar>
            </Box>
          ) : (
            <Icon as={Hash} size="md" className="text-gray-600" />
          )}
          <Heading className="text-lg font-bold">
            {channel.is_direct
              ? channel.participants.find(p => p.id !== userProfile?.id)?.first_name +
                ' ' +
                channel.participants.find(p => p.id !== userProfile?.id)?.last_name
              : channel.name}
          </Heading>
        </HStack>
        <HStack space="sm">
          <Icon as={Users} size="sm" className="text-gray-600" />
          <Text className="text-sm text-gray-500">{channel.participants.length}</Text>
        </HStack>
      </HStack>

      {/* Channel Messages */}
      <FlatList
        data={messagesWithSeparators}
        renderItem={renderItem}
        keyExtractor={item => item.id.toString()}
        contentContainerStyle={{ padding: 16 }}
        className="flex-1"
      />

      {/* Message Input */}
      <MessageInput channel={channel} onMessageSent={handleMessageSent} />
    </Box>
  );
};

export default ChannelContent;
