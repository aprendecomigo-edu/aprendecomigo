const createExpoWebpackConfigAsync = require('@expo/webpack-config');
const path = require('path');

module.exports = async function (env, argv) {
  const config = await createExpoWebpackConfigAsync(env, argv);

  // Replace the existing font loader with asset/resource type
  config.module.rules.push({
    test: /\.(woff|woff2|eot|ttf|otf)$/i,
    type: 'asset/resource',
    include: [
      path.resolve(__dirname, 'node_modules/@expo/vector-icons'),
      path.resolve(__dirname, 'node_modules/react-native-vector-icons'),
    ],
  });

  return config;
};
