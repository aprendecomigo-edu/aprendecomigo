/**
 * WebSocket testing utilities for Aprende Comigo platform
 * Provides standardized utilities for testing WebSocket functionality
 */

import React from 'react';

// Mock WebSocket instance management
export interface MockWebSocketInstance {
  connect: jest.Mock;
  disconnect: jest.Mock;
  send: jest.Mock;
  onMessage: jest.Mock;
  onError: jest.Mock;
  onConnect: jest.Mock;
  onDisconnect: jest.Mock;
  isConnected: jest.Mock;
  simulateMessage: jest.Mock;
  simulateError: jest.Mock;
  simulateNetworkFailure: jest.Mock;
  simulateReconnection: jest.Mock;
  getSentMessages: jest.Mock;
  dispose: jest.Mock;
  getState: jest.Mock;
  readyState: number;
  url: string;
}

/**
 * Creates a mock WebSocket instance with all required methods
 */
export const createMockWebSocket = (url = 'ws://localhost:8000/ws'): MockWebSocketInstance => {
  const sentMessages: string[] = [];
  let connected = false;
  let readyState = 0; // CONNECTING

  const mockWebSocket: MockWebSocketInstance = {
    connect: jest.fn().mockImplementation(async () => {
      connected = true;
      readyState = 1; // OPEN
      return Promise.resolve();
    }),
    disconnect: jest.fn().mockImplementation(() => {
      connected = false;
      readyState = 3; // CLOSED
    }),
    send: jest.fn().mockImplementation((message: any) => {
      if (connected) {
        sentMessages.push(JSON.stringify(message));
      }
    }),
    onMessage: jest.fn(),
    onError: jest.fn(),
    onConnect: jest.fn(),
    onDisconnect: jest.fn(),
    isConnected: jest.fn().mockImplementation(() => connected),
    simulateMessage: jest.fn().mockImplementation((data: any) => {
      // Trigger registered message handlers
      const parsedData = typeof data === 'string' ? data : JSON.stringify(data);
      mockWebSocket.onMessage.mock.calls.forEach(([handler]) => {
        if (typeof handler === 'function') {
          handler(parsedData);
        }
      });
    }),
    simulateError: jest.fn().mockImplementation((error: Error = new Error('WebSocket error')) => {
      mockWebSocket.onError.mock.calls.forEach(([handler]) => {
        if (typeof handler === 'function') {
          handler(error);
        }
      });
    }),
    simulateNetworkFailure: jest.fn().mockImplementation(() => {
      connected = false;
      readyState = 3; // CLOSED
      mockWebSocket.simulateError(new Error('Network failure'));
      mockWebSocket.onDisconnect.mock.calls.forEach(([handler]) => {
        if (typeof handler === 'function') {
          handler();
        }
      });
    }),
    simulateReconnection: jest.fn().mockImplementation(() => {
      connected = true;
      readyState = 1; // OPEN
      mockWebSocket.onConnect.mock.calls.forEach(([handler]) => {
        if (typeof handler === 'function') {
          handler();
        }
      });
    }),
    getSentMessages: jest.fn().mockImplementation(() => sentMessages.slice()),
    dispose: jest.fn().mockImplementation(() => {
      connected = false;
      readyState = 3; // CLOSED
      sentMessages.length = 0;
    }),
    getState: jest.fn().mockImplementation(() => (connected ? 'CONNECTED' : 'DISCONNECTED')),
    get readyState() {
      return readyState;
    },
    set readyState(value: number) {
      readyState = value;
      connected = value === 1; // OPEN
    },
    url,
  };

  return mockWebSocket;
};

/**
 * Creates a mock WebSocket client factory
 */
export const createMockWebSocketClient = (config: any = {}) => {
  const mockInstance = createMockWebSocket(config.url);

  // Store reference for global test access
  if (!global.__mockWebSocketClients) {
    global.__mockWebSocketClients = [];
  }
  global.__mockWebSocketClients.push(mockInstance);
  global.__lastMockWebSocketClient = mockInstance;

  return mockInstance;
};

