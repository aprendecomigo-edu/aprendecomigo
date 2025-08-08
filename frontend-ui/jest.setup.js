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
      // Simply return the component without transformation for testing
      return component;
    }),
    interop: jest.fn((Component) => Component),
    styled: jest.fn((Component) => Component),
    default: {
      cssInterop: cssInteropMock,
    }
  };
});

jest.mock('react-native-css-interop/jsx-runtime', () => {
  // Import the default React jsx-runtime to use normal React behavior
  const originalRuntime = require('react/jsx-runtime');
  return originalRuntime;
});

// Mock NativeWind core functionality with explicit __esModule
jest.mock('nativewind', () => {
  const cssInteropMock = jest.fn((Component, config) => {
    // Return the component unchanged for tests
    return Component;
  });
  
  return {
    __esModule: true,
    cssInterop: cssInteropMock,
    styled: jest.fn(Component => Component),
    useColorScheme: jest.fn(() => ({
      colorScheme: 'light',
      setColorScheme: jest.fn(),
      toggleColorScheme: jest.fn(),
    })),
    vars: jest.fn(() => ({})),
    rem: jest.fn(value => `${value}rem`),
    hairlineWidth: jest.fn(() => 1),
    default: {
      cssInterop: cssInteropMock,
    }
  };
});

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

// Mock for useBreakpointValue is in __mocks__ directory
// This allows better control and avoids module resolution issues

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
      showToast: jest.fn(),
      close: jest.fn(),
      closeAll: jest.fn(),
    })),
  };
});

