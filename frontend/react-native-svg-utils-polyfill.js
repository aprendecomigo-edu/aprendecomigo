/**
 * Polyfill for react-native-svg utils to fix React Native Web compatibility
 */

// Import the original module but provide fallbacks
let originalUtils;
try {
  // Try to import from the actual location
  originalUtils = require('./node_modules/react-native-svg/src/web/utils/index.ts');
} catch (e) {
  try {
    originalUtils = require('./node_modules/react-native-svg/src/web/utils');
  } catch (e2) {
    console.warn('Could not import original react-native-svg utils, using fallback');
    originalUtils = {};
  }
}

// Ensure hasTouchableProperty is always available
const hasTouchableProperty =
  originalUtils.hasTouchableProperty ||
  (props => {
    return Boolean(props?.onPress || props?.onPressIn || props?.onPressOut || props?.onLongPress);
  });

// Export all original functions plus our polyfill
module.exports = {
  ...originalUtils,
  hasTouchableProperty,
};
