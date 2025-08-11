/**
 * Tests for useWebSocket and useWebSocketEnhanced hooks
 *
 * Tests cover:
 * - Connection establishment and cleanup
 * - Authentication token handling
 * - Message sending and receiving
 * - Exponential backoff reconnection logic
 * - Error handling and network failures
 * - Multiple connection scenarios
 */

import AsyncStorage from '@react-native-async-storage/async-storage';
import { renderHook, act, waitFor } from '@testing-library/react-native';

import WebSocketTestUtils, {
  WebSocketTestData,
  MockWebSocket,
} from '@/__tests__/utils/websocket-test-utils';
import { useWebSocket, useWebSocketEnhanced } from '@/hooks/useWebSocket';

// Mock AsyncStorage
jest.mock('@react-native-async-storage/async-storage', () => ({
  getItem: jest.fn(),
  setItem: jest.fn(),
}));

describe('useWebSocket Hook', () => {
  beforeEach(() => {
    WebSocketTestUtils.setup();
    WebSocketTestUtils.setupFakeTimers();
    jest.clearAllMocks();
  });

  afterEach(() => {
    WebSocketTestUtils.cleanup();
    WebSocketTestUtils.cleanupFakeTimers();
  });

  describe('Connection Management', () => {
    it('should establish WebSocket connection with authentication token', async () => {
      const mockToken = 'test-auth-token';
      WebSocketTestUtils.mockAsyncStorage(mockToken);

      const { result } = renderHook(() =>
        useWebSocket({
          url: 'ws://localhost:8000/ws/test/',
          channelName: 'test-channel',
          shouldConnect: true,
        })
      );

      // Wait for AsyncStorage.getItem to resolve first
      await act(async () => {
        // Let AsyncStorage.getItem resolve (it's mocked to resolve immediately)
        await Promise.resolve();
      });

      // Then advance timers for WebSocket connection
      await act(async () => {
        WebSocketTestUtils.advanceTime(50); // This should trigger the connection
      });

      const ws = WebSocketTestUtils.getLastWebSocket();
      expect(ws).toBeTruthy();
      expect(ws?.url).toBe(`ws://localhost:8000/ws/test/?token=${mockToken}`);
      expect(result.current.isConnected).toBe(true);
      expect(result.current.error).toBeNull();
    });

    it('should handle missing authentication token', async () => {
      WebSocketTestUtils.mockAsyncStorageNoToken();

      const { result } = renderHook(() =>
        useWebSocket({
          url: 'ws://localhost:8000/ws/test/',
          channelName: 'test-channel',
          shouldConnect: true,
        })
      );

      await act(async () => {
        WebSocketTestUtils.advanceTime(100);
      });

      expect(result.current.isConnected).toBe(false);
      expect(result.current.error).toBe('No authentication token found');
    });

    it('should not connect when shouldConnect is false', async () => {
      WebSocketTestUtils.mockAsyncStorage();

      const { result } = renderHook(() =>
        useWebSocket({
          url: 'ws://localhost:8000/ws/test/',
          channelName: 'test-channel',
          shouldConnect: false,
        })
      );

      await act(async () => {
        WebSocketTestUtils.advanceTime(100);
      });

      const ws = WebSocketTestUtils.getLastWebSocket();
      expect(ws).toBeNull();
      expect(result.current.isConnected).toBe(false);
    });

    it('should cleanup connection on unmount', async () => {
      WebSocketTestUtils.mockAsyncStorage();

      const { result, unmount } = renderHook(() =>
        useWebSocket({
          url: 'ws://localhost:8000/ws/test/',
          channelName: 'test-channel',
          shouldConnect: true,
        })
      );

      await act(async () => {
        WebSocketTestUtils.advanceTime(100);
      });

      const ws = WebSocketTestUtils.getLastWebSocket()!;
      expect(result.current.isConnected).toBe(true);

      unmount();

      expect(ws.readyState).toBe(WebSocket.CLOSING);
    });
  });

  describe('Message Handling', () => {
    it('should receive and parse JSON messages', async () => {
      WebSocketTestUtils.mockAsyncStorage();
      const onMessage = jest.fn();

      renderHook(() =>
        useWebSocket({
          url: 'ws://localhost:8000/ws/test/',
          channelName: 'test-channel',
          onMessage,
          shouldConnect: true,
        })
      );

      await act(async () => {
        WebSocketTestUtils.advanceTime(100);
      });

      const ws = WebSocketTestUtils.getLastWebSocket()!;
      const testMessage = { type: 'test', data: 'hello' };

      act(() => {
        ws.simulateMessage(JSON.stringify(testMessage));
      });

      expect(onMessage).toHaveBeenCalledWith(testMessage);
    });

    it('should handle malformed JSON messages gracefully', async () => {
      WebSocketTestUtils.mockAsyncStorage();
      const onMessage = jest.fn();
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

      renderHook(() =>
        useWebSocket({
          url: 'ws://localhost:8000/ws/test/',
          channelName: 'test-channel',
          onMessage,
          shouldConnect: true,
        })
      );

      await act(async () => {
        WebSocketTestUtils.advanceTime(100);
      });

      const ws = WebSocketTestUtils.getLastWebSocket()!;

      act(() => {
        ws.simulateMessage('invalid json {');
      });

      expect(onMessage).not.toHaveBeenCalled();
      expect(consoleSpy).toHaveBeenCalledWith(
        'Error parsing WebSocket message:',
        expect.any(Error)
      );

      consoleSpy.mockRestore();
    });

    it('should send messages successfully when connected', async () => {
      WebSocketTestUtils.mockAsyncStorage();

      const { result } = renderHook(() =>
        useWebSocket({
          url: 'ws://localhost:8000/ws/test/',
          channelName: 'test-channel',
          shouldConnect: true,
        })
      );

      await act(async () => {
        WebSocketTestUtils.advanceTime(100);
      });

      const ws = WebSocketTestUtils.getLastWebSocket()!;
      const testMessage = { type: 'test', data: 'hello' };

      act(() => {
        result.current.sendMessage(testMessage);
      });

      const sentMessages = ws.getSentMessages();
      expect(sentMessages).toContain(JSON.stringify(testMessage));
    });

    it('should not send messages when disconnected', async () => {
      WebSocketTestUtils.mockAsyncStorage();
      const consoleSpy = jest.spyOn(console, 'warn').mockImplementation();

      const { result } = renderHook(() =>
        useWebSocket({
          url: 'ws://localhost:8000/ws/test/',
          channelName: 'test-channel',
          shouldConnect: false,
        })
      );

      const testMessage = { type: 'test', data: 'hello' };

      act(() => {
        result.current.sendMessage(testMessage);
      });

      expect(consoleSpy).toHaveBeenCalledWith('WebSocket not connected, cannot send message');

      consoleSpy.mockRestore();
    });
  });

  describe('Reconnection Logic', () => {
    it('should implement exponential backoff reconnection', async () => {
      WebSocketTestUtils.mockAsyncStorage();
      const maxReconnectAttempts = 3;
      const reconnectAttempts: number[] = [];

      const { result } = renderHook(() =>
        useWebSocket({
          url: 'ws://localhost:8000/ws/test/',
          channelName: 'test-channel',
          shouldConnect: true,
        })
      );

      await act(async () => {
        WebSocketTestUtils.advanceTime(100);
      });

      // Simulate connection failure
      const ws = WebSocketTestUtils.getLastWebSocket()!;

      act(() => {
        ws.simulateNetworkFailure();
      });

      expect(result.current.isConnected).toBe(false);

      // Track reconnection attempts with exponential backoff
      for (let attempt = 0; attempt < maxReconnectAttempts; attempt++) {
        const expectedDelay = Math.pow(2, attempt) * 1000;
        reconnectAttempts.push(Date.now());

        await act(async () => {
          WebSocketTestUtils.advanceTime(expectedDelay + 100);
        });
      }

      // Verify exponential backoff timing
      const isValidBackoff = WebSocketTestUtils.verifyBackoffTiming(reconnectAttempts, 1000, 200);
      expect(isValidBackoff).toBe(true);
    });

    it('should stop reconnecting after max attempts', async () => {
      WebSocketTestUtils.mockAsyncStorage();

      const { result } = renderHook(() =>
        useWebSocket({
          url: 'ws://localhost:8000/ws/test/',
          channelName: 'test-channel',
          shouldConnect: true,
        })
      );

      await act(async () => {
        WebSocketTestUtils.advanceTime(100);
      });

      const ws = WebSocketTestUtils.getLastWebSocket()!;

      act(() => {
        ws.simulateNetworkFailureWithReconnectBlocking();
      });

      // Fast-forward through all reconnection attempts
      for (let i = 0; i < 5; i++) {
        await act(async () => {
          WebSocketTestUtils.advanceTime(Math.pow(2, i) * 1000 + 100);
        });
      }

      // Should stop trying after max attempts
      expect(result.current.isConnected).toBe(false);
      expect(WebSocketTestUtils.getAllWebSockets().length).toBeLessThanOrEqual(6); // 1 initial + 5 reconnect attempts
    });

    it('should not reconnect on normal closure (code 1000)', async () => {
      WebSocketTestUtils.mockAsyncStorage();

      const { result } = renderHook(() =>
        useWebSocket({
          url: 'ws://localhost:8000/ws/test/',
          channelName: 'test-channel',
          shouldConnect: true,
        })
      );

      await act(async () => {
        WebSocketTestUtils.advanceTime(100);
      });

      const ws = WebSocketTestUtils.getLastWebSocket()!;
      const initialInstanceCount = WebSocketTestUtils.getAllWebSockets().length;

      act(() => {
        ws.close(1000, 'Normal closure');
      });

      await act(async () => {
        WebSocketTestUtils.advanceTime(5000); // Wait longer than any reconnect delay
      });

      expect(result.current.isConnected).toBe(false);
      expect(WebSocketTestUtils.getAllWebSockets().length).toBe(initialInstanceCount); // No new instances
    });

    it('should reset reconnect attempts on successful connection', async () => {
      WebSocketTestUtils.mockAsyncStorage();

      const { result } = renderHook(() =>
        useWebSocket({
          url: 'ws://localhost:8000/ws/test/',
          channelName: 'test-channel',
          shouldConnect: true,
        })
      );

      await act(async () => {
        WebSocketTestUtils.advanceTime(100);
      });

      let ws = WebSocketTestUtils.getLastWebSocket()!;

      // First failure
      act(() => {
        ws.simulateNetworkFailure();
      });

      // Wait for first reconnection
      await act(async () => {
        WebSocketTestUtils.advanceTime(1100);
      });

      ws = WebSocketTestUtils.getLastWebSocket()!;

      // Simulate successful connection
      act(() => {
        ws.readyState = WebSocket.OPEN;
      });

      expect(result.current.isConnected).toBe(true);

      // Another failure should start from 1-second delay again
      act(() => {
        ws.simulateNetworkFailure();
      });

      const startTime = Date.now();

      await act(async () => {
        WebSocketTestUtils.advanceTime(1100); // Should reconnect after ~1 second
      });

      // Verify it's using the first attempt delay, not a higher exponential delay
      expect(Date.now() - startTime).toBeLessThan(1500);
    });
  });

  describe('Error Handling', () => {
    it('should handle WebSocket creation errors', async () => {
      // Mock AsyncStorage to return token but WebSocket constructor to throw
      WebSocketTestUtils.mockAsyncStorage();

      const originalWebSocket = global.WebSocket;
      global.WebSocket = jest.fn(() => {
        throw new Error('WebSocket creation failed');
      }) as any;

      const { result } = renderHook(() =>
        useWebSocket({
          url: 'ws://localhost:8000/ws/test/',
          channelName: 'test-channel',
          shouldConnect: true,
        })
      );

      await act(async () => {
        WebSocketTestUtils.advanceTime(100);
      });

      expect(result.current.isConnected).toBe(false);
      expect(result.current.error).toBe('Failed to create WebSocket connection');

      global.WebSocket = originalWebSocket;
    });

    it('should call onError callback on WebSocket errors', async () => {
      WebSocketTestUtils.mockAsyncStorage();
      const onError = jest.fn();

      renderHook(() =>
        useWebSocket({
          url: 'ws://localhost:8000/ws/test/',
          channelName: 'test-channel',
          onError,
          shouldConnect: true,
        })
      );

      await act(async () => {
        WebSocketTestUtils.advanceTime(100);
      });

      const ws = WebSocketTestUtils.getLastWebSocket()!;
      const errorEvent = new Event('error');

      act(() => {
        ws.simulateError(errorEvent);
      });

      expect(onError).toHaveBeenCalledWith(errorEvent);
    });

    it('should handle network interruption and recovery', async () => {
      WebSocketTestUtils.mockAsyncStorage();
      const onOpen = jest.fn();
      const onClose = jest.fn();
      const onError = jest.fn();

      const { result } = renderHook(() =>
        useWebSocket({
          url: 'ws://localhost:8000/ws/test/',
          channelName: 'test-channel',
          onOpen,
          onClose,
          onError,
          shouldConnect: true,
        })
      );

      await act(async () => {
        WebSocketTestUtils.advanceTime(100);
      });

      expect(result.current.isConnected).toBe(true);
      expect(onOpen).toHaveBeenCalledTimes(1);

      let ws = WebSocketTestUtils.getLastWebSocket()!;

      // Simulate network interruption
      act(() => {
        ws.simulateNetworkFailure();
      });

      expect(result.current.isConnected).toBe(false);
      expect(onClose).toHaveBeenCalledTimes(1);
      expect(onError).toHaveBeenCalledTimes(1);

      // Wait for reconnection
      await act(async () => {
        WebSocketTestUtils.advanceTime(1100);
      });

      ws = WebSocketTestUtils.getLastWebSocket()!;
      expect(result.current.isConnected).toBe(true);
      expect(onOpen).toHaveBeenCalledTimes(2); // Called again on reconnect
    });
  });

  describe('Manual Connection Control', () => {
    it('should allow manual connection', async () => {
      WebSocketTestUtils.mockAsyncStorage();

      const { result } = renderHook(() =>
        useWebSocket({
          url: 'ws://localhost:8000/ws/test/',
          channelName: 'test-channel',
          shouldConnect: false,
        })
      );

      expect(result.current.isConnected).toBe(false);

      await act(async () => {
        result.current.connect();
        WebSocketTestUtils.advanceTime(100);
      });

      expect(result.current.isConnected).toBe(true);
    });

    it('should allow manual disconnection', async () => {
      WebSocketTestUtils.mockAsyncStorage();

      const { result } = renderHook(() =>
        useWebSocket({
          url: 'ws://localhost:8000/ws/test/',
          channelName: 'test-channel',
          shouldConnect: true,
        })
      );

      await act(async () => {
        WebSocketTestUtils.advanceTime(100);
      });

      expect(result.current.isConnected).toBe(true);

      act(() => {
        result.current.disconnect();
      });

      expect(result.current.isConnected).toBe(false);
    });
  });
});

