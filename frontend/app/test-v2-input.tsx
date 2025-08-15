import React, { useState } from 'react';
import { View, Text, ScrollView, StyleSheet } from 'react-native';

import { Input, InputField, InputIcon, InputSlot } from '@/components/ui/input/input-v2-simple';

export default function TestV2InputScreen() {
  const [value1, setValue1] = useState('');
  const [value2, setValue2] = useState('');
  const [value3, setValue3] = useState('');

  return (
    <ScrollView style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.title}>V2 Input Component Test</Text>

        <View style={styles.section}>
          <Text style={styles.label}>Basic Input (value: "{value1}")</Text>
          <Input variant="outline" size="md">
            <InputField placeholder="Type something..." value={value1} onChangeText={setValue1} />
          </Input>
        </View>

        <View style={styles.section}>
          <Text style={styles.label}>Underlined Input</Text>
          <Input variant="underlined">
            <InputField placeholder="Underlined style" value={value2} onChangeText={setValue2} />
          </Input>
        </View>

        <View style={styles.section}>
          <Text style={styles.label}>Rounded Input with Icon</Text>
          <Input variant="rounded">
            <InputIcon>
              <Text>🔍</Text>
            </InputIcon>
            <InputField placeholder="Search..." value={value3} onChangeText={setValue3} />
          </Input>
        </View>

        <View style={styles.section}>
          <Text style={styles.label}>Disabled Input</Text>
          <Input isDisabled>
            <InputField placeholder="This is disabled" />
          </Input>
        </View>

        <View style={styles.section}>
          <Text style={styles.label}>Invalid Input</Text>
          <Input isInvalid>
            <InputField placeholder="This has an error" />
          </Input>
        </View>

        <View style={styles.successBox}>
          <Text style={styles.successTitle}>✅ Test Results</Text>
          <Text style={styles.successText}>
            If you can type in the inputs and see the values update,{'\n'}
            the v2 Input migration is working correctly!
          </Text>
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
    marginBottom: 24,
  },
  section: {
    marginBottom: 24,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 8,
    color: '#374151',
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
