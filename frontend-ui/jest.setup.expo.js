// Jest setup file optimized for jest-expo
// This file works in conjunction with jest-expo preset which provides
// proper React Native and Expo SDK mocks

import '@testing-library/jest-native/extend-expect';

// Mock expo-router (not included in jest-expo)
jest.mock('expo-router', () => ({
  useRouter: jest.fn(() => ({
    push: jest.fn(),
    back: jest.fn(),
    replace: jest.fn(),
    canGoBack: jest.fn(() => true),
  })),
  useLocalSearchParams: jest.fn(() => ({})),
  usePathname: jest.fn(() => '/'),
  useGlobalSearchParams: jest.fn(() => ({})),
  Link: 'Link',
  Stack: 'Stack',
  Tabs: 'Tabs',
  router: {
    push: jest.fn(),
    back: jest.fn(),
    replace: jest.fn(),
    canGoBack: jest.fn(() => true),
  },
}));

// Mock @unitools packages
jest.mock('@unitools/router', () => ({
  __esModule: true,
  default: jest.fn(() => ({
    push: jest.fn(),
    back: jest.fn(),
    replace: jest.fn(),
    canGoBack: jest.fn(() => true),
  })),
}));

jest.mock('@unitools/link', () => ({
  __esModule: true,
  default: 'Link',
}));

// Mock Gluestack UI components
jest.mock('@/components/ui/form-control', () => ({
  FormControl: 'FormControl',
  FormControlError: 'FormControlError',
  FormControlErrorIcon: 'FormControlErrorIcon',
  FormControlErrorText: 'FormControlErrorText',
  FormControlLabel: 'FormControlLabel',
  FormControlLabelText: 'FormControlLabelText',
}));

jest.mock('@/components/ui/heading', () => ({
  Heading: 'Heading',
}));

jest.mock('@/components/ui/icon', () => ({
  Icon: 'Icon',
  ArrowLeftIcon: 'ArrowLeftIcon',
}));

jest.mock('@/components/ui/input', () => ({
  Input: 'Input',
  InputField: 'InputField',
}));

jest.mock('@/components/ui/pressable', () => ({
  Pressable: 'Pressable',
}));

jest.mock('@/components/ui/text', () => ({
  Text: 'Text',
}));

jest.mock('@/components/ui/vstack', () => ({
  VStack: 'VStack',
}));

jest.mock('@/components/ui/toast', () => ({
  useToast: jest.fn(() => ({
    showToast: jest.fn(),
    show: jest.fn(),
    close: jest.fn(),
    closeAll: jest.fn(),
  })),
  ToastProvider: 'ToastProvider',
}));

// Mock AuthLayout
jest.mock('@/components/auth/AuthLayout', () => ({
  AuthLayout: 'AuthLayout',
}));

// Mock API modules
jest.mock('@/api/authApi', () => ({
  requestEmailCode: jest.fn(() => Promise.resolve({ success: true })),
  verifyCode: jest.fn(() => Promise.resolve({ success: true, token: 'mock-token' })),
  resendCode: jest.fn(() => Promise.resolve({ success: true })),
  signUp: jest.fn(() => Promise.resolve({ success: true })),
}));

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

// Mock zodResolver
jest.mock('@hookform/resolvers/zod', () => ({
  zodResolver: jest.fn(() => () => Promise.resolve({ values: {}, errors: {} })),
}));

// Mock lucide-react-native
jest.mock('lucide-react-native', () => {
  const icons = {};
  return new Proxy(icons, {
    get: (target, prop) => {
      if (!target[prop]) {
        target[prop] = prop;
      }
      return target[prop];
    },
  });
});

// Mock NativeWind
jest.mock('nativewind', () => ({
  styled: component => component,
  useColorScheme: jest.fn(() => ({
    colorScheme: 'light',
    setColorScheme: jest.fn(),
    toggleColorScheme: jest.fn(),
  })),
}));

// Mock react-native-css-interop
jest.mock('react-native-css-interop', () => ({
  cssInterop: jest.fn(Component => Component),
  remapProps: jest.fn(Component => Component),
}));

// Global test utilities
global.flushPromises = () => new Promise(resolve => setImmediate(resolve));

// Cleanup after each test
afterEach(() => {
  jest.clearAllMocks();
});
