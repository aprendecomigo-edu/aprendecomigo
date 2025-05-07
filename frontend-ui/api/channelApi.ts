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
    const response = await apiClient.get('/api/channels/');
    return response.data;
  } catch (error) {
    console.error('Error fetching channels:', error);
    // Return sample data if API call fails
    return getSampleChannels();
  }
};

/**
 * Get sample channels data for fallback
 */
const getSampleChannels = (): Channel[] => {
  return [
    {
      id: '1',
      name: '9° Ano A',
      lastMessage: 'Dúvida sobre a lição de casa',
      time: '10:30',
      unreadCount: 3,
      avatarText: '9A',
      type: 'channel',
      onlineCount: 5
    },
    {
      id: '2',
      name: 'Professores de Matemática',
      lastMessage: 'Reunião amanhã às 14h',
      time: '09:15',
      unreadCount: 0,
      avatarText: 'PM',
      type: 'channel',
      onlineCount: 3
    },
    {
      id: '3',
      name: 'Coordenação Pedagógica',
      lastMessage: 'Relatórios do bimestre',
      time: 'Ontem',
      unreadCount: 5,
      avatarText: 'CP',
      type: 'channel',
      onlineCount: 2
    },
    {
      id: '4',
      name: 'Prof. Maria Silva',
      lastMessage: 'Pode me enviar o planejamento?',
      time: 'Ontem',
      unreadCount: 0,
      avatarText: 'MS',
      type: 'dm',
      participants: [
        {
          id: '123',
          name: 'Maria Silva',
          avatar: 'MS',
          isOnline: true
        }
      ]
    },
    {
      id: '5',
      name: 'João Santos',
      lastMessage: 'Olá, como vai?',
      time: '23/05',
      unreadCount: 1,
      avatarText: 'JS',
      type: 'dm',
      participants: [
        {
          id: '456',
          name: 'João Santos',
          avatar: 'JS',
          isOnline: false
        }
      ]
    },
    {
      id: '6',
      name: 'Ana Oliveira',
      lastMessage: 'Conseguiu verificar aqueles documentos?',
      time: '22/05',
      unreadCount: 0,
      avatarText: 'AO',
      type: 'dm',
      participants: [
        {
          id: '789',
          name: 'Ana Oliveira',
          avatar: 'AO',
          isOnline: true
        }
      ]
    }
  ];
};
