import { isWeb } from '@gluestack-ui/nativewind-utils/IsWeb';
import { router } from 'expo-router';
import {
  PaletteIcon,
  UploadIcon,
  EyeIcon,
  SaveIcon,
  RefreshCwIcon,
  ImageIcon,
  ColorWheelIcon,
  TypeIcon,
  MailIcon,
} from 'lucide-react-native';
import React, { useState, useCallback } from 'react';
import { Alert, Platform } from 'react-native';

import MainLayout from '@/components/layouts/main-layout';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Center } from '@/components/ui/center';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Image } from '@/components/ui/image';
import { Input, InputField } from '@/components/ui/input';
import { Pressable } from '@/components/ui/pressable';
import { ScrollView } from '@/components/ui/scroll-view';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { Textarea, TextareaInput } from '@/components/ui/textarea';
import { VStack } from '@/components/ui/vstack';
import { useSchoolBranding, useColorPicker, useBrandingPreview } from '@/hooks/useSchoolBranding';

const SchoolBrandingPage = () => {
  const [previewMode, setPreviewMode] = useState(false);

  // Hooks
  const {
    branding,
    loading,
    saving,
    error,
    hasUnsavedChanges,
    updateBrandingField,
    saveBranding,
    uploadLogo,
    resetChanges,
    clearError,
  } = useSchoolBranding();

  const {
    selectedColor: primaryColor,
    isPickerOpen: isPrimaryPickerOpen,
    presetColors,
    openPicker: openPrimaryPicker,
    closePicker: closePrimaryPicker,
    selectPresetColor: selectPrimaryPreset,
    setSelectedColor: setPrimaryColor,
  } = useColorPicker(branding?.primary_color);

  const {
    selectedColor: secondaryColor,
    isPickerOpen: isSecondaryPickerOpen,
    openPicker: openSecondaryPicker,
    closePicker: closeSecondaryPicker,
    selectPresetColor: selectSecondaryPreset,
    setSelectedColor: setSecondaryColor,
  } = useColorPicker(branding?.secondary_color);

  const {
    previewData,
    generateBrandingPreview,
    closePreview,
  } = useBrandingPreview();

  // Update primary color
  const handlePrimaryColorChange = useCallback((color: string) => {
    setPrimaryColor(color);
    updateBrandingField('primary_color', color);
  }, [setPrimaryColor, updateBrandingField]);

  // Update secondary color
  const handleSecondaryColorChange = useCallback((color: string) => {
    setSecondaryColor(color);
    updateBrandingField('secondary_color', color);
  }, [setSecondaryColor, updateBrandingField]);

  // Handle logo upload
  const handleLogoUpload = useCallback(async () => {
    if (!isWeb) {
      Alert.alert('Not Available', 'Logo upload is only available on web version');
      return;
    }

    // Create file input
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    input.onchange = async (e: Event) => {
      const target = e.target as HTMLInputElement;
      const file = target.files?.[0];
      
      if (file) {
        // Check file size (max 5MB)
        if (file.size > 5 * 1024 * 1024) {
          Alert.alert('File Too Large', 'Please select an image smaller than 5MB');
          return;
        }

        // Check file type
        if (!file.type.startsWith('image/')) {
          Alert.alert('Invalid File Type', 'Please select an image file');
          return;
        }

        try {
          await uploadLogo(file);
        } catch (err) {
          console.error('Error uploading logo:', err);
        }
      }
    };
    
    input.click();
  }, [uploadLogo]);

  // Handle save
  const handleSave = useCallback(async () => {
    try {
      await saveBranding();
    } catch (err) {
      console.error('Error saving branding:', err);
    }
  }, [saveBranding]);

  // Handle reset
  const handleReset = useCallback(() => {
    Alert.alert(
      'Reset Changes',
      'Are you sure you want to discard all unsaved changes?',
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Reset', 
          style: 'destructive',
          onPress: resetChanges 
        },
      ]
    );
  }, [resetChanges]);

  // Generate preview
  const handleGeneratePreview = useCallback(() => {
    if (branding) {
      generateBrandingPreview(branding);
      setPreviewMode(true);
    }
  }, [branding, generateBrandingPreview]);

  // Loading state
  if (loading) {
    return (
      <MainLayout _title="School Branding">
        <Center className="flex-1">
          <VStack space="md" className="items-center">
            <Spinner size="large" />
            <Text className="text-gray-600">Loading school branding...</Text>
          </VStack>
        </Center>
      </MainLayout>
    );
  }

  // Error state
  if (error && !branding) {
    return (
      <MainLayout _title="School Branding">
        <Center className="flex-1">
          <VStack space="md" className="items-center max-w-md">
            <Icon as={PaletteIcon} size="xl" className="text-red-400" />
            <Text className="text-red-600 font-semibold text-center">Error Loading Branding</Text>
            <Text className="text-gray-600 text-center">{error}</Text>
            <Button onPress={() => window.location.reload()} variant="outline">
              <ButtonText>Try Again</ButtonText>
            </Button>
          </VStack>
        </Center>
      </MainLayout>
    );
  }

  return (
    <ScrollView
      showsVerticalScrollIndicator={false}
      contentContainerStyle={{
        paddingBottom: isWeb ? 0 : 100,
        flexGrow: 1,
      }}
      className="flex-1 bg-gray-50"
    >
      <VStack className="p-6" space="lg">
        {/* Header */}
        <HStack className="justify-between items-center">
          <VStack space="xs">
            <Heading size="xl" className="text-gray-900">
              School Branding
            </Heading>
            <Text className="text-gray-600">
              Customize your school's visual identity for email communications
            </Text>
          </VStack>

          <HStack space="sm">
            <Button
              onPress={handleGeneratePreview}
              variant="outline"
              disabled={!branding}
            >
              <HStack space="xs" className="items-center">
                <Icon as={EyeIcon} size="sm" className="text-gray-600" />
                <ButtonText>Preview</ButtonText>
              </HStack>
            </Button>

            <Button
              onPress={handleSave}
              disabled={saving || !hasUnsavedChanges}
              className="bg-blue-600"
            >
              <HStack space="xs" className="items-center">
                <Icon as={SaveIcon} size="sm" className="text-white" />
                <ButtonText className="text-white">
                  {saving ? 'Saving...' : 'Save Changes'}
                </ButtonText>
              </HStack>
            </Button>
          </HStack>
        </HStack>

        {/* Error Display */}
        {error && (
          <Card className="p-4 bg-red-50 border-red-200">
            <HStack space="sm" className="items-start">
              <Icon as={PaletteIcon} size="sm" className="text-red-600 mt-0.5" />
              <VStack space="xs" className="flex-1">
                <Text className="font-medium text-red-800">Error Updating Branding</Text>
                <Text className="text-sm text-red-600">{error}</Text>
                <Button onPress={clearError} size="sm" variant="outline" className="border-red-300 self-start">
                  <ButtonText>Dismiss</ButtonText>
                </Button>
              </VStack>
            </HStack>
          </Card>
        )}

        {/* Unsaved Changes Warning */}
        {hasUnsavedChanges && (
          <Card className="p-4 bg-orange-50 border-orange-200">
            <HStack className="justify-between items-center">
              <HStack space="sm" className="items-center flex-1">
                <Icon as={SaveIcon} size="sm" className="text-orange-600" />
                <Text className="font-medium text-orange-800">You have unsaved changes</Text>
              </HStack>
              <HStack space="sm">
                <Button onPress={handleSave} size="sm" className="bg-orange-600">
                  <ButtonText className="text-white">Save</ButtonText>
                </Button>
                <Button onPress={handleReset} size="sm" variant="outline" className="border-orange-300">
                  <ButtonText>Reset</ButtonText>
                </Button>
              </HStack>
            </HStack>
          </Card>
        )}

        {branding && (
          <>
            {/* Logo Section */}
            <Card className="p-6">
              <VStack space="lg">
                <HStack className="justify-between items-center">
                  <VStack space="xs">
                    <Heading size="md" className="text-gray-900">School Logo</Heading>
                    <Text className="text-gray-600">Upload your school's logo for email headers</Text>
                  </VStack>
                  <Button onPress={handleLogoUpload} variant="outline" disabled={saving}>
                    <HStack space="xs" className="items-center">
                      <Icon as={UploadIcon} size="sm" className="text-gray-600" />
                      <ButtonText>Upload Logo</ButtonText>
                    </HStack>
                  </Button>
                </HStack>

                {/* Current Logo Display */}
                <Box className="bg-gray-100 rounded-lg p-8 border-2 border-dashed border-gray-300">
                  {branding.logo ? (
                    <VStack space="md" className="items-center">
                      <Image
                        source={{ uri: branding.logo }}
                        alt="School Logo"
                        style={{ width: 120, height: 80 }}
                        className="rounded-lg"
                        resizeMode="contain"
                      />
                      <VStack space="xs" className="items-center">
                        <Text className="text-sm font-medium text-gray-900">Current Logo</Text>
                        <Text className="text-xs text-gray-500">Click "Upload Logo" to change</Text>
                      </VStack>
                    </VStack>
                  ) : (
                    <VStack space="md" className="items-center">
                      <Icon as={ImageIcon} size="xl" className="text-gray-400" />
                      <VStack space="xs" className="items-center">
                        <Text className="text-sm font-medium text-gray-900">No Logo Uploaded</Text>
                        <Text className="text-xs text-gray-500 text-center">
                          Upload a logo to display in your email headers
                        </Text>
                      </VStack>
                    </VStack>
                  )}
                </Box>

                <VStack space="xs">
                  <Text className="text-xs text-gray-500">
                    • Recommended size: 400x200 pixels or similar 2:1 aspect ratio
                  </Text>
                  <Text className="text-xs text-gray-500">
                    • Supported formats: PNG, JPG, GIF (max 5MB)
                  </Text>
                  <Text className="text-xs text-gray-500">
                    • For best results, use a transparent background PNG
                  </Text>
                </VStack>
              </VStack>
            </Card>

            {/* Colors Section */}
            <Card className="p-6">
              <VStack space="lg">
                <VStack space="xs">
                  <Heading size="md" className="text-gray-900">Brand Colors</Heading>
                  <Text className="text-gray-600">Set your school's primary and secondary colors</Text>
                </VStack>

                {/* Primary Color */}
                <VStack space="md">
                  <Text className="font-medium text-gray-900">Primary Color</Text>
                  <Text className="text-sm text-gray-600">
                    Used for headers, buttons, and main accents in emails
                  </Text>
                  
                  <HStack space="md" className="items-center">
                    <Pressable
                      onPress={openPrimaryPicker}
                      className="w-16 h-16 rounded-lg border-2 border-gray-300 shadow-sm"
                      style={{ backgroundColor: primaryColor }}
                    />
                    
                    <VStack space="sm" className="flex-1">
                      <Input>
                        <InputField
                          placeholder="#3B82F6"
                          value={primaryColor}
                          onChangeText={handlePrimaryColorChange}
                          style={{ fontFamily: 'monospace' }}
                        />
                      </Input>
                      <Text className="text-xs text-gray-500">Enter hex color code</Text>
                    </VStack>
                  </HStack>

                  {/* Color Presets */}
                  {isPrimaryPickerOpen && (
                    <VStack space="sm">
                      <Text className="text-sm font-medium text-gray-900">Quick Colors</Text>
                      <HStack space="sm" className="flex-wrap">
                        {presetColors.map((color) => (
                          <Pressable
                            key={color}
                            onPress={() => {
                              selectPrimaryPreset(color);
                              handlePrimaryColorChange(color);
                            }}
                            className={`w-10 h-10 rounded-lg border-2 ${
                              primaryColor === color ? 'border-gray-900' : 'border-gray-300'
                            }`}
                            style={{ backgroundColor: color }}
                          />
                        ))}
                      </HStack>
                    </VStack>
                  )}
                </VStack>

                {/* Secondary Color */}
                <VStack space="md">
                  <Text className="font-medium text-gray-900">Secondary Color</Text>
                  <Text className="text-sm text-gray-600">
                    Used for text, borders, and secondary elements
                  </Text>
                  
                  <HStack space="md" className="items-center">
                    <Pressable
                      onPress={openSecondaryPicker}
                      className="w-16 h-16 rounded-lg border-2 border-gray-300 shadow-sm"
                      style={{ backgroundColor: secondaryColor }}
                    />
                    
                    <VStack space="sm" className="flex-1">
                      <Input>
                        <InputField
                          placeholder="#1F2937"
                          value={secondaryColor}
                          onChangeText={handleSecondaryColorChange}
                          style={{ fontFamily: 'monospace' }}
                        />
                      </Input>
                      <Text className="text-xs text-gray-500">Enter hex color code</Text>
                    </VStack>
                  </HStack>

                  {/* Color Presets */}
                  {isSecondaryPickerOpen && (
                    <VStack space="sm">
                      <Text className="text-sm font-medium text-gray-900">Quick Colors</Text>
                      <HStack space="sm" className="flex-wrap">
                        {presetColors.map((color) => (
                          <Pressable
                            key={color}
                            onPress={() => {
                              selectSecondaryPreset(color);
                              handleSecondaryColorChange(color);
                            }}
                            className={`w-10 h-10 rounded-lg border-2 ${
                              secondaryColor === color ? 'border-gray-900' : 'border-gray-300'
                            }`}
                            style={{ backgroundColor: color }}
                          />
                        ))}
                      </HStack>
                    </VStack>
                  )}
                </VStack>
              </VStack>
            </Card>

            {/* Custom Messaging */}
            <Card className="p-6">
              <VStack space="lg">
                <VStack space="xs">
                  <Heading size="md" className="text-gray-900">Custom Messaging</Heading>
                  <Text className="text-gray-600">
                    Add a custom message to appear in highlighted sections of emails
                  </Text>
                </VStack>

                <VStack space="sm">
                  <Text className="font-medium text-gray-900">Custom Message</Text>
                  <Textarea>
                    <TextareaInput
                      placeholder="e.g., 'Join our community of passionate educators committed to student success'"
                      value={branding.custom_messaging || ''}
                      onChangeText={(value) => updateBrandingField('custom_messaging', value)}
                      multiline
                      numberOfLines={3}
                    />
                  </Textarea>
                  <Text className="text-xs text-gray-500">
                    This message will appear in callout boxes within your email templates
                  </Text>
                </VStack>
              </VStack>
            </Card>

            {/* Email Footer */}
            <Card className="p-6">
              <VStack space="lg">
                <VStack space="xs">
                  <Heading size="md" className="text-gray-900">Email Footer</Heading>
                  <Text className="text-gray-600">
                    Set a custom footer message for all school emails
                  </Text>
                </VStack>

                <VStack space="sm">
                  <Text className="font-medium text-gray-900">Footer Message</Text>
                  <Textarea>
                    <TextareaInput
                      placeholder="e.g., 'Best regards, The School Team'"
                      value={branding.email_footer || ''}
                      onChangeText={(value) => updateBrandingField('email_footer', value)}
                      multiline
                      numberOfLines={2}
                    />
                  </Textarea>
                  <Text className="text-xs text-gray-500">
                    This will appear at the bottom of all emails sent from your school
                  </Text>
                </VStack>
              </VStack>
            </Card>

            {/* Preview Section */}
            <Card className="p-6">
              <VStack space="lg">
                <HStack className="justify-between items-center">
                  <VStack space="xs">
                    <Heading size="md" className="text-gray-900">Email Preview</Heading>
                    <Text className="text-gray-600">
                      See how your branding will look in emails
                    </Text>
                  </VStack>
                  <Button onPress={handleGeneratePreview} variant="outline">
                    <HStack space="xs" className="items-center">
                      <Icon as={EyeIcon} size="sm" className="text-gray-600" />
                      <ButtonText>Generate Preview</ButtonText>
                    </HStack>
                  </Button>
                </HStack>

                {previewData && previewMode && (
                  <VStack space="md">
                    <HStack className="justify-between items-center">
                      <Text className="font-medium text-gray-900">Email Preview</Text>
                      <Button onPress={() => setPreviewMode(false)} size="sm" variant="outline">
                        <ButtonText>Close Preview</ButtonText>
                      </Button>
                    </HStack>

                    {isWeb ? (
                      <Box className="border border-gray-200 rounded-lg overflow-hidden">
                        <div
                          dangerouslySetInnerHTML={{ __html: previewData }}
                          style={{ minHeight: '400px' }}
                        />
                      </Box>
                    ) : (
                      <Card className="p-6 bg-gray-100">
                        <VStack space="sm" className="items-center">
                          <Icon as={MailIcon} size="xl" className="text-gray-400" />
                          <Text className="text-gray-600 text-center">
                            Email preview is only available on web. Use the web version to see how your branding will look in emails.
                          </Text>
                        </VStack>
                      </Card>
                    )}
                  </VStack>
                )}

                {!previewData && (
                  <Card className="p-8 bg-gray-50">
                    <VStack space="sm" className="items-center">
                      <Icon as={MailIcon} size="xl" className="text-gray-400" />
                      <Text className="text-gray-600 text-center">
                        Click "Generate Preview" to see how your branding will look in emails
                      </Text>
                    </VStack>
                  </Card>
                )}
              </VStack>
            </Card>

            {/* Save Actions */}
            <Card className="p-6">
              <VStack space="md">
                <Text className="font-medium text-gray-900">Save Your Changes</Text>
                
                <HStack space="sm" className="flex-wrap">
                  <Button
                    onPress={handleSave}
                    disabled={saving || !hasUnsavedChanges}
                    className="bg-blue-600 flex-1"
                  >
                    <ButtonText className="text-white">
                      {saving ? 'Saving...' : 'Save Branding'}
                    </ButtonText>
                  </Button>

                  {hasUnsavedChanges && (
                    <Button onPress={handleReset} variant="outline" className="flex-1">
                      <HStack space="xs" className="items-center">
                        <Icon as={RefreshCwIcon} size="sm" className="text-gray-600" />
                        <ButtonText>Reset Changes</ButtonText>
                      </HStack>
                    </Button>
                  )}
                </HStack>

                <Text className="text-xs text-gray-500 text-center">
                  Your branding changes will apply to all new emails sent from your school
                </Text>
              </VStack>
            </Card>
          </>
        )}
      </VStack>
    </ScrollView>
  );
};

const SchoolBrandingPageWrapper = () => {
  return (
    <MainLayout _title="School Branding">
      <SchoolBrandingPage />
    </MainLayout>
  );
};

export default SchoolBrandingPageWrapper;