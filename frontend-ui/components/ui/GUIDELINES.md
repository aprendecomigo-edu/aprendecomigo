# Cross-Platform Component Guidelines

This document outlines the established patterns for implementing consistent `.web.tsx/.native.tsx` components in the Aprende Comigo platform.

## When to Use Platform-Specific Files

Use the `.web.tsx/.native.tsx` pattern when:

- **Platform-specific context providers**: Components need different style context handling (`withStyleContext` vs `withStyleContextAndStates`)
- **Significant platform differences**: Components behave fundamentally differently on web vs native
- **Runtime Platform.OS conditionals exist**: Replace runtime checks with build-time resolution
- **Performance optimization**: Eliminate unnecessary runtime platform checks

## File Structure Pattern

Each cross-platform component should follow this structure:

```
components/ui/[component-name]/
├── index.tsx                 # Fallback with Platform.OS check
├── index.web.tsx            # Web-specific implementation  
├── index.native.tsx         # Native-specific implementation
└── [component-name]-common.tsx  # Shared logic, styles, and types
```

## Implementation Pattern

### 1. Common File (`[component-name]-common.tsx`)

Contains shared logic, styles, types, and component creation functions:

```typescript
'use client';
import type { VariantProps } from '@gluestack-ui/nativewind-utils';
import { tva } from '@gluestack-ui/nativewind-utils/tva';
import { create[ComponentName] } from '@gluestack-ui/[component-name]';
import { cssInterop } from 'nativewind';
import React from 'react';
import { View, Text } from 'react-native';

export const SCOPE = 'COMPONENT_NAME';

// Shared styles using tva
export const componentStyle = tva({
  base: 'base-styles',
  variants: {
    // variant definitions
  },
});

// Common function to create UI component with platform-specific Root
export function createUIComponent(Root: React.ComponentType<any>) {
  const UIComponent = create[ComponentName]({
    Root: Root,
    // other component parts
  });

  // CSS interop setup
  cssInterop(UIComponent, { className: 'style' });
  
  return UIComponent;
}

// Shared types
export type IComponentProps = React.ComponentProps<any> &
  VariantProps<typeof componentStyle> & { className?: string };

// Common component creation function
export function createComponentComponents(UIComponent: any) {
  const Component = React.forwardRef<React.ElementRef<typeof UIComponent>, IComponentProps>(
    ({ className, ...props }, ref) => {
      return <UIComponent ref={ref} className={componentStyle({ class: className })} {...props} />;
    }
  );

  Component.displayName = 'Component';

  return { Component };
}
```

### 2. Web Implementation (`index.web.tsx`)

```typescript
import { withStyleContext } from '@gluestack-ui/nativewind-utils/withStyleContext';
import { View } from 'react-native';
import { SCOPE, createUIComponent, createComponentComponents } from './component-common';

// Web-specific Root component using withStyleContext
const Root = withStyleContext(View, SCOPE);

// Create UI component with web-specific Root
const UIComponent = createUIComponent(Root);

// Create and export all components
export const { Component } = createComponentComponents(UIComponent);
```

### 3. Native Implementation (`index.native.tsx`)

```typescript
import { withStyleContextAndStates } from '@gluestack-ui/nativewind-utils/withStyleContextAndStates';
import { View } from 'react-native';
import { SCOPE, createUIComponent, createComponentComponents } from './component-common';

// Native-specific Root component using withStyleContextAndStates
const Root = withStyleContextAndStates(View, SCOPE);

// Create UI component with native-specific Root
const UIComponent = createUIComponent(Root);

// Create and export all components
export const { Component } = createComponentComponents(UIComponent);
```

### 4. Fallback Implementation (`index.tsx`)

