/**
 * Image Upload Component - Fallback Implementation
 *
 * Main entry point with Platform.OS fallback.
 * Platform-specific files should override this implementation.
 */

import * as ImagePicker from 'expo-image-picker';
import React, { useState } from 'react';
import { Platform, Alert } from 'react-native';

import {
  ImageUploadComponentProps,
  validateImage,
  UploadProgressView,
  CurrentImageView,
  UploadAreaView,
} from './image-upload-common';

// Export types for external usage
export type { ImageUploadComponentProps };

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
      const { status: mediaLibraryStatus } =
        await ImagePicker.requestMediaLibraryPermissionsAsync();
      const { status: cameraStatus } = await ImagePicker.requestCameraPermissionsAsync();

      if (mediaLibraryStatus !== 'granted' || cameraStatus !== 'granted') {
        Alert.alert(
          'Permissions Required',
          'We need camera and photo library permissions to upload profile photos.',
          [{ text: 'OK', style: 'default' }],
        );
        return false;
      }
    }
    return true;
  };

  const selectImageFromLibrary = async () => {
    try {
      setIsSelecting(true);

      const hasPermissions = await requestPermissions();
      if (!hasPermissions) {
        return;
      }

      if (Platform.OS === 'web') {
        // Web implementation - fallback for when platform-specific files don't load
        alert('Please use the web-specific implementation for file selection.');
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

        const validationError = validateImage(selectedImage, maxSizeInMB);
        if (validationError) {
          Alert.alert('Invalid Image', validationError);
          return;
        }

        onImageSelected(selectedImage);
      }
    } catch (error) {
      if (__DEV__) {
        console.error('Error selecting image from library:', error); // TODO: Review for sensitive data
      }
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

        const validationError = validateImage(capturedImage, maxSizeInMB);
        if (validationError) {
          Alert.alert('Invalid Image', validationError);
          return;
        }

        onImageSelected(capturedImage);
      }
    } catch (error) {
      if (__DEV__) {
        console.error('Error taking photo:', error); // TODO: Review for sensitive data
      }
      Alert.alert('Error', 'Failed to take photo. Please try again.');
    } finally {
      setIsSelecting(false);
    }
  };

  const showImagePickerOptions = () => {
    if (Platform.OS === 'web') {
      selectImageFromLibrary();
      return;
    }

    Alert.alert('Select Image', 'Choose how you would like to select your profile photo:', [
      { text: 'Camera', onPress: takePhoto },
      { text: 'Photo Library', onPress: selectImageFromLibrary },
      { text: 'Cancel', style: 'cancel' },
    ]);
  };

  const handleRemoveImage = () => {
    if (Platform.OS === 'web') {
      if (window.confirm('Are you sure you want to remove this profile photo?')) {
        onImageRemoved?.();
      }
    } else {
      Alert.alert('Remove Image', 'Are you sure you want to remove this profile photo?', [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Remove',
          style: 'destructive',
          onPress: onImageRemoved,
        },
      ]);
    }
  };

  // Show upload progress if uploading
  if (uploadStatus === 'uploading' && currentImageUri) {
    return (
      <UploadProgressView
        currentImageUri={currentImageUri}
        uploadProgress={uploadProgress}
        uploadStatus={uploadStatus}
        uploadError={uploadError}
        onRetryUpload={onRetryUpload}
        className={className}
      />
    );
  }

  // Show current image with edit options
  if (currentImageUri && uploadStatus !== 'uploading') {
    return (
      <CurrentImageView
        currentImageUri={currentImageUri}
        uploadStatus={uploadStatus}
        uploadError={uploadError}
        onRetryUpload={onRetryUpload}
        onImagePickerPress={showImagePickerOptions}
        onImageRemoved={handleRemoveImage}
        disabled={disabled}
        isSelecting={isSelecting}
        className={className}
      />
    );
  }

  // Show upload area for new image
  return (
    <UploadAreaView
      onImagePickerPress={showImagePickerOptions}
      disabled={disabled}
      isSelecting={isSelecting}
      maxSizeInMB={maxSizeInMB}
      className={className}
    />
  );
};

export default ImageUploadComponent;
