import AsyncStorage from '@react-native-async-storage/async-storage';

import { SupportedLanguage } from './index';

const LANGUAGE_STORAGE_KEY = 'user_preferred_language';

/**
 * Utility functions for persisting user language preferences
 */
export class LanguageStorage {
  /**
   * Save the user's preferred language to storage
   * @param language The language to save
   */
  static async savePreferredLanguage(language: SupportedLanguage): Promise<void> {
    try {
      await AsyncStorage.setItem(LANGUAGE_STORAGE_KEY, language);
    } catch (error) {
      console.error('Failed to save preferred language:', error);
    }
  }

  /**
   * Get the user's preferred language from storage
   * @returns The saved language or null if not found
   */
  static async getPreferredLanguage(): Promise<SupportedLanguage | null> {
    try {
      const savedLanguage = await AsyncStorage.getItem(LANGUAGE_STORAGE_KEY);
      return savedLanguage as SupportedLanguage | null;
    } catch (error) {
      console.error('Failed to get preferred language:', error);
      return null;
    }
  }

  /**
   * Clear the saved language preference
   */
  static async clearPreferredLanguage(): Promise<void> {
    try {
      await AsyncStorage.removeItem(LANGUAGE_STORAGE_KEY);
    } catch (error) {
      console.error('Failed to clear preferred language:', error);
    }
  }

  /**
   * Check if a language preference is saved
   * @returns True if a preference exists
   */
  static async hasPreferredLanguage(): Promise<boolean> {
    try {
      const savedLanguage = await AsyncStorage.getItem(LANGUAGE_STORAGE_KEY);
      return savedLanguage !== null;
    } catch (error) {
      console.error('Failed to check for preferred language:', error);
      return false;
    }
  }
}

export default LanguageStorage;
