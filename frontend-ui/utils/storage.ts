import AsyncStorage from '@react-native-async-storage/async-storage';
import { Platform } from 'react-native';

/**
 * Platform-aware storage utility that provides a consistent interface
 * for storing data across web and mobile platforms.
 * 
 * On web: Uses localStorage as fallback if AsyncStorage fails
 * On mobile: Uses AsyncStorage directly
 */
class PlatformStorage {
  /**
   * Get an item from storage
   */
  async getItem(key: string): Promise<string | null> {
    try {
      // Try AsyncStorage first (works on all platforms when properly configured)
      const value = await AsyncStorage.getItem(key);
      return value;
    } catch (error) {
      // If AsyncStorage fails on web, fallback to localStorage
      if (Platform.OS === 'web') {
        try {
          return localStorage.getItem(key);
        } catch (localStorageError) {
          console.error('Both AsyncStorage and localStorage failed:', {
            asyncStorageError: error,
            localStorageError
          });
          return null;
        }
      }
      
      console.error('AsyncStorage.getItem failed:', error);
      return null;
    }
  }

  /**
   * Set an item in storage
   */
  async setItem(key: string, value: string): Promise<void> {
    try {
      // Try AsyncStorage first
      await AsyncStorage.setItem(key, value);
    } catch (error) {
      // If AsyncStorage fails on web, fallback to localStorage
      if (Platform.OS === 'web') {
        try {
          localStorage.setItem(key, value);
          return;
        } catch (localStorageError) {
          console.error('Both AsyncStorage and localStorage failed:', {
            asyncStorageError: error,
            localStorageError
          });
          throw new Error('Failed to store data');
        }
      }
      
      console.error('AsyncStorage.setItem failed:', error);
      throw error;
    }
  }

  /**
   * Remove an item from storage
   */
  async removeItem(key: string): Promise<void> {
    try {
      // Try AsyncStorage first
      await AsyncStorage.removeItem(key);
    } catch (error) {
      // If AsyncStorage fails on web, fallback to localStorage
      if (Platform.OS === 'web') {
        try {
          localStorage.removeItem(key);
          return;
        } catch (localStorageError) {
          console.error('Both AsyncStorage and localStorage failed:', {
            asyncStorageError: error,
            localStorageError
          });
          throw new Error('Failed to remove data');
        }
      }
      
      console.error('AsyncStorage.removeItem failed:', error);
      throw error;
    }
  }

  /**
   * Clear all storage (use with caution)
   */
  async clear(): Promise<void> {
    try {
      await AsyncStorage.clear();
    } catch (error) {
      if (Platform.OS === 'web') {
        try {
          localStorage.clear();
          return;
        } catch (localStorageError) {
          console.error('Both AsyncStorage and localStorage failed:', {
            asyncStorageError: error,
            localStorageError
          });
          throw new Error('Failed to clear storage');
        }
      }
      
      console.error('AsyncStorage.clear failed:', error);
      throw error;
    }
  }

  /**
   * Get all keys from storage
   */
  async getAllKeys(): Promise<readonly string[]> {
    try {
      return await AsyncStorage.getAllKeys();
    } catch (error) {
      if (Platform.OS === 'web') {
        try {
          return Object.keys(localStorage);
        } catch (localStorageError) {
          console.error('Both AsyncStorage and localStorage failed:', {
            asyncStorageError: error,
            localStorageError
          });
          return [];
        }
      }
      
      console.error('AsyncStorage.getAllKeys failed:', error);
      return [];
    }
  }
}

// Export singleton instance
export const storage = new PlatformStorage();

// Export individual methods for convenience
export const { getItem, setItem, removeItem, clear, getAllKeys } = storage;

// Default export for backward compatibility
export default storage;