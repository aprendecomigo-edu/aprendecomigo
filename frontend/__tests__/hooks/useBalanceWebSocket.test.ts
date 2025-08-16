/**
 * useBalanceWebSocket Hook Tests
 *
 * Comprehensive tests for balance WebSocket functionality including:
 * - Real-time balance updates via WebSocket
 * - Balance notification handling
 * - Low balance alerts and package expiring notifications
 * - User profile integration and authentication
 * - Connection lifecycle management
 * - Error handling and resilience
 * - Callback management and memory safety
 */

import { renderHook, act, waitFor } from '@testing-library/react-native';

import { MockWebSocket, WebSocketTestUtils } from '../utils/websocket-test-utils';

import { useBalanceWebSocket, useBalanceUpdates } from '@/hooks/useBalanceWebSocket';

// Mock dependencies
jest.mock('@/api/auth', () => ({
  useAuth: () => ({ isAuthenticated: true }),
  useUserProfile: () => ({
    userProfile: {
      id: 1,
      email: 'test@example.com',
      first_name: 'Test',
      last_name: 'User',
    },
  }),
}));

jest.mock('@/hooks/useWebSocket', () => ({
  useWebSocketEnhanced: jest.fn(),
}));

// Mock console methods
const originalConsoleLog = console.log;
const originalConsoleError = console.error;

