const { getDefaultConfig } = require('expo/metro-config');
const path = require('path');
const { withNativeWind } = require('nativewind/metro');

const projectRoot = __dirname;
const config = getDefaultConfig(projectRoot, {
  isCSSEnabled: true,
});

// Simple @ alias for imports + React Native SVG polyfill
config.resolver.alias = {
  '@': path.resolve(projectRoot),
  'react-native-svg/src/web/utils': path.resolve(projectRoot, 'react-native-svg-utils-polyfill.js'),
};

// Basic React 19 compatibility - use defaults mostly
config.resolver.unstable_enablePackageExports = false; // Disable for compatibility
config.resolver.platforms = ['ios', 'android', 'native', 'web'];

// Basic source extensions
config.resolver.sourceExts = [
  ...config.resolver.sourceExts,
  'ts',
  'tsx',
];

// Exclude test files from production bundle
config.resolver.blockList = [
  /.*\/__tests__\/.*/,
  /.*\.test\.(js|jsx|ts|tsx)$/,
  /.*\.spec\.(js|jsx|ts|tsx)$/,
  /jest\.setup\.js$/,
  /jest\.config\.js$/,
];

// Apply the NativeWind transformer
// Note: This configuration supports React 19 + Expo SDK 53 with platform-specific optimizations
// Web builds are production-only due to react-refresh incompatibility
module.exports = withNativeWind(config, { input: './global.css' });
