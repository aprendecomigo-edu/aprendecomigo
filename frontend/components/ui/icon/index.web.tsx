import { VariantProps } from '@gluestack-ui/nativewind-utils';
import { tva } from '@gluestack-ui/nativewind-utils/tva';
import React, { useMemo } from 'react';

const accessClassName = (style: any) => {
  const obj = style[0];
  const keys = Object.keys(obj);
  return obj[keys[1]];
};

const Svg = React.forwardRef<React.ElementRef<'svg'>, React.ComponentPropsWithoutRef<'svg'>>(
  ({ style, className, ...props }, ref) => {
    const calculateClassName = useMemo(() => {
      return className === undefined ? accessClassName(style) : className;
    }, [className, style]);

    return <svg ref={ref} {...props} className={calculateClassName} />;
  },
);

type IPrimitiveIcon = {
  height?: number | string;
  width?: number | string;
  fill?: string;
  color?: string;
  size?: number | string;
  stroke?: string;
  as?: React.ElementType;
  className?: string;
};

const PrimitiveIcon = React.forwardRef<
  React.ElementRef<'svg'>,
  React.ComponentPropsWithoutRef<'svg'> & IPrimitiveIcon
>(({ height, width, fill, color, size, stroke = 'currentColor', as: AsComp, ...props }, ref) => {
  const sizeProps = useMemo(() => {
    if (size) return { size };
    if (height && width) return { height, width };
    if (height) return { height };
    if (width) return { width };
    return {};
  }, [size, height, width]);

  const colorProps = stroke === 'currentColor' && color !== undefined ? color : stroke;

  if (AsComp) {
    return <AsComp ref={ref} fill={fill} {...props} {...sizeProps} stroke={colorProps} />;
  }
  return <Svg ref={ref} height={height} width={width} fill={fill} stroke={colorProps} {...props} />;
});

const UIIcon = React.forwardRef<
  React.ElementRef<typeof PrimitiveIcon>,
  React.ComponentPropsWithoutRef<typeof PrimitiveIcon>
>((props, ref) => {
  return <PrimitiveIcon ref={ref} {...props} />;
});

UIIcon.displayName = 'UIIcon';

export { UIIcon };

const iconStyle = tva({
  base: 'text-typography-950 fill-none',
  variants: {
    size: {
      '2xs': 'h-3 w-3',
      xs: 'h-3.5 w-3.5',
      sm: 'h-4 w-4',
      md: 'h-[18px] w-[18px]',
      lg: 'h-5 w-5',
      xl: 'h-6 w-6',
    },
  },
});

export const Icon = React.forwardRef<
  React.ElementRef<typeof UIIcon>,
  React.ComponentPropsWithoutRef<typeof UIIcon> &
    VariantProps<typeof iconStyle> & {
      height?: number | string;
      width?: number | string;
    }
>(({ size = 'md', className, ...props }, ref) => {
  if (typeof size === 'number') {
    return <UIIcon ref={ref} {...props} className={iconStyle({ class: className })} size={size} />;
  } else if ((props.height !== undefined || props.width !== undefined) && size === undefined) {
    return <UIIcon ref={ref} {...props} className={iconStyle({ class: className })} />;
  }
  return <UIIcon ref={ref} {...props} className={iconStyle({ size, class: className })} />;
});

// Create icons as simple React components following Gluestack UI v2 patterns
const AddIcon = React.forwardRef<React.ElementRef<'svg'>, React.ComponentPropsWithoutRef<'svg'>>((props, ref) => (
  <svg ref={ref} viewBox="0 0 24 24" {...props}>
    <path d="M12 5V19" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    <path d="M5 12H19" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
));

const AlertCircleIcon = React.forwardRef<React.ElementRef<'svg'>, React.ComponentPropsWithoutRef<'svg'>>((props, ref) => (
  <svg ref={ref} viewBox="0 0 24 24" {...props}>
    <path
      d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22Z"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path d="M12 8V12" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    <path d="M12 16H12.01" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
));

const ArrowUpIcon = React.forwardRef<React.ElementRef<'svg'>, React.ComponentPropsWithoutRef<'svg'>>((props, ref) => (
  <svg ref={ref} viewBox="0 0 24 24" {...props}>
    <path d="M12 19V5" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    <path d="M5 12L12 5L19 12" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
));

const ArrowDownIcon = React.forwardRef<React.ElementRef<'svg'>, React.ComponentPropsWithoutRef<'svg'>>((props, ref) => (
  <svg ref={ref} viewBox="0 0 24 24" {...props}>
    <path d="M12 5V19" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    <path d="M19 12L12 19L5 12" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
));

const ArrowRightIcon = React.forwardRef<React.ElementRef<'svg'>, React.ComponentPropsWithoutRef<'svg'>>((props, ref) => (
  <svg ref={ref} viewBox="0 0 24 24" {...props}>
    <path d="M5 12H19" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    <path d="M12 5L19 12L12 19" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
));

