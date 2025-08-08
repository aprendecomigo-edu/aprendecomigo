// Mock React Native Gesture Handler (not installed)
global.mockGestureHandler = true;

// Set global flag to disable host component detection in RNTL
process.env.RNTL_SKIP_AUTO_DETECT_COMPONENTS = 'true';

// Configure React Native Testing Library host components
Object.defineProperty(global, '__RNTLHostComponentNames', {
  value: new Set([
    'View', 'Text', 'TextInput', 'ScrollView', 'Image', 'TouchableOpacity', 
    'TouchableHighlight', 'TouchableWithoutFeedback', 'Button', 'FlatList',
    'SectionList', 'ActivityIndicator', 'SafeAreaView', 'KeyboardAvoidingView'
  ]),
  writable: false
});

// Enhanced NativeWind and CSS interop mocking  
jest.mock('react-native-css-interop', () => ({
  cssInterop: jest.fn((Component, config) => Component),
  remapProps: jest.fn((Component, config) => Component),
  useColorScheme: jest.fn(() => 'light'),
  vars: jest.fn(() => ({})),
  createContext: jest.fn(() => ({
    Provider: ({ children }) => children,
    Consumer: ({ children }) => children({}),
  })),
  createInteropElement: jest.fn((component, props, ...children) => {
    // Simply return the component without transformation for testing
    return component;
  }),
  interop: jest.fn((Component) => Component),
  styled: jest.fn((Component) => Component),
}));

jest.mock('react-native-css-interop/jsx-runtime', () => {
  // Import the default React jsx-runtime to use normal React behavior
  const originalRuntime = require('react/jsx-runtime');
  return originalRuntime;
});

// Mock NativeWind core functionality
jest.mock('nativewind', () => ({
  cssInterop: jest.fn((Component, config) => Component),
  styled: jest.fn(Component => Component),
  useColorScheme: jest.fn(() => ({
    colorScheme: 'light',
    setColorScheme: jest.fn(),
    toggleColorScheme: jest.fn(),
  })),
  vars: jest.fn(() => ({})),
  rem: jest.fn(value => `${value}rem`),
  hairlineWidth: jest.fn(() => 1),
}));

// Mock Gluestack UI NativeWind utilities
jest.mock('@gluestack-ui/nativewind-utils/tva', () => ({
  tva: jest.fn(() => jest.fn(() => 'mock-styles')),
}));

jest.mock('@gluestack-ui/nativewind-utils/withStyleContext', () => ({
  withStyleContext: jest.fn(Component => Component),
  useStyleContext: jest.fn(() => ({})),
}));

jest.mock('@gluestack-ui/nativewind-utils/withStyleContextAndStates', () => ({
  withStyleContextAndStates: jest.fn(Component => Component),
}));

// Mock additional Gluestack UI components and providers
jest.mock('@gluestack-ui/overlay', () => {
  const React = require('react');
  return {
    OverlayProvider: ({ children }) => React.createElement('div', { className: 'mock-overlay-provider' }, children),
    Overlay: React.forwardRef((props, ref) => 
      React.createElement('div', { ...props, ref, className: 'mock-overlay' })
    ),
  };
});

jest.mock('@gluestack-ui/toast', () => {
  const React = require('react');
  return {
    ToastProvider: ({ children }) => React.createElement('div', { className: 'mock-toast-provider' }, children),
    Toast: React.forwardRef((props, ref) => 
      React.createElement('div', { ...props, ref, className: 'mock-toast' })
    ),
    ToastTitle: React.forwardRef((props, ref) => 
      React.createElement('div', { ...props, ref, className: 'mock-toast-title' })
    ),
    ToastDescription: React.forwardRef((props, ref) => 
      React.createElement('div', { ...props, ref, className: 'mock-toast-description' })
    ),
    useToast: jest.fn(() => ({
      show: jest.fn(),
      close: jest.fn(),
      closeAll: jest.fn(),
    })),
  };
});

// Note: React Native Reanimated mock removed as it's not installed
// If needed later, uncomment and install the dependency first

