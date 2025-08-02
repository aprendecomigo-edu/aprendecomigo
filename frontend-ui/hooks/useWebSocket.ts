import AsyncStorage from '@react-native-async-storage/async-storage';
import { useEffect, useRef, useState, useCallback } from 'react';

interface WebSocketMessage {
  type: string;
  [key: string]: any;
}

interface UseWebSocketProps {
  url: string;
  channelName: string;
  onMessage?: (message: WebSocketMessage) => void;
  onError?: (error: Event) => void;
  onOpen?: () => void;
  onClose?: () => void;
  shouldConnect?: boolean;
}

interface UseWebSocketOptions {
  onOpen?: () => void;
  onClose?: () => void;
  onError?: (error: Event) => void;
  shouldReconnect?: boolean;
}

interface UseWebSocketResult {
  isConnected: boolean;
  lastMessage: string | null;
  sendMessage: (message: any) => void;
  connect: () => void;
  disconnect: () => void;
}

export const useWebSocket = ({
  url,
  channelName,
  onMessage,
  onError,
  onOpen,
  onClose,
  shouldConnect = true,
}: UseWebSocketProps) => {
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 5;

  const connect = async () => {
    try {
      // Get auth token for WebSocket connection
      const token = await AsyncStorage.getItem('auth_token');

      if (!token) {
        setError('No authentication token found');
        return;
      }

      // Create WebSocket URL with token
      const wsUrl = `${url}?token=${token}`;

      console.log('Connecting to WebSocket:', wsUrl);

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setError(null);
        reconnectAttemptsRef.current = 0;
        onOpen?.();
      };

      ws.onmessage = event => {
        try {
          const message = JSON.parse(event.data);
          console.log('WebSocket message received:', message);
          onMessage?.(message);
        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
        }
      };

      ws.onclose = event => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        setIsConnected(false);
        wsRef.current = null;
        onClose?.();

        // Attempt to reconnect if not a normal closure
        if (event.code !== 1000 && reconnectAttemptsRef.current < maxReconnectAttempts) {
          const timeout = Math.pow(2, reconnectAttemptsRef.current) * 1000; // Exponential backoff
          console.log(`Reconnecting in ${timeout}ms (attempt ${reconnectAttemptsRef.current + 1})`);

          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttemptsRef.current++;
            connect();
          }, timeout);
        }
      };

      ws.onerror = event => {
        console.error('WebSocket error:', event);
        setError('WebSocket connection error');
        onError?.(event);
      };
    } catch (err) {
      console.error('Error creating WebSocket connection:', err);
      setError('Failed to create WebSocket connection');
    }
  };

  const disconnect = () => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close(1000, 'User disconnected');
      wsRef.current = null;
    }

    setIsConnected(false);
    reconnectAttemptsRef.current = 0;
  };

  const sendMessage = (message: WebSocketMessage) => {
    if (wsRef.current && isConnected) {
      try {
        wsRef.current.send(JSON.stringify(message));
        console.log('WebSocket message sent:', message);
      } catch (err) {
        console.error('Error sending WebSocket message:', err);
      }
    } else {
      console.warn('WebSocket not connected, cannot send message');
    }
  };

  useEffect(() => {
    if (shouldConnect) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [shouldConnect, channelName]);

  return {
    isConnected,
    error,
    sendMessage,
    connect,
    disconnect,
  };
};

/**
 * Enhanced WebSocket hook that matches the interface expected by useBalanceWebSocket
 * This provides the correct interface for the balance WebSocket implementation
 */
export function useWebSocketEnhanced(
  wsUrl: string | null,
  options: UseWebSocketOptions = {}
): UseWebSocketResult {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 5;

  const {
    onOpen,
    onClose, 
    onError,
    shouldReconnect = true
  } = options;

  const connect = useCallback(async () => {
    if (!wsUrl) {
      console.warn('No WebSocket URL provided');
      return;
    }

    try {
      console.log('Connecting to WebSocket:', wsUrl);

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        reconnectAttemptsRef.current = 0;
        onOpen?.();
      };

      ws.onmessage = event => {
        try {
          console.log('WebSocket message received:', event.data);
          setLastMessage(event.data);
        } catch (err) {
          console.error('Error processing WebSocket message:', err);
        }
      };

      ws.onclose = event => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        setIsConnected(false);
        wsRef.current = null;
        onClose?.();

        // Attempt to reconnect if enabled and not a normal closure
        if (
          shouldReconnect && 
          event.code !== 1000 && 
          reconnectAttemptsRef.current < maxReconnectAttempts
        ) {
          const timeout = Math.pow(2, reconnectAttemptsRef.current) * 1000;
          console.log(`Reconnecting in ${timeout}ms (attempt ${reconnectAttemptsRef.current + 1})`);

          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttemptsRef.current++;
            connect();
          }, timeout);
        }
      };

      ws.onerror = (event) => {
        console.error('WebSocket error:', event);
        onError?.(event);
      };
    } catch (err) {
      console.error('Error creating WebSocket connection:', err);
      onError?.(new Event('error'));
    }
  }, [wsUrl, onOpen, onClose, onError, shouldReconnect]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close(1000, 'User disconnected');
      wsRef.current = null;
    }

    setIsConnected(false);
    reconnectAttemptsRef.current = 0;
  }, []);

  const sendMessage = useCallback((message: any) => {
    if (wsRef.current && isConnected) {
      try {
        const messageStr = typeof message === 'string' ? message : JSON.stringify(message);
        wsRef.current.send(messageStr);
        console.log('WebSocket message sent:', message);
      } catch (err) {
        console.error('Error sending WebSocket message:', err);
      }
    } else {
      console.warn('WebSocket not connected, cannot send message');
    }
  }, [isConnected]);

  // Connect when URL is available
  useEffect(() => {
    if (wsUrl) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [wsUrl, connect, disconnect]);

  return {
    isConnected,
    lastMessage,
    sendMessage,
    connect,
    disconnect,
  };
}

export default useWebSocket;