const ArrowLeftIcon = React.forwardRef<React.ElementRef<'svg'>, React.ComponentPropsWithoutRef<'svg'>>((props, ref) => (
  <svg ref={ref} viewBox="0 0 24 24" {...props}>
    <path d="M19 12H5" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    <path d="M12 19L5 12L12 5" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
));

const AtSignIcon = React.forwardRef<React.ElementRef<'svg'>, React.ComponentPropsWithoutRef<'svg'>>((props, ref) => (
  <svg ref={ref} viewBox="0 0 24 24" {...props}>
    <path
      d="M12 16C14.2091 16 16 14.2091 16 12C16 9.79086 14.2091 8 12 8C9.79086 8 8 9.79086 8 12C8 14.2091 9.79086 16 12 16Z"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path
      d="M16 7.99999V13C16 13.7956 16.3161 14.5587 16.8787 15.1213C17.4413 15.6839 18.2044 16 19 16C19.7957 16 20.5587 15.6839 21.1213 15.1213C21.6839 14.5587 22 13.7956 22 13V12C21.9999 9.74302 21.2362 7.55247 19.8333 5.78452C18.4303 4.01658 16.4706 2.77521 14.2726 2.26229C12.0747 1.74936 9.76794 1.99503 7.72736 2.95936C5.68677 3.92368 4.03241 5.54995 3.03327 7.57371C2.03413 9.59748 1.74898 11.8997 2.22418 14.1061C2.69938 16.3125 3.90699 18.2932 5.65064 19.7263C7.39429 21.1593 9.57144 21.9603 11.8281 21.9991C14.0847 22.0379 16.2881 21.3122 18.08 19.94"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
));

const BellIcon = React.forwardRef<React.ElementRef<'svg'>, React.ComponentPropsWithoutRef<'svg'>>((props, ref) => (
  <svg ref={ref} viewBox="0 0 24 24" {...props}>
    <path
      d="M18 8C18 6.4087 17.3679 4.88258 16.2426 3.75736C15.1174 2.63214 13.5913 2 12 2C10.4087 2 8.88258 2.63214 7.75736 3.75736C6.63214 4.88258 6 6.4087 6 8C6 15 3 17 3 17H21C21 17 18 15 18 8Z"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path
      d="M13.73 21C13.5542 21.3031 13.3018 21.5547 12.9982 21.7295C12.6946 21.9044 12.3504 21.9965 12 21.9965C11.6496 21.9965 11.3054 21.9044 11.0018 21.7295C10.6982 21.5547 10.4458 21.3031 10.27 21"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
));

const CalendarDaysIcon = React.forwardRef<React.ElementRef<'svg'>, React.ComponentPropsWithoutRef<'svg'>>((props, ref) => (
  <svg ref={ref} viewBox="0 0 24 24" {...props}>
    <path
      d="M19 4H5C3.89543 4 3 4.89543 3 6V20C3 21.1046 3.89543 22 5 22H19C20.1046 22 21 21.1046 21 20V6C21 4.89543 20.1046 4 19 4Z"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path d="M16 2V6" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    <path d="M8 2V6" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    <path d="M3 10H21" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    <path d="M8 14H8.01" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    <path d="M12 14H12.01" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    <path d="M16 14H16.01" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    <path d="M8 18H8.01" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    <path d="M12 18H12.01" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    <path d="M16 18H16.01" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
));

const CheckIcon = React.forwardRef<React.ElementRef<'svg'>, React.ComponentPropsWithoutRef<'svg'>>((props, ref) => (
  <svg ref={ref} viewBox="0 0 24 24" {...props}>
    <path d="M20 6L9 17L4 12" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
));

const CheckCircleIcon = React.forwardRef<React.ElementRef<'svg'>, React.ComponentPropsWithoutRef<'svg'>>((props, ref) => (
  <svg ref={ref} viewBox="0 0 24 24" {...props}>
    <path
      d="M12 22C17.523 22 22 17.523 22 12C22 6.477 17.523 2 12 2C6.477 2 2 6.477 2 12C2 17.523 6.477 22 12 22Z"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path d="M9 12L11 14L15 10" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
));

const ChevronUpIcon = React.forwardRef<React.ElementRef<'svg'>, React.ComponentPropsWithoutRef<'svg'>>((props, ref) => (
  <svg ref={ref} viewBox="0 0 24 24" {...props}>
    <path d="M18 15L12 9L6 15" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
));

const ChevronDownIcon = React.forwardRef<React.ElementRef<'svg'>, React.ComponentPropsWithoutRef<'svg'>>((props, ref) => (
  <svg ref={ref} viewBox="0 0 24 24" {...props}>
    <path d="M6 9L12 15L18 9" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
));

