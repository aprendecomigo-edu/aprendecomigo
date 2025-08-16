/**
 * Factory functions for creating ApiClient and ApiGateway instances
 * Provides convenient functions to create properly configured instances
 */

import { ApiClient, ApiClientConfig, StorageGateway, AuthErrorCallback } from './client/ApiClient';
import { ApiGateway, ApiGatewayImpl } from './gateway/index';

import { API_URL } from '@/constants/api';
import { StorageInterface } from '@/utils/storage';

/**
 * Storage adapter to convert StorageInterface to StorageGateway
 */
class StorageAdapter implements StorageGateway {
  constructor(private storage: StorageInterface) {}

  async get(key: string): Promise<string | null> {
    return await this.storage.getItem(key);
  }

  async set(key: string, value: string): Promise<void> {
    await this.storage.setItem(key, value);
  }

  async remove(key: string): Promise<void> {
    await this.storage.removeItem(key);
  }
}

/**
 * Create an ApiClient instance with default configuration
 */
export function createApiClient(
  storage: StorageInterface,
  onAuthError?: AuthErrorCallback,
  config?: Partial<ApiClientConfig>,
): ApiClient {
  const defaultConfig: ApiClientConfig = {
    baseURL: API_URL,
    timeout: 30000,
    headers: {},
  };

  const finalConfig = { ...defaultConfig, ...config };
  const storageAdapter = new StorageAdapter(storage);

  return new ApiClient(finalConfig, storageAdapter, onAuthError);
}

/**
 * Create an ApiGateway instance with default configuration
 */
export function createApiGateway(
  storage: StorageInterface,
  onAuthError?: AuthErrorCallback,
  config?: Partial<ApiClientConfig>,
): ApiGateway {
  const apiClient = createApiClient(storage, onAuthError, config);
  return new ApiGatewayImpl(apiClient);
}

/**
 * Create an ApiGateway instance from an existing ApiClient
 */
export function createApiGatewayFromClient(apiClient: ApiClient): ApiGateway {
  return new ApiGatewayImpl(apiClient);
}
