// Simplified Jest setup focused on business-critical functionality
// Optimized for Aprende Comigo EdTech platform testing

import React from 'react';
import '@testing-library/jest-native/extend-expect';
import '@testing-library/jest-dom';

// Define __DEV__ for test environment
global.__DEV__ = process.env.NODE_ENV !== 'production';

// Mock React lazy for dynamic imports in tests
jest.mock('react', () => {
  const actualReact = jest.requireActual('react');
  return {
    ...actualReact,
    lazy: jest.fn((importFn) => {
      // For tests, resolve the import immediately and return the component
      const Component = (props) => {
        const [LoadedComponent, setLoadedComponent] = actualReact.useState(null);
        
        actualReact.useEffect(() => {
          importFn().then((module) => {
            setLoadedComponent(() => module.default || module);
          }).catch(() => {
            // Fallback for failed imports
            setLoadedComponent(() => () => actualReact.createElement('div', { 'data-testid': 'lazy-fallback' }, 'Loading...'));
          });
        }, []);

        if (!LoadedComponent) {
          return actualReact.createElement('div', { 'data-testid': 'lazy-loading' }, 'Loading...');
        }

        return actualReact.createElement(LoadedComponent, props);
      };
      
      Component.displayName = 'LazyComponent';
      return Component;
    }),
  };
});

// ================================
// REACT NATIVE CORE MOCKING
// ================================

jest.mock('react-native', () => {
  const React = require('react');
  
  const createMockComponent = (displayName) => {
    const Component = React.forwardRef((props, ref) => {
      const { children, testID, ...otherProps } = props;
      return React.createElement('div', {
        ...otherProps,
        ref,
        'data-testid': testID || displayName,
        className: `mock-${displayName.toLowerCase()}`,
      }, children);
    });
    Component.displayName = displayName;
    return Component;
  };

  const TextInput = (props) => {
    const { value, onChangeText, placeholder, testID, editable = true, ...otherProps } = props;
    return React.createElement('input', {
      ...otherProps,
      type: 'text',
      value: value || '',
      placeholder,
      disabled: !editable,
      'data-testid': testID || 'TextInput',
      onChange: (e) => onChangeText && onChangeText(e.target.value),
      className: 'mock-textinput',
    });
  };

  const Pressable = (props) => {
    const { children, onPress, disabled, testID, ...otherProps } = props;
    return React.createElement('button', {
      ...otherProps,
      disabled,
      'data-testid': testID || 'Pressable',
      onClick: disabled ? undefined : onPress,
      className: `mock-pressable ${disabled ? 'disabled' : ''}`,
    }, children);
  };

  return {
    View: createMockComponent('View'),
    Text: createMockComponent('Text'),
    TextInput,
    Pressable,
    ScrollView: createMockComponent('ScrollView'),
    FlatList: createMockComponent('FlatList'),
    Image: createMockComponent('Image'),
    SafeAreaView: createMockComponent('SafeAreaView'),
    Platform: { OS: 'web', select: (spec) => spec.web || spec.default },
    Dimensions: { get: () => ({ width: 375, height: 667 }) },
    StyleSheet: { create: (styles) => styles, flatten: (style) => style },
  };
});

// ================================
// GENERIC UI COMPONENT FACTORY
// ================================
// Replaces 583 lines of individual Gluestack UI mocks

const createUIComponentFactory = (componentNames) => {
  const components = {};
  componentNames.forEach(name => {
    components[name] = React.forwardRef((props, ref) => {
      const { children, onPress, testID, ...otherProps } = props;
      const elementType = onPress ? 'button' : 'div';
      return React.createElement(elementType, {
        ...otherProps,
        ref,
        'data-testid': testID || name,
        onClick: onPress,
        className: `gluestack-${name.toLowerCase()}`,
      }, children);
    });
  });
  return components;
};

