import { Platform } from 'react-native';
import { tva } from '@gluestack-ui/nativewind-utils/tva';

const isWeb = Platform.OS === 'web';
const baseStyle = isWeb ? 'flex flex-col relative z-0' : '';

export const centerStyle = tva({
  base: `justify-center items-center ${baseStyle}`,
});
