import * as DocumentPicker from 'expo-document-picker';
import * as ImagePicker from 'expo-image-picker';

import apiClient from '@/api/apiClient';

export interface FileUploadProgress {
  loaded: number;
  total: number;
  percentage: number;
}

export interface FileUploadResult {
  success: boolean;
  url?: string;
  error?: string;
  fileName?: string;
}

export interface FileUploadOptions {
  onProgress?: (progress: FileUploadProgress) => void;
  onError?: (error: string) => void;
  onSuccess?: (result: FileUploadResult) => void;
  endpoint?: string;
  fieldName?: string;
  additionalData?: { [key: string]: any };
}

export class FileUploadService {
  private static createFormData(
    file: ImagePicker.ImagePickerAsset | DocumentPicker.DocumentPickerAsset,
    fieldName: string = 'file',
    additionalData?: { [key: string]: any },
  ): FormData {
    const formData = new FormData();

    // Handle file data based on platform
    const fileData: any = {
      uri: file.uri,
      name: file.name || 'upload',
      type: file.mimeType || 'application/octet-stream',
    };

    // Add the file to form data
    formData.append(fieldName, fileData as any);

    // Add any additional data
    if (additionalData) {
      Object.keys(additionalData).forEach(key => {
        const value = additionalData[key];
        if (value !== null && value !== undefined) {
          formData.append(key, typeof value === 'object' ? JSON.stringify(value) : String(value));
        }
      });
    }

    return formData;
  }

