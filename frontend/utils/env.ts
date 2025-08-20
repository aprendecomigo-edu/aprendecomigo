/**
 * Environment utilities for React 19 + Expo SDK 53 compatibility
 *
 * This utility provides safe environment detection that works across all platforms:
 * - React Native (mobile): Uses __DEV__ when available
 * - Web: Uses NODE_ENV or build-time environment detection
 * - Production builds: Always false for performance
 */

import { isWeb, isIOS, isAndroid } from './platform';

/**
 * Safe development environment detection
 * Works in React Native, Web, and all build environments
 */
export const isDev = (() => {
  try {
    // First try React Native __DEV__ (preferred for mobile)
    if (typeof __DEV__ !== 'undefined') {
      return __DEV__;
    }

    // Fallback to Node.js environment (web builds)
    if (typeof process !== 'undefined' && process.env) {
      return process.env.NODE_ENV === 'development';
    }

    // Final fallback - assume production for safety
    return false;
  } catch {
    // If any error occurs, assume production
    return false;
  }
})();

/**
 * Safe development-only console logging
 * Only logs in development, no-op in production
 */
export const devLog = (...args: any[]) => {
  if (isDev) {
    console.log(...args);
  }
};

/**
 * Safe development-only console warning
 * Only warns in development, no-op in production
 */
export const devWarn = (...args: any[]) => {
  if (isDev) {
    console.warn(...args);
  }
};

/**
 * Safe development-only console error
 * Only errors in development, no-op in production
 */
export const devError = (...args: any[]) => {
  if (isDev) {
    console.error(...args);
  }
};

/**
 * Conditional development execution
 * Only executes callback in development
 */
export const runInDev = (callback: () => void) => {
  if (isDev) {
    try {
      callback();
    } catch (error) {
      // Silently handle errors in production-like environments
      if (isDev) {
        console.error('Error in development-only code:', error);
      }
    }
  }
};

/**
 * Build environment detection
 */
export const buildEnv = (() => {
  try {
    if (typeof process !== 'undefined' && process.env) {
      return process.env.EXPO_PUBLIC_ENV || process.env.NODE_ENV || 'production';
    }
    return 'production';
  } catch {
    return 'production';
  }
})();

/**
 * Platform detection for cross-platform compatibility
 * Note: Uses platform utilities which already handle platform detection properly
 */
export const platform = (() => {
  try {
    // Use the platform utilities which already handle platform detection
    if (isWeb) {
      return 'web';
    } else if (isIOS) {
      return 'ios';
    } else if (isAndroid) {
      return 'android';
    }

    // Node.js/SSR detection
    if (typeof process !== 'undefined') {
      return 'node';
    }

    return 'unknown';
  } catch {
    return 'unknown';
  }
})();
