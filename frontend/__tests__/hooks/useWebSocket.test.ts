/**
 * useWebSocket Hook Tests
 *
 * Comprehensive tests for WebSocket connection management including:
 * - Connection establishment and cleanup
 * - Reconnection logic with exponential backoff
 * - Message handling and parsing
 * - Error handling and graceful degradation
 * - Authentication token refresh scenarios
 * - Memory leak prevention on unmount
 * - Connection state reporting
 */

import AsyncStorage from '@react-native-async-storage/async-storage';
import { renderHook, act, waitFor } from '@testing-library/react-native';

import {
  MockWebSocket,
  WebSocketTestUtils,
  ConnectionStates,
  WebSocketErrorCodes,
} from '../utils/websocket-test-utils';

import { useWebSocket, useWebSocketEnhanced } from '@/hooks/useWebSocket';

// Mock AsyncStorage
jest.mock('@react-native-async-storage/async-storage', () => ({
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
}));

// Mock WebSocket
class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  readyState = MockWebSocket.CONNECTING;
  url: string;
  onopen: ((event: any) => void) | null = null;
  onclose: ((event: any) => void) | null = null;
  onmessage: ((event: any) => void) | null = null;
  onerror: ((event: any) => void) | null = null;

  constructor(url: string) {
    this.url = url;
    // Auto-connect after short delay
    setTimeout(() => {
      this.readyState = MockWebSocket.OPEN;
      if (this.onopen) {
        this.onopen(new Event('open'));
      }
    }, 10);
  }

  send = jest.fn();
  close = jest.fn(() => {
    this.readyState = MockWebSocket.CLOSED;
    if (this.onclose) {
      this.onclose({ code: 1000, reason: 'Normal closure', wasClean: true });
    }
  });

  simulateMessage(data: any) {
    if (this.onmessage) {
      this.onmessage({ data: typeof data === 'string' ? data : JSON.stringify(data) });
    }
  }

  simulateError() {
    if (this.onerror) {
      this.onerror(new Event('error'));
    }
  }

  simulateClose(code = 1006, reason = 'Connection lost') {
    this.readyState = MockWebSocket.CLOSED;
    if (this.onclose) {
      this.onclose({ code, reason, wasClean: false });
    }
  }
}

// Mock console methods to reduce noise in tests
const originalConsoleLog = console.log;
const originalConsoleError = console.error;

