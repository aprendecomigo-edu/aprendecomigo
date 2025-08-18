/**
 * Tests for useBalanceWebSocket hook
 *
 * Tests cover:
 * - Balance update message handling
 * - User profile integration and authentication
 * - Subscription management and filtering
 * - Notification callbacks
 * - Reconnection logic and error handling
 * - Cross-platform WebSocket support
 * - Backend-disabled state handling
 */

import { renderHook, act, waitFor } from '@testing-library/react-native';
import React from 'react';

import WebSocketTestUtils, { WebSocketTestData } from '@/__tests__/utils/websocket-test-utils';
import { useBalanceWebSocket, useBalanceUpdates } from '@/hooks/useBalanceWebSocket';

// Mock dependencies
jest.mock('@/api/auth', () => ({
  useAuth: jest.fn(),
  useUserProfile: jest.fn(),
}));

jest.mock('@/hooks/useWebSocket', () => ({
  useWebSocketEnhanced: jest.fn(),
}));

const mockUseUserProfile = require('@/api/auth').useUserProfile as jest.Mock;
const mockUseWebSocketEnhanced = require('@/hooks/useWebSocket').useWebSocketEnhanced as jest.Mock;

describe('useBalanceWebSocket Hook', () => {
  const mockUserProfile = {
    id: 1,
    email: 'test@example.com',
    first_name: 'Test',
    last_name: 'User',
  };

  const mockWebSocketResult = {
    isConnected: false,
    lastMessage: null,
    sendMessage: jest.fn(),
    connect: jest.fn(),
    disconnect: jest.fn(),
  };

  beforeEach(() => {
    WebSocketTestUtils.setup();
    WebSocketTestUtils.setupFakeTimers();
    jest.clearAllMocks();

    mockUseUserProfile.mockReturnValue({
      userProfile: mockUserProfile,
    });

    mockUseWebSocketEnhanced.mockReturnValue(mockWebSocketResult);
  });

  afterEach(() => {
    WebSocketTestUtils.cleanup();
    WebSocketTestUtils.cleanupFakeTimers();
  });

  describe('Initialization and Connection', () => {
    it('should initialize with default options', () => {
      const { result } = renderHook(() => useBalanceWebSocket());

      expect(result.current.connected).toBe(false);
      expect(result.current.error).toBeNull();
      expect(result.current.latestBalance).toBeNull();
      expect(result.current.latestNotification).toBeNull();
    });

    it('should use enhanced WebSocket with null URL when backend consumer is disabled', () => {
      renderHook(() => useBalanceWebSocket({ enabled: true }));

      expect(mockUseWebSocketEnhanced).toHaveBeenCalledWith(
        null, // URL is null because backend consumer is not implemented yet
        expect.objectContaining({
          onOpen: expect.any(Function),
          onClose: expect.any(Function),
          onError: expect.any(Function),
          shouldReconnect: true,
        }),
      );
    });

    it('should not enable WebSocket when disabled', () => {
      renderHook(() => useBalanceWebSocket({ enabled: false }));

      expect(mockUseWebSocketEnhanced).toHaveBeenCalledWith(
        null,
        expect.objectContaining({
          shouldReconnect: false,
        }),
      );
    });

    it('should handle missing user profile gracefully', () => {
      mockUseUserProfile.mockReturnValue({
        userProfile: null,
      });

      const { result } = renderHook(() => useBalanceWebSocket());

      expect(result.current.connected).toBe(false);
      expect(result.current.error).toBeNull();
    });
  });

  describe('WebSocket Event Handlers', () => {
    it('should send subscription message on connection open', () => {
      const sendMessage = jest.fn();
      mockUseWebSocketEnhanced.mockReturnValue({
        ...mockWebSocketResult,
        sendMessage,
      });

      renderHook(() => useBalanceWebSocket());

      // Get the onOpen callback and call it
      const onOpenCallback = mockUseWebSocketEnhanced.mock.calls[0][1].onOpen;
      act(() => {
        onOpenCallback();
      });

      expect(sendMessage).toHaveBeenCalledWith({
        type: 'subscribe',
        data: {
          user_id: mockUserProfile.id,
          subscription_types: ['balance_updates', 'balance_notifications'],
        },
      });
    });

    it('should handle reconnection attempts on close', async () => {
      const connect = jest.fn();
      mockUseWebSocketEnhanced.mockReturnValue({
        ...mockWebSocketResult,
        connect,
      });

      renderHook(() =>
        useBalanceWebSocket({
          enabled: true,
          maxReconnectAttempts: 3,
          reconnectInterval: 1000,
        }),
      );

      // Get the onClose callback and call it
      const onCloseCallback = mockUseWebSocketEnhanced.mock.calls[0][1].onClose;

      act(() => {
        onCloseCallback();
      });

      // Fast-forward time to trigger reconnection
      await act(async () => {
        WebSocketTestUtils.advanceTime(1100);
      });

      expect(connect).toHaveBeenCalled();
    });

    it('should set error state on WebSocket error', () => {
      mockUseWebSocketEnhanced.mockReturnValue({
        ...mockWebSocketResult,
        isConnected: false,
      });

      const { result } = renderHook(() => useBalanceWebSocket());

      // Get the onError callback and call it
      const onErrorCallback = mockUseWebSocketEnhanced.mock.calls[0][1].onError;
      const errorMessage = 'Connection failed';

      act(() => {
        onErrorCallback(new Error(errorMessage));
      });

      expect(result.current.error).toBe(errorMessage);
    });

    it('should clear error on successful connection', () => {
      const { result } = renderHook(() => useBalanceWebSocket());

      // Simulate error first
      const onErrorCallback = mockUseWebSocketEnhanced.mock.calls[0][1].onError;
      act(() => {
        onErrorCallback(new Error('Connection failed'));
      });

      expect(result.current.error).toBeTruthy();

      // Simulate successful connection
      const onOpenCallback = mockUseWebSocketEnhanced.mock.calls[0][1].onOpen;
      act(() => {
        onOpenCallback();
      });

      expect(result.current.error).toBeNull();
    });
  });

  describe('Message Processing', () => {
    it('should process balance update messages', () => {
      const mockBalance = {
        id: 1,
        user_id: mockUserProfile.id,
        current_balance: 150.5,
        currency: 'EUR',
        last_updated: new Date().toISOString(),
      };

      mockUseWebSocketEnhanced.mockReturnValue({
        ...mockWebSocketResult,
        lastMessage: JSON.stringify({
          type: 'balance_update',
          data: { balance: mockBalance },
          user_id: mockUserProfile.id,
          timestamp: new Date().toISOString(),
        }),
      });

      const { result } = renderHook(() => useBalanceWebSocket());

      expect(result.current.latestBalance).toEqual(mockBalance);
    });

    it('should process balance notification messages', () => {
      const mockNotification = {
        id: 'notif_1',
        title: 'Low Balance Alert',
        message: 'Your balance is running low',
        type: 'balance_alert',
        created_at: new Date().toISOString(),
      };

      mockUseWebSocketEnhanced.mockReturnValue({
        ...mockWebSocketResult,
        lastMessage: JSON.stringify({
          type: 'balance_notification',
          data: { notification: mockNotification },
          user_id: mockUserProfile.id,
          timestamp: new Date().toISOString(),
        }),
      });

      const { result } = renderHook(() => useBalanceWebSocket());

      expect(result.current.latestNotification).toEqual(mockNotification);
    });

    it('should handle low balance alert messages', () => {
      const mockNotification = {
        id: 'alert_1',
        title: 'Low Balance',
        message: 'You have less than €10 remaining',
        type: 'low_balance_alert',
        created_at: new Date().toISOString(),
      };

      mockUseWebSocketEnhanced.mockReturnValue({
        ...mockWebSocketResult,
        lastMessage: JSON.stringify({
          type: 'low_balance_alert',
          data: {
            notification: mockNotification,
            remaining_hours: 2.5,
          },
          user_id: mockUserProfile.id,
          timestamp: new Date().toISOString(),
        }),
      });

      const { result } = renderHook(() => useBalanceWebSocket());

      expect(result.current.latestNotification).toEqual(mockNotification);
    });

    it('should handle package expiring messages', () => {
      const mockNotification = {
        id: 'expiry_1',
        title: 'Package Expiring',
        message: 'Your study package expires in 3 days',
        type: 'package_expiring',
        created_at: new Date().toISOString(),
      };

      mockUseWebSocketEnhanced.mockReturnValue({
        ...mockWebSocketResult,
        lastMessage: JSON.stringify({
          type: 'package_expiring',
          data: {
            notification: mockNotification,
            days_until_expiry: 3,
          },
          user_id: mockUserProfile.id,
          timestamp: new Date().toISOString(),
        }),
      });

      const { result } = renderHook(() => useBalanceWebSocket());

      expect(result.current.latestNotification).toEqual(mockNotification);
    });

    it('should ignore messages from different users', () => {
      const mockBalance = {
        id: 1,
        user_id: 999, // Different user
        current_balance: 150.5,
        currency: 'EUR',
        last_updated: new Date().toISOString(),
      };

      mockUseWebSocketEnhanced.mockReturnValue({
        ...mockWebSocketResult,
        lastMessage: JSON.stringify({
          type: 'balance_update',
          data: { balance: mockBalance },
          user_id: 999, // Different user
          timestamp: new Date().toISOString(),
        }),
      });

      const { result } = renderHook(() => useBalanceWebSocket());

      expect(result.current.latestBalance).toBeNull();
    });

    it('should handle malformed JSON messages gracefully', () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

      mockUseWebSocketEnhanced.mockReturnValue({
        ...mockWebSocketResult,
        lastMessage: 'invalid json {',
      });

      const { result } = renderHook(() => useBalanceWebSocket());

      expect(result.current.latestBalance).toBeNull();
      expect(result.current.latestNotification).toBeNull();
      expect(consoleSpy).toHaveBeenCalledWith(
        'Failed to parse WebSocket message:',
        expect.any(Error),
        'invalid json {',
      );

      consoleSpy.mockRestore();
    });

    it('should handle unknown message types gracefully', () => {
      const consoleSpy = jest.spyOn(console, 'log').mockImplementation();

      mockUseWebSocketEnhanced.mockReturnValue({
        ...mockWebSocketResult,
        lastMessage: JSON.stringify({
          type: 'unknown_message_type',
          data: {},
          user_id: mockUserProfile.id,
          timestamp: new Date().toISOString(),
        }),
      });

      const { result } = renderHook(() => useBalanceWebSocket());

      expect(result.current.latestBalance).toBeNull();
      expect(result.current.latestNotification).toBeNull();
      expect(consoleSpy).toHaveBeenCalledWith(
        'Unknown WebSocket message type:',
        'unknown_message_type',
      );

      consoleSpy.mockRestore();
    });
  });

  describe('Manual Reconnection', () => {
    it('should provide manual reconnection function', async () => {
      const connect = jest.fn();
      const disconnect = jest.fn();

      mockUseWebSocketEnhanced.mockReturnValue({
        ...mockWebSocketResult,
        connect,
        disconnect,
      });

      const { result } = renderHook(() => useBalanceWebSocket());

      await act(async () => {
        result.current.reconnect();
        WebSocketTestUtils.advanceTime(1100); // Wait for reconnection delay
      });

      expect(disconnect).toHaveBeenCalled();
      expect(connect).toHaveBeenCalled();
    });

    it('should reset error state on manual reconnection', () => {
      const connect = jest.fn();
      const disconnect = jest.fn();

      mockUseWebSocketEnhanced.mockReturnValue({
        ...mockWebSocketResult,
        connect,
        disconnect,
      });

      const { result } = renderHook(() => useBalanceWebSocket());

      // Set error state
      const onErrorCallback = mockUseWebSocketEnhanced.mock.calls[0][1].onError;
      act(() => {
        onErrorCallback(new Error('Connection failed'));
      });

      expect(result.current.error).toBeTruthy();

      // Manual reconnection should clear error
      act(() => {
        result.current.reconnect();
      });

      expect(result.current.error).toBeNull();
    });
  });

  describe('Reconnection Limits', () => {
    it('should stop reconnecting after max attempts', async () => {
      const connect = jest.fn();
      mockUseWebSocketEnhanced.mockReturnValue({
        ...mockWebSocketResult,
        connect,
      });

      const maxAttempts = 3;
      renderHook(() =>
        useBalanceWebSocket({
          enabled: true,
          maxReconnectAttempts: maxAttempts,
          reconnectInterval: 100,
        }),
      );

      const onCloseCallback = mockUseWebSocketEnhanced.mock.calls[0][1].onClose;

      // Trigger multiple reconnection attempts
      for (let i = 0; i < maxAttempts + 2; i++) {
        act(() => {
          onCloseCallback();
        });

        await act(async () => {
          WebSocketTestUtils.advanceTime(150);
        });
      }

      // Should not exceed max attempts
      expect(connect).toHaveBeenCalledTimes(maxAttempts);
    });
  });
});

