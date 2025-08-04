import { useRouter, type Href } from 'expo-router';
import { MessageCircle } from 'lucide-react-native';
import React, { useEffect, useState } from 'react';
import { View, StyleSheet } from 'react-native';

import { Channel, fetchChannels } from '@/api/channelApi';
import MainLayout from '@/components/layouts/MainLayout';
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
  const [selectedChannelId, setSelectedChannelId] = useState<number | undefined>(undefined);

  // Fetch channels on component mount
  useEffect(() => {
    const loadChannels = async () => {
      setIsLoading(true);
      try {
        const data = await fetchChannels();
        const channelsArray = Array.isArray(data) ? data : [];
        setChannels(channelsArray);
        setFilteredChannels(channelsArray);

        // Set the first channel as selected by default
        if (channelsArray.length > 0 && !selectedChannelId) {
          setSelectedChannelId(channelsArray[0].id);
        }
      } catch (error) {
        console.error('Error loading channels:', error);
        setChannels([]);
        setFilteredChannels([]);
      } finally {
        setIsLoading(false);
      }
    };

    loadChannels();
  }, []);

  // Filter channels based on search term
  useEffect(() => {
    const channelsArray = Array.isArray(channels) ? channels : [];
    if (searchTerm.trim() === '') {
      setFilteredChannels(channelsArray);
    } else {
      const searchTermLower = searchTerm.toLowerCase();
      const filtered = channelsArray.filter(
        channel =>
          channel.name.toLowerCase().includes(searchTermLower) ||
          (channel.last_message?.content || '').toLowerCase().includes(searchTermLower)
      );
      setFilteredChannels(filtered);
    }
  }, [searchTerm, channels]);

  return (
    <Box className="flex-1 bg-gray-50">
      <View style={styles.container}>
        {isLoading ? (
          <VStack className="flex-1 justify-center items-center">
            <Text>Carregando conversas...</Text>
          </VStack>
        ) : !Array.isArray(channels) || channels.length === 0 ? (
          <Center className="flex-1 p-8">
            <Icon as={MessageCircle} size="xl" className="text-gray-300 mb-4" />
            <Text className="text-xl font-bold text-gray-600 mb-2">Nenhuma conversa ainda</Text>
            <Text className="text-gray-500 text-center">
              As conversas aparecerão aqui quando você tiver professores e alunos cadastrados na
              escola.
            </Text>
          </Center>
        ) : (
          <VStack className="p-6" space="md">
            <Text className="text-xl font-bold text-gray-900">Mensagens</Text>
            <Text className="text-gray-600">
              Sistema de mensagens disponível em breve.
            </Text>
          </VStack>
        )}
      </View>
    </Box>
  );
};

// Wrap the ChannelListContent with MainLayout for consistent navigation
export const ChatList = () => {
  return (
    <MainLayout _title="Mensagens">
      <ChannelListContent />
    </MainLayout>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    flexDirection: 'row',
    position: 'relative',
  },
});

export default ChatList;