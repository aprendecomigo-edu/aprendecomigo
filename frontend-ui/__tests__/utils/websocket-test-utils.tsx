/**
 * WebSocket Test Utilities
 *
 * Comprehensive testing utilities for WebSocket functionality including:
 * - Mock WebSocket implementation with full lifecycle simulation
 * - Connection state management helpers
 * - Message sending/receiving simulation
 * - Network failure and recovery testing
 * - Exponential backoff testing
 * - Multiple connection handling
 */

interface MockWebSocketEvent {
  type: string;
  data?: string;
  code?: number;
  reason?: string;
}

interface MockWebSocketOptions {
  autoOpen?: boolean;
  simulateNetworkLatency?: boolean;
  latencyMs?: number;
  failConnection?: boolean;
  connectionDelay?: number;
}

/**
 * Mock WebSocket class that simulates WebSocket behavior for testing
 */
export class MockWebSocket {
  public readyState: number = WebSocket.CONNECTING;
  public url: string;
  public protocol: string;
  public onopen: ((event: Event) => void) | null = null;
  public onclose: ((event: CloseEvent) => void) | null = null;
  public onmessage: ((event: MessageEvent) => void) | null = null;
  public onerror: ((event: Event) => void) | null = null;

  private listeners: Map<string, Function[]> = new Map();
  private messageQueue: string[] = [];
  private isClosing = false;
  private closeCode: number | undefined;
  private closeReason: string | undefined;
  private options: MockWebSocketOptions;

  // Static registry for tracking all instances
  private static instances: MockWebSocket[] = [];
  private static lastInstance: MockWebSocket | null = null;

  constructor(url: string, protocols?: string | string[], options: MockWebSocketOptions = {}) {
    this.url = url;
    this.protocol = Array.isArray(protocols) ? protocols[0] || '' : protocols || '';
    this.options = {
      autoOpen: true,
      simulateNetworkLatency: false,
      latencyMs: 100,
      failConnection: false,
      connectionDelay: 10,
      ...options,
    };

    MockWebSocket.instances.push(this);
    MockWebSocket.lastInstance = this;

    if (this.options.autoOpen) {
      this.simulateConnection();
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
  }

  send(data: string): void {
    if (this.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket is not open. ReadyState: ' + this.readyState);
    }

    // Simulate sending message
    console.log(`MockWebSocket: Sending message: ${data}`);
    
    if (this.options.simulateNetworkLatency) {
      setTimeout(() => {
        this.messageQueue.push(data);
      }, this.options.latencyMs);
    } else {
      this.messageQueue.push(data);
    }
  }

  close(code?: number, reason?: string): void {
    if (this.readyState === WebSocket.CLOSED || this.readyState === WebSocket.CLOSING) {
      return;
    }

    this.isClosing = true;
    this.readyState = WebSocket.CLOSING;
    this.closeCode = code || 1000;
    this.closeReason = reason || 'Normal closure';

    // Simulate close delay
    setTimeout(() => {
      this.readyState = WebSocket.CLOSED;
      this.triggerEvent('close', {
        code: this.closeCode,
        reason: this.closeReason,
        wasClean: this.closeCode === 1000,
      });
    }, 10);
  }

  addEventListener(type: string, listener: Function): void {
    if (!this.listeners.has(type)) {
      this.listeners.set(type, []);
    }
    this.listeners.get(type)!.push(listener);
  }

  removeEventListener(type: string, listener: Function): void {
    if (this.listeners.has(type)) {
      const listeners = this.listeners.get(type)!;
      const index = listeners.indexOf(listener);
      if (index > -1) {
        listeners.splice(index, 1);
      }
    }
  }

  // Test control methods
  simulateConnection(): void {
    if (this.options.failConnection) {
      setTimeout(() => {
        this.readyState = WebSocket.CLOSED;
        this.triggerEvent('error', new Error('Connection failed'));
        this.triggerEvent('close', {
          code: 1006,
          reason: 'Connection failed',
          wasClean: false,
        });
      }, this.options.connectionDelay);
      return;
    }

    setTimeout(() => {
      if (!this.isClosing) {
        this.readyState = WebSocket.OPEN;
        this.triggerEvent('open', {});
      }
    }, this.options.connectionDelay);
  }

  simulateMessage(data: string): void {
    if (this.readyState === WebSocket.OPEN) {
      setTimeout(() => {
        this.triggerEvent('message', { data });
      }, this.options.simulateNetworkLatency ? this.options.latencyMs : 0);
    }
  }

  simulateError(error: Error | string): void {
    const errorEvent = typeof error === 'string' ? new Error(error) : error;
    this.triggerEvent('error', errorEvent);
  }

  simulateNetworkFailure(): void {
    this.readyState = WebSocket.CLOSED;
    this.triggerEvent('error', new Error('Network failure'));
    this.triggerEvent('close', {
      code: 1006,
      reason: 'Network failure',
      wasClean: false,
    });
  }

  simulateRecovery(): void {
    if (this.readyState === WebSocket.CLOSED) {
      this.readyState = WebSocket.CONNECTING;
      this.simulateConnection();
    }
  }

  getMessageQueue(): string[] {
    return [...this.messageQueue];
  }

  clearMessageQueue(): void {
    this.messageQueue.length = 0;
  }

  private triggerEvent(type: string, data: any): void {
    // Trigger property-based handlers
    switch (type) {
      case 'open':
        if (this.onopen) this.onopen(data);
        break;
      case 'close':
        if (this.onclose) this.onclose(data);
        break;
      case 'message':
        if (this.onmessage) this.onmessage(data);
        break;
      case 'error':
        if (this.onerror) this.onerror(data);
        break;
    }

    // Trigger addEventListener-based handlers
    if (this.listeners.has(type)) {
      this.listeners.get(type)!.forEach(listener => {
        try {
          listener(data);
        } catch (err) {
          console.error(`Error in ${type} listener:`, err);
        }
      });
    }
  }
}

/**
 * WebSocket test utilities and helpers
 */
export class WebSocketTestUtils {
  private static originalWebSocket: typeof WebSocket;

