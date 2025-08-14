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

interface MockWebSocketOptions {
  autoOpen?: boolean;
  simulateNetworkLatency?: boolean;
  latencyMs?: number;
  failConnection?: boolean;
  connectionDelay?: number;
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

  private _onopen: ((event: Event) => void) | null = null;
  private _onclose: ((event: MockCloseEvent) => void) | null = null;
  private _onmessage: ((event: MockMessageEvent) => void) | null = null;
  private _onerror: ((event: Event) => void) | null = null;

  private pendingConnection: boolean = false;

  public get onopen() {
    return this._onopen;
  }
  public set onopen(handler: ((event: Event) => void) | null) {
    this._onopen = handler;
    this.checkPendingConnection();
  }

  public get onclose() {
    return this._onclose;
  }
  public set onclose(handler: ((event: MockCloseEvent) => void) | null) {
    this._onclose = handler;
    this.checkPendingConnection();
  }

  public get onmessage() {
    return this._onmessage;
  }
  public set onmessage(handler: ((event: MockMessageEvent) => void) | null) {
    this._onmessage = handler;
    this.checkPendingConnection();
  }

  public get onerror() {
    return this._onerror;
  }
  public set onerror(handler: ((event: Event) => void) | null) {
    this._onerror = handler;
    this.checkPendingConnection();
  }

  private eventListeners: Map<string, Set<EventListener>> = new Map();
  private messageQueue: Array<{ data: any; timestamp: number }> = [];
  private connectionDelay: number = 0;
  private shouldFailConnection: boolean = false;
  private shouldFailOnSend: boolean = false;
  private autoConnect: boolean = true;
  private options: MockWebSocketOptions;
  private isClosing = false;
  private closeCode: number | undefined;
  private closeReason: string | undefined;

  // Static registry for tracking all instances
  private static instances: MockWebSocket[] = [];
  private static lastInstance: MockWebSocket | null = null;
  private static globalShouldFailConnection: boolean = false;

  constructor(url: string, protocols?: string | string[], options: MockWebSocketOptions = {}) {
    this.url = url;
    if (Array.isArray(protocols)) {
      this.protocol = protocols[0] || '';
    } else if (typeof protocols === 'string') {
      this.protocol = protocols;
    }

    this.options = {
      autoOpen: true,
      simulateNetworkLatency: false,
      latencyMs: 100,
      failConnection: false,
      connectionDelay: 0,
      ...options,
    };

    MockWebSocket.instances.push(this);
    MockWebSocket.lastInstance = this;

    if (this.autoConnect && this.options.autoOpen) {
      this.pendingConnection = true;
    }
  }

  // Static methods for test control
  static getLastInstance(): MockWebSocket | null {
    return MockWebSocket.lastInstance;
  }

  static getAllInstances(): MockWebSocket[] {
    return MockWebSocket.instances;
  }

  static clearInstances(): void {
    MockWebSocket.instances.length = 0;
    MockWebSocket.lastInstance = null;
  }

  static resetAll(): void {
    MockWebSocket.instances.forEach(instance => {
      instance.readyState = WebSocket.CLOSED;
    });
    MockWebSocket.clearInstances();
    MockWebSocket.globalShouldFailConnection = false;
  }

  static setGlobalConnectionFailure(shouldFail: boolean): void {
    MockWebSocket.globalShouldFailConnection = shouldFail;
  }

  private checkPendingConnection(): void {
    // If we have onopen handler and a pending connection, trigger it
    if (this.pendingConnection && this._onopen) {
      this.pendingConnection = false;
      this.simulateConnection();
    }
  }