// Note: React Native Gesture Handler mock removed as it's not installed
// If needed later, uncomment and install the dependency first

// Mock Expo modules
jest.mock('expo-router', () => ({
  useRouter: () => ({
    push: jest.fn(),
    back: jest.fn(),
    replace: jest.fn(),
    canGoBack: jest.fn(() => true),
  }),
  useLocalSearchParams: jest.fn(() => ({})),
  usePathname: jest.fn(() => '/'),
  useGlobalSearchParams: jest.fn(() => ({})),
  Link: ({ children, ...props }) => children,
  Stack: ({ children }) => children,
  Tabs: ({ children }) => children,
}));

jest.mock('@unitools/router', () => ({
  __esModule: true,
  default: () => ({
    push: jest.fn(),
    back: jest.fn(),
    replace: jest.fn(),
    canGoBack: jest.fn(() => true),
  }),
}));

// Mock AsyncStorage
jest.mock('@react-native-async-storage/async-storage', () => ({
  setItem: jest.fn(() => Promise.resolve()),
  getItem: jest.fn(() => Promise.resolve(null)),
  removeItem: jest.fn(() => Promise.resolve()),
  clear: jest.fn(() => Promise.resolve()),
  getAllKeys: jest.fn(() => Promise.resolve([])),
  multiGet: jest.fn(() => Promise.resolve([])),
  multiSet: jest.fn(() => Promise.resolve()),
  multiRemove: jest.fn(() => Promise.resolve()),
}));

