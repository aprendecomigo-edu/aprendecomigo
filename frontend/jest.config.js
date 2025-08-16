module.exports = {
  preset: 'jest-expo',
  transformIgnorePatterns: [
    'node_modules/(?!((jest-)?react-native|@react-native(-community)?)|expo(nent)?|@expo(nent)?/.*|@expo-google-fonts/.*|react-navigation|@react-navigation/.*|@sentry/react-native|native-base|react-native-svg|@gluestack-ui/.*|@gluestack-style/.*|lucide-react-native|react-native-css-interop|nativewind|expo-modules-core|react-native-reanimated|react-native-screens|react-native-safe-area-context|react-native-gesture-handler)',
  ],
  setupFilesAfterEnv: ['<rootDir>/jest.setup.minimal.js'],
  testMatch: [
    '<rootDir>/__tests__/**/*.(test|spec).(js|jsx|ts|tsx)',
    '<rootDir>/**/*.(test|spec).(js|jsx|ts|tsx)',
  ],
  testPathIgnorePatterns: ['<rootDir>/node_modules/', '<rootDir>/dist/', '<rootDir>/.expo/'],
  collectCoverageFrom: [
    'components/**/*.{js,jsx,ts,tsx}',
    'hooks/**/*.{js,jsx,ts,tsx}',
    'api/**/*.{js,jsx,ts,tsx}',
    '!**/*.d.ts',
    '!**/node_modules/**',
    '!**/__tests__/**',
    '!**/coverage/**',
    '!components/ui/**', // Exclude UI library components
  ],
  coverageReporters: ['text', 'lcov', 'html'],
  coverageDirectory: '<rootDir>/coverage',
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 90,
      lines: 85,
      statements: 85,
    },
    // Specific coverage requirements for critical components
    './components/onboarding/TeacherProfileWizard.tsx': {
      branches: 85,
      functions: 95,
      lines: 90,
      statements: 90,
    },
    './hooks/useProfileWizard.ts': {
      branches: 85,
      functions: 95,
      lines: 90,
      statements: 90,
    },
  },
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/$1',
    '^@/components/(.*)$': '<rootDir>/components/$1',
    '^@/hooks/(.*)$': '<rootDir>/hooks/$1',
    '^@/api/(.*)$': '<rootDir>/api/$1',
    '^@/constants/(.*)$': '<rootDir>/constants/$1',
    '^@/types/(.*)$': '<rootDir>/types/$1',
    '^@/utils/(.*)$': '<rootDir>/utils/$1',
  },
  globals: {
    'ts-jest': {
      tsconfig: {
        jsx: 'react',
      },
    },
  },
  // Use jest-expo's default test environment for React Native
  // testEnvironment is provided by jest-expo preset
  verbose: true,
  maxWorkers: '50%',
};
