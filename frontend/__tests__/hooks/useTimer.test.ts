/**
 * Tests for useTimer hooks to verify memory cleanup functionality
 */

import { renderHook, act } from '@testing-library/react-native';
import { useTimeout, useInterval, useTimerManager } from '@/hooks/useTimer';

// Mock timers
jest.useFakeTimers();

describe('useTimer hooks', () => {
  afterEach(() => {
    jest.clearAllTimers();
  });

  describe('useTimeout', () => {
    test('should execute callback after delay', () => {
      const callback = jest.fn();
      renderHook(() => useTimeout(callback, 1000));

      expect(callback).not.toHaveBeenCalled();
      
      act(() => {
        jest.advanceTimersByTime(1000);
      });
      
      expect(callback).toHaveBeenCalledTimes(1);
    });

    test('should clear timeout on unmount', () => {
      const callback = jest.fn();
      const { unmount } = renderHook(() => useTimeout(callback, 1000));

      unmount();
      
      act(() => {
        jest.advanceTimersByTime(1000);
      });
      
      expect(callback).not.toHaveBeenCalled();
    });

    test('should handle null delay', () => {
      const callback = jest.fn();
      renderHook(() => useTimeout(callback, null));

      act(() => {
        jest.advanceTimersByTime(5000);
      });
      
      expect(callback).not.toHaveBeenCalled();
    });
  });

  describe('useInterval', () => {
    test('should execute callback repeatedly', () => {
      const callback = jest.fn();
      renderHook(() => useInterval(callback, 1000));

      act(() => {
        jest.advanceTimersByTime(3000);
      });
      
      expect(callback).toHaveBeenCalledTimes(3);
    });

    test('should clear interval on unmount', () => {
      const callback = jest.fn();
      const { unmount } = renderHook(() => useInterval(callback, 1000));

      act(() => {
        jest.advanceTimersByTime(1000);
      });
      
      expect(callback).toHaveBeenCalledTimes(1);

      unmount();
      
      act(() => {
        jest.advanceTimersByTime(2000);
      });
      
      expect(callback).toHaveBeenCalledTimes(1);
    });

    test('should handle null delay', () => {
      const callback = jest.fn();
      renderHook(() => useInterval(callback, null));

      act(() => {
        jest.advanceTimersByTime(5000);
      });
      
      expect(callback).not.toHaveBeenCalled();
    });
  });

  describe('useTimerManager', () => {
    test('should clear all timers on clearAll', () => {
      const callback1 = jest.fn();
      const callback2 = jest.fn();
      
      const { result } = renderHook(() => useTimerManager());

      act(() => {
        result.current.setTimeout(callback1, 1000);
        result.current.setInterval(callback2, 500);
      });

      act(() => {
        result.current.clearAll();
        jest.advanceTimersByTime(2000);
      });
      
      expect(callback1).not.toHaveBeenCalled();
      expect(callback2).not.toHaveBeenCalled();
    });

    test('should clear all timers on unmount', () => {
      const callback = jest.fn();
      
      const { result, unmount } = renderHook(() => useTimerManager());

      act(() => {
        result.current.setTimeout(callback, 1000);
      });

      unmount();
      
      act(() => {
        jest.advanceTimersByTime(1000);
      });
      
      expect(callback).not.toHaveBeenCalled();
    });
  });
});