/**
 * Utility to get the last created mock WebSocket client
 */
export const getLastMockWebSocketClient = (): MockWebSocketInstance | null => {
  return global.__lastMockWebSocketClient || null;
};

/**
 * Utility to get all mock WebSocket clients
 */
export const getAllMockWebSocketClients = (): MockWebSocketInstance[] => {
  return global.__mockWebSocketClients || [];
};

/**
 * Clears all mock WebSocket clients (useful for test cleanup)
 */
export const clearMockWebSocketClients = () => {
  global.__mockWebSocketClients = [];
  global.__lastMockWebSocketClient = null;
  global.__webSocketGlobalFailure = false;
};

/**
 * Simulates global WebSocket connection failure
 */
export const simulateGlobalWebSocketFailure = (enabled = true) => {
  global.__webSocketGlobalFailure = enabled;
};

/**
 * Mock WebSocket hook for testing
 */
export const useMockWebSocket = (url: string, config: any = {}) => {
  const [webSocketClient] = React.useState(() => createMockWebSocketClient({ url, ...config }));
  const [isConnected, setIsConnected] = React.useState(false);
  const [connectionState, setConnectionState] = React.useState<
    'CONNECTING' | 'CONNECTED' | 'DISCONNECTED'
  >('DISCONNECTED');

  React.useEffect(() => {
    // Set up mock event handlers
    webSocketClient.onConnect(() => {
      setIsConnected(true);
      setConnectionState('CONNECTED');
    });

    webSocketClient.onDisconnect(() => {
      setIsConnected(false);
      setConnectionState('DISCONNECTED');
    });

    webSocketClient.onError(() => {
      setIsConnected(false);
      setConnectionState('DISCONNECTED');
    });

    return () => {
      webSocketClient.dispose();
    };
  }, [webSocketClient]);

  return {
    webSocketClient,
    isConnected,
    connectionState,
    connect: webSocketClient.connect,
    disconnect: webSocketClient.disconnect,
    send: webSocketClient.send,
  };
};

/**
 * Test data factories for common WebSocket message types
 */
export const createBalanceUpdateMessage = (balance: number, remainingHours: number) => ({
  type: 'balance_update',
  data: {
    balance,
    remainingHours,
    timestamp: new Date().toISOString(),
  },
});

export const createTransactionMessage = (transaction: any) => ({
  type: 'transaction',
  data: transaction,
});

export const createPurchaseApprovalMessage = (approval: any) => ({
  type: 'purchase_approval',
  data: approval,
});

/**
 * Waits for WebSocket to reach a specific state
 */
export const waitForWebSocketState = async (
  webSocket: MockWebSocketInstance,
  state: 'CONNECTED' | 'DISCONNECTED',
  timeout = 1000,
): Promise<void> => {
  return new Promise((resolve, reject) => {
    const startTime = Date.now();
    const checkState = () => {
      const currentState = webSocket.getState();
      if (currentState === state) {
        resolve();
        return;
      }

      if (Date.now() - startTime > timeout) {
        reject(new Error(`WebSocket did not reach state ${state} within ${timeout}ms`));
        return;
      }

      setTimeout(checkState, 10);
    };
    checkState();
  });
};

/**
 * Main WebSocket test utilities object with setup/cleanup methods
 * This provides the interface that tests expect
 */
