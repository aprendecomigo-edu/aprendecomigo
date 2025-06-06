import apiClient from './apiClient';

export interface Channel {
  id: string;
  name: string;
  lastMessage: string;
  time: string;
  unreadCount: number;
  avatarText: string;
  type: 'channel' | 'dm';
  participants?: {
    id: string;
    name: string;
    avatar: string;
    isOnline: boolean;
  }[];
  onlineCount?: number;
}

/**
 * Fetch channels for the current user
 */
export const fetchChannels = async (): Promise<Channel[]> => {
  try {
    // TODO: The backend Channel model doesn't match the frontend interface yet
    // For now, return empty array until the backend implements the required fields:
    // lastMessage, time, unreadCount, avatarText, type, onlineCount
    const response = await apiClient.get('/channels/');
    console.log('Backend channels response:', response.data);

    // Return empty array since we don't have real data yet and no longer want placeholder data
    return [];
  } catch (error) {
    console.error('Error fetching channels:', error);
    // Return empty array if API call fails - no more sample data
    return [];
  }
};
