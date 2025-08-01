/**
 * Receipt Preview Modal Component
 * 
 * Displays a receipt preview in a modal with download functionality
 * and proper loading/error states.
 */

import React, { useState, useEffect } from 'react';
import { Platform } from 'react-native';
import { Download, X, AlertTriangle, FileText } from 'lucide-react-native';

import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { 
  Modal, 
  ModalBackdrop, 
  ModalBody, 
  ModalCloseButton, 
  ModalContent, 
  ModalFooter, 
  ModalHeader 
} from '@/components/ui/modal';
import { Heading } from '@/components/ui/heading';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { useReceipts } from '@/hooks/useReceipts';

interface ReceiptPreviewModalProps {
  isOpen: boolean;
  receiptId: string;
  receiptNumber: string;
  onClose: () => void;
}

/**
 * Receipt Preview Modal Component
 */
export function ReceiptPreviewModal({
  isOpen,
  receiptId,
  receiptNumber,
  onClose,
}: ReceiptPreviewModalProps) {
  const { downloadReceipt, getPreviewUrl, downloading } = useReceipts();
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load preview URL when modal opens
  useEffect(() => {
    if (isOpen && receiptId) {
      loadPreview();
    } else {
      // Reset state when modal closes
      setPreviewUrl(null);
      setError(null);
    }
  }, [isOpen, receiptId]);

  const loadPreview = async () => {
    setLoading(true);
    setError(null);

    try {
      const url = await getPreviewUrl(receiptId);
      setPreviewUrl(url);
    } catch (error: any) {
      console.error('Error loading receipt preview:', error);
      setError(error.message || 'Failed to load receipt preview');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async () => {
    try {
      await downloadReceipt(receiptId);
      // Optionally close modal after successful download
      // onClose();
    } catch (error: any) {
      console.error('Error downloading receipt:', error);
      // Error is handled by the useReceipts hook
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="full">
      <ModalBackdrop />
      <ModalContent className="max-w-4xl mx-auto h-5/6">
        <ModalHeader className="pb-4">
          <VStack space="xs" className="flex-1">
            <Heading size="lg">Receipt Preview</Heading>
            <Text className="text-sm text-typography-600">
              Receipt #{receiptNumber}
            </Text>
          </VStack>
          <ModalCloseButton />
        </ModalHeader>

        <ModalBody className="flex-1 p-0">
          {loading && (
            <VStack space="md" className="items-center justify-center flex-1 p-8">
              <Spinner size="large" />
              <Text className="text-typography-600">Loading receipt preview...</Text>
            </VStack>
          )}

          {error && (
            <VStack space="md" className="items-center justify-center flex-1 p-8">
              <Icon as={AlertTriangle} size="xl" className="text-error-500" />
              <VStack space="sm" className="items-center">
                <Heading size="sm" className="text-error-900">
                  Preview Not Available
                </Heading>
                <Text className="text-error-700 text-sm text-center">
                  {error}
                </Text>
              </VStack>
              <Button
                action="secondary"
                variant="outline"
                size="sm"
                onPress={loadPreview}
              >
                <ButtonText>Try Again</ButtonText>
              </Button>
            </VStack>
          )}

          {previewUrl && !loading && !error && (
            <VStack className="flex-1 bg-background-100">
              {Platform.OS === 'web' ? (
                <div className="flex-1">
                  <iframe
                    src={previewUrl}
                    className="w-full h-full border-0"
                    title={`Receipt ${receiptNumber} Preview`}
                  />
                </div>
              ) : (
                <VStack space="md" className="items-center justify-center flex-1 p-8">
                  <Icon as={FileText} size="xl" className="text-primary-500" />
                  <VStack space="sm" className="items-center">
                    <Heading size="sm" className="text-typography-900">
                      Receipt Ready
                    </Heading>
                    <Text className="text-typography-700 text-sm text-center">
                      Receipt preview is not available on mobile. Tap download to view the receipt.
                    </Text>
                  </VStack>
                </VStack>
              )}
            </VStack>
          )}
        </ModalBody>

        <ModalFooter className="pt-4">
          <HStack space="md" className="w-full justify-end">
            <Button
              action="secondary"
              variant="outline"
              size="md"
              onPress={onClose}
            >
              <ButtonText>Close</ButtonText>
            </Button>
            
            <Button
              action="primary"
              variant="solid"
              size="md"
              onPress={handleDownload}
              disabled={downloading || loading}
            >
              {downloading ? (
                <>
                  <Spinner size="sm" />
                  <ButtonText className="ml-2">Downloading...</ButtonText>
                </>
              ) : (
                <>
                  <ButtonIcon as={Download} />
                  <ButtonText>Download PDF</ButtonText>
                </>
              )}
            </Button>
          </HStack>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}