// Mock React Native Reanimated
jest.mock('react-native-reanimated', () => {
  const React = require('react');
  
  const View = React.forwardRef((props, ref) => {
    const { children, ...otherProps } = props;
    return React.createElement('div', { ...otherProps, ref }, children);
  });
  View.displayName = 'ReanimatedView';
  
  const Text = React.forwardRef((props, ref) => {
    const { children, ...otherProps } = props;
    return React.createElement('span', { ...otherProps, ref }, children);
  });
  Text.displayName = 'ReanimatedText';
  
  const ScrollView = React.forwardRef((props, ref) => {
    const { children, ...otherProps } = props;
    return React.createElement('div', { ...otherProps, ref, style: { overflow: 'auto', ...props.style } }, children);
  });
  ScrollView.displayName = 'ReanimatedScrollView';

  const mockAnimatedValue = {
    setValue: jest.fn(),
    addListener: jest.fn(() => 'listener_id'),
    removeListener: jest.fn(),
    interpolate: jest.fn(() => 'interpolated_value'),
    extractOffset: jest.fn(),
    setOffset: jest.fn(),
    flattenOffset: jest.fn(),
    stopAnimation: jest.fn(),
    resetAnimation: jest.fn(),
    _value: 0,
  };

  const createAnimatedComponent = (Component) => {
    const AnimatedComponent = React.forwardRef((props, ref) => {
      const { style, ...otherProps } = props;
      return React.createElement(Component, { 
        ...otherProps, 
        ref,
        style: typeof style === 'object' ? style : undefined 
      });
    });
    AnimatedComponent.displayName = `Animated(${Component.displayName || Component.name || 'Component'})`;
    return AnimatedComponent;
  };

  return {
    __esModule: true,
    default: {
      View,
      Text,
      ScrollView,
      createAnimatedComponent,
      Value: jest.fn(() => mockAnimatedValue),
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
      delay: jest.fn(() => ({
        start: jest.fn(callback => callback && callback({ finished: true })),
      })),
      event: jest.fn(() => jest.fn()),
      add: jest.fn(() => mockAnimatedValue),
      subtract: jest.fn(() => mockAnimatedValue),
      multiply: jest.fn(() => mockAnimatedValue),
      divide: jest.fn(() => mockAnimatedValue),
      modulo: jest.fn(() => mockAnimatedValue),
      diffClamp: jest.fn(() => mockAnimatedValue),
      Extrapolate: {
        EXTEND: 'extend',
        CLAMP: 'clamp',
        IDENTITY: 'identity',
      },
      Easing: {
        linear: jest.fn(),
        ease: jest.fn(),
        quad: jest.fn(),
        cubic: jest.fn(),
        poly: jest.fn(),
        sin: jest.fn(),
        circle: jest.fn(),
        exp: jest.fn(),
        elastic: jest.fn(),
        back: jest.fn(),
        bounce: jest.fn(),
        bezier: jest.fn(),
        in: jest.fn(fn => fn),
        out: jest.fn(fn => fn),
        inOut: jest.fn(fn => fn),
      },
    },
    // Export common Reanimated v2 components and functions
    useSharedValue: jest.fn((initial) => ({ value: initial })),
    useAnimatedStyle: jest.fn((styleFunction) => styleFunction()),
    useAnimatedProps: jest.fn((propsFunction) => propsFunction()),
    useAnimatedGestureHandler: jest.fn(() => ({})),
    useAnimatedReaction: jest.fn(),
    useAnimatedRef: jest.fn(() => ({ current: null })),
    useDerivedValue: jest.fn((derivedFunction) => ({ value: derivedFunction() })),
    useAnimatedScrollHandler: jest.fn(() => ({})),
    useWorkletCallback: jest.fn((callback) => callback),
    runOnJS: jest.fn((callback) => callback),
    runOnUI: jest.fn((callback) => callback),
    withTiming: jest.fn((toValue) => toValue),
    withSpring: jest.fn((toValue) => toValue),
    withDecay: jest.fn(() => 0),
    withDelay: jest.fn((delay, animation) => animation),
    withRepeat: jest.fn((animation) => animation),
    withSequence: jest.fn((...animations) => animations[0]),
    cancelAnimation: jest.fn(),
    measure: jest.fn(() => null),
    scrollTo: jest.fn(),
    // Export entrance/exit animations
    FadeIn: { duration: jest.fn().mockReturnThis() },
    FadeOut: { duration: jest.fn().mockReturnThis() },
    SlideInLeft: { duration: jest.fn().mockReturnThis() },
    SlideInRight: { duration: jest.fn().mockReturnThis() },
    SlideInUp: { duration: jest.fn().mockReturnThis() },
    SlideInDown: { duration: jest.fn().mockReturnThis() },
    SlideOutLeft: { duration: jest.fn().mockReturnThis() },
    SlideOutRight: { duration: jest.fn().mockReturnThis() },
    SlideOutUp: { duration: jest.fn().mockReturnThis() },
    SlideOutDown: { duration: jest.fn().mockReturnThis() },
    BounceIn: { duration: jest.fn().mockReturnThis() },
    BounceOut: { duration: jest.fn().mockReturnThis() },
    ZoomIn: { duration: jest.fn().mockReturnThis() },
    ZoomOut: { duration: jest.fn().mockReturnThis() },
    // Animated components
    createAnimatedComponent,
  };
});

// Mock React Native Reanimated core modules that might be directly imported
jest.mock('react-native-reanimated/lib/reanimated2/core', () => ({}), { virtual: true });
jest.mock('react-native-reanimated/lib/module/reanimated2/NativeReanimated', () => ({}), { virtual: true });

// Note: React Native Gesture Handler mock removed as it's not installed
// If needed later, uncomment and install the dependency first

// Remove duplicate expo-router mock (already defined later)

// Mock @unitools/router (used by SignIn component)
jest.mock('@unitools/router', () => ({
  __esModule: true,
  default: () => ({
    push: jest.fn(),
    back: jest.fn(),
    replace: jest.fn(),
  }),
}));

// Mock @unitools/link (used by SignIn component)
jest.mock('@unitools/link', () => {
  const React = require('react');
  return {
    __esModule: true,
    default: React.forwardRef(({ href, children, ...props }, ref) => 
      React.createElement('a', { href, ref, ...props }, children)
    ),
  };
});

