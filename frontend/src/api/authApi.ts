import apiClient from './apiClient';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as SecureStore from 'expo-secure-store';

export interface RequestEmailCodeParams {
  email: string;
}

export interface VerifyEmailCodeParams {
  email: string;
  code: string;
}

export interface TOTPEmailCodeResponse {
  message: string;
  provisioning_uri: string;
}

export interface AuthResponse {
  token: string;
  expiry: string;
  user: UserProfile;
}

export interface UserProfile {
  id: number;
  email: string;
  name: string;
  phone_number?: string;
  user_type: 'admin' | 'teacher' | 'student' | 'parent';
  is_admin: boolean;
  created_at: string;
  updated_at: string;
}

// Use Secure Store for token storage if available
const storeToken = async (token: string) => {
  try {
    // Try to use SecureStore first
    await SecureStore.setItemAsync('auth_token', token);
  } catch (error) {
    // Fall back to AsyncStorage if SecureStore fails
    await AsyncStorage.setItem('auth_token', token);
    console.warn('Using AsyncStorage for token storage as SecureStore failed');
  }
};

const getToken = async (): Promise<string | null> => {
  try {
    // Try to use SecureStore first
    const token = await SecureStore.getItemAsync('auth_token');
    if (token) return token;

    // If not found in SecureStore, check AsyncStorage (for backward compatibility)
    const asyncToken = await AsyncStorage.getItem('auth_token');
    if (asyncToken) {
      // Migrate token to SecureStore
      await storeToken(asyncToken);
      await AsyncStorage.removeItem('auth_token');
      return asyncToken;
    }

    return null;
  } catch (error) {
    // Fall back to AsyncStorage if SecureStore fails
    return await AsyncStorage.getItem('auth_token');
  }
};

const removeToken = async () => {
  try {
    // Try to use SecureStore first
    await SecureStore.deleteItemAsync('auth_token');

    // Also clear from AsyncStorage (for backward compatibility)
    await AsyncStorage.removeItem('auth_token');
  } catch (error) {
    // Fall back to AsyncStorage if SecureStore fails
    await AsyncStorage.removeItem('auth_token');
  }

  // Clean up old tokens (if any)
  await AsyncStorage.removeItem('access_token');
  await AsyncStorage.removeItem('refresh_token');
};

/**
 * Request TOTP verification code
 */
export const requestEmailCode = async (params: RequestEmailCodeParams): Promise<TOTPEmailCodeResponse> => {
  const response = await apiClient.post<TOTPEmailCodeResponse>('/auth/request-code/', params);
  return response.data;
};

/**
 * Verify TOTP code and get authentication token
 */
export const verifyEmailCode = async (params: VerifyEmailCodeParams) => {
  const response = await apiClient.post<AuthResponse>('/auth/verify-code/', params);

  // Store token in secure storage
  await storeToken(response.data.token);

  return response.data;
};

/**
 * Get current user profile
 */
export const getUserProfile = async () => {
  const response = await apiClient.get<UserProfile>('/auth/profile/');
  return response.data;
};

/**
 * Logout user
 */
export const logout = async () => {
  // Call the server logout endpoint to invalidate the token
  try {
    await apiClient.post('/auth/logout/');
  } catch (error) {
    // Continue with local logout even if server call fails
    console.error('Error logging out on server:', error);
  }

  // Remove token from storage
  await removeToken();
};

/**
 * Check if user is logged in
 */
export const isAuthenticated = async (): Promise<boolean> => {
  const token = await getToken();
  return token !== null;
};
