'use client';
import React from 'react';
import type { TextProps, ViewProps } from 'react-native';
import { Text, View } from 'react-native';
import { Svg } from 'react-native-svg';

// Simple Form Control type definitions
export type IFormControlProps = ViewProps & {
  className?: string;
  size?: 'sm' | 'md' | 'lg';
};

export type IFormControlErrorProps = ViewProps & { className?: string };
export type IFormControlErrorTextProps = TextProps & { className?: string; size?: string };
export type IFormControlLabelProps = ViewProps & { className?: string };
export type IFormControlLabelTextProps = TextProps & { className?: string; size?: string };
export type IFormControlLabelAstrickProps = TextProps & { className?: string };
export type IFormControlHelperProps = ViewProps & { className?: string };
export type IFormControlHelperTextProps = TextProps & { className?: string; size?: string };

export type IFormControlErrorIconProps = React.ComponentPropsWithoutRef<typeof Svg> & {
  className?: string;
  size?: string | number;
  height?: number | string;
  width?: number | string;
  fill?: string;
  color?: string;
  stroke?: string;
  as?: React.ElementType;
};

// Simple FormControl Root
export const FormControl = React.forwardRef<View, IFormControlProps>(
  ({ className = '', size = 'md', ...props }, ref) => {
    const baseClasses = 'flex flex-col';
    
    return (
      <View
        ref={ref}
        {...props}
        className={`${baseClasses} ${className}`}
      />
    );
  }
);

// Simple FormControlError
export const FormControlError = React.forwardRef<View, IFormControlErrorProps>(
  ({ className = '', ...props }, ref) => {
    const baseClasses = 'flex flex-row justify-start items-center mt-1 gap-1';
    
    return (
      <View
        ref={ref}
        {...props}
        className={`${baseClasses} ${className}`}
      />
    );
  }
);

// Simple FormControlErrorText
export const FormControlErrorText = React.forwardRef<Text, IFormControlErrorTextProps>(
  ({ className = '', size = 'md', ...props }, ref) => {
    const sizeClasses = {
      'xs': 'text-xs',
      'sm': 'text-sm',
      'md': 'text-base',
      'lg': 'text-lg',
    };
    
    const baseClasses = 'text-error-700';
    const combinedClasses = `${baseClasses} ${typeof size === 'string' ? sizeClasses[size as keyof typeof sizeClasses] || '' : ''} ${className}`;
    
    return (
      <Text
        ref={ref}
        {...props}
        className={combinedClasses}
      />
    );
  }
);

// Simple FormControlErrorIcon
export const FormControlErrorIcon = React.forwardRef<React.ElementRef<typeof Svg>, IFormControlErrorIconProps>(
  ({ className = '', size, height, width, fill, color, stroke, as: AsComp, ...props }, ref) => {
    const sizeClasses = {
      'sm': 'h-4 w-4',
      'md': 'h-[18px] w-[18px]',
      'lg': 'h-5 w-5',
    };
    
    const baseClasses = 'text-error-700 fill-none';
    
    // Handle size prop
    const getSizeClass = () => {
      if (typeof size === 'number') return '';
      if (typeof size === 'string') return sizeClasses[size as keyof typeof sizeClasses] || '';
      return sizeClasses.md;
    };
    
    const combinedClasses = `${baseClasses} ${getSizeClass()} ${className}`;
    
    const colorProps: any = {};
    if (color) colorProps.color = color;
    if (stroke) colorProps.stroke = stroke;
    if (fill) colorProps.fill = fill;
    
    if (typeof size === 'number') {
      colorProps.size = size;
    } else if (height !== undefined || width !== undefined) {
      if (height) colorProps.height = height;
      if (width) colorProps.width = width;
    }
    
    if (AsComp) {
      return <AsComp ref={ref} {...colorProps} {...props} className={combinedClasses} />;
    }
    
    return (
      <Svg
        ref={ref}
        height={height}
        width={width}
        {...colorProps}
        {...props}
        className={combinedClasses}
      />
    );
  }
);

// Simple FormControlLabel
export const FormControlLabel = React.forwardRef<View, IFormControlLabelProps>(
  ({ className = '', ...props }, ref) => {
    const baseClasses = 'flex flex-row justify-start items-center mb-1';
    
    return (
      <View
        ref={ref}
        {...props}
        className={`${baseClasses} ${className}`}
      />
    );
  }
);

// Simple FormControlLabelText
export const FormControlLabelText = React.forwardRef<Text, IFormControlLabelTextProps>(
  ({ className = '', size = 'md', ...props }, ref) => {
    const sizeClasses = {
      'xs': 'text-xs',
      'sm': 'text-sm',
      'md': 'text-base',
      'lg': 'text-lg',
    };
    
    const baseClasses = 'font-medium text-typography-900';
    const combinedClasses = `${baseClasses} ${typeof size === 'string' ? sizeClasses[size as keyof typeof sizeClasses] || '' : ''} ${className}`;
    
    return (
      <Text
        ref={ref}
        {...props}
        className={combinedClasses}
      />
    );
  }
);

// Simple FormControlLabelAstrick
export const FormControlLabelAstrick = React.forwardRef<Text, IFormControlLabelAstrickProps>(
  ({ className = '', ...props }, ref) => {
    const baseClasses = 'font-medium text-typography-900';
    
    return (
      <Text
        ref={ref}
        {...props}
        className={`${baseClasses} ${className}`}
      />
    );
  }
);

// Simple FormControlHelper
export const FormControlHelper = React.forwardRef<View, IFormControlHelperProps>(
  ({ className = '', ...props }, ref) => {
    const baseClasses = 'flex flex-row justify-start items-center mt-1';
    
    return (
      <View
        ref={ref}
        {...props}
        className={`${baseClasses} ${className}`}
      />
    );
  }
);

// Simple FormControlHelperText
export const FormControlHelperText = React.forwardRef<Text, IFormControlHelperTextProps>(
  ({ className = '', size = 'md', ...props }, ref) => {
    const sizeClasses = {
      'xs': 'text-xs',
      'sm': 'text-xs',
      'md': 'text-sm',
      'lg': 'text-base',
    };
    
    const baseClasses = 'text-typography-500';
    const combinedClasses = `${baseClasses} ${typeof size === 'string' ? sizeClasses[size as keyof typeof sizeClasses] || '' : ''} ${className}`;
    
    return (
      <Text
        ref={ref}
        {...props}
        className={combinedClasses}
      />
    );
  }
);

// Display names
FormControl.displayName = 'FormControl';
FormControlError.displayName = 'FormControlError';
FormControlErrorText.displayName = 'FormControlErrorText';
FormControlErrorIcon.displayName = 'FormControlErrorIcon';
FormControlLabel.displayName = 'FormControlLabel';
FormControlLabelText.displayName = 'FormControlLabelText';
FormControlLabelAstrick.displayName = 'FormControlLabelAstrick';
FormControlHelper.displayName = 'FormControlHelper';
FormControlHelperText.displayName = 'FormControlHelperText';