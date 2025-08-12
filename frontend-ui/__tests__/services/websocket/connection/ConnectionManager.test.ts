/**
 * Tests for WebSocket ConnectionManager - Pure Connection Handling
 * 
 * This tests the new modular architecture where ConnectionManager only handles 
 * WebSocket connection lifecycle, delegating auth and reconnection to injected services.
 * 
 * EXPECTED TO FAIL: These tests validate the new architecture that hasn't been implemented yet.
 */

import { ConnectionManager } from '@/services/websocket/connection/ConnectionManager';
import { AuthProvider, WebSocketConfig, ConnectionState } from '@/services/websocket/types';

// Mock WebSocket for testing
class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  public readyState = MockWebSocket.CONNECTING;
  public onopen: ((event: Event) => void) | null = null;
  public onclose: ((event: CloseEvent) => void) | null = null;
  public onerror: ((event: Event) => void) | null = null;
  public onmessage: ((event: MessageEvent) => void) | null = null;

  private listeners: { [key: string]: ((event: any) => void)[] } = {};

  constructor(public url: string) {}

  send(data: string): void {
    if (this.readyState !== MockWebSocket.OPEN) {
      throw new Error('WebSocket is not open');
    }
  }

  close(code?: number, reason?: string): void {
    this.readyState = MockWebSocket.CLOSING;
    setTimeout(() => {
      this.readyState = MockWebSocket.CLOSED;
      const closeEvent = new CloseEvent('close', { code: code || 1000, reason: reason || '' });
      this.onclose?.(closeEvent);
    }, 0);
  }

  addEventListener(type: string, listener: (event: any) => void): void {
    if (!this.listeners[type]) {
      this.listeners[type] = [];
    }
    this.listeners[type].push(listener);
  }

  removeEventListener(type: string, listener: (event: any) => void): void {
    if (this.listeners[type]) {
      const index = this.listeners[type].indexOf(listener);
      if (index > -1) {
        this.listeners[type].splice(index, 1);
      }
    }
  }

  // Test helper methods
  simulateOpen(): void {
    this.readyState = MockWebSocket.OPEN;
    const event = new Event('open');
    this.onopen?.(event);
    this.listeners['open']?.forEach(listener => listener(event));
  }

  simulateMessage(data: string): void {
    if (this.readyState === MockWebSocket.OPEN) {
      const event = new MessageEvent('message', { data });
      this.onmessage?.(event);
      this.listeners['message']?.forEach(listener => listener(event));
    }
  }

  simulateError(): void {
    const event = new Event('error');
    this.onerror?.(event);
    this.listeners['error']?.forEach(listener => listener(event));
  }

  simulateClose(code: number = 1000, reason: string = ''): void {
    this.readyState = MockWebSocket.CLOSED;
    const closeEvent = new CloseEvent('close', { code, reason });
    this.onclose?.(closeEvent);
    this.listeners['close']?.forEach(listener => listener(closeEvent));
  }
}

// Replace global WebSocket with our mock
(global as any).WebSocket = MockWebSocket;
(global as any).CloseEvent = class extends Event {
  constructor(type: string, init?: { code?: number; reason?: string }) {
    super(type);
    this.code = init?.code || 1000;
    this.reason = init?.reason || '';
  }
  code: number;
  reason: string;
};

