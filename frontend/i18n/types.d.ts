/**
 * Type declarations for i18n module
 */

// Global type for React Native development flag
declare const __DEV__: boolean;

// JSON module declarations for locale files
declare module '*.json' {
  const value: any;
  export default value;
}

// Locale file specific declarations
declare module './locales/en-GB.json' {
  const translations: Record<string, any>;
  export default translations;
}

declare module './locales/pt-PT.json' {
  const translations: Record<string, any>;
  export default translations;
}
