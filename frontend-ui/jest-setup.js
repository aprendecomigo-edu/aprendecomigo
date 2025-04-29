import '@testing-library/jest-native/extend-expect';

// Configure React Native Testing Library
import { configure } from '@testing-library/react-native';
configure({
  // Ensure we wait for component updates
  asyncUtilTimeout: 2000,
});

// Mock the expo-router hooks
jest.mock('expo-router', () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    back: jest.fn(),
  }),
  useLocalSearchParams: jest.fn().mockReturnValue({}),
  router: {
    push: jest.fn(),
    replace: jest.fn(),
  },
  Link: 'Link',
  Stack: {
    Screen: props => props.children || null,
  },
  Redirect: props => props.children || null,
}));

// Mock Secure Store
jest.mock('expo-secure-store', () => ({
  getItemAsync: jest.fn(),
  setItemAsync: jest.fn(),
  deleteItemAsync: jest.fn(),
}));

// Mock AsyncStorage
jest.mock('@react-native-async-storage/async-storage', () => ({
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
}));

// Mock Local Authentication
jest.mock('expo-local-authentication', () => ({
  hasHardwareAsync: jest.fn(),
  isEnrolledAsync: jest.fn(),
  authenticateAsync: jest.fn(),
}));

// Mock the platform specific code
jest.mock('react-native/Libraries/Utilities/Platform', () => ({
  OS: 'ios',
  select: obj => obj.ios,
}));

// Mock GluestackUI Provider
jest.mock('@/components/ui/gluestack-ui-provider', () => ({
  GluestackUIProvider: ({ children }) => children,
}));

// Mock View
jest.mock('@/components/ui/view', () => ({
  View: ({ children }) => children,
}));

// Mock Text
jest.mock('@/components/ui/text', () => ({
  Text: ({ children }) => children,
}));

// Mock Spinner
jest.mock('@/components/ui/spinner', () => ({
  Spinner: () => 'Spinner',
}));

// Mock @legendapp/motion
jest.mock('@legendapp/motion', () => ({
  Motion: ({ children }) => children,
  AnimatePresence: ({ children }) => children,
  createMotionAnimatedComponent: component => component,
}));

// Mock problematic components from react-native
jest.mock('react-native/Libraries/Components/ScrollView/ScrollView', () => 'ScrollView');
jest.mock(
  'react-native/Libraries/Animated/components/AnimatedScrollView',
  () => 'AnimatedScrollView'
);