  /**
   * Setup mock WebSocket for testing
   */
  static setup(): void {
    WebSocketTestUtils.originalWebSocket = global.WebSocket;
    global.WebSocket = MockWebSocket as any;
    MockWebSocket.clearInstances();
  }

  /**
   * Cleanup mock WebSocket after testing
   */
  static cleanup(): void {
    if (WebSocketTestUtils.originalWebSocket) {
      global.WebSocket = WebSocketTestUtils.originalWebSocket;
    }
    MockWebSocket.resetAll();
  }

  /**
   * Create a mock WebSocket with specific options
   */
  static createMockWebSocket(url: string, options?: MockWebSocketOptions): MockWebSocket {
    return new MockWebSocket(url, [], options);
  }

  /**
   * Get the most recently created WebSocket instance
   */
  static getLastWebSocket(): MockWebSocket | null {
    return MockWebSocket.getLastInstance();
  }

  /**
   * Get all WebSocket instances
   */
  static getAllWebSockets(): MockWebSocket[] {
    return MockWebSocket.getAllInstances();
  }

  /**
   * Wait for WebSocket to reach a specific state
   */
  static async waitForState(ws: MockWebSocket, state: number, timeout = 1000): Promise<void> {
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
  }

  /**
   * Wait for WebSocket connection to open
   */
  static async waitForConnection(ws?: MockWebSocket, timeout = 1000): Promise<MockWebSocket> {
    const webSocket = ws || WebSocketTestUtils.getLastWebSocket();
    if (!webSocket) {
      throw new Error('No WebSocket instance found');
    }
    
    await WebSocketTestUtils.waitForState(webSocket, WebSocket.OPEN, timeout);
    return webSocket;
  }

  /**
   * Wait for WebSocket to close
   */
  static async waitForClose(ws?: MockWebSocket, timeout = 1000): Promise<MockWebSocket> {
    const webSocket = ws || WebSocketTestUtils.getLastWebSocket();
    if (!webSocket) {
      throw new Error('No WebSocket instance found');
    }
    
    await WebSocketTestUtils.waitForState(webSocket, WebSocket.CLOSED, timeout);
    return webSocket;
  }

  /**
   * Simulate a successful message exchange
   */
  static async simulateMessageExchange(
    ws: MockWebSocket,
    sendMessage: string,
    responseMessage: string,
    delay = 10
  ): Promise<void> {
    ws.send(sendMessage);
    
    setTimeout(() => {
      ws.simulateMessage(responseMessage);
    }, delay);
  }

  /**
   * Simulate network interruption and recovery
   */
  static async simulateNetworkInterruption(
    ws: MockWebSocket,
    interruptionDuration = 1000
  ): Promise<void> {
    ws.simulateNetworkFailure();
    
    return new Promise(resolve => {
      setTimeout(() => {
        ws.simulateRecovery();
        resolve();
      }, interruptionDuration);
    });
  }

