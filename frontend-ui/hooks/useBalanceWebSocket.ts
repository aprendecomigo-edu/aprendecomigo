/**
 * Balance WebSocket Hook
 *
 * Real-time balance updates via WebSocket infrastructure for immediate
 * balance notifications and live updates.
 */

import { useState, useEffect, useCallback, useRef } from 'react';

import { useAuth } from '@/api/authContext';
import { useWebSocketEnhanced } from '@/hooks/useWebSocket';
import type { NotificationResponse } from '@/types/notification';
import type { StudentBalanceResponse } from '@/types/purchase';

interface BalanceWebSocketMessage {
  type: 'balance_update' | 'balance_notification' | 'low_balance_alert' | 'package_expiring';
  data: {
    balance?: StudentBalanceResponse;
    notification?: NotificationResponse;
    remaining_hours?: number;
    days_until_expiry?: number;
    message?: string;
  };
  user_id: number;
  timestamp: string;
}

interface UseBalanceWebSocketOptions {
  /** Enable WebSocket connection */
  enabled?: boolean;
  /** Reconnection interval in milliseconds */
  reconnectInterval?: number;
  /** Maximum reconnection attempts */
  maxReconnectAttempts?: number;
}

interface UseBalanceWebSocketResult {
  /** WebSocket connection status */
  connected: boolean;
  /** Connection error */
  error: string | null;
  /** Latest balance data received via WebSocket */
  latestBalance: StudentBalanceResponse | null;
  /** Latest notification received */
  latestNotification: NotificationResponse | null;
  /** Manual reconnection function */
  reconnect: () => void;
  /** Send a message via WebSocket */
  sendMessage: (message: any) => void;
}

/**
 * Hook for real-time balance updates via WebSocket
 */
export function useBalanceWebSocket(
  options: UseBalanceWebSocketOptions = {}
): UseBalanceWebSocketResult {
  const { enabled = true, reconnectInterval = 5000, maxReconnectAttempts = 5 } = options;

  const { userProfile, token } = useAuth();

  // State
  const [latestBalance, setLatestBalance] = useState<StudentBalanceResponse | null>(null);
  const [latestNotification, setLatestNotification] = useState<NotificationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Refs
  const reconnectAttempts = useRef(0);
  const balanceCallbacks = useRef<((balance: StudentBalanceResponse) => void)[]>([]);
  const notificationCallbacks = useRef<((notification: NotificationResponse) => void)[]>([]);

  // WebSocket URL - currently no balance consumer in backend, fallback to polling
  // TODO: Implement balance WebSocket consumer in backend and enable this
  const wsUrl = null; // Temporarily disabled until backend consumer is implemented

  // Future WebSocket URL when backend consumer is available:
  // const wsUrl = userProfile && token && enabled
  //   ? `ws://localhost:8000/ws/balance/${userProfile.id}/?token=${token}`
  //   : null;

  const {
    isConnected: connected,
    lastMessage,
    sendMessage,
    connect,
    disconnect,
  } = useWebSocketEnhanced(wsUrl, {
    onOpen: () => {
      console.log('Balance WebSocket connected');
      setError(null);
      reconnectAttempts.current = 0;

      // Send initial subscription message
      sendMessage({
        type: 'subscribe',
        data: {
          user_id: userProfile?.id,
          subscription_types: ['balance_updates', 'balance_notifications'],
        },
      });
    },

    onClose: () => {
      console.log('Balance WebSocket disconnected');

      // Attempt reconnection if enabled and under limit
      if (enabled && reconnectAttempts.current < maxReconnectAttempts) {
        setTimeout(() => {
          reconnectAttempts.current++;
          connect();
        }, reconnectInterval);
      }
    },

    onError: error => {
      console.error('Balance WebSocket error:', error);
      setError(error.message || 'WebSocket connection error');
    },

    shouldReconnect: enabled && reconnectAttempts.current < maxReconnectAttempts,
  });

  /**
   * Handle incoming WebSocket messages
   */
  const handleMessage = useCallback(
    (message: BalanceWebSocketMessage) => {
      if (!message || message.user_id !== userProfile?.id) {
        return;
      }

      switch (message.type) {
        case 'balance_update':
          if (message.data.balance) {
            console.log('Received balance update:', message.data.balance);
            setLatestBalance(message.data.balance);

            // Notify registered callbacks
            balanceCallbacks.current.forEach(callback => {
              try {
                callback(message.data.balance!);
              } catch (err) {
                console.error('Error in balance callback:', err);
              }
            });
          }
          break;

        case 'balance_notification':
        case 'low_balance_alert':
        case 'package_expiring':
          if (message.data.notification) {
            console.log('Received balance notification:', message.data.notification);
            setLatestNotification(message.data.notification);

            // Notify registered callbacks
            notificationCallbacks.current.forEach(callback => {
              try {
                callback(message.data.notification!);
              } catch (err) {
                console.error('Error in notification callback:', err);
              }
            });
          }
          break;

        default:
          console.log('Unknown WebSocket message type:', message.type);
      }
    },
    [userProfile?.id]
  );

  /**
   * Process WebSocket messages
   */
  useEffect(() => {
    if (lastMessage) {
      try {
        const parsedMessage = JSON.parse(lastMessage) as BalanceWebSocketMessage;
        handleMessage(parsedMessage);
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err, lastMessage);
      }
    }
  }, [lastMessage, handleMessage]);

  /**
   * Manual reconnection
   */
  const reconnect = useCallback(() => {
    reconnectAttempts.current = 0;
    setError(null);
    disconnect();

    setTimeout(() => {
      connect();
    }, 1000);
  }, [connect, disconnect]);

  return {
    connected,
    error,
    latestBalance,
    latestNotification,
    reconnect,
    sendMessage,
  };
}

/**
 * Hook for subscribing to balance updates
 */
export function useBalanceUpdates(
  onBalanceUpdate?: (balance: StudentBalanceResponse) => void,
  onNotification?: (notification: NotificationResponse) => void
) {
  const { connected, latestBalance, latestNotification } = useBalanceWebSocket();

  // Handle balance updates
  useEffect(() => {
    if (latestBalance && onBalanceUpdate) {
      onBalanceUpdate(latestBalance);
    }
  }, [latestBalance, onBalanceUpdate]);

  // Handle notifications
  useEffect(() => {
    if (latestNotification && onNotification) {
      onNotification(latestNotification);
    }
  }, [latestNotification, onNotification]);

  return {
    connected,
    latestBalance,
    latestNotification,
  };
}

/**
 * Cross-platform WebSocket polyfill
 */
function getWebSocketClass() {
  if (typeof WebSocket !== 'undefined') {
    return WebSocket;
  }

  // React Native
  if (typeof global !== 'undefined' && global.WebSocket) {
    return global.WebSocket;
  }

  // Node.js (for testing)
  try {
    const ws = require('ws');
    return ws;
  } catch (err) {
    console.error('WebSocket not available');
    return null;
  }
}

/**
 * Create a cross-platform WebSocket connection
 */
export function createBalanceWebSocket(
  url: string,
  protocols?: string | string[]
): WebSocket | null {
  const WebSocketClass = getWebSocketClass();

  if (!WebSocketClass) {
    console.error('WebSocket not supported in this environment');
    return null;
  }

  try {
    return new WebSocketClass(url, protocols);
  } catch (err) {
    console.error('Failed to create WebSocket:', err);
    return null;
  }
}
