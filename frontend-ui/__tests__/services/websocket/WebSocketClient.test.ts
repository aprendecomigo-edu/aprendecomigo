/**
 * Tests for WebSocketClient - Unified WebSocket Client Integration
 * 
 * This tests the new modular architecture where WebSocketClient integrates
 * ConnectionManager, ReconnectionStrategy, and MessageDispatcher to provide
 * a unified interface replacing the monolithic useWebSocket hook.
 * 
 * EXPECTED TO FAIL: These tests validate the new architecture that hasn't been implemented yet.
 */

import { WebSocketClient } from '@/services/websocket/WebSocketClient';
import { ConnectionManager } from '@/services/websocket/connection/ConnectionManager';
import { MessageDispatcher } from '@/services/websocket/messaging/MessageDispatcher';
import { ExponentialBackoffStrategy } from '@/services/websocket/reconnection/strategies';
import {
  WebSocketConfig,
  ConnectionState,
  AuthProvider,
  ReconnectionConfig,
  WebSocketMessage
} from '@/services/websocket/types';

// Mock dependencies
jest.mock('@/services/websocket/connection/ConnectionManager');
jest.mock('@/services/websocket/messaging/MessageDispatcher');
jest.mock('@/services/websocket/reconnection/strategies');

// Mock CloseEvent for Node environment
(global as any).CloseEvent = class extends Event {
  constructor(type: string, init?: { code?: number; reason?: string }) {
    super(type);
    this.code = init?.code || 1000;
    this.reason = init?.reason || '';
  }
  code: number;
  reason: string;
};

const MockConnectionManager = ConnectionManager as jest.MockedClass<typeof ConnectionManager>;
const MockMessageDispatcher = MessageDispatcher as jest.MockedClass<typeof MessageDispatcher>;
const MockExponentialBackoffStrategy = ExponentialBackoffStrategy as jest.MockedClass<typeof ExponentialBackoffStrategy>;

