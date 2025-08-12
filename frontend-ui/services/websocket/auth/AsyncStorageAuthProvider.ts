/**
 * AsyncStorageAuthProvider - Authentication provider for WebSocket connections
 * 
 * This provider uses AsyncStorage to retrieve authentication tokens,
 * maintaining compatibility with the existing authentication system.
 */

import AsyncStorage from '@react-native-async-storage/async-storage';
import { AuthProvider } from '../types';

export class AsyncStorageAuthProvider implements AuthProvider {
  private tokenKey: string;

  constructor(tokenKey: string = 'auth_token') {
    this.tokenKey = tokenKey;
  }

  async getToken(): Promise<string | null> {
    try {
      return await AsyncStorage.getItem(this.tokenKey);
    } catch (error) {
      console.error('Failed to get auth token from AsyncStorage:', error);
      return null;
    }
  }

  onAuthError(): void {
    console.error('WebSocket authentication failed');
    // In a real implementation, this might trigger a logout or token refresh
  }
}