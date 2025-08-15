/**
 * WebSocketClient - Unified WebSocket Client Integration
 *
 * This class integrates ConnectionManager, ReconnectionStrategy, and MessageDispatcher
 * to provide a unified interface replacing the monolithic useWebSocket hook.
 */

import { ConnectionManager } from './connection/ConnectionManager';
import { MessageDispatcher } from './messaging/MessageDispatcher';
import { ReconnectionStrategy, ExponentialBackoffStrategy } from './reconnection/strategies';
import {
  WebSocketConfig,
  ConnectionState,
  WebSocketMessage,
  MessageHandler,
  MessageHandlerOptions,
  ReconnectionConfig,
  HookConfig,
  EventEmitterInterface,
} from './types';

export class WebSocketClient implements EventEmitterInterface {
  private connectionManager: ConnectionManager;
  private messageDispatcher: MessageDispatcher;
  private reconnectionStrategy: any;
  private config: WebSocketConfig;
  private reconnectTimeoutId: NodeJS.Timeout | null = null;
  private reconnectAttempts: number = 0;
  private disposed: boolean = false;
  private listeners: Map<string, Function[]> = new Map();

  constructor(config: WebSocketConfig) {
    this.validateConfig(config);
    this.config = this.mergeWithDefaults(config);

    this.connectionManager = new ConnectionManager(this.config);
    this.messageDispatcher = new MessageDispatcher();

    // Create reconnection strategy if config is provided
    if (this.config.reconnection) {
      this.reconnectionStrategy = new ExponentialBackoffStrategy(this.config.reconnection);
    }

    this.setupEventIntegration();
  }

  async connect(): Promise<void> {
    if (this.disposed) {
      throw new Error('WebSocketClient has been disposed');
    }

    // Prevent concurrent connections
    const currentState = this.connectionManager.getState();
    if (currentState === ConnectionState.CONNECTING || currentState === ConnectionState.CONNECTED) {
      return;
    }

    try {
      await this.connectionManager.connect();
    } catch (error) {
      throw error;
    }
  }

  disconnect(): void {
    this.ensureNotDisposed();

    if (this.reconnectTimeoutId) {
      clearTimeout(this.reconnectTimeoutId);
      this.reconnectTimeoutId = null;
    }

    this.connectionManager.disconnect();
    this.reconnectAttempts = 0;
  }

  send(message: WebSocketMessage): void {
    this.ensureNotDisposed();
    this.connectionManager.send(message);
  }

  isConnected(): boolean {
    return this.connectionManager.getState() === ConnectionState.CONNECTED;
  }

  getConnectionState(): ConnectionState {
    return this.connectionManager.getState();
  }

  addMessageHandler(
    messageType: string,
    handler: MessageHandler,
    options?: MessageHandlerOptions
  ): void {
    this.ensureNotDisposed();
    this.messageDispatcher.addHandler(messageType, handler, options);
  }

  removeMessageHandler(messageType: string, handler: MessageHandler): void {
    this.ensureNotDisposed();
    this.messageDispatcher.removeHandler(messageType, handler);
  }

  // Backwards compatibility methods
  onConnect(listener: () => void): void {
    this.on('connect', listener);
  }

  onDisconnect(listener: () => void): void {
    this.on('disconnect', listener);
  }

  onMessage(listener: MessageHandler): void {
    this.messageDispatcher.addHandler('*', listener);
  }

  onError(listener: (error: Error) => void): void {
    this.on('error', listener);
  }

  updateConfig(partialConfig: Partial<WebSocketConfig>): void {
    this.ensureNotDisposed();
    this.validatePartialConfig(partialConfig);

    this.config = { ...this.config, ...partialConfig };

    // Recreate connection manager with new config if needed
    if (partialConfig.url || partialConfig.auth) {
      const wasConnected = this.isConnected();
      this.disconnect();
      this.connectionManager = new ConnectionManager(this.config);
      this.setupEventIntegration();

      if (wasConnected) {
        this.connect().catch(error => {
          if (__DEV__) {
            console.error('Failed to reconnect after config update:', error);
          }
        });
      }
    }

    // Update reconnection strategy if needed
    if (partialConfig.reconnection) {
      this.reconnectionStrategy = this.createReconnectionStrategy();
    }
  }

  getConfig(): WebSocketConfig {
    return { ...this.config };
  }

  dispose(): void {
    if (this.disposed) return;

    this.disconnect();
    this.messageDispatcher.clearAllHandlers();
    this.listeners.clear();
    this.disposed = true;
  }