  /**
   * Simulate WebSocket connection with optional delay
   */
  private simulateConnection(): void {
    const delay = this.connectionDelay || this.options.connectionDelay || 0;

    const doConnection = () => {
      if (
        this.shouldFailConnection ||
        this.options.failConnection ||
        MockWebSocket.globalShouldFailConnection
      ) {
        this.readyState = MockWebSocket.CLOSED;
        const errorEvent = new Event('error');
        this.dispatchEvent(errorEvent);
        this._onerror?.(errorEvent);

        const closeEvent = new MockCloseEvent('close', {
          code: 1006,
          reason: 'Connection failed',
          wasClean: false,
        });
        this.dispatchEvent(closeEvent);
        this._onclose?.(closeEvent);
        return;
      }

      this.readyState = MockWebSocket.OPEN;
      const openEvent = new Event('open');
      this.dispatchEvent(openEvent);
      this._onopen?.(openEvent);
    };

    if (delay > 0) {
      setTimeout(doConnection, delay);
    } else {
      doConnection();
    }
  }

  public send(data: string | ArrayBuffer | Blob | ArrayBufferView): void {
    if (this.readyState !== MockWebSocket.OPEN) {
      if (this.shouldFailOnSend) {
        throw new Error('WebSocket is not open');
      }
      console.warn('WebSocket not connected, cannot send message');
      return;
    }

    if (this.shouldFailOnSend) {
      throw new Error('Simulated send failure');
    }

    const messageData = typeof data === 'string' ? data : JSON.stringify(data);
    this.messageQueue.push({ data: messageData, timestamp: Date.now() });

    // Simulate echo or response if needed
    if (this.options.simulateNetworkLatency) {
      setTimeout(() => {
        // Could simulate server response here
      }, this.options.latencyMs);
    }
  }

  public close(code?: number, reason?: string): void {
    if (this.readyState === MockWebSocket.CLOSED || this.readyState === MockWebSocket.CLOSING) {
      return;
    }

    this.isClosing = true;
    this.readyState = MockWebSocket.CLOSING;
    this.closeCode = code || 1000;
    this.closeReason = reason || 'Normal closure';

    // Simulate close delay
    setTimeout(() => {
      this.readyState = MockWebSocket.CLOSED;
      const closeEvent = new MockCloseEvent('close', {
        code: this.closeCode,
        reason: this.closeReason,
        wasClean: this.closeCode === 1000,
      });
      this.dispatchEvent(closeEvent);
      this._onclose?.(closeEvent);
    }, 10);
  }

  public addEventListener(type: string, listener: EventListener): void {
    if (!this.eventListeners.has(type)) {
      this.eventListeners.set(type, new Set());
    }
    this.eventListeners.get(type)!.add(listener);
  }

  public removeEventListener(type: string, listener: EventListener): void {
    const listeners = this.eventListeners.get(type);
    if (listeners) {
      listeners.delete(listener);
    }
  }

  public dispatchEvent(event: Event): boolean {
    const listeners = this.eventListeners.get(event.type);
    if (listeners) {
      listeners.forEach(listener => listener(event));
    }
    return true;
  }

  // Test helper methods
  public simulateMessage(data: any): void {
    if (this.readyState === MockWebSocket.OPEN) {
      const messageData = typeof data === 'string' ? data : JSON.stringify(data);
      const messageEvent = new MockMessageEvent('message', { data: messageData });
      this.dispatchEvent(messageEvent);
      this._onmessage?.(messageEvent);
    }
  }

  public simulateError(error?: Event): void {
    const errorEvent = error || new Event('error');
    this.dispatchEvent(errorEvent);
    this._onerror?.(errorEvent);
  }

  public simulateDisconnect(code = 1006, reason = 'Connection lost'): void {
    this.readyState = MockWebSocket.CLOSED;
    const closeEvent = new MockCloseEvent('close', {
      code,
      reason,
      wasClean: code === 1000,
    });
    this.dispatchEvent(closeEvent);
    this._onclose?.(closeEvent);
  }

  public simulateNetworkFailure(): void {
    this.readyState = MockWebSocket.CLOSED;
    this.simulateError();
    this.simulateDisconnect(1006, 'Network failure');
  }

  public simulateNetworkFailureWithReconnectBlocking(): void {
    MockWebSocket.setGlobalConnectionFailure(true);
    this.simulateNetworkFailure();
  }

