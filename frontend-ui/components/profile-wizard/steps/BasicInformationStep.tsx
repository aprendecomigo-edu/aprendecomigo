import * as ImagePicker from 'expo-image-picker';
import { ChevronDownIcon } from 'lucide-react-native';
import React, { useState } from 'react';
import { Alert } from 'react-native';

import { TeacherProfileData, ContactPreferences } from '@/api/invitationApi';
import { Box } from '@/components/ui/box';
import { ImageUploadComponent } from '@/components/ui/file-upload';
import { FormControl } from '@/components/ui/form-control';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Input, InputField } from '@/components/ui/input';
import {
  Select,
  SelectTrigger,
  SelectInput,
  SelectIcon,
  SelectPortal,
  SelectBackdrop,
  SelectContent,
  SelectDragIndicatorWrapper,
  SelectDragIndicator,
  SelectItem,
} from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Text } from '@/components/ui/text';
import { Textarea, TextareaInput } from '@/components/ui/textarea';
import { VStack } from '@/components/ui/vstack';
import FileUploadService from '@/services/FileUploadService';

interface BasicInformationStepProps {
  profileData: TeacherProfileData;
  updateProfileData: (updates: Partial<TeacherProfileData>) => void;
  validationErrors: { [key: string]: string };
  invitationData: any;
}

