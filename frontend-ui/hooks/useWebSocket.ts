import AsyncStorage from '@react-native-async-storage/async-storage';
import { useEffect, useRef, useState, useCallback } from 'react';
import { WebSocketClient } from '@/services/websocket/WebSocketClient';
import { AsyncStorageAuthProvider } from '@/services/websocket/auth/AsyncStorageAuthProvider';
import { WebSocketConfig, ConnectionState } from '@/services/websocket/types';

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
  const clientRef = useRef<WebSocketClient | null>(null);

  const connect = useCallback(async () => {
    try {
      if (clientRef.current) {
        clientRef.current.dispose();
      }

      const config: WebSocketConfig = {
        url,
        auth: new AsyncStorageAuthProvider(),
        reconnection: {
          strategy: 'exponential',
          initialDelay: 1000,
          maxDelay: 30000,
          backoffFactor: 2,
          maxAttempts: 5
        }
      };

      const client = new WebSocketClient(config);
      clientRef.current = client;

      // Set up event handlers
      client.onConnect(() => {
        setIsConnected(true);
        setError(null);
        onOpen?.();
      });

      client.onDisconnect(() => {
        setIsConnected(false);
        onClose?.();
      });

      client.onError((err) => {
        setError(err.message);
        onError?.(new Event('error'));
      });

      if (onMessage) {
        client.onMessage(onMessage);
      }

      await client.connect();
    } catch (err) {
      console.error('Error creating WebSocket connection:', err);
      setError('Failed to create WebSocket connection');
    }
  }, [url, onMessage, onError, onOpen, onClose]);

  const disconnect = useCallback(() => {
    if (clientRef.current) {
      clientRef.current.disconnect();
      setIsConnected(false);
    }
  }, []);

  const sendMessage = useCallback((message: WebSocketMessage) => {
    if (clientRef.current && isConnected) {
      try {
        clientRef.current.send(message);
      } catch (err) {
        console.error('Error sending WebSocket message:', err);
      }
    } else {
      console.warn('WebSocket not connected, cannot send message');
    }
  }, [isConnected]);

  useEffect(() => {
    if (shouldConnect) {
      connect();
    }

    return () => {
      if (clientRef.current) {
        clientRef.current.dispose();
      }
    };
  }, [shouldConnect, channelName, connect]);

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
  const clientRef = useRef<WebSocketClient | null>(null);

  const { onOpen, onClose, onError, shouldReconnect = true } = options;

  const connect = useCallback(async () => {
    if (!wsUrl) {
      console.warn('No WebSocket URL provided');
      return;
    }

    try {
      if (clientRef.current) {
        clientRef.current.dispose();
      }

      const config: WebSocketConfig = {
        url: wsUrl,
        reconnection: shouldReconnect ? {
          strategy: 'exponential',
          initialDelay: 1000,
          maxDelay: 30000,
          backoffFactor: 2,
          maxAttempts: 5
        } : undefined
      };

      const client = new WebSocketClient(config);
      clientRef.current = client;

      // Set up event handlers
      client.onConnect(() => {
        setIsConnected(true);
        onOpen?.();
      });

      client.onDisconnect(() => {
        setIsConnected(false);
        onClose?.();
      });

      client.onError((err) => {
        onError?.(new Event('error'));
      });

      // Handle messages - store raw data as string
      client.onMessage((message) => {
        setLastMessage(typeof message === 'string' ? message : JSON.stringify(message));
      });

      await client.connect();
    } catch (err) {
      console.error('Error creating WebSocket connection:', err);
      onError?.(new Event('error'));
    }
  }, [wsUrl, onOpen, onClose, onError, shouldReconnect]);

  const disconnect = useCallback(() => {
    if (clientRef.current) {
      clientRef.current.disconnect();
      setIsConnected(false);
    }
  }, []);

  const sendMessage = useCallback((message: any) => {
    if (clientRef.current && isConnected) {
      try {
        // Convert to WebSocket message format if needed
        const wsMessage = typeof message === 'string' 
          ? { type: 'raw', data: message }
          : (message.type ? message : { type: 'message', data: message });
        
        clientRef.current.send(wsMessage);
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
      if (clientRef.current) {
        clientRef.current.dispose();
      }
    };
  }, [wsUrl, connect]);

  return {
    isConnected,
    lastMessage,
    sendMessage,
    connect,
    disconnect,
  };
}

export default useWebSocket;
