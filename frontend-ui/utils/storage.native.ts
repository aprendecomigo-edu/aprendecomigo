import AsyncStorage from '@react-native-async-storage/async-storage';
import type { StorageInterface } from './storage';

/**
 * Native-specific storage utility that uses AsyncStorage directly
 * for iOS and Android platforms.
 */
class NativeStorage implements StorageInterface {
  /**
   * Get an item from storage using AsyncStorage
   */
  async getItem(key: string): Promise<string | null> {
    try {
      return await AsyncStorage.getItem(key);
    } catch (error) {
      console.error('AsyncStorage.getItem failed:', error);
      return null;
    }
  }

  /**
   * Set an item in storage using AsyncStorage
   */
  async setItem(key: string, value: string): Promise<void> {
    try {
      await AsyncStorage.setItem(key, value);
    } catch (error) {
      console.error('AsyncStorage.setItem failed:', error);
      throw error;
    }
  }

  /**
   * Remove an item from storage using AsyncStorage
   */
  async removeItem(key: string): Promise<void> {
    try {
      await AsyncStorage.removeItem(key);
    } catch (error) {
      console.error('AsyncStorage.removeItem failed:', error);
      throw error;
    }
  }

  /**
   * Clear all storage using AsyncStorage
   */
  async clear(): Promise<void> {
    try {
      await AsyncStorage.clear();
    } catch (error) {
      console.error('AsyncStorage.clear failed:', error);
      throw error;
    }
  }

  /**
   * Get all keys from storage using AsyncStorage
   */
  async getAllKeys(): Promise<readonly string[]> {
    try {
      return await AsyncStorage.getAllKeys();
    } catch (error) {
      console.error('AsyncStorage.getAllKeys failed:', error);
      return [];
    }
  }
}

// Export singleton instance
export const storage = new NativeStorage();

// Export individual methods for convenience
export const { getItem, setItem, removeItem, clear, getAllKeys } = storage;

// Default export for backward compatibility
export default storage;