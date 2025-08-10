// Minimal Jest setup that works with jest-expo preset
// jest-expo already provides React Native mocks, so we don't override them

import React from 'react';
import '@testing-library/jest-native/extend-expect';

// Mock React Native Platform and other components
jest.mock('react-native', () => {
  const React = require('react');

  return {
    Platform: {
      OS: 'web',
      select: jest.fn(obj => obj.web || obj.default),
      isTVOS: false,
    },
    Keyboard: {
      dismiss: jest.fn(),
    },
    ScrollView: ({ children, ...props }) =>
      React.createElement('div', { ...props, 'data-testid': 'ScrollView' }, children),
    View: ({ children, ...props }) =>
      React.createElement('div', { ...props, 'data-testid': 'View' }, children),
    Text: ({ children, ...props }) =>
      React.createElement('span', { ...props, 'data-testid': 'Text' }, children),
    TextInput: props => React.createElement('input', { ...props, 'data-testid': 'TextInput' }),
    TouchableOpacity: ({ children, ...props }) =>
      React.createElement('button', { ...props, 'data-testid': 'TouchableOpacity' }, children),
    Pressable: ({ children, ...props }) =>
      React.createElement('button', { ...props, 'data-testid': 'Pressable' }, children),
    Image: props => React.createElement('img', { ...props, 'data-testid': 'Image' }),
    StyleSheet: {
      create: jest.fn(styles => styles),
    },
    Dimensions: {
      get: jest.fn(() => ({ width: 375, height: 667 })),
    },
  };
});

// Configure React Native Testing Library BEFORE any other mocks
const { configure } = require('@testing-library/react-native');

configure({
  // Explicitly disable automatic host component detection to avoid issues
  hostComponentNames: [
    'View',
    'Text',
    'TextInput',
    'ScrollView',
    'Image',
    'TouchableOpacity',
    'Pressable',
  ],
});

// Mock Gluestack UI components as proper React components
jest.mock('@/components/ui/box', () => {
  const React = require('react');
  return {
    Box: React.forwardRef((props, ref) =>
      React.createElement('div', {
        ...props,
        ref,
        'data-testid': props.testID,
        className: `gluestack-box ${props.className || ''}`,
      })
    ),
  };
});

jest.mock('@/components/ui/button', () => {
  const React = require('react');
  return {
    Button: React.forwardRef((props, ref) =>
      React.createElement('button', {
        ...props,
        ref,
        'data-testid': props.testID,
        disabled: props.disabled,
        onClick: props.onPress,
        className: `gluestack-button ${props.className || ''}`,
      })
    ),
    ButtonText: React.forwardRef((props, ref) =>
      React.createElement('span', {
        ...props,
        ref,
        'data-testid': props.testID,
        className: `gluestack-button-text ${props.className || ''}`,
      })
    ),
    ButtonIcon: React.forwardRef((props, ref) =>
      React.createElement('span', {
        ...props,
        ref,
        'data-testid': props.testID,
        className: `gluestack-button-icon ${props.className || ''}`,
      })
    ),
  };
});

jest.mock('@/components/ui/card', () => {
  const React = require('react');
  return {
    Card: React.forwardRef((props, ref) =>
      React.createElement('div', {
        ...props,
        ref,
        'data-testid': props.testID,
        className: `gluestack-card ${props.className || ''}`,
      })
    ),
  };
});

jest.mock('@/components/ui/heading', () => {
  const React = require('react');
  return {
    Heading: React.forwardRef((props, ref) =>
      React.createElement('h1', {
        ...props,
        ref,
        'data-testid': props.testID,
        role: props.accessibilityRole,
        'aria-level': props.accessibilityLevel,
        className: `gluestack-heading ${props.className || ''}`,
      })
    ),
  };
});

jest.mock('@/components/ui/hstack', () => {
  const React = require('react');
  return {
    HStack: React.forwardRef((props, ref) =>
      React.createElement('div', {
        ...props,
        ref,
        'data-testid': props.testID,
        className: `gluestack-hstack ${props.className || ''}`,
      })
    ),
  };
});

jest.mock('@/components/ui/icon', () => {
  const React = require('react');
  return {
    Icon: React.forwardRef((props, ref) =>
      React.createElement('span', {
        ...props,
        ref,
        'data-testid': props.testID,
        className: `gluestack-icon ${props.className || ''}`,
      })
    ),
  };
});

