import { useState, useCallback } from 'react';
import { useTranslation } from 'react-i18next';

import {
  changeLanguage,
  getCurrentLanguage,
  isLanguageLoaded,
  SupportedLanguage,
  SUPPORTED_LANGUAGES,
} from './index';

/**
 * Custom hook for managing language state and switching
 * Provides loading states and error handling for language changes
 */
export const useLanguage = () => {
  const {} = useTranslation();
  const [isChangingLanguage, setIsChangingLanguage] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Change language with loading state management
   * @param newLanguage The language to switch to
   */
  const handleLanguageChange = useCallback(async (newLanguage: SupportedLanguage) => {
    if (newLanguage === getCurrentLanguage()) {
      return; // Already using this language
    }

    setIsChangingLanguage(true);
    setError(null);

    try {
      await changeLanguage(newLanguage);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to change language';
      setError(errorMessage);
      console.error('Language change failed:', err);
    } finally {
      setIsChangingLanguage(false);
    }
  }, []);

  /**
   * Clear any error state
   */
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  /**
   * Get available languages
   */
  const getAvailableLanguages = useCallback(() => {
    return Object.entries(SUPPORTED_LANGUAGES).map(([code, name]) => ({
      code: code as SupportedLanguage,
      name,
      isLoaded: isLanguageLoaded(code as SupportedLanguage),
      isCurrent: code === getCurrentLanguage(),
    }));
  }, []);

  return {
    currentLanguage: getCurrentLanguage(),
    availableLanguages: getAvailableLanguages(),
    isChangingLanguage,
    error,
    changeLanguage: handleLanguageChange,
    clearError,
    isLanguageLoaded,
  };
};

export default useLanguage;
