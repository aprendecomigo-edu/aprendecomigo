/**
 * Centralized WebSocket Manager Hook
 *
 * This hook provides a centralized WebSocket management system to prevent memory leaks,
 * coordinate reconnection strategies, and handle proper cleanup on component unmount.
 */

import { useRef, useEffect, useCallback, useState } from 'react';

interface WebSocketConfig {
  url: string;
  protocols?: string | string[];
  maxReconnectAttempts?: number;
  reconnectInterval?: number;
  heartbeatInterval?: number;
}

interface WebSocketManagerState {
  isConnected: boolean;
  isConnecting: boolean;
  error: string | null;
  reconnectAttempts: number;
}

interface WebSocketManager {
  state: WebSocketManagerState;
  connect: () => void;
  disconnect: () => void;
  send: (message: any) => boolean;
  addMessageHandler: (handler: (message: any) => void) => () => void;
  addConnectionHandler: (handler: (connected: boolean) => void) => () => void;
  addErrorHandler: (handler: (error: Error) => void) => () => void;
}

export function useWebSocketManager(config: WebSocketConfig): WebSocketManager {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const heartbeatTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const messageHandlersRef = useRef<Set<(message: any) => void>>(new Set());
  const connectionHandlersRef = useRef<Set<(connected: boolean) => void>>(new Set());
  const errorHandlersRef = useRef<Set<(error: Error) => void>>(new Set());
  const mountedRef = useRef(true);

  const [state, setState] = useState<WebSocketManagerState>({
    isConnected: false,
    isConnecting: false,
    error: null,
    reconnectAttempts: 0,
  });

  const {
    url,
    protocols,
    maxReconnectAttempts = 5,
    reconnectInterval = 1000,
    heartbeatInterval = 30000,
  } = config;

  // Clear all timeouts
  const clearTimeouts = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (heartbeatTimeoutRef.current) {
      clearTimeout(heartbeatTimeoutRef.current);
      heartbeatTimeoutRef.current = null;
    }
  }, []);

  // Setup heartbeat to keep connection alive
  const setupHeartbeat = useCallback(() => {
    if (!heartbeatInterval || heartbeatInterval <= 0) return;

    heartbeatTimeoutRef.current = setTimeout(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'ping' }));
        setupHeartbeat(); // Schedule next heartbeat
      }
    }, heartbeatInterval);
  }, [heartbeatInterval]);

  // Handle reconnection with exponential backoff
  const scheduleReconnect = useCallback(() => {
    if (!mountedRef.current) return;
    if (state.reconnectAttempts >= maxReconnectAttempts) {
      setState(prev => ({
        ...prev,
        error: `Max reconnection attempts (${maxReconnectAttempts}) reached`,
      }));
      return;
    }

    const delay = Math.min(
      reconnectInterval * Math.pow(2, state.reconnectAttempts),
      30000, // Max 30 seconds
    );

    reconnectTimeoutRef.current = setTimeout(() => {
      if (mountedRef.current) {
        setState(prev => ({ ...prev, reconnectAttempts: prev.reconnectAttempts + 1 }));
        connect();
      }
    }, delay);
  }, [state.reconnectAttempts, maxReconnectAttempts, reconnectInterval]);

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (!mountedRef.current) return;
    if (
      wsRef.current?.readyState === WebSocket.CONNECTING ||
      wsRef.current?.readyState === WebSocket.OPEN
    ) {
      return;
    }

    setState(prev => ({ ...prev, isConnecting: true, error: null }));

    try {
      const ws = new WebSocket(url, protocols);
      wsRef.current = ws;

      ws.onopen = () => {
        if (!mountedRef.current) return;

        setState(prev => ({
          ...prev,
          isConnected: true,
          isConnecting: false,
          reconnectAttempts: 0,
          error: null,
        }));

        // Notify connection handlers
        connectionHandlersRef.current.forEach(handler => {
          try {
            handler(true);
          } catch (err) {
            console.error('Error in connection handler:', err);
          }
        });

        setupHeartbeat();
      };

      ws.onmessage = event => {
        if (!mountedRef.current) return;

        try {
          const message = JSON.parse(event.data);

          // Skip heartbeat responses
          if (message.type === 'pong') return;

          // Notify message handlers
          messageHandlersRef.current.forEach(handler => {
            try {
              handler(message);
            } catch (err) {
              console.error('Error in message handler:', err);
            }
          });
        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
        }
      };

      ws.onclose = event => {
        if (!mountedRef.current) return;

        clearTimeouts();
        setState(prev => ({ ...prev, isConnected: false, isConnecting: false }));

        // Notify connection handlers
        connectionHandlersRef.current.forEach(handler => {
          try {
            handler(false);
          } catch (err) {
            console.error('Error in connection handler:', err);
          }
        });

        // Only reconnect if it wasn't a normal closure
        if (event.code !== 1000 && event.code !== 1001) {
          scheduleReconnect();
        }
      };

      ws.onerror = event => {
        if (!mountedRef.current) return;

        const error = new Error('WebSocket connection error');
        setState(prev => ({ ...prev, error: error.message, isConnecting: false }));

        // Notify error handlers
        errorHandlersRef.current.forEach(handler => {
          try {
            handler(error);
          } catch (err) {
            console.error('Error in error handler:', err);
          }
        });
      };
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Failed to create WebSocket');
      setState(prev => ({ ...prev, error: error.message, isConnecting: false }));

      errorHandlersRef.current.forEach(handler => {
        try {
          handler(error);
        } catch (handlerErr) {
          console.error('Error in error handler:', handlerErr);
        }
      });
    }
  }, [url, protocols, setupHeartbeat, scheduleReconnect]);

  // Disconnect WebSocket
  const disconnect = useCallback(() => {
    clearTimeouts();

    if (wsRef.current) {
      wsRef.current.close(1000, 'User disconnected');
      wsRef.current = null;
    }

    setState(prev => ({
      ...prev,
      isConnected: false,
      isConnecting: false,
      reconnectAttempts: 0,
    }));
  }, [clearTimeouts]);

  // Send message
  const send = useCallback((message: any): boolean => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      return false;
    }

    try {
      wsRef.current.send(JSON.stringify(message));
      return true;
    } catch (err) {
      console.error('Error sending WebSocket message:', err);
      return false;
    }
  }, []);

  // Add message handler
  const addMessageHandler = useCallback((handler: (message: any) => void) => {
    messageHandlersRef.current.add(handler);

    // Return cleanup function
    return () => {
      messageHandlersRef.current.delete(handler);
    };
  }, []);

  // Add connection handler
  const addConnectionHandler = useCallback((handler: (connected: boolean) => void) => {
    connectionHandlersRef.current.add(handler);

    return () => {
      connectionHandlersRef.current.delete(handler);
    };
  }, []);

  // Add error handler
  const addErrorHandler = useCallback((handler: (error: Error) => void) => {
    errorHandlersRef.current.add(handler);

    return () => {
      errorHandlersRef.current.delete(handler);
    };
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      mountedRef.current = false;
      clearTimeouts();

      if (wsRef.current) {
        wsRef.current.close(1000, 'Component unmounted');
        wsRef.current = null;
      }

      // Clear all handler sets
      messageHandlersRef.current.clear();
      connectionHandlersRef.current.clear();
      errorHandlersRef.current.clear();
    };
  }, [clearTimeouts]);

  return {
    state,
    connect,
    disconnect,
    send,
    addMessageHandler,
    addConnectionHandler,
    addErrorHandler,
  };
}
