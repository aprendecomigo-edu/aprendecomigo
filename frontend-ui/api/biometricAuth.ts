import AsyncStorage from '@react-native-async-storage/async-storage';
import * as LocalAuthentication from 'expo-local-authentication';
import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';

// Secure key names for storing biometric preferences
const BIOMETRIC_ENABLED_KEY = 'biometric_auth_enabled';
const BIOMETRIC_USER_EMAIL_KEY = 'biometric_user_email';

/**
 * Check if device supports biometric authentication
 * @returns Promise resolving to a boolean indicating if biometrics are available
 */
export const isBiometricAvailable = async (): Promise<boolean> => {
  try {
    const compatible = await LocalAuthentication.hasHardwareAsync();
    const enrolled = await LocalAuthentication.isEnrolledAsync();
    return compatible && enrolled;
  } catch (error) {
    console.error('Error checking biometric availability:', error);
    return false;
  }
};

/**
 * Authenticate using device biometrics
 * @param promptMessage Message to display to user during authentication
 * @returns Promise resolving to authentication result
 */
export const authenticateWithBiometrics = async (
  promptMessage = 'Authenticate to log in'
): Promise<{ success: boolean; error?: string }> => {
  try {
    const available = await isBiometricAvailable();
    if (!available) {
      return {
        success: false,
        error: 'Biometric authentication is not available on this device',
      };
    }

    const result = await LocalAuthentication.authenticateAsync({
      promptMessage,
      fallbackLabel: 'Use passcode',
      // On Android we can specify what types of authentication to use
      ...(Platform.OS === 'android'
        ? {
            requireConfirmation: false,
          }
        : {}),
    });

    return { success: result.success };
  } catch (error) {
    console.error('Biometric authentication error:', error);
    return {
      success: false,
      error: 'Authentication failed. Please try again.',
    };
  }
};

/**
 * Enable biometric authentication for a user
 * @param email The user's email address
 * @returns Promise resolving to a boolean indicating success
 */
export const enableBiometricAuth = async (email: string): Promise<boolean> => {
  try {
    // Verify biometrics are available
    const available = await isBiometricAvailable();
    if (!available) {
      return false;
    }

    // Authenticate before enabling to ensure it's really the user
    const authResult = await authenticateWithBiometrics('Authenticate to enable biometric login');

    if (!authResult.success) {
      return false;
    }

    // Store biometric preference and user email
    await SecureStore.setItemAsync(BIOMETRIC_ENABLED_KEY, 'true');
    await SecureStore.setItemAsync(BIOMETRIC_USER_EMAIL_KEY, email);

    // Fallback to AsyncStorage if SecureStore fails
    await AsyncStorage.setItem(BIOMETRIC_ENABLED_KEY, 'true');
    await AsyncStorage.setItem(BIOMETRIC_USER_EMAIL_KEY, email);

    return true;
  } catch (error) {
    console.error('Error enabling biometric authentication:', error);
    return false;
  }
};

/**
 * Disable biometric authentication for a user
 * @returns Promise resolving to a boolean indicating success
 */
export const disableBiometricAuth = async (): Promise<boolean> => {
  try {
    // Remove biometric preference and user email
    await SecureStore.deleteItemAsync(BIOMETRIC_ENABLED_KEY);
    await SecureStore.deleteItemAsync(BIOMETRIC_USER_EMAIL_KEY);

    // Also clear from AsyncStorage (for backward compatibility)
    await AsyncStorage.removeItem(BIOMETRIC_ENABLED_KEY);
    await AsyncStorage.removeItem(BIOMETRIC_USER_EMAIL_KEY);

    return true;
  } catch (error) {
    console.error('Error disabling biometric authentication:', error);
    return false;
  }
};

/**
 * Check if biometric authentication is enabled
 * @returns Promise resolving to a boolean indicating if biometrics are enabled
 */
export const isBiometricEnabled = async (): Promise<boolean> => {
  try {
    // Try to use SecureStore first
    let enabled = await SecureStore.getItemAsync(BIOMETRIC_ENABLED_KEY);

    // If not found in SecureStore, check AsyncStorage (for backward compatibility)
    if (!enabled) {
      enabled = await AsyncStorage.getItem(BIOMETRIC_ENABLED_KEY);
    }

    return enabled === 'true';
  } catch (error) {
    console.error('Error checking if biometric auth is enabled:', error);
    return false;
  }
};

/**
 * Get the email address associated with biometric authentication
 * @returns Promise resolving to email string or null if not found
 */
export const getBiometricAuthEmail = async (): Promise<string | null> => {
  try {
    // Try to use SecureStore first
    let email = await SecureStore.getItemAsync(BIOMETRIC_USER_EMAIL_KEY);

    // If not found in SecureStore, check AsyncStorage (for backward compatibility)
    if (!email) {
      email = await AsyncStorage.getItem(BIOMETRIC_USER_EMAIL_KEY);
    }

    return email;
  } catch (error) {
    console.error('Error getting biometric auth email:', error);
    return null;
  }
};
