# React Native Testing Guide

This document outlines the best practices for testing React Native applications in the Aprende Conmigo project.

## Testing Libraries

Our project uses the following testing tools:

- **Jest**: Base test runner and assertion library
- **React Test Renderer**: For rendering React components in tests without a DOM
- **@testing-library/react-native**: For more complex integration tests (note: currently has compatibility issues with our project setup)

## Testing Hierarchy

We follow a standard testing pyramid approach:

1. **Unit Tests**: Test individual functions and components in isolation
2. **Integration Tests**: Test interactions between components
3. **End-to-End Tests**: Test full app workflows (not implemented in this project yet)

## Best Practices

### General Guidelines

- **Keep Tests Fast**: Tests should run quickly to provide rapid feedback
- **Keep Tests Independent**: Tests should not depend on each other
- **Clean Up After Tests**: Always clean up resources in the `afterEach` or `afterAll` block
- **Mock External Dependencies**: Use Jest mocks for API calls, storage, etc.
- **Test Behavior, Not Implementation**: Focus on what the component does, not how it does it

### React Component Testing

We use React Test Renderer for testing components, which provides these advantages:
- Better compatibility with React Native
- Lower memory usage
- More reliable behavior

#### Component Testing Pattern

```typescript
// 1. Import necessary libraries
import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import YourComponent from '../YourComponent';

// 2. Mock dependencies
jest.mock('../dependency', () => ({
  someFunction: jest.fn(),
}));

// 3. Describe the test suite
describe('YourComponent', () => {
  // 4. Setup before each test
  beforeEach(() => {
    jest.clearAllMocks();
  });

  // 5. Clean up after each test
  afterEach(() => {
    if (testRenderer) {
      testRenderer.unmount();
    }
  });

  // 6. Write individual tests
  it('renders correctly', async () => {
    // Render component using act() for async actions
    let testRenderer;
    await act(async () => {
      testRenderer = TestRenderer.create(<YourComponent />);
    });

    // Make assertions
    const instance = testRenderer.root;
    expect(instance.findByType('Text').props.children).toBe('Expected Text');
  });
});
```

### Testing Context Providers

For testing React Context, follow these strategies:

1. **Create a test component** that uses the context
2. **Render the provider with the test component**
3. **Test the behavior** through the test component

```typescript
// Test component that accesses the context
const TestComponent = () => {
  const context = useYourContext();
  return <Text>{context.someValue}</Text>;
};

// Test
it('provides the correct context value', async () => {
  let testRenderer;
  await act(async () => {
    testRenderer = TestRenderer.create(
      <YourContextProvider>
        <TestComponent />
      </YourContextProvider>
    );
  });

  const text = testRenderer.root.findByType('Text');
  expect(text.props.children).toBe('expected value');
});
```

### Testing Async Operations

For async operations, always use `act()` to ensure all updates are processed:

```typescript
it('handles async operations', async () => {
  let testRenderer;
  await act(async () => {
    testRenderer = TestRenderer.create(<AsyncComponent />);
    // Wait for all promises to resolve
    await new Promise(resolve => setTimeout(resolve, 0));
  });

  // Now make assertions after async operations have completed
  expect(mockFunction).toHaveBeenCalled();
});
```

### Memory Management

To avoid memory issues in tests:

1. **Limit test scope**: Test specific functionality rather than trying to test everything at once
2. **Unmount components**: Always call `testRenderer.unmount()` after tests
3. **Clean up subscriptions**: Ensure any event listeners or subscriptions are cleared
4. **Split large test files**: Break down large test files into smaller, focused files

### Mocking

Properly mock external dependencies:

```typescript
// Mock module
jest.mock('../api', () => ({
  fetchData: jest.fn(),
}));

// Set up mock return values
beforeEach(() => {
  (api.fetchData as jest.Mock).mockResolvedValue({ data: 'mocked data' });
});
```

## Troubleshooting Common Issues

- **Memory Issues**: If tests run out of memory, try increasing Node memory with `NODE_OPTIONS=--max-old-space-size=4096`
- **Test Renderer vs. React Native Testing Library**: Prefer React Test Renderer for compatibility
- **Infinite loops**: Check for state updates that might cause infinite re-renders
- **Async timing issues**: Make sure to use `act()` and wait for promises to resolve

## Testing Commands

- Run all tests: `npm test`
- Run specific test file: `npx jest path/to/test.tsx`
- Run tests with more memory: `NODE_OPTIONS=--max-old-space-size=4096 npx jest`
- Update snapshots: `npx jest -u`