describe('WebSocketClient', () => {
  let client: WebSocketClient;
  let mockConnectionManager: jest.Mocked<ConnectionManager>;
  let mockMessageDispatcher: jest.Mocked<MessageDispatcher>;
  let mockReconnectionStrategy: jest.Mocked<ExponentialBackoffStrategy>;
  let mockAuthProvider: jest.Mocked<AuthProvider>;
  let config: WebSocketConfig;

  beforeEach(() => {
    jest.clearAllMocks();

    // Mock AuthProvider
    mockAuthProvider = {
      getToken: jest.fn().mockResolvedValue('mock-token'),
      onAuthError: jest.fn(),
    };

    // Mock ConnectionManager
    mockConnectionManager = {
      connect: jest.fn().mockResolvedValue(undefined),
      disconnect: jest.fn(),
      send: jest.fn(),
      getState: jest.fn().mockReturnValue(ConnectionState.DISCONNECTED),
      on: jest.fn(),
      off: jest.fn(),
    } as any;

    // Mock MessageDispatcher
    mockMessageDispatcher = {
      addHandler: jest.fn(),
      removeHandler: jest.fn(),
      removeAllHandlers: jest.fn(),
      dispatch: jest.fn().mockResolvedValue(undefined),
      clearAllHandlers: jest.fn(),
      on: jest.fn(),
      off: jest.fn(),
    } as any;

    // Mock ReconnectionStrategy
    mockReconnectionStrategy = {
      shouldReconnect: jest.fn().mockReturnValue(true),
      getNextDelay: jest.fn().mockReturnValue(1000),
      reset: jest.fn(),
    } as any;

    // Setup mocks
    MockConnectionManager.mockImplementation(() => mockConnectionManager);
    MockMessageDispatcher.mockImplementation(() => mockMessageDispatcher);
    MockExponentialBackoffStrategy.mockImplementation(() => mockReconnectionStrategy);

    // Test configuration
    config = {
      url: 'ws://localhost:8000/ws/test',
      auth: mockAuthProvider,
      reconnection: {
        strategy: 'exponential',
        initialDelay: 1000,
        maxDelay: 30000,
        backoffFactor: 2,
        maxAttempts: 5
      }
    };

    client = new WebSocketClient(config);
  });

  describe('Initialization', () => {
    it('should create client with all required components', () => {
      // Assert
      expect(MockConnectionManager).toHaveBeenCalledWith(config);
      expect(MockMessageDispatcher).toHaveBeenCalled();
      expect(MockExponentialBackoffStrategy).toHaveBeenCalledWith(config.reconnection);
    });

    it('should use default configuration for missing options', () => {
      // Arrange
      const minimalConfig: WebSocketConfig = {
        url: 'ws://localhost:8000/ws/minimal'
      };

      // Act
      const minimalClient = new WebSocketClient(minimalConfig);

      // Assert
      expect(MockConnectionManager).toHaveBeenCalledWith(
        expect.objectContaining({
          url: 'ws://localhost:8000/ws/minimal'
        })
      );
      expect(MockExponentialBackoffStrategy).toHaveBeenCalledWith(
        expect.objectContaining({
          strategy: 'exponential',
          initialDelay: 1000,
          maxDelay: 30000
        })
      );
    });

    it('should validate configuration on creation', () => {
      // Arrange
      const invalidConfigs = [
        { url: '' },
        { url: 'invalid-url' },
        { url: 'ws://test', reconnection: { maxAttempts: -1 } }
      ];

      // Act & Assert
      invalidConfigs.forEach(invalidConfig => {
        expect(() => new WebSocketClient(invalidConfig as any)).toThrow();
      });
    });
  });

  describe('Connection Management', () => {
    it('should connect through connection manager', async () => {
      // Act
      await client.connect();

      // Assert
      expect(mockConnectionManager.connect).toHaveBeenCalled();
    });

    it('should disconnect through connection manager', () => {
      // Act
      client.disconnect();

      // Assert
      expect(mockConnectionManager.disconnect).toHaveBeenCalled();
    });

    it('should get connection state from connection manager', () => {
      // Arrange
      mockConnectionManager.getState.mockReturnValue(ConnectionState.CONNECTED);

      // Act
      const state = client.getConnectionState();

      // Assert
      expect(state).toBe(ConnectionState.CONNECTED);
      expect(mockConnectionManager.getState).toHaveBeenCalled();
    });

    it('should check if connected based on connection state', () => {
      // Arrange
      mockConnectionManager.getState.mockReturnValue(ConnectionState.CONNECTED);

      // Act
      const isConnected = client.isConnected();

      // Assert
      expect(isConnected).toBe(true);

      // Test disconnected state
      mockConnectionManager.getState.mockReturnValue(ConnectionState.DISCONNECTED);
      expect(client.isConnected()).toBe(false);
    });
  });

  describe('Message Handling', () => {
    it('should send messages through connection manager', () => {
      // Arrange
      const message: WebSocketMessage = {
        type: 'chat.message',
        content: 'Hello world'
      };

      // Act
      client.send(message);

      // Assert
      expect(mockConnectionManager.send).toHaveBeenCalledWith(message);
    });

    it('should add message handlers through dispatcher', () => {
      // Arrange
      const handler = jest.fn();

      // Act
      client.addMessageHandler('chat.message', handler);

      // Assert
      expect(mockMessageDispatcher.addHandler).toHaveBeenCalledWith('chat.message', handler, undefined);
    });

    it('should remove message handlers through dispatcher', () => {
      // Arrange
      const handler = jest.fn();

      // Act
      client.removeMessageHandler('chat.message', handler);

      // Assert
      expect(mockMessageDispatcher.removeHandler).toHaveBeenCalledWith('chat.message', handler);
    });

    it('should support handler options', () => {
      // Arrange
      const handler = jest.fn();
      const options = { priority: 10, once: true };

      // Act
      client.addMessageHandler('priority.message', handler, options);

      // Assert
      expect(mockMessageDispatcher.addHandler).toHaveBeenCalledWith('priority.message', handler, options);
    });
  });

  describe('Auto-Reconnection Integration', () => {
    beforeEach(() => {
      // Setup connection manager to emit events
      mockConnectionManager.on.mockImplementation((event, callback) => {
        if (event === 'statechange') {
          // Store callback for later invocation
          (mockConnectionManager as any)._stateChangeCallback = callback;
        } else if (event === 'close') {
          (mockConnectionManager as any)._closeCallback = callback;
        }
      });
    });

    it('should handle connection close and attempt reconnection', async () => {
      // Arrange
      jest.useFakeTimers();
      await client.connect();

      // Simulate connection close event
      const closeEvent = new CloseEvent('close', { code: 1006, reason: 'Network error' });

      // Act
      const closeCallback = (mockConnectionManager as any)._closeCallback;
      closeCallback(closeEvent);

      // Fast-forward timers
      jest.advanceTimersByTime(1000);

      // Assert
      expect(mockReconnectionStrategy.shouldReconnect).toHaveBeenCalledWith(closeEvent, 0);
      expect(mockReconnectionStrategy.getNextDelay).toHaveBeenCalledWith(0);
      expect(mockConnectionManager.connect).toHaveBeenCalledTimes(2); // Initial + reconnect

      jest.useRealTimers();
    });

    it('should stop reconnection when max attempts reached', async () => {
      // Arrange
      jest.useFakeTimers();
      mockReconnectionStrategy.shouldReconnect.mockReturnValue(false);
      await client.connect();

      const closeEvent = new CloseEvent('close', { code: 1006 });

      // Act
      const closeCallback = (mockConnectionManager as any)._closeCallback;
      closeCallback(closeEvent);

      jest.advanceTimersByTime(2000);

      // Assert
      expect(mockConnectionManager.connect).toHaveBeenCalledTimes(1); // Only initial connect

      jest.useRealTimers();
    });

    it('should not reconnect for normal closures', async () => {
      // Arrange
      jest.useFakeTimers();
      mockReconnectionStrategy.shouldReconnect.mockReturnValue(false);
      await client.connect();

      const normalClose = new CloseEvent('close', { code: 1000, reason: 'Normal closure' });

      // Act
      const closeCallback = (mockConnectionManager as any)._closeCallback;
      closeCallback(normalClose);

      jest.advanceTimersByTime(5000);

      // Assert
      expect(mockReconnectionStrategy.shouldReconnect).toHaveBeenCalledWith(normalClose, 0);
      expect(mockConnectionManager.connect).toHaveBeenCalledTimes(1); // Only initial

      jest.useRealTimers();
    });

    it('should reset reconnection strategy on successful connection', async () => {
      // Arrange
      await client.connect();

      // Simulate successful connection
      const stateCallback = (mockConnectionManager as any)._stateChangeCallback;
      stateCallback(ConnectionState.CONNECTED);

      // Assert
      expect(mockReconnectionStrategy.reset).toHaveBeenCalled();
    });

    it('should handle multiple rapid disconnections', async () => {
      // Arrange
      jest.useFakeTimers();
      mockReconnectionStrategy.getNextDelay
        .mockReturnValueOnce(1000)
        .mockReturnValueOnce(2000)
        .mockReturnValueOnce(4000);

      await client.connect();

      const closeEvent = new CloseEvent('close', { code: 1006 });
      const closeCallback = (mockConnectionManager as any)._closeCallback;

      // Act - Simulate rapid disconnections
      closeCallback(closeEvent);
      jest.advanceTimersByTime(1000);

      closeCallback(closeEvent);
      jest.advanceTimersByTime(2000);

      closeCallback(closeEvent);
      jest.advanceTimersByTime(4000);

      // Assert
      expect(mockReconnectionStrategy.getNextDelay).toHaveBeenCalledWith(0);
      expect(mockReconnectionStrategy.getNextDelay).toHaveBeenCalledWith(1);
      expect(mockReconnectionStrategy.getNextDelay).toHaveBeenCalledWith(2);

      jest.useRealTimers();
    });
  });

  describe('Event Integration', () => {
    it('should forward connection events to client listeners', () => {
      // Arrange
      const connectionListener = jest.fn();
      const disconnectionListener = jest.fn();

      client.onConnect(connectionListener);
      client.onDisconnect(disconnectionListener);

      // Simulate connection manager events
      const stateCallback = (mockConnectionManager as any)._stateChangeCallback;

      // Act
      stateCallback(ConnectionState.CONNECTED);
      stateCallback(ConnectionState.DISCONNECTED);

      // Assert
      expect(connectionListener).toHaveBeenCalled();
      expect(disconnectionListener).toHaveBeenCalled();
    });

    it('should integrate message dispatcher with connection manager', () => {
      // Arrange
      mockConnectionManager.on.mockImplementation((event, callback) => {
        if (event === 'message') {
          (mockConnectionManager as any)._messageCallback = callback;
        }
      });

      // Create new client to trigger setup
      new WebSocketClient(config);

      // Act - Simulate message from connection manager
      const messageCallback = (mockConnectionManager as any)._messageCallback;
      const testMessage: WebSocketMessage = { type: 'test.message', data: 'test' };
      messageCallback(testMessage);

      // Assert
      expect(mockMessageDispatcher.dispatch).toHaveBeenCalledWith(testMessage);
    });

    it('should handle connection manager errors gracefully', () => {
      // Arrange
      const errorListener = jest.fn();
      client.onError(errorListener);

      mockConnectionManager.on.mockImplementation((event, callback) => {
        if (event === 'error') {
          (mockConnectionManager as any)._errorCallback = callback;
        }
      });

      // Act
      const errorCallback = (mockConnectionManager as any)._errorCallback;
      const testError = new Error('Connection failed');
      errorCallback(testError);

      // Assert
      expect(errorListener).toHaveBeenCalledWith(testError);
    });
  });

  describe('Resource Management', () => {
    it('should clean up all resources on disposal', () => {
      // Act
      client.dispose();

      // Assert
      expect(mockConnectionManager.disconnect).toHaveBeenCalled();
      expect(mockMessageDispatcher.clearAllHandlers).toHaveBeenCalled();
    });

    it('should prevent operations after disposal', () => {
      // Arrange
      client.dispose();

      // Act & Assert
      await expect(client.connect()).rejects.toThrow('WebSocketClient has been disposed');
      expect(() => client.send({ type: 'test' })).toThrow('WebSocketClient has been disposed');
      expect(() => client.addMessageHandler('test', jest.fn())).toThrow('WebSocketClient has been disposed');
    });

    it('should handle concurrent connect/disconnect calls', async () => {
      // Act
      const connectPromise1 = client.connect();
      const connectPromise2 = client.connect();
      client.disconnect();

      // Assert
      await expect(connectPromise1).resolves.toBeUndefined();
      await expect(connectPromise2).resolves.toBeUndefined();
      expect(mockConnectionManager.connect).toHaveBeenCalledTimes(1);
      expect(mockConnectionManager.disconnect).toHaveBeenCalled();
    });

    it('should handle memory leaks in long-running connections', async () => {
      // Arrange
      const handlers = Array.from({ length: 1000 }, (_, i) => jest.fn());

      // Act - Add many handlers
      handlers.forEach((handler, i) => {
        client.addMessageHandler(`handler.${i}`, handler);
      });

      // Remove some handlers
      handlers.slice(0, 500).forEach((handler, i) => {
        client.removeMessageHandler(`handler.${i}`, handler);
      });

      // Dispose
      client.dispose();

      // Assert
      expect(mockMessageDispatcher.removeHandler).toHaveBeenCalledTimes(500);
      expect(mockMessageDispatcher.clearAllHandlers).toHaveBeenCalled();
    });
  });

  describe('Configuration Updates', () => {
    it('should support runtime configuration updates', () => {
      // Arrange
      const newConfig: Partial<WebSocketConfig> = {
        reconnection: {
          strategy: 'linear',
          initialDelay: 2000,
          maxAttempts: 10
        }
      };

      // Act
      client.updateConfig(newConfig);

      // Assert
      expect(client.getConfig()).toEqual(
        expect.objectContaining({
          url: config.url,
          auth: config.auth,
          reconnection: expect.objectContaining(newConfig.reconnection)
        })
      );
    });

    it('should validate configuration updates', () => {
      // Arrange
      const invalidUpdates = [
        { url: '' },
        { reconnection: { maxAttempts: -1 } },
        { auth: null }
      ];

      // Act & Assert
      invalidUpdates.forEach(invalidUpdate => {
        expect(() => client.updateConfig(invalidUpdate as any)).toThrow();
      });
    });

    it('should apply configuration changes to active connection', () => {
      // Arrange
      const newAuth: AuthProvider = {
        getToken: jest.fn().mockResolvedValue('new-token'),
        onAuthError: jest.fn()
      };

      // Act
      client.updateConfig({ auth: newAuth });

      // Assert - Should update connection manager config
      expect(MockConnectionManager).toHaveBeenCalledWith(
        expect.objectContaining({ auth: newAuth })
      );
    });
  });

  describe('Backwards Compatibility', () => {
    it('should provide useWebSocket-compatible interface', () => {
      // Act & Assert - Should have all the methods the hook provided
      expect(typeof client.connect).toBe('function');
      expect(typeof client.disconnect).toBe('function');
      expect(typeof client.send).toBe('function');
      expect(typeof client.isConnected).toBe('function');
      expect(typeof client.addMessageHandler).toBe('function');
      expect(typeof client.removeMessageHandler).toBe('function');
    });

    it('should maintain existing event patterns', () => {
      // Arrange
      const onMessage = jest.fn();
      const onError = jest.fn();
      const onOpen = jest.fn();
      const onClose = jest.fn();

      // Act
      client.onMessage(onMessage);
      client.onError(onError);
      client.onConnect(onOpen);
      client.onDisconnect(onClose);

      // Assert - Should register handlers in expected format
      expect(mockMessageDispatcher.addHandler).toHaveBeenCalledWith('*', onMessage);
    });

    it('should handle migration from hook to client seamlessly', () => {
      // Arrange - Create client with hook-like configuration
      const hookConfig = {
        url: 'ws://localhost:8000/ws/chat',
        onMessage: jest.fn(),
        onError: jest.fn(),
        onOpen: jest.fn(),
        onClose: jest.fn(),
        shouldConnect: true
      };

      // Act
      const migratedClient = WebSocketClient.fromHookConfig(hookConfig);

      // Assert
      expect(migratedClient.isConnected()).toBeDefined();
      expect(typeof migratedClient.send).toBe('function');
      
      // Should auto-connect if shouldConnect was true
      expect(mockConnectionManager.connect).toHaveBeenCalled();
    });
  });
});