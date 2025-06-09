import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';
import * as SecureStore from 'expo-secure-store';

import { API_URL } from '@/constants/api';

// Authentication error callback - will be set by auth context
let authErrorCallback: (() => void) | null = null;

// Function to set the auth error callback (called by auth context)
export const setAuthErrorCallback = (callback: (() => void) | null) => {
  authErrorCallback = callback;
};

// Helper to get token from secure storage
const getToken = async (): Promise<string | null> => {
  try {
    // Try to use SecureStore first
    const token = await SecureStore.getItemAsync('auth_token');
    if (token) return token;

    // If not found in SecureStore, check AsyncStorage (for backward compatibility)
    return await AsyncStorage.getItem('auth_token');
  } catch {
    // Fall back to AsyncStorage if SecureStore fails
    return await AsyncStorage.getItem('auth_token');
  }
};

// Helper to remove token from secure storage
const removeToken = async () => {
  try {
    // Try to use SecureStore first
    await SecureStore.deleteItemAsync('auth_token');
    // Also clear from AsyncStorage (for backward compatibility)
    await AsyncStorage.removeItem('auth_token');
  } catch {
    // Fall back to AsyncStorage if SecureStore fails
    await AsyncStorage.removeItem('auth_token');
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

      // Clear the invalid token
      await removeToken();

      // Notify auth context of the error
      if (authErrorCallback) {
        authErrorCallback();
      }

      // Create a custom error that components can detect
      const authError = new Error('Authentication failed - token expired or invalid');
      authError.name = 'AuthenticationError';
      error.isAuthenticationError = true;

      return Promise.reject(error);
    }

    return Promise.reject(error);
  }
);

export default apiClient;
