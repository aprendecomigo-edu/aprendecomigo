import React, { useState } from 'react';
import { View, Text, TextInput, Pressable } from 'react-native';

// Import v1 components

// Import v2 components
import {
  FormControl as FormControlV2,
  FormControlError as FormControlErrorV2,
  FormControlErrorText as FormControlErrorTextV2,
  FormControlErrorIcon as FormControlErrorIconV2,
  FormControlLabel as FormControlLabelV2,
  FormControlLabelText as FormControlLabelTextV2,
  FormControlLabelAstrick as FormControlLabelAstrickV2,
  FormControlHelper as FormControlHelperV2,
  FormControlHelperText as FormControlHelperTextV2,
} from './form-control-v2';

// Import v2 simple components
import {
  FormControl as FormControlV2Simple,
  FormControlError as FormControlErrorV2Simple,
  FormControlErrorText as FormControlErrorTextV2Simple,
  FormControlErrorIcon as FormControlErrorIconV2Simple,
  FormControlLabel as FormControlLabelV2Simple,
  FormControlLabelText as FormControlLabelTextV2Simple,
  FormControlLabelAstrick as FormControlLabelAstrickV2Simple,
  FormControlHelper as FormControlHelperV2Simple,
  FormControlHelperText as FormControlHelperTextV2Simple,
} from './form-control-v2-simple';

import {
  FormControl as FormControlV1,
  FormControlError as FormControlErrorV1,
  FormControlErrorText as FormControlErrorTextV1,
  FormControlErrorIcon as FormControlErrorIconV1,
  FormControlLabel as FormControlLabelV1,
  FormControlLabelText as FormControlLabelTextV1,
  FormControlLabelAstrick as FormControlLabelAstrickV1,
  FormControlHelper as FormControlHelperV1,
  FormControlHelperText as FormControlHelperTextV1,
} from './index';

// Simple error icon component for demo
const ErrorIcon = () => (
  <View className="w-4 h-4 bg-red-500 rounded-full items-center justify-center">
    <Text className="text-white text-xs font-bold">!</Text>
  </View>
);

/**
 * Demo component to compare FormControl v1, v2, and v2-simple implementations
 * This helps verify that v2 components work identically to v1
 */
