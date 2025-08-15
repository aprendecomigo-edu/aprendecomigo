import React, { useState } from 'react';
import { View, Text, ScrollView, Alert } from 'react-native';

// Import all v2 components (simplified versions for testing)
import { Button, ButtonText, ButtonGroup } from '@/components/ui/button/button-v2-simple';
import { Input, InputField, InputIcon, InputSlot } from '@/components/ui/input/input-v2-simple';
import { 
  Modal, 
  ModalBackdrop, 
  ModalContent, 
  ModalHeader, 
  ModalCloseButton,
  ModalBody,
  ModalFooter 
} from '@/components/ui/modal/modal-v2-simple';
import { Toast, ToastTitle, ToastDescription, useToast } from '@/components/ui/toast/toast-v2-simple';
import {
  FormControl,
  FormControlLabel,
  FormControlLabelText,
  FormControlHelper,
  FormControlHelperText,
  FormControlError,
  FormControlErrorIcon,
  FormControlErrorText
} from '@/components/ui/form-control/form-control-v2-simple';
import { X, AlertCircle } from 'lucide-react-native';

export default function TestV2AllComponentsScreen() {
  // State for testing
  const [showModal, setShowModal] = useState(false);
  const [inputValue, setInputValue] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [formError, setFormError] = useState(false);
  const toast = useToast();

  // Test handlers
  const handleShowToast = (variant: 'success' | 'error' | 'warning' | 'info') => {
    const messages = {
      success: { title: 'Success!', description: 'Operation completed successfully' },
      error: { title: 'Error!', description: 'Something went wrong' },
      warning: { title: 'Warning!', description: 'Please be careful' },
      info: { title: 'Info', description: 'Here is some information' }
    };
    
    toast.show({
      placement: 'top',
      render: ({ id }) => (
        <Toast action={variant} variant="solid">
          <ToastTitle>{messages[variant].title}</ToastTitle>
          <ToastDescription>{messages[variant].description}</ToastDescription>
        </Toast>
      ),
    });
  };

  const handleFormSubmit = () => {
    if (!email || !password) {
      setFormError(true);
      Alert.alert('Validation Error', 'Please fill in all fields');
    } else {
      setFormError(false);
      Alert.alert('Success', `Form submitted with email: ${email}`);
    }
  };

  return (
    <ScrollView className="flex-1 bg-background-0">
      <View className="p-6 gap-8">
        <View>
          <Text className="text-3xl font-bold mb-2">V2 Components Test Suite</Text>
          <Text className="text-base text-typography-500">
            Testing all high-priority Gluestack UI v2 components
          </Text>
        </View>

        {/* Button Component Tests */}
        <View className="gap-4">
          <Text className="text-xl font-semibold">1. Button Component</Text>
          
          <Text className="text-sm text-typography-500">Variants:</Text>
          <ButtonGroup space="sm">
            <Button variant="solid" action="primary">
              <ButtonText>Solid</ButtonText>
            </Button>
            <Button variant="outline" action="secondary">
              <ButtonText>Outline</ButtonText>
            </Button>
            <Button variant="link" action="default">
              <ButtonText>Link</ButtonText>
            </Button>
          </ButtonGroup>

          <Text className="text-sm text-typography-500">Sizes:</Text>
          <View className="gap-2">
            <Button size="xs"><ButtonText>Extra Small</ButtonText></Button>
            <Button size="md"><ButtonText>Medium</ButtonText></Button>
            <Button size="xl"><ButtonText>Extra Large</ButtonText></Button>
          </View>

          <Text className="text-sm text-typography-500">States:</Text>
          <Button disabled>
            <ButtonText>Disabled Button</ButtonText>
          </Button>
        </View>

        {/* Input Component Tests */}
        <View className="gap-4">
          <Text className="text-xl font-semibold">2. Input Component</Text>
          
          <Text className="text-sm text-typography-500">Basic Input:</Text>
          <Input variant="outline" size="md">
            <InputField 
              placeholder="Enter text here"
              value={inputValue}
              onChangeText={setInputValue}
            />
          </Input>

          <Text className="text-sm text-typography-500">Variants:</Text>
          <Input variant="underlined">
            <InputField placeholder="Underlined input" />
          </Input>
          <Input variant="rounded">
            <InputField placeholder="Rounded input" />
          </Input>

          <Text className="text-sm text-typography-500">With Icons:</Text>
          <Input>
            <InputIcon>
              <Text>📧</Text>
            </InputIcon>
            <InputField placeholder="Email address" />
          </Input>

          <Text className="text-sm text-typography-500">Disabled:</Text>
          <Input isDisabled>
            <InputField placeholder="Disabled input" />
          </Input>
        </View>

        {/* Form Control Tests */}
        <View className="gap-4">
          <Text className="text-xl font-semibold">3. Form Control Component</Text>
          
          <FormControl isRequired isInvalid={formError}>
            <FormControlLabel>
              <FormControlLabelText>Email</FormControlLabelText>
            </FormControlLabel>
            <Input>
              <InputField 
                placeholder="Enter email"
                value={email}
                onChangeText={setEmail}
              />
            </Input>
            <FormControlHelper>
              <FormControlHelperText>
                We'll never share your email
              </FormControlHelperText>
            </FormControlHelper>
            {formError && (
              <FormControlError>
                <FormControlErrorIcon as={AlertCircle} />
                <FormControlErrorText>
                  Email is required
                </FormControlErrorText>
              </FormControlError>
            )}
          </FormControl>

          <FormControl isRequired isInvalid={formError}>
            <FormControlLabel>
              <FormControlLabelText>Password</FormControlLabelText>
            </FormControlLabel>
            <Input>
              <InputField 
                placeholder="Enter password"
                secureTextEntry
                value={password}
                onChangeText={setPassword}
              />
            </Input>
            {formError && (
              <FormControlError>
                <FormControlErrorText>
                  Password is required
                </FormControlErrorText>
              </FormControlError>
            )}
          </FormControl>

          <Button onPress={handleFormSubmit}>
            <ButtonText>Submit Form</ButtonText>
          </Button>
        </View>

        {/* Modal Component Tests */}
        <View className="gap-4">
          <Text className="text-xl font-semibold">4. Modal Component</Text>
          
          <Button onPress={() => setShowModal(true)}>
            <ButtonText>Open Modal</ButtonText>
          </Button>

          <Modal
            isOpen={showModal}
            onClose={() => setShowModal(false)}
            size="md"
          >
            <ModalBackdrop />
            <ModalContent>
              <ModalHeader>
                <Text className="text-lg font-semibold">Modal Title</Text>
                <ModalCloseButton onPress={() => setShowModal(false)}>
                  <X size={24} />
                </ModalCloseButton>
              </ModalHeader>
              <ModalBody>
                <Text>
                  This is a test modal using the v2 implementation.
                  It should work exactly like the v1 modal but without
                  factory functions.
                </Text>
              </ModalBody>
              <ModalFooter>
                <ButtonGroup space="sm">
                  <Button
                    variant="outline"
                    onPress={() => setShowModal(false)}
                  >
                    <ButtonText>Cancel</ButtonText>
                  </Button>
                  <Button
                    action="primary"
                    onPress={() => {
                      Alert.alert('Confirmed!');
                      setShowModal(false);
                    }}
                  >
                    <ButtonText>Confirm</ButtonText>
                  </Button>
                </ButtonGroup>
              </ModalFooter>
            </ModalContent>
          </Modal>
        </View>

        {/* Toast Component Tests */}
        <View className="gap-4">
          <Text className="text-xl font-semibold">5. Toast Component</Text>
          
          <Text className="text-sm text-typography-500">Show different toast variants:</Text>
          <ButtonGroup space="sm">
            <Button 
              action="positive"
              onPress={() => handleShowToast('success')}
            >
              <ButtonText>Success</ButtonText>
            </Button>
            <Button 
              action="negative"
              onPress={() => handleShowToast('error')}
            >
              <ButtonText>Error</ButtonText>
            </Button>
          </ButtonGroup>
          
          <ButtonGroup space="sm">
            <Button 
              variant="outline"
              onPress={() => handleShowToast('warning')}
            >
              <ButtonText>Warning</ButtonText>
            </Button>
            <Button 
              variant="outline"
              onPress={() => handleShowToast('info')}
            >
              <ButtonText>Info</ButtonText>
            </Button>
          </ButtonGroup>
        </View>

        {/* Test Results Summary */}
        <View className="p-4 bg-success-50 rounded-lg">
          <Text className="text-lg font-semibold text-success-700 mb-2">
            ✅ Components Ready for Testing
          </Text>
          <Text className="text-sm text-success-600">
            1. Button - All variants, sizes, and states{'\n'}
            2. Input - All variants with icons and states{'\n'}
            3. Form Control - Validation and error states{'\n'}
            4. Modal - Open/close with backdrop{'\n'}
            5. Toast - All notification variants
          </Text>
        </View>

        <View className="p-4 bg-info-50 rounded-lg">
          <Text className="text-lg font-semibold text-info-700 mb-2">
            📋 Testing Checklist
          </Text>
          <Text className="text-sm text-info-600">
            • Click all buttons - should respond{'\n'}
            • Type in inputs - text should appear{'\n'}
            • Submit empty form - should show errors{'\n'}
            • Open/close modal - should animate{'\n'}
            • Show all toasts - should appear and dismiss{'\n'}
            • Check disabled states - should not respond
          </Text>
        </View>
      </View>
    </ScrollView>
  );
}