  public simulateRecovery(): void {
    if (this.readyState === MockWebSocket.CLOSED) {
      this.readyState = MockWebSocket.CONNECTING;
      this.simulateConnection();
    }
  }

  // Additional test control methods
  public triggerOpen(): void {
    this.readyState = MockWebSocket.OPEN;
    const event = new Event('open');
    this.dispatchEvent(event);
    this._onopen?.(event);
  }

  public triggerClose(code = 1000, reason = 'Normal closure'): void {
    this.readyState = MockWebSocket.CLOSED;
    const event = new MockCloseEvent('close', { code, reason, wasClean: code === 1000 });
    this.dispatchEvent(event);
    this._onclose?.(event);
  }

  public triggerMessage(data: any): void {
    const messageData = typeof data === 'string' ? data : JSON.stringify(data);
    const event = new MockMessageEvent('message', { data: messageData });
    this.dispatchEvent(event);
    this._onmessage?.(event);
  }

  public triggerError(error?: Event): void {
    const event = error || new Event('error');
    this.dispatchEvent(event);
    this._onerror?.(event);
  }

  // Utility methods
  public setShouldFailConnection(shouldFail: boolean): void {
    this.shouldFailConnection = shouldFail;
  }

  public setShouldFailOnSend(shouldFail: boolean): void {
    this.shouldFailOnSend = shouldFail;
  }

  public setConnectionDelay(delay: number): void {
    this.connectionDelay = delay;
  }

  public setAutoConnect(autoConnect: boolean): void {
    this.autoConnect = autoConnect;
  }

  public getMessageQueue(): Array<{ data: any; timestamp: number }> {
    return [...this.messageQueue];
  }

  public getSentMessages(): string[] {
    return this.messageQueue.map(msg => msg.data);
  }

  public clearMessageQueue(): void {
    this.messageQueue.length = 0;
  }
}

/**
 * WebSocket test utilities and helper functions
 */
