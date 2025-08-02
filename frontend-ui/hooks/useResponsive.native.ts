import { Dimensions } from 'react-native';

interface ResponsiveState {
  isMobile: boolean;
  isTablet: boolean;
  isDesktop: boolean;
  screenWidth: number;
}

export function useResponsive(): ResponsiveState {
  const screenWidth = Dimensions.get('window').width;

  // On native platforms, we're always in a mobile/tablet context
  // But we can still differentiate between phone and tablet sizes
  const isMobile = screenWidth < 768;
  const isTablet = screenWidth >= 768;
  const isDesktop = false; // Never desktop on native

  return {
    isMobile,
    isTablet,
    isDesktop,
    screenWidth,
  };
}