describe('useBalanceUpdates Hook', () => {
  const mockUserProfile = {
    id: 1,
    email: 'test@example.com',
    first_name: 'Test',
    last_name: 'User',
  };

  const mockWebSocketResult = {
    isConnected: false,
    lastMessage: null,
    sendMessage: jest.fn(),
    connect: jest.fn(),
    disconnect: jest.fn(),
  };

  beforeEach(() => {
    WebSocketTestUtils.setup();
    jest.clearAllMocks();

    mockUseUserProfile.mockReturnValue({
      userProfile: mockUserProfile,
    });
  });

  afterEach(() => {
    WebSocketTestUtils.cleanup();
  });

  it('should call onBalanceUpdate callback when balance changes', () => {
    const onBalanceUpdate = jest.fn();
    const mockBalance = {
      id: 1,
      user_id: mockUserProfile.id,
      current_balance: 100.0,
      currency: 'EUR',
      last_updated: new Date().toISOString(),
    };

    mockUseWebSocketEnhanced.mockReturnValue({
      ...mockWebSocketResult,
      connected: true,
      lastMessage: JSON.stringify({
        type: 'balance_update',
        data: { balance: mockBalance },
        user_id: mockUserProfile.id,
        timestamp: new Date().toISOString(),
      }),
    });

    renderHook(() => useBalanceUpdates(onBalanceUpdate));

    expect(onBalanceUpdate).toHaveBeenCalledWith(mockBalance);
  });

  it('should call onNotification callback when notification received', () => {
    const onNotification = jest.fn();
    const mockNotification = {
      id: 'notif_1',
      title: 'Balance Alert',
      message: 'Your balance has been updated',
      type: 'balance_notification',
      created_at: new Date().toISOString(),
    };

    mockUseWebSocketEnhanced.mockReturnValue({
      ...mockWebSocketResult,
      connected: true,
      lastMessage: JSON.stringify({
        type: 'balance_notification',
        data: { notification: mockNotification },
        user_id: mockUserProfile.id,
        timestamp: new Date().toISOString(),
      }),
    });

    renderHook(() => useBalanceUpdates(undefined, onNotification));

    expect(onNotification).toHaveBeenCalledWith(mockNotification);
  });

  it('should return connection state and latest data', () => {
    const mockBalance = {
      id: 1,
      user_id: mockUserProfile.id,
      current_balance: 75.25,
      currency: 'EUR',
      last_updated: new Date().toISOString(),
    };

    mockUseWebSocketEnhanced.mockReturnValue({
      ...mockWebSocketResult,
      isConnected: true,
      lastMessage: JSON.stringify({
        type: 'balance_update',
        data: { balance: mockBalance },
        user_id: mockUserProfile.id,
        timestamp: new Date().toISOString(),
      }),
    });

    const { result } = renderHook(() => useBalanceUpdates());

    expect(result.current.connected).toBe(true);
    expect(result.current.latestBalance).toEqual(mockBalance);
  });

  it('should not call callbacks when callbacks are not provided', () => {
    const mockBalance = {
      id: 1,
      user_id: mockUserProfile.id,
      current_balance: 100.0,
      currency: 'EUR',
      last_updated: new Date().toISOString(),
    };

    mockUseWebSocketEnhanced.mockReturnValue({
      ...mockWebSocketResult,
      connected: true,
      lastMessage: JSON.stringify({
        type: 'balance_update',
        data: { balance: mockBalance },
        user_id: mockUserProfile.id,
        timestamp: new Date().toISOString(),
      }),
    });

    // Should not throw when no callbacks provided
    expect(() => {
      renderHook(() => useBalanceUpdates());
    }).not.toThrow();
  });
});

