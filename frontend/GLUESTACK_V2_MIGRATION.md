# Gluestack UI v1 to v2 Migration Guide

## Overview
This document outlines the migration from Gluestack UI v1 (factory-based) to v2 (copy-paste pattern) for the Aprende Comigo platform.

## Migration Status

### ✅ Completed
- [x] Analysis of v1 dependencies and usage patterns
- [x] Button component v2 implementation (`button-v2.tsx`)
- [x] Migration script for automated import updates
- [x] Demo component showing v1 vs v2 comparison

### 🚧 In Progress
- [ ] Testing v2 Button in real application contexts
- [ ] Migrating remaining high-priority components

### 📋 Pending
- [ ] Input component migration
- [ ] Modal component migration  
- [ ] Toast component migration
- [ ] Form Control migration
- [ ] Medium and low priority components
- [ ] Full codebase import updates
- [ ] Package.json cleanup

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
- `components/ui/button/button-v2.tsx` - Complete v2 Button implementation
- `components/ui/button/button-v2.test.tsx` - Tests for v2 Button
- `components/ui/button/button-migration-demo.tsx` - Demo comparing v1 and v2

### Migration Tools
- `scripts/migrate-button-to-v2.js` - Automated migration script

## Impact Analysis

- **168 files** use the Button component
- All files can be automatically migrated using the script
- Backup files are created for rollback if needed

## Component Priority List

### High Priority (Most Used)
1. ✅ Button (160+ files) - COMPLETED
2. ⏳ Input - Next
3. ⏳ Modal
4. ⏳ Toast  
5. ⏳ Form Control

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

## Next Steps

1. **Test v2 Button thoroughly** in a few key screens
2. **If successful**, proceed with Input component migration
3. **Use the same pattern** for remaining components
4. **Run the migration script** when ready to update all imports
5. **Remove v1 packages** after all components migrated

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