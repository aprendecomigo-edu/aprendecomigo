import { DollarSign, TrendingUp, AlertCircle } from 'lucide-react-native';
import React, { useState } from 'react';

import { Box } from '@/components/ui/box';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Input, InputField } from '@/components/ui/input';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

interface RateInputFieldProps {
  value: number;
  onChange: (value: number) => void;
  currency: string;
  suggestedRate?: { min: number; max: number; average: number };
  placeholder?: string;
  error?: string;
}

export const RateInputField: React.FC<RateInputFieldProps> = ({
  value,
  onChange,
  currency,
  suggestedRate,
  placeholder,
  error,
}) => {
  const [focused, setFocused] = useState(false);

  return (
    <VStack space="xs">
      <HStack space="sm" className="items-center">
        <Box className="flex-1">
          <HStack space="xs" className="items-center">
            <Icon as={DollarSign} className="text-gray-500" size="sm" />
            <Input className={`flex-1 ${error ? 'border-red-300' : ''}`}>
              <InputField
                value={value.toString()}
                onChangeText={text => {
                  const numValue = parseFloat(text) || 0;
                  onChange(numValue);
                }}
                onFocus={() => setFocused(true)}
                onBlur={() => setFocused(false)}
                placeholder={placeholder || '0'}
                keyboardType="numeric"
                className="text-right"
              />
            </Input>
            <Text className="text-gray-600 text-sm">{currency}/h</Text>
          </HStack>
        </Box>
      </HStack>

      {focused && suggestedRate && (
        <HStack space="xs" className="items-center">
          <Icon as={TrendingUp} className="text-blue-500" size="xs" />
          <Text className="text-blue-600 text-xs">
            Market: {suggestedRate.min}-{suggestedRate.max}
            {currency} (avg. {suggestedRate.average}
            {currency})
          </Text>
        </HStack>
      )}

      {error && (
        <HStack space="xs" className="items-center">
          <Icon as={AlertCircle} className="text-red-500" size="xs" />
          <Text className="text-red-600 text-xs">{error}</Text>
        </HStack>
      )}
    </VStack>
  );
};