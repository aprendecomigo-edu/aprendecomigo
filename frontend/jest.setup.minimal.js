// Minimal Jest setup that works with jest-expo preset
// jest-expo already provides React Native mocks, so we don't override them

import React from 'react';
import '@testing-library/jest-native/extend-expect';
import '@testing-library/jest-dom';

// Don't mock react-native at all - let jest-expo handle it completely
// jest-expo preset includes proper React Native mocks

// Configure React Native Testing Library properly
const { configure } = require('@testing-library/react-native');
configure({
  // Enable detection of common host components including our mocked ones
  hostComponentNames: ['span', 'h1', 'div', 'button', 'input', 'Text', 'View'],
});

// Mock Gluestack UI components as proper React components
jest.mock('@/components/ui/box', () => {
  const React = require('react');
  return {
    Box: React.forwardRef(({ children, ...props }, ref) =>
      React.createElement(
        'div',
        {
          ...props,
          ref,
          'data-testid': props.testID || 'Box',
          className: 'mock-box',
        },
        children
      )
    ),
  };
});

jest.mock('@/components/ui/button', () => {
  const React = require('react');
  const { Pressable, Text } = require('react-native');
  return {
    Button: ({ children, onPress, disabled, ...props }) => {
      return React.createElement(
        Pressable,
        {
          testID: 'Button',
          disabled: disabled,
          onPress: onPress,
          accessibilityRole: 'button',
        },
        children
      );
    },
    ButtonText: ({ children, ...props }) => {
      return React.createElement(
        Text,
        {
          testID: props.testID || 'ButtonText',
          ...props,
        },
        children
      );
    },
    ButtonIcon: ({ children, ...props }) => {
      return React.createElement(
        Text,
        {
          testID: 'ButtonIcon',
        },
        children
      );
    },
  };
});

jest.mock('@/components/ui/card', () => {
  const React = require('react');
  return {
    Card: React.forwardRef(({ children, ...props }, ref) =>
      React.createElement(
        'div',
        {
          ...props,
          ref,
          'data-testid': props.testID,
          className: `gluestack-card ${props.className || ''}`,
        },
        children
      )
    ),
  };
});

jest.mock('@/components/ui/heading', () => {
  const React = require('react');
  const { Text } = require('react-native');
  return {
    Heading: React.forwardRef(({ children, ...props }, ref) => {
      return React.createElement(
        Text,
        {
          ref,
          testID: props.testID || 'Heading',
          accessibilityRole: 'header',
          ...props,
        },
        children
      );
    }),
  };
});

jest.mock('@/components/ui/hstack', () => {
  const React = require('react');
  return {
    HStack: React.forwardRef(({ children, ...props }, ref) =>
      React.createElement(
        'div',
        {
          ...props,
          ref,
          'data-testid': props.testID || 'HStack',
          className: 'mock-hstack',
        },
        children
      )
    ),
  };
});

jest.mock('@/components/ui/icon', () => {
  const React = require('react');
  const { View } = require('react-native');
  return {
    Icon: React.forwardRef((props, ref) =>
      React.createElement(View, {
        ...props,
        ref,
        testID: props.testID || 'Icon',
      })
    ),
    ArrowLeftIcon: React.forwardRef((props, ref) =>
      React.createElement(View, {
        ...props,
        ref,
        testID: props.testID || 'ArrowLeftIcon',
      })
    ),
  };
});

jest.mock('@/components/ui/text', () => {
  const React = require('react');
  const { Text: RNText } = require('react-native');

  return {
    Text: React.forwardRef(({ children, ...props }, ref) => {
      return React.createElement(
        RNText,
        {
          ref,
          testID: props.testID || 'Text',
          ...props,
        },
        children
      );
    }),
  };
});

jest.mock('@/components/ui/vstack', () => {
  const React = require('react');
  const { View } = require('react-native');
  return {
    VStack: React.forwardRef(({ children, ...props }, ref) =>
      React.createElement(
        View,
        {
          ...props,
          ref,
          testID: props.testID || 'VStack',
        },
        children
      )
    ),
  };
});