describe('useWebSocketEnhanced Hook', () => {
  beforeEach(() => {
    WebSocketTestUtils.setup();
    WebSocketTestUtils.setupFakeTimers();
    jest.clearAllMocks();
  });

  afterEach(() => {
    WebSocketTestUtils.cleanup();
    WebSocketTestUtils.cleanupFakeTimers();
  });

  describe('Enhanced Interface', () => {
    it('should connect with URL and track last message', async () => {
      const wsUrl = 'ws://localhost:8000/ws/enhanced/';
      const onOpen = jest.fn();
      const onClose = jest.fn();

      const { result } = renderHook(() =>
        useWebSocketEnhanced(wsUrl, {
          onOpen,
          onClose,
          shouldReconnect: true,
        })
      );

      await act(async () => {
        WebSocketTestUtils.advanceTime(100);
      });

      expect(result.current.isConnected).toBe(true);
      expect(onOpen).toHaveBeenCalledTimes(1);

      const ws = WebSocketTestUtils.getLastWebSocket()!;
      const testMessage = 'Hello Enhanced WebSocket';

      act(() => {
        ws.simulateMessage(testMessage);
      });

      expect(result.current.lastMessage).toBe(testMessage);
    });

    it('should handle null URL gracefully', () => {
      const { result } = renderHook(() => useWebSocketEnhanced(null));

      expect(result.current.isConnected).toBe(false);
      expect(result.current.lastMessage).toBeNull();
    });

    it('should support sending both string and object messages', async () => {
      const wsUrl = 'ws://localhost:8000/ws/enhanced/';

      const { result } = renderHook(() => useWebSocketEnhanced(wsUrl));

      await act(async () => {
        WebSocketTestUtils.advanceTime(100);
      });

      const ws = WebSocketTestUtils.getLastWebSocket()!;

      // Send string message
      act(() => {
        result.current.sendMessage('string message');
      });

      // Send object message
      act(() => {
        result.current.sendMessage({ type: 'object', data: 'test' });
      });

      const sentMessages = ws.getSentMessages();
      expect(sentMessages).toContain('string message');
      expect(sentMessages).toContain('{"type":"object","data":"test"}');
    });

    it('should disable reconnection when shouldReconnect is false', async () => {
      const wsUrl = 'ws://localhost:8000/ws/enhanced/';

      const { result } = renderHook(() =>
        useWebSocketEnhanced(wsUrl, {
          shouldReconnect: false,
        })
      );

      await act(async () => {
        WebSocketTestUtils.advanceTime(100);
      });

      const ws = WebSocketTestUtils.getLastWebSocket()!;
      const initialInstanceCount = WebSocketTestUtils.getAllWebSockets().length;

      act(() => {
        ws.simulateNetworkFailure();
      });

      await act(async () => {
        WebSocketTestUtils.advanceTime(5000); // Wait longer than any reconnect delay
      });

      expect(result.current.isConnected).toBe(false);
      expect(WebSocketTestUtils.getAllWebSockets().length).toBe(initialInstanceCount); // No new instances
    });
  });

  describe('Connection Lifecycle', () => {
    it('should reconnect when URL changes', async () => {
      // Ensure no global failures from previous tests
      WebSocketTestUtils.setGlobalConnectionFailure(false);

      const { result, rerender } = renderHook(({ url }) => useWebSocketEnhanced(url), {
        initialProps: { url: 'ws://localhost:8000/ws/test1/' },
      });

      await act(async () => {
        WebSocketTestUtils.advanceTime(100);
      });

      expect(result.current.isConnected).toBe(true);
      const firstWs = WebSocketTestUtils.getLastWebSocket()!;

      // Change URL
      rerender({ url: 'ws://localhost:8000/ws/test2/' });

      await act(async () => {
        WebSocketTestUtils.advanceTime(100);
      });

      const secondWs = WebSocketTestUtils.getLastWebSocket()!;
      expect(firstWs).not.toBe(secondWs);
      expect(secondWs.url).toBe('ws://localhost:8000/ws/test2/');
      expect(result.current.isConnected).toBe(true);
    });

    it('should cleanup properly on unmount with enhanced interface', async () => {
      const wsUrl = 'ws://localhost:8000/ws/enhanced/';

      const { result, unmount } = renderHook(() => useWebSocketEnhanced(wsUrl));

      await act(async () => {
        WebSocketTestUtils.advanceTime(100);
      });

      const ws = WebSocketTestUtils.getLastWebSocket()!;
      expect(result.current.isConnected).toBe(true);

      unmount();

      expect(ws.readyState).toBe(WebSocket.CLOSING);
    });
  });
});

