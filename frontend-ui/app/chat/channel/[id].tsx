import { useLocalSearchParams } from 'expo-router';
import React, { useEffect, useState } from 'react';
import { View, StyleSheet } from 'react-native';

import { Channel, fetchChannels } from '@/api/channelApi';
import MainLayout from '@/components/layouts/MainLayout';
import { Box } from '@/components/ui/box';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import ChannelContent from '@/screens/chat/components/ChannelContent';
import { ChannelDrawer } from '@/screens/chat/components/ChannelDrawer';

export default function ChatRoomScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const [isLoading, setIsLoading] = useState(true);
  const [channels, setChannels] = useState<Channel[]>([]);
  const [selectedChannel, setSelectedChannel] = useState<Channel | undefined>(undefined);
  const [isDrawerOpen, setIsDrawerOpen] = useState(true);

  useEffect(() => {
    const loadChannels = async () => {
      setIsLoading(true);
      try {
        const data = await fetchChannels();
        setChannels(data);

        // Find the selected channel
        const channel = data.find(c => c.id === id);
        setSelectedChannel(channel);
      } catch (error) {
        console.error('Error loading channels:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadChannels();
  }, [id]);

  // Handle channel selection
  const handleChannelSelect = (channelId: string) => {
    const channel = channels.find(c => c.id === channelId);
    setSelectedChannel(channel);
  };

  // Toggle drawer
  const toggleDrawer = () => {
    setIsDrawerOpen(!isDrawerOpen);
  };

  return (
    <MainLayout title="Chat" showSidebar={true}>
      <Box className="flex-1">
        <View style={styles.container}>
          {/* Channel Drawer */}
          <ChannelDrawer
            isOpen={isDrawerOpen}
            onToggle={toggleDrawer}
            channels={channels}
            onChannelSelect={handleChannelSelect}
            selectedChannelId={id}
          />

          {/* Main Content */}
          <View style={[styles.contentContainer, { marginLeft: isDrawerOpen ? 240 : 0 }]}>
            <ChannelContent channel={selectedChannel} isLoading={isLoading} />
          </View>
        </View>
      </Box>
    </MainLayout>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    flexDirection: 'row',
    position: 'relative',
  },
  contentContainer: {
    flex: 1,
  },
});