// Enhanced React Native mocking with proper component implementations
jest.mock('react-native', () => {
  const React = require('react');

  // Helper function to create proper React components for mocking
  const mockComponent = (name, defaultProps = {}) => {
    const MockedComponent = React.forwardRef((props, ref) => {
      const { children, testID, accessibilityLabel, style, ...otherProps } = props;
      return React.createElement('div', {
        ...defaultProps,
        ...otherProps,
        ref,
        'data-testid': testID || name.toLowerCase(),
        'aria-label': accessibilityLabel,
        className: `mock-${name.toLowerCase()}`,
        style: typeof style === 'object' ? style : undefined,
      }, children);
    });
    MockedComponent.displayName = name; // Use the actual component name
    return MockedComponent;
  };

  // Special handling for input components
  const mockTextInput = React.forwardRef((props, ref) => {
    const { 
      onChangeText, 
      onFocus, 
      onBlur, 
      value, 
      defaultValue,
      placeholder,
      testID,
      secureTextEntry,
      multiline,
      ...otherProps 
    } = props;
    
    return React.createElement(multiline ? 'textarea' : 'input', {
      ...otherProps,
      ref,
      type: secureTextEntry ? 'password' : 'text',
      value: value || defaultValue || '',
      placeholder,
      'data-testid': testID || 'textinput',
      className: 'mock-textinput',
      onChange: onChangeText ? (e) => onChangeText(e.target.value) : undefined,
      onFocus,
      onBlur,
    });
  });
  mockTextInput.displayName = 'TextInput';

  // Special handling for pressable components
  const mockPressable = (name) => {
    const Component = React.forwardRef((props, ref) => {
      const { onPress, children, testID, disabled, ...otherProps } = props;
      return React.createElement('button', {
        ...otherProps,
        ref,
        onClick: onPress,
        disabled,
        'data-testid': testID || name.toLowerCase(),
        className: `mock-${name.toLowerCase()}`,
      }, children);
    });
    Component.displayName = name;
    return Component;
  };

  // Special handling for ScrollView
  const mockScrollView = React.forwardRef((props, ref) => {
    const { children, testID, horizontal, ...otherProps } = props;
    return React.createElement('div', {
      ...otherProps,
      ref,
      'data-testid': testID || 'mock-scrollview',
      className: `mock-scrollview ${horizontal ? 'horizontal' : 'vertical'}`,
      style: { overflow: 'auto', ...props.style }
    }, children);
  });
  mockScrollView.displayName = 'ScrollView';

  // Special handling for FlatList
  const mockFlatList = React.forwardRef((props, ref) => {
    const { 
      data = [], 
      renderItem, 
      keyExtractor, 
      testID,
      horizontal,
      ...otherProps 
    } = props;
    
    return React.createElement('div', {
      ...otherProps,
      ref,
      'data-testid': testID || 'mock-flatlist',
      className: `mock-flatlist ${horizontal ? 'horizontal' : 'vertical'}`,
    }, data.map((item, index) => {
      const key = keyExtractor ? keyExtractor(item, index) : index;
      return renderItem ? renderItem({ item, index }) : React.createElement('div', { key }, String(item));
    }));
  });
  mockFlatList.displayName = 'FlatList';

  return {
    // Platform APIs
    Platform: {
      OS: 'web',
      select: jest.fn((obj) => obj.web || obj.default),
      Version: 123,
      isPad: false,
      isTV: false,
      isTesting: true,
    },
    
    // Dimensions API with full support for Gluestack UI
    Dimensions: {
      get: jest.fn(() => ({ 
        width: 1024, 
        height: 768,
        scale: 1,
        fontScale: 1
      })),
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      // Add properties that Gluestack UI overlays expect
      currentHeight: 768,
      currentWidth: 1024,
    },
    
    // Appearance API for NativeWind color scheme support
    Appearance: {
      getColorScheme: jest.fn(() => 'light'),
      addChangeListener: jest.fn(() => ({ remove: jest.fn() })),
      removeChangeListener: jest.fn(),
    },
    
    // Alert API
    Alert: {
      alert: jest.fn(),
      prompt: jest.fn(),
    },
    
    // Core UI Components
    View: mockComponent('View'),
    Text: mockComponent('Text'),
    TextInput: mockTextInput,
    Image: mockComponent('Image'),
    ScrollView: mockScrollView,
    FlatList: mockFlatList,
    SectionList: mockComponent('SectionList'),
    ActivityIndicator: mockComponent('ActivityIndicator'),
    
    // Add hostComponentNames to help React Native Testing Library - this should be a getter
    get __hostComponentNames() {
      return new Set(['View', 'Text', 'TextInput', 'Image', 'ScrollView', 'TouchableOpacity', 'Button', 'FlatList', 'ActivityIndicator']);
    },
    
    // Interaction Components
    TouchableOpacity: mockPressable('TouchableOpacity'),
    TouchableHighlight: mockPressable('TouchableHighlight'),
    TouchableWithoutFeedback: mockPressable('TouchableWithoutFeedback'),
    Pressable: mockPressable('Pressable'),
    Button: React.forwardRef((props, ref) => {
      const { onPress, title, disabled, testID, ...otherProps } = props;
      return React.createElement('button', {
        ...otherProps,
        ref,
        onClick: onPress,
        disabled,
        'data-testid': testID || 'mock-button',
        className: 'mock-button',
      }, title);
    }),
    
    // Layout Components
    SafeAreaView: mockComponent('SafeAreaView'),
    KeyboardAvoidingView: mockComponent('KeyboardAvoidingView'),
    
    // Status Bar
    StatusBar: mockComponent('StatusBar'),
    
    // Style and Layout APIs
    StyleSheet: {
      create: jest.fn(styles => styles),
      compose: jest.fn(),
      flatten: jest.fn(style => style),
      absoluteFill: { position: 'absolute', top: 0, left: 0, bottom: 0, right: 0 },
      absoluteFillObject: { position: 'absolute', top: 0, left: 0, bottom: 0, right: 0 },
      hairlineWidth: 1,
    },
    
    // Accessibility
    AccessibilityInfo: {
      isReduceMotionEnabled: jest.fn(() => Promise.resolve(false)),
      isScreenReaderEnabled: jest.fn(() => Promise.resolve(false)),
      addEventListener: jest.fn(() => ({ remove: jest.fn() })),
      announceForAccessibility: jest.fn(),
    },
    
    // Keyboard
    Keyboard: {
      addListener: jest.fn(() => ({ remove: jest.fn() })),
      removeListener: jest.fn(),
      removeAllListeners: jest.fn(),
      dismiss: jest.fn(),
    },
    
    // Linking
    Linking: {
      openURL: jest.fn(() => Promise.resolve()),
      canOpenURL: jest.fn(() => Promise.resolve(true)),
      getInitialURL: jest.fn(() => Promise.resolve(null)),
      addEventListener: jest.fn(() => ({ remove: jest.fn() })),
    },
    
    // Gesture handling
    PanResponder: {
      create: jest.fn(() => ({
        panHandlers: {},
      })),
    },
    
    // Native modules and events
    NativeModules: {},
    DeviceEventEmitter: {
      addListener: jest.fn(() => ({ remove: jest.fn() })),
      removeAllListeners: jest.fn(),
      emit: jest.fn(),
    },
    NativeEventEmitter: jest.fn(() => ({
      addListener: jest.fn(() => ({ remove: jest.fn() })),
      removeAllListeners: jest.fn(),
    })),
    
    // App Registry
    AppRegistry: {
      registerComponent: jest.fn(),
      runApplication: jest.fn(),
    },
    
    // Animated API (basic mock)
    Animated: {
      View: mockComponent('AnimatedView'),
      Text: mockComponent('AnimatedText'),
      Value: jest.fn(() => ({
        setValue: jest.fn(),
        addListener: jest.fn(() => 'listener_id'),
        removeListener: jest.fn(),
        interpolate: jest.fn(() => 'interpolated_value'),
      })),
      timing: jest.fn(() => ({
        start: jest.fn(callback => callback && callback({ finished: true })),
        stop: jest.fn(),
        reset: jest.fn(),
      })),
      spring: jest.fn(() => ({
        start: jest.fn(callback => callback && callback({ finished: true })),
        stop: jest.fn(),
        reset: jest.fn(),
      })),
      sequence: jest.fn(() => ({
        start: jest.fn(callback => callback && callback({ finished: true })),
      })),
      parallel: jest.fn(() => ({
        start: jest.fn(callback => callback && callback({ finished: true })),
      })),
      decay: jest.fn(() => ({
        start: jest.fn(callback => callback && callback({ finished: true })),
      })),
      loop: jest.fn(() => ({
        start: jest.fn(callback => callback && callback({ finished: true })),
      })),
      createAnimatedComponent: jest.fn(component => component),
      event: jest.fn(() => jest.fn()),
    },
  };
});

