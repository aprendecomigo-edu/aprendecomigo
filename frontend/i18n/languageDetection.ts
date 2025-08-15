import * as Localization from 'expo-localization';

import LanguageStorage from './languageStorage';

import { SupportedLanguage } from './index';

/**
 * Enhanced language detection that considers user preferences and device settings
 */
export class LanguageDetection {
  /**
   * Get the device's preferred language with better mapping
   * @returns The device's preferred language mapped to our supported languages
   */
  static getDeviceLanguage(): SupportedLanguage {
    try {
      const locales = Localization.getLocales();

      for (const locale of locales) {
        const languageTag = locale.languageTag;

        // Direct matches
        if (languageTag === 'en-GB' || languageTag === 'pt-PT') {
          return languageTag as SupportedLanguage;
        }

        // Language family matches
        if (languageTag.startsWith('pt')) {
          return 'pt-PT';
        }

        if (languageTag.startsWith('en')) {
          return 'en-GB';
        }
      }

      return 'en-GB'; // Fallback
    } catch (error) {
      console.warn('Failed to get device language, falling back to en-GB:', error);
      return 'en-GB';
    }
  }

  /**
   * Get the best language preference considering saved preferences and device settings
   * Priority: Saved preference > Device language > Fallback (en-GB)
   * @returns Promise that resolves to the best language choice
   */
  static async getBestLanguageChoice(): Promise<SupportedLanguage> {
    try {
      // First, check if user has a saved preference
      const savedLanguage = await LanguageStorage.getPreferredLanguage();
      if (savedLanguage) {
        console.log(`Using saved language preference: ${savedLanguage}`);
        return savedLanguage;
      }

      // Fall back to device language
      const deviceLanguage = this.getDeviceLanguage();
      console.log(`Using device language: ${deviceLanguage}`);
      return deviceLanguage;
    } catch (error) {
      console.error('Failed to determine best language choice:', error);
      return 'en-GB';
    }
  }

  /**
   * Check if the user has set a custom language preference (different from device)
   * @returns Promise that resolves to true if user has overridden device language
   */
  static async hasCustomLanguagePreference(): Promise<boolean> {
    try {
      const savedLanguage = await LanguageStorage.getPreferredLanguage();
      if (!savedLanguage) {
        return false;
      }

      const deviceLanguage = this.getDeviceLanguage();
      return savedLanguage !== deviceLanguage;
    } catch (error) {
      console.error('Failed to check custom language preference:', error);
      return false;
    }
  }

  /**
   * Get language statistics for analytics
   * @returns Object with language preference information
   */
  static async getLanguageStats(): Promise<{
    deviceLanguage: SupportedLanguage;
    savedLanguage: SupportedLanguage | null;
    activeLanguage: SupportedLanguage;
    hasCustomPreference: boolean;
  }> {
    const deviceLanguage = this.getDeviceLanguage();
    const savedLanguage = await LanguageStorage.getPreferredLanguage();
    const activeLanguage = savedLanguage || deviceLanguage;
    const hasCustomPreference = await this.hasCustomLanguagePreference();

    return {
      deviceLanguage,
      savedLanguage,
      activeLanguage,
      hasCustomPreference,
    };
  }
}

export default LanguageDetection;
