/**
 * Simplified useWebSocket Hook Tests
 *
 * Focused tests for core WebSocket functionality that work reliably
 * in the React Native testing environment.
 */

import AsyncStorage from '@react-native-async-storage/async-storage';
import { renderHook, act } from '@testing-library/react-native';

import { MockWebSocket } from '../utils/websocket-test-utils';
import { useWebSocket, useWebSocketEnhanced } from '@/hooks/useWebSocket';

// Mock AsyncStorage
jest.mock('@react-native-async-storage/async-storage', () => ({
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
}));

// MockWebSocket is imported from websocket-test-utils

describe('useWebSocket - Core Functionality', () => {
  let mockWebSocket: MockWebSocket;
  const originalConsole = {
    log: console.log,
    error: console.error,
    warn: console.warn,
  };

  beforeEach(() => {
    // Setup mock
    mockWebSocket = new MockWebSocket('ws://test');
    (global as any).WebSocket = jest.fn(() => mockWebSocket);

    // Mock AsyncStorage
    (AsyncStorage.getItem as jest.Mock).mockImplementation((key: string) => {
      if (key === 'auth_token') {
        return Promise.resolve('test_token');
      }
      return Promise.resolve(null);
    });

    // Suppress console - use proper mocks
    if (__DEV__) {
      // Suppress console - use proper mocks
      console.log = jest.fn();
      // Suppress console - use proper mocks
    }
    console.error = jest.fn();
    if (__DEV__) {
      console.warn = jest.fn();
    }

    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
    if (__DEV__) {
      jest.useRealTimers();
      console.log = originalConsole.log;
      jest.useRealTimers();
    }
    console.error = originalConsole.error;
    if (__DEV__) {
      console.warn = originalConsole.warn;
    }
    jest.clearAllMocks();
  });

  describe('Basic Connection', () => {
    it('should initialize with disconnected state', () => {
      const { result } = renderHook(() =>
        useWebSocket({
          url: 'ws://localhost:8000/test/',
          channelName: 'test',
          shouldConnect: true,
        }),
      );

      expect(result.current.isConnected).toBe(false);
      expect(result.current.error).toBeNull();
      expect(typeof result.current.sendMessage).toBe('function');
      expect(typeof result.current.connect).toBe('function');
      expect(typeof result.current.disconnect).toBe('function');
    });

    it('should not connect when shouldConnect is false', () => {
      renderHook(() =>
        useWebSocket({
          url: 'ws://localhost:8000/test/',
          channelName: 'test',
          shouldConnect: false,
        }),
      );

      expect(global.WebSocket).not.toHaveBeenCalled();
    });

    it('should connect when shouldConnect is true', async () => {
      renderHook(() =>
        useWebSocket({
          url: 'ws://localhost:8000/test/',
          channelName: 'test',
          shouldConnect: true,
        }),
      );

      // Wait for async operations to complete
      await act(async () => {
        await Promise.resolve();
      });

      // Should attempt to create WebSocket
      expect(global.WebSocket).toHaveBeenCalled();
    });

    it('should handle missing auth token', async () => {
      (AsyncStorage.getItem as jest.Mock).mockResolvedValue(null);

      const { result } = renderHook(() =>
        useWebSocket({
          url: 'ws://localhost:8000/test/',
          channelName: 'test',
          shouldConnect: true,
        }),
      );

      // Let async operations complete
      await act(async () => {
        await Promise.resolve();
        jest.runAllTimers();
      });

      expect(result.current.error).toBe('No authentication token found');
    });
  });

  describe('Message Handling', () => {
    it('should handle received messages', async () => {
      const mockOnMessage = jest.fn();

      const { result } = renderHook(() =>
        useWebSocket({
          url: 'ws://localhost:8000/test/',
          channelName: 'test',
          onMessage: mockOnMessage,
          shouldConnect: true,
        }),
      );

      // Simulate connection and message
      await act(async () => {
        // Let the WebSocket be created first
        await Promise.resolve();
        mockWebSocket.triggerOpen();
        mockWebSocket.triggerMessage({ type: 'test', data: 'hello' });
      });

      expect(mockOnMessage).toHaveBeenCalledWith({ type: 'test', data: 'hello' });
    });

    it('should handle malformed JSON gracefully', async () => {
      const mockOnMessage = jest.fn();

      renderHook(() =>
        useWebSocket({
          url: 'ws://localhost:8000/test/',
          channelName: 'test',
          onMessage: mockOnMessage,
          shouldConnect: true,
        }),
      );

      await act(async () => {
        await Promise.resolve();
        mockWebSocket.triggerOpen();
        mockWebSocket.triggerMessage('invalid json {');
      });

      expect(mockOnMessage).not.toHaveBeenCalled();
      expect(console.error).toHaveBeenCalledWith(
        'Error parsing WebSocket message:',
        expect.any(Error),
      );
    });

    it('should send messages when connected', async () => {
      const { result } = renderHook(() =>
        useWebSocket({
          url: 'ws://localhost:8000/test/',
          channelName: 'test',
          shouldConnect: true,
        }),
      );

      await act(async () => {
        await Promise.resolve();
        mockWebSocket.triggerOpen();
      });

      // Check connection state first
      expect(result.current.isConnected).toBe(true);

      act(() => {
        result.current.sendMessage({ type: 'test', data: 'hello' });
      });

      expect(mockWebSocket.send).toHaveBeenCalledWith(
        JSON.stringify({ type: 'test', data: 'hello' }),
      );
    });

    it('should not send messages when disconnected', () => {
      const { result } = renderHook(() =>
        useWebSocket({
          url: 'ws://localhost:8000/test/',
          channelName: 'test',
          shouldConnect: true,
        }),
      );

      act(() => {
        result.current.sendMessage({ type: 'test', data: 'hello' });
      });

      expect(mockWebSocket.send).not.toHaveBeenCalled();
      if (__DEV__) {
        expect(console.warn).toHaveBeenCalledWith('WebSocket not connected, cannot send message');
      }
    });
  });

  describe('Connection State Management', () => {
    it('should update connection state on open', async () => {
      const mockOnOpen = jest.fn();

      const { result } = renderHook(() =>
        useWebSocket({
          url: 'ws://localhost:8000/test/',
          channelName: 'test',
          onOpen: mockOnOpen,
          shouldConnect: true,
        }),
      );

      await act(async () => {
        await Promise.resolve();
        mockWebSocket.triggerOpen();
      });

      expect(result.current.isConnected).toBe(true);
      expect(mockOnOpen).toHaveBeenCalledTimes(1);
    });

    it('should update connection state on close', async () => {
      const mockOnClose = jest.fn();

      const { result } = renderHook(() =>
        useWebSocket({
          url: 'ws://localhost:8000/test/',
          channelName: 'test',
          onClose: mockOnClose,
          shouldConnect: true,
        }),
      );

      await act(async () => {
        await Promise.resolve();
        mockWebSocket.triggerOpen();
      });

      expect(result.current.isConnected).toBe(true);

      await act(async () => {
        mockWebSocket.triggerClose();
      });

      expect(result.current.isConnected).toBe(false);
      expect(mockOnClose).toHaveBeenCalledTimes(1);
    });

    it('should handle errors', async () => {
      const mockOnError = jest.fn();

      const { result } = renderHook(() =>
        useWebSocket({
          url: 'ws://localhost:8000/test/',
          channelName: 'test',
          onError: mockOnError,
          shouldConnect: true,
        }),
      );

      await act(async () => {
        await Promise.resolve();
        mockWebSocket.triggerError();
      });

      expect(result.current.error).toBe('WebSocket connection error');
      expect(mockOnError).toHaveBeenCalledTimes(1);
    });
  });

  describe('Manual Connection Control', () => {
    it('should allow manual disconnect', async () => {
      const { result } = renderHook(() =>
        useWebSocket({
          url: 'ws://localhost:8000/test/',
          channelName: 'test',
          shouldConnect: true,
        }),
      );

      await act(async () => {
        await Promise.resolve();
        mockWebSocket.triggerOpen();
      });

      expect(result.current.isConnected).toBe(true);

      act(() => {
        result.current.disconnect();
      });

      expect(mockWebSocket.close).toHaveBeenCalledWith(1000, 'User disconnected');
    });
  });
});