jest.mock('@/components/ui/text', () => {
  const React = require('react');
  return {
    Text: React.forwardRef((props, ref) =>
      React.createElement('span', {
        ...props,
        ref,
        'data-testid': props.testID,
        'aria-live': props.accessibilityLiveRegion,
        className: `gluestack-text ${props.className || ''}`,
      })
    ),
  };
});

jest.mock('@/components/ui/vstack', () => {
  const React = require('react');
  return {
    VStack: React.forwardRef((props, ref) =>
      React.createElement('div', {
        ...props,
        ref,
        'data-testid': props.testID,
        className: `gluestack-vstack ${props.className || ''}`,
      })
    ),
  };
});

// Mock additional UI components needed for auth tests
jest.mock('@/components/ui/input', () => {
  const React = require('react');
  return {
    Input: React.forwardRef((props, ref) =>
      React.createElement('div', {
        ...props,
        ref,
        'data-testid': props.testID,
        className: `gluestack-input ${props.className || ''}`,
      })
    ),
    InputField: React.forwardRef((props, ref) =>
      React.createElement('input', {
        ...props,
        ref,
        'data-testid': props.testID || props.name,
        placeholder: props.placeholder,
        value: props.value,
        onChange: e => props.onChangeText?.(e.target.value),
        onBlur: props.onBlur,
        type: props.type,
        keyboardType: props.keyboardType,
        maxLength: props.maxLength,
        className: `gluestack-input-field ${props.className || ''}`,
      })
    ),
  };
});

jest.mock('@/components/ui/form-control', () => {
  const React = require('react');
  return {
    FormControl: React.forwardRef((props, ref) =>
      React.createElement('div', {
        ...props,
        ref,
        'data-testid': props.testID,
        className: `gluestack-form-control ${props.className || ''}`,
      })
    ),
    FormControlLabel: React.forwardRef((props, ref) =>
      React.createElement('label', {
        ...props,
        ref,
        'data-testid': props.testID,
        className: `gluestack-form-control-label ${props.className || ''}`,
      })
    ),
    FormControlLabelText: React.forwardRef((props, ref) =>
      React.createElement('span', {
        ...props,
        ref,
        'data-testid': props.testID,
        className: `gluestack-form-control-label-text ${props.className || ''}`,
      })
    ),
    FormControlError: React.forwardRef((props, ref) =>
      React.createElement('div', {
        ...props,
        ref,
        'data-testid': props.testID,
        className: `gluestack-form-control-error ${props.className || ''}`,
      })
    ),
    FormControlErrorIcon: React.forwardRef((props, ref) =>
      React.createElement('span', {
        ...props,
        ref,
        'data-testid': props.testID,
        className: `gluestack-form-control-error-icon ${props.className || ''}`,
      })
    ),
    FormControlErrorText: React.forwardRef((props, ref) =>
      React.createElement('span', {
        ...props,
        ref,
        'data-testid': props.testID,
        className: `gluestack-form-control-error-text ${props.className || ''}`,
      })
    ),
    FormControlHelper: React.forwardRef((props, ref) =>
      React.createElement('div', {
        ...props,
        ref,
        'data-testid': props.testID,
        className: `gluestack-form-control-helper ${props.className || ''}`,
      })
    ),
    FormControlHelperText: React.forwardRef((props, ref) =>
      React.createElement('span', {
        ...props,
        ref,
        'data-testid': props.testID,
        className: `gluestack-form-control-helper-text ${props.className || ''}`,
      })
    ),
  };
});

jest.mock('@/components/ui/pressable', () => {
  const React = require('react');
  return {
    Pressable: React.forwardRef((props, ref) =>
      React.createElement('button', {
        ...props,
        ref,
        'data-testid': props.testID,
        onClick: props.onPress,
        disabled: props.disabled,
        className: `gluestack-pressable ${props.className || ''}`,
      })
    ),
  };
});

