const path = require('path');

module.exports = function (api) {
  api.cache(true);
  return {
    presets: [
      ['babel-preset-expo', { jsxImportSource: 'nativewind' }],
      'nativewind/babel',
      '@babel/preset-typescript',
    ],
    plugins: [
      [
        'module-resolver',
        {
          alias: {
            '@': './',
          },
          root: ['./'],
          extensions: ['.js', '.jsx', '.ts', '.tsx', '.web.js', '.web.tsx', '.web.ts'],
          cwd: 'packagejson',
        },
      ],
      'react-native-reanimated/plugin',
    ],
    env: {
      production: {
        plugins: [
          ['transform-remove-console', { exclude: ['error', 'warn'] }],
        ],
      },
      test: {
        plugins: ['@babel/plugin-transform-modules-commonjs'],
      },
      web: {
        plugins: [
          // Better React Native Web compatibility
        ],
      },
    },
  };
};
