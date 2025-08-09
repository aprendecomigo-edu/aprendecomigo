/**
 * WebSocket Test Utils
 *
 * Comprehensive utilities for testing WebSocket functionality including:
 * - Mock WebSocket implementation
 * - Test message creation helpers
 * - Connection simulation utilities
 * - Error condition helpers
 * - Memory leak detection
 * - Performance testing helpers
 */

// WebSocket connection states
export const ConnectionStates = {
  CONNECTING: 0,
  OPEN: 1,
  CLOSING: 2,
  CLOSED: 3,
} as const;

// Common WebSocket error codes
export const WebSocketErrorCodes = {
  NORMAL_CLOSURE: 1000,
  GOING_AWAY: 1001,
  PROTOCOL_ERROR: 1002,
  ABNORMAL_CLOSURE: 1006,
  INVALID_FRAME_PAYLOAD_DATA: 1007,
  POLICY_VIOLATION: 1008,
  MESSAGE_TOO_BIG: 1009,
  MISSING_EXTENSION: 1010,
  INTERNAL_ERROR: 1011,
  SERVICE_RESTART: 1012,
  TRY_AGAIN_LATER: 1013,
  BAD_GATEWAY: 1014,
} as const;

/**
 * Enhanced Mock WebSocket for testing
 */
export class MockWebSocket {
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

  private shouldFailConnection = false;
  private shouldFailOnSend = false;
  private connectionDelay = 10;
  private messageQueue: any[] = [];

  constructor(url: string) {
    this.url = url;
    // Auto-connect after short delay unless configured to fail
    setTimeout(() => {
      if (!this.shouldFailConnection) {
        this.readyState = MockWebSocket.OPEN;
        if (this.onopen) {
          this.onopen(new Event('open'));
        }
      } else {
        this.readyState = MockWebSocket.CLOSED;
        if (this.onerror) {
          this.onerror(new Event('error'));
        }
      }
    }, this.connectionDelay);
  }

  send = jest.fn((data: any) => {
    if (this.shouldFailOnSend) {
      throw new Error('WebSocket send failed');
    }
    if (this.readyState !== MockWebSocket.OPEN) {
      throw new Error('WebSocket is not open');
    }
    // Store sent messages for verification
    this.messageQueue.push(data);
  });

  close = jest.fn((code = 1000, reason = 'Normal closure') => {
    this.readyState = MockWebSocket.CLOSED;
    if (this.onclose) {
      this.onclose({
        code,
        reason,
        wasClean: code === 1000,
        type: 'close',
      });
    }
  });

  // Test helper methods
  simulateMessage(data: any) {
    if (this.onmessage && this.readyState === MockWebSocket.OPEN) {
      const messageData = typeof data === 'string' ? data : JSON.stringify(data);
      this.onmessage({
        data: messageData,
        type: 'message',
      });
    }
  }

  simulateError() {
    if (this.onerror) {
      this.onerror(new Event('error'));
    }
  }

  simulateDisconnect(code = WebSocketErrorCodes.ABNORMAL_CLOSURE, reason = 'Connection lost') {
    this.readyState = MockWebSocket.CLOSED;
    if (this.onclose) {
      this.onclose({
        code,
        reason,
        wasClean: code === WebSocketErrorCodes.NORMAL_CLOSURE,
        type: 'close',
      });
    }
  }

  triggerOpen() {
    this.readyState = MockWebSocket.OPEN;
    if (this.onopen) {
      this.onopen({ type: 'open' });
    }
  }

  triggerClose(code = 1000, reason = 'Normal closure') {
    this.readyState = MockWebSocket.CLOSED;
    if (this.onclose) {
      this.onclose({ type: 'close', code, reason, wasClean: code === 1000 });
    }
  }

  triggerMessage(data: any) {
    if (this.onmessage) {
      this.onmessage({
        type: 'message',
        data: typeof data === 'string' ? data : JSON.stringify(data),
      });
    }
  }

  triggerError() {
    if (this.onerror) {
      this.onerror({ type: 'error' });
    }
  }

  // Configuration methods for testing error scenarios
  setShouldFailConnection(shouldFail: boolean) {
    this.shouldFailConnection = shouldFail;
  }

  setShouldFailOnSend(shouldFail: boolean) {
    this.shouldFailOnSend = shouldFail;
  }

  setConnectionDelay(delay: number) {
    this.connectionDelay = delay;
  }

  // Get sent messages for verification
  getSentMessages() {
    return [...this.messageQueue];
  }

  clearSentMessages() {
    this.messageQueue = [];
  }
}

/**
 * WebSocket Test Utilities
 */
export class WebSocketTestUtils {
  private static originalWebSocket: any;
  private static mockInstance: MockWebSocket | null = null;

