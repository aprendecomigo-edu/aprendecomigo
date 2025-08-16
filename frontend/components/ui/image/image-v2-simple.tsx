import React, { createContext, useContext, useMemo } from 'react';
import { Image as RNImage, ImageProps } from 'react-native';

// Image Context for sharing state between components
interface ImageContextValue {
  size?: string;
  variant?: string;
}

const ImageContext = createContext<ImageContextValue>({});

// Type definitions - simplified for testing
export type IImageProps = ImageProps & {
  size?: '2xs' | 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl' | 'full';
  className?: string;
};

// Simple style generator for testing
const getImageStyles = (size?: string) => {
  const dimensions = {
    '2xs': 24,
    xs: 40,
    sm: 64,
    md: 80,
    lg: 96,
    xl: 128,
    '2xl': 256,
    full: '100%' as const,
  };

  const dimension = dimensions[size as keyof typeof dimensions] || dimensions.md;

  if (size === 'full') {
    return { width: '100%', height: '100%' };
  }

  return {
    width: dimension,
    height: dimension,
  };
};

// Main Image component - Simplified v2 without factory functions
export const Image = React.forwardRef<RNImage, IImageProps>(
  ({ size = 'md', style, ...props }, ref) => {
    const contextValue = useMemo(() => ({ size }), [size]);

    const imageStyles = getImageStyles(size);

    return (
      <ImageContext.Provider value={contextValue}>
        <RNImage ref={ref} {...props} style={[imageStyles, style]} />
      </ImageContext.Provider>
    );
  },
);

// Display names for debugging
Image.displayName = 'Image';