jest.mock('@/components/ui/radio', () => {
  const React = require('react');
  return {
    RadioGroup: React.forwardRef((props, ref) =>
      React.createElement('div', {
        ...props,
        ref,
        'data-testid': props.testID,
        className: `gluestack-radio-group ${props.className || ''}`,
      })
    ),
    Radio: React.forwardRef((props, ref) =>
      React.createElement('label', {
        ...props,
        ref,
        'data-testid': props.testID,
        onClick: () => props.onChange?.(props.value),
        className: `gluestack-radio ${props.className || ''}`,
      })
    ),
    RadioIndicator: React.forwardRef((props, ref) =>
      React.createElement('span', {
        ...props,
        ref,
        'data-testid': props.testID,
        className: `gluestack-radio-indicator ${props.className || ''}`,
      })
    ),
    RadioIcon: React.forwardRef((props, ref) =>
      React.createElement('span', {
        ...props,
        ref,
        'data-testid': props.testID,
        className: `gluestack-radio-icon ${props.className || ''}`,
      })
    ),
    RadioLabel: React.forwardRef((props, ref) =>
      React.createElement('span', {
        ...props,
        ref,
        'data-testid': props.testID,
        className: `gluestack-radio-label ${props.className || ''}`,
      })
    ),
  };
});

jest.mock('@/components/ui/tabs', () => {
  const React = require('react');
  return {
    Tabs: React.forwardRef((props, ref) =>
      React.createElement('div', {
        ...props,
        ref,
        'data-testid': props.testID,
        className: `gluestack-tabs ${props.className || ''}`,
      })
    ),
  };
});

jest.mock('@/components/ui/divider', () => {
  const React = require('react');
  return {
    Divider: React.forwardRef((props, ref) =>
      React.createElement('hr', {
        ...props,
        ref,
        'data-testid': props.testID,
        className: `gluestack-divider ${props.className || ''}`,
      })
    ),
  };
});

jest.mock('@/components/ui/toast', () => {
  const React = require('react');
  return {
    useToast: jest.fn(() => ({
      showToast: jest.fn(),
    })),
    Toast: React.forwardRef((props, ref) =>
      React.createElement('div', {
        ...props,
        ref,
        'data-testid': props.testID,
        className: `gluestack-toast ${props.className || ''}`,
      })
    ),
  };
});

jest.mock('@/components/ui/link', () => {
  const React = require('react');
  return {
    Link: React.forwardRef((props, ref) =>
      React.createElement('a', {
        ...props,
        ref,
        'data-testid': props.testID,
        href: props.href,
        className: `gluestack-link ${props.className || ''}`,
      })
    ),
    LinkText: React.forwardRef((props, ref) =>
      React.createElement('span', {
        ...props,
        ref,
        'data-testid': props.testID,
        className: `gluestack-link-text ${props.className || ''}`,
      })
    ),
  };
});

// Mock AuthLayout and ErrorBoundary
jest.mock('@/components/auth/AuthLayout', () => {
  const React = require('react');
  return {
    AuthLayout: React.forwardRef(({ children, ...props }, ref) =>
      React.createElement('div', {
        ...props,
        ref,
        'data-testid': 'AuthLayout',
        className: 'auth-layout',
      }, children)
    ),
  };
});

jest.mock('@/components/ErrorBoundary', () => {
  const React = require('react');
  return {
    ErrorBoundary: React.forwardRef(({ children, ...props }, ref) =>
      React.createElement('div', {
        ...props,
        ref,
        'data-testid': 'ErrorBoundary',
        className: 'error-boundary',
      }, children)
    ),
  };
});

// Mock @unitools/router and @unitools/link
jest.mock('@unitools/router', () => ({
  __esModule: true,
  default: jest.fn(() => ({
    push: jest.fn(),
    back: jest.fn(),
    replace: jest.fn(),
    canGoBack: jest.fn(() => true),
  })),
}));

jest.mock('@unitools/link', () => {
  const React = require('react');
  return {
    __esModule: true,
    default: React.forwardRef((props, ref) =>
      React.createElement('a', {
        ...props,
        ref,
        'data-testid': props.testID,
        href: props.href,
      })
    ),
  };
});

jest.mock('@/components/ui/gluestack-ui-provider', () => ({
  GluestackUIProvider: ({ children }) => children,
}));

jest.mock('@/components/ui/gluestack-ui-provider/config', () => ({
  config: {},
}));

// Enhanced NativeWind and CSS interop mocking
jest.mock('react-native-css-interop', () => {
  const cssInteropMock = jest.fn((Component, config) => Component);

  return {
    __esModule: true,
    cssInterop: cssInteropMock,
    remapProps: jest.fn((Component, config) => Component),
    useColorScheme: jest.fn(() => 'light'),
    vars: jest.fn(() => ({})),
    createContext: jest.fn(() => ({
      Provider: ({ children }) => children,
      Consumer: ({ children }) => children({}),
    })),
    createInteropElement: jest.fn((component, props, ...children) => {
      return component;
    }),
    interop: jest.fn(Component => Component),
    styled: jest.fn(Component => Component),
    default: {
      cssInterop: cssInteropMock,
    },
  };
});

