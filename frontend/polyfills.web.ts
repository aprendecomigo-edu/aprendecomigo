/**
 * Web polyfills for React Native compatibility
 * This file is imported at the very top of the app to ensure polyfills are available
 * before any other modules that might need them.
 */

// Immediately execute polyfills on web platform
if (typeof window !== 'undefined') {
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

  // Also add to the global 't' object that seems to be used by the bundler
  if (typeof (globalThis as any).t === 'undefined') {
    (globalThis as any).t = {};
  }
  if ((globalThis as any).t) {
    (globalThis as any).t.hasTouchableProperty = (window as any).hasTouchableProperty;
  }

  console.log('🔧 React Native Web polyfills initialized');
}

export {};