export function FormControlMigrationDemo() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showError, setShowError] = useState(false);

  const validateForm = () => {
    const hasErrors = !email.includes('@') || password.length < 6;
    setShowError(hasErrors);
    return !hasErrors;
  };

  return (
    <View className="flex-1 p-6">
      <Text className="text-xl font-bold mb-4">Form Control Migration Demo</Text>
      <Text className="text-gray-600 mb-6">
        Compare v1 (factory-based) and v2 (direct implementation) FormControl components. They
        should look and behave identically.
      </Text>

      <Pressable onPress={validateForm} className="bg-blue-500 p-2 rounded mb-6">
        <Text className="text-white text-center">Validate Forms (Toggle Errors)</Text>
      </Pressable>

      {/* v1 Form Control */}
      <View className="mb-8">
        <Text className="text-lg font-semibold mb-4">v1 FormControl (Factory)</Text>

        <FormControlV1 size="md" className="mb-4">
          <FormControlLabelV1>
            <FormControlLabelTextV1>Email</FormControlLabelTextV1>
            <FormControlLabelAstrickV1>*</FormControlLabelAstrickV1>
          </FormControlLabelV1>

          <TextInput
            value={email}
            onChangeText={setEmail}
            placeholder="Enter your email"
            className="border border-gray-300 px-3 py-2 rounded"
          />

          {showError && !email.includes('@') && (
            <FormControlErrorV1>
              <FormControlErrorIconV1 as={ErrorIcon} />
              <FormControlErrorTextV1>Please enter a valid email</FormControlErrorTextV1>
            </FormControlErrorV1>
          )}

          <FormControlHelperV1>
            <FormControlHelperTextV1>We'll never share your email</FormControlHelperTextV1>
          </FormControlHelperV1>
        </FormControlV1>

        <FormControlV1 size="md">
          <FormControlLabelV1>
            <FormControlLabelTextV1>Password</FormControlLabelTextV1>
            <FormControlLabelAstrickV1>*</FormControlLabelAstrickV1>
          </FormControlLabelV1>

          <TextInput
            value={password}
            onChangeText={setPassword}
            placeholder="Enter your password"
            secureTextEntry
            className="border border-gray-300 px-3 py-2 rounded"
          />

          {showError && password.length < 6 && (
            <FormControlErrorV1>
              <FormControlErrorIconV1 as={ErrorIcon} />
              <FormControlErrorTextV1>
                Password must be at least 6 characters
              </FormControlErrorTextV1>
            </FormControlErrorV1>
          )}

          <FormControlHelperV1>
            <FormControlHelperTextV1>Minimum 6 characters required</FormControlHelperTextV1>
          </FormControlHelperV1>
        </FormControlV1>
      </View>

      {/* v2 Form Control */}
      <View className="mb-8">
        <Text className="text-lg font-semibold mb-4">v2 FormControl (Direct)</Text>

        <FormControlV2 size="md" className="mb-4">
          <FormControlLabelV2>
            <FormControlLabelTextV2>Email</FormControlLabelTextV2>
            <FormControlLabelAstrickV2>*</FormControlLabelAstrickV2>
          </FormControlLabelV2>

          <TextInput
            value={email}
            onChangeText={setEmail}
            placeholder="Enter your email"
            className="border border-gray-300 px-3 py-2 rounded"
          />

          {showError && !email.includes('@') && (
            <FormControlErrorV2>
              <FormControlErrorIconV2 as={ErrorIcon} />
              <FormControlErrorTextV2>Please enter a valid email</FormControlErrorTextV2>
            </FormControlErrorV2>
          )}

          <FormControlHelperV2>
            <FormControlHelperTextV2>We'll never share your email</FormControlHelperTextV2>
          </FormControlHelperV2>
        </FormControlV2>

        <FormControlV2 size="md">
          <FormControlLabelV2>
            <FormControlLabelTextV2>Password</FormControlLabelTextV2>
            <FormControlLabelAstrickV2>*</FormControlLabelAstrickV2>
          </FormControlLabelV2>

          <TextInput
            value={password}
            onChangeText={setPassword}
            placeholder="Enter your password"
            secureTextEntry
            className="border border-gray-300 px-3 py-2 rounded"
          />

          {showError && password.length < 6 && (
            <FormControlErrorV2>
              <FormControlErrorIconV2 as={ErrorIcon} />
              <FormControlErrorTextV2>
                Password must be at least 6 characters
              </FormControlErrorTextV2>
            </FormControlErrorV2>
          )}

          <FormControlHelperV2>
            <FormControlHelperTextV2>Minimum 6 characters required</FormControlHelperTextV2>
          </FormControlHelperV2>
        </FormControlV2>
      </View>

      {/* v2 Simple Form Control */}
      <View className="mb-8">
        <Text className="text-lg font-semibold mb-4">v2 Simple FormControl</Text>

        <FormControlV2Simple size="md" className="mb-4">
          <FormControlLabelV2Simple>
            <FormControlLabelTextV2Simple>Email</FormControlLabelTextV2Simple>
            <FormControlLabelAstrickV2Simple>*</FormControlLabelAstrickV2Simple>
          </FormControlLabelV2Simple>

          <TextInput
            value={email}
            onChangeText={setEmail}
            placeholder="Enter your email"
            className="border border-gray-300 px-3 py-2 rounded"
          />

          {showError && !email.includes('@') && (
            <FormControlErrorV2Simple>
              <FormControlErrorIconV2Simple as={ErrorIcon} />
              <FormControlErrorTextV2Simple>
                Please enter a valid email
              </FormControlErrorTextV2Simple>
            </FormControlErrorV2Simple>
          )}

          <FormControlHelperV2Simple>
            <FormControlHelperTextV2Simple>
              We'll never share your email
            </FormControlHelperTextV2Simple>
          </FormControlHelperV2Simple>
        </FormControlV2Simple>

        <FormControlV2Simple size="md">
          <FormControlLabelV2Simple>
            <FormControlLabelTextV2Simple>Password</FormControlLabelTextV2Simple>
            <FormControlLabelAstrickV2Simple>*</FormControlLabelAstrickV2Simple>
          </FormControlLabelV2Simple>

          <TextInput
            value={password}
            onChangeText={setPassword}
            placeholder="Enter your password"
            secureTextEntry
            className="border border-gray-300 px-3 py-2 rounded"
          />

          {showError && password.length < 6 && (
            <FormControlErrorV2Simple>
              <FormControlErrorIconV2Simple as={ErrorIcon} />
              <FormControlErrorTextV2Simple>
                Password must be at least 6 characters
              </FormControlErrorTextV2Simple>
            </FormControlErrorV2Simple>
          )}

          <FormControlHelperV2Simple>
            <FormControlHelperTextV2Simple>
              Minimum 6 characters required
            </FormControlHelperTextV2Simple>
          </FormControlHelperV2Simple>
        </FormControlV2Simple>
      </View>

      <View className="p-4 bg-gray-100 rounded-md">
        <Text className="text-sm">
          <Text className="font-semibold">Test Results:</Text> {'\n'}• All three forms should look
          identical{'\n'}• Labels, helper text, and error states should work the same{'\n'}• Size
          variants should be consistent{'\n'}• Error icons should display properly{'\n'}• v2 Simple
          should have the same functionality with cleaner code
        </Text>
      </View>
    </View>
  );
}
