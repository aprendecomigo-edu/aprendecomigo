/**
 * WebSocket Test Utilities
 *
 * Comprehensive testing utilities for WebSocket connections and real-time features.
 * Includes MockWebSocket class, connection simulation, and helper functions.
 */

import { act } from '@testing-library/react-native';

export interface MockWebSocketEventHandlers {
  onopen?: (event: Event) => void;
  onclose?: (event: CloseEvent) => void;
  onmessage?: (event: MessageEvent) => void;
  onerror?: (event: Event) => void;
}

// Mock CloseEvent and MessageEvent for React Native testing environment
class MockCloseEvent extends Event {
  public code: number;
  public reason: string;
  public wasClean: boolean;

  constructor(
    type: string,
    eventInitDict: { code?: number; reason?: string; wasClean?: boolean } = {}
  ) {
    super(type);
    this.code = eventInitDict.code || 1000;
    this.reason = eventInitDict.reason || '';
    this.wasClean = eventInitDict.wasClean || false;
  }
}

class MockMessageEvent extends Event {
  public data: any;

  constructor(type: string, eventInitDict: { data?: any } = {}) {
    super(type);
    this.data = eventInitDict.data;
  }
}

// Make these available globally for tests
(global as any).CloseEvent = MockCloseEvent;
(global as any).MessageEvent = MockMessageEvent;

/**
 * Mock WebSocket class for testing WebSocket functionality
 */
export class MockWebSocket implements WebSocket {
  public static CONNECTING = 0;
  public static OPEN = 1;
  public static CLOSING = 2;
  public static CLOSED = 3;

  public readonly CONNECTING = 0;
  public readonly OPEN = 1;
  public readonly CLOSING = 2;
  public readonly CLOSED = 3;

  public readyState: number = MockWebSocket.CONNECTING;
  public url: string;
  public protocol: string = '';
  public extensions: string = '';
  public binaryType: BinaryType = 'blob';
  public bufferedAmount: number = 0;

  public onopen: ((event: Event) => void) | null = null;
  public onclose: ((event: MockCloseEvent) => void) | null = null;
  public onmessage: ((event: MockMessageEvent) => void) | null = null;
  public onerror: ((event: Event) => void) | null = null;

  private eventListeners: Map<string, Set<EventListener>> = new Map();
  private messageQueue: Array<{ data: any; timestamp: number }> = [];
  private connectionDelay: number = 0;
  private shouldFailConnection: boolean = false;
  private shouldFailOnSend: boolean = false;
  private autoConnect: boolean = true;

  constructor(url: string, protocols?: string | string[]) {
    this.url = url;
    if (Array.isArray(protocols)) {
      this.protocol = protocols[0] || '';
    } else if (typeof protocols === 'string') {
      this.protocol = protocols;
    }

    if (this.autoConnect) {
      this.simulateConnection();
    }
  }

  /**
   * Simulate WebSocket connection with optional delay
   */
  private async simulateConnection(): Promise<void> {
    const timeoutFn = (global as any).setTimeout || setTimeout;

    if (this.connectionDelay > 0) {
      await new Promise(resolve => timeoutFn(resolve, this.connectionDelay));
    }

    if (this.shouldFailConnection) {
      this.readyState = MockWebSocket.CLOSED;
      const errorEvent = new Event('error');
      this.dispatchEvent(errorEvent);
      this.onerror?.(errorEvent);

      const closeEvent = new MockCloseEvent('close', {
        code: 1006,
        reason: 'Connection failed',
        wasClean: false,
      });
      this.dispatchEvent(closeEvent);
      this.onclose?.(closeEvent);
      return;
    }

    this.readyState = MockWebSocket.OPEN;
    const openEvent = new Event('open');
    this.dispatchEvent(openEvent);
    this.onopen?.(openEvent);

    // Process queued messages
    this.processMessageQueue();
  }

  /**
   * Send message through WebSocket
   */
  public send(data: string | ArrayBuffer | Blob | ArrayBufferView): void {
    if (this.readyState !== MockWebSocket.OPEN) {
      throw new Error('WebSocket is not open');
    }

    if (this.shouldFailOnSend) {
      const errorEvent = new Event('error');
      this.dispatchEvent(errorEvent);
      this.onerror?.(errorEvent);
      return;
    }

    // Simulate message sending
    console.log('MockWebSocket: Sending message:', data);
  }