export const WebSocketTestUtils = {
  /**
   * Setup mock WebSocket for testing
   */
  setup(): void {
    (global as any).WebSocket = MockWebSocket;
    MockWebSocket.clearInstances();

    // Setup WebSocketClient mock registry
    if (!(global as any).__mockWebSocketClients) {
      (global as any).__mockWebSocketClients = [];
    }
  },

  /**
   * Cleanup mock WebSocket after testing
   */
  cleanup(): void {
    MockWebSocket.resetAll();
    MockWebSocket.setGlobalConnectionFailure(false);

    // Clear WebSocketClient registry
    if ((global as any).__mockWebSocketClients) {
      (global as any).__mockWebSocketClients.length = 0;
    }
    (global as any).__lastMockWebSocketClient = null;
    (global as any).__webSocketGlobalFailure = false;
  },

  /**
   * Create a mock WebSocket instance
   */
  createMockWebSocket: (
    url: string = 'ws://localhost:8000/test/',
    protocols?: string | string[],
    options?: MockWebSocketOptions
  ): MockWebSocket => {
    return new MockWebSocket(url, protocols, options);
  },

  /**
   * Get the most recently created WebSocket instance
   */
  getLastWebSocket(): any {
    // For the new architecture, we need to get the mock client from the hook render
    // This will be updated by the hook when it creates a client
    return (global as any).__lastMockWebSocketClient || MockWebSocket.getLastInstance();
  },

  /**
   * Get all WebSocket instances
   */
  getAllWebSockets(): any[] {
    const clients = (global as any).__mockWebSocketClients || [];
    const nativeWs = MockWebSocket.getAllInstances();
    return [...clients, ...nativeWs];
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
   * Clean up WebSocket mock
   */
  cleanupWebSocketMock: (): void => {
    (global as any).WebSocket = undefined;
    jest.clearAllMocks();
  },

  /**
   * Set global connection failure for all new WebSocket instances
   */
  setGlobalConnectionFailure: (shouldFail: boolean): void => {
    MockWebSocket.setGlobalConnectionFailure(shouldFail);
    // Also set for the new WebSocketClient mock
    (global as any).__webSocketGlobalFailure = shouldFail;
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
   * Wait for WebSocket to reach a specific state
   */
  waitForState: async (ws: MockWebSocket, state: number, timeout = 1000): Promise<void> => {
    const start = Date.now();

    return new Promise((resolve, reject) => {
      const check = () => {
        if (ws.readyState === state) {
          resolve();
        } else if (Date.now() - start > timeout) {
          reject(new Error(`WebSocket did not reach state ${state} within ${timeout}ms`));
        } else {
          setTimeout(check, 10);
        }
      };
      check();
    });
  },

  /**
   * Wait for WebSocket connection to open
   */
  waitForConnection: async (ws?: MockWebSocket, timeout = 1000): Promise<MockWebSocket> => {
    const webSocket = ws || WebSocketTestUtils.getLastWebSocket();
    if (!webSocket) {
      throw new Error('No WebSocket instance found');
    }

    await WebSocketTestUtils.waitForState(webSocket, WebSocket.OPEN, timeout);
    return webSocket;
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
          current_balance: 100.0,
          currency: 'EUR',
          last_updated: new Date().toISOString(),
        },
      },
      timestamp: new Date().toISOString(),
      ...overrides,
    }),

    purchaseApproval: (overrides: Partial<any> = {}) => ({
      type: 'purchase_approval_notification',
      notification_type: 'new_request',
      notification_id: 'approval_123',
      title: 'New Purchase Request',
      message: 'Your child wants to purchase a study package',
      data: {
        request_id: 1,
        child_name: 'Test Child',
        amount: '25.00',
        plan_name: 'Basic Package',
      },
      priority: 'high',
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
    mockWs.close();
    await new Promise(resolve => setTimeout(resolve, 50));
    expect(mockWs.readyState).toBe(MockWebSocket.CLOSED);
  },

  /**
   * Create exponential backoff delays
   */
  createExponentialBackoffDelays: (baseDelay: number, maxAttempts: number): number[] => {
    const delays: number[] = [];
    for (let i = 0; i < maxAttempts; i++) {
      delays.push(Math.min(Math.pow(2, i) * baseDelay, 30000));
    }
    return delays;
  },

  /**
   * Verify message received
   */
  expectMessageReceived: (
    mockWs: MockWebSocket,
    expectedMessage: any,
    onMessage: jest.Mock
  ): void => {
    act(() => {
      mockWs.simulateMessage(expectedMessage);
    });
    expect(onMessage).toHaveBeenCalledWith(expectedMessage);
  },

  /**
   * Test error handling
   */
  testErrorHandling: async (mockWs: MockWebSocket, onError: jest.Mock): Promise<void> => {
    await act(async () => {
      mockWs.simulateError();
    });
    expect(onError).toHaveBeenCalled();
  },

  /**
   * Mock AsyncStorage for WebSocket authentication
   */
  mockAsyncStorage: (token?: string): void => {
    const mockToken = token || 'mock-jwt-token-' + Date.now();

    const AsyncStorage = require('@react-native-async-storage/async-storage');
    AsyncStorage.getItem = jest.fn().mockResolvedValue(mockToken);
    AsyncStorage.setItem = jest.fn().mockResolvedValue(undefined);
  },

  /**
   * Mock AsyncStorage with no token (unauthenticated scenario)
   */
  mockAsyncStorageNoToken: (): void => {
    const AsyncStorage = require('@react-native-async-storage/async-storage');
    AsyncStorage.getItem = jest.fn().mockResolvedValue(null);
  },

  /**
   * Test memory cleanup
   */
  testMemoryCleanup: (mockWs: MockWebSocket): void => {
    // Check if event listeners are properly cleaned up
    const initialListenerCount = (mockWs as any).eventListeners.size;
    mockWs.close();
    const finalListenerCount = (mockWs as any).eventListeners.size;
    expect(finalListenerCount).toBeLessThanOrEqual(initialListenerCount);
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

    packetLoss: (mockWs: MockWebSocket) => {
      const originalSend = mockWs.send.bind(mockWs);
      mockWs.send = jest.fn(data => {
        // Randomly drop 20% of messages
        if (Math.random() > 0.2) {
          originalSend(data);
        }
      });
    },
  },

  /**
   * Create reconnection delay tracker
   */
  createReconnectionTracker: (): { attempts: number[]; track: () => void } => {
    const attempts: number[] = [];
    let lastAttemptTime = Date.now();

    return {
      attempts,
      track: () => {
        const now = Date.now();
        attempts.push(now - lastAttemptTime);
        lastAttemptTime = now;
      },
    };
  },

  /**
   * Setup fake timers for WebSocket testing
   */
  setupFakeTimers: (): void => {
    jest.useFakeTimers();
  },

  /**
   * Cleanup fake timers
   */
  cleanupFakeTimers: (): void => {
    jest.useRealTimers();
  },

  /**
   * Utility to advance time for testing timers
   */
  advanceTime: (ms: number): void => {
    jest.advanceTimersByTime(ms);
  },

  /**
   * Verify exponential backoff timing
   */
  verifyBackoffTiming: (
    attempts: number[],
    baseDelay: number,
    toleranceMs: number = 100
  ): boolean => {
    if (attempts.length < 2) return true;

    for (let i = 1; i < attempts.length; i++) {
      const expectedDelay = Math.pow(2, i - 1) * baseDelay;
      const actualDelay = attempts[i] - attempts[i - 1];
      const tolerance = toleranceMs;

      if (Math.abs(actualDelay - expectedDelay) > tolerance) {
        console.log(`Backoff timing verification failed at attempt ${i}:`, {
          expected: expectedDelay,
          actual: actualDelay,
          tolerance,
          difference: Math.abs(actualDelay - expectedDelay),
        });
        return false;
      }
    }
    return true;
  },
};