jest.mock('@/components/ui/view', () => {
  const React = require('react');
  const { View: RNView } = require('react-native');

  return {
    View: React.forwardRef(({ children, ...props }, ref) => {
      return React.createElement(
        RNView,
        {
          ...props,
          ref,
          testID: props.testID || 'View',
        },
        children
      );
    }),
  };
});

jest.mock('@/components/ui/safe-area-view', () => {
  const React = require('react');
  const { View } = require('react-native');

  return {
    SafeAreaView: React.forwardRef(({ children, ...props }, ref) => {
      return React.createElement(
        View,
        {
          ...props,
          ref,
          testID: props.testID || 'SafeAreaView',
        },
        children
      );
    }),
  };
});

// Mock additional UI components needed for auth tests
jest.mock('@/components/ui/input', () => {
  const React = require('react');
  const { View, TextInput } = require('react-native');

  return {
    Input: ({ children, ...props }) => {
      return React.createElement(
        View,
        {
          testID: 'Input',
        },
        children
      );
    },
    InputField: ({
      placeholder,
      value,
      onChangeText,
      onBlur,
      onFocus,
      onSubmitEditing,
      ...props
    }) => {
      return React.createElement(TextInput, {
        ...props,
        testID: props.testID || 'InputField',
        placeholder: placeholder,
        value: value,
        onChangeText: onChangeText,
        onBlur: onBlur,
        onFocus: onFocus,
        onSubmitEditing: onSubmitEditing,
        returnKeyType: props.returnKeyType || 'done',
      });
    },
  };
});

jest.mock('@/components/ui/form-control', () => {
  const React = require('react');
  const { View, Text } = require('react-native');

  return {
    FormControl: ({ children, ...props }) => {
      return React.createElement(
        View,
        {
          testID: 'FormControl',
        },
        children
      );
    },
    FormControlLabel: ({ children, ...props }) => {
      return React.createElement(
        View,
        {
          testID: 'FormControlLabel',
        },
        children
      );
    },
    FormControlLabelText: ({ children, ...props }) => {
      return React.createElement(
        Text,
        {
          testID: props.testID || 'FormControlLabelText',
          ...props,
        },
        children
      );
    },
    FormControlError: ({ children, ...props }) => {
      return React.createElement(
        View,
        {
          testID: 'FormControlError',
        },
        children
      );
    },
    FormControlErrorIcon: ({ children, ...props }) => {
      return React.createElement(
        View,
        {
          testID: 'FormControlErrorIcon',
        },
        children
      );
    },
    FormControlErrorText: ({ children, ...props }) => {
      return React.createElement(
        Text,
        {
          testID: props.testID || 'FormControlErrorText',
          ...props,
        },
        children
      );
    },
    FormControlHelper: ({ children, ...props }) => {
      return React.createElement(
        View,
        {
          testID: 'FormControlHelper',
        },
        children
      );
    },
    FormControlHelperText: ({ children, ...props }) => {
      return React.createElement(
        Text,
        {
          testID: props.testID || 'FormControlHelperText',
          ...props,
        },
        children
      );
    },
  };
});

jest.mock('@/components/ui/pressable', () => {
  const React = require('react');
  const { Pressable: RNPressable } = require('react-native');

  return {
    Pressable: React.forwardRef(({ children, ...props }, ref) =>
      React.createElement(
        RNPressable,
        {
          ...props,
          ref,
          testID: props.testID || 'Pressable',
          onPress: props.onPress,
          disabled: props.disabled,
        },
        children
      )
    ),
  };
});

