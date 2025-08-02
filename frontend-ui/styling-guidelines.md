# Aprende Comigo - Frontend Styling Guidelines

**Last Updated:** August 2, 2025  
**Version:** 1.0  

This document provides comprehensive styling guidelines for the Aprende Comigo EdTech platform, addressing Tailwind CSS best practices, theming system usage, and cross-platform considerations.

## Table of Contents

1. [Overview](#overview)
2. [Architecture Principles](#architecture-principles)
3. [Theming System](#theming-system)
4. [Styling Best Practices](#styling-best-practices)
5. [Migration from Legacy Patterns](#migration-from-legacy-patterns)
6. [Component Styling Guidelines](#component-styling-guidelines)
7. [Cross-Platform Considerations](#cross-platform-considerations)
8. [Performance Optimization](#performance-optimization)

## Overview

The Aprende Comigo platform uses a sophisticated styling architecture combining:

- **NativeWind**: Cross-platform Tailwind CSS implementation
- **Gluestack UI**: Component library with comprehensive theming
- **CSS Variables**: Dynamic theme system supporting light/dark modes
- **Platform-specific implementations**: Optimized for web, iOS, and Android

### Key Goals

✅ **Type Safety**: Compile-time checking of styles and themes  
✅ **Performance**: Optimal bundle sizes and runtime efficiency  
✅ **Consistency**: Unified design system across all platforms  
✅ **Maintainability**: Centralized theme management and easy updates  

## Architecture Principles

### 1. Avoid Dynamic Class Generation

❌ **Never Use Dynamic Template Literals**
```typescript
// WRONG: These classes may be purged in production
const QuickActionItem = ({ action }) => (
  <VStack className={`border-${action.color}-200 bg-${action.color}-50`}>
    <Icon className={`text-${action.color}-600`} />
  </VStack>
);
```

✅ **Use Explicit Class Mappings**
```typescript
// CORRECT: Type-safe and production-ready
const COLOR_SCHEMES = {
  green: 'border-green-200 bg-green-50 text-green-600',
  blue: 'border-blue-200 bg-blue-50 text-blue-600',
  purple: 'border-purple-200 bg-purple-50 text-purple-600',
} as const;

const QuickActionItem = ({ action }) => (
  <VStack className={COLOR_SCHEMES[action.color]}>
    <Icon />
  </VStack>
);
```

### 2. Leverage the Design System

✅ **Prefer CSS Variables for Dynamic Theming**
```typescript
// Use the established theme system
const PrimaryButton = () => (
  <Button style={{ backgroundColor: 'var(--color-primary-600)' }}>
    Click me
  </Button>
);

// Or use Tailwind classes that map to CSS variables
const PrimaryButton = () => (
  <Button className="bg-primary-600">
    Click me
  </Button>
);
```

### 3. Create Reusable Style Constants

```typescript
// constants/design-tokens.ts
export const COMPONENT_VARIANTS = {
  success: {
    background: 'bg-success-50',
    border: 'border-success-200',
    text: 'text-success-600',
    hover: 'hover:bg-success-100',
  },
  error: {
    background: 'bg-error-50',
    border: 'border-error-200',
    text: 'text-error-600',
    hover: 'hover:bg-error-100',
  },
  warning: {
    background: 'bg-warning-50',
    border: 'border-warning-200',
    text: 'text-warning-600',
    hover: 'hover:bg-warning-100',
  },
  info: {
    background: 'bg-info-50',
    border: 'border-info-200',
    text: 'text-info-600',
    hover: 'hover:bg-info-100',
  },
} as const;

export type ComponentVariant = keyof typeof COMPONENT_VARIANTS;
```

## Theming System

### Available Color Palettes

The platform provides comprehensive color palettes with 11 shades each (0, 50, 100-950):

#### Brand Colors
- **Primary**: Brand blue (`#2563EB`) - Main actions, links, buttons
- **Secondary**: Neutral grays - Supporting elements
- **Tertiary**: Orange accents - Secondary actions

#### Semantic Colors
- **Success**: Green palette - Success states, confirmations
- **Error**: Red palette - Error states, warnings
- **Warning**: Orange/yellow palette - Caution states
- **Info**: Blue palette - Informational content

#### Utility Colors
- **Typography**: Text color scales
- **Background**: Surface colors
- **Outline**: Border and outline colors

### Theme Configuration

The platform uses a **two-file theming architecture** required by Gluestack UI's manual installation:

#### Primary Theme Definition: `config.ts`
**File:** `frontend-ui/components/ui/gluestack-ui-provider/config.ts`

This is the **main theme configuration** where you make most changes:
- **Defines actual color values** as hex codes (`#2563EB`, `#DC2626`, etc.)
- **Creates CSS variables** (`--color-primary-600`, `--color-error-500`, etc.)
- **Handles light/dark mode switching** using NativeWind's `vars()` function
- **Provides platform optimizations** (direct hex for native, CSS vars for web)
- **Required by Gluestack UI components** - they expect these exact variable names

#### Tailwind Integration: `tailwind.config.js`
**File:** `frontend-ui/tailwind.config.js`

This file **consumes** the CSS variables from config.ts:
- **Maps Tailwind classes to CSS variables** (e.g., `bg-primary-600` → `var(--color-primary-600)`)
- **Extends Tailwind's color system** with your custom theme tokens
- **Must be updated** when you add new colors to config.ts

#### Where to Make Changes

✅ **For color changes**: Edit `config.ts` first
✅ **For new colors**: Edit both `config.ts` and `tailwind.config.js`
✅ **For spacing/typography**: Edit `tailwind.config.js`

> **Gluestack UI Documentation**: "In case you are adding a new color in your config file, you need to update it in the tailwind.config.js file as well."

### Changing Main Theme Colors

#### 1. Update Primary Brand Color

```typescript
// In config.ts, modify lightThemeHex and darkThemeHex

const lightThemeHex = {
  // Change primary brand color (currently #2563EB)
  '--color-primary-500': '#YOUR_BRAND_COLOR',
  '--color-primary-600': '#YOUR_BRAND_COLOR',
  // Update related shades for consistency
  '--color-primary-400': '#LIGHTER_SHADE',
  '--color-primary-700': '#DARKER_SHADE',
  // ...
};
```

#### 2. Update Semantic Colors

```typescript
// Modify success color scheme
'--color-success-500': '#YOUR_SUCCESS_COLOR',
'--color-success-600': '#YOUR_SUCCESS_COLOR',

// Modify error color scheme  
'--color-error-500': '#YOUR_ERROR_COLOR',
'--color-error-600': '#YOUR_ERROR_COLOR',
```

#### 3. Adding a New Color (Requires Both Files)

When adding a completely new color (e.g., `accent`):

**Step 1: Add to `config.ts`**
```typescript
// In lightThemeHex object
const lightThemeHex = {
  // ... existing colors
  
  /* Accent - New color */
  '--color-accent-0': '#FFF7ED',
  '--color-accent-50': '#FFEDD5',
  '--color-accent-100': '#FED7AA',
  '--color-accent-200': '#FDBA74',
  '--color-accent-300': '#FB923C',
  '--color-accent-400': '#F97316',
  '--color-accent-500': '#EA580C',
  '--color-accent-600': '#DC2626', // Your main accent color
  '--color-accent-700': '#C2410C',
  '--color-accent-800': '#9A3412',
  '--color-accent-900': '#7C2D12',
  '--color-accent-950': '#431407',
};

// Also add to darkThemeHex with appropriate dark mode values
```

**Step 2: Add to `tailwind.config.js`**
```typescript
// In theme.extend.colors object
colors: {
  // ... existing colors
  
  accent: {
    0: 'var(--color-accent-0)',
    50: 'var(--color-accent-50)',
    100: 'var(--color-accent-100)',
    200: 'var(--color-accent-200)',
    300: 'var(--color-accent-300)',
    400: 'var(--color-accent-400)',
    500: 'var(--color-accent-500)',
    600: 'var(--color-accent-600)',
    700: 'var(--color-accent-700)',
    800: 'var(--color-accent-800)',
    900: 'var(--color-accent-900)',
    950: 'var(--color-accent-950)',
  },
}
```

**Step 3: Use the new color**
```typescript
// Now you can use accent in your components
<Button className="bg-accent-600 text-white">
  Accent Button
</Button>
```

#### 4. Testing Theme Changes

After modifying theme colors:

1. **Restart development server**: Theme changes require restart
2. **Test both light and dark modes**: Verify both theme variants
3. **Check cross-platform**: Test web, iOS, and Android if applicable
4. **Verify CSS variables**: Use browser DevTools to confirm variables resolve correctly

```bash
# Restart development to apply theme changes
make dev-open
```

### Using Theme Colors in Components

#### Method 1: CSS Variables (Recommended)
```typescript
const ThemedComponent = () => (
  <View style={{
    backgroundColor: 'var(--color-primary-50)',
    borderColor: 'var(--color-primary-200)',
    color: 'var(--color-primary-600)',
  }}>
    Content
  </View>
);
```

#### Method 2: Tailwind Classes
```typescript
const ThemedComponent = () => (
  <View className="bg-primary-50 border-primary-200 text-primary-600">
    Content
  </View>
);
```

#### Method 3: Typed Variants
```typescript
interface ComponentProps {
  variant: 'primary' | 'secondary' | 'success' | 'error';
}

const getVariantStyles = (variant: ComponentProps['variant']) => {
  const variants = {
    primary: 'bg-primary-50 border-primary-200 text-primary-600',
    secondary: 'bg-secondary-50 border-secondary-200 text-secondary-600',
    success: 'bg-success-50 border-success-200 text-success-600',
    error: 'bg-error-50 border-error-200 text-error-600',
  };
  return variants[variant];
};
```

### Configuration File Workflow Summary

#### For Most Theme Changes
1. ✅ **Edit only `config.ts`** - Most color changes go here
2. ✅ **Restart dev server** - Changes require restart
3. ✅ **Test both themes** - Verify light and dark modes

#### For New Colors Only
1. ✅ **Add to `config.ts`** first with full color palette (0-950)
2. ✅ **Add to `tailwind.config.js`** second with CSS variable references
3. ✅ **Restart dev server** and test

#### Common Gotchas
❌ **Forgetting to restart** - Theme changes don't hot-reload  
❌ **Only updating one file** - New colors need both files  
❌ **Missing dark mode values** - Always define both light and dark variants  
❌ **Inconsistent naming** - CSS variable names must match exactly  

## Styling Best Practices

### 1. Component Styling Patterns

#### Use TVA (Tailwind Variants API) for Component Variants

```typescript
import { tva } from '@gluestack-ui/nativewind-utils/tva';

const buttonStyle = tva({
  base: 'px-4 py-2 rounded-lg font-medium transition-colors',
  variants: {
    variant: {
      primary: 'bg-primary-600 text-white hover:bg-primary-700',
      secondary: 'bg-secondary-200 text-secondary-800 hover:bg-secondary-300',
      outline: 'border border-primary-600 text-primary-600 hover:bg-primary-50',
    },
    size: {
      sm: 'px-3 py-1.5 text-sm',
      md: 'px-4 py-2 text-base',
      lg: 'px-6 py-3 text-lg',
    },
    disabled: {
      true: 'opacity-50 cursor-not-allowed pointer-events-none',
    },
  },
  defaultVariants: {
    variant: 'primary',
    size: 'md',
  },
});

// Usage
const Button = ({ variant, size, disabled, className, ...props }) => (
  <Pressable 
    className={buttonStyle({ variant, size, disabled, class: className })}
    {...props}
  />
);
```

#### Create Style Hooks for Complex Logic

```typescript
// hooks/useComponentStyles.ts
export const useComponentStyles = (
  variant: ComponentVariant,
  options?: { disabled?: boolean; loading?: boolean }
) => {
  return useMemo(() => {
    const base = COMPONENT_VARIANTS[variant];
    
    if (options?.disabled) {
      return {
        ...base,
        background: 'bg-gray-50',
        text: 'text-gray-400',
      };
    }
    
    if (options?.loading) {
      return {
        ...base,
        background: 'bg-gray-100',
        text: 'text-gray-500',
      };
    }
    
    return base;
  }, [variant, options]);
};
```

### 2. Responsive Design

#### Use NativeWind Responsive Utilities

```typescript
const ResponsiveComponent = () => (
  <View className="w-full px-4 md:px-8 lg:px-12">
    <Text className="text-lg md:text-xl lg:text-2xl">
      Responsive heading
    </Text>
    <View className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {/* Grid items */}
    </View>
  </View>
);
```

#### Platform-Specific Responsive Components

```typescript
// Use the established cross-platform pattern
import { ResponsiveContainer } from '@/components/ui/responsive';

const DashboardLayout = () => (
  <ResponsiveContainer>
    <View className="flex-1 p-4">
      {/* Content adapts to platform and screen size */}
    </View>
  </ResponsiveContainer>
);
```

### 3. State-Based Styling

#### Interactive States

```typescript
const InteractiveButton = () => {
  const [isPressed, setIsPressed] = useState(false);
  const [isHovered, setIsHovered] = useState(false);
  
  const buttonStyles = useMemo(() => 
    cn(
      'bg-primary-600 px-4 py-2 rounded-lg transition-colors',
      isPressed && 'bg-primary-800',
      isHovered && 'bg-primary-700'
    ), [isPressed, isHovered]
  );
  
  return (
    <Pressable 
      className={buttonStyles}
      onPressIn={() => setIsPressed(true)}
      onPressOut={() => setIsPressed(false)}
      onHoverIn={() => setIsHovered(true)}
      onHoverOut={() => setIsHovered(false)}
    >
      <Text className="text-white font-medium">Press me</Text>
    </Pressable>
  );
};
```

#### Form States

```typescript
const FormInput = ({ error, success, disabled }) => {
  const inputStyles = cn(
    'border rounded-lg px-3 py-2 transition-colors',
    'border-outline-300 focus:border-primary-500',
    error && 'border-error-500 focus:border-error-600',
    success && 'border-success-500 focus:border-success-600',
    disabled && 'bg-gray-50 text-gray-400 cursor-not-allowed'
  );
  
  return <Input className={inputStyles} disabled={disabled} />;
};
```

## Migration from Legacy Patterns

### Priority Migration List

Based on the audit findings, prioritize migrating these components:

#### Phase 1: High-Risk Components (Immediate)
1. **QuickActionsPanel** - Multiple dynamic color patterns
2. **FileUploadProgress** - Status-based colors  
3. **SchoolStats** - Complex conditional styling

#### Phase 2: Medium-Risk Components (Next Sprint)
1. **DashboardOverview** - Action-based colors
2. **ActivityFeed** - Dynamic status indicators
3. **Wizard components** - Multi-step styling

### Migration Patterns

#### From Dynamic Classes to Explicit Mappings

```typescript
// BEFORE: Risky dynamic pattern
const StatusBadge = ({ status }) => (
  <Badge className={`bg-${status}-100 text-${status}-800`}>
    {status}
  </Badge>
);

// AFTER: Safe explicit mapping  
const STATUS_STYLES = {
  active: 'bg-success-100 text-success-800',
  pending: 'bg-warning-100 text-warning-800',
  inactive: 'bg-gray-100 text-gray-800',
  error: 'bg-error-100 text-error-800',
} as const;

const StatusBadge = ({ status }: { status: keyof typeof STATUS_STYLES }) => (
  <Badge className={STATUS_STYLES[status]}>
    {status}
  </Badge>
);
```

#### From Template Literals to Style Functions

```typescript
// BEFORE: Template literal concatenation
const MetricCard = ({ metric, trend }) => (
  <Card className={`${metric.color} ${trend > 0 ? 'border-green-200' : 'border-red-200'}`}>
    <Text>{metric.value}</Text>
  </Card>
);

// AFTER: Style composition function
const getMetricCardStyles = (metric: Metric, trend: number) => {
  const baseStyles = 'p-4 rounded-lg shadow-sm';
  const colorStyles = METRIC_COLORS[metric.type];
  const trendStyles = trend > 0 ? 'border-success-200' : 'border-error-200';
  
  return cn(baseStyles, colorStyles, trendStyles);
};

const MetricCard = ({ metric, trend }) => (
  <Card className={getMetricCardStyles(metric, trend)}>
    <Text>{metric.value}</Text>
  </Card>
);
```

## Component Styling Guidelines

### 1. Following the Established Pattern

Use the cross-platform pattern documented in [`x-platform-dev-guidelines.md`](/frontend-ui/x-platform-dev-guidelines.md):

```
components/ui/[component-name]/
├── index.tsx                        # Fallback
├── index.web.tsx                   # Web implementation  
├── index.native.tsx                # Native implementation
└── [component-name]-common.tsx     # Shared styles and logic
```

### 2. Common File Structure

```typescript
// component-common.tsx
export const componentStyle = tva({
  base: 'base-styles',
  variants: {
    variant: {
      primary: 'bg-primary-600 text-white',
      secondary: 'bg-secondary-200 text-secondary-800',
    },
    size: {
      sm: 'px-3 py-1.5 text-sm',
      md: 'px-4 py-2 text-base',
    },
  },
});

export type ComponentProps = {
  variant?: 'primary' | 'secondary';
  size?: 'sm' | 'md';
  className?: string;
};
```

### 3. Platform-Specific Considerations

#### Web-Specific Styles
```typescript
// index.web.tsx
import { withStyleContext } from '@gluestack-ui/nativewind-utils/withStyleContext';

// Web can handle hover states, complex CSS
const webSpecificStyles = 'hover:shadow-lg transition-shadow cursor-pointer';
```

#### Native-Specific Styles  
```typescript
// index.native.tsx
import { withStyleContextAndStates } from '@gluestack-ui/nativewind-utils/withStyleContextAndStates';

// Native needs different interaction handling
const nativeSpecificStyles = 'active:opacity-80';
```

## Cross-Platform Considerations

### 1. Platform-Specific Properties

```typescript
// Use Platform.select for platform-specific values
const styles = StyleSheet.create({
  container: {
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.25,
        shadowRadius: 3.84,
      },
      android: {
        elevation: 5,
      },
      web: {
        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.15)',
      },
    }),
  },
});
```

### 2. Safe Area Handling

```typescript
import { SafeAreaView } from '@/components/ui/safe-area-view';

const ScreenComponent = () => (
  <SafeAreaView className="flex-1 bg-background-0">
    {/* Content automatically handles safe areas */}
  </SafeAreaView>
);
```

### 3. Typography Scaling

```typescript
// Use rem units for web, responsive scaling for native
const typographyStyles = {
  web: 'text-base leading-relaxed',
  native: 'text-base leading-6',
};
```

## Performance Optimization

### 1. Bundle Size Optimization

- **Avoid dynamic class generation**: Prevents unused class bloat
- **Use platform-specific files**: Reduces bundle size per platform
- **Leverage tree-shaking**: Import only used style utilities

### 2. Runtime Performance

```typescript
// GOOD: Memoize complex style calculations
const ExpensiveComponent = ({ items, variant }) => {
  const itemStyles = useMemo(() => 
    items.map(item => getItemStyles(item, variant))
  , [items, variant]);
  
  return (
    <View>
      {items.map((item, index) => (
        <View key={item.id} className={itemStyles[index]}>
          {item.content}
        </View>
      ))}
    </View>
  );
};

// AVOID: Recalculating styles on every render
const SlowComponent = ({ items, variant }) => (
  <View>
    {items.map(item => (
      <View key={item.id} className={getItemStyles(item, variant)}>
        {item.content}
      </View>
    ))}
  </View>
);
```

### 3. CSS Variable Performance

```typescript
// EFFICIENT: Batch CSS variable updates
const updateTheme = (newTheme: Theme) => {
  const root = document.documentElement;
  Object.entries(newTheme).forEach(([key, value]) => {
    root.style.setProperty(key, value);
  });
};

// INEFFICIENT: Individual updates
const slowThemeUpdate = (newTheme: Theme) => {
  Object.entries(newTheme).forEach(([key, value]) => {
    document.documentElement.style.setProperty(key, value);
  });
};
```

## Testing Styling Changes

### 1. Cross-Platform Testing

```bash
# Test web platform
npm run web

# Test iOS simulator (requires macOS)
npm run ios

# Test Android emulator
npm run android
```

### 2. Theme Testing

```typescript
// Test component with different themes
const ThemeTest = () => {
  const [isDark, setIsDark] = useState(false);
  
  return (
    <GluestackUIProvider mode={isDark ? 'dark' : 'light'}>
      <YourComponent />
      <Button onPress={() => setIsDark(!isDark)}>
        Toggle Theme
      </Button>
    </GluestackUIProvider>
  );
};
```

### 3. Responsive Testing

```typescript
// Test responsive behavior
const ResponsiveTest = () => {
  const [width, setWidth] = useState(1200);
  
  return (
    <View style={{ width, minHeight: 600 }}>
      <YourResponsiveComponent />
      <Slider 
        value={width} 
        onValueChange={setWidth}
        minimumValue={320}
        maximumValue={1920}
      />
    </View>
  );
};
```

## Common Pitfalls to Avoid

### ❌ Don't Use Dynamic Classes
```typescript
// This will break in production
className={`bg-${color}-500`}
```

### ❌ Don't Hardcode Colors
```typescript
// Avoid hardcoded hex values
style={{ backgroundColor: '#2563EB' }}
```

### ❌ Don't Ignore Platform Differences
```typescript
// Web-only properties will break on native
className="hover:bg-blue-500 cursor-pointer"
```

### ❌ Don't Mix Styling Approaches
```typescript
// Inconsistent - pick one approach
<View 
  className="bg-blue-500" 
  style={{ backgroundColor: 'var(--color-primary-600)' }}
/>
```

## Quick Reference

### Color Usage
- **Primary**: Main actions (`bg-primary-600`)
- **Secondary**: Supporting elements (`bg-secondary-200`)
- **Success**: Positive states (`bg-success-500`)
- **Error**: Error states (`bg-error-500`)
- **Warning**: Caution states (`bg-warning-500`)

### Spacing Scale
- **xs**: `p-1` (4px)
- **sm**: `p-2` (8px)  
- **md**: `p-4` (16px)
- **lg**: `p-6` (24px)
- **xl**: `p-8` (32px)

### Typography Scale
- **xs**: `text-xs` (12px)
- **sm**: `text-sm` (14px)
- **base**: `text-base` (16px)
- **lg**: `text-lg` (18px)
- **xl**: `text-xl` (20px)

---

**Remember**: Consistency, performance, and maintainability are key. When in doubt, refer to existing component implementations in `/components/ui/` and follow the established patterns.

For questions or clarifications, refer to:
- [Cross-Platform Component Guidelines](./components/ui/GUIDELINES.md)
- [Gluestack UI Documentation](https://gluestack.io/ui/docs)
- [NativeWind Documentation](https://www.nativewind.dev/docs)