describe('useWebSocket', () => {
  let mockWebSocket: MockWebSocket;

  beforeEach(() => {
    // Setup fresh mock WebSocket for each test
    mockWebSocket = new MockWebSocket('ws://test');
    (global as any).WebSocket = jest.fn(() => mockWebSocket);

    // Mock AsyncStorage to return a valid auth token
    (AsyncStorage.getItem as jest.Mock).mockImplementation((key: string) => {
      if (key === 'auth_token') {
        return Promise.resolve('test_auth_token_123');
      }
      return Promise.resolve(null);
    });

    // Suppress console logs during tests
    if (__DEV__) {
      // Suppress console logs during tests
      console.log = jest.fn();
      // Suppress console logs during tests
    }
    console.error = jest.fn();

    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();

    // Restore console methods
    if (__DEV__) {
      // Restore console methods
      console.log = originalConsoleLog;
      // Restore console methods
    }
    console.error = originalConsoleError;

    // Clear all mocks
    jest.clearAllMocks();
  });

  describe('Connection Management', () => {
    it('should establish WebSocket connection with auth token', async () => {
      const mockOnOpen = jest.fn();
      const testUrl = 'ws://localhost:8000/test/';

      const { result } = renderHook(() =>
        useWebSocket({
          url: testUrl,
          channelName: 'test',
          onOpen: mockOnOpen,
          shouldConnect: true,
        }),
      );

      // Initially should be disconnected
      expect(result.current.isConnected).toBe(false);

      // Wait for connection to establish
      await act(async () => {
        jest.advanceTimersByTime(20); // Advance past connection delay
      });

      // Should be connected and callback called
      expect(result.current.isConnected).toBe(true);
      expect(mockOnOpen).toHaveBeenCalledTimes(1);
      expect(result.current.error).toBeNull();
    });

    it('should not connect when shouldConnect is false', async () => {
      const mockOnOpen = jest.fn();

      const { result } = renderHook(() =>
        useWebSocket({
          url: 'ws://localhost:8000/test/',
          channelName: 'test',
          onOpen: mockOnOpen,
          shouldConnect: false,
        }),
      );

      // Wait for potential connection
      await act(async () => {
        jest.advanceTimersByTime(100);
      });

      // Should remain disconnected
      expect(result.current.isConnected).toBe(false);
      expect(mockOnOpen).not.toHaveBeenCalled();
    });

    it('should handle missing auth token gracefully', async () => {
      (AsyncStorage.getItem as jest.Mock).mockResolvedValue(null);

      const { result } = renderHook(() =>
        useWebSocket({
          url: 'ws://localhost:8000/test/',
          channelName: 'test',
          shouldConnect: true,
        }),
      );

      await act(async () => {
        jest.advanceTimersByTime(100);
      });

      expect(result.current.isConnected).toBe(false);
      expect(result.current.error).toBe('No authentication token found');
    });

    it('should properly disconnect and cleanup on unmount', async () => {
      const { result, unmount } = renderHook(() =>
        useWebSocket({
          url: 'ws://localhost:8000/test/',
          channelName: 'test',
          shouldConnect: true,
        }),
      );

      // Wait for connection
      await act(async () => {
        jest.advanceTimersByTime(20);
      });

      expect(result.current.isConnected).toBe(true);

      // Unmount component
      act(() => {
        unmount();
      });

      // Check that WebSocket was closed properly
      expect(mockWebSocket.close).toHaveBeenCalled();
    });
  });

  describe('Message Handling', () => {
    it('should receive and parse JSON messages correctly', async () => {
      const mockOnMessage = jest.fn();

      const { result } = renderHook(() =>
        useWebSocket({
          url: 'ws://localhost:8000/test/',
          channelName: 'test',
          onMessage: mockOnMessage,
          shouldConnect: true,
        }),
      );

      // Wait for connection
      await act(async () => {
        await WebSocketTestUtils.simulateConnection(mockWebSocket);
      });

      // Send a test message
      const testMessage = { type: 'test_message', data: { value: 123 } };
      act(() => {
        WebSocketTestUtils.simulateMessageSend(mockWebSocket, testMessage);
      });

      expect(mockOnMessage).toHaveBeenCalledWith(testMessage);
    });

    it('should handle malformed JSON messages gracefully', async () => {
      const mockOnMessage = jest.fn();

      const { result } = renderHook(() =>
        useWebSocket({
          url: 'ws://localhost:8000/test/',
          channelName: 'test',
          onMessage: mockOnMessage,
          shouldConnect: true,
        }),
      );

      // Wait for connection
      await act(async () => {
        await WebSocketTestUtils.simulateConnection(mockWebSocket);
      });

      // Send malformed JSON
      act(() => {
        mockWebSocket.simulateMessage('{ invalid json }');
      });

      // Should not crash and should not call onMessage
      expect(mockOnMessage).not.toHaveBeenCalled();
      expect(console.error).toHaveBeenCalledWith(
        'Error parsing WebSocket message:',
        expect.any(Error),
      );
    });

    it('should send messages correctly when connected', async () => {
      const mockSend = jest.spyOn(mockWebSocket, 'send');

      const { result } = renderHook(() =>
        useWebSocket({
          url: 'ws://localhost:8000/test/',
          channelName: 'test',
          shouldConnect: true,
        }),
      );

      // Wait for connection
      await act(async () => {
        await WebSocketTestUtils.simulateConnection(mockWebSocket);
      });

      const testMessage = { type: 'test', data: 'hello' };
      act(() => {
        result.current.sendMessage(testMessage);
      });

      expect(mockSend).toHaveBeenCalledWith(JSON.stringify(testMessage));
    });

    it('should not send messages when disconnected', async () => {
      const mockSend = jest.spyOn(mockWebSocket, 'send');

      const { result } = renderHook(() =>
        useWebSocket({
          url: 'ws://localhost:8000/test/',
          channelName: 'test',
          shouldConnect: false,
        }),
      );

      const testMessage = { type: 'test', data: 'hello' };
      act(() => {
        result.current.sendMessage(testMessage);
      });

      expect(mockSend).not.toHaveBeenCalled();
      if (__DEV__) {
        expect(console.warn).toHaveBeenCalledWith('WebSocket not connected, cannot send message');
      }
    });
  });

  describe('Reconnection Logic', () => {
    it('should attempt reconnection with exponential backoff', async () => {
      const mockOnClose = jest.fn();
      const reconnectionAttempts: number[] = [];

      // Track reconnection attempts
      const originalSetTimeout = global.setTimeout;
      global.setTimeout = jest.fn((callback, delay) => {
        reconnectionAttempts.push(delay);
        return originalSetTimeout(callback, 0); // Execute immediately for testing
      }) as any;

      const { result } = renderHook(() =>
        useWebSocket({
          url: 'ws://localhost:8000/test/',
          channelName: 'test',
          onClose: mockOnClose,
          shouldConnect: true,
        }),
      );

      // Wait for initial connection
      await act(async () => {
        jest.advanceTimersByTime(20);
      });

      // Simulate unexpected disconnection (not normal closure)
      await act(async () => {
        mockWebSocket.triggerClose(WebSocketErrorCodes.ABNORMAL_CLOSURE, 'Connection lost');
        jest.runAllTimers();
      });

      // Should have attempted reconnection with exponential backoff
      expect(reconnectionAttempts.length).toBeGreaterThan(0);
      // Check first retry delay is 1000ms (2^0 * 1000)
      expect(reconnectionAttempts[0]).toBe(1000);

      global.setTimeout = originalSetTimeout;
    });

    it('should stop reconnecting after max attempts', async () => {
      const reconnectionAttempts: number[] = [];

      // Mock setTimeout to track attempts
      const originalSetTimeout = global.setTimeout;
      global.setTimeout = jest.fn((callback, delay) => {
        reconnectionAttempts.push(delay);
        callback(); // Execute immediately
        return 0 as any;
      }) as any;

      const { result } = renderHook(() =>
        useWebSocket({
          url: 'ws://localhost:8000/test/',
          channelName: 'test',
          shouldConnect: true,
        }),
      );

      // Initial connection
      await act(async () => {
        jest.advanceTimersByTime(20);
      });

      // Simulate multiple disconnections
      for (let i = 0; i < 7; i++) {
        await act(async () => {
          mockWebSocket.triggerClose(WebSocketErrorCodes.ABNORMAL_CLOSURE);
          jest.runAllTimers();
        });
      }

      // Should have stopped at max attempts (5)
      expect(reconnectionAttempts.length).toBeLessThanOrEqual(5);

      global.setTimeout = originalSetTimeout;
    });

    it('should not reconnect on normal closure', async () => {
      const reconnectionAttempts: number[] = [];

      // Mock setTimeout to track attempts
      const originalSetTimeout = global.setTimeout;
      global.setTimeout = jest.fn((callback, delay) => {
        reconnectionAttempts.push(delay);
        return originalSetTimeout(callback, delay);
      }) as any;

      const { result } = renderHook(() =>
        useWebSocket({
          url: 'ws://localhost:8000/test/',
          channelName: 'test',
          shouldConnect: true,
        }),
      );

      // Wait for connection
      await act(async () => {
        jest.advanceTimersByTime(20);
      });

      // Normal disconnection
      await act(async () => {
        mockWebSocket.triggerClose(WebSocketErrorCodes.NORMAL_CLOSURE, 'User disconnected');
      });

      // Should not attempt reconnection
      expect(reconnectionAttempts).toHaveLength(0);

      global.setTimeout = originalSetTimeout;
    });
  });

  describe('Error Handling', () => {
    it('should handle WebSocket connection errors', async () => {
      const mockOnError = jest.fn();

      const { result } = renderHook(() =>
        useWebSocket({
          url: 'ws://localhost:8000/test/',
          channelName: 'test',
          onError: mockOnError,
          shouldConnect: true,
        }),
      );

      // Simulate connection error
      await act(async () => {
        mockWebSocket.triggerError();
      });

      expect(mockOnError).toHaveBeenCalledTimes(1);
      expect(result.current.error).toBe('WebSocket connection error');
    });

    it('should handle WebSocket send errors', async () => {
      const mockOnError = jest.fn();

      const { result } = renderHook(() =>
        useWebSocket({
          url: 'ws://localhost:8000/test/',
          channelName: 'test',
          onError: mockOnError,
          shouldConnect: true,
        }),
      );

      // Wait for connection
      await act(async () => {
        jest.advanceTimersByTime(20);
      });

      // Configure WebSocket to fail on send
      mockWebSocket.setShouldFailOnSend(true);

      // Try to send a message
      const testMessage = { type: 'test', data: 'hello' };
      act(() => {
        result.current.sendMessage(testMessage);
      });

      // Should handle the error gracefully
      expect(console.error).toHaveBeenCalledWith(
        'Error sending WebSocket message:',
        expect.any(Error),
      );
    });

    it('should handle AsyncStorage errors gracefully', async () => {
      (AsyncStorage.getItem as jest.Mock).mockRejectedValue(new Error('Storage error'));

      const { result } = renderHook(() =>
        useWebSocket({
          url: 'ws://localhost:8000/test/',
          channelName: 'test',
          shouldConnect: true,
        }),
      );

      await act(async () => {
        jest.advanceTimersByTime(100);
      });

      expect(result.current.isConnected).toBe(false);
      expect(result.current.error).toBe('Failed to create WebSocket connection');
    });
  });

  describe('Manual Connection Control', () => {
    it('should allow manual connection', async () => {
      const { result } = renderHook(() =>
        useWebSocket({
          url: 'ws://localhost:8000/test/',
          channelName: 'test',
          shouldConnect: false, // Start disconnected
        }),
      );

      expect(result.current.isConnected).toBe(false);

      // Manually connect
      await act(async () => {
        result.current.connect();
        jest.advanceTimersByTime(20);
      });

      expect(result.current.isConnected).toBe(true);
    });

    it('should allow manual disconnection', async () => {
      const { result } = renderHook(() =>
        useWebSocket({
          url: 'ws://localhost:8000/test/',
          channelName: 'test',
          shouldConnect: true,
        }),
      );

      // Wait for connection
      await act(async () => {
        jest.advanceTimersByTime(20);
      });

      expect(result.current.isConnected).toBe(true);

      // Manually disconnect
      await act(async () => {
        result.current.disconnect();
      });

      expect(result.current.isConnected).toBe(false);
    });
  });
});