const ChevronLeftIcon = React.forwardRef<React.ElementRef<'svg'>, React.ComponentPropsWithoutRef<'svg'>>((props, ref) => (
  <svg ref={ref} viewBox="0 0 24 24" {...props}>
    <path d="M15 18L9 12L15 6" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
));

const ChevronRightIcon = React.forwardRef<React.ElementRef<'svg'>, React.ComponentPropsWithoutRef<'svg'>>((props, ref) => (
  <svg ref={ref} viewBox="0 0 24 24" {...props}>
    <path d="M9 18L15 12L9 6" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
));

const ChevronsLeftIcon = React.forwardRef<React.ElementRef<'svg'>, React.ComponentPropsWithoutRef<'svg'>>((props, ref) => (
  <svg ref={ref} viewBox="0 0 24 24" {...props}>
    <path d="M11 17L6 12L11 7" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    <path d="M18 17L13 12L18 7" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
));

const ChevronsRightIcon = React.forwardRef<React.ElementRef<'svg'>, React.ComponentPropsWithoutRef<'svg'>>((props, ref) => (
  <svg ref={ref} viewBox="0 0 24 24" {...props}>
    <path d="M13 17L18 12L13 7" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    <path d="M6 17L11 12L6 7" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
));

const ChevronsUpDownIcon = React.forwardRef<React.ElementRef<'svg'>, React.ComponentPropsWithoutRef<'svg'>>((props, ref) => (
  <svg ref={ref} viewBox="0 0 24 24" {...props}>
    <path d="M7 15L12 20L17 15" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    <path d="M7 9L12 4L17 9" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
));

const CircleIcon = React.forwardRef<React.ElementRef<'svg'>, React.ComponentPropsWithoutRef<'svg'>>((props, ref) => (
  <svg ref={ref} viewBox="0 0 24 24" {...props}>
    <path
      d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22Z"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
));

const ClockIcon = React.forwardRef<React.ElementRef<'svg'>, React.ComponentPropsWithoutRef<'svg'>>((props, ref) => (
  <svg ref={ref} viewBox="0 0 24 24" {...props}>
    <path
      d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22Z"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path d="M12 6V12L16 14" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
));

const CloseIcon = React.forwardRef<React.ElementRef<'svg'>, React.ComponentPropsWithoutRef<'svg'>>((props, ref) => (
  <svg ref={ref} viewBox="0 0 24 24" {...props}>
    <path d="M18 6L6 18" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    <path d="M6 6L18 18" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
));

const CloseCircleIcon = React.forwardRef<React.ElementRef<'svg'>, React.ComponentPropsWithoutRef<'svg'>>((props, ref) => (
  <svg ref={ref} viewBox="0 0 24 24" {...props}>
    <path
      d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22Z"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path d="M15 9L9 15" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    <path d="M9 9L15 15" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
));

// Add display names for better debugging
AddIcon.displayName = 'AddIcon';
AlertCircleIcon.displayName = 'AlertCircleIcon';
ArrowUpIcon.displayName = 'ArrowUpIcon';
ArrowDownIcon.displayName = 'ArrowDownIcon';
ArrowRightIcon.displayName = 'ArrowRightIcon';
ArrowLeftIcon.displayName = 'ArrowLeftIcon';
AtSignIcon.displayName = 'AtSignIcon';
BellIcon.displayName = 'BellIcon';
CalendarDaysIcon.displayName = 'CalendarDaysIcon';
CheckIcon.displayName = 'CheckIcon';
CheckCircleIcon.displayName = 'CheckCircleIcon';
ChevronUpIcon.displayName = 'ChevronUpIcon';
ChevronDownIcon.displayName = 'ChevronDownIcon';
ChevronLeftIcon.displayName = 'ChevronLeftIcon';
ChevronRightIcon.displayName = 'ChevronRightIcon';
ChevronsLeftIcon.displayName = 'ChevronsLeftIcon';
ChevronsRightIcon.displayName = 'ChevronsRightIcon';
ChevronsUpDownIcon.displayName = 'ChevronsUpDownIcon';
CircleIcon.displayName = 'CircleIcon';
ClockIcon.displayName = 'ClockIcon';
CloseIcon.displayName = 'CloseIcon';
CloseCircleIcon.displayName = 'CloseCircleIcon';

// Export all icons
export {
  AddIcon,
  AlertCircleIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  ArrowRightIcon,
  ArrowLeftIcon,
  AtSignIcon,
  BellIcon,
  CalendarDaysIcon,
  CheckIcon,
  CheckCircleIcon,
  ChevronUpIcon,
  ChevronDownIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  ChevronsLeftIcon,
  ChevronsRightIcon,
  ChevronsUpDownIcon,
  CircleIcon,
  ClockIcon,
  CloseIcon,
  CloseCircleIcon,
};