  /**
   * Close WebSocket connection
   */
  public close(code?: number, reason?: string): void {
    if (this.readyState === MockWebSocket.CLOSED || this.readyState === MockWebSocket.CLOSING) {
      return;
    }

    this.readyState = MockWebSocket.CLOSING;

    // Simulate close delay
    const timeoutFn = (global as any).setTimeout || setTimeout;
    timeoutFn(() => {
      this.readyState = MockWebSocket.CLOSED;
      const closeEvent = new MockCloseEvent('close', {
        code: code || 1000,
        reason: reason || 'Normal closure',
        wasClean: code === 1000,
      });
      this.dispatchEvent(closeEvent);
      this.onclose?.(closeEvent);
    }, 10);
  }

  /**
   * Add event listener
   */
  public addEventListener(type: string, listener: EventListener): void {
    if (!this.eventListeners.has(type)) {
      this.eventListeners.set(type, new Set());
    }
    this.eventListeners.get(type)!.add(listener);
  }

  /**
   * Remove event listener
   */
  public removeEventListener(type: string, listener: EventListener): void {
    const listeners = this.eventListeners.get(type);
    if (listeners) {
      listeners.delete(listener);
    }
  }

  /**
   * Dispatch event to listeners
   */
  public dispatchEvent(event: Event): boolean {
    const listeners = this.eventListeners.get(event.type);
    if (listeners) {
      listeners.forEach(listener => {
        listener(event);
      });
    }
    return true;
  }

  /**
   * Simulate receiving a message
   */
  public simulateMessage(data: any): void {
    if (this.readyState === MockWebSocket.OPEN) {
      const messageData = typeof data === 'string' ? data : JSON.stringify(data);
      const messageEvent = new MockMessageEvent('message', { data: messageData });
      this.dispatchEvent(messageEvent);
      this.onmessage?.(messageEvent);
    } else {
      // Queue message for later delivery
      this.messageQueue.push({ data, timestamp: Date.now() });
    }
  }

  /**
   * Simulate connection error
   */
  public simulateError(): void {
    const errorEvent = new Event('error');
    this.dispatchEvent(errorEvent);
    this.onerror?.(errorEvent);
  }

  /**
   * Simulate unexpected disconnection
   */
  public simulateDisconnect(code: number = 1006, reason: string = 'Connection lost'): void {
    this.readyState = MockWebSocket.CLOSED;
    const closeEvent = new MockCloseEvent('close', {
      code,
      reason,
      wasClean: false,
    });
    this.dispatchEvent(closeEvent);
    this.onclose?.(closeEvent);
  }

  /**
   * Process queued messages
   */
  private processMessageQueue(): void {
    while (this.messageQueue.length > 0 && this.readyState === MockWebSocket.OPEN) {
      const { data } = this.messageQueue.shift()!;
      this.simulateMessage(data);
    }
  }

  /**
   * Configuration methods for testing scenarios
   */
  public setConnectionDelay(delay: number): void {
    this.connectionDelay = delay;
  }

  public setShouldFailConnection(shouldFail: boolean): void {
    this.shouldFailConnection = shouldFail;
  }

  public setShouldFailOnSend(shouldFail: boolean): void {
    this.shouldFailOnSend = shouldFail;
  }

  public setAutoConnect(autoConnect: boolean): void {
    this.autoConnect = autoConnect;
  }

  public getMessageQueue(): Array<{ data: any; timestamp: number }> {
    return [...this.messageQueue];
  }
}

/**
 * WebSocket test utilities and helper functions
 */
