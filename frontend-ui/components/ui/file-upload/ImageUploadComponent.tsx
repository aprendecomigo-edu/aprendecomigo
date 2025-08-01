import React, { useState } from 'react';
import { Platform, Alert } from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { Image } from 'expo-image';
import { Box } from '@/components/ui/box';
import { VStack } from '@/components/ui/vstack';
import { HStack } from '@/components/ui/hstack';
import { Text } from '@/components/ui/text';
import { Button, ButtonText } from '@/components/ui/button';
import { Pressable } from '@/components/ui/pressable';
import { Icon } from '@/components/ui/icon';
import { Camera, Image as ImageIcon, Edit3, Trash2, Upload } from 'lucide-react-native';
import FileUploadProgress from './FileUploadProgress';

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

const ImageUploadComponent: React.FC<ImageUploadComponentProps> = ({
  onImageSelected,
  onImageRemoved,
  currentImageUri,
  uploadProgress = 0,
  uploadStatus = 'idle',
  uploadError,
  onRetryUpload,
  maxSizeInMB = 5,
  quality = 0.8,
  allowsEditing = true,
  aspect = [1, 1],
  className,
  disabled = false,
}) => {
  const [isSelecting, setIsSelecting] = useState(false);

  const requestPermissions = async (): Promise<boolean> => {
    if (Platform.OS !== 'web') {
      const { status: mediaLibraryStatus } = await ImagePicker.requestMediaLibraryPermissionsAsync();
      const { status: cameraStatus } = await ImagePicker.requestCameraPermissionsAsync();
      
      if (mediaLibraryStatus !== 'granted' || cameraStatus !== 'granted') {
        Alert.alert(
          'Permissions Required',
          'We need camera and photo library permissions to upload profile photos.',
          [{ text: 'OK', style: 'default' }]
        );
        return false;
      }
    }
    return true;
  };

  const validateImage = (image: ImagePicker.ImagePickerAsset): string | null => {
    // Check file size
    if (image.fileSize && image.fileSize > maxSizeInMB * 1024 * 1024) {
      return `Image must be smaller than ${maxSizeInMB}MB. Current size: ${(image.fileSize / (1024 * 1024)).toFixed(2)}MB`;
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

  const selectImageFromLibrary = async () => {
    try {
      setIsSelecting(true);
      
      const hasPermissions = await requestPermissions();
      if (!hasPermissions) {
        return;
      }

      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing,
        aspect,
        quality,
        allowsMultipleSelection: false,
      });

      if (!result.canceled && result.assets && result.assets.length > 0) {
        const selectedImage = result.assets[0];
        
        const validationError = validateImage(selectedImage);
        if (validationError) {
          Alert.alert('Invalid Image', validationError);
          return;
        }

        onImageSelected(selectedImage);
      }
    } catch (error) {
      console.error('Error selecting image from library:', error);
      Alert.alert('Error', 'Failed to select image from library. Please try again.');
    } finally {
      setIsSelecting(false);
    }
  };

  const takePhoto = async () => {
    try {
      setIsSelecting(true);
      
      const hasPermissions = await requestPermissions();
      if (!hasPermissions) {
        return;
      }

      const result = await ImagePicker.launchCameraAsync({
        allowsEditing,
        aspect,
        quality,
      });

      if (!result.canceled && result.assets && result.assets.length > 0) {
        const capturedImage = result.assets[0];
        
        const validationError = validateImage(capturedImage);
        if (validationError) {
          Alert.alert('Invalid Image', validationError);
          return;
        }

        onImageSelected(capturedImage);
      }
    } catch (error) {
      console.error('Error taking photo:', error);
      Alert.alert('Error', 'Failed to take photo. Please try again.');
    } finally {
      setIsSelecting(false);
    }
  };

  const showImagePickerOptions = () => {
    if (Platform.OS === 'web') {
      // On web, directly open image library
      selectImageFromLibrary();
      return;
    }

    Alert.alert(
      'Select Image',
      'Choose how you would like to select your profile photo:',
      [
        { text: 'Camera', onPress: takePhoto },
        { text: 'Photo Library', onPress: selectImageFromLibrary },
        { text: 'Cancel', style: 'cancel' },
      ]
    );
  };

  const handleRemoveImage = () => {
    Alert.alert(
      'Remove Image',
      'Are you sure you want to remove this profile photo?',
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Remove', 
          style: 'destructive',
          onPress: onImageRemoved 
        },
      ]
    );
  };

  // Show upload progress if uploading
  if (uploadStatus === 'uploading' && currentImageUri) {
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

  // Show current image with edit options
  if (currentImageUri && uploadStatus !== 'uploading') {
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
                onPress={showImagePickerOptions}
                disabled={disabled || isSelecting}
              >
                <Icon as={Edit3} size="sm" className="mr-2" />
                <ButtonText>Change Photo</ButtonText>
              </Button>
              
              {onImageRemoved && (
                <Button
                  variant="outline"
                  size="sm"
                  onPress={handleRemoveImage}
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
              <Text className="text-red-800 text-sm">
                Upload failed: {uploadError}
              </Text>
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
              <Text className="text-green-800 text-sm">
                Profile photo uploaded successfully!
              </Text>
            </Box>
          )}
        </VStack>
      </Box>
    );
  }

  // Show upload area for new image
  return (
    <Box className={className}>
      <VStack space="md">
        <Text className="font-medium text-gray-800">
          Profile Photo <Text className="text-gray-500 font-normal">(optional)</Text>
        </Text>
        
        <Pressable
          onPress={showImagePickerOptions}
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
};

export default ImageUploadComponent;