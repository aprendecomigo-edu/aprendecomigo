/**
 * Promise Utilities for Safe Error Handling
 *
 * Provides utilities to improve Promise.all error handling by implementing
 * graceful degradation patterns where partial failures don't crash entire operations.
 */

export interface PromiseResult<T> {
  success: boolean;
  data?: T;
  error?: string;
  index: number;
}

/**
 * Safely executes multiple promises and returns all results, including failures.
 * Failed promises return default values instead of throwing.
 *
 * @param promises Array of promises to execute
 * @param defaultValues Array of default values to use when promises fail
 * @returns Array of results with the same length as input promises
 */
export async function safePromiseAll<T>(promises: Promise<T>[], defaultValues: T[]): Promise<T[]> {
  if (promises.length !== defaultValues.length) {
    throw new Error('promises and defaultValues arrays must have the same length');
  }

  const results = await Promise.allSettled(promises);

  return results.map((result, index) => {
    if (result.status === 'fulfilled') {
      return result.value;
    } else {
      // Log the failure for monitoring
      console.error(`Promise ${index} failed:`, result.reason);
      return defaultValues[index];
    }
  });
}

/**
 * Executes promises with detailed results including success/failure status.
 * Useful when you need to know which specific operations failed.
 *
 * @param promises Array of promises to execute
 * @returns Array of detailed results with success status and error info
 */
export async function safePromiseAllWithResults<T>(
  promises: Promise<T>[]
): Promise<PromiseResult<T>[]> {
  const results = await Promise.allSettled(promises);

  return results.map((result, index) => {
    if (result.status === 'fulfilled') {
      return {
        success: true,
        data: result.value,
        index,
      };
    } else {
      const errorMessage =
        result.reason instanceof Error ? result.reason.message : String(result.reason);

      // Log the failure for monitoring
      console.error(`Promise ${index} failed:`, result.reason);

      return {
        success: false,
        error: errorMessage,
        index,
      };
    }
  });
}

/**
 * Helper to log failed operations for monitoring purposes.
 *
 * @param results Array of Promise.allSettled results
 * @param operationNames Optional array of operation names for better logging
 */
export function logFailedOperations<T>(
  results: PromiseSettledResult<T>[],
  operationNames?: string[]
): void {
  results.forEach((result, index) => {
    if (result.status === 'rejected') {
      const operationName = operationNames?.[index] || `Operation ${index}`;
      console.error(`${operationName} failed:`, result.reason);

      // TODO: In production, send to monitoring service
      // Example: errorTrackingService.logError(operationName, result.reason);
    }
  });
}

/**
 * Executes promises with retry logic for transient failures.
 *
 * @param promiseFactories Array of functions that return promises
 * @param maxRetries Maximum number of retries per promise
 * @param retryDelay Delay between retries in milliseconds
 * @returns Promise.allSettled results with retry attempts
 */
export async function safePromiseAllWithRetry<T>(
  promiseFactories: (() => Promise<T>)[],
  maxRetries = 2,
  retryDelay = 1000
): Promise<PromiseSettledResult<T>[]> {
  const retryPromise = async (factory: () => Promise<T>): Promise<T> => {
    let lastError: any;

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        return await factory();
      } catch (error) {
        lastError = error;

        if (attempt < maxRetries) {
          // Wait before retrying
          await new Promise(resolve => setTimeout(resolve, retryDelay));
          console.warn(`Retrying promise attempt ${attempt + 1}/${maxRetries}`);
        }
      }
    }

    throw lastError;
  };

  const promisesWithRetry = promiseFactories.map(factory => retryPromise(factory));
  return Promise.allSettled(promisesWithRetry);
}

/**
 * Type guard to check if a promise result is fulfilled.
 */
export function isFulfilled<T>(
  result: PromiseSettledResult<T>
): result is PromiseFulfilledResult<T> {
  return result.status === 'fulfilled';
}

/**
 * Type guard to check if a promise result is rejected.
 */
export function isRejected<T>(result: PromiseSettledResult<T>): result is PromiseRejectedResult {
  return result.status === 'rejected';
}