  /**
   * Test exponential backoff behavior
   */
  static calculateExpectedBackoffDelay(attempt: number, baseDelay = 1000): number {
    return Math.pow(2, attempt) * baseDelay;
  }

  /**
   * Verify exponential backoff timing
   */
  static verifyBackoffTiming(attempts: number[], baseDelay = 1000, tolerance = 100): boolean {
    for (let i = 1; i < attempts.length; i++) {
      const expectedDelay = WebSocketTestUtils.calculateExpectedBackoffDelay(i - 1, baseDelay);
      const actualDelay = attempts[i] - attempts[i - 1];
      
      if (Math.abs(actualDelay - expectedDelay) > tolerance) {
        return false;
      }
    }
    return true;
  }

  /**
   * Create a mock auth token for WebSocket authentication
   */
  static createMockAuthToken(): string {
    return 'mock-jwt-token-' + Date.now();
  }

  /**
   * Mock AsyncStorage for WebSocket authentication
   */
  static mockAsyncStorage(token?: string): void {
    const mockToken = token || WebSocketTestUtils.createMockAuthToken();
    
    require('@react-native-async-storage/async-storage').getItem = jest.fn()
      .mockResolvedValue(mockToken);
    
    require('@react-native-async-storage/async-storage').setItem = jest.fn()
      .mockResolvedValue(undefined);
  }

  /**
   * Mock AsyncStorage with no token (unauthenticated scenario)
   */
  static mockAsyncStorageNoToken(): void {
    require('@react-native-async-storage/async-storage').getItem = jest.fn()
      .mockResolvedValue(null);
  }

  /**
   * Create mock WebSocket message
   */
  static createMockMessage(type: string, data: any = {}, userId?: number): string {
    return JSON.stringify({
      type,
      data,
      user_id: userId,
      timestamp: new Date().toISOString(),
    });
  }

  /**
   * Create mock balance update message
   */
  static createMockBalanceMessage(balance: any, userId: number): string {
    return WebSocketTestUtils.createMockMessage('balance_update', { balance }, userId);
  }

  /**
   * Create mock purchase approval message
   */
  static createMockPurchaseApprovalMessage(
    notificationType: string,
    data: any = {},
    userId?: number
  ): string {
    return WebSocketTestUtils.createMockMessage('purchase_approval_notification', {
      notification_type: notificationType,
      title: `Purchase ${notificationType}`,
      message: `Test ${notificationType} message`,
      data,
      priority: 'medium',
      actionable: true,
    }, userId);
  }

  /**
   * Create mock transaction update message
   */
  static createMockTransactionMessage(action: string, transaction: any): string {
    return WebSocketTestUtils.createMockMessage('transaction_update', {
      action,
      transaction,
    });
  }

  /**
   * Create mock payment monitoring message
   */
  static createMockPaymentMonitoringMessage(type: string, data: any): string {
    return WebSocketTestUtils.createMockMessage(type, data);
  }

  /**
   * Utility to advance time for testing timers
   */
  static advanceTime(ms: number): void {
    jest.advanceTimersByTime(ms);
  }

  /**
   * Setup fake timers for WebSocket testing
   */
  static setupFakeTimers(): void {
    jest.useFakeTimers();
  }

  /**
   * Cleanup fake timers
   */
  static cleanupFakeTimers(): void {
    jest.useRealTimers();
  }
}

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
        amount: 25.00,
        currency: 'EUR',
        status: 'completed',
        created_at: new Date().toISOString(),
      },
    },
    timestamp: new Date().toISOString(),
  }),

  fraudAlert: (alertId: number = 1) => ({
    type: 'fraud_alert',
    data: {
      action: 'created',
      alert: {
        id: alertId,
        severity: 'high',
        status: 'active',
        description: 'Suspicious transaction detected',
        created_at: new Date().toISOString(),
      },
    },
    timestamp: new Date().toISOString(),
  }),

  webhookStatus: (url: string = 'https://example.com/webhook') => ({
    type: 'webhook_status',
    data: {
      webhook_status: {
        endpoint_url: url,
        status: 'healthy',
        last_success: new Date().toISOString(),
        success_rate: 98.5,
        avg_response_time: 125,
      },
    },
    timestamp: new Date().toISOString(),
  }),
};

// Export default utilities object
export default WebSocketTestUtils;