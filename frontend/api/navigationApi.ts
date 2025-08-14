import apiClient from './apiClient';

// Types for API responses
export interface SearchResult {
  id: string;
  type: 'teacher' | 'student' | 'class';
  title: string;
  subtitle?: string;
  avatar?: string;
  route: string;
  metadata?: Record<string, any>;
}

export interface GlobalSearchResponse {
  results: SearchResult[];
  total_count: number;
  categories: {
    [key: string]: number;
  };
}

export interface NotificationCountsResponse {
  pending_invitations: number;
  new_registrations: number;
  incomplete_profiles: number;
  overdue_tasks: number;
  total_unread: number;
}

export interface NavigationPreferences {
  collapsed_sidebar: boolean;
  preferred_landing_page: string;
  quick_actions_visible: boolean;
  notification_preferences: {
    show_badges: boolean;
    categories: string[];
  };
  recent_searches: string[];
}

// API functions
export const navigationApi = {
  // Global search API
  async globalSearch(
    query: string,
    types?: string[],
    limit: number = 10
  ): Promise<GlobalSearchResponse> {
    const params = new URLSearchParams({
      q: query,
      limit: limit.toString(),
    });

    if (types && types.length > 0) {
      params.append('types', types.join(','));
    }

    const response = await apiClient.get(`accounts/search/global/?${params.toString()}`);
    return response.data;
  },

  // Get notification counts
  async getNotificationCounts(): Promise<NotificationCountsResponse> {
    const response = await apiClient.get('notifications/counts/');
    return response.data;
  },

  // Get user navigation preferences
  async getNavigationPreferences(): Promise<NavigationPreferences> {
    const response = await apiClient.get('accounts/users/navigation_preferences/');
    return response.data;
  },

  // Update user navigation preferences
  async updateNavigationPreferences(
    preferences: Partial<NavigationPreferences>
  ): Promise<NavigationPreferences> {
    const response = await apiClient.post('accounts/users/navigation_preferences/', preferences);
    return response.data;
  },

  // Save recent search
  async saveRecentSearch(query: string): Promise<void> {
    await apiClient.post('accounts/users/navigation_preferences/', {
      recent_searches_add: query,
    });
  },

  // Clear recent searches
  async clearRecentSearches(): Promise<void> {
    await apiClient.post('accounts/users/navigation_preferences/', {
      recent_searches_clear: true,
    });
  },
};

export default navigationApi;
