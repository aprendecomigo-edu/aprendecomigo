# Gluestack UI v1 to v2 Migration Guide

## Overview
This document outlines the migration from Gluestack UI v1 (factory-based) to v2 (copy-paste pattern) for the Aprende Comigo platform.

## Migration Status

### ✅ Completed
- [x] Analysis of v1 dependencies and usage patterns
- [x] Button component v2 implementation (`button-v2.tsx` and `button-v2-simple.tsx`)
- [x] Input component v2 implementation (`input-v2.tsx` and `input-v2-simple.tsx`)
- [x] Modal component v2 implementation (`modal-v2.tsx` and `modal-v2-simple.tsx`)
- [x] Toast component v2 implementation (`toast-v2.tsx` and `toast-v2-simple.tsx`)
- [x] Form Control v2 implementation (`form-control-v2.tsx` and `form-control-v2-simple.tsx`)
- [x] Migration script for automated Button import updates
- [x] Demo components for v1 vs v2 comparison (Button, Modal, Toast, FormControl)

### 🚧 In Progress
- [ ] Fix cssInterop issues in full v2 implementations
- [ ] Create migration scripts for Modal, Toast, FormControl
- [ ] Testing v2 components in real application contexts

### 📋 Pending
- [ ] Medium priority components (Select, Checkbox, Radio, Alert, Menu, Card, Avatar)
- [ ] Low priority components (Accordion, Slider, Switch, Progress, Divider, FAB, etc.)
- [ ] Full codebase import updates (168 files affected)
- [ ] Package.json cleanup (remove 28 v1 packages)

## Key Changes: v1 to v2

### Before (v1 - Factory Pattern)
```typescript
import { createButton } from '@gluestack-ui/button';

const UIButton = createButton({
  Root: Pressable,
  Text: Text,
  Spinner: ActivityIndicator,
  Icon: withStates(Icon),
});
```

### After (v2 - Direct Implementation)
```typescript
// No factory function needed - direct component implementation
export const Button = React.forwardRef<View, IButtonProps>(
  ({ className, variant, size, action, children, ...props }, ref) => {
    // Direct implementation with context and styling
    return (
      <ButtonContext.Provider value={contextValue}>
        <StyledButtonRoot {...props}>
          {children}
        </StyledButtonRoot>
      </ButtonContext.Provider>
    );
  }
);
```

## Migration Approach

### Phase 1: Component Implementation ✅
1. Created `button-v2.tsx` without factory functions
2. Maintained all existing styling (tva styles)
3. Preserved platform-specific behavior
4. Added proper TypeScript types

### Phase 2: Testing (Current Phase)
1. Created demo component for side-by-side comparison
2. Verify v2 components work identically to v1
3. Test in real application screens

### Phase 3: Automated Migration
Run the migration script to update imports:

```bash
# Dry run to see what will change
node scripts/migrate-button-to-v2.js --dry-run

# Perform actual migration
node scripts/migrate-button-to-v2.js

# After verification, clean up backups
rm **/*.backup
```

### Phase 4: Cleanup
1. Update main export files to use v2 components
2. Remove v1 packages from package.json
3. Run comprehensive tests

## Files Created

### New v2 Implementation
#### Button Components
- `components/ui/button/button-v2.tsx` - Complete v2 Button implementation
- `components/ui/button/button-v2-simple.tsx` - Simplified v2 Button implementation  
- `components/ui/button/button-v2.test.tsx` - Tests for v2 Button
- `components/ui/button/button-migration-demo.tsx` - Demo comparing v1 and v2

#### Input Components  
- `components/ui/input/input-v2.tsx` - Complete v2 Input implementation
- `components/ui/input/input-v2-simple.tsx` - Simplified v2 Input implementation

#### Modal Components
- `components/ui/modal/modal-v2.tsx` - Complete v2 Modal implementation
- `components/ui/modal/modal-v2-simple.tsx` - Simplified v2 Modal implementation
- `components/ui/modal/modal-migration-demo.tsx` - Demo comparing Modal v1 and v2

#### Toast Components  
- `components/ui/toast/toast-v2.tsx` - Complete v2 Toast implementation with useToast hook
- `components/ui/toast/toast-v2-simple.tsx` - Simplified v2 Toast implementation
- `components/ui/toast/toast-migration-demo.tsx` - Demo comparing Toast implementations