jest.mock('@/components/ui/radio', () => {
  const React = require('react');
  return {
    RadioGroup: React.forwardRef(({ children, value, onChange, ...props }, ref) => {
      const handleChildClick = childValue => {
        if (onChange) {
          onChange(childValue);
        }
      };

      return React.createElement(
        'div',
        {
          ...props,
          ref,
          'data-testid': props.testID,
          className: `gluestack-radio-group ${props.className || ''}`,
          'data-value': value,
        },
        React.Children.map(children, child =>
          React.isValidElement(child)
            ? React.cloneElement(child, {
                onClick: () => handleChildClick(child.props.value),
                'data-selected': child.props.value === value,
              })
            : child
        )
      );
    }),
    Radio: React.forwardRef(({ children, value, ...props }, ref) =>
      React.createElement(
        'label',
        {
          ...props,
          ref,
          'data-testid': props.testID,
          'data-value': value,
          className: `gluestack-radio ${props.className || ''}`,
          'aria-label': props.value,
        },
        children
      )
    ),
    RadioIndicator: React.forwardRef(({ children, ...props }, ref) =>
      React.createElement(
        'span',
        {
          ...props,
          ref,
          'data-testid': props.testID,
          className: `gluestack-radio-indicator ${props.className || ''}`,
        },
        children
      )
    ),
    RadioIcon: React.forwardRef(({ children, ...props }, ref) =>
      React.createElement(
        'span',
        {
          ...props,
          ref,
          'data-testid': props.testID,
          className: `gluestack-radio-icon ${props.className || ''}`,
        },
        children
      )
    ),
    RadioLabel: React.forwardRef(({ children, ...props }, ref) =>
      React.createElement(
        'span',
        {
          ...props,
          ref,
          'data-testid': props.testID,
          className: `gluestack-radio-label ${props.className || ''}`,
        },
        children
      )
    ),
  };
});

jest.mock('@/components/ui/tabs', () => {
  const React = require('react');
  return {
    Tabs: React.forwardRef(({ children, items, activeTab, onTabChange, ...props }, ref) => {
      const handleTabClick = tabId => {
        if (onTabChange) {
          onTabChange(tabId);
        }
      };

      return React.createElement(
        'div',
        {
          ...props,
          ref,
          'data-testid': props.testID,
          className: `gluestack-tabs ${props.className || ''}`,
          'data-active-tab': activeTab,
        },
        [
          // Render tab buttons
          items &&
            items.map(item =>
              React.createElement(
                'button',
                {
                  key: item.id,
                  onClick: () => handleTabClick(item.id),
                  'data-tab-id': item.id,
                  'data-active': item.id === activeTab,
                  'aria-label': item.label,
                  className: 'tab-button',
                },
                item.label
              )
            ),
          // Render children
          children,
        ]
      );
    }),
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
    Link: React.forwardRef(({ children, ...props }, ref) =>
      React.createElement(
        'a',
        {
          ...props,
          ref,
          'data-testid': props.testID,
          href: props.href,
          className: `gluestack-link ${props.className || ''}`,
        },
        children
      )
    ),
    LinkText: React.forwardRef(({ children, ...props }, ref) =>
      React.createElement(
        'span',
        {
          ...props,
          ref,
          'data-testid': props.testID,
          className: `gluestack-link-text ${props.className || ''}`,
        },
        children
      )
    ),
  };
});

// Mock AuthLayout and ErrorBoundary
jest.mock('@/components/auth/AuthLayout', () => {
  const React = require('react');
  const { View } = require('react-native');
  return {
    AuthLayout: ({ children, ...props }) => {
      // Ensure children is properly rendered
      return React.createElement(
        View,
        {
          ...props,
          testID: 'AuthLayout',
        },
        typeof children === 'function' ? null : children
      );
    },
  };
});

