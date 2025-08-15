import React from 'react';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { View } from '@/components/ui/view';

interface LoadingScreenProps {
  message?: string;
  size?: 'small' | 'large';
  className?: string;
}

/**
 * Reusable loading screen component for Suspense fallbacks and async operations
 * Used throughout the app for consistent loading states
 */
export function LoadingScreen({ 
  message = 'Loading...', 
  size = 'large',
  className = 'flex-1 justify-center items-center bg-gray-50'
}: LoadingScreenProps) {
  return (
    <View className={className}>
      <Spinner size={size} />
      <Text className="mt-4 text-gray-600">{message}</Text>
    </View>
  );
}

export default LoadingScreen;