import AsyncStorage from '@react-native-async-storage/async-storage';

import type { StorageInterface } from './storage';

/**
 * Web-specific storage utility that uses localStorage as primary storage
 * with AsyncStorage as fallback for React Native Web compatibility.
 */
class WebStorage implements StorageInterface {
  /**
   * Get an item from storage (localStorage first, AsyncStorage fallback)
   */
  async getItem(key: string): Promise<string | null> {
    try {
      // Try localStorage first on web
      return localStorage.getItem(key);
    } catch (localStorageError) {
      // Fallback to AsyncStorage for React Native Web
      try {
        const value = await AsyncStorage.getItem(key);
        return value;
      } catch (asyncStorageError) {
        console.error('Both localStorage and AsyncStorage failed:', {
          localStorageError,
          asyncStorageError,
        });
        return null;
      }
    }
  }

  /**
   * Set an item in storage (localStorage first, AsyncStorage fallback)
   */
  async setItem(key: string, value: string): Promise<void> {
    try {
      // Try localStorage first on web
      localStorage.setItem(key, value);
    } catch (localStorageError) {
      // Fallback to AsyncStorage for React Native Web
      try {
        await AsyncStorage.setItem(key, value);
      } catch (asyncStorageError) {
        console.error('Both localStorage and AsyncStorage failed:', {
          localStorageError,
          asyncStorageError,
        });
        throw new Error('Failed to store data');
      }
    }
  }

  /**
   * Remove an item from storage (localStorage first, AsyncStorage fallback)
   */
  async removeItem(key: string): Promise<void> {
    try {
      // Try localStorage first on web
      localStorage.removeItem(key);
    } catch (localStorageError) {
      // Fallback to AsyncStorage for React Native Web
      try {
        await AsyncStorage.removeItem(key);
      } catch (asyncStorageError) {
        console.error('Both localStorage and AsyncStorage failed:', {
          localStorageError,
          asyncStorageError,
        });
        throw new Error('Failed to remove data');
      }
    }
  }

  /**
   * Clear all storage (localStorage first, AsyncStorage fallback)
   */
  async clear(): Promise<void> {
    try {
      // Try localStorage first on web
      localStorage.clear();
    } catch (localStorageError) {
      // Fallback to AsyncStorage for React Native Web
      try {
        await AsyncStorage.clear();
      } catch (asyncStorageError) {
        console.error('Both localStorage and AsyncStorage failed:', {
          localStorageError,
          asyncStorageError,
        });
        throw new Error('Failed to clear storage');
      }
    }
  }

  /**
   * Get all keys from storage (localStorage first, AsyncStorage fallback)
   */
  async getAllKeys(): Promise<readonly string[]> {
    try {
      // Try localStorage first on web
      return Object.keys(localStorage);
    } catch (localStorageError) {
      // Fallback to AsyncStorage for React Native Web
      try {
        return await AsyncStorage.getAllKeys();
      } catch (asyncStorageError) {
        console.error('Both localStorage and AsyncStorage failed:', {
          localStorageError,
          asyncStorageError,
        });
        return [];
      }
    }
  }
}

// Export singleton instance
export const storage = new WebStorage();

// Export individual methods for convenience
export const { getItem, setItem, removeItem, clear, getAllKeys } = storage;

// Default export for backward compatibility
export default storage;
