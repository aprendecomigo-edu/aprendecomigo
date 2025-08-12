/**
 * WebSocket Types - Core type definitions for the modular WebSocket architecture
 * 
 * This module defines all interfaces and types used across the WebSocket
 * services, providing a clean separation of concerns and type safety.
 */

export interface WebSocketMessage {
  type: string;
  [key: string]: any;
}

export interface AuthProvider {
  getToken(): Promise<string | null>;
  onAuthError(): void;
}

export interface MessageHandler {
  (message: WebSocketMessage): Promise<void> | void;
}

export interface MessageFilter {
  (message: WebSocketMessage): boolean;
}

export interface MessageHandlerOptions {
  filter?: MessageFilter;
  priority?: number;
  once?: boolean;
}

export interface MessageMiddleware {
  (message: WebSocketMessage): WebSocketMessage | Promise<WebSocketMessage>;
}

export interface ReconnectionConfig {
  strategy: 'exponential' | 'linear' | 'fixed';
  initialDelay?: number;
  maxDelay?: number;
  backoffFactor?: number;
  increment?: number;
  interval?: number;
  maxAttempts?: number;
}

export interface ReconnectionStrategy {
  shouldReconnect(event: CloseEvent, attempts: number): boolean;
  getNextDelay(attempts: number): number;
  reset(): void;
}

export interface WebSocketConfig {
  url: string;
  reconnection?: ReconnectionConfig;
  auth?: AuthProvider;
  messageHandlers?: Map<string, MessageHandler>;
}

export enum ConnectionState {
  DISCONNECTED = 'disconnected',
  CONNECTING = 'connecting',
  CONNECTED = 'connected',
  RECONNECTING = 'reconnecting',
  ERROR = 'error'
}

export type WebSocketState = ConnectionState;

export interface ConnectionEventMap {
  'statechange': [ConnectionState];
  'message': [WebSocketMessage];
  'error': [Error];
  'open': [];
  'close': [CloseEvent];
}

export interface MessageDispatcherMetrics {
  totalMessages: number;
  successfulDispatches: number;
  failedDispatches: number;
  handlerExecutionTime: Record<string, number>;
  averageExecutionTime: number;
}

export interface EventEmitterInterface {
  on<K extends keyof ConnectionEventMap>(
    event: K,
    listener: (...args: ConnectionEventMap[K]) => void
  ): void;
  off<K extends keyof ConnectionEventMap>(
    event: K,
    listener: (...args: ConnectionEventMap[K]) => void
  ): void;
  emit<K extends keyof ConnectionEventMap>(
    event: K,
    ...args: ConnectionEventMap[K]
  ): void;
}

// Legacy hook compatibility types
export interface UseWebSocketOptions {
  onOpen?: () => void;
  onClose?: () => void;
  onError?: (error: Event) => void;
  shouldReconnect?: boolean;
}

export interface UseWebSocketResult {
  isConnected: boolean;
  lastMessage: string | null;
  sendMessage: (message: any) => void;
  connect: () => void;
  disconnect: () => void;
}

// Hook config compatibility for migration
export interface HookConfig {
  url: string;
  onMessage?: (message: WebSocketMessage) => void;
  onError?: (error: Event) => void;
  onOpen?: () => void;
  onClose?: () => void;
  shouldConnect?: boolean;
}