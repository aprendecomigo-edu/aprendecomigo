/**
 * Utility exports for the optimized i18n implementation
 * This file provides easy access to all language-related utilities
 */

// Import functions locally to avoid circular dependencies
import {
  getCurrentLanguage as _getCurrentLanguage,
  SUPPORTED_LANGUAGES as _SUPPORTED_LANGUAGES,
} from './index';

// Main i18n instance and core functions
export {
  default as i18n,
  changeLanguage,
  getCurrentLanguage,
  isLanguageLoaded,
  SUPPORTED_LANGUAGES,
  type SupportedLanguage,
} from './index';

// React hooks
export { useLanguage } from './useLanguage';

// Storage utilities
export { default as LanguageStorage } from './languageStorage';

// Detection utilities
export { default as LanguageDetection } from './languageDetection';

// React components (commented out to avoid JSX compilation issues in utils)
// export { LanguageSwitcher } from './LanguageSwitcher';

/**
 * Quick utility functions for common operations
 */

/**
 * Check if the current language is right-to-left
 * @returns True if current language uses RTL layout
 */
export const isRTL = (): boolean => {
  // None of our current languages use RTL, but this is useful for future expansion
  const rtlLanguages: string[] = [];
  return rtlLanguages.includes(_getCurrentLanguage());
};

/**
 * Get the current language's display name
 * @returns The human-readable name of the current language
 */
export const getCurrentLanguageName = (): string => {
  const currentLang = _getCurrentLanguage();
  return _SUPPORTED_LANGUAGES[currentLang];
};

/**
 * Format a number according to the current locale
 * @param number The number to format
 * @param options Intl.NumberFormat options
 * @returns Formatted number string
 */
export const formatNumber = (number: number, options?: Intl.NumberFormatOptions): string => {
  const currentLang = _getCurrentLanguage();
  const locale = currentLang === 'pt-PT' ? 'pt-PT' : 'en-GB';

  try {
    return new Intl.NumberFormat(locale, options).format(number);
  } catch (error) {
    console.warn('Failed to format number:', error);
    return number.toString();
  }
};

/**
 * Format a date according to the current locale
 * @param date The date to format
 * @param options Intl.DateTimeFormat options
 * @returns Formatted date string
 */
export const formatDate = (
  date: Date | string | number,
  options?: Intl.DateTimeFormatOptions,
): string => {
  const currentLang = _getCurrentLanguage();
  const locale = currentLang === 'pt-PT' ? 'pt-PT' : 'en-GB';

  try {
    const dateObj = date instanceof Date ? date : new Date(date);
    return new Intl.DateTimeFormat(locale, options).format(dateObj);
  } catch (error) {
    console.warn('Failed to format date:', error);
    return date.toString();
  }
};

/**
 * Format currency according to the current locale
 * @param amount The amount to format
 * @param currency The currency code (default: EUR)
 * @returns Formatted currency string
 */
export const formatCurrency = (amount: number, currency: string = 'EUR'): string => {
  const currentLang = _getCurrentLanguage();
  const locale = currentLang === 'pt-PT' ? 'pt-PT' : 'en-GB';

  try {
    return new Intl.NumberFormat(locale, {
      style: 'currency',
      currency: currency,
    }).format(amount);
  } catch (error) {
    console.warn('Failed to format currency:', error);
    return `${amount} ${currency}`;
  }
};