  // Static factory methods for backwards compatibility
  static fromHookConfig(hookConfig: HookConfig): WebSocketClient {
    const config: WebSocketConfig = {
      url: hookConfig.url,
      reconnection: {
        strategy: 'exponential',
        initialDelay: 1000,
        maxDelay: 30000,
        backoffFactor: 2,
        maxAttempts: 5,
      },
    };

    const client = new WebSocketClient(config);

    // Setup hook-style callbacks
    if (hookConfig.onMessage) {
      client.onMessage(hookConfig.onMessage);
    }
    if (hookConfig.onError) {
      client.onError(hookConfig.onError);
    }
    if (hookConfig.onOpen) {
      client.onConnect(hookConfig.onOpen);
    }
    if (hookConfig.onClose) {
      client.onDisconnect(hookConfig.onClose);
    }

    // Auto-connect if requested
    if (hookConfig.shouldConnect) {
      client.connect().catch(error => {
        if (__DEV__) {
          console.error('Auto-connect failed:', error);
        }
      });
    }

    return client;
  }

  private mergeWithDefaults(config: WebSocketConfig): WebSocketConfig {
    const defaultReconnection: ReconnectionConfig = {
      strategy: 'exponential',
      initialDelay: 1000,
      maxDelay: 30000,
      backoffFactor: 2,
      maxAttempts: 5,
    };

    return {
      ...config,
      reconnection: { ...defaultReconnection, ...config.reconnection },
    };
  }

  private validateConfig(config: WebSocketConfig): void {
    if (!config.url || typeof config.url !== 'string') {
      throw new Error('Invalid WebSocket URL');
    }

    try {
      new URL(config.url.replace('ws://', 'http://').replace('wss://', 'https://'));
    } catch {
      throw new Error('Invalid WebSocket URL format');
    }

    if (
      config.reconnection &&
      config.reconnection.maxAttempts !== undefined &&
      config.reconnection.maxAttempts < 0
    ) {
      throw new Error('Max attempts must be non-negative');
    }
  }

  private validatePartialConfig(config: Partial<WebSocketConfig>): void {
    if (config.url !== undefined) {
      if (!config.url || typeof config.url !== 'string') {
        throw new Error('Invalid WebSocket URL');
      }
    }

    if (config.auth !== undefined && config.auth === null) {
      throw new Error('Auth provider cannot be null');
    }

    if (config.reconnection?.maxAttempts !== undefined && config.reconnection.maxAttempts < 0) {
      throw new Error('Max attempts must be non-negative');
    }
  }

  private createReconnectionStrategy(): any {
    if (!this.config.reconnection) {
      return null;
    }
    return ReconnectionStrategy.create(this.config.reconnection);
  }

  private setupEventIntegration(): void {
    // Forward connection events
    this.connectionManager.on('statechange', (state: ConnectionState) => {
      if (state === ConnectionState.CONNECTED) {
        this.reconnectAttempts = 0;
        this.reconnectionStrategy?.reset();
        this.emit('connect');
      } else if (state === ConnectionState.DISCONNECTED) {
        this.emit('disconnect');
      } else if (state === ConnectionState.ERROR) {
        this.emit('error', new Error('Connection error'));
      }
    });

    // Handle close events for reconnection
    this.connectionManager.on('close', (event: CloseEvent) => {
      if (this.reconnectionStrategy?.shouldReconnect(event, this.reconnectAttempts)) {
        const delay = this.reconnectionStrategy.getNextDelay(this.reconnectAttempts);

        this.reconnectTimeoutId = setTimeout(async () => {
          this.reconnectAttempts++;
          try {
            await this.connect();
          } catch (error) {
            if (__DEV__) {
              console.error('Reconnection failed:', error);
            }
          }
        }, delay);
      }
    });

    // Forward messages to dispatcher
    this.connectionManager.on('message', async (message: WebSocketMessage) => {
      try {
        await this.messageDispatcher.dispatch(message);
      } catch (error) {
        if (__DEV__) {
          console.error('Message dispatch error:', error);
        }
        this.emit('error', new Error('Message dispatch error'));
      }
    });

    // Forward connection errors
    this.connectionManager.on('error', (error: Error) => {
      this.emit('error', error);
    });
  }

  private ensureNotDisposed(): void {
    if (this.disposed) {
      throw new Error('WebSocketClient has been disposed');
    }
  }

  // EventEmitter implementation
  on<K extends keyof any>(event: K, listener: Function): void {
    const eventName = event as string;
    if (!this.listeners.has(eventName)) {
      this.listeners.set(eventName, []);
    }
    this.listeners.get(eventName)!.push(listener);
  }

  off<K extends keyof any>(event: K, listener: Function): void {
    const eventName = event as string;
    const listeners = this.listeners.get(eventName);
    if (listeners) {
      const index = listeners.indexOf(listener);
      if (index > -1) {
        listeners.splice(index, 1);
      }
    }
  }

  emit<K extends keyof any>(event: K, ...args: any[]): void {
    const eventName = event as string;
    const listeners = this.listeners.get(eventName);
    if (listeners) {
      listeners.forEach(listener => {
        try {
          listener(...args);
        } catch (error) {
          if (__DEV__) {
            console.error(`Error in event listener for ${eventName}:`, error);
          }
        }
      });
    }
  }
}