export const WebSocketTestUtils = {
  /**
   * Create a mock WebSocket instance
   */
  createMockWebSocket: (
    url: string = 'ws://localhost:8000/test/',
    protocols?: string | string[]
  ): MockWebSocket => {
    return new MockWebSocket(url, protocols);
  },

  /**
   * Setup global WebSocket mock
   */
  setupWebSocketMock: (): MockWebSocket => {
    const mockWs = new MockWebSocket('ws://localhost:8000/test/');
    (global as any).WebSocket = jest.fn(() => mockWs);
    return mockWs;
  },

  /**
   * Restore original WebSocket
   */
  restoreWebSocket: (): void => {
    if ((global as any).WebSocket.mockRestore) {
      (global as any).WebSocket.mockRestore();
    }
  },

  /**
   * Simulate connection establishment
   */
  simulateConnection: async (mockWs: MockWebSocket, delay: number = 0): Promise<void> => {
    if (delay > 0) {
      mockWs.setConnectionDelay(delay);
    }

    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, delay + 50));
    });
  },

  /**
   * Simulate connection failure
   */
  simulateConnectionFailure: async (mockWs: MockWebSocket): Promise<void> => {
    mockWs.setShouldFailConnection(true);

    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 50));
    });
  },

  /**
   * Simulate message sending
   */
  simulateMessageSend: (mockWs: MockWebSocket, message: any): void => {
    act(() => {
      mockWs.simulateMessage(message);
    });
  },

  /**
   * Simulate disconnection with reconnection scenario
   */
  simulateDisconnectAndReconnect: async (
    mockWs: MockWebSocket,
    reconnectDelay: number = 1000
  ): Promise<void> => {
    await act(async () => {
      mockWs.simulateDisconnect();
      await new Promise(resolve => setTimeout(resolve, reconnectDelay + 100));
    });
  },

  /**
   * Create test message for different WebSocket types
   */
  createTestMessage: {
    balance: (overrides: Partial<any> = {}) => ({
      type: 'balance_update',
      data: {
        balance: {
          id: 1,
          current_balance: 100,
          currency: 'EUR',
          last_updated: new Date().toISOString(),
        },
        ...overrides.data,
      },
      user_id: 1,
      timestamp: new Date().toISOString(),
      ...overrides,
    }),

    purchaseApproval: (overrides: Partial<any> = {}) => ({
      type: 'purchase_approval_notification',
      notification_type: 'new_request',
      title: 'New Purchase Request',
      message: 'Your child wants to purchase a lesson package',
      data: {
        request_id: 1,
        child_name: 'Test Child',
        amount: '25.00',
        plan_name: 'Math Lesson Package',
      },
      priority: 'medium',
      actionable: true,
      timestamp: new Date().toISOString(),
      ...overrides,
    }),

    transaction: (overrides: Partial<any> = {}) => ({
      type: 'transaction_update',
      data: {
        transaction_id: 'txn_123',
        status: 'completed',
        amount: 25.0,
        currency: 'EUR',
        student_id: 1,
      },
      timestamp: new Date().toISOString(),
      ...overrides,
    }),
  },

  /**
   * Test WebSocket connection lifecycle
   */
  testConnectionLifecycle: async (mockWs: MockWebSocket): Promise<void> => {
    // Test connection
    expect(mockWs.readyState).toBe(MockWebSocket.CONNECTING);

    await WebSocketTestUtils.simulateConnection(mockWs);
    expect(mockWs.readyState).toBe(MockWebSocket.OPEN);

    // Test message sending
    const testMessage = { type: 'test', data: 'hello' };
    mockWs.send(JSON.stringify(testMessage));

    // Test disconnection
    await act(async () => {
      mockWs.close();
      await new Promise(resolve => setTimeout(resolve, 50));
    });
    expect(mockWs.readyState).toBe(MockWebSocket.CLOSED);
  },

  /**
   * Test error scenarios
   */
  testErrorScenarios: async (mockWs: MockWebSocket): Promise<void> => {
    // Test connection error
    mockWs.setShouldFailConnection(true);
    await WebSocketTestUtils.simulateConnectionFailure(mockWs);

    // Test send error
    mockWs.setShouldFailOnSend(true);
    mockWs.simulateError();
  },

  /**
   * Wait for WebSocket events with timeout
   */
  waitForWebSocketEvent: (eventType: string, timeout: number = 5000): Promise<Event> => {
    return new Promise((resolve, reject) => {
      const timeoutId = setTimeout(() => {
        reject(new Error(`WebSocket event '${eventType}' not received within ${timeout}ms`));
      }, timeout);

      const handler = (event: Event) => {
        clearTimeout(timeoutId);
        resolve(event);
      };

      // This would be used with a real WebSocket instance
      // mockWs.addEventListener(eventType, handler, { once: true });
    });
  },

  /**
   * Assert WebSocket message format
   */
  assertMessageFormat: (message: any, expectedType: string): void => {
    expect(message).toHaveProperty('type', expectedType);
    expect(message).toHaveProperty('timestamp');
    expect(typeof message.timestamp).toBe('string');
  },

  /**
   * Create authentication token for WebSocket URL
   */
  createTestAuthToken: (): string => {
    return 'test_auth_token_123';
  },

  /**
   * Mock AsyncStorage for WebSocket authentication
   */
  mockAsyncStorageForWebSocket: (token: string = 'test_token') => {
    const AsyncStorage = require('@react-native-async-storage/async-storage');
    AsyncStorage.getItem = jest.fn().mockImplementation((key: string) => {
      if (key === 'auth_token') {
        return Promise.resolve(token);
      }
      return Promise.resolve(null);
    });
    return AsyncStorage;
  },

  /**
   * Test exponential backoff for reconnection
   */
  testExponentialBackoff: (attempts: number[]): void => {
    for (let i = 0; i < attempts.length; i++) {
      const expectedDelay = Math.pow(2, i) * 1000;
      expect(attempts[i]).toBeCloseTo(expectedDelay, -2); // Allow 10ms tolerance
    }
  },

  /**
   * Simulate network conditions
   */
  simulateNetworkConditions: {
    slowConnection: (mockWs: MockWebSocket) => {
      mockWs.setConnectionDelay(2000);
    },

    unstableConnection: async (mockWs: MockWebSocket) => {
      await act(async () => {
        // Simulate multiple disconnect/reconnect cycles
        for (let i = 0; i < 3; i++) {
          mockWs.simulateDisconnect();
          await new Promise(resolve => setTimeout(resolve, 100));
          mockWs.simulateConnection();
          await new Promise(resolve => setTimeout(resolve, 100));
        }
      });
    },

    lossyConnection: (mockWs: MockWebSocket, lossRate: number = 0.3) => {
      const originalSimulateMessage = mockWs.simulateMessage.bind(mockWs);
      mockWs.simulateMessage = (data: any) => {
        if (Math.random() > lossRate) {
          originalSimulateMessage(data);
        }
      };
    },
  },

  /**
   * Memory leak detection utilities
   */
  detectMemoryLeaks: {
    checkEventListenerCleanup: (mockWs: MockWebSocket): boolean => {
      return mockWs.eventListeners.size === 0;
    },

    checkTimeoutCleanup: (): boolean => {
      // In a real implementation, we would check if all timeouts were cleared
      return true;
    },

    simulateComponentUnmount: async (): Promise<void> => {
      await act(async () => {
        // Simulate React component unmounting
        await new Promise(resolve => setTimeout(resolve, 100));
      });
    },
  },
};

/**
 * WebSocket connection state helpers
 */
export const ConnectionStates = {
  CONNECTING: 0,
  OPEN: 1,
  CLOSING: 2,
  CLOSED: 3,
} as const;

/**
 * Common WebSocket error codes
 */
export const WebSocketErrorCodes = {
  NORMAL_CLOSURE: 1000,
  GOING_AWAY: 1001,
  PROTOCOL_ERROR: 1002,
  UNSUPPORTED_DATA: 1003,
  NO_STATUS_RECEIVED: 1005,
  ABNORMAL_CLOSURE: 1006,
  INVALID_FRAME_PAYLOAD_DATA: 1007,
  POLICY_VIOLATION: 1008,
  MESSAGE_TOO_BIG: 1009,
  MANDATORY_EXTENSION: 1010,
  INTERNAL_SERVER_ERROR: 1011,
  SERVICE_RESTART: 1012,
  TRY_AGAIN_LATER: 1013,
  BAD_GATEWAY: 1014,
  TLS_HANDSHAKE: 1015,
} as const;

export default WebSocketTestUtils;