// Mock all Gluestack UI components with factory
jest.mock('@/components/ui/box', () => createUIComponentFactory(['Box']));
jest.mock('@/components/ui/button', () => createUIComponentFactory(['Button', 'ButtonText', 'ButtonIcon']));
jest.mock('@/components/ui/card', () => createUIComponentFactory(['Card']));
jest.mock('@/components/ui/heading', () => createUIComponentFactory(['Heading']));
jest.mock('@/components/ui/hstack', () => createUIComponentFactory(['HStack']));
jest.mock('@/components/ui/vstack', () => createUIComponentFactory(['VStack']));
jest.mock('@/components/ui/text', () => createUIComponentFactory(['Text']));
jest.mock('@/components/ui/view', () => createUIComponentFactory(['View']));
jest.mock('@/components/ui/safe-area-view', () => createUIComponentFactory(['SafeAreaView']));
jest.mock('@/components/ui/pressable', () => createUIComponentFactory(['Pressable']));
jest.mock('@/components/ui/divider', () => createUIComponentFactory(['Divider']));
jest.mock('@/components/ui/link', () => createUIComponentFactory(['Link', 'LinkText']));

// Mock form components (critical for business functionality)
jest.mock('@/components/ui/input', () => {
  const React = require('react');
  const { TextInput } = require('react-native');
  
  return {
    Input: createUIComponentFactory(['Input']).Input,
    InputField: (props) => React.createElement(TextInput, {
      testID: 'InputField',
      ...props,
    }),
  };
});

jest.mock('@/components/ui/form-control', () => createUIComponentFactory([
  'FormControl', 'FormControlLabel', 'FormControlLabelText',
  'FormControlError', 'FormControlErrorText', 'FormControlHelper', 'FormControlHelperText'
]));

// ================================
// GENERIC ICON & SVG FACTORY
// ================================
// Replaces 49 lines of individual SVG mocks + 20 lines of icon mocks

const createIconFactory = (iconNames = []) => {
  const React = require('react');
  return new Proxy({}, {
    get: (target, prop) => {
      if (!target[prop]) {
        target[prop] = React.forwardRef((props, ref) =>
          React.createElement('div', {
            ...props,
            ref,
            'data-testid': props.testID || prop,
            className: `mock-icon mock-${String(prop).toLowerCase()}`,
          })
        );
      }
      return target[prop];
    }
  });
};

jest.mock('react-native-svg', () => createIconFactory());
jest.mock('lucide-react-native', () => createIconFactory());
jest.mock('@/components/ui/icon', () => createIconFactory(['Icon', 'ArrowLeftIcon']));

// ================================
// SIMPLIFIED WEBSOCKET MOCKING
// ================================
// Simplified from 206 lines to ~30 lines, keeping business-critical functionality

jest.mock('@/services/websocket/WebSocketClient', () => {
  const EventEmitter = require('events');

  class MockWebSocketClient extends EventEmitter {
    constructor(config = {}) {
      super();
      this.isConnectedState = false;
      this.sentMessages = [];
      
      // Auto-connect for tests
      setTimeout(() => {
        this.isConnectedState = true;
        this.emit('connect');
      }, 10);
    }

    send(message) {
      if (this.isConnectedState) {
        this.sentMessages.push(JSON.stringify(message));
      }
    }

    isConnected() { return this.isConnectedState; }
    disconnect() { this.isConnectedState = false; this.emit('disconnect'); }
    onMessage(listener) { this.on('message', listener); }
    dispose() { this.removeAllListeners(); }
    
    // Test helpers
    simulateMessage(data) { this.emit('message', data); }
    getSentMessages() { return this.sentMessages; }
  }

  return { WebSocketClient: MockWebSocketClient };
});

// ================================
// BUSINESS-CRITICAL SERVICE MOCKS
// ================================

// Authentication (critical for all user flows)
jest.mock('@react-native-async-storage/async-storage', () => ({
  getItem: jest.fn(() => Promise.resolve(null)),
  setItem: jest.fn(() => Promise.resolve()),
  removeItem: jest.fn(() => Promise.resolve()),
  clear: jest.fn(() => Promise.resolve()),
}));

jest.mock('@/services/websocket/auth/AsyncStorageAuthProvider', () => ({
  AsyncStorageAuthProvider: jest.fn(() => ({
    getToken: jest.fn(async () => {
      const AsyncStorage = jest.requireMock('@react-native-async-storage/async-storage');
      const token = await AsyncStorage.getItem('authToken');
      if (!token) throw new Error('No authentication token found');
      return token;
    }),
  })),
}));

// Navigation (critical for app flow)
jest.mock('expo-router', () => {
  const React = require('react');
  return {
    useRouter: jest.fn(() => ({
      push: jest.fn(),
      back: jest.fn(),
      replace: jest.fn(),
    })),
    useLocalSearchParams: jest.fn(() => ({})),
    Link: React.forwardRef((props, ref) =>
      React.createElement('a', { ...props, ref, href: props.href })
    ),
  };
});

