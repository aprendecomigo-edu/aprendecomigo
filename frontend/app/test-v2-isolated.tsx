import React, { useState } from 'react';
import { View, Text, ScrollView, StyleSheet } from 'react-native';

// Only import the simplified Button component for isolated testing
import { Button, ButtonText } from '@/components/ui/button/button-v2-simple';

export default function TestV2IsolatedScreen() {
  const [clickCount, setClickCount] = useState(0);

  return (
    <ScrollView style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.title}>V2 Button Isolated Test</Text>
        <Text style={styles.subtitle}>Testing only the Button v2 simple implementation</Text>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Interactive Test</Text>
          <Button onPress={() => setClickCount(prev => prev + 1)} variant="solid" action="primary">
            <ButtonText>Clicked {clickCount} times</ButtonText>
          </Button>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Button Variants</Text>
          <View style={styles.buttonGroup}>
            <Button variant="solid" action="primary">
              <ButtonText>Solid Primary</ButtonText>
            </Button>
            <Button variant="outline" action="secondary">
              <ButtonText>Outline Secondary</ButtonText>
            </Button>
            <Button variant="link" action="default">
              <ButtonText>Link Default</ButtonText>
            </Button>
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Button Sizes</Text>
          <View style={styles.buttonColumn}>
            <Button size="xs">
              <ButtonText>Extra Small</ButtonText>
            </Button>
            <Button size="md">
              <ButtonText>Medium</ButtonText>
            </Button>
            <Button size="xl">
              <ButtonText>Extra Large</ButtonText>
            </Button>
          </View>
        </View>

        <View style={styles.successBox}>
          <Text style={styles.successTitle}>✅ If you can see and click these buttons</Text>
          <Text style={styles.successText}>The v2 Button migration is working correctly!</Text>
        </View>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f9fafb',
  },
  content: {
    padding: 24,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#6b7280',
    marginBottom: 32,
  },
  section: {
    marginBottom: 32,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 16,
  },
  buttonGroup: {
    gap: 12,
  },
  buttonColumn: {
    gap: 8,
  },
  successBox: {
    backgroundColor: '#d1fae5',
    padding: 16,
    borderRadius: 8,
    marginTop: 32,
  },
  successTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#065f46',
    marginBottom: 4,
  },
  successText: {
    fontSize: 14,
    color: '#047857',
  },
});