describe('useWebSocketEnhanced - Core Functionality', () => {
  let mockWebSocket: MockWebSocket;
  const originalConsole = {
    log: console.log,
    error: console.error,
    warn: console.warn,
  };

  beforeEach(() => {
    mockWebSocket = new MockWebSocket('ws://test');
    (global as any).WebSocket = jest.fn(() => mockWebSocket);

    if (__DEV__) {
      console.log = jest.fn();
    }
    console.error = jest.fn();
    if (__DEV__) {
      console.warn = jest.fn();
    }

    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
    if (__DEV__) {
      jest.useRealTimers();
      console.log = originalConsole.log;
      jest.useRealTimers();
    }
    console.error = originalConsole.error;
    if (__DEV__) {
      console.warn = originalConsole.warn;
    }
    jest.clearAllMocks();
  });

  describe('Enhanced Features', () => {
    it('should handle null URL gracefully', async () => {
      const { result } = renderHook(() => useWebSocketEnhanced(null));

      expect(result.current.isConnected).toBe(false);
      expect(result.current.lastMessage).toBeNull();
      expect(typeof result.current.sendMessage).toBe('function');
      expect(typeof result.current.connect).toBe('function');
      expect(typeof result.current.disconnect).toBe('function');

      // When URL is null, connect is never called, so no warning is logged automatically
      // But if we manually call connect, it should warn
      await act(async () => {
        await result.current.connect();
      });

      if (__DEV__) {
        expect(console.warn).toHaveBeenCalledWith('No WebSocket URL provided');
      }
    });

    it('should track last message', async () => {
      const { result } = renderHook(() => useWebSocketEnhanced('ws://localhost:8000/test/'));

      await act(async () => {
        await Promise.resolve();
        mockWebSocket.triggerOpen();
        mockWebSocket.triggerMessage('test message');
      });

      expect(result.current.lastMessage).toBe('test message');
    });

    it('should send string and object messages', async () => {
      const { result } = renderHook(() => useWebSocketEnhanced('ws://localhost:8000/test/'));

      await act(async () => {
        await Promise.resolve();
        mockWebSocket.triggerOpen();
      });

      expect(result.current.isConnected).toBe(true);

      act(() => {
        // Send string message
        result.current.sendMessage('string message');
        expect(mockWebSocket.send).toHaveBeenCalledWith('string message');

        // Send object message
        const objMessage = { type: 'test', data: 'hello' };
        result.current.sendMessage(objMessage);
        expect(mockWebSocket.send).toHaveBeenCalledWith(JSON.stringify(objMessage));
      });
    });
  });

  describe('Connection State', () => {
    it('should reflect connection state correctly', async () => {
      const { result } = renderHook(() => useWebSocketEnhanced('ws://localhost:8000/test/'));

      expect(result.current.isConnected).toBe(false);

      await act(async () => {
        await Promise.resolve();
        mockWebSocket.triggerOpen();
      });

      expect(result.current.isConnected).toBe(true);

      await act(async () => {
        mockWebSocket.triggerClose();
      });

      expect(result.current.isConnected).toBe(false);
    });
  });
});
