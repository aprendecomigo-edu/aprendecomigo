import { useCallback, useEffect, useRef } from 'react';

/**
 * Custom hook for debouncing function calls
 * Delays the execution of a function until after a specified delay has passed
 * since the last time it was invoked.
 *
 * @param callback - The function to debounce
 * @param delay - The delay in milliseconds
 * @param dependencies - Dependencies that should trigger a reset of the debounced function
 * @returns A debounced version of the callback function
 */
export function useDebounce<T extends (...args: any[]) => any>(
  callback: T,
  delay: number,
  dependencies: any[] = []
): [T, () => void, () => void] {
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const callbackRef = useRef<T>(callback);
  const argsRef = useRef<Parameters<T>>();

  // Update callback ref when dependencies change
  useEffect(() => {
    callbackRef.current = callback;
  }, [callback, ...dependencies]);

  // Cancel pending execution
  const cancel = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  }, []);

  // Execute immediately (flush)
  const flush = useCallback(() => {
    cancel();
    if (argsRef.current) {
      callbackRef.current(...argsRef.current);
    }
  }, [cancel]);

  // Debounced function
  const debouncedCallback = useCallback(
    ((...args: Parameters<T>) => {
      argsRef.current = args;
      cancel();

      timeoutRef.current = setTimeout(() => {
        callbackRef.current(...args);
        timeoutRef.current = null;
      }, delay);
    }) as T,
    [delay, cancel]
  );

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      cancel();
    };
  }, [cancel]);

  return [debouncedCallback, cancel, flush];
}

/**
 * Hook for debouncing state values
 * Returns a debounced version of the value that only updates after the delay
 *
 * @param value - The value to debounce
 * @param delay - The delay in milliseconds
 * @returns The debounced value
 */
export function useDebouncedValue<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    timeoutRef.current = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [value, delay]);

  return debouncedValue;
}

/**
 * Hook for debouncing API calls with loading state
 * Provides loading state and error handling for debounced async operations
 *
 * @param asyncCallback - The async function to debounce
 * @param delay - The delay in milliseconds
 * @param dependencies - Dependencies that should trigger a reset
 * @returns Object with debounced function, loading state, error, and control functions
 */
export function useDebouncedAsync<T extends (...args: any[]) => Promise<any>>(
  asyncCallback: T,
  delay: number,
  dependencies: any[] = []
): {
  debouncedFn: T;
  isLoading: boolean;
  error: Error | null;
  cancel: () => void;
  flush: () => Promise<void>;
} {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const wrappedCallback = useCallback(
    async (...args: Parameters<T>) => {
      // Cancel any ongoing request
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      // Create new abort controller
      abortControllerRef.current = new AbortController();

      setIsLoading(true);
      setError(null);

      try {
        const result = await asyncCallback(...args);

        // Only update state if not aborted
        if (!abortControllerRef.current.signal.aborted) {
          setIsLoading(false);
        }

        return result;
      } catch (err) {
        // Only update state if not aborted
        if (!abortControllerRef.current.signal.aborted) {
          const error = err instanceof Error ? err : new Error('Unknown error occurred');
          setError(error);
          setIsLoading(false);
          throw error;
        }
      }
    },
    [asyncCallback, ...dependencies]
  );

  const [debouncedFn, cancel, flush] = useDebounce(wrappedCallback as T, delay, dependencies);

  const enhancedCancel = useCallback(() => {
    cancel();
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setIsLoading(false);
    setError(null);
  }, [cancel]);

  const enhancedFlush = useCallback(async () => {
    try {
      await flush();
    } catch (error) {
      // Error is already handled in wrappedCallback
      console.error('Debounced async flush error:', error);
    }
  }, [flush]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  return {
    debouncedFn,
    isLoading,
    error,
    cancel: enhancedCancel,
    flush: enhancedFlush,
  };
}

/**
 * Hook for smart auto-save functionality
 * Only triggers save when data actually changes and user stops editing
 *
 * @param saveFunction - The function to call for saving
 * @param data - The data to save
 * @param options - Configuration options
 * @returns Object with save controls and status
 */
export function useSmartAutoSave<T>(
  saveFunction: (data: T) => Promise<void>,
  data: T,
  options: {
    delay?: number;
    enabled?: boolean;
    dependencies?: any[];
    onSaveStart?: () => void;
    onSaveSuccess?: () => void;
    onSaveError?: (error: Error) => void;
  } = {}
): {
  isSaving: boolean;
  error: Error | null;
  forceSave: () => Promise<void>;
  cancelSave: () => void;
  hasUnsavedChanges: boolean;
} {
  const {
    delay = 2000,
    enabled = true,
    dependencies = [],
    onSaveStart,
    onSaveSuccess,
    onSaveError,
  } = options;

  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const lastSavedDataRef = useRef<T>(data);
  const isMountedRef = useRef(true);

  const wrappedSaveFunction = useCallback(
    async (dataToSave: T) => {
      if (!enabled || !isMountedRef.current) return;

      onSaveStart?.();

      try {
        await saveFunction(dataToSave);

        if (isMountedRef.current) {
          lastSavedDataRef.current = dataToSave;
          setHasUnsavedChanges(false);
          onSaveSuccess?.();
        }
      } catch (error) {
        if (isMountedRef.current) {
          const saveError = error instanceof Error ? error : new Error('Save failed');
          onSaveError?.(saveError);
          throw saveError;
        }
      }
    },
    [saveFunction, enabled, onSaveStart, onSaveSuccess, onSaveError]
  );

  const { debouncedFn, isLoading, error, cancel, flush } = useDebouncedAsync(
    wrappedSaveFunction,
    delay,
    dependencies
  );

  // Check if data has changed
  useEffect(() => {
    const hasChanged = JSON.stringify(data) !== JSON.stringify(lastSavedDataRef.current);

    if (hasChanged && enabled) {
      setHasUnsavedChanges(true);
      debouncedFn(data);
    }
  }, [data, enabled, debouncedFn]);

  // Cleanup on unmount
  useEffect(() => {
    isMountedRef.current = true;

    return () => {
      isMountedRef.current = false;
      cancel();
    };
  }, [cancel]);

  return {
    isSaving: isLoading,
    error,
    forceSave: () => flush(),
    cancelSave: cancel,
    hasUnsavedChanges,
  };
}

// Re-export useState for useDebouncedValue
import { useState } from 'react';