describe('useBalanceWebSocket', () => {
  let mockWebSocket: MockWebSocket;
  let mockUseWebSocketEnhanced: jest.Mock;

  beforeEach(() => {
    // Setup WebSocket mock
    mockWebSocket = new MockWebSocket('ws://localhost:8000/test/');

    // Mock the useWebSocketEnhanced hook
    mockUseWebSocketEnhanced = require('@/hooks/useWebSocket').useWebSocketEnhanced;
    mockUseWebSocketEnhanced.mockReturnValue({
      isConnected: false,
      lastMessage: null,
      sendMessage: jest.fn(),
      connect: jest.fn(),
      disconnect: jest.fn(),
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
    if (__DEV__) {
      jest.useRealTimers();
      console.log = originalConsoleLog;
      jest.useRealTimers();
    }
    console.error = originalConsoleError;
    jest.clearAllMocks();
  });

  describe('Connection Management', () => {
    it('should initialize with correct default values', () => {
      const { result } = renderHook(() => useBalanceWebSocket());

      expect(result.current.connected).toBe(false);
      expect(result.current.error).toBeNull();
      expect(result.current.latestBalance).toBeNull();
      expect(result.current.latestNotification).toBeNull();
      expect(typeof result.current.reconnect).toBe('function');
      expect(typeof result.current.sendMessage).toBe('function');
    });

    it('should handle connection establishment', async () => {
      // Mock connected state
      mockUseWebSocketEnhanced.mockReturnValue({
        isConnected: true,
        lastMessage: null,
        sendMessage: jest.fn(),
        connect: jest.fn(),
        disconnect: jest.fn(),
      });

      const { result } = renderHook(() => useBalanceWebSocket({ enabled: true }));

      expect(result.current.connected).toBe(true);
    });

    it('should handle connection with custom options', () => {
      const customOptions = {
        enabled: true,
        reconnectInterval: 10000,
        maxReconnectAttempts: 3,
      };

      const { result } = renderHook(() => useBalanceWebSocket(customOptions));

      // Verify the hook was called with correct parameters
      expect(mockUseWebSocketEnhanced).toHaveBeenCalledWith(
        null, // WebSocket URL is null as noted in the hook (backend consumer not implemented)
        expect.objectContaining({
          onOpen: expect.any(Function),
          onClose: expect.any(Function),
          onError: expect.any(Function),
          shouldReconnect: expect.any(Boolean),
        }),
      );
    });

    it('should be disabled when enabled option is false', () => {
      const { result } = renderHook(() => useBalanceWebSocket({ enabled: false }));

      expect(result.current.connected).toBe(false);
      expect(mockUseWebSocketEnhanced).toHaveBeenCalledWith(null, expect.any(Object));
    });
  });

  describe('Message Handling', () => {
    it('should handle balance update messages correctly', async () => {
      const mockSendMessage = jest.fn();
      const testBalance = {
        id: 1,
        current_balance: 150.0,
        currency: 'EUR',
        last_updated: new Date().toISOString(),
        student_id: 1,
        school_id: 1,
      };

      const balanceMessage = WebSocketTestUtils.createTestMessage.balance({
        data: { balance: testBalance },
        user_id: 1,
      });

      // Setup connected WebSocket with message
      mockUseWebSocketEnhanced.mockReturnValue({
        isConnected: true,
        lastMessage: JSON.stringify(balanceMessage),
        sendMessage: mockSendMessage,
        connect: jest.fn(),
        disconnect: jest.fn(),
      });

      const { result } = renderHook(() => useBalanceWebSocket({ enabled: true }));

      // Wait for message processing
      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 50));
      });

      expect(result.current.latestBalance).toEqual(testBalance);
    });

    it('should handle balance notification messages', async () => {
      const testNotification = {
        id: 'notif_123',
        type: 'low_balance_alert',
        title: 'Low Balance Alert',
        message: 'Your balance is running low',
        priority: 'high' as const,
        created_at: new Date().toISOString(),
        read: false,
      };

      const notificationMessage = {
        type: 'balance_notification',
        data: { notification: testNotification },
        user_id: 1,
        timestamp: new Date().toISOString(),
      };

      mockUseWebSocketEnhanced.mockReturnValue({
        isConnected: true,
        lastMessage: JSON.stringify(notificationMessage),
        sendMessage: jest.fn(),
        connect: jest.fn(),
        disconnect: jest.fn(),
      });

      const { result } = renderHook(() => useBalanceWebSocket({ enabled: true }));

      // Wait for message processing
      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 50));
      });

      expect(result.current.latestNotification).toEqual(testNotification);
    });

    it('should handle low balance alert messages', async () => {
      const lowBalanceMessage = {
        type: 'low_balance_alert',
        data: {
          remaining_hours: 2,
          message: 'Only 2 hours remaining',
          notification: {
            id: 'alert_123',
            type: 'low_balance',
            title: 'Low Balance Alert',
            message: 'Only 2 hours remaining',
            priority: 'urgent' as const,
            created_at: new Date().toISOString(),
            read: false,
          },
        },
        user_id: 1,
        timestamp: new Date().toISOString(),
      };

      mockUseWebSocketEnhanced.mockReturnValue({
        isConnected: true,
        lastMessage: JSON.stringify(lowBalanceMessage),
        sendMessage: jest.fn(),
        connect: jest.fn(),
        disconnect: jest.fn(),
      });

      const { result } = renderHook(() => useBalanceWebSocket({ enabled: true }));

      // Wait for message processing
      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 50));
      });

      expect(result.current.latestNotification).toEqual(lowBalanceMessage.data.notification);
    });

    it('should handle package expiring messages', async () => {
      const packageExpiringMessage = {
        type: 'package_expiring',
        data: {
          days_until_expiry: 3,
          message: 'Package expires in 3 days',
          notification: {
            id: 'expiry_123',
            type: 'package_expiring',
            title: 'Package Expiring Soon',
            message: 'Package expires in 3 days',
            priority: 'medium' as const,
            created_at: new Date().toISOString(),
            read: false,
          },
        },
        user_id: 1,
        timestamp: new Date().toISOString(),
      };

      mockUseWebSocketEnhanced.mockReturnValue({
        isConnected: true,
        lastMessage: JSON.stringify(packageExpiringMessage),
        sendMessage: jest.fn(),
        connect: jest.fn(),
        disconnect: jest.fn(),
      });

      const { result } = renderHook(() => useBalanceWebSocket({ enabled: true }));

      // Wait for message processing
      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 50));
      });

      expect(result.current.latestNotification).toEqual(packageExpiringMessage.data.notification);
    });

    it('should ignore messages for different users', async () => {
      const balanceMessage = WebSocketTestUtils.createTestMessage.balance({
        user_id: 999, // Different user ID
        data: {
          balance: {
            id: 1,
            current_balance: 150.0,
            currency: 'EUR',
            last_updated: new Date().toISOString(),
            student_id: 999,
            school_id: 1,
          },
        },
      });

      mockUseWebSocketEnhanced.mockReturnValue({
        isConnected: true,
        lastMessage: JSON.stringify(balanceMessage),
        sendMessage: jest.fn(),
        connect: jest.fn(),
        disconnect: jest.fn(),
      });

      const { result } = renderHook(() => useBalanceWebSocket({ enabled: true }));

      // Wait for message processing
      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 50));
      });

      // Should not update balance for different user
      expect(result.current.latestBalance).toBeNull();
    });

    it('should handle malformed messages gracefully', async () => {
      mockUseWebSocketEnhanced.mockReturnValue({
        isConnected: true,
        lastMessage: '{ invalid json }',
        sendMessage: jest.fn(),
        connect: jest.fn(),
        disconnect: jest.fn(),
      });

      const { result } = renderHook(() => useBalanceWebSocket({ enabled: true }));

      // Wait for message processing
      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 50));
      });

      // Should handle gracefully without crashing
      expect(result.current.latestBalance).toBeNull();
      expect(result.current.latestNotification).toBeNull();
      expect(console.error).toHaveBeenCalledWith(
        'Failed to parse WebSocket message:',
        expect.any(Error),
        '{ invalid json }',
      );
    });

    it('should handle unknown message types gracefully', async () => {
      const unknownMessage = {
        type: 'unknown_type',
        data: { some: 'data' },
        user_id: 1,
        timestamp: new Date().toISOString(),
      };

      mockUseWebSocketEnhanced.mockReturnValue({
        isConnected: true,
        lastMessage: JSON.stringify(unknownMessage),
        sendMessage: jest.fn(),
        connect: jest.fn(),
        disconnect: jest.fn(),
      });

      const { result } = renderHook(() => useBalanceWebSocket({ enabled: true }));

      // Wait for message processing
      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 50));
      });

      if (__DEV__) {
        expect(console.log).toHaveBeenCalledWith('Unknown WebSocket message type:', 'unknown_type');
      }
    });
  });

  describe('Reconnection Management', () => {
    it('should provide manual reconnection functionality', async () => {
      const mockConnect = jest.fn();
      const mockDisconnect = jest.fn();

      mockUseWebSocketEnhanced.mockReturnValue({
        isConnected: false,
        lastMessage: null,
        sendMessage: jest.fn(),
        connect: mockConnect,
        disconnect: mockDisconnect,
      });

      const { result } = renderHook(() => useBalanceWebSocket({ enabled: true }));

      // Trigger manual reconnection
      await act(async () => {
        result.current.reconnect();
      });

      // Should disconnect first, then reconnect after delay
      expect(mockDisconnect).toHaveBeenCalledTimes(1);

      // Fast forward the timer
      await act(async () => {
        jest.advanceTimersByTime(1000);
      });

      expect(mockConnect).toHaveBeenCalledTimes(1);
    });

    it('should reset error state on manual reconnection', async () => {
      mockUseWebSocketEnhanced.mockReturnValue({
        isConnected: false,
        lastMessage: null,
        sendMessage: jest.fn(),
        connect: jest.fn(),
        disconnect: jest.fn(),
      });

      const { result } = renderHook(() => useBalanceWebSocket({ enabled: true }));

      // Simulate error state
      act(() => {
        const onError = mockUseWebSocketEnhanced.mock.calls[0][1].onError;
        onError(new Event('error'));
      });

      // Trigger manual reconnection
      await act(async () => {
        result.current.reconnect();
      });

      expect(result.current.error).toBeNull();
    });
  });

  describe('Error Handling', () => {
    it('should handle WebSocket errors correctly', () => {
      mockUseWebSocketEnhanced.mockReturnValue({
        isConnected: false,
        lastMessage: null,
        sendMessage: jest.fn(),
        connect: jest.fn(),
        disconnect: jest.fn(),
      });

      const { result } = renderHook(() => useBalanceWebSocket({ enabled: true }));

      // Simulate WebSocket error
      act(() => {
        const onError = mockUseWebSocketEnhanced.mock.calls[0][1].onError;
        const errorEvent = new Event('error');
        (errorEvent as any).message = 'Connection failed';
        onError(errorEvent);
      });

      expect(result.current.error).toBe('Connection failed');
    });

    it('should handle errors without message property', () => {
      mockUseWebSocketEnhanced.mockReturnValue({
        isConnected: false,
        lastMessage: null,
        sendMessage: jest.fn(),
        connect: jest.fn(),
        disconnect: jest.fn(),
      });

      const { result } = renderHook(() => useBalanceWebSocket({ enabled: true }));

      // Simulate WebSocket error without message
      act(() => {
        const onError = mockUseWebSocketEnhanced.mock.calls[0][1].onError;
        onError(new Event('error'));
      });

      expect(result.current.error).toBe('WebSocket connection error');
    });
  });

  describe('Message Sending', () => {
    it('should send subscription message on connection', () => {
      const mockSendMessage = jest.fn();

      mockUseWebSocketEnhanced.mockReturnValue({
        isConnected: true,
        lastMessage: null,
        sendMessage: mockSendMessage,
        connect: jest.fn(),
        disconnect: jest.fn(),
      });

      renderHook(() => useBalanceWebSocket({ enabled: true }));

      // Trigger onOpen callback
      act(() => {
        const onOpen = mockUseWebSocketEnhanced.mock.calls[0][1].onOpen;
        onOpen();
      });

      expect(mockSendMessage).toHaveBeenCalledWith({
        type: 'subscribe',
        data: {
          user_id: 1,
          subscription_types: ['balance_updates', 'balance_notifications'],
        },
      });
    });

    it('should expose sendMessage function', () => {
      const mockSendMessage = jest.fn();

      mockUseWebSocketEnhanced.mockReturnValue({
        isConnected: true,
        lastMessage: null,
        sendMessage: mockSendMessage,
        connect: jest.fn(),
        disconnect: jest.fn(),
      });

      const { result } = renderHook(() => useBalanceWebSocket({ enabled: true }));

      const testMessage = { type: 'test', data: 'hello' };
      result.current.sendMessage(testMessage);

      expect(mockSendMessage).toHaveBeenCalledWith(testMessage);
    });
  });
});

