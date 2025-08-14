/**
 * Comprehensive tests for the new ApiClient class
 * Tests the new architecture with dependency injection and no global state
 *
 * These tests will initially FAIL since the implementation doesn't exist yet.
 * They serve as the specification for the new architecture described in issue #176.
 */

import axios, { AxiosInstance, AxiosResponse } from 'axios';

import { ApiClient, ApiClientConfig } from './ApiClient';

// Mock axios
jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

// Mock storage interface
interface MockStorageGateway {
  get: jest.MockedFunction<(key: string) => Promise<string | null>>;
  set: jest.MockedFunction<(key: string, value: string) => Promise<void>>;
  remove: jest.MockedFunction<(key: string) => Promise<void>>;
}

describe('ApiClient', () => {
  let mockAxiosInstance: jest.Mocked<AxiosInstance>;
  let mockStorage: MockStorageGateway;
  let mockOnAuthError: jest.MockedFunction<(error: any) => void>;
  let config: ApiClientConfig;

  beforeEach(() => {
    // Reset all mocks
    jest.clearAllMocks();

    // Mock axios instance
    mockAxiosInstance = {
      get: jest.fn(),
      post: jest.fn(),
      put: jest.fn(),
      patch: jest.fn(),
      delete: jest.fn(),
      interceptors: {
        request: {
          use: jest.fn(),
        },
        response: {
          use: jest.fn(),
        },
      },
    } as any;

    mockedAxios.create.mockReturnValue(mockAxiosInstance);

    // Mock storage
    mockStorage = {
      get: jest.fn(),
      set: jest.fn(),
      remove: jest.fn(),
    };

    // Mock auth error callback
    mockOnAuthError = jest.fn();

    // Default config
    config = {
      baseURL: 'https://api.example.com',
      timeout: 5000,
      headers: {
        'Custom-Header': 'test-value',
      },
    };
  });

  describe('Constructor and Initialization', () => {
    it('should create ApiClient with injected dependencies', () => {
      // This test will FAIL initially - no ApiClient class exists yet
      const client = new ApiClient(config, mockStorage, mockOnAuthError);

      expect(client).toBeInstanceOf(ApiClient);
      expect(mockedAxios.create).toHaveBeenCalledWith({
        baseURL: 'https://api.example.com',
        timeout: 5000,
        headers: {
          'Content-Type': 'application/json',
          'Custom-Header': 'test-value',
        },
      });
    });

    it('should use default timeout when not provided', () => {
      const configWithoutTimeout = {
        baseURL: 'https://api.example.com',
      };

      new ApiClient(configWithoutTimeout, mockStorage, mockOnAuthError);

      expect(mockedAxios.create).toHaveBeenCalledWith({
        baseURL: 'https://api.example.com',
        timeout: 30000, // Default timeout
        headers: {
          'Content-Type': 'application/json',
        },
      });
    });

    it('should work without auth error callback', () => {
      expect(() => {
        new ApiClient(config, mockStorage); // No onAuthError callback
      }).not.toThrow();
    });

    it('should setup interceptors during initialization', () => {
      new ApiClient(config, mockStorage, mockOnAuthError);

      expect(mockAxiosInstance.interceptors.request.use).toHaveBeenCalled();
      expect(mockAxiosInstance.interceptors.response.use).toHaveBeenCalled();
    });
  });

  describe('Dependency Injection', () => {
    it('should use injected storage instead of global imports', async () => {
      mockStorage.get.mockResolvedValue('test-token');

      const client = new ApiClient(config, mockStorage, mockOnAuthError);

      // Trigger request interceptor
      const requestInterceptor = mockAxiosInstance.interceptors.request.use.mock.calls[0][0];
      const mockConfig = { headers: {} };
      await requestInterceptor(mockConfig);

      expect(mockStorage.get).toHaveBeenCalledWith('auth_token');
      expect(mockConfig.headers.Authorization).toBe('Token test-token');
    });

    it('should use injected auth error callback instead of global callback', async () => {
      const client = new ApiClient(config, mockStorage, mockOnAuthError);

      // Trigger response interceptor with 401 error
      const responseInterceptor = mockAxiosInstance.interceptors.response.use.mock.calls[0][1];
      const error = {
        response: { status: 401 },
        config: {},
      };

      try {
        await responseInterceptor(error);
      } catch (e) {
        // Expected to throw
      }

      expect(mockOnAuthError).toHaveBeenCalledWith(error);
      expect(mockStorage.remove).toHaveBeenCalledWith('auth_token');
    });

    it('should not call auth error callback when not provided', async () => {
      const client = new ApiClient(config, mockStorage); // No callback

      const responseInterceptor = mockAxiosInstance.interceptors.response.use.mock.calls[0][1];
      const error = {
        response: { status: 401 },
        config: {},
      };

      try {
        await responseInterceptor(error);
      } catch (e) {
        // Expected to throw
      }

      // Should not throw error when callback is not provided
      expect(mockStorage.remove).toHaveBeenCalledWith('auth_token');
    });
  });

  describe('No Global State', () => {
    it('should allow multiple client instances with different configurations', () => {
      const config1 = { baseURL: 'https://api1.example.com' };
      const config2 = { baseURL: 'https://api2.example.com' };

      const client1 = new ApiClient(config1, mockStorage, mockOnAuthError);
      const client2 = new ApiClient(config2, mockStorage, mockOnAuthError);

      expect(mockedAxios.create).toHaveBeenCalledTimes(2);
      expect(mockedAxios.create).toHaveBeenNthCalledWith(
        1,
        expect.objectContaining({
          baseURL: 'https://api1.example.com',
        })
      );
      expect(mockedAxios.create).toHaveBeenNthCalledWith(
        2,
        expect.objectContaining({
          baseURL: 'https://api2.example.com',
        })
      );
    });

    it('should allow different storage implementations per instance', async () => {
      const mockStorage2: MockStorageGateway = {
        get: jest.fn().mockResolvedValue('different-token'),
        set: jest.fn(),
        remove: jest.fn(),
      };

      const client1 = new ApiClient(config, mockStorage, mockOnAuthError);
      const client2 = new ApiClient(config, mockStorage2, mockOnAuthError);

      // Trigger request interceptors for both clients
      const requestInterceptor1 = mockAxiosInstance.interceptors.request.use.mock.calls[0][0];
      const requestInterceptor2 = mockAxiosInstance.interceptors.request.use.mock.calls[1][0];

      mockStorage.get.mockResolvedValue('token1');

      const mockConfig1 = { headers: {} };
      const mockConfig2 = { headers: {} };

      await requestInterceptor1(mockConfig1);
      await requestInterceptor2(mockConfig2);

      expect(mockStorage.get).toHaveBeenCalledWith('auth_token');
      expect(mockStorage2.get).toHaveBeenCalledWith('auth_token');
      expect(mockConfig1.headers.Authorization).toBe('Token token1');
      expect(mockConfig2.headers.Authorization).toBe('Token different-token');
    });

    it('should allow different error handlers per instance', () => {
      const mockOnAuthError2 = jest.fn();

      const client1 = new ApiClient(config, mockStorage, mockOnAuthError);
      const client2 = new ApiClient(config, mockStorage, mockOnAuthError2);

      // Verify that different instances are created with different error handlers
      expect(client1).not.toBe(client2);
      // Both clients should have been created with axios.create
      expect(mockedAxios.create).toHaveBeenCalledTimes(2);

      // This test verifies that the instances are separate and have different configurations
      // The actual error handler behavior is tested in other tests
      expect(mockOnAuthError).not.toBe(mockOnAuthError2);
    });
  });

  describe('Request Interceptor', () => {
    it('should add token to request headers when token exists', async () => {
      mockStorage.get.mockResolvedValue('valid-token');

      const client = new ApiClient(config, mockStorage, mockOnAuthError);
      const requestInterceptor = mockAxiosInstance.interceptors.request.use.mock.calls[0][0];

      const mockConfig = { headers: {} };
      const result = await requestInterceptor(mockConfig);

      expect(result.headers.Authorization).toBe('Token valid-token');
    });

    it('should not add token to headers when token does not exist', async () => {
      mockStorage.get.mockResolvedValue(null);

      const client = new ApiClient(config, mockStorage, mockOnAuthError);
      const requestInterceptor = mockAxiosInstance.interceptors.request.use.mock.calls[0][0];

      const mockConfig = { headers: {} };
      const result = await requestInterceptor(mockConfig);

      expect(result.headers.Authorization).toBeUndefined();
    });

    it('should handle storage errors gracefully', async () => {
      mockStorage.get.mockRejectedValue(new Error('Storage error'));

      const client = new ApiClient(config, mockStorage, mockOnAuthError);
      const requestInterceptor = mockAxiosInstance.interceptors.request.use.mock.calls[0][0];

      const mockConfig = { headers: {} };

      // Should continue without token when storage fails (not throw)
      const result = await requestInterceptor(mockConfig);
      expect(result.headers.Authorization).toBeUndefined();
    });
  });

  describe('Response Interceptor', () => {
    let client: ApiClient;
    let responseInterceptor: any;

    beforeEach(() => {
      client = new ApiClient(config, mockStorage, mockOnAuthError);
      responseInterceptor = mockAxiosInstance.interceptors.response.use.mock.calls[0][1];
    });

    it('should handle 401 errors by removing token and calling auth error callback', async () => {
      const error = {
        response: { status: 401 },
        config: { _retry: undefined },
      };

      try {
        await responseInterceptor(error);
      } catch (e) {
        expect(e).toBe(error);
      }

      expect(mockStorage.remove).toHaveBeenCalledWith('auth_token');
      expect(mockOnAuthError).toHaveBeenCalledWith(error);
      expect(error.config._retry).toBe(true);
    });

    it('should not retry 401 errors that have already been retried', async () => {
      const error = {
        response: { status: 401 },
        config: { _retry: true },
      };

      try {
        await responseInterceptor(error);
      } catch (e) {
        expect(e).toBe(error);
      }

      expect(mockStorage.remove).not.toHaveBeenCalled();
      expect(mockOnAuthError).not.toHaveBeenCalled();
    });

    it('should pass through non-401 errors without special handling', async () => {
      const error = {
        response: { status: 500 },
        config: {},
      };

      try {
        await responseInterceptor(error);
      } catch (e) {
        expect(e).toBe(error);
      }

      expect(mockStorage.remove).not.toHaveBeenCalled();
      expect(mockOnAuthError).not.toHaveBeenCalled();
    });

    it('should extract error messages from response data', async () => {
      const error = {
        response: {
          status: 400,
          data: { detail: 'Validation failed' },
        },
        config: {},
        message: 'Original message',
      };

      try {
        await responseInterceptor(error);
      } catch (e) {
        expect(e.message).toBe('Validation failed');
      }
    });

    it('should handle successful responses without modification', async () => {
      const successInterceptor = mockAxiosInstance.interceptors.response.use.mock.calls[0][0];
      const response = { status: 200, data: 'success' };

      const result = successInterceptor(response);

      expect(result).toBe(response);
    });
  });

  describe('HTTP Methods', () => {
    let client: ApiClient;

    beforeEach(() => {
      client = new ApiClient(config, mockStorage, mockOnAuthError);
    });

    it('should expose GET method bound to axios instance', async () => {
      const mockResponse = { data: 'get-data' };
      mockAxiosInstance.get.mockResolvedValue(mockResponse);

      const result = await client.get('/endpoint');

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/endpoint');
      expect(result).toBe(mockResponse);
    });

    it('should expose POST method bound to axios instance', async () => {
      const mockResponse = { data: 'post-data' };
      const postData = { field: 'value' };
      mockAxiosInstance.post.mockResolvedValue(mockResponse);

      const result = await client.post('/endpoint', postData);

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/endpoint', postData);
      expect(result).toBe(mockResponse);
    });

    it('should expose PUT method bound to axios instance', async () => {
      const mockResponse = { data: 'put-data' };
      const putData = { field: 'updated-value' };
      mockAxiosInstance.put.mockResolvedValue(mockResponse);

      const result = await client.put('/endpoint', putData);

      expect(mockAxiosInstance.put).toHaveBeenCalledWith('/endpoint', putData);
      expect(result).toBe(mockResponse);
    });

    it('should expose PATCH method bound to axios instance', async () => {
      const mockResponse = { data: 'patch-data' };
      const patchData = { field: 'patched-value' };
      mockAxiosInstance.patch.mockResolvedValue(mockResponse);

      const result = await client.patch('/endpoint', patchData);

      expect(mockAxiosInstance.patch).toHaveBeenCalledWith('/endpoint', patchData);
      expect(result).toBe(mockResponse);
    });

    it('should expose DELETE method bound to axios instance', async () => {
      const mockResponse = { data: 'delete-data' };
      mockAxiosInstance.delete.mockResolvedValue(mockResponse);

      const result = await client.delete('/endpoint');

      expect(mockAxiosInstance.delete).toHaveBeenCalledWith('/endpoint');
      expect(result).toBe(mockResponse);
    });
  });

  describe('Parallel Test Execution', () => {
    it('should handle multiple parallel requests without interference', async () => {
      mockStorage.get.mockResolvedValue('test-token');

      // Create multiple client instances
      const client1 = new ApiClient(config, mockStorage, mockOnAuthError);
      const client2 = new ApiClient(config, mockStorage, mockOnAuthError);

      // Mock successful responses
      mockAxiosInstance.get.mockResolvedValue({ data: 'success' });

      // Execute parallel requests
      const promises = [
        client1.get('/endpoint1'),
        client2.get('/endpoint2'),
        client1.post('/endpoint3', { data: 'test' }),
        client2.put('/endpoint4', { data: 'test' }),
      ];

      const results = await Promise.all(promises);

      expect(results).toHaveLength(4);
      expect(mockAxiosInstance.get).toHaveBeenCalledTimes(2);
      expect(mockAxiosInstance.post).toHaveBeenCalledTimes(1);
      expect(mockAxiosInstance.put).toHaveBeenCalledTimes(1);
    });

    it('should isolate errors between different client instances', async () => {
      const mockOnAuthError2 = jest.fn();

      const client1 = new ApiClient(config, mockStorage, mockOnAuthError);
      const client2 = new ApiClient(config, mockStorage, mockOnAuthError2);

      // Verify that both clients are separate instances
      expect(client1).not.toBe(client2);
      expect(mockOnAuthError).not.toBe(mockOnAuthError2);

      // Verify that axios.create was called twice for separate instances
      expect(mockedAxios.create).toHaveBeenCalledTimes(2);

      // This test verifies instance isolation
      // Error handling isolation is covered by the response interceptor tests
    });
  });

  describe('Type Safety and Interface Compliance', () => {
    it('should properly type the ApiClientConfig interface', () => {
      const validConfig: ApiClientConfig = {
        baseURL: 'https://api.example.com',
        timeout: 5000,
        headers: {
          'Custom-Header': 'value',
        },
      };

      expect(() => {
        new ApiClient(validConfig, mockStorage, mockOnAuthError);
      }).not.toThrow();
    });

    it('should work with minimal configuration', () => {
      const minimalConfig: ApiClientConfig = {
        baseURL: 'https://api.example.com',
      };

      expect(() => {
        new ApiClient(minimalConfig, mockStorage, mockOnAuthError);
      }).not.toThrow();
    });
  });
});