const BasicInformationStep: React.FC<BasicInformationStepProps> = ({
  profileData,
  updateProfileData,
  validationErrors,
  invitationData,
}) => {
  // Profile photo upload state
  const [photoUploadProgress, setPhotoUploadProgress] = useState(0);
  const [photoUploadStatus, setPhotoUploadStatus] = useState<
    'idle' | 'uploading' | 'success' | 'error'
  >('idle');
  const [photoUploadError, setPhotoUploadError] = useState<string>('');

  const contactPreferences = profileData.contact_preferences || {
    email_notifications: true,
    sms_notifications: false,
    call_notifications: false,
    preferred_contact_method: 'email',
  };

  const updateContactPreference = (key: keyof ContactPreferences, value: any) => {
    const updatedPreferences = {
      ...contactPreferences,
      [key]: value,
    };
    updateProfileData({ contact_preferences: updatedPreferences });
  };

  const handleIntroductionChange = (value: string) => {
    updateProfileData({ introduction: value });
  };

  const handleImageSelected = async (image: ImagePicker.ImagePickerAsset) => {
    try {
      // Update profile data with the local image URI immediately for preview
      updateProfileData({ profile_photo: image.uri });

      // Start upload process
      setPhotoUploadStatus('uploading');
      setPhotoUploadProgress(0);
      setPhotoUploadError('');

      const result = await FileUploadService.uploadProfilePhoto(image, {
        onProgress: progress => {
          setPhotoUploadProgress(progress.percentage);
        },
        onError: error => {
          setPhotoUploadStatus('error');
          setPhotoUploadError(error);
        },
        onSuccess: result => {
          setPhotoUploadStatus('success');
          // Update profile data with the server URL
          if (result.url) {
            updateProfileData({ profile_photo: result.url });
          }
        },
      });

      if (!result.success) {
        setPhotoUploadStatus('error');
        setPhotoUploadError(result.error || 'Upload failed');
      }
    } catch (error) {
      setPhotoUploadStatus('error');
      setPhotoUploadError('Failed to upload profile photo');
      console.error('Profile photo upload error:', error);
    }
  };

  const handleImageRemoved = () => {
    updateProfileData({ profile_photo: undefined });
    setPhotoUploadStatus('idle');
    setPhotoUploadProgress(0);
    setPhotoUploadError('');
  };

  const handleRetryUpload = () => {
    if (profileData.profile_photo && typeof profileData.profile_photo === 'string') {
      // If we have a local URI, try to re-upload
      // This is a simplified retry - in a real app you might want to store the original ImagePickerAsset
      setPhotoUploadStatus('idle');
      setPhotoUploadError('');
    }
  };

  return (
    <Box className="flex-1">
      <VStack space="lg">
        {/* Header */}
        <VStack space="sm">
          <Heading size="xl" className="text-gray-900">
            Informações Básicas
          </Heading>
          <Text className="text-gray-600">
            Estas informações ajudarão a escola e os alunos a conhecerem você melhor.
          </Text>
        </VStack>

        {/* Welcome Message */}
        <Box className="bg-blue-50 p-4 rounded-lg border border-blue-200">
          <VStack space="sm">
            <Text className="text-blue-800 font-medium">Bem-vindo, {invitationData?.email}!</Text>
            <Text className="text-blue-700 text-sm">
              Você foi convidado para se juntar à escola {invitationData?.invitation?.school?.name}.
              Vamos configurar seu perfil de professor.
            </Text>
          </VStack>
        </Box>

        {/* Profile Photo Upload */}
        <ImageUploadComponent
          onImageSelected={handleImageSelected}
          onImageRemoved={handleImageRemoved}
          currentImageUri={
            typeof profileData.profile_photo === 'string' ? profileData.profile_photo : undefined
          }
          uploadProgress={photoUploadProgress}
          uploadStatus={photoUploadStatus}
          uploadError={photoUploadError}
          onRetryUpload={handleRetryUpload}
          maxSizeInMB={5}
          quality={0.8}
          allowsEditing={true}
          aspect={[1, 1]}
        />

        {/* Introduction */}
        <FormControl className={validationErrors.introduction ? 'error' : ''}>
          <VStack space="sm">
            <Text className="font-medium">Apresentação Pessoal *</Text>
            <Text className="text-sm text-gray-600">
              Escreva uma breve apresentação sobre você e sua paixão pelo ensino.
            </Text>
            <Textarea className="min-h-[120px]">
              <TextareaInput
                placeholder="Exemplo: Sou professora de Matemática há 10 anos, apaixonada por ajudar os alunos a descobrirem a beleza dos números..."
                value={profileData.introduction || ''}
                onChangeText={handleIntroductionChange}
                multiline
                textAlignVertical="top"
              />
            </Textarea>
            {validationErrors.introduction && (
              <Text className="text-red-600 text-sm">{validationErrors.introduction}</Text>
            )}
            <Text className="text-xs text-gray-500">
              Caracteres: {(profileData.introduction || '').length}/500
            </Text>
          </VStack>
        </FormControl>

        {/* Contact Preferences */}
        <FormControl>
          <VStack space="lg">
            <Heading size="md" className="text-gray-800">
              Preferências de Contato
            </Heading>

            {/* Notification Preferences */}
            <VStack space="md">
              <Text className="font-medium">Como você gostaria de receber notificações?</Text>

              <VStack space="sm">
                <HStack className="justify-between items-center py-2">
                  <VStack>
                    <Text className="font-medium">Notificações por Email</Text>
                    <Text className="text-sm text-gray-600">
                      Receber updates sobre aulas e mensagens
                    </Text>
                  </VStack>
                  <Switch
                    value={contactPreferences.email_notifications}
                    onValueChange={value => updateContactPreference('email_notifications', value)}
                  />
                </HStack>

                <HStack className="justify-between items-center py-2">
                  <VStack>
                    <Text className="font-medium">Notificações por SMS</Text>
                    <Text className="text-sm text-gray-600">
                      Avisos importantes por mensagem de texto
                    </Text>
                  </VStack>
                  <Switch
                    value={contactPreferences.sms_notifications}
                    onValueChange={value => updateContactPreference('sms_notifications', value)}
                  />
                </HStack>

                <HStack className="justify-between items-center py-2">
                  <VStack>
                    <Text className="font-medium">Chamadas Telefônicas</Text>
                    <Text className="text-sm text-gray-600">
                      Aceitar chamadas para assuntos urgentes
                    </Text>
                  </VStack>
                  <Switch
                    value={contactPreferences.call_notifications}
                    onValueChange={value => updateContactPreference('call_notifications', value)}
                  />
                </HStack>
              </VStack>
            </VStack>

            {/* Preferred Contact Method */}
            <VStack space="sm">
              <Text className="font-medium">Método de Contato Preferido</Text>
              <Select
                selectedValue={contactPreferences.preferred_contact_method}
                onValueChange={value => updateContactPreference('preferred_contact_method', value)}
              >
                <SelectTrigger variant="outline" size="md">
                  <SelectInput placeholder="Selecione o método preferido" />
                  <SelectIcon className="mr-3" as={ChevronDownIcon} />
                </SelectTrigger>
                <SelectPortal>
                  <SelectBackdrop />
                  <SelectContent>
                    <SelectDragIndicatorWrapper>
                      <SelectDragIndicator />
                    </SelectDragIndicatorWrapper>
                    <SelectItem label="Email" value="email" />
                    <SelectItem label="SMS" value="sms" />
                    <SelectItem label="Chamada" value="call" />
                  </SelectContent>
                </SelectPortal>
              </Select>
            </VStack>
          </VStack>
        </FormControl>

        {/* Help Text */}
        <Box className="bg-gray-50 p-4 rounded-lg">
          <VStack space="sm">
            <Text className="font-medium text-gray-800">Dica:</Text>
            <Text className="text-sm text-gray-600">
              Uma boa apresentação inclui sua experiência, suas matérias favoritas e o que te motiva
              como educador. Isso ajuda os alunos e pais a se conectarem com você.
            </Text>
          </VStack>
        </Box>
      </VStack>
    </Box>
  );
};

export default BasicInformationStep;
