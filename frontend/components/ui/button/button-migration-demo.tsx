import React from 'react';
import { View, Text } from 'react-native';

// v1 imports (current implementation)
import { Button as ButtonV1, ButtonText as ButtonTextV1 } from './index';

// v2 imports (new implementation without factory functions)
import { Button as ButtonV2, ButtonText as ButtonTextV2 } from './button-v2';

/**
 * Demo component showing v1 vs v2 Button implementation
 * This demonstrates that both versions work identically from a usage perspective
 */
export function ButtonMigrationDemo() {
  return (
    <View style={{ padding: 20, gap: 20 }}>
      <Text style={{ fontSize: 18, fontWeight: 'bold' }}>Button Migration Demo</Text>
      
      <View>
        <Text style={{ marginBottom: 8 }}>V1 Button (with factory function):</Text>
        <ButtonV1 
          onPress={() => console.log('V1 Button pressed')}
          variant="solid"
          action="primary"
        >
          <ButtonTextV1>V1 Button</ButtonTextV1>
        </ButtonV1>
      </View>

      <View>
        <Text style={{ marginBottom: 8 }}>V2 Button (without factory function):</Text>
        <ButtonV2 
          onPress={() => console.log('V2 Button pressed')}
          variant="solid"
          action="primary"
        >
          <ButtonTextV2>V2 Button</ButtonTextV2>
        </ButtonV2>
      </View>

      <View>
        <Text style={{ marginBottom: 8 }}>V2 Button Variants:</Text>
        <View style={{ gap: 10 }}>
          <ButtonV2 variant="solid" action="primary">
            <ButtonTextV2>Solid Primary</ButtonTextV2>
          </ButtonV2>
          
          <ButtonV2 variant="outline" action="secondary">
            <ButtonTextV2>Outline Secondary</ButtonTextV2>
          </ButtonV2>
          
          <ButtonV2 variant="link" action="default">
            <ButtonTextV2>Link Default</ButtonTextV2>
          </ButtonV2>
        </View>
      </View>

      <View>
        <Text style={{ marginBottom: 8 }}>V2 Button Sizes:</Text>
        <View style={{ gap: 10 }}>
          <ButtonV2 size="xs">
            <ButtonTextV2>Extra Small</ButtonTextV2>
          </ButtonV2>
          
          <ButtonV2 size="md">
            <ButtonTextV2>Medium</ButtonTextV2>
          </ButtonV2>
          
          <ButtonV2 size="xl">
            <ButtonTextV2>Extra Large</ButtonTextV2>
          </ButtonV2>
        </View>
      </View>
    </View>
  );
}