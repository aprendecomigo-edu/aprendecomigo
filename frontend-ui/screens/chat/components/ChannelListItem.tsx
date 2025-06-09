import { Hash, MessageCircle, Lock } from 'lucide-react-native';
import React from 'react';

import { Channel } from '@/api/channelApi';
import { Avatar, AvatarFallbackText } from '@/components/ui/avatar';
import { Box } from '@/components/ui/box';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Pressable } from '@/components/ui/pressable';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

interface ChannelListItemProps {
  channel: Channel;
  onPress: (channelId: string) => void;
}

export const ChannelListItem = ({ channel, onPress }: ChannelListItemProps) => {
  const isDM = channel.type === 'dm';
  const isUnread = channel.unreadCount > 0;

  // Get the appropriate icon based on channel type
  const getChannelIcon = () => {
    if (isDM) {
      return null; // No icon for DMs, will show avatar
    } else {
      return channel.name.includes('private') ? Lock : Hash;
    }
  };

  const ChannelIcon = getChannelIcon();

  // For DMs, get the online status from participants
  const isOnline = isDM && channel.participants && channel.participants[0]?.isOnline;

  return (
    <Pressable onPress={() => onPress(channel.id)}>
      <HStack className="bg-white p-4 rounded-lg border border-gray-100 items-center mb-2">
        <Box className="relative">
          <Avatar className={`${isDM ? 'bg-purple-100' : 'bg-blue-100'} h-12 w-12 mr-3`}>
            {ChannelIcon ? (
              <Icon as={ChannelIcon} size="sm" className="text-gray-600" />
            ) : (
              <AvatarFallbackText>{channel.avatarText}</AvatarFallbackText>
            )}
          </Avatar>

          {/* Online status indicator (only for DM channels) */}
          {isDM && (
            <Box
              className={`absolute bottom-0 right-3 rounded-full h-3 w-3 border-2 border-white ${
                isOnline ? 'bg-green-500' : 'bg-gray-400'
              }`}
            />
          )}

          {/* Channel member count indicator */}
          {!isDM && channel.onlineCount && channel.onlineCount > 0 && (
            <Box className="absolute bottom-0 right-3 rounded-full bg-green-500 px-1.5 py-0.5 border border-white">
              <Text className="text-[8px] text-white font-bold">{channel.onlineCount}</Text>
            </Box>
          )}
        </Box>

        <VStack className="flex-1">
          <HStack className="justify-between items-center">
            <Text className={`${isUnread ? 'font-bold' : 'font-medium'}`}>{channel.name}</Text>
            <Text className="text-xs text-gray-500">{channel.time}</Text>
          </HStack>

          <HStack className="justify-between items-center">
            <Text
              className={`text-sm ${
                isUnread ? 'text-gray-800 font-medium' : 'text-gray-600'
              } flex-1`}
              numberOfLines={1}
            >
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
  );
};
