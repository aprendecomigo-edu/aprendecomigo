import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';
import * as SecureStore from 'expo-secure-store';

import { API_URL } from '@/constants/api';

// Helper to get token from secure storage
const getToken = async (): Promise<string | null> => {
  try {
    // Try to use SecureStore first
    const token = await SecureStore.getItemAsync('auth_token');
    if (token) return token;

    // If not found in SecureStore, check AsyncStorage (for backward compatibility)
    return await AsyncStorage.getItem('auth_token');
  } catch (error) {
    // Fall back to AsyncStorage if SecureStore fails
    return await AsyncStorage.getItem('auth_token');
  }
};

// Create axios instance
const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor to add auth token
apiClient.interceptors.request.use(
  async config => {
    // Get token from storage
    const token = await getToken();

    // If token exists, add to headers
    if (token) {
      config.headers.Authorization = `Token ${token}`;
    }

    return config;
  },
  error => {
    return Promise.reject(error);
  }
);

// Add response interceptor to handle unauthorized errors
apiClient.interceptors.response.use(
  response => response,
  async error => {
    const originalRequest = error.config;

    // If error is 401 and not already retrying
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      // Handle unauthorized error
      return Promise.reject(error);
    }

    return Promise.reject(error);
  }
);

export default apiClient;
