import React from 'react';

import { Box } from '@/components/ui/box';

// Minimal responsive utilities to fix build
export const isMobile = () => true;
export const isTablet = () => false;
export const isDesktop = () => false;
export const getDeviceType = () => 'mobile';

export const getResponsiveTextSize = (size: string) => 'text-sm';
export const getResponsiveSpacing = (size: string) => 'p-4';
export const getResponsivePadding = (size: string) => 'p-4';
export const getResponsiveMargin = (size: string) => 'm-4';

// Breakpoints
export const breakpoints = {
  mobile: 768,
  tablet: 1024,
  desktop: 1200,
};

// Touch sizes
export const touchSizes = {
  small: 'min-h-10',
  medium: 'min-h-12',
  large: 'min-h-14',
};

// Spacing
export const spacing = {
  xs: 'p-1',
  sm: 'p-2',
  md: 'p-4',
  lg: 'p-6',
  xl: 'p-8',
};

export type Breakpoint = 'mobile' | 'tablet' | 'desktop';

export const ResponsiveContainer: React.FC<any> = ({ children, className = '' }) => (
  <Box className={className}>{children}</Box>
);

export const ResponsiveStack: React.FC<any> = ({ children, className = '' }) => (
  <Box className={className}>{children}</Box>
);

export const TouchFriendly: React.FC<any> = ({ children, className = '' }) => (
  <Box className={className}>{children}</Box>
);

export default ResponsiveContainer;