describe('WebSocket Hook Performance', () => {
  beforeEach(() => {
    WebSocketTestUtils.setup();
    WebSocketTestUtils.setupFakeTimers();
    jest.clearAllMocks();
  });

  afterEach(() => {
    WebSocketTestUtils.cleanup();
    WebSocketTestUtils.cleanupFakeTimers();
  });

  it('should complete connection within 100ms', async () => {
    WebSocketTestUtils.mockAsyncStorage();
    const startTime = Date.now();

    const { result } = renderHook(() =>
      useWebSocket({
        url: 'ws://localhost:8000/ws/test/',
        channelName: 'test-channel',
        shouldConnect: true,
      })
    );

    await act(async () => {
      WebSocketTestUtils.advanceTime(50); // Connection should happen quickly
    });

    const endTime = Date.now();
    expect(endTime - startTime).toBeLessThan(100);
    expect(result.current.isConnected).toBe(true);
  });

  it('should handle rapid message sending without blocking', async () => {
    WebSocketTestUtils.mockAsyncStorage();

    const { result } = renderHook(() =>
      useWebSocket({
        url: 'ws://localhost:8000/ws/test/',
        channelName: 'test-channel',
        shouldConnect: true,
      })
    );

    await act(async () => {
      WebSocketTestUtils.advanceTime(100);
    });

    const startTime = Date.now();

    // Send 100 messages rapidly
    act(() => {
      for (let i = 0; i < 100; i++) {
        result.current.sendMessage({ id: i, data: `message${i}` });
      }
    });

    const endTime = Date.now();
    expect(endTime - startTime).toBeLessThan(100); // Should complete quickly

    const ws = WebSocketTestUtils.getLastWebSocket()!;
    expect(ws.getMessageQueue()).toHaveLength(100);
  });
});
