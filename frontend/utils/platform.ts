import { Platform } from 'react-native';

// Platform detection with React 19 + Expo SDK 53 compatibility
export const isWeb = Platform.OS === 'web';
export const isIOS = Platform.OS === 'ios';
export const isAndroid = Platform.OS === 'android';
export const isMobile = Platform.OS !== 'web';

// Environment variables for platform-specific builds
export const platformEnv = process.env.EXPO_PUBLIC_PLATFORM;
export const buildEnv = process.env.EXPO_PUBLIC_ENV || 'development';
export const nodeEnv = process.env.NODE_ENV || 'development';

// Enhanced platform checks with environment awareness
export const isWebBuild = platformEnv === 'web' || isWeb;
export const isProductionWebBuild = isWebBuild && nodeEnv === 'production';
export const isDevelopmentBuild = buildEnv === 'development';
export const isStagingBuild = buildEnv === 'staging';
export const isProductionBuild = buildEnv === 'production';

// Platform-specific feature flags for React 19 compatibility
export const platformFeatures = {
  // Web builds are production-only due to react-refresh incompatibility
  supportsHotReload: !isWebBuild,
  supportsDevServer: !isWebBuild,
  requiresProductionBuild: isWebBuild,
  supportsWebSockets: true,
  supportsNativeModules: isMobile,
} as const;

// Helper for conditional rendering based on platform
export const PlatformSelect = {
  web: <T>(value: T): T | null => (isWeb ? value : null),
  ios: <T>(value: T): T | null => (isIOS ? value : null),
  android: <T>(value: T): T | null => (isAndroid ? value : null),
  mobile: <T>(value: T): T | null => (isMobile ? value : null),
} as const;

/**
 * Polyfill for React Native SVG hasTouchableProperty function
 * This fixes compatibility issues with React 19 + React Native Web + Expo SDK 53
 */
export function initializeWebPolyfills() {
  if (isWeb && typeof window !== 'undefined') {
    // Polyfill hasTouchableProperty function for react-native-svg
    if (!(window as any).hasTouchableProperty) {
      (window as any).hasTouchableProperty = (props: any) => {
        return Boolean(props?.onPress || props?.onPressIn || props?.onPressOut || props?.onLongPress);
      };
    }

    // Add to global scope for bundler compatibility
    if (typeof (globalThis as any) !== 'undefined') {
      (globalThis as any).hasTouchableProperty = (window as any).hasTouchableProperty;
    }

    console.log('🔧 Web polyfills initialized successfully');
  }
}