describe('useBalanceUpdates', () => {
  let mockUseBalanceWebSocket: jest.Mock;

  beforeEach(() => {
    // Mock the useBalanceWebSocket hook
    mockUseBalanceWebSocket = jest.fn();
    jest.doMock('@/hooks/useBalanceWebSocket', () => ({
      useBalanceWebSocket: mockUseBalanceWebSocket,
    }));

    if (__DEV__) {
      console.log = jest.fn();
    }
    console.error = jest.fn();
  });

  afterEach(() => {
    if (__DEV__) {
      console.log = originalConsoleLog;
    }
    console.error = originalConsoleError;
    jest.clearAllMocks();
  });

  it('should call balance update callback when balance changes', () => {
    const mockOnBalanceUpdate = jest.fn();
    const testBalance = {
      id: 1,
      current_balance: 100.0,
      currency: 'EUR',
      last_updated: new Date().toISOString(),
      student_id: 1,
      school_id: 1,
    };

    // Mock initial state
    mockUseBalanceWebSocket.mockReturnValue({
      connected: true,
      latestBalance: null,
      latestNotification: null,
    });

    const { rerender } = renderHook(() => useBalanceUpdates(mockOnBalanceUpdate));

    // Update with new balance
    mockUseBalanceWebSocket.mockReturnValue({
      connected: true,
      latestBalance: testBalance,
      latestNotification: null,
    });

    rerender();

    expect(mockOnBalanceUpdate).toHaveBeenCalledWith(testBalance);
  });

  it('should call notification callback when notification changes', () => {
    const mockOnNotification = jest.fn();
    const testNotification = {
      id: 'notif_123',
      type: 'low_balance_alert',
      title: 'Low Balance Alert',
      message: 'Your balance is running low',
      priority: 'high' as const,
      created_at: new Date().toISOString(),
      read: false,
    };

    // Mock initial state
    mockUseBalanceWebSocket.mockReturnValue({
      connected: true,
      latestBalance: null,
      latestNotification: null,
    });

    const { rerender } = renderHook(() => useBalanceUpdates(undefined, mockOnNotification));

    // Update with new notification
    mockUseBalanceWebSocket.mockReturnValue({
      connected: true,
      latestBalance: null,
      latestNotification: testNotification,
    });

    rerender();

    expect(mockOnNotification).toHaveBeenCalledWith(testNotification);
  });

  it('should return connection state and latest data', () => {
    const testBalance = {
      id: 1,
      current_balance: 100.0,
      currency: 'EUR',
      last_updated: new Date().toISOString(),
      student_id: 1,
      school_id: 1,
    };

    const testNotification = {
      id: 'notif_123',
      type: 'low_balance_alert',
      title: 'Low Balance Alert',
      message: 'Your balance is running low',
      priority: 'high' as const,
      created_at: new Date().toISOString(),
      read: false,
    };

    mockUseBalanceWebSocket.mockReturnValue({
      connected: true,
      latestBalance: testBalance,
      latestNotification: testNotification,
    });

    const { result } = renderHook(() => useBalanceUpdates());

    expect(result.current.connected).toBe(true);
    expect(result.current.latestBalance).toEqual(testBalance);
    expect(result.current.latestNotification).toEqual(testNotification);
  });

  it('should handle callbacks gracefully when data is null', () => {
    const mockOnBalanceUpdate = jest.fn();
    const mockOnNotification = jest.fn();

    mockUseBalanceWebSocket.mockReturnValue({
      connected: false,
      latestBalance: null,
      latestNotification: null,
    });

    renderHook(() => useBalanceUpdates(mockOnBalanceUpdate, mockOnNotification));

    expect(mockOnBalanceUpdate).not.toHaveBeenCalled();
    expect(mockOnNotification).not.toHaveBeenCalled();
  });
});
