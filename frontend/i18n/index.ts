import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

import LanguageDetection from './languageDetection';
import LanguageStorage from './languageStorage';

// Supported languages
export const SUPPORTED_LANGUAGES = {
  'en-GB': 'English',
  'pt-PT': 'Português',
} as const;

export type SupportedLanguage = keyof typeof SUPPORTED_LANGUAGES;

// State management for loading
let isInitialized = false;
let currentLoadingPromise: Promise<any> | null = null;

/**
 * Dynamically loads a locale file on demand
 * @param language The language code to load
 * @returns Promise that resolves with the translation data
 */
const loadLocale = async (language: SupportedLanguage) => {
  try {
    switch (language) {
      case 'pt-PT':
        return await import('./locales/pt-PT.json');
      case 'en-GB':
      default:
        return await import('./locales/en-GB.json');
    }
  } catch (error) {
    console.warn(`Failed to load locale ${language}, falling back to en-GB:`, error);
    return await import('./locales/en-GB.json');
  }
};

/**
 * Get the best language choice considering saved preferences and device settings
 * @returns Promise that resolves to the preferred language
 */
const getBestLanguageChoice = async (): Promise<SupportedLanguage> => {
  return await LanguageDetection.getBestLanguageChoice();
};

/**
 * Initialize i18n with the user's preferred language only
 * This reduces initial bundle size by loading only one locale
 */
const initializeI18n = async (): Promise<void> => {
  if (isInitialized) {
    return;
  }

  if (currentLoadingPromise) {
    return currentLoadingPromise;
  }

  currentLoadingPromise = (async () => {
    try {
      const userLanguage = await getBestLanguageChoice();
      const translations = await loadLocale(userLanguage);

      await i18n.use(initReactI18next).init({
        resources: {
          [userLanguage]: {
            translation: translations,
          },
        },
        lng: userLanguage,
        fallbackLng: 'en-GB',
        debug: process.env.NODE_ENV === 'development',

        interpolation: {
          escapeValue: false, // React already escapes by default
        },

        react: {
          useSuspense: false,
        },

        // Cache configuration
        cache: {
          enabled: true,
        },

        // Namespace configuration
        defaultNS: 'translation',
        ns: ['translation'],
      });

      isInitialized = true;
      console.log(`i18n initialized with language: ${userLanguage}`);
    } catch (error) {
      console.error('Failed to initialize i18n:', error);
      throw error;
    } finally {
      currentLoadingPromise = null;
    }
  })();

  return currentLoadingPromise;
};

/**
 * Change language dynamically, loading the locale on demand if needed
 * @param newLanguage The language to switch to
 * @returns Promise that resolves when language change is complete
 */
export const changeLanguage = async (newLanguage: SupportedLanguage): Promise<void> => {
  try {
    // Ensure i18n is initialized
    if (!isInitialized) {
      await initializeI18n();
    }

    // Check if we already have this language loaded
    if (!i18n.hasResourceBundle(newLanguage, 'translation')) {
      console.log(`Loading locale on demand: ${newLanguage}`);
      const translations = await loadLocale(newLanguage);

      // Add the new resource bundle
      i18n.addResourceBundle(
        newLanguage,
        'translation',
        translations,
        true, // deep merge
        true // overwrite
      );
    }

    // Change to the new language
    await i18n.changeLanguage(newLanguage);

    // Save the new language preference
    await LanguageStorage.savePreferredLanguage(newLanguage);
    console.log(`Language changed to: ${newLanguage}`);
  } catch (error) {
    console.error(`Failed to change language to ${newLanguage}:`, error);
    // Fallback to English if the language change fails
    if (newLanguage !== 'en-GB') {
      console.log('Falling back to en-GB');
      await changeLanguage('en-GB');
    }
    throw error;
  }
};

/**
 * Get the current language
 * @returns The current language code
 */
export const getCurrentLanguage = (): SupportedLanguage => {
  return (i18n.language as SupportedLanguage) || 'en-GB';
};

/**
 * Check if a language is currently loaded
 * @param language The language to check
 * @returns True if the language is loaded
 */
export const isLanguageLoaded = (language: SupportedLanguage): boolean => {
  return i18n.hasResourceBundle(language, 'translation');
};

// Initialize i18n with the device's preferred language
initializeI18n().catch(error => {
  console.error('Failed to initialize i18n:', error);
});

export default i18n;
