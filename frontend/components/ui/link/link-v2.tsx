import type { VariantProps } from '@gluestack-ui/nativewind-utils';
import { tva } from '@gluestack-ui/nativewind-utils/tva';
import React, { createContext, useContext, useMemo } from 'react';
import { Text, Pressable, PressableProps, TextProps } from 'react-native';

// Link Context for sharing state between components
interface LinkContextValue {
  isDisabled?: boolean;
  isHovered?: boolean;
}

const LinkContext = createContext<LinkContextValue>({});

// Scope for style context
const SCOPE = 'LINK';

// Style definitions
export const linkStyle = tva({
  base: 'group/link web:outline-0 data-[disabled=true]:web:cursor-not-allowed data-[focus-visible=true]:web:ring-2 data-[focus-visible=true]:web:ring-indicator-primary data-[focus-visible=true]:web:outline-0 data-[disabled=true]:opacity-40',
});

export const linkTextStyle = tva({
  base: 'underline text-info-700 data-[hover=true]:text-info-600 data-[hover=true]:no-underline data-[active=true]:text-info-700 font-normal font-body web:font-sans web:tracking-sm web:my-0 web:bg-transparent web:border-0 web:box-border web:display-inline web:list-none web:margin-0 web:padding-0 web:position-relative web:text-start web:whitespace-pre-wrap web:word-wrap-break-word',
  variants: {
    isTruncated: {
      true: 'web:truncate',
    },
    bold: {
      true: 'font-bold',
    },
    underline: {
      true: 'underline',
    },
    strikeThrough: {
      true: 'line-through',
    },
    size: {
      '2xs': 'text-2xs',
      xs: 'text-xs',
      sm: 'text-sm',
      md: 'text-base',
      lg: 'text-lg',
      xl: 'text-xl',
      '2xl': 'text-2xl',
      '3xl': 'text-3xl',
      '4xl': 'text-4xl',
      '5xl': 'text-5xl',
      '6xl': 'text-6xl',
    },
  },
});

// Type definitions
export type ILinkProps = PressableProps & {
  className?: string;
  isDisabled?: boolean;
};

export type ILinkTextProps = TextProps &
  VariantProps<typeof linkTextStyle> & {
    className?: string;
  };

// Main Link component - Direct implementation without factory
export const Link = React.forwardRef<Pressable, ILinkProps>(
  ({ className, isDisabled = false, children, disabled, ...props }, ref) => {
    const contextValue = useMemo(
      () => ({ isDisabled: isDisabled || disabled }),
      [isDisabled, disabled],
    );

    const finalDisabled = isDisabled || disabled;

    return (
      <LinkContext.Provider value={contextValue}>
        <Pressable
          ref={ref as any}
          {...props}
          disabled={finalDisabled}
          className={linkStyle({ class: className })}
          style={{ opacity: finalDisabled ? 0.4 : 1 }}
        >
          {children}
        </Pressable>
      </LinkContext.Provider>
    );
  },
);

// LinkText component
export const LinkText = React.forwardRef<Text, ILinkTextProps>(
  (
    {
      className,
      isTruncated = false,
      bold = false,
      underline = true,
      strikeThrough = false,
      size = 'md',
      ...props
    },
    ref,
  ) => {
    return (
      <Text
        ref={ref}
        {...props}
        className={linkTextStyle({
          isTruncated,
          bold,
          underline,
          strikeThrough,
          size,
          class: className,
        })}
      />
    );
  },
);

// Display names for debugging
Link.displayName = 'Link';
LinkText.displayName = 'LinkText';
