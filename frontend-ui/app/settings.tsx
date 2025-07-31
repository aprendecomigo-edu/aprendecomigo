import React from 'react';
import { SchoolSettingsForm } from '../components/school-settings/SchoolSettingsForm';
import { useSchoolSettings, SchoolSettingsFormData } from '../hooks/useSchoolSettings';
import { useAuth } from '@/api/authContext';
import { useState, useEffect } from 'react';
import { Alert } from 'react-native';
import { router } from 'expo-router';
import { Box } from '@/components/ui/box';
import { VStack } from '@/components/ui/vstack';
import { HStack } from '@/components/ui/hstack';
import { Text } from '@/components/ui/text';
import { Button, ButtonText } from '@/components/ui/button';
import { Center } from '@/components/ui/center';
import { Spinner } from '@/components/ui/spinner';
import { 
  AlertDialog,
  AlertDialogBackdrop,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogBody,
  AlertDialogFooter,
  AlertDialogCloseButton,
} from '@/components/ui/alert-dialog';
import { Heading } from '@/components/ui/heading';
import { Icon } from '@/components/ui/icon';
import { CloseIcon } from '@/components/ui/icon';

export default function SettingsPage() {
  const [showExitDialog, setShowExitDialog] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const { userProfile } = useAuth();
  const {
    schoolSettings,
    educationalSystems,
    loading,
    saving,
    error,
    fetchSchoolSettings,
    fetchEducationalSystems,
    updateSchoolSettings,
    clearError,
  } = useSchoolSettings();

  // Use dummy school ID for testing - in production this should be based on user's school
  const selectedSchoolId = 1;

  // Fetch school settings on mount
  useEffect(() => {
    if (selectedSchoolId) {
      fetchSchoolSettings(selectedSchoolId);
      fetchEducationalSystems(selectedSchoolId);
    }
  }, [selectedSchoolId, fetchSchoolSettings, fetchEducationalSystems]);

  // Show error toast when error occurs
  useEffect(() => {
    if (error) {
      Alert.alert('Error', error);
      clearError();
    }
  }, [error, clearError]);

  const handleSave = async (data: SchoolSettingsFormData) => {
    try {
      await updateSchoolSettings(selectedSchoolId, data);
      setHasUnsavedChanges(false);
      Alert.alert('Success', 'School settings updated successfully');
    } catch (err) {
      console.error('Save error:', err);
    }
  };

  const handleCancel = () => {
    if (hasUnsavedChanges) {
      setShowExitDialog(true);
    } else {
      router.back();
    }
  };

  if (loading) {
    return (
      <Center className="flex-1 bg-background-light-0">
        <VStack space="md" className="items-center">
          <Spinner size="large" />
          <Text>Loading school settings...</Text>
        </VStack>
      </Center>
    );
  }

  return (
    <Box className="flex-1 bg-background-light-0">
      <SchoolSettingsForm
        schoolId={selectedSchoolId}
        initialData={schoolSettings || undefined}
        educationalSystems={educationalSystems}
        onSave={handleSave}
        onCancel={handleCancel}
        loading={saving}
      />

      {/* Exit Confirmation Dialog */}
      <AlertDialog isOpen={showExitDialog} onClose={() => setShowExitDialog(false)}>
        <AlertDialogBackdrop />
        <AlertDialogContent>
          <AlertDialogHeader>
            <Heading size="lg">Unsaved Changes</Heading>
            <AlertDialogCloseButton>
              <Icon as={CloseIcon} />
            </AlertDialogCloseButton>
          </AlertDialogHeader>
          <AlertDialogBody>
            <Text>
              You have unsaved changes that will be lost if you leave this page. 
              Are you sure you want to continue?
            </Text>
          </AlertDialogBody>
          <AlertDialogFooter>
            <HStack space="md">
              <Button variant="outline" onPress={() => setShowExitDialog(false)}>
                <ButtonText>Cancel</ButtonText>
              </Button>
              <Button action="negative" onPress={() => {
                setShowExitDialog(false);
                setHasUnsavedChanges(false);
                router.back();
              }}>
                <ButtonText>Leave</ButtonText>
              </Button>
            </HStack>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </Box>
  );
}
