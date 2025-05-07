import React from 'react';
import { ScrollView, Animated, StyleSheet, View } from 'react-native';
import { Box } from '@/components/ui/box';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Pressable } from '@/components/ui/pressable';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { Avatar, AvatarFallbackText } from '@/components/ui/avatar';
import { Hash, ChevronDown, PlusCircle, Users, ChevronRight, ChevronLeft } from 'lucide-react-native';
import { useAuth } from '@/api/authContext';
import { Channel } from '@/api/channelApi';

interface ChannelDrawerProps {
  isOpen: boolean;
  onToggle: () => void;
  channels: Channel[];
  onChannelSelect: (channelId: string) => void;
  selectedChannelId?: string;
}

export const ChannelDrawer = ({
  isOpen,
  onToggle,
  channels,
  onChannelSelect,
  selectedChannelId
}: ChannelDrawerProps) => {
  const { userProfile } = useAuth();
  const userName = userProfile?.name;

  // Animation value for drawer
  const [slideAnim] = React.useState(new Animated.Value(isOpen ? 0 : -240));

  // Handle drawer animation
  React.useEffect(() => {
    Animated.timing(slideAnim, {
      toValue: isOpen ? 0 : -240,
      duration: 300,
      useNativeDriver: true,
    }).start();
  }, [isOpen, slideAnim]);

  // Group channels by type and unread status
  const unreadChannels = channels.filter(channel => channel.unreadCount > 0);
  const groupChannels = channels.filter(channel => channel.type === 'channel' && channel.unreadCount === 0);
  const directMessages = channels.filter(channel => channel.type === 'dm' && channel.unreadCount === 0);

  return (
    <View style={styles.container}>
      <Animated.View
        style={[
          styles.drawer,
          { transform: [{ translateX: slideAnim }] },
          { width: 240 }
        ]}
      >
        <VStack className="h-full pt-4 bg-white border-r border-gray-200">

          <ScrollView className="flex-1 mt-2 px-2">
            {/* Unread Section */}
            {unreadChannels.length > 0 && (
              <VStack className="mb-4">
                <HStack className="justify-between items-center mb-2">
                  <Text className="text-xs font-bold text-gray-500 uppercase">Não lidas</Text>
                </HStack>

                {unreadChannels.map(channel => (
                  <Pressable
                    key={channel.id}
                    onPress={() => onChannelSelect(channel.id)}
                    className={`py-2 px-2 rounded-md ${selectedChannelId === channel.id ? 'bg-blue-100' : 'hover:bg-gray-100'}`}
                  >
                    <HStack space="sm" className="items-center">
                      {channel.type === 'channel' ? (
                        <Icon as={Hash} size="sm" className="text-gray-600" />
                      ) : (
                        <Box className="relative">
                          <Avatar className="bg-purple-100 h-6 w-6">
                            <AvatarFallbackText>{channel.avatarText}</AvatarFallbackText>
                          </Avatar>
                          {channel.type === 'dm' && channel.participants && channel.participants[0]?.isOnline && (
                            <Box className="absolute bottom-0 right-0 rounded-full h-2 w-2 bg-green-500 border border-white" />
                          )}
                        </Box>
                      )}
                      <Text className="font-bold">{channel.name}</Text>
                      <Box className="bg-blue-500 ml-auto rounded-full h-5 w-5 items-center justify-center">
                        <Text className="text-xs text-white">{channel.unreadCount}</Text>
                      </Box>
                    </HStack>
                  </Pressable>
                ))}
              </VStack>
            )}

            {/* Channels Section */}
            <VStack className="mb-4">
              <HStack className="justify-between items-center mb-2">
                <Text className="text-xs font-bold text-gray-500 uppercase">Canais</Text>
                <Pressable className="p-1">
                  <Icon as={PlusCircle} size="sm" className="text-gray-600" />
                </Pressable>
              </HStack>

              {groupChannels.map(channel => (
                <Pressable
                  key={channel.id}
                  onPress={() => onChannelSelect(channel.id)}
                  className={`py-2 px-2 rounded-md ${selectedChannelId === channel.id ? 'bg-blue-100' : 'hover:bg-gray-100'}`}
                >
                  <HStack space="sm" className="items-center">
                    <Icon as={Hash} size="sm" className="text-gray-600" />
                    <Text className="text-gray-800">{channel.name}</Text>
                  </HStack>
                </Pressable>
              ))}
            </VStack>

            {/* Direct Messages Section */}
            <VStack className="mb-4">
              <HStack className="justify-between items-center mb-2">
                <Text className="text-xs font-bold text-gray-500 uppercase">Mensagens Diretas</Text>
                <Pressable className="p-1">
                  <Icon as={PlusCircle} size="sm" className="text-gray-600" />
                </Pressable>
              </HStack>

              {directMessages.map(channel => (
                <Pressable
                  key={channel.id}
                  onPress={() => onChannelSelect(channel.id)}
                  className={`py-2 px-2 rounded-md ${selectedChannelId === channel.id ? 'bg-blue-100' : 'hover:bg-gray-100'}`}
                >
                  <HStack space="sm" className="items-center">
                    <Box className="relative">
                      <Avatar className="bg-purple-100 h-6 w-6">
                        <AvatarFallbackText>{channel.avatarText}</AvatarFallbackText>
                      </Avatar>
                      {channel.participants && channel.participants[0]?.isOnline && (
                        <Box className="absolute bottom-0 right-0 rounded-full h-2 w-2 bg-green-500 border border-white" />
                      )}
                    </Box>
                    <Text className="text-gray-800">{channel.name}</Text>
                  </HStack>
                </Pressable>
              ))}
            </VStack>
          </ScrollView>
        </VStack>
      </Animated.View>

      {/* Toggle button */}
      <Pressable
        onPress={onToggle}
        style={[
          styles.toggleButton,
          { left: isOpen ? 239 : -1 }
        ]}
        className="bg-gray-100 border border-gray-200"
      >
        <Icon as={isOpen ? ChevronLeft : ChevronRight} size="sm" className="text-gray-600" />
      </Pressable>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    position: 'relative',
    height: '100%',
  },
  drawer: {
    position: 'absolute',
    top: 0,
    left: 0,
    bottom: 0,
    backgroundColor: 'white',
    zIndex: 10,
  },
  toggleButton: {
    position: 'absolute',
    top: '50%',
    zIndex: 20,
    width: 24,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
    borderRadius: 4,
    marginTop: -20,
  }
});