jest.mock('@/components/ErrorBoundary', () => {
  const React = require('react');
  return {
    ErrorBoundary: React.forwardRef(({ children, ...props }, ref) =>
      React.createElement(
        'div',
        {
          ...props,
          ref,
          'data-testid': 'ErrorBoundary',
          className: 'error-boundary',
        },
        children
      )
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
    default: React.forwardRef(({ children, ...props }, ref) =>
      React.createElement(
        'a',
        {
          ...props,
          ref,
          'data-testid': props.testID,
          href: props.href,
        },
        children
      )
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

// Mock WebSocket services for testing
jest.mock('@/services/websocket/WebSocketClient', () => {
  const EventEmitter = require('events');

  class MockWebSocketClient extends EventEmitter {
    constructor(config) {
      super();
      this.config = config;
      this.url = config.url; // Store URL for tests
      this.isConnectedState = false;
      this.disposed = false;
      this.messageHandlers = new Map();
      this.reconnectAttempts = 0;
      this.sentMessages = [];
      this._readyState = 3; // CLOSED by default
      this.canReconnect = !!config.reconnection; // Only allow reconnection if config supports it

      // Register this instance globally for tests
      if (!global.__mockWebSocketClients) {
        global.__mockWebSocketClients = [];
      }
      global.__mockWebSocketClients.push(this);
      global.__lastMockWebSocketClient = this;

      // Simulate async connection with token check
      setTimeout(async () => {
        if (this.disposed) return;

        // Check global connection failure first
        if (global.__webSocketGlobalFailure) {
          this.emit('error', new Error('WebSocket creation failed'));
          return;
        }

        // Check for auth token if auth provider exists
        if (config.auth) {
          try {
            const token = await config.auth.getToken();
            if (!token) {
              this.emit('error', new Error('No authentication token found'));
              return;
            }
            // Append token to URL for testing
            if (token && this.url.indexOf('?') === -1) {
              this.url = `${this.url}?token=${token}`;
            }
          } catch (error) {
            this.emit('error', error);
            return;
          }
        }

        this.isConnectedState = true;
        this._readyState = 1; // OPEN
        this.emit('connect');
      }, 10);
    }

    async connect() {
      if (this.disposed) {
        throw new Error('WebSocketClient has been disposed');
      }
      // Connection is handled in constructor with setTimeout
    }

    disconnect() {
      this.isConnectedState = false;
      this._readyState = 2; // CLOSING
      this.emit('disconnect');
      // Don't auto-transition to CLOSED immediately for unmount tests
    }

    send(message) {
      if (this.isConnectedState) {
        this.sentMessages.push(JSON.stringify(message));
      } else {
        if (__DEV__) {
          console.warn('WebSocket not connected, cannot send message');
        }
      }
    }

    isConnected() {
      return this.isConnectedState;
    }

    onConnect(listener) {
      this.on('connect', listener);
    }

    onDisconnect(listener) {
      this.on('disconnect', listener);
    }

    onMessage(listener) {
      this.messageHandlers.set('*', listener);
      // Check if this looks like the useWebSocketEnhanced pattern
      const listenerString = listener.toString();
      this.isEnhancedHook =
        listenerString.includes('setLastMessage') || listenerString.includes('typeof message');
    }

    onError(listener) {
      this.on('error', listener);
    }

    dispose() {
      this.disposed = true;
      this.isConnectedState = false;
      this._readyState = 2; // CLOSING when disposed
      this.removeAllListeners();
    }

    // Test helper methods
    simulateMessage(data) {
      const listener = this.messageHandlers.get('*');
      if (listener) {
        // Check if we should pass raw string messages (for useWebSocketEnhanced)
        if (typeof data === 'string' && this.isEnhancedHook) {
          // For useWebSocketEnhanced, pass the raw string
          listener(data);
        } else if (typeof data === 'string') {
          try {
            const messageObj = JSON.parse(data);
            listener(messageObj);
          } catch (error) {
            // For malformed JSON, don't call the listener but log error
            if (__DEV__) {
              console.error('Error parsing WebSocket message:', error); // TODO: Review for sensitive data
            }
            return; // Don't call listener for malformed JSON
          }
        } else {
          // Already an object
          listener(data);
        }
      }
    }

    simulateError(error) {
      this.emit('error', error || new Error('WebSocket error'));
    }

    simulateNetworkFailure() {
      this.isConnectedState = false;
      this._readyState = 3; // CLOSED
      this.simulateError();
      this.emit('disconnect');

      // Set up for reconnection simulation - simulate the reconnection logic
      if (!this.blockReconnection && this.canReconnect) {
        setTimeout(() => {
          if (!this.disposed) {
            this.isConnectedState = true;
            this._readyState = 1; // OPEN
            this.emit('connect');
          }
        }, 1000); // Match the reconnection delay expected by tests
      }
    }

    getSentMessages() {
      return this.sentMessages;
    }

    simulateNetworkFailureWithReconnectBlocking() {
      this.isConnectedState = false;
      this.simulateError();
      this.emit('disconnect');

      // Set a flag to prevent auto-reconnection
      this.blockReconnection = true;
    }

    // Additional test utilities that some tests might expect
    close(code = 1000, reason = 'Normal closure') {
      this.isConnectedState = false;
      this.emit('disconnect');
    }

    get readyState() {
      return this._readyState;
    }

    set readyState(value) {
      this._readyState = value;
      if (value === 1) {
        this.isConnectedState = true;
        this.emit('connect'); // Trigger connect event when manually set to OPEN
      } else if (value >= 2) {
        this.isConnectedState = false;
      }
    }

    // Add missing test utility methods
    getMessageQueue() {
      return this.sentMessages.map((msg, index) => ({
        data: msg,
        timestamp: Date.now() - (this.sentMessages.length - index) * 10,
      }));
    }
  }

  return {
    WebSocketClient: MockWebSocketClient,
  };
});

jest.mock('@/services/websocket/auth/AsyncStorageAuthProvider', () => {
  return {
    AsyncStorageAuthProvider: jest.fn().mockImplementation(() => ({
      getToken: jest.fn().mockImplementation(async () => {
        // Use jest module registry to get the current mock
        const AsyncStorage = jest.requireMock('@react-native-async-storage/async-storage');
        const token = await AsyncStorage.getItem('authToken');
        if (!token) {
          throw new Error('No authentication token found');
        }
        return token;
      }),
    })),
  };
});

// Mock WebSocket global objects that might be missing in Jest environment
// These mocks ensure compatibility with WebSocket-related tests in Node.js environment

// Force override of DOM Event constructors for Jest environment
// This ensures consistent behavior across different Node.js versions

// Mock CloseEvent (WebSocket close event)
global.CloseEvent = class CloseEvent extends Event {
  constructor(type, eventInitDict = {}) {
    super(type);
    this.code = eventInitDict.code || 1000;
    this.reason = eventInitDict.reason || '';
    this.wasClean = eventInitDict.wasClean !== undefined ? eventInitDict.wasClean : false;

    // Additional WebSocket close code constants for reference
    this.NORMAL_CLOSURE = 1000;
    this.GOING_AWAY = 1001;
    this.PROTOCOL_ERROR = 1002;
    this.UNSUPPORTED_DATA = 1003;
    this.NO_STATUS_RCVD = 1005;
    this.ABNORMAL_CLOSURE = 1006;
  }
};

// Add static constants to CloseEvent
global.CloseEvent.NORMAL_CLOSURE = 1000;
global.CloseEvent.GOING_AWAY = 1001;
global.CloseEvent.PROTOCOL_ERROR = 1002;
global.CloseEvent.UNSUPPORTED_DATA = 1003;
global.CloseEvent.NO_STATUS_RCVD = 1005;
global.CloseEvent.ABNORMAL_CLOSURE = 1006;

// Mock MessageEvent (WebSocket message event)
global.MessageEvent = class MessageEvent extends Event {
  constructor(type, eventInitDict) {
    super(type);
    // If eventInitDict is undefined, set data to undefined
    // If eventInitDict is provided but doesn't have data property, set data to undefined
    // If eventInitDict has data property, use that value (even if it's null or undefined)
    if (eventInitDict === undefined) {
      this.data = undefined;
    } else {
      this.data = eventInitDict.hasOwnProperty('data') ? eventInitDict.data : undefined;
    }
    this.origin = (eventInitDict && eventInitDict.origin) || '';
    this.lastEventId = (eventInitDict && eventInitDict.lastEventId) || '';
    this.source = (eventInitDict && eventInitDict.source) || null;
    this.ports = (eventInitDict && eventInitDict.ports) || [];
  }
};

// Mock ErrorEvent (WebSocket error event)
global.ErrorEvent = class ErrorEvent extends Event {
  constructor(type, eventInitDict = {}) {
    super(type);
    this.message = eventInitDict.message || '';
    this.filename = eventInitDict.filename || '';
    this.lineno = eventInitDict.lineno || 0;
    this.colno = eventInitDict.colno || 0;
    this.error = eventInitDict.error || null;
  }
};

// Mock WebSocket constants if not available
if (typeof global.WebSocket === 'undefined') {
  global.WebSocket = class MockWebSocket {
    static CONNECTING = 0;
    static OPEN = 1;
    static CLOSING = 2;
    static CLOSED = 3;

    constructor(url) {
      this.url = url;
      this.readyState = MockWebSocket.CONNECTING;
      this.onopen = null;
      this.onclose = null;
      this.onerror = null;
      this.onmessage = null;
    }

    send() {
      throw new Error('MockWebSocket: send() not implemented in Jest mock');
    }

    close() {
      this.readyState = MockWebSocket.CLOSED;
    }
  };
}

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
  // This gets overridden by WebSocketTestUtils.mockAsyncStorage() in tests
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
    handleSubmit: jest.fn(fn => data => fn(data || {})),
    formState: { errors: {} },
    setValue: jest.fn(),
    getValues: jest.fn(() => ({})),
    watch: jest.fn(() => ''),
    reset: jest.fn(),
  })),
  Controller: ({ render, name }) => {
    const React = require('react');
    const field = {
      onChange: jest.fn(),
      onBlur: jest.fn(),
      value: '',
      name: name || 'test',
    };
    const fieldState = { error: null };
    const formState = { errors: {} };

    return render({ field, fieldState, formState });
  },
}));