describe('Cross-platform WebSocket Support', () => {
  beforeEach(() => {
    WebSocketTestUtils.setup();
    jest.clearAllMocks();
  });

  afterEach(() => {
    WebSocketTestUtils.cleanup();
  });

  it('should use browser WebSocket when available', () => {
    // This is already the case in our test environment
    expect(typeof WebSocket).toBe('function');
  });

  it('should handle WebSocket not available gracefully', () => {
    const originalWebSocket = global.WebSocket;

    // Temporarily remove WebSocket
    Object.defineProperty(global, 'WebSocket', {
      value: undefined,
      configurable: true,
    });

    // Mock the createBalanceWebSocket function behavior
    const { createBalanceWebSocket } = require('@/hooks/useBalanceWebSocket');

    const result = createBalanceWebSocket('ws://test.com');
    expect(result).toBeNull();

    // Restore WebSocket
    Object.defineProperty(global, 'WebSocket', {
      value: originalWebSocket,
      configurable: true,
    });
  });
});

describe('Integration with User Profile', () => {
  const mockUserProfile = {
    id: 1,
    email: 'test@example.com',
    first_name: 'Test',
    last_name: 'User',
  };

  const mockWebSocketResult = {
    isConnected: false,
    lastMessage: null,
    sendMessage: jest.fn(),
    connect: jest.fn(),
    disconnect: jest.fn(),
  };

  beforeEach(() => {
    WebSocketTestUtils.setup();
    jest.clearAllMocks();
    
    // Re-setup mocks after clearing
    mockUseUserProfile.mockReturnValue({
      userProfile: mockUserProfile,
    });

    mockUseWebSocketEnhanced.mockReturnValue(mockWebSocketResult);
  });

  afterEach(() => {
    WebSocketTestUtils.cleanup();
  });

  it('should handle user profile changes', () => {
    const { rerender } = renderHook(() => useBalanceWebSocket());

    // Change user profile
    mockUseUserProfile.mockReturnValue({
      userProfile: {
        id: 2,
        email: 'different@example.com',
        first_name: 'Different',
        last_name: 'User',
      },
    });

    rerender();

    // Should call useWebSocketEnhanced again with the same parameters
    expect(mockUseWebSocketEnhanced).toHaveBeenCalledTimes(2);
  });

  it('should handle user profile becoming null', () => {
    const { rerender } = renderHook(() => useBalanceWebSocket());

    // Remove user profile
    mockUseUserProfile.mockReturnValue({
      userProfile: null,
    });

    rerender();

    // Should still work without throwing
    expect(mockUseWebSocketEnhanced).toHaveBeenCalledTimes(2);
  });
});
