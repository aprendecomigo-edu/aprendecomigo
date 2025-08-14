import * as Localization from 'expo-localization';
import i18n from 'i18next';
import Backend from 'i18next-resources-to-backend';
import { initReactI18next } from 'react-i18next';

// Import translation files
import enGB from './locales/en-GB.json';
import ptPT from './locales/pt-PT.json';

const resources = {
  'en-GB': {
    translation: enGB,
  },
  'pt-PT': {
    translation: ptPT,
  },
};

// Get device locale with fallback
const getDeviceLanguage = () => {
  const deviceLocale = Localization.getLocales()[0];
  const languageTag = deviceLocale?.languageTag || 'en-GB';

  // Map device locales to our supported locales
  if (languageTag.startsWith('pt')) {
    return 'pt-PT';
  }
  return 'en-GB';
};

i18n
  .use(Backend(() => import('./locales/en-GB.json')))
  .use(Backend(() => import('./locales/pt-PT.json')))
  .use(initReactI18next)
  .init({
    resources,
    lng: getDeviceLanguage(),
    fallbackLng: 'en-GB',
    debug: __DEV__,

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

export default i18n;
