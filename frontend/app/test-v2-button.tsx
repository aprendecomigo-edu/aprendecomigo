import React, { useState } from 'react';
import { View, Text, ScrollView } from 'react-native';
import { Button, ButtonText, ButtonIcon, ButtonSpinner, ButtonGroup } from '@/components/ui/button/button-v2-simple';
import { ChevronRight } from 'lucide-react-native';

export default function TestV2ButtonScreen() {
  const [isLoading, setIsLoading] = useState(false);
  const [clickCount, setClickCount] = useState(0);

  const handleClick = () => {
    setClickCount(prev => prev + 1);
  };

  const handleLoadingClick = () => {
    setIsLoading(true);
    setTimeout(() => setIsLoading(false), 2000);
  };

  return (
    <ScrollView className="flex-1 bg-background-0">
      <View className="p-6 gap-8">
        <View>
          <Text className="text-2xl font-bold mb-4">V2 Button Test Page</Text>
          <Text className="text-base text-typography-500 mb-6">
            Testing Gluestack UI v2 Button implementation without factory functions
          </Text>
        </View>

        {/* Click Counter Test */}
        <View className="gap-4">
          <Text className="text-lg font-semibold">Interactive Test</Text>
          <Button onPress={handleClick} testID="click-counter-btn">
            <ButtonText>Clicked {clickCount} times</ButtonText>
          </Button>
        </View>

        {/* Variants */}
        <View className="gap-4">
          <Text className="text-lg font-semibold">Variants</Text>
          <Button variant="solid" action="primary" testID="solid-primary-btn">
            <ButtonText>Solid Primary</ButtonText>
          </Button>
          <Button variant="outline" action="secondary" testID="outline-secondary-btn">
            <ButtonText>Outline Secondary</ButtonText>
          </Button>
          <Button variant="link" action="default" testID="link-default-btn">
            <ButtonText>Link Default</ButtonText>
          </Button>
        </View>

        {/* Sizes */}
        <View className="gap-4">
          <Text className="text-lg font-semibold">Sizes</Text>
          <Button size="xs" testID="size-xs-btn">
            <ButtonText>Extra Small</ButtonText>
          </Button>
          <Button size="sm" testID="size-sm-btn">
            <ButtonText>Small</ButtonText>
          </Button>
          <Button size="md" testID="size-md-btn">
            <ButtonText>Medium</ButtonText>
          </Button>
          <Button size="lg" testID="size-lg-btn">
            <ButtonText>Large</ButtonText>
          </Button>
          <Button size="xl" testID="size-xl-btn">
            <ButtonText>Extra Large</ButtonText>
          </Button>
        </View>

        {/* Actions */}
        <View className="gap-4">
          <Text className="text-lg font-semibold">Actions</Text>
          <Button action="primary" testID="action-primary-btn">
            <ButtonText>Primary Action</ButtonText>
          </Button>
          <Button action="secondary" testID="action-secondary-btn">
            <ButtonText>Secondary Action</ButtonText>
          </Button>
          <Button action="positive" testID="action-positive-btn">
            <ButtonText>Positive Action</ButtonText>
          </Button>
          <Button action="negative" testID="action-negative-btn">
            <ButtonText>Negative Action</ButtonText>
          </Button>
        </View>

        {/* With Icons */}
        <View className="gap-4">
          <Text className="text-lg font-semibold">With Icons</Text>
          <Button testID="icon-btn">
            <ButtonText>Next</ButtonText>
            <ButtonIcon as={ChevronRight} />
          </Button>
        </View>

        {/* Loading State */}
        <View className="gap-4">
          <Text className="text-lg font-semibold">Loading State</Text>
          <Button onPress={handleLoadingClick} disabled={isLoading} testID="loading-btn">
            {isLoading && <ButtonSpinner />}
            <ButtonText>{isLoading ? 'Loading...' : 'Click to Load'}</ButtonText>
          </Button>
        </View>

        {/* Disabled State */}
        <View className="gap-4">
          <Text className="text-lg font-semibold">Disabled State</Text>
          <Button disabled testID="disabled-btn">
            <ButtonText>Disabled Button</ButtonText>
          </Button>
        </View>

        {/* Button Group */}
        <View className="gap-4">
          <Text className="text-lg font-semibold">Button Group</Text>
          <ButtonGroup space="sm">
            <Button variant="outline" testID="group-btn-1">
              <ButtonText>Option 1</ButtonText>
            </Button>
            <Button variant="outline" testID="group-btn-2">
              <ButtonText>Option 2</ButtonText>
            </Button>
            <Button variant="outline" testID="group-btn-3">
              <ButtonText>Option 3</ButtonText>
            </Button>
          </ButtonGroup>
        </View>
      </View>
    </ScrollView>
  );
}