const WebSocketTestUtils = {
  // Setup methods
  setup: () => {
    clearMockWebSocketClients();
    global.__webSocketGlobalFailure = false;
  },

  cleanup: () => {
    clearMockWebSocketClients();
    global.__webSocketGlobalFailure = false;
  },

  setupFakeTimers: () => {
    jest.useFakeTimers();
  },

  cleanupFakeTimers: () => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  },

  // Timer utilities for testing
  advanceTime: (ms: number) => {
    jest.advanceTimersByTime(ms);
  },

  runAllTimers: () => {
    jest.runAllTimers();
  },

  runOnlyPendingTimers: () => {
    jest.runOnlyPendingTimers();
  },

  // AsyncStorage mocking for tests
  mockAsyncStorage: (token: string | null = 'test-token') => {
    const AsyncStorage = require('@react-native-async-storage/async-storage');
    AsyncStorage.getItem.mockResolvedValue(token);
  },

  mockAsyncStorageNoToken: () => {
    const AsyncStorage = require('@react-native-async-storage/async-storage');
    AsyncStorage.getItem.mockResolvedValue(null);
  },

  // WebSocket instance management (with aliases that tests expect)
  getLastWebSocket: getLastMockWebSocketClient, // Alias for compatibility
  getLastWebSocketClient: getLastMockWebSocketClient,
  getAllWebSocketClients: getAllMockWebSocketClients,
  getAllWebSockets: getAllMockWebSocketClients, // Alias for compatibility - tests expect this name
  clearWebSocketClients: clearMockWebSocketClients,
  simulateGlobalFailure: simulateGlobalWebSocketFailure,
  setGlobalConnectionFailure: simulateGlobalWebSocketFailure, // Alias for compatibility

  // Backoff timing verification for exponential backoff tests
  verifyBackoffTiming: (attempts: number[], baseDelay: number, tolerance = 200): boolean => {
    if (attempts.length === 0) return true;
    
    for (let i = 1; i < attempts.length; i++) {
      const expectedDelay = Math.min(baseDelay * Math.pow(2, i - 1), 30000); // Max 30s
      const actualDelay = attempts[i] - attempts[i - 1];
      const minAllowed = expectedDelay - tolerance;
      const maxAllowed = expectedDelay + tolerance;
      
      if (actualDelay < minAllowed || actualDelay > maxAllowed) {
        return false;
      }
    }
    return true;
  },

  // Message factories
  createBalanceUpdate: createBalanceUpdateMessage,
  createTransaction: createTransactionMessage,
  createPurchaseApproval: createPurchaseApprovalMessage,

  // Async utilities
  waitForWebSocketState,
};

/**
 * Mock push notifications for testing
 * Sets up Notification API mock with required methods
 */
export const mockPushNotifications = () => {
  // Mock Notification API for web environments
  global.Notification = {
    permission: 'granted',
    requestPermission: jest.fn().mockResolvedValue('granted'),
  } as any;

  // Mock Notification constructor
  global.Notification = jest.fn().mockImplementation((title, options) => ({
    title,
    options,
    onclick: null,
    onclose: null,
    onerror: null,
    onshow: null,
    close: jest.fn(),
  }));

  // Add permission property to the constructor
  (global.Notification as any).permission = 'granted';
  (global.Notification as any).requestPermission = jest.fn().mockResolvedValue('granted');

  // Mock expo-notifications for native environments
  jest.mock('expo-notifications', () => ({
    scheduleNotificationAsync: jest.fn().mockResolvedValue('notification-id'),
    cancelScheduledNotificationAsync: jest.fn(),
    getAllScheduledNotificationsAsync: jest.fn().mockResolvedValue([]),
    getPermissionsAsync: jest.fn().mockResolvedValue({
      status: 'granted',
      canAskAgain: true,
      granted: true,
    }),
    requestPermissionsAsync: jest.fn().mockResolvedValue({
      status: 'granted',
      canAskAgain: true,
      granted: true,
    }),
  }), { virtual: true });
};

// Export types that tests might need
export interface WebSocketTestData {
  type: string;
  data: any;
  timestamp?: string;
}

export interface MockWebSocket extends MockWebSocketInstance {}

// Default export that tests expect
export default WebSocketTestUtils;

// Global type declarations
declare global {
  var __mockWebSocketClients: MockWebSocketInstance[];
  var __lastMockWebSocketClient: MockWebSocketInstance | null;
  var __webSocketGlobalFailure: boolean;
}
