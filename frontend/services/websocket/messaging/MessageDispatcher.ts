/**
 * MessageDispatcher - Message Routing and Handling
 *
 * This class handles message routing to specific handlers based on message types,
 * supporting wildcard patterns, filters, priorities, and middleware.
 */

import {
  WebSocketMessage,
  MessageHandler,
  MessageHandlerOptions,
  MessageFilter,
  MessageMiddleware,
  MessageDispatcherMetrics,
  EventEmitterInterface,
} from '../types';

interface HandlerEntry {
  handler: MessageHandler;
  options: MessageHandlerOptions;
}

export class MessageDispatcher implements EventEmitterInterface {
  private handlers: Map<string, HandlerEntry[]> = new Map();
  private middleware: MessageMiddleware[] = [];
  private listeners: Map<string, Function[]> = new Map();
  private metrics: MessageDispatcherMetrics = {
    totalMessages: 0,
    successfulDispatches: 0,
    failedDispatches: 0,
    handlerExecutionTime: {},
    averageExecutionTime: 0,
  };
  private metricsEnabled: boolean = false;
  private maxQueueSize: number = 1000;
  private currentQueueSize: number = 0;
  private errorCallback?: (
    error: Error,
    message: WebSocketMessage,
    handler: MessageHandler,
  ) => void;

  addHandler(
    messageType: string,
    handler: MessageHandler,
    options: MessageHandlerOptions = {},
  ): void {
    if (!this.handlers.has(messageType)) {
      this.handlers.set(messageType, []);
    }

    const entry: HandlerEntry = { handler, options };
    const handlers = this.handlers.get(messageType)!;

    // Insert based on priority (higher priority first)
    const priority = options.priority ?? 0;
    const insertIndex = handlers.findIndex(h => (h.options.priority ?? 0) < priority);

    if (insertIndex === -1) {
      handlers.push(entry);
    } else {
      handlers.splice(insertIndex, 0, entry);
    }
  }

  removeHandler(messageType: string, handler: MessageHandler): void {
    const handlers = this.handlers.get(messageType);
    if (handlers) {
      const index = handlers.findIndex(entry => entry.handler === handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
  }

  removeAllHandlers(messageType: string): void {
    this.handlers.delete(messageType);
  }

  clearAllHandlers(): void {
    this.handlers.clear();
  }

  getHandlers(messageType: string): MessageHandler[] {
    const matchingHandlers: MessageHandler[] = [];

    // Find all matching patterns
    for (const [pattern, entries] of this.handlers) {
      if (this.matchesPattern(messageType, pattern)) {
        entries.forEach(entry => matchingHandlers.push(entry.handler));
      }
    }

    return matchingHandlers;
  }

  async dispatch(message: WebSocketMessage): Promise<void> {
    if (!this.isValidMessage(message)) {
      throw new Error('Invalid message format');
    }

    if (this.currentQueueSize >= this.maxQueueSize) {
      if (__DEV__) {
        console.warn('Message dispatch queue is full, dropping message');
      }
      return;
    }

    this.currentQueueSize++;

    try {
      this.metrics.totalMessages++;
      const startTime = Date.now();

      // Apply middleware
      let processedMessage = message;
      for (const middleware of this.middleware) {
        processedMessage = await middleware(processedMessage);
      }

      // Find all matching handlers
      const matchingEntries: HandlerEntry[] = [];

      for (const [pattern, entries] of this.handlers) {
        if (this.matchesPattern(message.type, pattern)) {
          entries.forEach(entry => {
            // Apply filter if present
            if (!entry.options.filter || entry.options.filter(processedMessage)) {
              matchingEntries.push(entry);
            }
          });
        }
      }

      // Sort by priority (already sorted within each type, but need global sort)
      matchingEntries.sort((a, b) => (b.options.priority ?? 0) - (a.options.priority ?? 0));

      // Execute handlers
      const handlersToRemove: { pattern: string; handler: MessageHandler }[] = [];

      for (const entry of matchingEntries) {
        try {
          await entry.handler(processedMessage);

          // Mark for removal if it's a one-time handler
          if (entry.options.once) {
            // Find the pattern this handler belongs to
            for (const [pattern, entries] of this.handlers) {
              if (entries.includes(entry)) {
                handlersToRemove.push({ pattern, handler: entry.handler });
                break;
              }
            }
          }
        } catch (error) {
          this.metrics.failedDispatches++;
          const handlerError =
            error instanceof Error ? error : new Error('Handler execution failed');

          if (this.errorCallback) {
            this.errorCallback(handlerError, processedMessage, entry.handler);
          } else {
            console.error('Handler error:', handlerError);
          }
        }
      }

      // Remove one-time handlers
      handlersToRemove.forEach(({ pattern, handler }) => {
        this.removeHandler(pattern, handler);
      });

      this.metrics.successfulDispatches++;

      // Update metrics
      if (this.metricsEnabled) {
        const executionTime = Date.now() - startTime;
        this.metrics.handlerExecutionTime[message.type] = executionTime;
        this.updateAverageExecutionTime();
      }
    } finally {
      this.currentQueueSize--;
    }
  }

  addMiddleware(middleware: MessageMiddleware): void {
    this.middleware.push(middleware);
  }

  removeMiddleware(middleware: MessageMiddleware): void {
    const index = this.middleware.indexOf(middleware);
    if (index > -1) {
      this.middleware.splice(index, 1);
    }
  }

  enableMetrics(enabled: boolean): void {
    this.metricsEnabled = enabled;
  }

  getMetrics(): MessageDispatcherMetrics {
    return { ...this.metrics };
  }

  setMaxQueueSize(size: number): void {
    this.maxQueueSize = size;
  }

  getQueueSize(): number {
    return this.currentQueueSize;
  }

  onHandlerError(
    callback: (error: Error, message: WebSocketMessage, handler: MessageHandler) => void,
  ): void {
    this.errorCallback = callback;
  }

  private matchesPattern(messageType: string, pattern: string): boolean {
    // Exact match
    if (pattern === messageType) {
      return true;
    }

    // Global wildcard
    if (pattern === '*') {
      return true;
    }

    // Pattern matching with wildcards
    if (pattern.includes('*')) {
      const regexPattern = pattern.replace(/\./g, '\\.').replace(/\*/g, '.*');
      const regex = new RegExp(`^${regexPattern}$`);
      return regex.test(messageType);
    }

    return false;
  }

  private isValidMessage(message: any): message is WebSocketMessage {
    return (
      message &&
      typeof message === 'object' &&
      typeof message.type === 'string' &&
      message.type.length > 0
    );
  }

  private updateAverageExecutionTime(): void {
    const times = Object.values(this.metrics.handlerExecutionTime);
    const sum = times.reduce((acc, time) => acc + time, 0);
    this.metrics.averageExecutionTime = times.length > 0 ? sum / times.length : 0;
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
