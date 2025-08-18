/**
 * WebSocket Mock Setup for Jest Tests
 * 
 * This file sets up comprehensive WebSocket mocking infrastructure
 * for testing real-time features and WebSocket integrations.
 */

import { MockWebSocket } from '../utils/websocket-test-utils';

// Mock WebSocketClient before it's imported anywhere
class MockWebSocketClient {
  private ws: MockWebSocket | null = null;
  private config: any;
  private listeners: Map<string, Function[]> = new Map();
  private disposed = false;
  private messageHandlers: Map<string, Function[]> = new Map();

  constructor(config: any) {
    this.config = config;
    
    // Register this instance
    const clients = (global as any).__mockWebSocketClients || [];
    clients.push(this);
    (global as any).__mockWebSocketClients = clients;
    (global as any).__lastMockWebSocketClient = this;
  }

  async connect(): Promise<void> {
    if (this.disposed) {
      throw new Error('WebSocketClient has been disposed');
    }

    // Check for global connection failure
    if ((global as any).__webSocketGlobalFailure) {
      this.emit('error', new Error('Connection failed'));
      return;
    }

    // Check for auth token if auth provider is configured
    if (this.config.auth) {
      const token = await this.config.auth.getToken();
      if (!token) {
        this.emit('error', new Error('No authentication token found'));
        return;
      }
      // Append token to URL
      const url = `${this.config.url}?token=${token}`;
      this.ws = new MockWebSocket(url);
    } else {
      this.ws = new MockWebSocket(this.config.url);
    }

    // Setup WebSocket event handlers
    this.ws.onopen = () => {
      this.emit('connect');
    };

    this.ws.onclose = (event) => {
      this.emit('disconnect');
      this.emit('close', event);
    };

    this.ws.onerror = (error) => {
      this.emit('error', error);
    };

    this.ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        this.emit('message', message);
        
        // Handle message routing to specific handlers
        const handlers = this.messageHandlers.get(message.type) || [];
        const universalHandlers = this.messageHandlers.get('*') || [];
        [...handlers, ...universalHandlers].forEach(handler => {
          try {
            handler(message);
          } catch (err) {
            console.error('Message handler error:', err);
          }
        });
      } catch (err) {
        console.error('Error parsing WebSocket message:', err);
      }
    };

    // Trigger connection immediately for testing
    if (this.ws) {
      this.ws.triggerOpen();
    }
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  send(message: any): void {
    if (this.ws && this.ws.readyState === MockWebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      throw new Error('WebSocket not connected');
    }
  }

  dispose(): void {
    this.disconnect();
    this.listeners.clear();
    this.messageHandlers.clear();
    this.disposed = true;
  }

  getState(): string {
    if (!this.ws) return 'DISCONNECTED';
    switch (this.ws.readyState) {
      case MockWebSocket.CONNECTING: return 'CONNECTING';
      case MockWebSocket.OPEN: return 'CONNECTED';
      case MockWebSocket.CLOSING: return 'DISCONNECTING';
      case MockWebSocket.CLOSED: return 'DISCONNECTED';
      default: return 'DISCONNECTED';
    }
  }

  // Event emitter methods
  on(event: string, listener: Function): void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event)!.push(listener);
  }

  emit(event: string, ...args: any[]): void {
    const listeners = this.listeners.get(event);
    if (listeners) {
      listeners.forEach(listener => {
        try {
          listener(...args);
        } catch (error) {
          console.error(`Error in event listener for ${event}:`, error);
        }
      });
    }
  }

  // Backwards compatibility methods
  onConnect(listener: () => void): void {
    this.on('connect', listener);
  }

  onDisconnect(listener: () => void): void {
    this.on('disconnect', listener);
  }

  onMessage(listener: Function): void {
    if (!this.messageHandlers.has('*')) {
      this.messageHandlers.set('*', []);
    }
    this.messageHandlers.get('*')!.push(listener);
  }

  onError(listener: (error: Error) => void): void {
    this.on('error', listener);
  }

  // Test helper methods
  simulateMessage(message: any): void {
    if (this.ws) {
      this.ws.simulateMessage(JSON.stringify(message));
    }
  }

  simulateError(error?: Event): void {
    if (this.ws) {
      this.ws.simulateError(error);
    }
  }

  simulateNetworkFailure(): void {
    if (this.ws) {
      this.ws.simulateNetworkFailure();
    }
  }

  simulateNetworkFailureWithReconnectBlocking(): void {
    if (this.ws) {
      this.ws.simulateNetworkFailureWithReconnectBlocking();
    }
  }

  getWebSocket(): MockWebSocket | null {
    return this.ws;
  }

  getSentMessages(): string[] {
    return this.ws ? this.ws.getSentMessages() : [];
  }

  getMessageQueue(): Array<{ data: any; timestamp: number }> {
    return this.ws ? this.ws.getMessageQueue() : [];
  }
}

// Mock the entire WebSocketClient module
jest.mock('@/services/websocket/WebSocketClient', () => ({
  WebSocketClient: MockWebSocketClient,
}));

// Mock AsyncStorageAuthProvider
jest.mock('@/services/websocket/auth/AsyncStorageAuthProvider', () => ({
  AsyncStorageAuthProvider: jest.fn().mockImplementation(() => ({
    getToken: jest.fn().mockResolvedValue('mock-token'),
    onAuthError: jest.fn(),
  })),
}));

// Export for use in tests
export { MockWebSocketClient };