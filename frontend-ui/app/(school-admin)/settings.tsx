import { router } from 'expo-router';
import React, { useEffect, useState } from 'react';
import { View, Alert } from 'react-native';

import { SchoolSettingsForm } from '../../components/school-settings/SchoolSettingsForm';
import { useSchoolSettings, SchoolSettingsFormData } from '../../hooks/useSchoolSettings';

import { useAuth } from '@/api/authContext';
import { getUserAdminSchools, SchoolMembership } from '@/api/userApi';
import {
  AlertDialog,
  AlertDialogBackdrop,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogBody,
  AlertDialogFooter,
  AlertDialogCloseButton,
} from '@/components/ui/alert-dialog';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Center } from '@/components/ui/center';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon, CloseIcon } from '@/components/ui/icon';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { useToast } from '@/components/ui/toast';
import { VStack } from '@/components/ui/vstack';

export default function SchoolSettingsPage() {
  const [showExitDialog, setShowExitDialog] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [adminSchools, setAdminSchools] = useState<SchoolMembership[]>([]);
  const [selectedSchoolId, setSelectedSchoolId] = useState<number | null>(null);
  const [schoolsLoading, setSchoolsLoading] = useState(true);
  const [authorizationError, setAuthorizationError] = useState<string | null>(null);
  const toast = useToast();
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

  // Load admin schools on mount
  useEffect(() => {
    const loadAdminSchools = async () => {
      try {
        setSchoolsLoading(true);
        const schools = await getUserAdminSchools();
        setAdminSchools(schools);

        if (schools.length > 0) {
          // Auto-select the first school
          setSelectedSchoolId(schools[0].school.id);
          setAuthorizationError(null);
        } else {
          // User has no admin schools - this is a legitimate authorization issue
          setAuthorizationError(
            'You do not have administrative access to any schools. Please contact your system administrator.'
          );
          setSelectedSchoolId(null);
        }
      } catch (error) {
        // Handle API errors properly without bypassing authorization
        setAuthorizationError(
          'Failed to load school information. Please try again or contact support.'
        );
        setSelectedSchoolId(null);
        setAdminSchools([]);
      } finally {
        setSchoolsLoading(false);
      }
    };

    if (userProfile) {
      loadAdminSchools();
    }
  }, [userProfile]);

  // Fetch school settings when selected school changes
  useEffect(() => {
    if (selectedSchoolId) {
      fetchSchoolSettings(selectedSchoolId);
      fetchEducationalSystems(selectedSchoolId);
    }
  }, [selectedSchoolId, fetchSchoolSettings, fetchEducationalSystems]);

  // Show error toast when error occurs
  useEffect(() => {
    if (error) {
      // Simple alert for now
      Alert.alert('Error', error);
      clearError();
    }
  }, [error, clearError]);

  const handleSave = async (data: SchoolSettingsFormData) => {
    if (!selectedSchoolId) {
      Alert.alert('Error', 'No school selected');
      return;
    }

    try {
      await updateSchoolSettings(selectedSchoolId, data);
      setHasUnsavedChanges(false);

      // Simple alert for now
      Alert.alert('Success', 'School settings updated successfully');
    } catch (err) {
      // Error is handled in the hook and displayed via toast
    }
  };

  const handleCancel = () => {
    if (hasUnsavedChanges) {
      setShowExitDialog(true);
    } else {
      router.back();
    }
  };

  const confirmExit = () => {
    setShowExitDialog(false);
    setHasUnsavedChanges(false);
    router.back();
  };

  const cancelExit = () => {
    setShowExitDialog(false);
  };

  if (schoolsLoading || loading) {
    return (
      <Center className="flex-1 bg-background-light-0">
        <VStack space="md" className="items-center">
          <Spinner size="large" />
          <Text>Loading school settings...</Text>
        </VStack>
      </Center>
    );
  }

  if (authorizationError || (!selectedSchoolId && !schoolsLoading)) {
    // Check if user is school_admin but has no admin schools - this might be a data issue
    const isSchoolAdmin = userProfile?.user_type === 'school_admin' || userProfile?.is_admin;
    
    if (isSchoolAdmin && !authorizationError) {
      // For school admins without admin schools, show a more helpful message
      return (
        <Center className="flex-1 bg-background-light-0">
          <VStack space="lg" className="items-center px-6 max-w-md">
            <VStack space="md" className="items-center">
              <Heading size="lg" className="text-center">
                School Setup Required
              </Heading>
              <Text className="text-center text-typography-600">
                Your account has admin permissions but no schools are configured. Please contact support or check your account setup.
              </Text>
              <Text className="text-center text-typography-500 text-sm mt-2">
                User Type: {userProfile?.user_type} | Admin: {userProfile?.is_admin ? 'Yes' : 'No'}
              </Text>
            </VStack>
            <VStack space="sm" className="w-full">
              <Button onPress={() => router.replace('/(school-admin)/dashboard')} className="w-full">
                <ButtonText>Go to Dashboard</ButtonText>
              </Button>
              <Button
                variant="outline"
                onPress={() => {
                  // Try to reload the page to refresh data
                  if (typeof window !== 'undefined') {
                    window.location.reload();
                  }
                }}
                className="w-full"
              >
                <ButtonText>Refresh Page</ButtonText>
              </Button>
            </VStack>
          </VStack>
        </Center>
      );
    }
    
    return (
      <Center className="flex-1 bg-background-light-0">
        <VStack space="lg" className="items-center px-6 max-w-md">
          <VStack space="md" className="items-center">
            <Heading size="lg" className="text-center">
              Access Denied
            </Heading>
            <Text className="text-center text-typography-600">
              {authorizationError || 'You do not have permission to access school settings.'}
            </Text>
          </VStack>
          <VStack space="sm" className="w-full">
            <Button onPress={() => router.replace('/(school-admin)/dashboard')} className="w-full">
              <ButtonText>Go to Dashboard</ButtonText>
            </Button>
            <Button
              variant="outline"
              onPress={() => router.push('/auth/signin' as any)}
              className="w-full"
            >
              <ButtonText>Sign Out</ButtonText>
            </Button>
          </VStack>
        </VStack>
      </Center>
    );
  }

  const currentSchool = adminSchools.find(s => s.school.id === selectedSchoolId)?.school;

  return (
    <View style={{ flex: 1, backgroundColor: '#ffffff' }}>
      <Box className="flex-1 bg-background-light-0">
        <SchoolSettingsForm
          schoolId={selectedSchoolId!}
          initialData={schoolSettings || undefined}
          educationalSystems={educationalSystems}
          onSave={handleSave}
          onCancel={handleCancel}
          loading={saving}
        />

        {/* Exit Confirmation Dialog */}
        <AlertDialog isOpen={showExitDialog} onClose={cancelExit}>
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
                You have unsaved changes that will be lost if you leave this page. Are you sure you
                want to continue?
              </Text>
            </AlertDialogBody>
            <AlertDialogFooter>
              <HStack space="md">
                <Button variant="outline" onPress={cancelExit}>
                  <ButtonText>Cancel</ButtonText>
                </Button>
                <Button action="negative" onPress={confirmExit}>
                  <ButtonText>Leave</ButtonText>
                </Button>
              </HStack>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </Box>
    </View>
  );
}
