# Gluestack UI v2 Component Testing Guide

## Quick Testing Instructions

To test the new v2 components, you can import and use the migration demo components:

### 1. Modal Testing
```tsx
import { ModalMigrationDemo } from './components/ui/modal/modal-migration-demo';

// In your app or test screen:
<ModalMigrationDemo />
```

### 2. Toast Testing  
```tsx
import { ToastMigrationDemo } from './components/ui/toast/toast-migration-demo';

// In your app or test screen:
<ToastMigrationDemo />
```

### 3. Form Control Testing
```tsx
import { FormControlMigrationDemo } from './components/ui/form-control/form-control-migration-demo';

// In your app or test screen:
<FormControlMigrationDemo />
```

## Using v2 Components Directly

### Modal v2 Usage
```tsx
import {
  Modal,
  ModalBackdrop,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalCloseButton,
} from './components/ui/modal/modal-v2';

// Or use the simple version:
// from './components/ui/modal/modal-v2-simple';

function MyModal({ isOpen, onClose }) {
  return (
    <Modal size="md">
      {isOpen && (
        <>
          <ModalBackdrop onPress={onClose} />
          <ModalContent>
            <ModalHeader>
              <Text>Modal Title</Text>
              <ModalCloseButton onPress={onClose}>
                <Text>×</Text>
              </ModalCloseButton>
            </ModalHeader>
            <ModalBody>
              <Text>Modal content goes here</Text>
            </ModalBody>
            <ModalFooter>
              <Button onPress={onClose}>Close</Button>
            </ModalFooter>
          </ModalContent>
        </>
      )}
    </Modal>
  );
}
```

### Toast v2 Usage
```tsx
import { useToast, ToastContainer } from './components/ui/toast/toast-v2';

// Or use the simple version:
// from './components/ui/toast/toast-v2-simple';

function MyComponent() {
  const toast = useToast();

  const showSuccess = () => {
    toast.show({
      title: 'Success!',
      description: 'Operation completed successfully',
      action: 'success',
      duration: 3000,
    });
  };

  return (
    <View>
      <Button onPress={showSuccess}>Show Toast</Button>
      {/* Required for toasts to display */}
      <ToastContainer />
    </View>
  );
}
```

### Form Control v2 Usage
```tsx
import {
  FormControl,
  FormControlLabel,
  FormControlLabelText,
  FormControlError,
  FormControlErrorText,
  FormControlHelper,
  FormControlHelperText,
} from './components/ui/form-control/form-control-v2';

// Or use the simple version:
// from './components/ui/form-control/form-control-v2-simple';

function MyForm() {
  const [value, setValue] = useState('');
  const [error, setError] = useState('');

  return (
    <FormControl size="md">
      <FormControlLabel>
        <FormControlLabelText>Email Address</FormControlLabelText>
      </FormControlLabel>
      
      <TextInput
        value={value}
        onChangeText={setValue}
        className="border px-3 py-2 rounded"
      />
      
      {error && (
        <FormControlError>
          <FormControlErrorText>{error}</FormControlErrorText>
        </FormControlError>
      )}
      
      <FormControlHelper>
        <FormControlHelperText>Enter a valid email address</FormControlHelperText>
      </FormControlHelper>
    </FormControl>
  );
}
```

## Key Differences from v1

### No Factory Functions
- ✅ v2: Direct component imports
- ❌ v1: `createModal()`, `createToast()`, `createFormControl()`

### Direct Implementation
- ✅ v2: Components work directly with React patterns
- ❌ v1: Complex factory-based initialization

### Simplified Context
- ✅ v2: Clean React context for state sharing
- ❌ v1: Factory-managed internal state

### Better TypeScript Support
- ✅ v2: Direct prop types and better inference
- ❌ v1: Complex generated types from factories

## Testing Checklist

### Modal
- [ ] All size variants work (xs, sm, md, lg, full)
- [ ] Backdrop click to close works
- [ ] Animations work (fade in/out)
- [ ] Header, body, footer layout correctly
- [ ] Close button functionality
- [ ] Platform compatibility (web, iOS, Android)

### Toast
- [ ] useToast hook works without factory
- [ ] All action variants display correctly (success, error, warning, info, muted)
- [ ] Auto-hide after specified duration
- [ ] Manual hide/hideAll functions work
- [ ] Multiple toasts can be shown
- [ ] Toast container displays properly

### Form Control
- [ ] All size variants work (sm, md, lg)
- [ ] Label, error, helper text display correctly
- [ ] Error states show/hide properly
- [ ] Icon support works
- [ ] Context propagates size to children
- [ ] Required asterisk displays

## Performance Comparison

Run this in your app to compare bundle sizes:

```bash
# Check current bundle size
npm run build:web:prod

# After switching to v2, check again
# Bundle size should be smaller due to tree-shaking
```

## Migration Path

1. **Test components using demo screens**
2. **Replace one component at a time in your app**
3. **Verify functionality matches v1 exactly**
4. **Run full test suite**
5. **Deploy and monitor for issues**

## Need Help?

If you encounter issues with the v2 components:

1. Check the demo components first
2. Compare props with v1 implementation
3. Verify all required imports
4. Test on your target platforms
5. Report specific issues found

The goal is 100% API compatibility, so any differences in behavior should be reported as bugs to fix.