/**
 * ConnectionManager - Pure WebSocket Connection Handling
 *
 * This class handles the raw WebSocket connection lifecycle with authentication
 * support. It delegates auth and reconnection to injected services, following
 * the Single Responsibility Principle.
 */

import {
  AuthProvider,
  WebSocketConfig,
  ConnectionState,
  WebSocketMessage,
  EventEmitterInterface,
} from '../types';

export class ConnectionManager implements EventEmitterInterface {
  private ws: WebSocket | null = null;
  private config: WebSocketConfig;
  private state: ConnectionState = ConnectionState.DISCONNECTED;
  private listeners: Map<string, Function[]> = new Map();

  constructor(config: WebSocketConfig) {
    this.config = config;
  }

  async connect(): Promise<void> {
    if (this.ws && this.ws.readyState !== WebSocket.CLOSED) {
      throw new Error('Connection already exists');
    }

    this.setState(ConnectionState.CONNECTING);

    try {
      const authenticatedUrl = await this.buildAuthenticatedUrl();
      this.ws = new WebSocket(authenticatedUrl);
      this.attachListeners();
    } catch (error) {
      this.setState(ConnectionState.ERROR);
      if (this.config.auth) {
        this.config.auth.onAuthError();
      }
      throw error;
    }
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close(1000, 'User disconnected');
      this.ws = null;
    }
    this.setState(ConnectionState.DISCONNECTED);
  }

  send(message: WebSocketMessage): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error('Cannot send message: WebSocket is not connected');
    }

    this.ws.send(JSON.stringify(message));
  }

  getState(): ConnectionState {
    return this.state;
  }

  private async buildAuthenticatedUrl(): Promise<string> {
    let url = this.config.url;

    if (this.config.auth) {
      const token = await this.config.auth.getToken();
      if (token) {
        const separator = url.includes('?') ? '&' : '?';
        url = `${url}${separator}token=${token}`;
      }
    }

    return url;
  }

  private attachListeners(): void {
    if (!this.ws) return;

    this.ws.onopen = event => {
      this.setState(ConnectionState.CONNECTED);
      this.emit('open');
    };

    this.ws.onclose = event => {
      this.setState(ConnectionState.DISCONNECTED);
      this.emit('close', event);
    };

    this.ws.onerror = event => {
      this.setState(ConnectionState.ERROR);
      this.emit('error', new Error('WebSocket connection error'));
    };

    this.ws.onmessage = event => {
      try {
        const message = JSON.parse(event.data);
        this.emit('message', message);
      } catch (error) {
        this.emit('error', new Error(`Failed to parse message: ${event.data}`));
      }
    };
  }

  private setState(newState: ConnectionState): void {
    if (this.state !== newState) {
      this.state = newState;
      this.emit('statechange', newState);
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
          console.error(`Error in event listener for ${eventName}:`, error);
        }
      });
    }
  }
}
