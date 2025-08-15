import React, { useState } from 'react';
import { View, Text, Pressable } from 'react-native';

// Import v1 components
import {
  Modal as ModalV1,
  ModalBackdrop as ModalBackdropV1,
  ModalContent as ModalContentV1,
  ModalHeader as ModalHeaderV1,
  ModalBody as ModalBodyV1,
  ModalFooter as ModalFooterV1,
  ModalCloseButton as ModalCloseButtonV1,
} from './index';

// Import v2 components
import {
  Modal as ModalV2,
  ModalBackdrop as ModalBackdropV2,
  ModalContent as ModalContentV2,
  ModalHeader as ModalHeaderV2,
  ModalBody as ModalBodyV2,
  ModalFooter as ModalFooterV2,
  ModalCloseButton as ModalCloseButtonV2,
} from './modal-v2';

// Import v2 simple components
import {
  Modal as ModalV2Simple,
  ModalBackdrop as ModalBackdropV2Simple,
  ModalContent as ModalContentV2Simple,
  ModalHeader as ModalHeaderV2Simple,
  ModalBody as ModalBodyV2Simple,
  ModalFooter as ModalFooterV2Simple,
  ModalCloseButton as ModalCloseButtonV2Simple,
} from './modal-v2-simple';

/**
 * Demo component to compare Modal v1, v2, and v2-simple implementations
 * This helps verify that v2 components work identically to v1
 */
export function ModalMigrationDemo() {
  const [showV1Modal, setShowV1Modal] = useState(false);
  const [showV2Modal, setShowV2Modal] = useState(false);
  const [showV2SimpleModal, setShowV2SimpleModal] = useState(false);

  const modalContent = (
    <>
      <Text>This is the modal content. Both v1 and v2 should look identical.</Text>
      <Text className="mt-2 text-sm text-gray-600">
        The v2 implementation eliminates the factory pattern while maintaining 
        full API compatibility.
      </Text>
    </>
  );

  return (
    <View className="flex-1 p-6 justify-center items-center gap-4">
      <Text className="text-xl font-bold mb-4">Modal Migration Demo</Text>
      <Text className="text-center text-gray-600 mb-6">
        Compare the v1 (factory-based) and v2 (direct implementation) Modal components.
        They should look and behave identically.
      </Text>

      {/* Control buttons */}
      <View className="gap-3 w-full max-w-xs">
        <Pressable
          onPress={() => setShowV1Modal(true)}
          className="bg-blue-500 p-3 rounded-md"
        >
          <Text className="text-white text-center font-medium">Show v1 Modal (Factory)</Text>
        </Pressable>

        <Pressable
          onPress={() => setShowV2Modal(true)}
          className="bg-green-500 p-3 rounded-md"
        >
          <Text className="text-white text-center font-medium">Show v2 Modal (Direct)</Text>
        </Pressable>

        <Pressable
          onPress={() => setShowV2SimpleModal(true)}
          className="bg-purple-500 p-3 rounded-md"
        >
          <Text className="text-white text-center font-medium">Show v2 Simple Modal</Text>
        </Pressable>
      </View>

      {/* v1 Modal */}
      <ModalV1 isOpen={showV1Modal} onClose={() => setShowV1Modal(false)} size="md">
        <ModalBackdropV1 />
        <ModalContentV1>
          <ModalHeaderV1>
            <Text className="text-lg font-semibold">v1 Modal (Factory)</Text>
            <ModalCloseButtonV1 onPress={() => setShowV1Modal(false)}>
              <Text>×</Text>
            </ModalCloseButtonV1>
          </ModalHeaderV1>
          <ModalBodyV1>
            {modalContent}
          </ModalBodyV1>
          <ModalFooterV1>
            <Pressable
              onPress={() => setShowV1Modal(false)}
              className="bg-gray-200 px-4 py-2 rounded"
            >
              <Text>Cancel</Text>
            </Pressable>
            <Pressable
              onPress={() => setShowV1Modal(false)}
              className="bg-blue-500 px-4 py-2 rounded ml-2"
            >
              <Text className="text-white">Confirm</Text>
            </Pressable>
          </ModalFooterV1>
        </ModalContentV1>
      </ModalV1>

      {/* v2 Modal */}
      <ModalV2 size="md">
        {showV2Modal && (
          <>
            <ModalBackdropV2 onPress={() => setShowV2Modal(false)} />
            <ModalContentV2>
              <ModalHeaderV2>
                <Text className="text-lg font-semibold">v2 Modal (Direct)</Text>
                <ModalCloseButtonV2 onPress={() => setShowV2Modal(false)}>
                  <Text>×</Text>
                </ModalCloseButtonV2>
              </ModalHeaderV2>
              <ModalBodyV2>
                {modalContent}
              </ModalBodyV2>
              <ModalFooterV2>
                <Pressable
                  onPress={() => setShowV2Modal(false)}
                  className="bg-gray-200 px-4 py-2 rounded"
                >
                  <Text>Cancel</Text>
                </Pressable>
                <Pressable
                  onPress={() => setShowV2Modal(false)}
                  className="bg-green-500 px-4 py-2 rounded ml-2"
                >
                  <Text className="text-white">Confirm</Text>
                </Pressable>
              </ModalFooterV2>
            </ModalContentV2>
          </>
        )}
      </ModalV2>

      {/* v2 Simple Modal */}
      <ModalV2Simple size="md">
        {showV2SimpleModal && (
          <>
            <ModalBackdropV2Simple onPress={() => setShowV2SimpleModal(false)} />
            <ModalContentV2Simple>
              <ModalHeaderV2Simple>
                <Text className="text-lg font-semibold">v2 Simple Modal</Text>
                <ModalCloseButtonV2Simple onPress={() => setShowV2SimpleModal(false)}>
                  <Text>×</Text>
                </ModalCloseButtonV2Simple>
              </ModalHeaderV2Simple>
              <ModalBodyV2Simple>
                {modalContent}
              </ModalBodyV2Simple>
              <ModalFooterV2Simple>
                <Pressable
                  onPress={() => setShowV2SimpleModal(false)}
                  className="bg-gray-200 px-4 py-2 rounded"
                >
                  <Text>Cancel</Text>
                </Pressable>
                <Pressable
                  onPress={() => setShowV2SimpleModal(false)}
                  className="bg-purple-500 px-4 py-2 rounded ml-2"
                >
                  <Text className="text-white">Confirm</Text>
                </Pressable>
              </ModalFooterV2Simple>
            </ModalContentV2Simple>
          </>
        )}
      </ModalV2Simple>

      <View className="mt-6 p-4 bg-gray-100 rounded-md">
        <Text className="text-sm">
          <Text className="font-semibold">Test Results:</Text> {'\n'}
          • Visual appearance should be identical{'\n'}
          • All props should work the same way{'\n'}
          • Animations and interactions preserved{'\n'}
          • v2 Simple should have same functionality with simpler code
        </Text>
      </View>
    </View>
  );
}