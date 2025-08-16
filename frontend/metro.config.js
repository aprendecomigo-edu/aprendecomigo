const { getDefaultConfig } = require('expo/metro-config');
const path = require('path');
const { withNativeWind } = require('nativewind/metro');

const projectRoot = __dirname;
const config = getDefaultConfig(projectRoot, {
  isCSSEnabled: true,
});

// Enhanced resolver configuration for React Native Web compatibility
config.resolver.nodeModulesPaths = [path.resolve(projectRoot, 'node_modules')];

// Ensure proper aliasing for @ imports
config.resolver.alias = {
  '@': path.resolve(projectRoot),
};

// Add platform-specific extensions for React Native Web
config.resolver.platforms = ['ios', 'android', 'native', 'web'];

// Add TypeScript and JSX extensions
config.resolver.sourceExts = [
  ...config.resolver.sourceExts,
  'ts',
  'tsx',
  'js',
  'jsx',
  'json',
  'wasm',
  'svg',
];

// Transform configuration for React Native Web
config.transformer = {
  ...config.transformer,
  babelTransformerPath: require.resolve('@expo/metro-config/babel-transformer'),
  assetRegistryPath: 'react-native/Libraries/Image/AssetRegistry',
};

// Better module resolution for React Native Web compatibility
config.resolver.resolverMainFields = ['react-native', 'browser', 'main'];

// Exclude test files from production bundle
config.resolver.blockList = [
  // Test files
  /.*\/__tests__\/.*/,
  /.*\.test\.(js|jsx|ts|tsx)$/,
  /.*\.spec\.(js|jsx|ts|tsx)$/,
  /jest\.setup\.js$/,
  /jest\.config\.js$/,
  // QA test files
  /.*\/qa-tests\/.*/,
  // Development files
  /.*\.development\.(js|jsx|ts|tsx)$/,
  /.*\.dev\.(js|jsx|ts|tsx)$/,
];

// Watchman and file watching configuration to prevent EMFILE errors
config.watchFolders = [projectRoot];

// Simple server configuration
config.server = {
  enhanceMiddleware: middleware => {
    return middleware;
  },
};

// Apply the NativeWind transformer
module.exports = withNativeWind(config, { input: './global.css' });
