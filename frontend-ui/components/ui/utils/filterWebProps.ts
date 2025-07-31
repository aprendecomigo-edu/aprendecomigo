import { Platform } from 'react-native';

// React Native accessibility props that should be filtered out on web
const REACT_NATIVE_ACCESSIBILITY_PROPS = [
  'accessibilityRole',
  'accessibilityLevel',
  'accessibilityHint', 
  'accessibilityLabel',
  'accessibilityState',
  'accessibilityActions',
  'accessibilityValue',
  'accessibilityElementsHidden',
  'accessibilityViewIsModal',
  'accessibilityIgnoresInvertColors',
  'accessibilityLiveRegion',
  'importantForAccessibility'
];

/**
 * Utility function to filter out React Native accessibility props when running on web
 * This prevents React DOM warnings about unrecognized props
 * 
 * @param props - The props object to filter
 * @returns Filtered props object (on web) or original props (on native)
 */
export const filterWebProps = (props: any) => {
  if (Platform.OS !== 'web') {
    return props;
  }
  
  const filteredProps = { ...props };
  REACT_NATIVE_ACCESSIBILITY_PROPS.forEach(prop => {
    delete filteredProps[prop];
  });
  
  return filteredProps;
}; 