// Console error suppression (optional - comment out to see errors)
const originalError = console.error;
beforeAll(() => {
  console.error = (...args) => {
    if (
      typeof args[0] === 'string' &&
      (args[0].includes('Warning: ReactDOM.render') ||
        args[0].includes('Warning: React.createElement') ||
        args[0].includes('Warning: Functions are not valid as a React child'))
    ) {
      return;
    }
    originalError.call(console, ...args);
  };
});

afterAll(() => {
  console.error = originalError;
});

// Mock @hookform/resolvers/zod
jest.mock('@hookform/resolvers/zod', () => ({
  zodResolver: jest.fn(schema => data => {
    try {
      schema.parse(data);
      return { values: data, errors: {} };
    } catch (error) {
      return {
        values: {},
        errors: {
          email: { message: 'Invalid email' },
        },
      };
    }
  }),
}));

// Mock zod with chainable methods
jest.mock('zod', () => {
  const createStringValidator = () => ({
    min: jest.fn(() => createStringValidator()),
    max: jest.fn(() => createStringValidator()),
    email: jest.fn(() => createStringValidator()),
    url: jest.fn(() => createStringValidator()),
    regex: jest.fn(() => createStringValidator()),
    length: jest.fn(() => createStringValidator()),
    optional: jest.fn(() => createStringValidator()),
    refine: jest.fn(() => createStringValidator()),
    or: jest.fn(() => createStringValidator()),
    and: jest.fn(() => createStringValidator()),
  });

  return {
    z: {
      object: jest.fn(shape => ({
        parse: jest.fn(data => data),
        safeParse: jest.fn(data => ({ success: true, data })),
        refine: jest.fn(() => ({
          parse: jest.fn(data => data),
          safeParse: jest.fn(data => ({ success: true, data })),
        })),
      })),
      string: jest.fn(() => createStringValidator()),
      literal: jest.fn(() => createStringValidator()),
      enum: jest.fn(() => createStringValidator()),
      number: jest.fn(() => createStringValidator()),
      boolean: jest.fn(() => createStringValidator()),
      array: jest.fn(() => createStringValidator()),
      union: jest.fn(() => createStringValidator()),
      infer: jest.fn(),
    },
  };
});