// App configuration (critical for API/WebSocket URLs)
jest.mock('expo-constants', () => ({
  default: {
    expoConfig: {
      extra: {
        apiUrl: 'http://localhost:8000',
        wsUrl: 'ws://localhost:8000',
      },
    },
  },
}));

// Forms & Validation (critical for user interactions and payments)
jest.mock('react-hook-form', () => ({
  useForm: jest.fn(() => ({
    control: {},
    handleSubmit: jest.fn(fn => data => fn(data || {})),
    formState: { errors: {} },
    setValue: jest.fn(),
    getValues: jest.fn(() => ({})),
  })),
  Controller: ({ render, name }) => {
    const field = { onChange: jest.fn(), onBlur: jest.fn(), value: '', name };
    const fieldState = { error: null };
    const formState = { errors: {} };
    return render({ field, fieldState, formState });
  },
}));

jest.mock('@hookform/resolvers/zod', () => ({
  zodResolver: jest.fn(schema => data => {
    try {
      schema.parse(data);
      return { values: data, errors: {} };
    } catch (error) {
      return { values: {}, errors: { email: { message: 'Invalid email' } } };
    }
  }),
}));

jest.mock('zod', () => {
  const createChainableValidator = () => ({
    min: jest.fn(() => createChainableValidator()),
    max: jest.fn(() => createChainableValidator()),
    email: jest.fn(() => createChainableValidator()),
    optional: jest.fn(() => createChainableValidator()),
    refine: jest.fn(() => createChainableValidator()),
    length: jest.fn(() => createChainableValidator()),
    regex: jest.fn(() => createChainableValidator()),
    url: jest.fn(() => createChainableValidator()),
    or: jest.fn(() => createChainableValidator()),
    and: jest.fn(() => createChainableValidator()),
  });

  return {
    z: {
      object: jest.fn(() => ({
        parse: jest.fn(data => data),
        safeParse: jest.fn(data => ({ success: true, data })),
        refine: jest.fn(() => ({
          parse: jest.fn(data => data),
          safeParse: jest.fn(data => ({ success: true, data })),
        })),
      })),
      string: jest.fn(() => createChainableValidator()),
      number: jest.fn(() => createChainableValidator()),
      boolean: jest.fn(() => createChainableValidator()),
      literal: jest.fn(() => createChainableValidator()),
      enum: jest.fn(() => createChainableValidator()),
      union: jest.fn(() => createChainableValidator()),
      array: jest.fn(() => createChainableValidator()),
    },
  };
});

// ================================
// SIMPLIFIED NATIVE WIND & CSS
// ================================

jest.mock('react-native-css-interop', () => ({
  cssInterop: jest.fn(Component => Component),
  useColorScheme: jest.fn(() => 'light'),
  getColorScheme: jest.fn(() => 'light'),
  remapProps: jest.fn((Component, config) => Component),
  vars: jest.fn(() => ({})),
  createContext: jest.fn(() => ({
    Provider: ({ children }) => children,
    Consumer: ({ children }) => children({}),
  })),
  createInteropElement: jest.fn((type, props, ...children) => {
    // Use cached React reference to avoid infinite recursion
    if (!global.__mockReact) {
      global.__mockReact = jest.requireActual('react');
    }
    return global.__mockReact.createElement(type, props, ...children);
  }),
}));

jest.mock('react-native-css-interop/jsx-runtime', () => {
  const originalRuntime = require('react/jsx-runtime');
  return originalRuntime;
});

jest.mock('nativewind', () => ({
  styled: jest.fn(component => component),
  useColorScheme: jest.fn(() => ({ colorScheme: 'light' })),
}));

// ================================
// TESTING LIBRARY CONFIGURATION
// ================================

const { configure } = require('@testing-library/react-native');
configure({
  hostComponentNames: ['span', 'h1', 'div', 'button', 'input', 'Text', 'View'],
});

// Simplified error suppression for cleaner test output
const originalError = console.error;
beforeAll(() => {
  console.error = (...args) => {
    if (
      typeof args[0] === 'string' &&
      (args[0].includes('Warning:') ||
        args[0].includes('not wrapped in act(...)') ||
        args[0].includes('An update to'))
    ) {
      return;
    }
    originalError.call(console, ...args);
  };
});
afterAll(() => { console.error = originalError; });