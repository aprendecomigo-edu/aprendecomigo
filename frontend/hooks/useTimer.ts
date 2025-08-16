/**
 * Reusable Timer Hooks for Proper Memory Cleanup
 *
 * These hooks provide safe timer management with automatic cleanup on unmount
 * to prevent memory leaks and unexpected behavior.
 */

import { useRef, useEffect, useCallback } from 'react';

export interface TimerRef {
  current: NodeJS.Timeout | null;
}

/**
 * Hook for managing setTimeout with automatic cleanup
 */
export function useTimeout(
  callback: () => void,
  delay: number | null,
  deps: React.DependencyList = [],
): {
  start: () => void;
  clear: () => void;
  isActive: () => boolean;
} {
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const callbackRef = useRef(callback);

  // Update callback ref when callback changes
  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  const clear = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  }, []);

  const start = useCallback(() => {
    clear(); // Clear any existing timeout

    if (delay !== null && delay >= 0) {
      timeoutRef.current = setTimeout(() => {
        timeoutRef.current = null;
        callbackRef.current();
      }, delay);
    }
  }, [delay, clear, ...deps]);

  const isActive = useCallback(() => {
    return timeoutRef.current !== null;
  }, []);

  // Auto-start when delay changes (if delay is provided)
  useEffect(() => {
    if (delay !== null) {
      start();
    }
    return clear;
  }, [delay, start, clear]);

  // Cleanup on unmount
  useEffect(() => {
    return clear;
  }, [clear]);

  return { start, clear, isActive };
}

/**
 * Hook for managing setInterval with automatic cleanup
 */
export function useInterval(
  callback: () => void,
  delay: number | null,
  deps: React.DependencyList = [],
): {
  start: () => void;
  stop: () => void;
  isRunning: () => boolean;
} {
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const callbackRef = useRef(callback);

  // Update callback ref when callback changes
  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  const stop = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  const start = useCallback(() => {
    stop(); // Clear any existing interval

    if (delay !== null && delay > 0) {
      intervalRef.current = setInterval(() => {
        callbackRef.current();
      }, delay);
    }
  }, [delay, stop, ...deps]);

  const isRunning = useCallback(() => {
    return intervalRef.current !== null;
  }, []);

  // Auto-start when delay changes (if delay is provided)
  useEffect(() => {
    if (delay !== null) {
      start();
    }
    return stop;
  }, [delay, start, stop]);

  // Cleanup on unmount
  useEffect(() => {
    return stop;
  }, [stop]);

  return { start, stop, isRunning };
}

/**
 * Hook for managing multiple timers with centralized cleanup
 */
export function useTimerManager(): {
  setTimeout: (callback: () => void, delay: number) => TimerRef;
  setInterval: (callback: () => void, delay: number) => TimerRef;
  clearTimeout: (timerRef: TimerRef) => void;
  clearInterval: (timerRef: TimerRef) => void;
  clearAll: () => void;
} {
  const timersRef = useRef<Set<TimerRef>>(new Set());

  const clearTimer = useCallback((timerRef: TimerRef, clearFn: typeof clearTimeout) => {
    if (timerRef.current) {
      clearFn(timerRef.current);
      timerRef.current = null;
    }
    timersRef.current.delete(timerRef);
  }, []);

  const setTimeout = useCallback((callback: () => void, delay: number): TimerRef => {
    const timerRef: TimerRef = { current: null };

    timerRef.current = global.setTimeout(() => {
      callback();
      timersRef.current.delete(timerRef);
      timerRef.current = null;
    }, delay);

    timersRef.current.add(timerRef);
    return timerRef;
  }, []);

  const setInterval = useCallback((callback: () => void, delay: number): TimerRef => {
    const timerRef: TimerRef = { current: null };

    timerRef.current = global.setInterval(callback, delay);
    timersRef.current.add(timerRef);
    return timerRef;
  }, []);

  const clearTimeout = useCallback(
    (timerRef: TimerRef) => {
      clearTimer(timerRef, global.clearTimeout);
    },
    [clearTimer],
  );

  const clearInterval = useCallback(
    (timerRef: TimerRef) => {
      clearTimer(timerRef, global.clearInterval);
    },
    [clearTimer],
  );

  const clearAll = useCallback(() => {
    timersRef.current.forEach(timerRef => {
      if (timerRef.current) {
        // Try both clear functions since we don't know the timer type
        try {
          global.clearTimeout(timerRef.current);
        } catch {
          // If clearTimeout fails, try clearInterval
          global.clearInterval(timerRef.current);
        }
        timerRef.current = null;
      }
    });
    timersRef.current.clear();
  }, []);

  // Cleanup all timers on unmount
  useEffect(() => {
    return clearAll;
  }, [clearAll]);

  return {
    setTimeout,
    setInterval,
    clearTimeout,
    clearInterval,
    clearAll,
  };
}

/**
 * Hook for polling with automatic cleanup and exponential backoff
 */
export function usePolling(
  callback: () => Promise<void> | void,
  options: {
    interval: number;
    enabled?: boolean;
    maxRetries?: number;
    backoffMultiplier?: number;
    maxInterval?: number;
  },
): {
  start: () => void;
  stop: () => void;
  isPolling: () => boolean;
  retryCount: number;
} {
  const {
    interval,
    enabled = true,
    maxRetries = 5,
    backoffMultiplier = 2,
    maxInterval = 60000,
  } = options;

  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const retryCountRef = useRef(0);
  const callbackRef = useRef(callback);
  const mountedRef = useRef(true);

  // Update callback ref
  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  const stop = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    retryCountRef.current = 0;
  }, []);

  const start = useCallback(() => {
    if (!mountedRef.current) return;

    stop(); // Clear any existing interval

    const poll = async () => {
      if (!mountedRef.current) return;

      try {
        await callbackRef.current();
        retryCountRef.current = 0; // Reset retry count on success
      } catch (error) {
        console.error('Polling error:', error);
        retryCountRef.current++;

        // Stop polling if max retries reached
        if (retryCountRef.current >= maxRetries) {
          console.error(`Polling stopped after ${maxRetries} failed attempts`);
          stop();
          return;
        }

        // Apply exponential backoff
        const nextInterval = Math.min(
          interval * Math.pow(backoffMultiplier, retryCountRef.current - 1),
          maxInterval,
        );

        // Restart with new interval
        stop();
        if (mountedRef.current) {
          intervalRef.current = setTimeout(() => {
            if (mountedRef.current) {
              intervalRef.current = setInterval(poll, nextInterval);
            }
          }, nextInterval);
        }
        return;
      }
    };

    // Start polling immediately, then at intervals
    poll();
    intervalRef.current = setInterval(poll, interval);
  }, [interval, maxRetries, backoffMultiplier, maxInterval, stop]);

  const isPolling = useCallback(() => {
    return intervalRef.current !== null;
  }, []);

  // Auto-start/stop based on enabled flag
  useEffect(() => {
    if (enabled) {
      start();
    } else {
      stop();
    }
  }, [enabled, start, stop]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      mountedRef.current = false;
      stop();
    };
  }, [stop]);

  return {
    start,
    stop,
    isPolling,
    retryCount: retryCountRef.current,
  };
}