// Mock react-native-safe-area-context first (must come before other mocks)
jest.mock('react-native-safe-area-context', () => {
  const React = require('react');
  return {
    SafeAreaProvider: ({ children }) => React.createElement('div', { className: 'safe-area-provider' }, children),
    SafeAreaView: React.forwardRef((props, ref) => 
      React.createElement('div', { ...props, ref, className: 'safe-area-view' })
    ),
    SafeAreaInsetsContext: {
      Consumer: ({ children }) => children({ top: 0, bottom: 0, left: 0, right: 0 }),
    },
    EdgeInsets: { top: 0, bottom: 0, left: 0, right: 0 },
    useSafeAreaInsets: () => ({ top: 0, bottom: 0, left: 0, right: 0 }),
    useSafeAreaFrame: () => ({ x: 0, y: 0, width: 390, height: 844 }),
    withSafeAreaInsets: (component) => component,
  };
});

// Mock Expo modules
jest.mock('expo-router', () => {
  const React = require('react');
  
  const mockLink = React.forwardRef((props, ref) => {
    const { href, children, ...otherProps } = props;
    return React.createElement('a', { ...otherProps, ref, href }, children);
  });
  mockLink.displayName = 'Link';

  return {
    useRouter: () => ({
      push: jest.fn(),
      back: jest.fn(),
      replace: jest.fn(),
      canGoBack: jest.fn(() => true),
    }),
    useLocalSearchParams: jest.fn(() => ({})),
    usePathname: jest.fn(() => '/'),
    useGlobalSearchParams: jest.fn(() => ({})),
    Link: mockLink,
    Stack: ({ children }) => React.createElement('div', { className: 'expo-stack' }, children),
    Tabs: ({ children }) => React.createElement('div', { className: 'expo-tabs' }, children),
    router: {
      push: jest.fn(),
      back: jest.fn(),
      replace: jest.fn(),
      canGoBack: jest.fn(() => true),
    },
  };
});

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
  const mockLink = React.forwardRef((props, ref) => {
    const { href, children, ...otherProps } = props;
    return React.createElement('a', { ...otherProps, ref, href }, children);
  });
  mockLink.displayName = 'UnitoolsLink';
  return {
    __esModule: true,
    default: mockLink,
  };
});

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

// Mock for expo-notifications is in __mocks__ directory

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
    request: jest.fn(() => Promise.resolve({ data: { data: {} } })),
  },
}));

