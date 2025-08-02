/**
 * Receipt Download Button Component
 *
 * Provides download functionality for receipts with loading states
 * and error handling for both existing and to-be-generated receipts.
 */

import { Download, FileText, RefreshCw, AlertTriangle } from 'lucide-react-native';
import React, { useState } from 'react';

import type { Receipt } from '@/api/receiptApi';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { useReceipts } from '@/hooks/useReceipts';

interface ReceiptDownloadButtonProps {
  transactionId: string;
  existingReceipt?: Receipt;
  planName: string;
  amount: string;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'solid' | 'outline' | 'link';
  onPreview?: (receiptId: string) => void;
  className?: string;
}

/**
 * Receipt Download Button Component
 */
export function ReceiptDownloadButton({
  transactionId,
  existingReceipt,
  planName,
  amount,
  size = 'sm',
  variant = 'outline',
  onPreview,
  className = '',
}: ReceiptDownloadButtonProps) {
  const {
    generateReceipt,
    downloadReceipt,
    generating,
    downloading,
    generationError,
    downloadError,
  } = useReceipts();
  const [localError, setLocalError] = useState<string | null>(null);

  const handleDownload = async () => {
    setLocalError(null);

    try {
      if (existingReceipt) {
        // Download existing receipt
        if (existingReceipt.status === 'generated') {
          await downloadReceipt(existingReceipt.id);
        } else if (existingReceipt.status === 'pending') {
          setLocalError('Receipt is still being generated. Please try again in a moment.');
        } else {
          setLocalError('Receipt generation failed. Please contact support.');
        }
      } else {
        // Generate and download new receipt
        const result = await generateReceipt(transactionId);
        if (result?.success && result.status === 'generated') {
          // Receipt was generated immediately, try to download
          if (result.receipt_id) {
            await downloadReceipt(result.receipt_id);
          }
        } else if (result?.status === 'pending') {
          setLocalError('Receipt generation started. It will be available for download shortly.');
        } else {
          setLocalError(result?.message || 'Failed to generate receipt');
        }
      }
    } catch (error: any) {
      console.error('Error in receipt download:', error);
      setLocalError(error.message || 'Failed to process receipt');
    }
  };

  const handlePreview = () => {
    if (existingReceipt && existingReceipt.status === 'generated' && onPreview) {
      onPreview(existingReceipt.id);
    }
  };

  const isLoading = generating || downloading;
  const hasError = localError || generationError || downloadError;
  const canDownload = existingReceipt?.status === 'generated' || !existingReceipt;
  const isPending = existingReceipt?.status === 'pending';
  const hasFailed = existingReceipt?.status === 'failed';

  if (hasFailed) {
    return (
      <VStack space="xs" className={className}>
        <HStack space="xs" className="items-center">
          <Icon as={AlertTriangle} size="sm" className="text-error-500" />
          <Text className="text-xs text-error-600">Receipt generation failed</Text>
        </HStack>
        <Button
          action="secondary"
          variant="outline"
          size={size}
          onPress={handleDownload}
          disabled={isLoading}
        >
          <ButtonIcon as={RefreshCw} />
          <ButtonText>Retry Generation</ButtonText>
        </Button>
      </VStack>
    );
  }

  if (isPending) {
    return (
      <VStack space="xs" className={className}>
        <HStack space="xs" className="items-center">
          <Spinner size="sm" />
          <Text className="text-xs text-typography-600">Generating receipt...</Text>
        </HStack>
        <Button
          action="secondary"
          variant="outline"
          size={size}
          onPress={handleDownload}
          disabled={true}
        >
          <ButtonIcon as={FileText} />
          <ButtonText>Generating...</ButtonText>
        </Button>
      </VStack>
    );
  }

  return (
    <VStack space="xs" className={className}>
      {hasError && (
        <Text className="text-xs text-error-600">
          {localError || generationError || downloadError}
        </Text>
      )}

      <HStack space="xs">
        {/* Download Button */}
        <Button
          action="primary"
          variant={variant}
          size={size}
          onPress={handleDownload}
          disabled={isLoading || !canDownload}
        >
          {isLoading ? (
            <>
              <Spinner size="sm" />
              <ButtonText className="ml-2">
                {generating ? 'Generating...' : 'Downloading...'}
              </ButtonText>
            </>
          ) : (
            <>
              <ButtonIcon as={Download} />
              <ButtonText>{existingReceipt ? 'Download' : 'Generate & Download'}</ButtonText>
            </>
          )}
        </Button>

        {/* Preview Button (only for existing generated receipts) */}
        {existingReceipt?.status === 'generated' && onPreview && (
          <Button action="secondary" variant="outline" size={size} onPress={handlePreview}>
            <ButtonIcon as={FileText} />
            <ButtonText>Preview</ButtonText>
          </Button>
        )}
      </HStack>

      {/* Receipt Info */}
      {existingReceipt && (
        <VStack space="0" className="mt-1">
          <Text className="text-xs text-typography-500">
            Receipt #{existingReceipt.receipt_number}
          </Text>
          {existingReceipt.generated_at && (
            <Text className="text-xs text-typography-400">
              Generated: {new Date(existingReceipt.generated_at).toLocaleDateString()}
            </Text>
          )}
        </VStack>
      )}
    </VStack>
  );
}