  private static createXMLHttpRequest(
    url: string,
    formData: FormData,
    options: FileUploadOptions,
  ): Promise<FileUploadResult> {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();

      // Configure progress tracking
      if (options.onProgress) {
        xhr.upload.addEventListener('progress', event => {
          if (event.lengthComputable) {
            const progress: FileUploadProgress = {
              loaded: event.loaded,
              total: event.total,
              percentage: Math.round((event.loaded / event.total) * 100),
            };
            options.onProgress!(progress);
          }
        });
      }

      // Configure completion handlers
      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const response = JSON.parse(xhr.responseText);
            const result: FileUploadResult = {
              success: true,
              url: response.url || response.file_url,
              fileName: response.filename || response.name,
            };

            if (options.onSuccess) {
              options.onSuccess(result);
            }
            resolve(result);
          } catch (parseError) {
            const errorMessage = 'Failed to parse server response';
            if (options.onError) {
              options.onError(errorMessage);
            }
            resolve({
              success: false,
              error: errorMessage,
            });
          }
        } else {
          const errorMessage = `Upload failed with status ${xhr.status}`;
          if (options.onError) {
            options.onError(errorMessage);
          }
          resolve({
            success: false,
            error: errorMessage,
          });
        }
      });

      xhr.addEventListener('error', () => {
        const errorMessage = 'Network error during upload';
        if (options.onError) {
          options.onError(errorMessage);
        }
        resolve({
          success: false,
          error: errorMessage,
        });
      });

      xhr.addEventListener('abort', () => {
        const errorMessage = 'Upload was cancelled';
        if (options.onError) {
          options.onError(errorMessage);
        }
        resolve({
          success: false,
          error: errorMessage,
        });
      });

      // Get auth token from apiClient
      const token = apiClient.defaults.headers.common['Authorization'];

      // Open and send request
      xhr.open('POST', url);

      // Set headers
      if (token) {
        xhr.setRequestHeader('Authorization', token);
      }

      // Note: Don't set Content-Type header for FormData - browser will set it with boundary

      xhr.send(formData);
    });
  }

  /**
   * Upload profile photo
   */
  static async uploadProfilePhoto(
    image: ImagePicker.ImagePickerAsset,
    options: FileUploadOptions = {},
  ): Promise<FileUploadResult> {
    try {
      const endpoint = options.endpoint || '/accounts/teacher-profile/upload-photo/';
      const fieldName = options.fieldName || 'profile_photo';

      const formData = this.createFormData(image, fieldName, options.additionalData);

      // Use the base URL from apiClient
      const baseURL = apiClient.defaults.baseURL || '';
      const fullUrl = `${baseURL}${endpoint}`;

      return await this.createXMLHttpRequest(fullUrl, formData, options);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown upload error';

      if (options.onError) {
        options.onError(errorMessage);
      }

      return {
        success: false,
        error: errorMessage,
      };
    }
  }

  /**
   * Upload credential document
   */
  static async uploadCredentialDocument(
    document: DocumentPicker.DocumentPickerAsset,
    options: FileUploadOptions = {},
  ): Promise<FileUploadResult> {
    try {
      const endpoint = options.endpoint || '/accounts/teacher-profile/upload-credential/';
      const fieldName = options.fieldName || 'credential_file';

      const formData = this.createFormData(document, fieldName, options.additionalData);

      // Use the base URL from apiClient
      const baseURL = apiClient.defaults.baseURL || '';
      const fullUrl = `${baseURL}${endpoint}`;

      return await this.createXMLHttpRequest(fullUrl, formData, options);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown upload error';

      if (options.onError) {
        options.onError(errorMessage);
      }

      return {
        success: false,
        error: errorMessage,
      };
    }
  }

  /**
   * Generic file upload method
   */
  static async uploadFile(
    file: ImagePicker.ImagePickerAsset | DocumentPicker.DocumentPickerAsset,
    endpoint: string,
    options: FileUploadOptions = {},
  ): Promise<FileUploadResult> {
    try {
      const fieldName = options.fieldName || 'file';

      const formData = this.createFormData(file, fieldName, options.additionalData);

      // Use the base URL from apiClient
      const baseURL = apiClient.defaults.baseURL || '';
      const fullUrl = `${baseURL}${endpoint}`;

      return await this.createXMLHttpRequest(fullUrl, formData, options);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown upload error';

      if (options.onError) {
        options.onError(errorMessage);
      }

      return {
        success: false,
        error: errorMessage,
      };
    }
  }

  /**
   * Validate file size and type before upload
   */
  static validateFile(
    file: ImagePicker.ImagePickerAsset | DocumentPicker.DocumentPickerAsset,
    options: {
      maxSizeInMB?: number;
      allowedTypes?: string[];
      isImage?: boolean;
    } = {},
  ): { isValid: boolean; error?: string } {
    const { maxSizeInMB = 10, allowedTypes = [], isImage = false } = options;

    // Check file size
    if (file.size && file.size > maxSizeInMB * 1024 * 1024) {
      return {
        isValid: false,
        error: `File must be smaller than ${maxSizeInMB}MB. Current size: ${(
          file.size /
          (1024 * 1024)
        ).toFixed(2)}MB`,
      };
    }

    // Check file type
    if (allowedTypes.length > 0 && file.mimeType && !allowedTypes.includes(file.mimeType)) {
      return {
        isValid: false,
        error: `Invalid file type. Allowed types: ${allowedTypes.join(', ')}`,
      };
    }

    // Additional image-specific validations
    if (isImage && 'width' in file && 'height' in file) {
      if (file.width && file.height) {
        if (file.width < 50 || file.height < 50) {
          return {
            isValid: false,
            error: 'Image is too small (minimum 50x50 pixels)',
          };
        }

        if (file.width > 4000 || file.height > 4000) {
          return {
            isValid: false,
            error: 'Image is too large (maximum 4000x4000 pixels)',
          };
        }
      }
    }

    return { isValid: true };
  }

  /**
   * Get allowed MIME types for images
   */
  static getAllowedImageTypes(): string[] {
    return ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
  }

  /**
   * Get allowed MIME types for documents
   */
  static getAllowedDocumentTypes(): string[] {
    return [
      'application/pdf',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'application/vnd.ms-excel',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'application/vnd.ms-powerpoint',
      'application/vnd.openxmlformats-officedocument.presentationml.presentation',
      'text/plain',
    ];
  }
}

export default FileUploadService;