  /**
   * Setup WebSocket mock for testing
   */
  static setupWebSocketMock(url = 'ws://test'): MockWebSocket {
    this.originalWebSocket = global.WebSocket;
    this.mockInstance = new MockWebSocket(url);
    global.WebSocket = jest.fn(() => this.mockInstance) as any;
    return this.mockInstance;
  }

  /**
   * Restore original WebSocket
   */
  static restoreWebSocket() {
    if (this.originalWebSocket) {
      global.WebSocket = this.originalWebSocket;
    }
    this.mockInstance = null;
  }

  /**
   * Simulate successful WebSocket connection
   */
  static async simulateConnection(mockWs: MockWebSocket): Promise<void> {
    return new Promise(resolve => {
      setTimeout(() => {
        mockWs.triggerOpen();
        resolve();
      }, 0);
    });
  }

  /**
   * Simulate connection failure
   */
  static async simulateConnectionFailure(mockWs: MockWebSocket): Promise<void> {
    return new Promise(resolve => {
      setTimeout(() => {
        mockWs.setShouldFailConnection(true);
        mockWs.triggerError();
        resolve();
      }, 0);
    });
  }

  /**
   * Simulate message sending
   */
  static simulateMessageSend(mockWs: MockWebSocket, message: any) {
    mockWs.simulateMessage(message);
  }

  /**
   * Test exponential backoff pattern
   */
  static testExponentialBackoff(attempts: number[]) {
    for (let i = 1; i < attempts.length; i++) {
      const expectedDelay = Math.pow(2, i - 1) * 1000;
      expect(attempts[i - 1]).toBe(expectedDelay);
    }
  }

  /**
   * Create test messages for different scenarios
   */
  static createTestMessage = {
    balance: (data: any) => ({
      type: 'balance_update',
      timestamp: new Date().toISOString(),
      ...data,
    }),

    purchaseApproval: (data: any) => ({
      notification_type: 'new_request',
      title: 'Test Notification',
      message: 'Test message',
      priority: 'medium',
      notification_id: `test_${Date.now()}`,
      timestamp: new Date().toISOString(),
      ...data,
    }),

    transaction: (data: any) => ({
      type: 'transaction_update',
      timestamp: new Date().toISOString(),
      ...data,
    }),

    generic: (data: any) => ({
      type: 'test_message',
      timestamp: new Date().toISOString(),
      ...data,
    }),
  };

  /**
   * Memory leak detection utilities
   */
  static detectMemoryLeaks = {
    simulateComponentUnmount: async () => {
      // Simulate component unmount for memory leak testing
      await new Promise(resolve => setTimeout(resolve, 0));
    },

    checkEventListenerCleanup: (mockWs: MockWebSocket): boolean => {
      // Check if event listeners were properly cleaned up
      return (
        mockWs.onopen === null &&
        mockWs.onclose === null &&
        mockWs.onmessage === null &&
        mockWs.onerror === null
      );
    },
  };

  /**
   * Performance testing utilities
   */
  static performance = {
    measureConnectionTime: async (mockWs: MockWebSocket): Promise<number> => {
      const start = Date.now();
      await this.simulateConnection(mockWs);
      return Date.now() - start;
    },

    simulateHighVolume: (mockWs: MockWebSocket, messageCount: number) => {
      for (let i = 0; i < messageCount; i++) {
        mockWs.simulateMessage({ type: 'bulk_test', sequence: i });
      }
    },
  };

  /**
   * Error scenario helpers
   */
  static errorScenarios = {
    networkFailure: (mockWs: MockWebSocket) => {
      mockWs.simulateDisconnect(WebSocketErrorCodes.ABNORMAL_CLOSURE, 'Network failure');
    },

    serverRestart: (mockWs: MockWebSocket) => {
      mockWs.simulateDisconnect(WebSocketErrorCodes.SERVICE_RESTART, 'Server restart');
    },

    protocolError: (mockWs: MockWebSocket) => {
      mockWs.simulateDisconnect(WebSocketErrorCodes.PROTOCOL_ERROR, 'Protocol error');
    },
  };

  /**
   * Wait for WebSocket state change
   */
  static async waitForStateChange(
    mockWs: MockWebSocket,
    targetState: number,
    timeout = 1000
  ): Promise<void> {
    return new Promise((resolve, reject) => {
      const startTime = Date.now();

      const checkState = () => {
        if (mockWs.readyState === targetState) {
          resolve();
        } else if (Date.now() - startTime > timeout) {
          reject(new Error(`Timeout waiting for state ${targetState}`));
        } else {
          setTimeout(checkState, 10);
        }
      };

      checkState();
    });
  }

  /**
   * Batch message sending for testing
   */
  static sendMessageBatch(mockWs: MockWebSocket, messages: any[]) {
    messages.forEach(message => {
      mockWs.simulateMessage(message);
    });
  }
}

export default WebSocketTestUtils;
