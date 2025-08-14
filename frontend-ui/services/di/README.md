# Dependency Injection Infrastructure

## Overview

The Dependency Injection (DI) infrastructure provides a standardized way to manage dependencies in the Aprende Comigo frontend, improving testability and reducing coupling between components.

## Quick Start

### Using Dependencies in Components

```typescript
import { useDependencies } from '@/services/di';

export const MyComponent: React.FC = () => {
  const { authApi, toastService } = useDependencies();
  
  const handleAction = async () => {
    try {
      await authApi.requestEmailCode({ email: 'user@example.com' });
      toastService.showToast('success', 'Code sent!');
    } catch (error) {
      toastService.showToast('error', 'Failed to send code');
    }
  };
  
  return <Button onPress={handleAction}>Send Code</Button>;
};
```

### Testing Components with DI

```typescript
import { render } from '@testing-library/react-native';
import { TestDependencyProvider, createMockDependencies } from '@/services/di/testing';

test('should send verification code', async () => {
  const mockDeps = createMockDependencies();
  mockDeps.authApi.requestEmailCode.mockResolvedValue({ success: true });
  
  const { getByText } = render(
    <TestDependencyProvider dependencies={mockDeps}>
      <MyComponent />
    </TestDependencyProvider>
  );
  
  fireEvent.press(getByText('Send Code'));
  
  await waitFor(() => {
    expect(mockDeps.authApi.requestEmailCode).toHaveBeenCalledWith({ 
      email: 'user@example.com' 
    });
  });
});
```

## Architecture

### Core Components

1. **DependencyContext** - React context that holds dependencies
2. **DependencyProvider** - Provider component that supplies dependencies
3. **useDependencies** - Hook to access dependencies in components
4. **Service Interfaces** - TypeScript interfaces defining service contracts

### Service Types

- **AuthApiService** - Authentication API operations
- **StorageService** - Persistent storage operations
- **AnalyticsService** - Analytics tracking
- **RouterService** - Navigation operations
- **ToastService** - User notifications
- **AuthContextService** - Authentication state management
- **OnboardingApiService** - Onboarding flow operations

## Migration Guide

### Step 1: Identify Dependencies

```typescript
// Before: Direct import
import { requestEmailCode } from '@/api/authApi';

// After: Using DI
const { authApi } = useDependencies();
await authApi.requestEmailCode(params);
```

### Step 2: Update Component

```typescript
// Before
export const SignIn: React.FC = () => {
  const handleSubmit = async () => {
    await requestEmailCode({ email }); // Direct API call
  };
};

// After
export const SignInWithDI: React.FC = () => {
  const { authApi } = useDependencies();
  
  const handleSubmit = async () => {
    await authApi.requestEmailCode({ email }); // Via DI
  };
};
```

### Step 3: Update Tests

```typescript
// Before: Complex mocking
jest.mock('@/api/authApi');

// After: Simple dependency injection
const mockDeps = createMockDependencies();
mockDeps.authApi.requestEmailCode = jest.fn();
```

## Testing Utilities

### createMockDependencies()
Creates a complete set of mock dependencies with Jest mocks.

### MockDependencyBuilder
Fluent API for building custom mock dependencies:

```typescript
const deps = new MockDependencyBuilder()
  .withAuthApi(customAuthMock)
  .withToastService(customToastMock)
  .build();
```

### TestDependencyProvider
Test-specific provider component:

```typescript
<TestDependencyProvider 
  dependencies={mockDeps}
  overrides={{ authApi: customAuthApi }}
>
  <ComponentUnderTest />
</TestDependencyProvider>
```

## Best Practices

1. **Always use interfaces** - Define clear contracts for services
2. **Inject at the highest level needed** - Don't inject in every component
3. **Use factories for complex services** - Encapsulate initialization logic
4. **Mock at the service level** - Test components in isolation
5. **Gradually migrate** - No need to refactor everything at once

## Environment Configuration

The DI system automatically configures services based on the environment:

- **Development**: Uses mock services with console logging
- **Test**: Uses Jest mocks for complete control
- **Production**: Uses real API implementations

## Troubleshooting

### "useDependencies must be used within a DependencyProvider"

Ensure your component is wrapped with DependencyProvider or TestDependencyProvider.

### TypeScript errors with service methods

Check that the service interface matches the implementation in `types.ts`.

### Tests failing after migration

Ensure you're providing all required dependencies in your test setup.

## Future Enhancements

- [ ] Lazy loading of services
- [ ] Service lifecycle management (initialize/dispose)
- [ ] Dependency scoping (singleton vs transient)
- [ ] Service composition and decoration
- [ ] Automatic mock generation from interfaces