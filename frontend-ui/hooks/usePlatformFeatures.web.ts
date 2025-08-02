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
  const hasTouch = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
  
  return {
    hasHover: true, // Web supports hover interactions
    hasKeyboard: true, // Web has keyboard support
    hasTouch, // Detected based on browser capabilities
    hasClipboard: typeof navigator.clipboard !== 'undefined',
    hasNotifications: 'Notification' in window,
    hasFileSystem: 'showOpenFilePicker' in window, // File System Access API
    hasCamera: 'mediaDevices' in navigator,
    hasGeolocation: 'geolocation' in navigator,
    canOpenExternalLinks: true,
    supportsMultipleWindows: true,
    supportsContextMenus: true,
  };
}