import React from 'react';
import { View, Text, Pressable } from 'react-native';

// Import v2 components and hook
import {
  Toast as ToastV2,
  ToastTitle as ToastTitleV2,
  ToastDescription as ToastDescriptionV2,
  useToast as useToastV2,
  ToastContainer as ToastContainerV2,
} from './toast-v2';

// Import v2 simple components and hook
import {
  Toast as ToastV2Simple,
  ToastTitle as ToastTitleV2Simple,
  ToastDescription as ToastDescriptionV2Simple,
  useToast as useToastV2Simple,
  ToastContainer as ToastContainerV2Simple,
} from './toast-v2-simple';

/**
 * Demo component to test Toast v2 implementations
 * Shows how the new useToast hook and Toast components work
 */
export function ToastMigrationDemo() {
  const toastV2 = useToastV2();
  const toastV2Simple = useToastV2Simple();

  const showToastV2 = (action: 'success' | 'error' | 'warning' | 'info' | 'muted') => {
    toastV2.show({
      title: 'v2 Toast',
      description: `This is a ${action} toast using the v2 implementation`,
      action,
      variant: 'solid',
      duration: 3000,
    });
  };

  const showToastV2Simple = (action: 'success' | 'error' | 'warning' | 'info' | 'muted') => {
    toastV2Simple.show({
      title: 'v2 Simple Toast',
      description: `This is a ${action} toast using the v2 simple implementation`,
      action,
      variant: 'solid',
      duration: 3000,
    });
  };

  return (
    <View className="flex-1 p-6">
      <Text className="text-xl font-bold mb-4">Toast Migration Demo</Text>
      <Text className="text-gray-600 mb-6">
        Test the v2 Toast implementations. Both should work identically with the useToast hook.
      </Text>

      {/* v2 Toast Demo */}
      <View className="mb-8">
        <Text className="text-lg font-semibold mb-3">v2 Toast (Full Implementation)</Text>
        <View className="flex-row flex-wrap gap-2">
          <Pressable
            onPress={() => showToastV2('success')}
            className="bg-green-500 px-3 py-2 rounded"
          >
            <Text className="text-white text-sm">Success</Text>
          </Pressable>
          <Pressable onPress={() => showToastV2('error')} className="bg-red-500 px-3 py-2 rounded">
            <Text className="text-white text-sm">Error</Text>
          </Pressable>
          <Pressable
            onPress={() => showToastV2('warning')}
            className="bg-yellow-500 px-3 py-2 rounded"
          >
            <Text className="text-white text-sm">Warning</Text>
          </Pressable>
          <Pressable onPress={() => showToastV2('info')} className="bg-blue-500 px-3 py-2 rounded">
            <Text className="text-white text-sm">Info</Text>
          </Pressable>
          <Pressable onPress={() => showToastV2('muted')} className="bg-gray-500 px-3 py-2 rounded">
            <Text className="text-white text-sm">Muted</Text>
          </Pressable>
        </View>
        <Pressable onPress={() => toastV2.hideAll()} className="bg-gray-300 px-3 py-2 rounded mt-2">
          <Text className="text-sm">Hide All v2</Text>
        </Pressable>
      </View>

      {/* v2 Simple Toast Demo */}
      <View className="mb-8">
        <Text className="text-lg font-semibold mb-3">v2 Simple Toast</Text>
        <View className="flex-row flex-wrap gap-2">
          <Pressable
            onPress={() => showToastV2Simple('success')}
            className="bg-green-600 px-3 py-2 rounded"
          >
            <Text className="text-white text-sm">Success</Text>
          </Pressable>
          <Pressable
            onPress={() => showToastV2Simple('error')}
            className="bg-red-600 px-3 py-2 rounded"
          >
            <Text className="text-white text-sm">Error</Text>
          </Pressable>
          <Pressable
            onPress={() => showToastV2Simple('warning')}
            className="bg-yellow-600 px-3 py-2 rounded"
          >
            <Text className="text-white text-sm">Warning</Text>
          </Pressable>
          <Pressable
            onPress={() => showToastV2Simple('info')}
            className="bg-blue-600 px-3 py-2 rounded"
          >
            <Text className="text-white text-sm">Info</Text>
          </Pressable>
          <Pressable
            onPress={() => showToastV2Simple('muted')}
            className="bg-gray-600 px-3 py-2 rounded"
          >
            <Text className="text-white text-sm">Muted</Text>
          </Pressable>
        </View>
        <Pressable
          onPress={() => toastV2Simple.hideAll()}
          className="bg-gray-300 px-3 py-2 rounded mt-2"
        >
          <Text className="text-sm">Hide All v2 Simple</Text>
        </Pressable>
      </View>

      {/* Manual Toast Examples */}
      <View className="mb-8">
        <Text className="text-lg font-semibold mb-3">Manual Toast Components</Text>

        <Text className="text-md font-medium mb-2">v2 Toast Example:</Text>
        <ToastV2 variant="solid" action="info" className="mb-2">
          <ToastTitleV2>Manual v2 Toast</ToastTitleV2>
          <ToastDescriptionV2>This toast is rendered manually</ToastDescriptionV2>
        </ToastV2>

        <Text className="text-md font-medium mb-2 mt-4">v2 Simple Toast Example:</Text>
        <ToastV2Simple variant="outline" action="success" className="mb-2">
          <ToastTitleV2Simple>Manual v2 Simple Toast</ToastTitleV2Simple>
          <ToastDescriptionV2Simple>This toast is also rendered manually</ToastDescriptionV2Simple>
        </ToastV2Simple>
      </View>

      <View className="p-4 bg-gray-100 rounded-md">
        <Text className="text-sm">
          <Text className="font-semibold">Test Results:</Text> {'\n'}• useToast hook should work
          without factory functions{'\n'}• Toast colors should match actions (success=green,
          error=red, etc.){'\n'}• Toasts should auto-hide after 3 seconds{'\n'}• Hide All buttons
          should clear all toasts{'\n'}• Manual toasts should display immediately
        </Text>
      </View>

      {/* Toast Containers - Required for toasts to show */}
      <ToastContainerV2 />
      <ToastContainerV2Simple />
    </View>
  );
}
