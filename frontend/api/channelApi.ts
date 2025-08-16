import apiClient from './apiClient';

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
}

export interface Message {
  id: number;
  channel: number;
  sender: User;
  content: string;
  timestamp: string;
  file?: string;
  reactions: any[];
  attachments: any[];
}

export interface Channel {
  id: number;
  name: string;
  is_direct: boolean;
  participants: User[];
  online: User[];
  created_at: string;
  updated_at: string;
  last_message: Message | null;
}

/**
 * Fetch channels for the current user
 */
export const fetchChannels = async (): Promise<Channel[]> => {
  try {
    const response = await apiClient.get('/channels/');
    if (__DEV__) {
      console.log('Backend channels response:', response.data);
    }
    // Handle paginated response from Django REST Framework
    if (response.data && Array.isArray(response.data.results)) {
      return response.data.results;
    }
    // Handle direct array response (fallback)
    if (Array.isArray(response.data)) {
      return response.data;
    }
    if (__DEV__) {
      console.warn('Unexpected API response format:', response.data);
    }
    return [];
  } catch (error) {
    console.error('Error fetching channels:', error);
    return [];
  }
};

/**
 * Fetch messages for a specific channel
 */
export const fetchMessages = async (channelId: number): Promise<Message[]> => {
  try {
    const response = await apiClient.get(`/channels/${channelId}/messages/`);
    return response.data;
  } catch (error) {
    console.error('Error fetching messages:', error);
    return [];
  }
};

/**
 * Send a message to a channel
 */
export const sendMessage = async (
  channelId: number,
  content: string,
  file?: File,
): Promise<Message> => {
  try {
    const formData = new FormData();
    formData.append('content', content);
    if (file) {
      formData.append('file', file);
    }

    const response = await apiClient.post(`/channels/${channelId}/send_message/`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  } catch (error) {
    console.error('Error sending message:', error);
    throw error;
  }
};

/**
 * Create a new channel
 */
export const createChannel = async (
  name: string,
  isDirect: boolean,
  participantIds: number[],
): Promise<Channel> => {
  try {
    const response = await apiClient.post('/channels/', {
      name,
      is_direct: isDirect,
      participant_ids: participantIds,
    });
    return response.data;
  } catch (error) {
    console.error('Error creating channel:', error);
    throw error;
  }
};

/**
 * Search users
 */
export const searchUsers = async (query: string): Promise<User[]> => {
  try {
    const response = await apiClient.get(`/users/?search=${encodeURIComponent(query)}`);
    if (__DEV__) {
      console.log('Backend users search response:', response.data);
    }
    // Handle paginated response from Django REST Framework
    if (response.data && Array.isArray(response.data.results)) {
      return response.data.results;
    }
    // Handle direct array response (fallback)
    if (Array.isArray(response.data)) {
      return response.data;
    }
    if (__DEV__) {
      console.warn('Unexpected users API response format:', response.data);
    }
    return [];
  } catch (error) {
    console.error('Error searching users:', error);
    return [];
  }
};