jest.mock('react-native-css-interop/jsx-runtime', () => {
  const originalRuntime = require('react/jsx-runtime');
  return originalRuntime;
});

// Mock NativeWind
jest.mock('nativewind', () => ({
  styled: jest.fn(component => component),
  useColorScheme: jest.fn(() => ({
    colorScheme: 'light',
    setColorScheme: jest.fn(),
    toggleColorScheme: jest.fn(),
  })),
  withExpoSnack: jest.fn(fn => fn),
  vars: jest.fn(varObj => varObj),
  cssInterop: jest.fn(Component => Component),
}));

// Mock Expo Constants
jest.mock('expo-constants', () => ({
  default: {
    expoConfig: {
      extra: {
        apiUrl: 'http://localhost:8000',
        wsUrl: 'ws://localhost:8000',
      },
    },
    executionEnvironment: 'standalone',
    isDevice: false,
  },
}));

// Mock AsyncStorage
jest.mock('@react-native-async-storage/async-storage', () => ({
  getItem: jest.fn(() => Promise.resolve(null)),
  setItem: jest.fn(() => Promise.resolve()),
  removeItem: jest.fn(() => Promise.resolve()),
  clear: jest.fn(() => Promise.resolve()),
  getAllKeys: jest.fn(() => Promise.resolve([])),
  multiGet: jest.fn(() => Promise.resolve([])),
  multiSet: jest.fn(() => Promise.resolve()),
  multiRemove: jest.fn(() => Promise.resolve()),
}));

// Mock lucide-react-native
jest.mock('lucide-react-native', () => {
  const React = require('react');
  const icons = {};
  return new Proxy(icons, {
    get: (target, prop) => {
      if (!target[prop]) {
        target[prop] = React.forwardRef((props, ref) =>
          React.createElement('div', {
            ...props,
            ref,
            'data-testid': props.testID,
            className: `lucide-icon lucide-${prop.toLowerCase()}`,
          })
        );
      }
      return target[prop];
    },
  });
});

// Mock Expo Router (essential for navigation testing)
jest.mock('expo-router', () => {
  const React = require('react');
  return {
    useRouter: jest.fn(() => ({
      push: jest.fn(),
      back: jest.fn(),
      replace: jest.fn(),
      canGoBack: jest.fn(() => true),
    })),
    useLocalSearchParams: jest.fn(() => ({})),
    usePathname: jest.fn(() => '/'),
    useGlobalSearchParams: jest.fn(() => ({})),
    Link: React.forwardRef((props, ref) =>
      React.createElement('a', {
        ...props,
        ref,
        'data-testid': props.testID,
        href: props.href,
      })
    ),
    Stack: ({ children, ...props }) => React.createElement('div', props, children),
    Tabs: ({ children, ...props }) => React.createElement('div', props, children),
    router: {
      push: jest.fn(),
      back: jest.fn(),
      replace: jest.fn(),
      canGoBack: jest.fn(() => true),
    },
  };
});

// Mock react-hook-form
jest.mock('react-hook-form', () => ({
  useForm: jest.fn(() => ({
    control: {},
    handleSubmit: jest.fn(fn => () => fn),
    formState: { errors: {} },
    setValue: jest.fn(),
    getValues: jest.fn(),
    watch: jest.fn(),
    reset: jest.fn(),
  })),
  Controller: ({ render }) =>
    render({
      field: {
        onChange: jest.fn(),
        onBlur: jest.fn(),
        value: '',
        name: 'test',
      },
      fieldState: { error: null },
      formState: { errors: {} },
    }),
}));

// Console error suppression (optional - comment out to see errors)
const originalError = console.error;
beforeAll(() => {
  console.error = (...args) => {
    if (
      typeof args[0] === 'string' &&
      (args[0].includes('Warning: ReactDOM.render') ||
        args[0].includes('Warning: React.createElement'))
    ) {
      return;
    }
    originalError.call(console, ...args);
  };
});

afterAll(() => {
  console.error = originalError;
});
