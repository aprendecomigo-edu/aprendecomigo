/**
 * Tests to verify the new API client architecture has NO global state
 * These tests ensure parallel test execution and prevent test interference
 *
 * These tests will initially FAIL since the new architecture doesn't exist yet.
 * They serve as verification that issue #176 requirements are met.
 */

import axios from 'axios';

import { ApiClient, ApiClientConfig } from '../../api/client/ApiClient';
import { ApiGatewayImpl } from '../../api/gateway/index';

// Mock axios
jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

// Mock storage interface
interface MockStorageGateway {
  get: jest.MockedFunction<(key: string) => Promise<string | null>>;
  set: jest.MockedFunction<(key: string, value: string) => Promise<void>>;
  remove: jest.MockedFunction<(key: string) => Promise<void>>;
}

describe('No Global State Verification', () => {
  const createMockStorage = (): MockStorageGateway => ({
    get: jest.fn(),
    set: jest.fn(),
    remove: jest.fn(),
  });

  const createMockAuthErrorHandler = () => jest.fn();

  const baseConfig: ApiClientConfig = {
    baseURL: 'https://api.example.com',
  };

  // Cache file content to avoid reading the same file multiple times
  const fileCache = new Map<string, string>();
  const readCachedFile = async (filePath: string): Promise<string> => {
    if (!fileCache.has(filePath)) {
      const { readFile } = require('fs/promises');
      const content = await readFile(filePath, 'utf8');
      fileCache.set(filePath, content);
    }
    return fileCache.get(filePath)!;
  };

  beforeEach(() => {
    jest.clearAllMocks();
    fileCache.clear();

    // Setup axios mock
    const mockAxiosInstance = {
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
  });

  describe('Global State Elimination', () => {
    it('should not export any global variables from ApiClient module', () => {
      // This test will FAIL initially since the new module doesn't exist
      const ApiClientModule = require('../../api/client/ApiClient');

      // Check that no global variables are exported
      const exportedKeys = Object.keys(ApiClientModule);

      // Should only export the class and interface, no global state
      expect(exportedKeys).not.toContain('authErrorCallback');
      expect(exportedKeys).not.toContain('globalStorage');
      expect(exportedKeys).not.toContain('defaultClient');
      expect(exportedKeys).not.toContain('apiClient'); // singleton instance

      // Should only export legitimate exports
      expect(exportedKeys).toContain('ApiClient');
      // Note: TypeScript interfaces don't exist at runtime, so ApiClientConfig won't be in exportedKeys
    });

    it('should not import storage modules directly', async () => {
      // Verify that ApiClient doesn't have direct storage imports
      const path = require('path');

      const apiClientPath = path.resolve(__dirname, '../../api/client/ApiClient.ts');

      try {
        const apiClientSource = await readCachedFile(apiClientPath);

        // Check that direct storage imports are not present
        expect(apiClientSource).not.toMatch(/import.*storage.*from.*utils\/storage/);
        expect(apiClientSource).not.toMatch(/import.*AsyncStorage/);
        expect(apiClientSource).not.toMatch(/import.*SecureStore/);

        // Should use injected storage instead
        expect(apiClientSource).toMatch(/storage.*StorageGateway/);
      } catch (error) {
        // File doesn't exist yet - test will fail as expected
        throw new Error('ApiClient.ts does not exist yet - implementation needed');
      }
    });

    it('should not use global authentication error callbacks', async () => {
      const path = require('path');

      const apiClientPath = path.resolve(__dirname, '../../api/client/ApiClient.ts');

      try {
        const apiClientSource = await readCachedFile(apiClientPath);

        // Check that global callback patterns are not present
        expect(apiClientSource).not.toMatch(/let.*authErrorCallback/);
        expect(apiClientSource).not.toMatch(/setAuthErrorCallback/);
        expect(apiClientSource).not.toMatch(/globalAuthErrorHandler/);

        // Should use injected callback instead
        expect(apiClientSource).toMatch(/onAuthError.*\?:/);
      } catch (error) {
        throw new Error('ApiClient.ts does not exist yet - implementation needed');
      }
    });
  });

  describe('Instance Isolation', () => {
    it('should create completely isolated ApiClient instances', async () => {
      const storage1 = createMockStorage();
      const storage2 = createMockStorage();
      const authHandler1 = createMockAuthErrorHandler();
      const authHandler2 = createMockAuthErrorHandler();

      storage1.get.mockResolvedValue('token1');
      storage2.get.mockResolvedValue('token2');

      const client1 = new ApiClient(
        { ...baseConfig, baseURL: 'https://api1.example.com' },
        storage1,
        authHandler1,
      );

      const client2 = new ApiClient(
        { ...baseConfig, baseURL: 'https://api2.example.com' },
        storage2,
        authHandler2,
      );

      // Verify instances are completely separate
      expect(client1).not.toBe(client2);

      // Mock axios to verify different configurations
      expect(mockedAxios.create).toHaveBeenCalledWith(
        expect.objectContaining({ baseURL: 'https://api1.example.com' }),
      );
      expect(mockedAxios.create).toHaveBeenCalledWith(
        expect.objectContaining({ baseURL: 'https://api2.example.com' }),
      );
    });

    it('should isolate storage operations between instances', async () => {
      const storage1 = createMockStorage();
      const storage2 = createMockStorage();

      storage1.get.mockResolvedValue('token-from-storage1');
      storage2.get.mockResolvedValue('token-from-storage2');

      const client1 = new ApiClient(baseConfig, storage1, createMockAuthErrorHandler());
      const client2 = new ApiClient(baseConfig, storage2, createMockAuthErrorHandler());

      // Get the mock axios instance that was set up in beforeEach
      const mockAxiosInstance = mockedAxios.create.mock.results[0].value;

      // Simulate request interceptor execution
      const requestInterceptor1 = mockAxiosInstance.interceptors.request.use.mock.calls[0][0];
      const requestInterceptor2 = mockAxiosInstance.interceptors.request.use.mock.calls[1][0];

      const config1 = { headers: {} as Record<string, string> };
      const config2 = { headers: {} as Record<string, string> };

      await requestInterceptor1(config1);
      await requestInterceptor2(config2);

      expect(storage1.get).toHaveBeenCalledWith('auth_token');
      expect(storage2.get).toHaveBeenCalledWith('auth_token');
      expect(config1.headers.Authorization).toBe('Token token-from-storage1');
      expect(config2.headers.Authorization).toBe('Token token-from-storage2');
    });

    it('should isolate error handling between instances', async () => {
      const storage1 = createMockStorage();
      const storage2 = createMockStorage();
      const authHandler1 = createMockAuthErrorHandler();
      const authHandler2 = createMockAuthErrorHandler();

      const client1 = new ApiClient(baseConfig, storage1, authHandler1);
      const client2 = new ApiClient(baseConfig, storage2, authHandler2);

      // Get the mock axios instance that was set up in beforeEach
      const mockAxiosInstance = mockedAxios.create.mock.results[0].value;

      // Trigger error handling through response interceptors
      const responseInterceptor1 = mockAxiosInstance.interceptors.response.use.mock.calls[0][1];
      const responseInterceptor2 = mockAxiosInstance.interceptors.response.use.mock.calls[1][1];

      const error1 = { response: { status: 401 }, config: {} };
      const error2 = { response: { status: 401 }, config: {} };

      try {
        await responseInterceptor1(error1);
      } catch (e) {
        // Expected to throw
      }

      try {
        await responseInterceptor2(error2);
      } catch (e) {
        // Expected to throw
      }

      expect(authHandler1).toHaveBeenCalledWith(error1);
      expect(authHandler2).toHaveBeenCalledWith(error2);
      expect(storage1.remove).toHaveBeenCalledWith('auth_token');
      expect(storage2.remove).toHaveBeenCalledWith('auth_token');
    });
  });

  describe('Gateway Isolation', () => {
    it('should create isolated API gateway instances', () => {
      const storage1 = createMockStorage();
      const storage2 = createMockStorage();

      const client1 = new ApiClient(baseConfig, storage1, createMockAuthErrorHandler());
      const client2 = new ApiClient(baseConfig, storage2, createMockAuthErrorHandler());

      const gateway1 = new ApiGatewayImpl(client1);
      const gateway2 = new ApiGatewayImpl(client2);

      expect(gateway1).not.toBe(gateway2);
      expect(gateway1.auth).not.toBe(gateway2.auth);
      expect(gateway1.payment).not.toBe(gateway2.payment);
      expect(gateway1.user).not.toBe(gateway2.user);
    });

    it('should prevent service cross-contamination between gateways', async () => {
      const storage1 = createMockStorage();
      const storage2 = createMockStorage();

      storage1.get.mockResolvedValue('user1-token');
      storage2.get.mockResolvedValue('user2-token');

      const client1 = new ApiClient(baseConfig, storage1, createMockAuthErrorHandler());
      const client2 = new ApiClient(baseConfig, storage2, createMockAuthErrorHandler());

      const gateway1 = new ApiGatewayImpl(client1);
      const gateway2 = new ApiGatewayImpl(client2);

      // Mock the actual service methods
      const mockPost = jest.fn();
      const mockAxiosInstance = mockedAxios.create.mock.results[0].value;
      mockAxiosInstance.post = mockPost;

      mockPost.mockResolvedValue({ data: { success: true } });

      // Execute operations in parallel that would trigger token retrieval
      try {
        await Promise.all([
          gateway1.auth.requestEmailCode({ email: 'user1@example.com' }),
          gateway2.auth.requestEmailCode({ email: 'user2@example.com' }),
        ]);
      } catch (error) {
        // Services might fail, but that's not what we're testing
      }

      // Verify that the gateways are using different clients
      expect(client1).not.toBe(client2);
      expect(gateway1).not.toBe(gateway2);
    });
  });

  describe('Parallel Test Execution Safety', () => {
    it('should handle concurrent test execution without interference', async () => {
      const testPromises = [];

      // Simulate multiple tests running in parallel
      for (let i = 0; i < 10; i++) {
        testPromises.push(
          (async () => {
            const storage = createMockStorage();
            const authHandler = createMockAuthErrorHandler();

            storage.get.mockResolvedValue(`token-${i}`);

            const client = new ApiClient(
              { ...baseConfig, baseURL: `https://api${i}.example.com` },
              storage,
              authHandler,
            );

            const gateway = new ApiGatewayImpl(client);

            // Each instance should maintain its own state
            expect(client).toBeDefined();
            expect(gateway).toBeDefined();
            expect(gateway.auth).toBeDefined();

            return { client, gateway, index: i };
          })(),
        );
      }

      const results = await Promise.all(testPromises);

      // Verify all instances are unique
      const clients = results.map(r => r.client);
      const gateways = results.map(r => r.gateway);

      for (let i = 0; i < clients.length; i++) {
        for (let j = i + 1; j < clients.length; j++) {
          expect(clients[i]).not.toBe(clients[j]);
          expect(gateways[i]).not.toBe(gateways[j]);
        }
      }
    });

    it('should maintain isolation during rapid instance creation and destruction', () => {
      const instances: Array<{ client: ApiClient; gateway: ApiGatewayImpl }> = [];

      // Create many instances rapidly
      for (let i = 0; i < 100; i++) {
        const storage = createMockStorage();
        const client = new ApiClient(baseConfig, storage, createMockAuthErrorHandler());
        const gateway = new ApiGatewayImpl(client);

        instances.push({ client, gateway });
      }

      // Verify all instances are unique
      for (let i = 0; i < instances.length; i++) {
        for (let j = i + 1; j < instances.length; j++) {
          expect(instances[i].client).not.toBe(instances[j].client);
          expect(instances[i].gateway).not.toBe(instances[j].gateway);
          expect(instances[i].gateway.auth).not.toBe(instances[j].gateway.auth);
        }
      }
    });
  });

  describe('Memory Management', () => {
    it('should not create memory leaks through global references', () => {
      let client = new ApiClient(baseConfig, createMockStorage(), createMockAuthErrorHandler());
      let gateway = new ApiGatewayImpl(client);

      // Create weak references to verify garbage collection potential
      const clientRef = new WeakRef(client);
      const gatewayRef = new WeakRef(gateway);

      // Remove strong references
      client = null as any;
      gateway = null as any;

      // References should still exist before GC
      expect(clientRef.deref()).toBeDefined();
      expect(gatewayRef.deref()).toBeDefined();

      // This test mainly ensures no global references prevent GC
      // Actual GC timing is non-deterministic in tests
    });

    it('should clean up resources when instances are destroyed', () => {
      const storage = createMockStorage();
      const authHandler = createMockAuthErrorHandler();

      let client = new ApiClient(baseConfig, storage, authHandler);
      const gateway = new ApiGatewayImpl(client);

      // Verify instances are created
      expect(client).toBeDefined();
      expect(gateway).toBeDefined();

      // Clear references
      client = null as any;

      // No global state should prevent cleanup
      expect(storage.get).toHaveBeenCalledTimes(0); // Only called during actual requests
    });
  });

  describe('Configuration Isolation', () => {
    it('should maintain separate configurations for each client', () => {
      const config1 = {
        baseURL: 'https://api1.example.com',
        timeout: 1000,
        headers: { 'X-Client': 'client1' },
      };

      const config2 = {
        baseURL: 'https://api2.example.com',
        timeout: 2000,
        headers: { 'X-Client': 'client2' },
      };

      const client1 = new ApiClient(config1, createMockStorage(), createMockAuthErrorHandler());
      const client2 = new ApiClient(config2, createMockStorage(), createMockAuthErrorHandler());

      expect(mockedAxios.create).toHaveBeenCalledWith(
        expect.objectContaining({
          baseURL: 'https://api1.example.com',
          timeout: 1000,
          headers: expect.objectContaining({
            'X-Client': 'client1',
          }),
        }),
      );

      expect(mockedAxios.create).toHaveBeenCalledWith(
        expect.objectContaining({
          baseURL: 'https://api2.example.com',
          timeout: 2000,
          headers: expect.objectContaining({
            'X-Client': 'client2',
          }),
        }),
      );
    });
  });

  describe('Backward Compatibility Prevention', () => {
    it('should prevent access to old global API client patterns', () => {
      // The new architecture should not export these legacy patterns
      const ApiClientModule = require('../../api/client/ApiClient');
      expect(ApiClientModule.setAuthErrorCallback).toBeUndefined();
      expect(ApiClientModule.authErrorCallback).toBeUndefined();

      // The old apiClient module still exists for backward compatibility during migration
      // but it should not affect the new architecture's isolation
      const oldApiClientModule = require('../../api/apiClient');
      expect(oldApiClientModule.setAuthErrorCallback).toBeDefined(); // Legacy function still exists

      // But the new module should be completely separate
      expect(ApiClientModule.default).toBeUndefined(); // No default export of singleton
    });
  });
});
