import { useState, useEffect, useCallback } from 'react';
import { Alert } from 'react-native';

import CommunicationApi, { SchoolBranding, UpdateBrandingRequest } from '@/api/communicationApi';

export const useSchoolBranding = (autoFetch = true) => {
  const [branding, setBranding] = useState<SchoolBranding | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  const fetchBranding = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const brandingData = await CommunicationApi.getSchoolBranding();
      setBranding(brandingData);
      setHasUnsavedChanges(false);
    } catch (err: any) {
      const errorMessage =
        err.response?.data?.detail || err.message || 'Failed to fetch school branding';
      setError(errorMessage);
      console.error('Error fetching school branding:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const updateBranding = useCallback(async (data: UpdateBrandingRequest) => {
    try {
      setSaving(true);
      setError(null);

      const updatedBranding = await CommunicationApi.updateSchoolBranding(data);
      setBranding(updatedBranding);
      setHasUnsavedChanges(false);

      Alert.alert('Success', 'School branding updated successfully');
      return updatedBranding;
    } catch (err: any) {
      const errorMessage =
        err.response?.data?.detail || err.message || 'Failed to update school branding';
      setError(errorMessage);
      Alert.alert('Error', errorMessage);
      throw err;
    } finally {
      setSaving(false);
    }
  }, []);

  const uploadLogo = useCallback(async (logoFile: File) => {
    try {
      setSaving(true);
      setError(null);

      const updatedBranding = await CommunicationApi.uploadLogo(logoFile);
      setBranding(updatedBranding);
      setHasUnsavedChanges(false);

      Alert.alert('Success', 'School logo uploaded successfully');
      return updatedBranding;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to upload logo';
      setError(errorMessage);
      Alert.alert('Error', errorMessage);
      throw err;
    } finally {
      setSaving(false);
    }
  }, []);

  const updateBrandingField = useCallback(
    (field: keyof SchoolBranding, value: any) => {
      if (branding) {
        setBranding({
          ...branding,
          [field]: value,
        });
        setHasUnsavedChanges(true);
      }
    },
    [branding],
  );

  const resetChanges = useCallback(() => {
    if (branding) {
      fetchBranding(); // Reload original data
    }
  }, [branding, fetchBranding]);

  const saveBranding = useCallback(async () => {
    if (!branding || !hasUnsavedChanges) return;

    const updateData: UpdateBrandingRequest = {
      primary_color: branding.primary_color,
      secondary_color: branding.secondary_color,
      custom_messaging: branding.custom_messaging,
      email_footer: branding.email_footer,
    };

    return updateBranding(updateData);
  }, [branding, hasUnsavedChanges, updateBranding]);

  useEffect(() => {
    if (autoFetch) {
      fetchBranding();
    }
  }, [autoFetch, fetchBranding]);

  return {
    branding,
    loading,
    saving,
    error,
    hasUnsavedChanges,
    fetchBranding,
    updateBranding,
    uploadLogo,
    updateBrandingField,
    resetChanges,
    saveBranding,
    clearError: () => setError(null),
  };
};

export const useColorPicker = (initialColor: string = '#3B82F6') => {
  const [selectedColor, setSelectedColor] = useState(initialColor);
  const [isPickerOpen, setIsPickerOpen] = useState(false);

  const presetColors = [
    '#3B82F6', // Blue
    '#EF4444', // Red
    '#10B981', // Green
    '#F59E0B', // Yellow
    '#8B5CF6', // Purple
    '#EC4899', // Pink
    '#06B6D4', // Cyan
    '#84CC16', // Lime
    '#F97316', // Orange
    '#6B7280', // Gray
  ];

  const openPicker = useCallback(() => {
    setIsPickerOpen(true);
  }, []);

  const closePicker = useCallback(() => {
    setIsPickerOpen(false);
  }, []);

  const selectColor = useCallback((color: string) => {
    setSelectedColor(color);
  }, []);

  const selectPresetColor = useCallback((color: string) => {
    setSelectedColor(color);
    setIsPickerOpen(false);
  }, []);

  return {
    selectedColor,
    isPickerOpen,
    presetColors,
    openPicker,
    closePicker,
    selectColor,
    selectPresetColor,
    setSelectedColor,
  };
};

export const useBrandingPreview = () => {
  const [previewMode, setPreviewMode] = useState<'email' | 'template' | null>(null);
  const [previewData, setPreviewData] = useState<any>(null);

  const generateBrandingPreview = useCallback(
    (branding: SchoolBranding, templateContent?: string) => {
      const previewHtml = `
      <div style="
        font-family: Arial, sans-serif;
        max-width: 600px;
        margin: 0 auto;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        overflow: hidden;
      ">
        <!-- Header with school branding -->
        <div style="
          background-color: ${branding.primary_color};
          color: white;
          padding: 20px;
          text-align: center;
        ">
          ${
            branding.logo
              ? `<img src="${branding.logo}" alt="School Logo" style="max-height: 60px; margin-bottom: 10px;">`
              : ''
          }
          <h1 style="margin: 0; font-size: 24px;">Your School Name</h1>
        </div>
        
        <!-- Content area -->
        <div style="padding: 30px; background-color: white;">
          ${
            templateContent ||
            `
            <h2 style="color: ${branding.primary_color}; margin-top: 0;">Welcome to Our School!</h2>
            <p>This is a preview of how your emails will look with your school branding.</p>
            <div style="
              background-color: ${branding.primary_color}15;
              border-left: 4px solid ${branding.primary_color};
              padding: 15px;
              margin: 20px 0;
            ">
              <p style="margin: 0;"><strong>Custom messaging:</strong> ${
                branding.custom_messaging || 'Your custom message will appear here.'
              }</p>
            </div>
            <a href="#" style="
              display: inline-block;
              background-color: ${branding.primary_color};
              color: white;
              padding: 12px 24px;
              text-decoration: none;
              border-radius: 6px;
              font-weight: bold;
            ">Get Started</a>
          `
          }
        </div>
        
        <!-- Footer -->
        <div style="
          background-color: #f9fafb;
          padding: 20px;
          text-align: center;
          border-top: 1px solid #e5e7eb;
        ">
          <p style="margin: 0; font-size: 14px; color: #6b7280;">
            ${branding.email_footer || 'Best regards, Your School Team'}
          </p>
        </div>
      </div>
    `;

      setPreviewData(previewHtml);
      setPreviewMode('email');

      return previewHtml;
    },
    [],
  );

  const closePreview = useCallback(() => {
    setPreviewMode(null);
    setPreviewData(null);
  }, []);

  return {
    previewMode,
    previewData,
    generateBrandingPreview,
    closePreview,
  };
};
