import '@testing-library/jest-native/extend-expect';

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
