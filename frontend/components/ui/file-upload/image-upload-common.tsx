/**
 * Image Upload Component - Common Logic and Types
 *
 * Shared business logic, types, and utilities for image upload functionality
 * across web and native platforms.
 */

import { Image } from 'expo-image';
import * as ImagePicker from 'expo-image-picker';
import { Upload, Edit3, Trash2, ImageIcon } from '@/components/ui/icons';
import React from 'react';

import FileUploadProgress from './FileUploadProgress';

import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Pressable } from '@/components/ui/pressable';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

// Shared types and interfaces
export interface ImageUploadComponentProps {
  onImageSelected: (image: ImagePicker.ImagePickerAsset) => void;
  onImageRemoved?: () => void;
  currentImageUri?: string;
  uploadProgress?: number;
  uploadStatus?: 'idle' | 'uploading' | 'success' | 'error';
  uploadError?: string;
  onRetryUpload?: () => void;
  maxSizeInMB?: number;
  quality?: number;
  allowsEditing?: boolean;
  aspect?: [number, number];
  className?: string;
  disabled?: boolean;
}

// Shared validation logic
export const validateImage = (
  image: ImagePicker.ImagePickerAsset,
  maxSizeInMB: number
): string | null => {
  // Check file size
  if (image.fileSize && image.fileSize > maxSizeInMB * 1024 * 1024) {
    return `Image must be smaller than ${maxSizeInMB}MB. Current size: ${(
      image.fileSize /
      (1024 * 1024)
    ).toFixed(2)}MB`;
  }

  // Check dimensions (reasonable limits)
  if (image.width < 50 || image.height < 50) {
    return 'Image is too small (minimum 50x50 pixels)';
  }

  if (image.width > 4000 || image.height > 4000) {
    return 'Image is too large (maximum 4000x4000 pixels)';
  }

  return null;
};

// Shared upload progress view
export function UploadProgressView({
  currentImageUri,
  uploadProgress,
  uploadStatus,
  uploadError,
  onRetryUpload,
  className,
}: {
  currentImageUri: string;
  uploadProgress: number;
  uploadStatus: string;
  uploadError?: string;
  onRetryUpload?: () => void;
  className?: string;
}) {
  return (
    <Box className={className}>
      <VStack space="md">
        <Text className="font-medium text-gray-800">Profile Photo</Text>

        {/* Image preview with progress overlay */}
        <Box className="relative">
          <Box className="w-32 h-32 rounded-full overflow-hidden bg-gray-100 border-2 border-gray-200">
            <Image
              source={{ uri: currentImageUri }}
              style={{ width: '100%', height: '100%' }}
              contentFit="cover"
            />
            {/* Upload overlay */}
            <Box className="absolute inset-0 bg-black/50 flex items-center justify-center">
              <VStack className="items-center" space="xs">
                <Icon as={Upload} size="md" className="text-white" />
                <Text className="text-white text-sm font-medium">
                  {Math.round(uploadProgress)}%
                </Text>
              </VStack>
            </Box>
          </Box>
        </Box>

        <FileUploadProgress
          fileName="Profile Photo"
          progress={uploadProgress}
          status={uploadStatus}
          error={uploadError}
          onRetry={onRetryUpload}
        />
      </VStack>
    </Box>
  );
}

// Shared current image view with edit options
export function CurrentImageView({
  currentImageUri,
  uploadStatus,
  uploadError,
  onRetryUpload,
  onImagePickerPress,
  onImageRemoved,
  disabled,
  isSelecting,
  className,
}: {
  currentImageUri: string;
  uploadStatus: string;
  uploadError?: string;
  onRetryUpload?: () => void;
  onImagePickerPress: () => void;
  onImageRemoved?: () => void;
  disabled: boolean;
  isSelecting: boolean;
  className?: string;
}) {
  return (
    <Box className={className}>
      <VStack space="md">
        <Text className="font-medium text-gray-800">Profile Photo</Text>

        <HStack className="items-center" space="md">
          {/* Image preview */}
          <Box className="w-32 h-32 rounded-full overflow-hidden bg-gray-100 border-2 border-gray-200">
            <Image
              source={{ uri: currentImageUri }}
              style={{ width: '100%', height: '100%' }}
              contentFit="cover"
            />
          </Box>

          {/* Edit actions */}
          <VStack space="sm">
            <Button
              variant="outline"
              size="sm"
              onPress={onImagePickerPress}
              disabled={disabled || isSelecting}
            >
              <Icon as={Edit3} size="sm" className="mr-2" />
              <ButtonText>Change Photo</ButtonText>
            </Button>

            {onImageRemoved && (
              <Button
                variant="outline"
                size="sm"
                onPress={onImageRemoved}
                disabled={disabled}
                className="border-red-300"
              >
                <Icon as={Trash2} size="sm" className="mr-2 text-red-600" />
                <ButtonText className="text-red-600">Remove</ButtonText>
              </Button>
            )}
          </VStack>
        </HStack>

        {/* Upload status messages */}
        {uploadStatus === 'error' && uploadError && (
          <Box className="bg-red-50 p-3 rounded border border-red-200">
            <Text className="text-red-800 text-sm">Upload failed: {uploadError}</Text>
            {onRetryUpload && (
              <Button
                variant="outline"
                size="sm"
                onPress={onRetryUpload}
                className="mt-2 border-red-300 self-start"
              >
                <ButtonText className="text-red-700">Try Again</ButtonText>
              </Button>
            )}
          </Box>
        )}

        {uploadStatus === 'success' && (
          <Box className="bg-green-50 p-3 rounded border border-green-200">
            <Text className="text-green-800 text-sm">Profile photo uploaded successfully!</Text>
          </Box>
        )}
      </VStack>
    </Box>
  );
}

// Shared upload area for new image
export function UploadAreaView({
  onImagePickerPress,
  disabled,
  isSelecting,
  maxSizeInMB,
  className,
}: {
  onImagePickerPress: () => void;
  disabled: boolean;
  isSelecting: boolean;
  maxSizeInMB: number;
  className?: string;
}) {
  return (
    <Box className={className}>
      <VStack space="md">
        <Text className="font-medium text-gray-800">
          Profile Photo <Text className="text-gray-500 font-normal">(optional)</Text>
        </Text>

        <Pressable
          onPress={onImagePickerPress}
          disabled={disabled || isSelecting}
          className={`
            border-2 border-dashed border-gray-300 rounded-lg p-6 items-center justify-center
            ${disabled ? 'opacity-50' : 'hover:border-gray-400 active:border-blue-500'}
          `}
        >
          <VStack className="items-center" space="md">
            {/* Upload icon */}
            <Box className="w-16 h-16 rounded-full bg-gray-100 items-center justify-center">
              <Icon as={ImageIcon} size="lg" className="text-gray-400" />
            </Box>

            {/* Upload text */}
            <VStack className="items-center" space="xs">
              <Text className="font-medium text-gray-700">
                {isSelecting ? 'Selecting...' : 'Add Profile Photo'}
              </Text>
              <Text className="text-sm text-gray-500 text-center max-w-64">
                Upload a professional photo to help students and parents get to know you
              </Text>
            </VStack>

            {/* Format info */}
            <Box className="bg-gray-50 px-3 py-2 rounded border">
              <Text className="text-xs text-gray-600 text-center">
                JPEG, PNG, GIF or WebP • Max {maxSizeInMB}MB • Min 50x50 pixels
              </Text>
            </Box>
          </VStack>
        </Pressable>
      </VStack>
    </Box>
  );
}
