import * as LocalAuthentication from 'expo-local-authentication';
import * as SecureStore from 'expo-secure-store';
import AsyncStorage from '@react-native-async-storage/async-storage';
import {
  isBiometricAvailable,
  authenticateWithBiometrics,
  enableBiometricAuth,
  disableBiometricAuth,
  isBiometricEnabled,
  getBiometricAuthEmail
} from '../biometricAuth';

// Mock expo-local-authentication
jest.mock('expo-local-authentication', () => ({
  hasHardwareAsync: jest.fn(),
  isEnrolledAsync: jest.fn(),
  authenticateAsync: jest.fn(),
}));

// Mock expo-secure-store
jest.mock('expo-secure-store', () => ({
  setItemAsync: jest.fn(),
  getItemAsync: jest.fn(),
  deleteItemAsync: jest.fn(),
}));

// Mock AsyncStorage
jest.mock('@react-native-async-storage/async-storage', () => ({
  setItem: jest.fn(),
  getItem: jest.fn(),
  removeItem: jest.fn(),
}));

describe('Biometric Authentication', () => {
  beforeEach(() => {
    // Clear all mocks before each test
    jest.clearAllMocks();
  });

  describe('isBiometricAvailable', () => {
    it('should return true if hardware is available and user is enrolled', async () => {
      (LocalAuthentication.hasHardwareAsync as jest.Mock).mockResolvedValue(true);
      (LocalAuthentication.isEnrolledAsync as jest.Mock).mockResolvedValue(true);

      const result = await isBiometricAvailable();
      expect(result).toBe(true);
      expect(LocalAuthentication.hasHardwareAsync).toHaveBeenCalled();
      expect(LocalAuthentication.isEnrolledAsync).toHaveBeenCalled();
    });

    it('should return false if hardware is not available', async () => {
      (LocalAuthentication.hasHardwareAsync as jest.Mock).mockResolvedValue(false);
      (LocalAuthentication.isEnrolledAsync as jest.Mock).mockResolvedValue(true);

      const result = await isBiometricAvailable();
      expect(result).toBe(false);
    });

    it('should return false if user is not enrolled', async () => {
      (LocalAuthentication.hasHardwareAsync as jest.Mock).mockResolvedValue(true);
      (LocalAuthentication.isEnrolledAsync as jest.Mock).mockResolvedValue(false);

      const result = await isBiometricAvailable();
      expect(result).toBe(false);
    });

    it('should handle errors properly', async () => {
      (LocalAuthentication.hasHardwareAsync as jest.Mock).mockRejectedValue(new Error('Test error'));

      const result = await isBiometricAvailable();
      expect(result).toBe(false);
    });
  });

  describe('authenticateWithBiometrics', () => {
    it('should authenticate successfully', async () => {
      (LocalAuthentication.hasHardwareAsync as jest.Mock).mockResolvedValue(true);
      (LocalAuthentication.isEnrolledAsync as jest.Mock).mockResolvedValue(true);
      (LocalAuthentication.authenticateAsync as jest.Mock).mockResolvedValue({ success: true });

      const result = await authenticateWithBiometrics();
      expect(result).toEqual({ success: true });
      expect(LocalAuthentication.authenticateAsync).toHaveBeenCalled();
    });

    it('should fail if biometrics are not available', async () => {
      (LocalAuthentication.hasHardwareAsync as jest.Mock).mockResolvedValue(false);
      (LocalAuthentication.isEnrolledAsync as jest.Mock).mockResolvedValue(false);

      const result = await authenticateWithBiometrics();
      expect(result).toEqual({
        success: false,
        error: 'Biometric authentication is not available on this device'
      });
      expect(LocalAuthentication.authenticateAsync).not.toHaveBeenCalled();
    });

    it('should handle authentication errors', async () => {
      (LocalAuthentication.hasHardwareAsync as jest.Mock).mockResolvedValue(true);
      (LocalAuthentication.isEnrolledAsync as jest.Mock).mockResolvedValue(true);
      (LocalAuthentication.authenticateAsync as jest.Mock).mockRejectedValue(new Error('Auth error'));

      const result = await authenticateWithBiometrics();
      expect(result).toEqual({
        success: false,
        error: 'Authentication failed. Please try again.'
      });
    });
  });

  describe('enableBiometricAuth', () => {
    it('should enable biometric authentication successfully', async () => {
      (LocalAuthentication.hasHardwareAsync as jest.Mock).mockResolvedValue(true);
      (LocalAuthentication.isEnrolledAsync as jest.Mock).mockResolvedValue(true);
      (LocalAuthentication.authenticateAsync as jest.Mock).mockResolvedValue({ success: true });
      (SecureStore.setItemAsync as jest.Mock).mockResolvedValue(undefined);
      (AsyncStorage.setItem as jest.Mock).mockResolvedValue(undefined);

      const result = await enableBiometricAuth('test@example.com');
      expect(result).toBe(true);
      expect(SecureStore.setItemAsync).toHaveBeenCalledWith('biometric_auth_enabled', 'true');
      expect(SecureStore.setItemAsync).toHaveBeenCalledWith('biometric_user_email', 'test@example.com');
      expect(AsyncStorage.setItem).toHaveBeenCalledWith('biometric_auth_enabled', 'true');
      expect(AsyncStorage.setItem).toHaveBeenCalledWith('biometric_user_email', 'test@example.com');
    });

    it('should fail if biometrics are not available', async () => {
      (LocalAuthentication.hasHardwareAsync as jest.Mock).mockResolvedValue(false);
      (LocalAuthentication.isEnrolledAsync as jest.Mock).mockResolvedValue(false);

      const result = await enableBiometricAuth('test@example.com');
      expect(result).toBe(false);
      expect(SecureStore.setItemAsync).not.toHaveBeenCalled();
      expect(AsyncStorage.setItem).not.toHaveBeenCalled();
    });

    it('should fail if authentication fails', async () => {
      (LocalAuthentication.hasHardwareAsync as jest.Mock).mockResolvedValue(true);
      (LocalAuthentication.isEnrolledAsync as jest.Mock).mockResolvedValue(true);
      (LocalAuthentication.authenticateAsync as jest.Mock).mockResolvedValue({ success: false });

      const result = await enableBiometricAuth('test@example.com');
      expect(result).toBe(false);
      expect(SecureStore.setItemAsync).not.toHaveBeenCalled();
      expect(AsyncStorage.setItem).not.toHaveBeenCalled();
    });
  });

  describe('disableBiometricAuth', () => {
    it('should disable biometric authentication successfully', async () => {
      (SecureStore.deleteItemAsync as jest.Mock).mockResolvedValue(undefined);
      (AsyncStorage.removeItem as jest.Mock).mockResolvedValue(undefined);

      const result = await disableBiometricAuth();
      expect(result).toBe(true);
      expect(SecureStore.deleteItemAsync).toHaveBeenCalledWith('biometric_auth_enabled');
      expect(SecureStore.deleteItemAsync).toHaveBeenCalledWith('biometric_user_email');
      expect(AsyncStorage.removeItem).toHaveBeenCalledWith('biometric_auth_enabled');
      expect(AsyncStorage.removeItem).toHaveBeenCalledWith('biometric_user_email');
    });

    it('should handle errors properly', async () => {
      (SecureStore.deleteItemAsync as jest.Mock).mockRejectedValue(new Error('Test error'));

      const result = await disableBiometricAuth();
      expect(result).toBe(false);
    });
  });

  describe('isBiometricEnabled', () => {
    it('should return true if biometrics are enabled in SecureStore', async () => {
      (SecureStore.getItemAsync as jest.Mock).mockResolvedValue('true');

      const result = await isBiometricEnabled();
      expect(result).toBe(true);
      expect(SecureStore.getItemAsync).toHaveBeenCalledWith('biometric_auth_enabled');
      expect(AsyncStorage.getItem).not.toHaveBeenCalled();
    });

    it('should check AsyncStorage if SecureStore returns null', async () => {
      (SecureStore.getItemAsync as jest.Mock).mockResolvedValue(null);
      (AsyncStorage.getItem as jest.Mock).mockResolvedValue('true');

      const result = await isBiometricEnabled();
      expect(result).toBe(true);
      expect(SecureStore.getItemAsync).toHaveBeenCalledWith('biometric_auth_enabled');
      expect(AsyncStorage.getItem).toHaveBeenCalledWith('biometric_auth_enabled');
    });

    it('should return false if biometrics are not enabled', async () => {
      (SecureStore.getItemAsync as jest.Mock).mockResolvedValue(null);
      (AsyncStorage.getItem as jest.Mock).mockResolvedValue(null);

      const result = await isBiometricEnabled();
      expect(result).toBe(false);
    });

    it('should handle errors properly', async () => {
      (SecureStore.getItemAsync as jest.Mock).mockRejectedValue(new Error('Test error'));

      const result = await isBiometricEnabled();
      expect(result).toBe(false);
    });
  });

  describe('getBiometricAuthEmail', () => {
    it('should return email from SecureStore', async () => {
      (SecureStore.getItemAsync as jest.Mock).mockResolvedValue('test@example.com');

      const result = await getBiometricAuthEmail();
      expect(result).toBe('test@example.com');
      expect(SecureStore.getItemAsync).toHaveBeenCalledWith('biometric_user_email');
      expect(AsyncStorage.getItem).not.toHaveBeenCalled();
    });

    it('should check AsyncStorage if SecureStore returns null', async () => {
      (SecureStore.getItemAsync as jest.Mock).mockResolvedValue(null);
      (AsyncStorage.getItem as jest.Mock).mockResolvedValue('test@example.com');

      const result = await getBiometricAuthEmail();
      expect(result).toBe('test@example.com');
      expect(SecureStore.getItemAsync).toHaveBeenCalledWith('biometric_user_email');
      expect(AsyncStorage.getItem).toHaveBeenCalledWith('biometric_user_email');
    });

    it('should return null if email is not found', async () => {
      (SecureStore.getItemAsync as jest.Mock).mockResolvedValue(null);
      (AsyncStorage.getItem as jest.Mock).mockResolvedValue(null);

      const result = await getBiometricAuthEmail();
      expect(result).toBe(null);
    });

    it('should handle errors properly', async () => {
      (SecureStore.getItemAsync as jest.Mock).mockRejectedValue(new Error('Test error'));

      const result = await getBiometricAuthEmail();
      expect(result).toBe(null);
    });
  });
});
