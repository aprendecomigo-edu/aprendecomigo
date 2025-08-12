/**
 * Reconnection Strategies - Modular reconnection logic with different backoff algorithms
 * 
 * This module provides different reconnection strategies that can be configured
 * and swapped out as needed, following the Strategy pattern.
 */

import { ReconnectionStrategy, ReconnectionConfig } from '../types';

export abstract class BaseReconnectionStrategy implements ReconnectionStrategy {
  protected maxAttempts: number;

  constructor(config: ReconnectionConfig) {
    this.maxAttempts = config.maxAttempts ?? 5;
    this.validateConfig(config);
  }

  abstract getNextDelay(attempts: number): number;

  shouldReconnect(event: CloseEvent, attempts: number): boolean {
    // Don't reconnect if max attempts exceeded
    if (attempts >= this.maxAttempts) {
      return false;
    }

    // Don't reconnect for normal closures
    if (event.code === 1000) {
      return false;
    }

    // Don't reconnect for authentication/authorization errors
    if (event.code >= 4001 && event.code <= 4999) {
      return false;
    }

    // Reconnect for all other cases (network errors, server errors, etc.)
    return true;
  }

  reset(): void {
    // Reset any internal state (implemented by subclasses if needed)
  }

  protected validateConfig(config: ReconnectionConfig): void {
    if (config.maxAttempts !== undefined && config.maxAttempts <= 0) {
      throw new Error('Max attempts must be positive');
    }
  }
}

export class ExponentialBackoffStrategy extends BaseReconnectionStrategy {
  private initialDelay: number;
  private maxDelay: number;
  private backoffFactor: number;

  constructor(config: ReconnectionConfig) {
    super(config);
    this.initialDelay = config.initialDelay ?? 1000;
    this.maxDelay = config.maxDelay ?? 30000;
    this.backoffFactor = config.backoffFactor ?? 2;
    this.validateExponentialConfig();
  }

  getNextDelay(attempts: number): number {
    if (attempts < 0) {
      attempts = 0;
    }

    const delay = this.initialDelay * Math.pow(this.backoffFactor, attempts);
    return Math.min(delay, this.maxDelay);
  }

  private validateExponentialConfig(): void {
    if (this.initialDelay <= 0) {
      throw new Error('Initial delay must be positive');
    }
    if (this.backoffFactor <= 1) {
      throw new Error('Backoff factor must be greater than 1');
    }
  }
}

export class LinearBackoffStrategy extends BaseReconnectionStrategy {
  private initialDelay: number;
  private maxDelay: number;
  private increment: number;

  constructor(config: ReconnectionConfig) {
    super(config);
    this.initialDelay = config.initialDelay ?? 1000;
    this.maxDelay = config.maxDelay ?? 30000;
    this.increment = config.increment ?? 1000;
    this.validateLinearConfig();
  }

  getNextDelay(attempts: number): number {
    if (attempts < 0) {
      attempts = 0;
    }

    const delay = this.initialDelay + (attempts * this.increment);
    return Math.min(delay, this.maxDelay);
  }

  private validateLinearConfig(): void {
    if (this.initialDelay <= 0) {
      throw new Error('Initial delay must be positive');
    }
    if (this.increment <= 0) {
      throw new Error('Increment must be positive');
    }
  }
}

export class FixedIntervalStrategy extends BaseReconnectionStrategy {
  private interval: number;

  constructor(config: ReconnectionConfig) {
    super(config);
    this.interval = config.interval ?? 5000;
    this.validateFixedConfig();
  }

  getNextDelay(attempts: number): number {
    return this.interval;
  }

  private validateFixedConfig(): void {
    if (this.interval <= 0) {
      throw new Error('Interval must be positive');
    }
  }
}

// Strategy factory
export class ReconnectionStrategyFactory {
  static create(config: ReconnectionConfig): ReconnectionStrategy {
    // Provide defaults
    const configWithDefaults: ReconnectionConfig = {
      initialDelay: 1000,
      maxDelay: 30000,
      backoffFactor: 2,
      increment: 1000,
      interval: 5000,
      maxAttempts: 5,
      ...config
    };

    switch (config.strategy) {
      case 'exponential':
        return new ExponentialBackoffStrategy(configWithDefaults);
      case 'linear':
        return new LinearBackoffStrategy(configWithDefaults);
      case 'fixed':
        return new FixedIntervalStrategy(configWithDefaults);
      default:
        throw new Error(`Unknown strategy type: ${config.strategy}`);
    }
  }
}

// Export the factory method as a static method
export { ReconnectionStrategyFactory as ReconnectionStrategy };