describe('ConnectionManager', () => {
  let connectionManager: ConnectionManager;
  let mockAuthProvider: jest.Mocked<AuthProvider>;
  let config: WebSocketConfig;
  let mockWebSocket: MockWebSocket;

  beforeEach(() => {
    jest.clearAllMocks();

    // Mock AuthProvider
    mockAuthProvider = {
      getToken: jest.fn().mockResolvedValue('mock-token'),
      onAuthError: jest.fn(),
    };

    // Test configuration
    config = {
      url: 'ws://localhost:8000/ws/test',
      auth: mockAuthProvider,
    };

    // Create ConnectionManager instance
    connectionManager = new ConnectionManager(config);

    // Capture the created WebSocket instance
    jest.spyOn(global, 'WebSocket').mockImplementation((url: string) => {
      mockWebSocket = new MockWebSocket(url);
      return mockWebSocket as any;
    });
  });

  afterEach(() => {
    connectionManager?.disconnect();
    jest.restoreAllMocks();
  });

  describe('Connection Lifecycle', () => {
    it('should create WebSocket with authenticated URL when connecting', async () => {
      // Act
      await connectionManager.connect();

      // Assert
      expect(mockAuthProvider.getToken).toHaveBeenCalled();
      expect(global.WebSocket).toHaveBeenCalledWith('ws://localhost:8000/ws/test?token=mock-token');
    });

    it('should handle authentication failure gracefully', async () => {
      // Arrange
      mockAuthProvider.getToken.mockRejectedValue(new Error('Auth failed'));

      // Act & Assert
      await expect(connectionManager.connect()).rejects.toThrow('Auth failed');
      expect(mockAuthProvider.onAuthError).toHaveBeenCalled();
    });

    it('should transition to CONNECTING state when connection starts', async () => {
      // Act
      const connectPromise = connectionManager.connect();

      // Assert
      expect(connectionManager.getState()).toBe(ConnectionState.CONNECTING);

      // Cleanup
      mockWebSocket?.simulateOpen();
      await connectPromise;
    });

    it('should transition to CONNECTED state when WebSocket opens', async () => {
      // Arrange
      const connectPromise = connectionManager.connect();

      // Act
      mockWebSocket.simulateOpen();
      await connectPromise;

      // Assert
      expect(connectionManager.getState()).toBe(ConnectionState.CONNECTED);
    });

    it('should transition to DISCONNECTED state when WebSocket closes', async () => {
      // Arrange
      await connectionManager.connect();
      mockWebSocket.simulateOpen();

      // Act
      mockWebSocket.simulateClose();

      // Assert
      expect(connectionManager.getState()).toBe(ConnectionState.DISCONNECTED);
    });

    it('should transition to ERROR state when WebSocket errors', async () => {
      // Arrange
      await connectionManager.connect();

      // Act
      mockWebSocket.simulateError();

      // Assert
      expect(connectionManager.getState()).toBe(ConnectionState.ERROR);
    });
  });

  describe('Message Handling', () => {
    beforeEach(async () => {
      await connectionManager.connect();
      mockWebSocket.simulateOpen();
    });

    it('should send messages when connected', async () => {
      // Arrange
      const mockSend = jest.spyOn(mockWebSocket, 'send');
      const message = { type: 'test', data: 'hello' };

      // Act
      connectionManager.send(message);

      // Assert
      expect(mockSend).toHaveBeenCalledWith(JSON.stringify(message));
    });

    it('should throw error when sending messages while disconnected', async () => {
      // Arrange
      mockWebSocket.simulateClose();

      // Act & Assert
      expect(() => {
        connectionManager.send({ type: 'test' });
      }).toThrow('Cannot send message: WebSocket is not connected');
    });

    it('should emit received messages through event system', async () => {
      // Arrange
      const messageHandler = jest.fn();
      connectionManager.on('message', messageHandler);
      const testMessage = JSON.stringify({ type: 'greeting', content: 'hello' });

      // Act
      mockWebSocket.simulateMessage(testMessage);

      // Assert
      expect(messageHandler).toHaveBeenCalledWith({
        type: 'greeting',
        content: 'hello'
      });
    });

    it('should handle invalid JSON messages gracefully', async () => {
      // Arrange
      const errorHandler = jest.fn();
      connectionManager.on('error', errorHandler);

      // Act
      mockWebSocket.simulateMessage('invalid json');

      // Assert
      expect(errorHandler).toHaveBeenCalledWith(
        expect.objectContaining({
          message: expect.stringContaining('Failed to parse message')
        })
      );
    });
  });

  describe('Event System', () => {
    it('should support event listener registration and removal', async () => {
      // Arrange
      const stateHandler = jest.fn();
      const errorHandler = jest.fn();

      // Act
      connectionManager.on('statechange', stateHandler);
      connectionManager.on('error', errorHandler);

      await connectionManager.connect();
      mockWebSocket.simulateOpen();

      // Assert
      expect(stateHandler).toHaveBeenCalledWith(ConnectionState.CONNECTED);

      // Act - Remove listener
      connectionManager.off('statechange', stateHandler);
      mockWebSocket.simulateClose();

      // Assert - Handler should not be called again
      expect(stateHandler).toHaveBeenCalledTimes(2); // CONNECTING + CONNECTED only
    });

    it('should emit connection events in correct order', async () => {
      // Arrange
      const events: string[] = [];
      connectionManager.on('statechange', (state) => {
        events.push(`state:${state}`);
      });

      // Act
      const connectPromise = connectionManager.connect();
      events.push('connect-called');
      
      mockWebSocket.simulateOpen();
      await connectPromise;
      
      mockWebSocket.simulateClose();

      // Assert
      expect(events).toEqual([
        'connect-called',
        'state:connecting',
        'state:connected',
        'state:disconnected'
      ]);
    });
  });

  describe('Resource Management', () => {
    it('should clean up WebSocket on disconnect', async () => {
      // Arrange
      await connectionManager.connect();
      mockWebSocket.simulateOpen();
      const mockClose = jest.spyOn(mockWebSocket, 'close');

      // Act
      connectionManager.disconnect();

      // Assert
      expect(mockClose).toHaveBeenCalledWith(1000, 'User disconnected');
    });

    it('should prevent multiple simultaneous connections', async () => {
      // Arrange
      const firstConnectPromise = connectionManager.connect();
      mockWebSocket.simulateOpen();
      await firstConnectPromise;

      // Act
      const secondConnectPromise = connectionManager.connect();

      // Assert
      await expect(secondConnectPromise).rejects.toThrow('Connection already exists');
    });

    it('should handle connection cleanup on error', async () => {
      // Arrange
      const stateHandler = jest.fn();
      connectionManager.on('statechange', stateHandler);

      await connectionManager.connect();
      mockWebSocket.simulateOpen();

      // Act
      mockWebSocket.simulateError();

      // Assert
      expect(connectionManager.getState()).toBe(ConnectionState.ERROR);
      expect(stateHandler).toHaveBeenCalledWith(ConnectionState.ERROR);
    });
  });

  describe('Configuration Handling', () => {
    it('should handle missing auth provider gracefully', async () => {
      // Arrange
      const configWithoutAuth: WebSocketConfig = {
        url: 'ws://localhost:8000/ws/test'
      };
      const managerWithoutAuth = new ConnectionManager(configWithoutAuth);

      // Act
      await managerWithoutAuth.connect();

      // Assert
      expect(global.WebSocket).toHaveBeenCalledWith('ws://localhost:8000/ws/test');
    });

    it('should handle URL with existing query parameters', async () => {
      // Arrange
      config.url = 'ws://localhost:8000/ws/test?existing=param';

      // Act
      await connectionManager.connect();

      // Assert
      expect(global.WebSocket).toHaveBeenCalledWith(
        'ws://localhost:8000/ws/test?existing=param&token=mock-token'
      );
    });

    it('should handle auth provider that returns null token', async () => {
      // Arrange
      mockAuthProvider.getToken.mockResolvedValue(null);

      // Act
      await connectionManager.connect();

      // Assert
      expect(global.WebSocket).toHaveBeenCalledWith('ws://localhost:8000/ws/test');
    });
  });

  describe('Separation of Concerns', () => {
    it('should NOT handle reconnection logic internally', async () => {
      // Arrange
      await connectionManager.connect();
      mockWebSocket.simulateOpen();

      // Act - Simulate unexpected close
      mockWebSocket.simulateClose(1006, 'Connection lost');

      // Assert - Should just transition to disconnected, not attempt reconnect
      expect(connectionManager.getState()).toBe(ConnectionState.DISCONNECTED);
      expect(global.WebSocket).toHaveBeenCalledTimes(1); // Only initial connection
    });

    it('should NOT parse message types internally', async () => {
      // Arrange
      const messageHandler = jest.fn();
      connectionManager.on('message', messageHandler);

      await connectionManager.connect();
      mockWebSocket.simulateOpen();

      // Act
      const complexMessage = JSON.stringify({
        type: 'classroom.message',
        room_id: '123',
        user: { id: 1, name: 'test' },
        content: 'Hello world'
      });
      mockWebSocket.simulateMessage(complexMessage);

      // Assert - Should emit raw parsed JSON, not processed message
      expect(messageHandler).toHaveBeenCalledWith({
        type: 'classroom.message',
        room_id: '123',
        user: { id: 1, name: 'test' },
        content: 'Hello world'
      });
    });

    it('should delegate auth errors to auth provider', async () => {
      // Arrange
      mockAuthProvider.getToken.mockRejectedValue(new Error('Token expired'));

      // Act
      try {
        await connectionManager.connect();
      } catch (error) {
        // Expected to fail
      }

      // Assert
      expect(mockAuthProvider.onAuthError).toHaveBeenCalled();
    });
  });
});