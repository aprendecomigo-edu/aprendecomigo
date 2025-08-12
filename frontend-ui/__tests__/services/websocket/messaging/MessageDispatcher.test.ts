/**
 * Tests for WebSocket MessageDispatcher - Message Routing and Handling
 * 
 * This tests the new modular architecture where MessageDispatcher handles message
 * routing to specific handlers based on message types, replacing the monolithic
 * message handling in useWebSocket.
 * 
 * EXPECTED TO FAIL: These tests validate the new architecture that hasn't been implemented yet.
 */

import { MessageDispatcher } from '@/services/websocket/messaging/MessageDispatcher';
import { MessageHandler, MessageFilter, WebSocketMessage } from '@/services/websocket/types';

describe('MessageDispatcher', () => {
  let dispatcher: MessageDispatcher;
  let mockHandler1: jest.MockedFunction<MessageHandler>;
  let mockHandler2: jest.MockedFunction<MessageHandler>;
  let mockHandler3: jest.MockedFunction<MessageHandler>;

  beforeEach(() => {
    dispatcher = new MessageDispatcher();
    mockHandler1 = jest.fn();
    mockHandler2 = jest.fn();
    mockHandler3 = jest.fn();
  });

  describe('Handler Registration', () => {
    it('should register handlers for specific message types', () => {
      // Act
      dispatcher.addHandler('user.message', mockHandler1);
      dispatcher.addHandler('system.notification', mockHandler2);

      // Assert
      expect(dispatcher.getHandlers('user.message')).toContain(mockHandler1);
      expect(dispatcher.getHandlers('system.notification')).toContain(mockHandler2);
      expect(dispatcher.getHandlers('user.message')).not.toContain(mockHandler2);
    });

    it('should support multiple handlers for the same message type', () => {
      // Act
      dispatcher.addHandler('chat.message', mockHandler1);
      dispatcher.addHandler('chat.message', mockHandler2);
      dispatcher.addHandler('chat.message', mockHandler3);

      // Assert
      const handlers = dispatcher.getHandlers('chat.message');
      expect(handlers).toContain(mockHandler1);
      expect(handlers).toContain(mockHandler2);
      expect(handlers).toContain(mockHandler3);
      expect(handlers).toHaveLength(3);
    });

    it('should support wildcard patterns for message types', () => {
      // Act
      dispatcher.addHandler('chat.*', mockHandler1);
      dispatcher.addHandler('user.*', mockHandler2);
      dispatcher.addHandler('*', mockHandler3); // Global handler

      // Assert
      expect(dispatcher.getHandlers('chat.message')).toContain(mockHandler1);
      expect(dispatcher.getHandlers('chat.typing')).toContain(mockHandler1);
      expect(dispatcher.getHandlers('user.join')).toContain(mockHandler2);
      expect(dispatcher.getHandlers('system.alert')).toContain(mockHandler3);
      expect(dispatcher.getHandlers('any.message')).toContain(mockHandler3);
    });

    it('should handle overlapping patterns correctly', () => {
      // Arrange
      dispatcher.addHandler('chat.*', mockHandler1);
      dispatcher.addHandler('chat.message', mockHandler2);
      dispatcher.addHandler('*', mockHandler3);

      // Act
      const handlers = dispatcher.getHandlers('chat.message');

      // Assert
      expect(handlers).toContain(mockHandler1); // chat.*
      expect(handlers).toContain(mockHandler2); // chat.message
      expect(handlers).toContain(mockHandler3); // *
      expect(handlers).toHaveLength(3);
    });
  });

  describe('Handler Removal', () => {
    beforeEach(() => {
      dispatcher.addHandler('test.message', mockHandler1);
      dispatcher.addHandler('test.message', mockHandler2);
      dispatcher.addHandler('other.message', mockHandler3);
    });

    it('should remove specific handler from message type', () => {
      // Act
      dispatcher.removeHandler('test.message', mockHandler1);

      // Assert
      const handlers = dispatcher.getHandlers('test.message');
      expect(handlers).not.toContain(mockHandler1);
      expect(handlers).toContain(mockHandler2);
      expect(dispatcher.getHandlers('other.message')).toContain(mockHandler3);
    });

    it('should remove all handlers for a message type', () => {
      // Act
      dispatcher.removeAllHandlers('test.message');

      // Assert
      expect(dispatcher.getHandlers('test.message')).toHaveLength(0);
      expect(dispatcher.getHandlers('other.message')).toContain(mockHandler3);
    });

    it('should clear all handlers', () => {
      // Act
      dispatcher.clearAllHandlers();

      // Assert
      expect(dispatcher.getHandlers('test.message')).toHaveLength(0);
      expect(dispatcher.getHandlers('other.message')).toHaveLength(0);
    });

    it('should handle removal of non-existent handlers gracefully', () => {
      // Act & Assert - Should not throw
      expect(() => {
        dispatcher.removeHandler('test.message', jest.fn());
        dispatcher.removeHandler('non.existent', mockHandler1);
        dispatcher.removeAllHandlers('non.existent');
      }).not.toThrow();
    });
  });

  describe('Message Dispatching', () => {
    beforeEach(() => {
      dispatcher.addHandler('chat.message', mockHandler1);
      dispatcher.addHandler('chat.*', mockHandler2);
      dispatcher.addHandler('*', mockHandler3);
    });

    it('should dispatch messages to appropriate handlers', async () => {
      // Arrange
      const message: WebSocketMessage = {
        type: 'chat.message',
        id: '123',
        content: 'Hello world',
        user: { id: 1, name: 'John' },
        timestamp: Date.now()
      };

      // Act
      await dispatcher.dispatch(message);

      // Assert
      expect(mockHandler1).toHaveBeenCalledWith(message);
      expect(mockHandler2).toHaveBeenCalledWith(message);
      expect(mockHandler3).toHaveBeenCalledWith(message);
    });

    it('should not dispatch to handlers that dont match', async () => {
      // Arrange
      dispatcher.addHandler('user.join', mockHandler1);
      const message: WebSocketMessage = {
        type: 'chat.message',
        content: 'Hello'
      };

      // Act
      await dispatcher.dispatch(message);

      // Assert
      expect(mockHandler1).not.toHaveBeenCalled();
      expect(mockHandler2).toHaveBeenCalledWith(message); // chat.*
      expect(mockHandler3).toHaveBeenCalledWith(message); // *
    });

    it('should handle handler errors gracefully', async () => {
      // Arrange
      const errorHandler = jest.fn().mockRejectedValue(new Error('Handler failed'));
      dispatcher.addHandler('error.test', errorHandler);
      dispatcher.addHandler('error.test', mockHandler1); // Should still be called

      const message: WebSocketMessage = { type: 'error.test', data: 'test' };

      // Act & Assert - Should not throw
      await expect(dispatcher.dispatch(message)).resolves.toBeUndefined();
      expect(errorHandler).toHaveBeenCalledWith(message);
      expect(mockHandler1).toHaveBeenCalledWith(message);
    });

    it('should execute handlers in order of registration', async () => {
      // Arrange
      const executionOrder: number[] = [];
      const handler1 = jest.fn(() => executionOrder.push(1));
      const handler2 = jest.fn(() => executionOrder.push(2));
      const handler3 = jest.fn(() => executionOrder.push(3));

      dispatcher.addHandler('test.order', handler1);
      dispatcher.addHandler('test.order', handler2);
      dispatcher.addHandler('test.order', handler3);

      const message: WebSocketMessage = { type: 'test.order' };

      // Act
      await dispatcher.dispatch(message);

      // Assert
      expect(executionOrder).toEqual([1, 2, 3]);
    });

    it('should support async handlers', async () => {
      // Arrange
      const asyncHandler = jest.fn().mockImplementation(async (message) => {
        await new Promise(resolve => setTimeout(resolve, 10));
        return `Processed: ${message.type}`;
      });

      dispatcher.addHandler('async.test', asyncHandler);
      const message: WebSocketMessage = { type: 'async.test', data: 'test' };

      // Act
      await dispatcher.dispatch(message);

      // Assert
      expect(asyncHandler).toHaveBeenCalledWith(message);
    });
  });

  describe('Message Filtering', () => {
    it('should support filtering based on message content', () => {
      // Arrange
      const filter: MessageFilter = (message) => {
        return message.user?.id === 123;
      };

      dispatcher.addHandler('chat.message', mockHandler1, { filter });
      dispatcher.addHandler('chat.message', mockHandler2); // No filter

      const messageForUser123: WebSocketMessage = {
        type: 'chat.message',
        content: 'Hello',
        user: { id: 123, name: 'John' }
      };

      const messageForUser456: WebSocketMessage = {
        type: 'chat.message',
        content: 'Hello',
        user: { id: 456, name: 'Jane' }
      };

      // Act
      dispatcher.dispatch(messageForUser123);
      dispatcher.dispatch(messageForUser456);

      // Assert
      expect(mockHandler1).toHaveBeenCalledTimes(1);
      expect(mockHandler1).toHaveBeenCalledWith(messageForUser123);
      expect(mockHandler2).toHaveBeenCalledTimes(2);
    });

    it('should support priority-based handling', async () => {
      // Arrange
      const highPriorityHandler = jest.fn();
      const normalPriorityHandler = jest.fn();
      const lowPriorityHandler = jest.fn();

      dispatcher.addHandler('urgent.message', highPriorityHandler, { priority: 10 });
      dispatcher.addHandler('urgent.message', normalPriorityHandler, { priority: 5 });
      dispatcher.addHandler('urgent.message', lowPriorityHandler, { priority: 1 });

      const message: WebSocketMessage = { type: 'urgent.message', data: 'urgent' };

      // Act
      await dispatcher.dispatch(message);

      // Assert - Handlers should be called in priority order
      const callOrder = [
        highPriorityHandler.mock.invocationCallOrder[0],
        normalPriorityHandler.mock.invocationCallOrder[0],
        lowPriorityHandler.mock.invocationCallOrder[0]
      ];

      expect(callOrder).toEqual(callOrder.sort((a, b) => a - b));
    });

    it('should support one-time handlers', async () => {
      // Arrange
      dispatcher.addHandler('one.time', mockHandler1, { once: true });
      dispatcher.addHandler('one.time', mockHandler2); // Regular handler

      const message: WebSocketMessage = { type: 'one.time', data: 'test' };

      // Act
      await dispatcher.dispatch(message);
      await dispatcher.dispatch(message);

      // Assert
      expect(mockHandler1).toHaveBeenCalledTimes(1); // One-time handler
      expect(mockHandler2).toHaveBeenCalledTimes(2); // Regular handler
    });
  });

  describe('Complex Message Routing', () => {
    it('should handle nested message types', async () => {
      // Arrange
      dispatcher.addHandler('classroom.student.join', mockHandler1);
      dispatcher.addHandler('classroom.student.*', mockHandler2);
      dispatcher.addHandler('classroom.*', mockHandler3);

      const message: WebSocketMessage = {
        type: 'classroom.student.join',
        room_id: 'room123',
        student: { id: 456, name: 'Alice' }
      };

      // Act
      await dispatcher.dispatch(message);

      // Assert
      expect(mockHandler1).toHaveBeenCalledWith(message);
      expect(mockHandler2).toHaveBeenCalledWith(message);
      expect(mockHandler3).toHaveBeenCalledWith(message);
    });

    it('should handle message transformation in handlers', async () => {
      // Arrange
      const transformingHandler = jest.fn().mockImplementation((message) => {
        // Transform message and possibly dispatch new messages
        if (message.type === 'raw.data') {
          const transformedMessage: WebSocketMessage = {
            type: 'processed.data',
            originalType: message.type,
            processedContent: `Processed: ${message.content}`,
            timestamp: Date.now()
          };
          dispatcher.dispatch(transformedMessage);
        }
      });

      const processedHandler = jest.fn();

      dispatcher.addHandler('raw.data', transformingHandler);
      dispatcher.addHandler('processed.data', processedHandler);

      const rawMessage: WebSocketMessage = {
        type: 'raw.data',
        content: 'raw content'
      };

      // Act
      await dispatcher.dispatch(rawMessage);

      // Assert
      expect(transformingHandler).toHaveBeenCalledWith(rawMessage);
      expect(processedHandler).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'processed.data',
          originalType: 'raw.data',
          processedContent: 'Processed: raw content'
        })
      );
    });

    it('should support middleware for message preprocessing', async () => {
      // Arrange
      const middleware = jest.fn().mockImplementation((message) => {
        // Add metadata to all messages
        return {
          ...message,
          processedAt: Date.now(),
          middleware: 'test'
        };
      });

      dispatcher.addMiddleware(middleware);
      dispatcher.addHandler('test.message', mockHandler1);

      const originalMessage: WebSocketMessage = {
        type: 'test.message',
        content: 'original'
      };

      // Act
      await dispatcher.dispatch(originalMessage);

      // Assert
      expect(middleware).toHaveBeenCalledWith(originalMessage);
      expect(mockHandler1).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'test.message',
          content: 'original',
          processedAt: expect.any(Number),
          middleware: 'test'
        })
      );
    });
  });

  describe('Performance and Metrics', () => {
    it('should track handler execution metrics', async () => {
      // Arrange
      const slowHandler = jest.fn().mockImplementation(async () => {
        await new Promise(resolve => setTimeout(resolve, 50));
      });

      dispatcher.addHandler('performance.test', slowHandler);
      dispatcher.enableMetrics(true);

      const message: WebSocketMessage = { type: 'performance.test' };

      // Act
      await dispatcher.dispatch(message);

      // Assert
      const metrics = dispatcher.getMetrics();
      expect(metrics.totalMessages).toBe(1);
      expect(metrics.handlerExecutionTime['performance.test']).toBeGreaterThan(40);
      expect(metrics.successfulDispatches).toBe(1);
      expect(metrics.failedDispatches).toBe(0);
    });

    it('should handle high-frequency message dispatching efficiently', async () => {
      // Arrange
      dispatcher.addHandler('high.frequency', mockHandler1);
      const messages: WebSocketMessage[] = Array.from({ length: 1000 }, (_, i) => ({
        type: 'high.frequency',
        id: i,
        data: `message-${i}`
      }));

      const startTime = Date.now();

      // Act
      await Promise.all(messages.map(message => dispatcher.dispatch(message)));

      // Assert
      const endTime = Date.now();
      const executionTime = endTime - startTime;

      expect(mockHandler1).toHaveBeenCalledTimes(1000);
      expect(executionTime).toBeLessThan(1000); // Should process 1000 messages in less than 1 second
    });

    it('should limit handler execution queue to prevent memory leaks', async () => {
      // Arrange
      const blockingHandler = jest.fn().mockImplementation(() => {
        return new Promise(() => {}); // Never resolves
      });

      dispatcher.addHandler('blocking.test', blockingHandler);
      dispatcher.setMaxQueueSize(10);

      // Act
      const messages = Array.from({ length: 20 }, (_, i) => ({ type: 'blocking.test', id: i }));
      const dispatchPromises = messages.map(message => dispatcher.dispatch(message));

      // Wait a bit for queue to fill
      await new Promise(resolve => setTimeout(resolve, 50));

      // Assert
      expect(dispatcher.getQueueSize()).toBeLessThanOrEqual(10);
      
      // Cleanup
      dispatchPromises.forEach(promise => promise.catch(() => {}));
    });
  });

  describe('Error Handling and Recovery', () => {
    it('should continue processing other handlers when one fails', async () => {
      // Arrange
      const failingHandler = jest.fn().mockRejectedValue(new Error('Handler failed'));
      const successHandler = jest.fn().mockResolvedValue('success');

      dispatcher.addHandler('error.test', failingHandler);
      dispatcher.addHandler('error.test', successHandler);

      const message: WebSocketMessage = { type: 'error.test' };

      // Act
      await dispatcher.dispatch(message);

      // Assert
      expect(failingHandler).toHaveBeenCalledWith(message);
      expect(successHandler).toHaveBeenCalledWith(message);
    });

    it('should provide error callback for handler failures', async () => {
      // Arrange
      const errorCallback = jest.fn();
      const failingHandler = jest.fn().mockRejectedValue(new Error('Test error'));

      dispatcher.onHandlerError(errorCallback);
      dispatcher.addHandler('error.test', failingHandler);

      const message: WebSocketMessage = { type: 'error.test' };

      // Act
      await dispatcher.dispatch(message);

      // Assert
      expect(errorCallback).toHaveBeenCalledWith(
        expect.any(Error),
        message,
        failingHandler
      );
    });

    it('should validate message format before dispatching', async () => {
      // Arrange
      dispatcher.addHandler('*', mockHandler1);

      const invalidMessages = [
        null,
        undefined,
        'string message',
        { data: 'no type field' },
        { type: null },
        { type: '' }
      ] as any[];

      // Act & Assert
      for (const invalidMessage of invalidMessages) {
        await expect(dispatcher.dispatch(invalidMessage)).rejects.toThrow('Invalid message format');
      }

      expect(mockHandler1).not.toHaveBeenCalled();
    });
  });
});