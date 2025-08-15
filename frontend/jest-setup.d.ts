// Type definitions for Jest DOM matchers
/// <reference types="@testing-library/jest-dom" />
/// <reference types="@testing-library/jest-native" />

declare global {
  namespace jest {
    interface Matchers<R> {
      toHaveTextContent(text: string | RegExp): R;
      toBeDisabled(): R;
      toBeEnabled(): R;
      toBeVisible(): R;
      toHaveAccessibilityState(expectedState: Record<string, boolean | string>): R;
      toHaveAccessibilityValue(expectedValue: Record<string, string | number>): R;
      toHaveProp(prop: string, value?: any): R;
      toHaveStyle(style: Record<string, any> | Record<string, any>[]): R;
      toBeOnTheScreen(): R;
      toBeBusy(): R;
      toBeChecked(): R;
      toBeCollapsed(): R;
      toBeExpanded(): R;
      toBePartiallyChecked(): R;
      toBeSelected(): R;
    }
  }
}

export {};