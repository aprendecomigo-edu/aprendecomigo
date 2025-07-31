import 'react-native-gesture-handler/jestSetup';

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

// Mock React Native modules
jest.mock('react-native', () => {
  const RN = jest.requireActual('react-native');
  return {
    ...RN,
    Platform: {
      ...RN.Platform,
      OS: 'web',
    },
    Dimensions: {
      get: jest.fn(() => ({ width: 1024, height: 768 })),
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
    },
    Alert: {
      alert: jest.fn(),
    },
    NativeModules: {
      ...RN.NativeModules,
      RNGestureHandlerModule: {
        attachGestureHandler: jest.fn(),
        createGestureHandler: jest.fn(),
        dropGestureHandler: jest.fn(),
        updateGestureHandler: jest.fn(),
        State: {},
        Directions: {},
      },
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

// Mock React Native Vector Icons
jest.mock('lucide-react-native', () => {
  const React = require('react');
  
  const MockIcon = React.forwardRef((props, ref) => {
    const { testID, ...otherProps } = props;
    return React.createElement('Text', {
      ...otherProps,
      ref,
      testID: testID || 'mock-icon',
    }, 'MockIcon');
  });
  
  return new Proxy({}, {
    get: () => MockIcon,
  });
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
global.flushPromises = () => new Promise(resolve => setImmediate(resolve));

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

// Cleanup after each test
afterEach(() => {
  jest.clearAllMocks();
  jest.clearAllTimers();
});