/**
 * Image Upload Component - Web Implementation
 *
 * Web-specific implementation using HTML file input with drag & drop support.
 * Uses FileReader API for browser-based file handling.
 */

import * as ImagePicker from 'expo-image-picker';
import React, { useState, useRef } from 'react';

import {
  ImageUploadComponentProps,
  validateImage,
  UploadProgressView,
  CurrentImageView,
  UploadAreaView,
} from './image-upload-common';

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
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = async (file: File) => {
    try {
      setIsSelecting(true);

      // Create ImagePicker.ImagePickerAsset from File
      const imageAsset: ImagePicker.ImagePickerAsset = {
        uri: URL.createObjectURL(file),
        width: 0, // Will be set after image loads
        height: 0, // Will be set after image loads
        type: 'image',
        fileName: file.name,
        fileSize: file.size,
        mimeType: file.type,
        base64: undefined,
        exif: undefined,
      };

      // Load image to get dimensions
      const img = new window.Image();
      img.onload = () => {
        imageAsset.width = img.width;
        imageAsset.height = img.height;

        const validationError = validateImage(imageAsset, maxSizeInMB);
        if (validationError) {
          alert(validationError);
          URL.revokeObjectURL(imageAsset.uri);
          return;
        }

        onImageSelected(imageAsset);
      };
      img.onerror = () => {
        alert('Failed to load selected image. Please try again.');
        URL.revokeObjectURL(imageAsset.uri);
      };
      img.src = imageAsset.uri;
    } catch (error) {
      if (__DEV__) {
        console.error('Error processing selected file:', error); // TODO: Review for sensitive data
      }
      alert('Failed to process selected image. Please try again.');
    } finally {
      setIsSelecting(false);
    }
  };

  const selectImageFromLibrary = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const handleFileInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      handleFileSelect(file);
    }
    // Reset input value to allow selecting the same file again
    event.target.value = '';
  };

  const handleRemoveImage = () => {
    if (window.confirm('Are you sure you want to remove this profile photo?')) {
      onImageRemoved?.();
    }
  };

  const showImagePickerOptions = () => {
    selectImageFromLibrary();
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
    <>
      <UploadAreaView
        onImagePickerPress={showImagePickerOptions}
        disabled={disabled}
        isSelecting={isSelecting}
        maxSizeInMB={maxSizeInMB}
        className={className}
      />

      {/* Hidden file input for web */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        onChange={handleFileInputChange}
        style={{ display: 'none' }}
        disabled={disabled || isSelecting}
      />
    </>
  );
};

export default ImageUploadComponent;
