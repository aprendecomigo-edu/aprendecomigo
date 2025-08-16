import type { VariantProps } from '@gluestack-ui/nativewind-utils';
import { tva } from '@gluestack-ui/nativewind-utils/tva';
import React, { createContext, useContext, useMemo } from 'react';
import { Image as RNImage, ImageProps } from 'react-native';

// Image Context for sharing state between components
interface ImageContextValue {
  size?: string;
  variant?: string;
}

const ImageContext = createContext<ImageContextValue>({});

// Scope for style context
const SCOPE = 'IMAGE';

// Style definitions
export const imageStyle = tva({
  base: '',
  variants: {
    size: {
      '2xs': 'h-6 w-6',
      xs: 'h-10 w-10',
      sm: 'h-16 w-16',
      md: 'h-20 w-20',
      lg: 'h-24 w-24',
      xl: 'h-32 w-32',
      '2xl': 'h-64 w-64',
      full: 'h-full w-full',
    },
  },
});

// Type definitions
export type IImageProps = ImageProps &
  VariantProps<typeof imageStyle> & {
    className?: string;
  };

// Main Image component - Direct implementation without factory
export const Image = React.forwardRef<RNImage, IImageProps>(
  ({ className, size = 'md', ...props }, ref) => {
    const contextValue = useMemo(() => ({ size }), [size]);

    return (
      <ImageContext.Provider value={contextValue}>
        <RNImage ref={ref} {...props} className={imageStyle({ size, class: className })} />
      </ImageContext.Provider>
    );
  },
);

// Display names for debugging
Image.displayName = 'Image';