// Mock Expo Font
jest.mock('expo-font', () => ({
  loadAsync: jest.fn(() => Promise.resolve()),
  isLoaded: jest.fn(() => true),
}));

// Mock Expo Asset
jest.mock('expo-asset', () => ({
  Asset: {
    loadAsync: jest.fn(() => Promise.resolve()),
    fromModule: jest.fn(() => ({ downloadAsync: jest.fn(() => Promise.resolve()) })),
  },
}));

// Mock React Native SVG
jest.mock('react-native-svg', () => {
  const React = require('react');
  
  const mockSvgComponent = (name) => React.forwardRef((props, ref) => {
    const { children, testID, ...otherProps } = props;
    return React.createElement('div', {
      ...otherProps,
      ref,
      'data-testid': testID || `mock-${name.toLowerCase()}`,
      className: `mock-svg-${name.toLowerCase()}`,
    }, children);
  });

  return {
    Svg: mockSvgComponent('Svg'),
    Circle: mockSvgComponent('Circle'),
    Ellipse: mockSvgComponent('Ellipse'),
    G: mockSvgComponent('G'),
    Text: mockSvgComponent('SvgText'),
    TSpan: mockSvgComponent('TSpan'),
    TextPath: mockSvgComponent('TextPath'),
    Path: mockSvgComponent('Path'),
    Polygon: mockSvgComponent('Polygon'),
    Polyline: mockSvgComponent('Polyline'),
    Line: mockSvgComponent('Line'),
    Rect: mockSvgComponent('Rect'),
    Use: mockSvgComponent('Use'),
    Image: mockSvgComponent('SvgImage'),
    Symbol: mockSvgComponent('Symbol'),
    Defs: mockSvgComponent('Defs'),
    LinearGradient: mockSvgComponent('LinearGradient'),
    RadialGradient: mockSvgComponent('RadialGradient'),
    Stop: mockSvgComponent('Stop'),
    ClipPath: mockSvgComponent('ClipPath'),
    Pattern: mockSvgComponent('Pattern'),
    Mask: mockSvgComponent('Mask'),
  };
});