// Mock authApi
jest.mock('@/api/authApi', () => ({
  requestEmailCode: jest.fn(() => Promise.resolve({ success: true })),
  verifyCode: jest.fn(() => Promise.resolve({ success: true, token: 'mock-token' })),
  resendCode: jest.fn(() => Promise.resolve({ success: true })),
  signUp: jest.fn(() => Promise.resolve({ success: true })),
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
    (errorString.includes('Warning: ReactDOM.render is no longer supported') ||
     errorString.includes('Warning: An update to') ||
     errorString.includes('was not wrapped in act'))
  ) {
    return;
  }
  originalConsoleError.apply(console, args);
};

// Mock UI components that cause cssInterop issues
jest.mock('@/components/ui/badge', () => {
  const React = require('react');
  return {
    Badge: ({ children, variant, ...props }) => React.createElement('div', { ...props, className: `badge ${variant || ''}` }, children),
    BadgeText: ({ children, ...props }) => React.createElement('span', { ...props, className: 'badge-text' }, children),
    BadgeIcon: ({ as: IconComponent, ...props }) => React.createElement('span', { ...props, className: 'badge-icon' }),
  };
});

jest.mock('@/components/ui/button', () => {
  const React = require('react');
  return {
    Button: React.forwardRef(({ children, onPress, disabled, ...props }, ref) => 
      React.createElement('button', { ...props, ref, onClick: onPress, disabled, className: 'button' }, children)
    ),
    ButtonText: ({ children, ...props }) => React.createElement('span', { ...props, className: 'button-text' }, children),
    ButtonIcon: ({ as: IconComponent, ...props }) => React.createElement('span', { ...props, className: 'button-icon' }),
    ButtonSpinner: () => React.createElement('span', { className: 'button-spinner' }, 'Loading...'),
  };
});

jest.mock('@/components/ui/card', () => {
  const React = require('react');
  return {
    Card: ({ children, ...props }) => React.createElement('div', { ...props, className: 'card' }, children),
  };
});

jest.mock('@/components/ui/box', () => {
  const React = require('react');
  return {
    Box: ({ children, ...props }) => React.createElement('div', { ...props, className: 'box' }, children),
  };
});

jest.mock('@/components/ui/hstack', () => {
  const React = require('react');
  return {
    HStack: ({ children, ...props }) => React.createElement('div', { ...props, className: 'hstack' }, children),
  };
});

jest.mock('@/components/ui/select', () => {
  const React = require('react');
  return {
    Select: ({ children, ...props }) => React.createElement('div', { ...props, className: 'select' }, children),
    SelectTrigger: ({ children, ...props }) => React.createElement('button', { ...props, className: 'select-trigger' }, children),
    SelectInput: ({ children, ...props }) => React.createElement('div', { ...props, className: 'select-input' }, children),
    SelectPortal: ({ children, ...props }) => React.createElement('div', { ...props, className: 'select-portal' }, children),
    SelectBackdrop: ({ children, ...props }) => React.createElement('div', { ...props, className: 'select-backdrop' }, children),
    SelectContent: ({ children, ...props }) => React.createElement('div', { ...props, className: 'select-content' }, children),
    SelectDragIndicatorWrapper: ({ children, ...props }) => React.createElement('div', { ...props, className: 'select-drag-indicator' }, children),
    SelectDragIndicator: ({ children, ...props }) => React.createElement('div', { ...props, className: 'select-drag-indicator' }, children),
    SelectItem: ({ children, value, ...props }) => React.createElement('option', { ...props, value, className: 'select-item' }, children),
  };
});

jest.mock('@/components/ui/spinner', () => {
  const React = require('react');
  return {
    Spinner: ({ ...props }) => React.createElement('div', { ...props, className: 'spinner' }, 'Loading...'),
  };
});

jest.mock('@/components/ui/progress', () => {
  const React = require('react');
  return {
    Progress: ({ children, value, ...props }) => React.createElement('div', { ...props, className: 'progress', 'data-value': value }, children),
    ProgressFilledTrack: ({ ...props }) => React.createElement('div', { ...props, className: 'progress-filled' }),
  };
});

jest.mock('@/components/ui/divider', () => {
  const React = require('react');
  return {
    Divider: ({ ...props }) => React.createElement('hr', { ...props, className: 'divider' }),
  };
});

// Mock all Gluestack UI components
jest.mock('@/components/ui/form-control', () => {
  const React = require('react');
  return {
    FormControl: ({ children, ...props }) => React.createElement('div', { ...props, className: 'form-control' }, children),
    FormControlError: ({ children, ...props }) => React.createElement('div', { ...props, className: 'form-control-error' }, children),
    FormControlErrorIcon: ({ as: IconComponent, ...props }) => React.createElement('div', { ...props, className: 'form-control-error-icon' }),
    FormControlErrorText: ({ children, ...props }) => React.createElement('div', { ...props, className: 'form-control-error-text' }, children),
    FormControlLabel: ({ children, ...props }) => React.createElement('div', { ...props, className: 'form-control-label' }, children),
    FormControlLabelText: ({ children, ...props }) => React.createElement('div', { ...props, className: 'form-control-label-text' }, children),
  };
});

jest.mock('@/components/ui/heading', () => {
  const React = require('react');
  return {
    Heading: ({ children, ...props }) => React.createElement('h1', { ...props, className: 'heading' }, children),
  };
});

jest.mock('@/components/ui/icon', () => {
  const React = require('react');
  return {
    Icon: ({ as: IconComponent, ...props }) => React.createElement('div', { ...props, className: 'icon' }),
    ArrowLeftIcon: React.forwardRef((props, ref) => React.createElement('div', { ...props, ref, className: 'arrow-left-icon' })),
  };
});

jest.mock('@/components/ui/input', () => {
  const React = require('react');
  return {
    Input: ({ children, ...props }) => React.createElement('div', { ...props, className: 'input' }, children),
    InputField: React.forwardRef((props, ref) => {
      const { testID, onChangeText, value, ...otherProps } = props;
      return React.createElement('input', {
        ...otherProps,
        ref,
        'data-testid': testID,
        value: value || '',
        onChange: onChangeText ? (e) => onChangeText(e.target.value) : undefined,
        className: 'input-field'
      });
    }),
  };
});

jest.mock('@/components/ui/pressable', () => {
  const React = require('react');
  return {
    Pressable: React.forwardRef(({ onPress, disabled, children, ...props }, ref) => {
      return React.createElement('button', {
        ...props,
        ref,
        onClick: onPress,
        disabled,
        className: 'pressable'
      }, children);
    }),
  };
});

jest.mock('@/components/ui/text', () => {
  const React = require('react');
  return {
    Text: ({ children, ...props }) => React.createElement('span', { ...props, className: 'text' }, children),
  };
});

jest.mock('@/components/ui/vstack', () => {
  const React = require('react');
  return {
    VStack: ({ children, ...props }) => React.createElement('div', { ...props, className: 'vstack' }, children),
  };
});

jest.mock('@/components/ui/grid', () => {
  const React = require('react');
  return {
    Grid: React.forwardRef(({ children, ...props }, ref) => 
      React.createElement('div', { ...props, ref, className: 'grid' }, children)
    ),
    GridItem: React.forwardRef(({ children, ...props }, ref) => 
      React.createElement('div', { ...props, ref, className: 'grid-item' }, children)
    ),
  };
});

jest.mock('@/components/ui/toast', () => ({
  useToast: jest.fn(() => ({
    showToast: jest.fn(),
    show: jest.fn(),
    close: jest.fn(),
    closeAll: jest.fn(),
  })),
  ToastProvider: ({ children }) => {
    const React = require('react');
    return React.createElement('div', { className: 'toast-provider' }, children);
  },
}));

jest.mock('@/components/ui/alert', () => {
  const React = require('react');
  return {
    Alert: ({ children, ...props }) => React.createElement('div', { ...props, className: 'alert' }, children),
    AlertIcon: ({ as: IconComponent, ...props }) => React.createElement('div', { ...props, className: 'alert-icon' }),
    AlertText: ({ children, ...props }) => React.createElement('div', { ...props, className: 'alert-text' }, children),
  };
});

// Mock AuthLayout
jest.mock('@/components/auth/AuthLayout', () => {
  const React = require('react');
  return {
    AuthLayout: ({ children }) => React.createElement('div', { className: 'auth-layout', 'data-testid': 'auth-layout' }, children),
  };
});

// Mock react-hook-form
jest.mock('react-hook-form', () => ({
  useForm: jest.fn(() => ({
    control: {},
    handleSubmit: jest.fn((fn) => () => fn),
    formState: { errors: {} },
    setValue: jest.fn(),
    getValues: jest.fn(),
    watch: jest.fn(),
    reset: jest.fn(),
  })),
  Controller: ({ render, name, control, defaultValue }) => {
    const React = require('react');
    return render({ 
      field: { 
        onChange: jest.fn(), 
        onBlur: jest.fn(), 
        value: defaultValue || '',
        name,
      },
      fieldState: { error: null },
      formState: { errors: {} },
    });
  },
}));

// Mock zodResolver
jest.mock('@hookform/resolvers/zod', () => ({
  zodResolver: jest.fn(() => () => Promise.resolve({ values: {}, errors: {} })),
}));

// lucide-react-native already mocked above

// Configure React Native Testing Library after all mocks are set up
// Note: We're skipping the configure step as it's causing issues with the afterEach hook
// The mocks should work without explicit configuration

// Global cleanup after each test
global.afterEach = global.afterEach || (() => {});
const originalAfterEach = global.afterEach;
global.afterEach = (fn, timeout) => {
  originalAfterEach(() => {
    jest.clearAllMocks();
    jest.clearAllTimers();
    if (fn) fn();
  }, timeout || 10000);
};
