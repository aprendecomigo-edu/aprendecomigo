import { X, AlertCircle, CheckCircle, Upload } from '@/components/ui/icons';
import React from 'react';
import { Platform } from 'react-native';

import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Progress, ProgressFilledTrack } from '@/components/ui/progress';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

export interface FileUploadProgressProps {
  fileName: string;
  progress: number; // 0-100
  status: 'uploading' | 'success' | 'error' | 'idle';
  error?: string;
  fileSize?: number;
  onCancel?: () => void;
  onRetry?: () => void;
  onRemove?: () => void;
  className?: string;
}

const FileUploadProgress: React.FC<FileUploadProgressProps> = ({
  fileName,
  progress,
  status,
  error,
  fileSize,
  onCancel,
  onRetry,
  onRemove,
  className,
}) => {
  const formatFileSize = (bytes?: number): string => {
    if (!bytes) return '';

    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    const size = (bytes / Math.pow(1024, i)).toFixed(1);

    return `${size} ${sizes[i]}`;
  };

  const getStatusIcon = () => {
    switch (status) {
      case 'uploading':
        return <Icon as={Upload} size="sm" className="text-blue-600" />;
      case 'success':
        return <Icon as={CheckCircle} size="sm" className="text-green-600" />;
      case 'error':
        return <Icon as={AlertCircle} size="sm" className="text-red-600" />;
      default:
        return <Icon as={Upload} size="sm" className="text-gray-600" />;
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'uploading':
        return 'blue';
      case 'success':
        return 'green';
      case 'error':
        return 'red';
      default:
        return 'gray';
    }
  };

  const getProgressValue = () => {
    if (status === 'success') return 100;
    if (status === 'error') return 0;
    return Math.max(0, Math.min(100, progress));
  };

  return (
    <Box className={`bg-white border rounded-lg p-4 ${className || ''}`}>
      <VStack space="sm">
        {/* File info header */}
        <HStack className="justify-between items-start">
          <HStack className="items-center flex-1" space="sm">
            {getStatusIcon()}
            <VStack className="flex-1">
              <Text
                className="font-medium text-gray-900 text-sm"
                numberOfLines={1}
                ellipsizeMode="middle"
              >
                {fileName}
              </Text>
              {fileSize && (
                <Text className="text-xs text-gray-500">{formatFileSize(fileSize)}</Text>
              )}
            </VStack>
          </HStack>

          {/* Action buttons */}
          <HStack space="xs">
            {status === 'uploading' && onCancel && (
              <Button variant="outline" size="xs" onPress={onCancel} className="border-gray-300">
                <Icon as={X} size="xs" className="text-gray-600" />
              </Button>
            )}

            {(status === 'success' || status === 'error') && onRemove && (
              <Button variant="outline" size="xs" onPress={onRemove} className="border-gray-300">
                <Icon as={X} size="xs" className="text-gray-600" />
              </Button>
            )}
          </HStack>
        </HStack>

        {/* Progress bar */}
        {(status === 'uploading' || status === 'success') && (
          <VStack space="xs">
            <Progress value={getProgressValue()} className="w-full h-2 bg-gray-200">
              <ProgressFilledTrack
                className={`bg-${getStatusColor()}-600 transition-all duration-300`}
              />
            </Progress>

            <HStack className="justify-between items-center">
              <Text className="text-xs text-gray-600">
                {status === 'uploading'
                  ? `${Math.round(progress)}% uploaded`
                  : status === 'success'
                    ? 'Upload complete'
                    : ''}
              </Text>

              {status === 'uploading' && (
                <Text className="text-xs text-gray-500">
                  {progress > 0 ? 'Uploading...' : 'Preparing...'}
                </Text>
              )}
            </HStack>
          </VStack>
        )}

        {/* Error message */}
        {status === 'error' && (
          <VStack space="sm" className="bg-red-50 p-3 rounded border border-red-200">
            <Text className="text-red-800 text-sm font-medium">Upload failed</Text>
            {error && <Text className="text-red-600 text-sm">{error}</Text>}
            {onRetry && (
              <Button
                variant="outline"
                size="sm"
                onPress={onRetry}
                className="mt-2 border-red-300 self-start"
              >
                <ButtonText className="text-red-700">Try Again</ButtonText>
              </Button>
            )}
          </VStack>
        )}

        {/* Success message */}
        {status === 'success' && (
          <Box className="bg-green-50 p-3 rounded border border-green-200">
            <Text className="text-green-800 text-sm font-medium">File uploaded successfully</Text>
          </Box>
        )}
      </VStack>
    </Box>
  );
};

export default FileUploadProgress;