// Mock React Native Vector Icons
jest.mock('lucide-react-native', () => {
  const React = require('react');

  const MockIcon = React.forwardRef((props, ref) => {
    const { testID, size = 24, color = 'black', ...otherProps } = props;
    return React.createElement('div', {
      ...otherProps,
      ref,
      'data-testid': testID || 'mock-icon',
      className: 'mock-lucide-icon',
      style: { width: size, height: size, color },
    }, '📄'); // Simple icon placeholder
  });
  MockIcon.displayName = 'MockLucideIcon';

  return new Proxy(
    {},
    {
      get: () => MockIcon,
    }
  );
});

// Mock API client
jest.mock('@/api/apiClient', () => ({
  __esModule: true,
  default: {
    get: jest.fn(() => Promise.resolve({ data: { data: {} } })),
    post: jest.fn(() => Promise.resolve({ data: { data: {} } })),
    put: jest.fn(() => Promise.resolve({ data: { data: {} } })),
    delete: jest.fn(() => Promise.resolve({ data: { data: {} } })),
  },
}));

// Mock form data for File uploads
global.FormData = class FormData {
  constructor() {
    this.data = {};
  }

  append(key, value) {
    this.data[key] = value;
  }

  get(key) {
    return this.data[key];
  }

  has(key) {
    return key in this.data;
  }
};

// Mock Image component
jest.mock('@/components/ui/image', () => {
  const React = require('react');
  return {
    Image: React.forwardRef((props, ref) =>
      React.createElement('View', { ...props, ref, testID: 'mock-image' })
    ),
  };
});

// Mock WebSocket
global.WebSocket = class WebSocket {
  constructor(url) {
    this.url = url;
    this.readyState = WebSocket.CONNECTING;
    setTimeout(() => {
      this.readyState = WebSocket.OPEN;
      if (this.onopen) this.onopen();
    }, 100);
  }

  send(data) {
    // Mock send
  }

  close() {
    this.readyState = WebSocket.CLOSED;
    if (this.onclose) this.onclose();
  }

  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;
};

// Mock timers for auto-save testing
jest.useFakeTimers();

// Global test utilities
global.flushPromises = () => new Promise(resolve => setTimeout(resolve, 0));

// Console warning suppression for known issues
const originalConsoleWarn = console.warn;
const originalConsoleError = console.error;

console.warn = (...args) => {
  // Suppress known warnings during tests
  const warningString = args[0];
  if (
    typeof warningString === 'string' &&
    (warningString.includes('componentWillReceiveProps') ||
      warningString.includes('componentWillUpdate'))
  ) {
    return;
  }
  originalConsoleWarn.apply(console, args);
};

console.error = (...args) => {
  // Suppress known errors during tests
  const errorString = args[0];
  if (
    typeof errorString === 'string' &&
    errorString.includes('Warning: ReactDOM.render is no longer supported')
  ) {
    return;
  }
  originalConsoleError.apply(console, args);
};

// Configure React Native Testing Library after all mocks are set up
try {
  const { configure } = require('@testing-library/react-native');
  configure({
    hostComponentNames: new Set([
      'View', 'Text', 'TextInput', 'ScrollView', 'Image', 'TouchableOpacity', 
      'TouchableHighlight', 'TouchableWithoutFeedback', 'Button', 'FlatList',
      'SectionList', 'ActivityIndicator', 'SafeAreaView', 'KeyboardAvoidingView'
    ])
  });
} catch (e) {
  // If configure doesn't exist, continue without error logging
}

// Cleanup after each test
afterEach(() => {
  jest.clearAllMocks();
  jest.clearAllTimers();
});
