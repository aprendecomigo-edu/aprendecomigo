import React from 'react';
import { View, Text } from 'react-native';

// Test component to verify accent colors work
export const TestAccentColors = () => {
  return (
    <View className="p-4 space-y-4">
      <Text className="text-2xl font-bold text-primary-600">
        Updated Primary Color (Electric Blue: #0EA5E9)
      </Text>
      
      <View className="bg-accent-600 p-4 rounded-lg">
        <Text className="text-white font-semibold">
          Accent Golden Orange (#F59E0B)
        </Text>
      </View>
      
      <View className="bg-accent-dark-600 p-4 rounded-lg">
        <Text className="text-white font-semibold">
          Accent Dark Burnt Orange (#F97316)
        </Text>
      </View>
      
      <View className="bg-accent-pink-600 p-4 rounded-lg">
        <Text className="text-white font-semibold">
          Accent Pink Neon Magenta (#D946EF)
        </Text>
      </View>
      
      <Text className="font-brand text-xl text-accent-600">
        Kirang Haerang Brand Font
      </Text>
      
      <Text className="font-primary text-lg text-accent-dark-600">
        Work Sans Primary Font
      </Text>
      
      <Text className="font-body text-base text-accent-pink-600">
        Poppins Body Font
      </Text>
    </View>
  );
};