/**
 * Test helper for mocking push notifications
 */
export const mockPushNotifications = () => {
  const mockNotification = {
    onclick: jest.fn(),
    close: jest.fn(),
  };

  global.Notification = jest.fn().mockImplementation(() => mockNotification) as any;
  global.Notification.permission = 'granted';
  global.Notification.requestPermission = jest.fn().mockResolvedValue('granted');

  return mockNotification;
};

/**
 * Test data factories for WebSocket messages
 */
export const WebSocketTestData = {
  balanceUpdate: (userId: number, balance: number = 100) => ({
    type: 'balance_update',
    data: {
      balance: {
        id: 1,
        user_id: userId,
        current_balance: balance,
        currency: 'EUR',
        last_updated: new Date().toISOString(),
      },
    },
    user_id: userId,
    timestamp: new Date().toISOString(),
  }),

  purchaseApproval: (userId: number, requestId: number = 1) => ({
    type: 'purchase_approval_notification',
    notification_type: 'new_request',
    notification_id: `approval_${requestId}`,
    title: 'New Purchase Request',
    message: 'Your child wants to purchase a study package',
    data: {
      request_id: requestId,
      child_name: 'Test Child',
      amount: '25.00',
      plan_name: 'Basic Package',
    },
    priority: 'high',
    timestamp: new Date().toISOString(),
  }),

  transactionUpdate: (transactionId: number = 1, action: string = 'created') => ({
    type: 'transaction_update',
    data: {
      action,
      transaction: {
        id: transactionId,
        amount: 25.0,
        currency: 'EUR',
        status: 'completed',
        created_at: new Date().toISOString(),
      },
    },
    timestamp: new Date().toISOString(),
  }),
};

// WebSocket close codes
export const WebSocketErrorCodes = {
  NORMAL_CLOSURE: 1000,
  GOING_AWAY: 1001,
  PROTOCOL_ERROR: 1002,
  UNSUPPORTED_DATA: 1003,
  NO_STATUS_RECEIVED: 1005,
  ABNORMAL_CLOSURE: 1006,
  INVALID_FRAME_PAYLOAD: 1007,
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
