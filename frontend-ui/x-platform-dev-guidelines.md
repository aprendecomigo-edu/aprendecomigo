# Cross-Platform Component Guidelines

## Overview

This document outlines the standard pattern for implementing cross-platform components in the Aprende Comigo React Native frontend. The goal is to eliminate runtime `Platform.OS` conditionals by using platform-specific file extensions.

## Pattern Structure

### File Naming Convention

For components with significant platform differences, use the following structure:

```
components/ui/[component-name]/
├── index.tsx          # Main entry point (fallback with Platform.OS)
├── index.web.tsx      # Web-specific implementation
├── index.native.tsx   # iOS/Android-specific implementation
├── [component]-common.tsx  # Shared logic, types, and utilities
```

### Platform Resolution

React Native automatically resolves platform-specific files:
- `index.web.tsx` is used for web platforms
- `index.native.tsx` is used for iOS and Android
- `index.tsx` serves as fallback (should contain Platform.OS conditional for backwards compatibility)

## Implementation Pattern

### 1. Common File Structure

Create a `[component]-common.tsx` file containing:
- Shared types and interfaces
- Common utility functions
- Style definitions (tva styles)
- Component creation helpers
- Export functions for component variants

**Example:**
```typescript
// button-common.tsx
export const SCOPE = 'BUTTON';
export const ButtonWrapper = React.forwardRef<...>(...);
export function createUIButton(Root: React.ComponentType<any>) { ... }
export function createButtonComponents(UIButton: any) { ... }
export const buttonStyle = tva({ ... });
export type IButtonProps = ...;
```

### 2. Web-Specific Implementation

Create `index.web.tsx` with web-optimized components:
```typescript
// index.web.tsx
import { withStyleContext } from '@gluestack-ui/nativewind-utils/withStyleContext';
import { ButtonWrapper, SCOPE, createUIButton, createButtonComponents } from './button-common';

const Root = withStyleContext(ButtonWrapper, SCOPE);
const UIButton = createUIButton(Root);

export const { Button, ButtonText, ButtonSpinner, ButtonIcon, ButtonGroup } = createButtonComponents(UIButton);
```

### 3. Native-Specific Implementation

Create `index.native.tsx` with native-optimized components:
```typescript
// index.native.tsx
import { withStyleContextAndStates } from '@gluestack-ui/nativewind-utils/withStyleContextAndStates';
import { ButtonWrapper, SCOPE, createUIButton, createButtonComponents } from './button-common';

const Root = withStyleContextAndStates(ButtonWrapper, SCOPE);
const UIButton = createUIButton(Root);

export const { Button, ButtonText, ButtonSpinner, ButtonIcon, ButtonGroup } = createButtonComponents(UIButton);
```

### 4. Main Entry Point (Fallback)

Keep `index.tsx` as fallback with Platform.OS conditional:
```typescript
// index.tsx
import { Platform } from 'react-native';
import { withStyleContext } from '@gluestack-ui/nativewind-utils/withStyleContext';
import { withStyleContextAndStates } from '@gluestack-ui/nativewind-utils/withStyleContextAndStates';
import { ButtonWrapper, SCOPE, createUIButton, createButtonComponents } from './button-common';

// Fallback implementation (should be overridden by platform-specific files)
const Root = Platform.OS === 'web'
  ? withStyleContext(ButtonWrapper, SCOPE)
  : withStyleContextAndStates(ButtonWrapper, SCOPE);

const UIButton = createUIButton(Root);

export const { Button, ButtonText, ButtonSpinner, ButtonIcon, ButtonGroup } = createButtonComponents(UIButton);
```

## When to Apply This Pattern

### ✅ Apply When:
- Component has different behavior between web and native
- Using different Gluestack utilities (`withStyleContext` vs `withStyleContextAndStates`)
- Platform-specific styling or interaction patterns
- Significant differences in event handling or accessibility

### ❌ Don't Apply When:
- Minor styling differences that can be handled with CSS
- Single line Platform.OS checks for simple properties
- Components with no significant platform differences
- Utility functions or simple components

## Key Components to Prioritize

Based on current codebase analysis, prioritize these components:

1. **High Priority** (significant platform differences):
   - `modal` - Different overlay behaviors
   - `toast` - Platform-specific notifications
   - `tooltip` - Hover vs touch interactions
   - `popover` - Different positioning strategies
   - `actionsheet` - Platform-specific sheet behaviors

2. **Medium Priority**:
   - `select` - Dropdown vs native picker differences
   - `menu` - Context menu implementations
   - `alert-dialog` - Modal vs native alert differences

3. **Low Priority**:
   - Basic UI components with minimal platform differences

## Migration Steps

1. **Analyze Component**: Review current Platform.OS usage
2. **Extract Common Logic**: Move shared code to `[component]-common.tsx`
3. **Create Platform Files**: Implement `.web.tsx` and `.native.tsx` versions
4. **Update Main File**: Keep fallback implementation in `index.tsx`
5. **Test**: Verify component works on all platforms
6. **Update Imports**: Ensure no breaking changes for consumers

## Best Practices

- **Maintain API Compatibility**: Exported component interface should remain consistent
- **Share Common Logic**: Maximize code reuse through common files
- **Document Platform Differences**: Add comments explaining why platforms differ
- **Test Both Platforms**: Verify functionality on web and native
- **Progressive Migration**: Convert components incrementally, not all at once

## Reference Implementation

See `components/ui/button/` for the complete reference implementation following this pattern.

## Notes

- This pattern follows React Native's built-in platform resolution
- Metro bundler automatically resolves platform-specific files
- No runtime performance impact from Platform.OS conditionals
- Backwards compatible with existing imports