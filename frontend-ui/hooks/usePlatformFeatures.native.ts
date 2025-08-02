import { Platform, Linking } from 'react-native';

interface PlatformFeatures {
  hasHover: boolean;
  hasKeyboard: boolean;
  hasTouch: boolean;
  hasClipboard: boolean;
  hasNotifications: boolean;
  hasFileSystem: boolean;
  hasCamera: boolean;
  hasGeolocation: boolean;
  canOpenExternalLinks: boolean;
  supportsMultipleWindows: boolean;
  supportsContextMenus: boolean;
}

export function usePlatformFeatures(): PlatformFeatures {
  return {
    hasHover: false, // Native doesn't support hover
    hasKeyboard: true, // Virtual keyboards available
    hasTouch: true, // Native is touch-first
    hasClipboard: true, // React Native Clipboard API
    hasNotifications: true, // Push notifications supported
    hasFileSystem: Platform.OS === 'ios' || Platform.OS === 'android', // Document picker available
    hasCamera: true, // Camera access available on mobile
    hasGeolocation: true, // Location services available
    canOpenExternalLinks: Linking.canOpenURL !== undefined,
    supportsMultipleWindows: false, // Single window/app focus
    supportsContextMenus: false, // No right-click context menus
  };
}