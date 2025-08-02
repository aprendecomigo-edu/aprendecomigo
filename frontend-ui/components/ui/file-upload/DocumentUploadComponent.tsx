import * as DocumentPicker from 'expo-document-picker';
import { Upload, FileText, Trash2, AlertCircle, CheckCircle } from 'lucide-react-native';
import React, { useState } from 'react';
import { Platform, Alert } from 'react-native';

import FileUploadProgress from './FileUploadProgress';

import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Pressable } from '@/components/ui/pressable';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

export interface DocumentUploadComponentProps {
  onDocumentSelected: (document: DocumentPicker.DocumentPickerAsset) => void;
  onDocumentRemoved?: () => void;
  currentDocument?: {
    name: string;
    uri: string;
    size?: number;
  };
  uploadProgress?: number;
  uploadStatus?: 'idle' | 'uploading' | 'success' | 'error';
  uploadError?: string;
  onRetryUpload?: () => void;
  acceptedTypes?: string[];
  maxSizeInMB?: number;
  label?: string;
  description?: string;
  required?: boolean;
  className?: string;
  disabled?: boolean;
}

const DocumentUploadComponent: React.FC<DocumentUploadComponentProps> = ({
  onDocumentSelected,
  onDocumentRemoved,
  currentDocument,
  uploadProgress = 0,
  uploadStatus = 'idle',
  uploadError,
  onRetryUpload,
  acceptedTypes = [
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  ],
  maxSizeInMB = 10,
  label = 'Document',
  description = 'Upload your credential document',
  required = false,
  className,
  disabled = false,
}) => {
  const [isSelecting, setIsSelecting] = useState(false);

  const getFileExtensionsFromMimeTypes = (mimeTypes: string[]): string[] => {
    const mimeToExt: { [key: string]: string[] } = {
      'application/pdf': ['pdf'],
      'application/msword': ['doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['docx'],
      'application/vnd.ms-excel': ['xls'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['xlsx'],
      'application/vnd.ms-powerpoint': ['ppt'],
      'application/vnd.openxmlformats-officedocument.presentationml.presentation': ['pptx'],
      'text/plain': ['txt'],
      'image/jpeg': ['jpg', 'jpeg'],
      'image/png': ['png'],
    };

    const extensions: string[] = [];
    mimeTypes.forEach(mimeType => {
      if (mimeToExt[mimeType]) {
        extensions.push(...mimeToExt[mimeType]);
      }
    });

    return extensions;
  };

  const validateDocument = (document: DocumentPicker.DocumentPickerAsset): string | null => {
    // Check file size
    if (document.size && document.size > maxSizeInMB * 1024 * 1024) {
      return `Document must be smaller than ${maxSizeInMB}MB. Current size: ${(
        document.size /
        (1024 * 1024)
      ).toFixed(2)}MB`;
    }

    // Check file type if specified
    if (
      acceptedTypes.length > 0 &&
      document.mimeType &&
      !acceptedTypes.includes(document.mimeType)
    ) {
      const allowedExtensions = getFileExtensionsFromMimeTypes(acceptedTypes);
      return `Invalid file type. Allowed formats: ${allowedExtensions
        .map(ext => ext.toUpperCase())
        .join(', ')}`;
    }

    return null;
  };

  const selectDocument = async () => {
    try {
      setIsSelecting(true);

      const result = await DocumentPicker.getDocumentAsync({
        type: acceptedTypes.length > 0 ? acceptedTypes : '*/*',
        copyToCacheDirectory: true,
        multiple: false,
      });

      if (!result.canceled && result.assets && result.assets.length > 0) {
        const selectedDocument = result.assets[0];

        const validationError = validateDocument(selectedDocument);
        if (validationError) {
          Alert.alert('Invalid Document', validationError);
          return;
        }

        onDocumentSelected(selectedDocument);
      }
    } catch (error) {
      console.error('Error selecting document:', error);
      Alert.alert('Error', 'Failed to select document. Please try again.');
    } finally {
      setIsSelecting(false);
    }
  };

  const handleRemoveDocument = () => {
    Alert.alert('Remove Document', `Are you sure you want to remove this ${label.toLowerCase()}?`, [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Remove',
        style: 'destructive',
        onPress: onDocumentRemoved,
      },
    ]);
  };

  const formatFileSize = (bytes?: number): string => {
    if (!bytes) return '';

    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    const size = (bytes / Math.pow(1024, i)).toFixed(1);

    return `${size} ${sizes[i]}`;
  };

  const getFileIcon = (fileName?: string) => {
    if (!fileName) return FileText;

    const extension = fileName.split('.').pop()?.toLowerCase();
    switch (extension) {
      case 'pdf':
        return FileText;
      case 'doc':
      case 'docx':
        return FileText;
      case 'xls':
      case 'xlsx':
        return FileText;
      case 'ppt':
      case 'pptx':
        return FileText;
      default:
        return FileText;
    }
  };

  // Show upload progress if uploading
  if (uploadStatus === 'uploading' && currentDocument) {
    return (
      <Box className={className}>
        <VStack space="md">
          <Text className="font-medium text-gray-800">
            {label} {required && <Text className="text-red-500">*</Text>}
          </Text>

          <FileUploadProgress
            fileName={currentDocument.name}
            progress={uploadProgress}
            status={uploadStatus}
            error={uploadError}
            fileSize={currentDocument.size}
            onRetry={onRetryUpload}
          />
        </VStack>
      </Box>
    );
  }

  // Show current document with edit options
  if (currentDocument && uploadStatus !== 'uploading') {
    const FileIcon = getFileIcon(currentDocument.name);

    return (
      <Box className={className}>
        <VStack space="md">
          <Text className="font-medium text-gray-800">
            {label} {required && <Text className="text-red-500">*</Text>}
          </Text>

          <Box className="bg-white border rounded-lg p-4">
            <HStack className="justify-between items-start">
              <HStack className="items-center flex-1" space="sm">
                <Box className="w-10 h-10 bg-blue-50 rounded items-center justify-center">
                  <Icon as={FileIcon} size="md" className="text-blue-600" />
                </Box>

                <VStack className="flex-1">
                  <Text
                    className="font-medium text-gray-900 text-sm"
                    numberOfLines={2}
                    ellipsizeMode="middle"
                  >
                    {currentDocument.name}
                  </Text>
                  {currentDocument.size && (
                    <Text className="text-xs text-gray-500">
                      {formatFileSize(currentDocument.size)}
                    </Text>
                  )}

                  {/* Upload status indicator */}
                  {uploadStatus === 'success' && (
                    <HStack className="items-center mt-1" space="xs">
                      <Icon as={CheckCircle} size="xs" className="text-green-600" />
                      <Text className="text-xs text-green-600">Uploaded</Text>
                    </HStack>
                  )}

                  {uploadStatus === 'error' && (
                    <HStack className="items-center mt-1" space="xs">
                      <Icon as={AlertCircle} size="xs" className="text-red-600" />
                      <Text className="text-xs text-red-600">Upload failed</Text>
                    </HStack>
                  )}
                </VStack>
              </HStack>

              {/* Action buttons */}
              <VStack space="xs">
                <Button
                  variant="outline"
                  size="xs"
                  onPress={selectDocument}
                  disabled={disabled || isSelecting}
                >
                  <ButtonText className="text-xs">Replace</ButtonText>
                </Button>

                {onDocumentRemoved && (
                  <Button
                    variant="outline"
                    size="xs"
                    onPress={handleRemoveDocument}
                    disabled={disabled}
                    className="border-red-300"
                  >
                    <Icon as={Trash2} size="xs" className="text-red-600" />
                  </Button>
                )}
              </VStack>
            </HStack>
          </Box>

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
              <Text className="text-green-800 text-sm">Document uploaded successfully!</Text>
            </Box>
          )}
        </VStack>
      </Box>
    );
  }

  // Show upload area for new document
  const allowedExtensions = getFileExtensionsFromMimeTypes(acceptedTypes);

  return (
    <Box className={className}>
      <VStack space="md">
        <VStack space="xs">
          <Text className="font-medium text-gray-800">
            {label} {required && <Text className="text-red-500">*</Text>}
          </Text>
          {description && <Text className="text-sm text-gray-600">{description}</Text>}
        </VStack>

        <Pressable
          onPress={selectDocument}
          disabled={disabled || isSelecting}
          className={`
            border-2 border-dashed border-gray-300 rounded-lg p-6 items-center justify-center
            ${disabled ? 'opacity-50' : 'hover:border-gray-400 active:border-blue-500'}
          `}
        >
          <VStack className="items-center" space="md">
            {/* Upload icon */}
            <Box className="w-12 h-12 rounded-full bg-gray-100 items-center justify-center">
              <Icon as={Upload} size="md" className="text-gray-400" />
            </Box>

            {/* Upload text */}
            <VStack className="items-center" space="xs">
              <Text className="font-medium text-gray-700">
                {isSelecting ? 'Selecting...' : `Upload ${label}`}
              </Text>
              <Text className="text-sm text-gray-500 text-center max-w-64">
                Choose a file from your device
              </Text>
            </VStack>

            {/* Format info */}
            <Box className="bg-gray-50 px-3 py-2 rounded border">
              <Text className="text-xs text-gray-600 text-center">
                {allowedExtensions.length > 0
                  ? `${allowedExtensions
                      .map(ext => ext.toUpperCase())
                      .join(', ')} • Max ${maxSizeInMB}MB`
                  : `Max ${maxSizeInMB}MB`}
              </Text>
            </Box>
          </VStack>
        </Pressable>
      </VStack>
    </Box>
  );
};

export default DocumentUploadComponent;
