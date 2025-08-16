/**
 * New ApiClient class with dependency injection and no global state
 * This replaces the global apiClient singleton with a class-based approach
 * that supports proper dependency injection and parallel test execution.
 *
 * Key improvements over the old architecture:
 * - No global state or singleton pattern
 * - Dependencies injected via constructor
 * - Support for multiple client instances
 * - Isolated storage and error handling per instance
 * - Proper TypeScript typing
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';

// Storage interface to abstract storage implementation
export interface StorageGateway {
  get(key: string): Promise<string | null>;
  set(key: string, value: string): Promise<void>;
  remove(key: string): Promise<void>;
}

// Configuration interface for ApiClient
export interface ApiClientConfig {
  baseURL: string;
  timeout?: number;
  headers?: Record<string, string>;
}

// Auth error callback type
export type AuthErrorCallback = (error: any) => void;

export class ApiClient {
  private readonly axios: AxiosInstance;
  private readonly storage: StorageGateway;
  private readonly onAuthError?: AuthErrorCallback;

  constructor(config: ApiClientConfig, storage: StorageGateway, onAuthError?: AuthErrorCallback) {
    this.storage = storage;
    this.onAuthError = onAuthError;

    // Create axios instance with provided configuration
    this.axios = axios.create({
      baseURL: config.baseURL,
      timeout: config.timeout || 30000, // Default 30 second timeout
      headers: {
        'Content-Type': 'application/json',
        ...config.headers,
      },
    });

    // Setup interceptors
    this.setupRequestInterceptor();
    this.setupResponseInterceptor();
  }

  /**
   * Setup request interceptor to add authentication token
   */
  private setupRequestInterceptor(): void {
    this.axios.interceptors.request.use(
      async config => {
        try {
          const token = await this.storage.get('auth_token');
          if (token) {
            config.headers.Authorization = `Token ${token}`;
          }
        } catch (error) {
          // If storage fails, let the request continue without token
          // The error will be handled by the server (likely 401)
          if (__DEV__) {
            if (__DEV__) {
              console.warn('Failed to get auth token from storage:', error);
            }
          }
        }
        return config;
      },
      error => {
        return Promise.reject(error);
      },
    );
  }

  /**
   * Setup response interceptor to handle errors and token cleanup
   */
  private setupResponseInterceptor(): void {
    this.axios.interceptors.response.use(
      response => response,
      async error => {
        const originalRequest = error.config;

        // Handle 401 errors (authentication failures)
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          try {
            // Clear the invalid token
            await this.storage.remove('auth_token');

            // Notify auth error callback if provided
            if (this.onAuthError) {
              this.onAuthError(error);
            }
          } catch (storageError) {
            if (__DEV__) {
              console.error('Failed to handle auth error:', storageError);
            }
          }
        }

        // Extract error messages from response data
        if (error.response?.data?.detail) {
          error.message = error.response.data.detail;
        } else if (error.response?.data?.error) {
          error.message = error.response.data.error;
        }

        return Promise.reject(error);
      },
    );
  }

  /**
   * HTTP GET method
   */
  get<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return config ? this.axios.get(url, config) : this.axios.get(url);
  }

  /**
   * HTTP POST method
   */
  post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return config ? this.axios.post(url, data, config) : this.axios.post(url, data);
  }

  /**
   * HTTP PUT method
   */
  put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return config ? this.axios.put(url, data, config) : this.axios.put(url, data);
  }

  /**
   * HTTP PATCH method
   */
  patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return config ? this.axios.patch(url, data, config) : this.axios.patch(url, data);
  }

  /**
   * HTTP DELETE method
   */
  delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return config ? this.axios.delete(url, config) : this.axios.delete(url);
  }
}