describe('useWebSocketEnhanced', () => {
  let mockWebSocket: MockWebSocket;

  beforeEach(() => {
    mockWebSocket = new MockWebSocket('ws://test');
    (global as any).WebSocket = jest.fn(() => mockWebSocket);
    if (__DEV__) {
      (global as any).WebSocket = jest.fn(() => mockWebSocket);
      console.log = jest.fn();
      (global as any).WebSocket = jest.fn(() => mockWebSocket);
    }
    console.error = jest.fn();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
    if (__DEV__) {
      jest.useRealTimers();
      console.log = originalConsoleLog;
      jest.useRealTimers();
    }
    console.error = originalConsoleError;
    jest.clearAllMocks();
  });

  describe('Enhanced WebSocket Features', () => {
    it('should handle null URL gracefully', async () => {
      const { result } = renderHook(() => useWebSocketEnhanced(null));

      await act(async () => {
        jest.advanceTimersByTime(100);
      });

      expect(result.current.isConnected).toBe(false);
      if (__DEV__) {
        expect(console.warn).toHaveBeenCalledWith('No WebSocket URL provided');
      }
    });

    it('should track last message correctly', async () => {
      const testUrl = 'ws://localhost:8000/enhanced/';

      const { result } = renderHook(() => useWebSocketEnhanced(testUrl));

      // Wait for connection
      await act(async () => {
        jest.advanceTimersByTime(20);
      });

      // Send a test message
      const testMessage = JSON.stringify({ type: 'test', data: 'hello' });
      act(() => {
        mockWebSocket.triggerMessage(testMessage);
      });

      expect(result.current.lastMessage).toBe(testMessage);
    });

    it('should support both string and object message sending', async () => {
      const mockSend = jest.spyOn(mockWebSocket, 'send');
      const testUrl = 'ws://localhost:8000/enhanced/';

      const { result } = renderHook(() => useWebSocketEnhanced(testUrl));

      // Wait for connection
      await act(async () => {
        jest.advanceTimersByTime(20);
      });

      // Send string message
      act(() => {
        result.current.sendMessage('string message');
      });

      expect(mockSend).toHaveBeenCalledWith('string message');

      // Send object message
      const objectMessage = { type: 'test', data: 'hello' };
      act(() => {
        result.current.sendMessage(objectMessage);
      });

      expect(mockSend).toHaveBeenCalledWith(JSON.stringify(objectMessage));
    });

    it('should respect shouldReconnect option', async () => {
      const reconnectionAttempts: number[] = [];

      // Mock setTimeout to track attempts
      const originalSetTimeout = global.setTimeout;
      global.setTimeout = jest.fn((callback, delay) => {
        reconnectionAttempts.push(delay);
        return originalSetTimeout(callback, 0); // Execute immediately
      }) as any;

      const testUrl = 'ws://localhost:8000/enhanced/';

      const { result } = renderHook(() =>
        useWebSocketEnhanced(testUrl, {
          shouldReconnect: false,
        }),
      );

      // Wait for connection
      await act(async () => {
        jest.advanceTimersByTime(20);
      });

      // Simulate unexpected disconnection
      await act(async () => {
        mockWebSocket.triggerClose(WebSocketErrorCodes.ABNORMAL_CLOSURE);
        jest.runAllTimers();
      });

      // Should not attempt reconnection
      expect(reconnectionAttempts).toHaveLength(0);

      global.setTimeout = originalSetTimeout;
    });
  });

  describe('Memory Leak Prevention', () => {
    it('should clean up timers on unmount', async () => {
      const testUrl = 'ws://localhost:8000/memory-test/';

      const { result, unmount } = renderHook(() => useWebSocketEnhanced(testUrl));

      // Wait for connection
      await act(async () => {
        jest.advanceTimersByTime(20);
      });

      // Simulate disconnection to trigger reconnection timer
      await act(async () => {
        mockWebSocket.triggerClose(WebSocketErrorCodes.ABNORMAL_CLOSURE);
      });

      // Unmount before reconnection
      act(() => {
        unmount();
      });

      // Verify cleanup - component should unmount without errors
      expect(mockWebSocket.close).toHaveBeenCalled();
    });

    it('should clean up event listeners properly', async () => {
      const testUrl = 'ws://localhost:8000/listeners-test/';

      const { result, unmount } = renderHook(() =>
        useWebSocketEnhanced(testUrl, {
          onOpen: jest.fn(),
          onClose: jest.fn(),
          onError: jest.fn(),
        }),
      );

      // Wait for connection
      await act(async () => {
        jest.advanceTimersByTime(20);
      });

      // Unmount
      act(() => {
        unmount();
      });

      // Component should unmount without errors
      expect(mockWebSocket.close).toHaveBeenCalled();
    });
  });

  describe('Performance', () => {
    it('should complete connection within reasonable time', async () => {
      const startTime = Date.now();
      const testUrl = 'ws://localhost:8000/performance/';

      const { result } = renderHook(() => useWebSocketEnhanced(testUrl));

      await act(async () => {
        jest.advanceTimersByTime(20);
      });

      const connectionTime = Date.now() - startTime;

      expect(result.current.isConnected).toBe(true);
      expect(connectionTime).toBeLessThan(100); // Should connect quickly in test environment
    });

    it('should handle rapid message sending without blocking', async () => {
      const testUrl = 'ws://localhost:8000/rapid/';
      const mockSend = jest.spyOn(mockWebSocket, 'send');

      const { result } = renderHook(() => useWebSocketEnhanced(testUrl));

      // Wait for connection
      await act(async () => {
        jest.advanceTimersByTime(20);
      });

      // Send multiple messages rapidly
      const messageCount = 100;
      act(() => {
        for (let i = 0; i < messageCount; i++) {
          result.current.sendMessage({ type: 'rapid_test', sequence: i });
        }
      });

      expect(mockSend).toHaveBeenCalledTimes(messageCount);
    });
  });
});
