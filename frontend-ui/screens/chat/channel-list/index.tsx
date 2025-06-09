import { useRouter, type Href } from 'expo-router';
import { MessageCircle } from 'lucide-react-native';
import React, { useEffect, useState } from 'react';
import { View, StyleSheet } from 'react-native';

import ChannelContent from '../components/ChannelContent';
import { ChannelDrawer } from '../components/ChannelDrawer';
import { ChannelHeader } from '../components/ChannelHeader';
import { ChannelListItem } from '../components/ChannelListItem';

import { useAuth } from '@/api/authContext';
import { Channel, fetchChannels } from '@/api/channelApi';
import MainLayout from '@/components/layouts/main-layout';
import { Box } from '@/components/ui/box';
import { Center } from '@/components/ui/center';
import { Icon } from '@/components/ui/icon';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

const ChannelListContent = () => {
  const router = useRouter();
  const [channels, setChannels] = useState<Channel[]>([]);
  const [filteredChannels, setFilteredChannels] = useState<Channel[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isDrawerOpen, setIsDrawerOpen] = useState(true); // Start with drawer open
  const [selectedChannelId, setSelectedChannelId] = useState<string | undefined>(undefined);

  // Fetch channels on component mount
  useEffect(() => {
    const loadChannels = async () => {
      setIsLoading(true);
      try {
        const data = await fetchChannels();
        setChannels(data);
        setFilteredChannels(data);

        // Set the first channel as selected by default
        if (data.length > 0 && !selectedChannelId) {
          setSelectedChannelId(data[0].id);
        }
      } catch (error) {
        console.error('Error loading channels:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadChannels();
  }, []);

  // Filter channels based on search term
  useEffect(() => {
    if (searchTerm.trim() === '') {
      setFilteredChannels(channels);
    } else {
      const searchTermLower = searchTerm.toLowerCase();
      const filtered = channels.filter(
        channel =>
          channel.name.toLowerCase().includes(searchTermLower) ||
          channel.lastMessage.toLowerCase().includes(searchTermLower)
      );
      setFilteredChannels(filtered);
    }
  }, [searchTerm, channels]);

  // Handle channel selection
  const handleChannelSelect = (channelId: string) => {
    setSelectedChannelId(channelId);
  };

  // Toggle drawer
  const toggleDrawer = () => {
    setIsDrawerOpen(!isDrawerOpen);
  };

  // Get the selected channel
  const selectedChannel = channels.find(channel => channel.id === selectedChannelId);

  return (
    <Box className="flex-1 bg-gray-50">
      <View style={styles.container}>
        {/* Channel Drawer */}
        <ChannelDrawer
          isOpen={isDrawerOpen}
          onToggle={toggleDrawer}
          channels={channels}
          onChannelSelect={handleChannelSelect}
          selectedChannelId={selectedChannelId}
        />

        {/* Main Content */}
        <View style={[styles.contentContainer, { marginLeft: isDrawerOpen ? 240 : 0 }]}>
          {isLoading ? (
            <VStack className="flex-1 justify-center items-center">
              <Text>Carregando conversas...</Text>
            </VStack>
          ) : channels.length === 0 ? (
            <Center className="flex-1 p-8">
              <Icon as={MessageCircle} size="xl" className="text-gray-300 mb-4" />
              <Text className="text-xl font-bold text-gray-600 mb-2">Nenhuma conversa ainda</Text>
              <Text className="text-gray-500 text-center">
                As conversas aparecerão aqui quando você tiver professores e alunos cadastrados na
                escola.
              </Text>
            </Center>
          ) : (
            <ChannelContent channel={selectedChannel || channels[0]} isLoading={isLoading} />
          )}
        </View>
      </View>
    </Box>
  );
};

// Wrap the ChannelListContent with MainLayout for consistent navigation
const ChannelListScreen = () => {
  return (
    <MainLayout title="Mensagens" showSidebar={true}>
      <ChannelListContent />
    </MainLayout>
  );
};

export const ChannelListScreenPage = () => {
  return <ChannelListScreen />;
};

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

export default ChannelListScreenPage;