#### Form Control Components
- `components/ui/form-control/form-control-v2.tsx` - Complete v2 FormControl implementation
- `components/ui/form-control/form-control-v2-simple.tsx` - Simplified v2 FormControl implementation  
- `components/ui/form-control/form-control-migration-demo.tsx` - Demo comparing FormControl implementations

### Migration Tools
- `scripts/migrate-button-to-v2.js` - Automated Button migration script

## Impact Analysis

- **168 files** use the Button component
- All files can be automatically migrated using the script
- Backup files are created for rollback if needed

## Component Priority List

### High Priority (Most Used)
1. ✅ Button (160+ files) - COMPLETED
2. ✅ Input - COMPLETED
3. ✅ Modal - COMPLETED
4. ✅ Toast - COMPLETED
5. ✅ Form Control - COMPLETED

### Medium Priority
- Select, Checkbox, Radio, Alert, Menu, Card, Avatar

### Low Priority
- Accordion, Slider, Switch, Progress, Divider, FAB, etc.

## Benefits of v2

1. **No npm dependencies** - Components are directly in your codebase
2. **Full control** - Easy to customize without library constraints
3. **Smaller bundle** - Only include what you use
4. **Better tree-shaking** - Direct imports allow better optimization
5. **Type safety** - Better TypeScript support with direct implementations

## Testing Checklist

- [ ] Button renders correctly
- [ ] All variants work (solid, outline, link)
- [ ] All sizes work (xs, sm, md, lg, xl)
- [ ] All actions work (primary, secondary, positive, negative, default)
- [ ] Platform-specific behavior preserved (web vs native)
- [ ] Accessibility features maintained
- [ ] Performance metrics unchanged or improved

## New v2 Components Details

### Modal Component
- **Full v2**: Complete context-aware implementation with animations
- **Simple v2**: Lightweight version with essential functionality
- **Features**: Size variants (xs, sm, md, lg, full), backdrop handling, animated transitions
- **Demo**: Interactive comparison between v1, v2, and v2-simple implementations

### Toast Component  
- **Full v2**: Complete implementation with useToast hook and context management
- **Simple v2**: Streamlined version with basic toast functionality
- **Features**: Action variants (success, error, warning, info, muted), auto-hide, manual control
- **Hook**: Direct useToast implementation without factory dependencies
- **Demo**: Live toast testing with all variants and manual examples

### Form Control Component
- **Full v2**: Complete form control system with context and variant support  
- **Simple v2**: Clean implementation focused on essential form control features
- **Features**: Size variants, error states, helper text, label management, icon support
- **Components**: Label, Error, Helper, Icon components with full styling support
- **Demo**: Interactive form validation showing all states and components

## Next Steps

1. **Test v2 high-priority components** in real application contexts
2. **Fix any cssInterop issues** discovered during testing  
3. **Create migration scripts** for Modal, Toast, and FormControl
4. **Proceed with medium priority components** (Select, Checkbox, Radio, etc.)
5. **Run comprehensive migration** when ready to update all imports
6. **Remove v1 packages** after all components migrated

## Rollback Plan

If issues are discovered:
1. Restore from backup files created by migration script
2. Revert to original button/index.tsx exports
3. Keep v1 packages in package.json
4. Debug and fix v2 implementation
5. Retry migration

## Commands Reference

```bash
# Check current v1 usage
grep -r "from.*@gluestack-ui" . --include="*.tsx" | grep -v node_modules | cut -d: -f2 | sort | uniq -c

# Run migration for specific component
node scripts/migrate-button-to-v2.js

# Test v2 components
npm test button-v2

# Check bundle size impact
npm run build:web:prod && ls -lh dist/
```

## Resources

- [Gluestack UI v2 Documentation](https://gluestack.io/ui/docs/home/overview/introduction)
- [Migration Discussion](https://github.com/gluestack/gluestack-ui/discussions/2225)
- [NativeWind v4 Documentation](https://www.nativewind.dev/)

## Notes

- Current setup already uses NativeWind and tva (compatible with v2)
- Platform-specific files (.web.tsx, .native.tsx) pattern is maintained
- All existing props and APIs remain the same for consumers
- This is a refactoring, not a breaking change for component users