```typescript
/**
 * Platform-aware Component that automatically resolves to the appropriate
 * platform-specific implementation:
 * - index.web.tsx for web platforms (uses withStyleContext)
 * - index.native.tsx for iOS/Android platforms (uses withStyleContextAndStates)
 * 
 * This file serves as a fallback and should not be used in practice.
 * The platform-specific files will be automatically resolved by React Native.
 */

import { Platform } from 'react-native';
import { withStyleContext } from '@gluestack-ui/nativewind-utils/withStyleContext';
import { withStyleContextAndStates } from '@gluestack-ui/nativewind-utils/withStyleContextAndStates';
import { View } from 'react-native';
import { SCOPE, createUIComponent, createComponentComponents } from './component-common';

// Fallback implementation (should be overridden by platform-specific files)
const Root = Platform.OS === 'web'
  ? withStyleContext(View, SCOPE)
  : withStyleContextAndStates(View, SCOPE);

const UIComponent = createUIComponent(Root);

export const { Component } = createComponentComponents(UIComponent);
```

## Real Examples

### Simple Component: Tooltip

**File Structure:**
```
components/ui/tooltip/
├── index.tsx
├── index.web.tsx
├── index.native.tsx
└── tooltip-common.tsx
```

The tooltip component demonstrates the basic pattern with minimal complexity.

### Moderate Component: Toast

**File Structure:**
```
components/ui/toast/
├── index.tsx
├── index.web.tsx
├── index.native.tsx
└── toast-common.tsx
```

The toast component shows how to handle:
- Custom hooks (`useToast`)
- Multiple sub-components (`Toast`, `ToastTitle`, `ToastDescription`)
- Style context usage with `useStyleContext`

### Complex Component: Modal

**File Structure:**
```
components/ui/modal/
├── index.tsx
├── index.web.tsx
├── index.native.tsx
└── modal-common.tsx
```

The modal component demonstrates:
- Multiple sub-components with complex relationships
- React Native Reanimated animations
- Advanced styling with parent variants
- Complex component creation patterns

## Best Practices

### 1. Maintain Backwards Compatibility
- Existing imports should continue to work
- Export signatures must remain identical
- Component behavior should be consistent across platforms

### 2. Extract Maximum Shared Logic
- Move all styles, types, and business logic to common files
- Platform-specific files should be minimal
- Avoid code duplication between platforms

### 3. Consistent Naming
- Common files: `[component-name]-common.tsx`
- Scope constants: `SCOPE = 'COMPONENT_NAME'`
- Creation functions: `createUI[ComponentName]`, `create[ComponentName]Components`

### 4. Performance Considerations
- Platform-specific files eliminate runtime Platform.OS checks
- Build-time resolution is more efficient than runtime conditionals
- Tree-shaking benefits from separate platform builds

### 5. Type Safety
- Maintain strict TypeScript typing
- Use proper generic constraints for component props
- Export consistent type definitions

## Migration Checklist

When converting existing components:

- [ ] Create common file with shared logic
- [ ] Extract all styles and TVA definitions
- [ ] Create platform-specific creation functions
- [ ] Implement web-specific file
- [ ] Implement native-specific file
- [ ] Update main index file as fallback
- [ ] Test cross-platform functionality
- [ ] Verify existing imports still work
- [ ] Update any relevant documentation

## Remaining Components to Convert

The following components still use runtime Platform.OS conditionals and should be converted following this pattern:

- `popover/index.tsx` - Complex component with Arrow, Backdrop, Content, Header, Body, Footer
- `actionsheet/index.tsx` - Modal-like component with platform-specific behavior
- `menu/index.tsx` - Dropdown component with complex state management
- `alert-dialog/index.tsx` - Dialog component similar to Modal

Each follows the same basic pattern but with increasing complexity of sub-components and animations.

## Platform Resolution

React Native's Metro bundler automatically resolves platform-specific files:

1. **First**: Look for `index.web.tsx` on web, `index.native.tsx` on mobile
2. **Second**: Fall back to `index.tsx` if platform-specific file doesn't exist
3. **Build time**: This resolution happens during bundling, not runtime

This ensures optimal performance and smaller bundle sizes for each platform.

## Testing

When implementing this pattern:

1. **Cross-platform testing**: Verify functionality on web, iOS, and Android
2. **Import testing**: Ensure existing imports continue to work
3. **Bundle analysis**: Confirm platform-specific code isn't included in other platform builds
4. **Performance testing**: Measure improvement from eliminating runtime Platform.OS checks

---

*This pattern is established and proven with the Button, Tooltip, Toast, and Modal components. Follow these guidelines for consistent implementation across all cross-platform UI components.*