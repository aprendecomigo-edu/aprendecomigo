import React from 'react';
import { Platform } from 'react-native';
import { SafeAreaView } from '@/components/ui/safe-area-view';
import { VStack } from '@/components/ui/vstack';
import { View } from '@/components/ui/view';

type AuthLayoutProps = {
  children: React.ReactNode;
};

export const AuthLayout = (props: AuthLayoutProps) => {
  return (
    <SafeAreaView className="flex-1 w-full h-full">
      {/* Full screen container with proper flex hierarchy */}
      <View className="flex-1 w-full h-full">
        {/* White background with colorful geometric shapes */}
        <View className="flex-1 w-full bg-white relative overflow-hidden">
          {/* Colorful tilted background shape - single large circle */}
          <View className="absolute inset-0">
            {/* Single large top-left gradient shape */}
            <View 
              className="absolute -top-56 -left-70 w-[90rem] h-[50rem] rounded-full opacity-80 bg-gradient-primary"
              style={{
                transform: 'rotate(-40deg)'
              }}
            />
          </View>
          
          {/* Content container - above the background shapes */}
          <VStack className="flex-1 w-full items-center p-4 md:p-6 relative z-10 min-h-screen">
            <View className="w-full max-w-2xl mx-auto my-auto flex-1 justify-center">
              {/* Glassmorphism card container - grows with content */}
              <View className="glass-container rounded-2xl p-6 md:p-8 backdrop-blur-xl bg-white/90">
                <VStack>
                  {props.children}
                </VStack>
              </View>
            </View>
          </VStack>
        </View>
      </View>
    </SafeAreaView>
  );
};