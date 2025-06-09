import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';
import * as SecureStore from 'expo-secure-store';

import apiClient from './apiClient';
import {
  authenticateWithBiometrics,
  getBiometricAuthEmail,
  isBiometricEnabled,
} from './biometricAuth';

export interface RequestEmailCodeParams {
  email: string;
}

export interface RequestPhoneCodeParams {
  phone: string;
}

export interface VerifyEmailCodeParams {
  email?: string;
  phone?: string;
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
  is_new_user?: boolean;
  school?: SchoolInfo;
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
  roles?: UserRole[];
}

export interface SchoolInfo {
  id: number;
  name: string;
  description?: string;
  address?: string;
  contact_email?: string;
  phone_number?: string;
  website?: string;
  created_at?: string;
  updated_at?: string;
}

export interface UserRole {
  school: {
    id: number;
    name: string;
  };
  role: string;
  role_display: string;
}

export interface OnboardingData {
  name: string;
  email: string;
  phone_number: string;
  primary_contact: 'email' | 'phone';
  school: {
    name: string;
    description?: string;
    address?: string;
    contact_email?: string;
    phone_number?: string;
    website?: string;
  };
}

export interface OnboardingResponse {
  message: string;
  user: UserProfile;
  schools: SchoolInfo[];
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
 * Request verification code (TOTP)
 */
export const requestEmailCode = async (
  params: RequestEmailCodeParams | RequestPhoneCodeParams
): Promise<TOTPEmailCodeResponse> => {
  const response = await apiClient.post<TOTPEmailCodeResponse>(
    '/accounts/auth/request-code/',
    params
  );
  return response.data;
};

/**
 * Verify code and get authentication token
 */
export const verifyEmailCode = async (params: VerifyEmailCodeParams) => {
  const response = await apiClient.post<AuthResponse>('/accounts/auth/verify-code/', params);

  // Store token in secure storage
  await storeToken(response.data.token);

  return response.data;
};

/**
 * Authenticate with biometrics and get token
 * @returns Authentication response or null if biometric auth fails
 */
export const authenticateWithBiometricsAndGetToken = async (): Promise<AuthResponse | null> => {
  try {
    // Check if biometric auth is enabled
    const biometricEnabled = await isBiometricEnabled();
    if (!biometricEnabled) {
      return null;
    }

    // Get email associated with biometric auth
    const email = await getBiometricAuthEmail();
    if (!email) {
      return null;
    }

    // Authenticate with biometrics
    const authResult = await authenticateWithBiometrics('Authenticate to log in');
    if (!authResult.success) {
      return null;
    }

    // Request a code for this email
    await requestEmailCode({ email });

    // Since this is biometric auth, we'll request a special biometric verification
    // This endpoint should exist on the backend - if not, you'll need to implement it
    try {
      const response = await apiClient.post<AuthResponse>('accounts/auth/biometric-verify/', {
        email,
      });

      // Store token in secure storage
      await storeToken(response.data.token);

      return response.data;
    } catch (error) {
      // If the biometric endpoint doesn't exist, we can't proceed with biometric auth
      console.error('Error authenticating with biometrics:', error);
      return null;
    }
  } catch (error) {
    console.error('Error in biometric authentication flow:', error);
    return null;
  }
};

/**
 * Logout user
 */
export const logout = async () => {
  // Call the server logout endpoint to invalidate the token
  try {
    await apiClient.post('accounts/auth/logout/');
  } catch (error) {
    // Continue with local logout even if server call fails
    console.error('Error logging out on server:', error);
  }

  // Remove token from storage
  await removeToken();
};

/**
 * Check if user is authenticated
 */
export const isAuthenticated = async (): Promise<boolean> => {
  const token = await getToken();
  if (!token) {
    return false;
  }

  // Validate token with server
  try {
    await apiClient.get('/accounts/users/dashboard_info/');
    return true;
  } catch (error: any) {
    // If server is unreachable, we can't verify auth - logout user
    if (!error.response || error.code === 'ERR_NETWORK' || error.code === 'ERR_CONNECTION_REFUSED') {
      await removeToken();
      return false;
    }

    // If 401, token is invalid
    if (error.response?.status === 401) {
      await removeToken();
      return false;
    }

    // For other HTTP errors (500, 503, etc.), assume token is still valid
    // but server is having issues
    return true;
  }
};

/**
 * Fill out form and create user
 */
export const createUser = async (data: OnboardingData): Promise<OnboardingResponse> => {
  try {
    const response = await apiClient.post<OnboardingResponse>('/accounts/users/signup/', data);
    return response.data;
  } catch (error) {
    console.error('Error creating user:', error);
    if (axios.isAxiosError(error)) {
      console.error('API Error Response:', error.response?.data);
      console.error('API Error Status:', error.response?.status);
    }
    throw error;
  }
};
