import { router } from 'expo-router';
import {
  AlertTriangleIcon,
  ChevronDownIcon,
  LogOutIcon,
  MenuIcon,
  PlusIcon,
} from 'lucide-react-native';
import React, { useState } from 'react';
import { Platform, Alert } from 'react-native';

import { NAVIGATION_COLORS } from './navigation-config';
import { QuickActions } from './quick-actions';

import { useAuth, UserSchool } from '@/api/authContext';
import { GlobalSearch } from '@/components/search/global-search';
import { Avatar, AvatarFallbackText } from '@/components/ui/avatar';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Center } from '@/components/ui/center';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import {
  Modal,
  ModalBackdrop,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
} from '@/components/ui/modal';
import { Pressable } from '@/components/ui/pressable';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

interface TopNavigationProps {
  variant?: 'web' | 'mobile';
  onToggleSidebar?: () => void;
  onSchoolChange?: (school: UserSchool) => void;
  className?: string;
  showSearch?: boolean;
  showQuickActions?: boolean;
}

/**
 * TopNavigation component - renders the top header navigation
 * Adapts its layout based on the variant prop (web or mobile)
 *
 * @param variant Layout variant - 'web' shows menu toggle, 'mobile' shows back button
 * @param onToggleSidebar Callback for sidebar toggle (web only)
 * @param onSchoolChange Callback when school is changed
 * @param className Additional CSS classes
 * @param showSearch Whether to show the global search component
 * @param showQuickActions Whether to show quick actions dropdown
 */
export const TopNavigation = ({
  variant = 'web',
  onToggleSidebar,
  onSchoolChange,
  className = '',
  showSearch = false,
  showQuickActions = true,
}: TopNavigationProps) => {
  const { logout, userProfile, userSchools, currentSchool, setCurrentSchool } = useAuth();
  const [showSchoolMenu, setShowSchoolMenu] = useState(false);
  const [showLogoutModal, setShowLogoutModal] = useState(false);

  // Check if user is admin to show admin features
  const isAdmin = userProfile?.user_type === 'admin' || userProfile?.is_admin;

  // School selector handlers
  const handleSelectSchool = (school: UserSchool) => {
    setCurrentSchool(school);
    setShowSchoolMenu(false);
    if (onSchoolChange) {
      onSchoolChange(school);
    }
  };

  const handleAddNewSchool = () => {
    setShowSchoolMenu(false);
    Alert.alert('Add School', 'This would open a form to add a new school');
  };

  // Logout handlers
  const handlePressLogout = () => {
    setShowLogoutModal(true);
  };

  const handleConfirmLogout = async () => {
    setShowLogoutModal(false);
    setTimeout(async () => {
      try {
        await logout();
      } catch (error) {
        console.error('Error during logout:', error);
      }
    }, 150);
  };

  const handleCancelLogout = () => {
    setShowLogoutModal(false);
  };

  // School selector component
  const SchoolSelector = () => {
    if (!currentSchool && userSchools.length === 0) {
      return (
        <Text className="text-2xl font-medium text-white">Loading...</Text>
      );
    }

    return (
      <Box className="relative">
        <Pressable
          onPress={() => setShowSchoolMenu(!showSchoolMenu)}
          className="flex-row items-center"
        >
          <Text className="text-2xl font-medium text-white">{currentSchool?.name || 'Select School'}</Text>
          <Icon as={ChevronDownIcon} size="sm" className="ml-2 mt-1 text-white" />
        </Pressable>

        {showSchoolMenu && (
          <Box 
            className="absolute top-full left-0 mt-2 w-64 bg-background-0 border border-border-200 rounded-md shadow-lg z-50"
            style={{
              minWidth: 250,
              maxHeight: 300,
            }}
          >
            <VStack className="max-h-60 overflow-y-auto">
              {userSchools.map(school => (
                <Pressable
                  key={school.id}
                  className={`p-3 hover:bg-background-50 ${
                    currentSchool?.id === school.id ? 'bg-background-50' : ''
                  }`}
                  onPress={() => handleSelectSchool(school)}
                >
                  <VStack>
                    <Text className="font-medium">{school.name}</Text>
                    <Text className="text-sm text-typography-500">{school.role_display}</Text>
                  </VStack>
                </Pressable>
              ))}
              {userProfile?.is_admin && (
                <Pressable
                  className="p-3 flex-row items-center border-t border-border-200 hover:bg-background-50"
                  onPress={handleAddNewSchool}
                >
                  <Icon as={PlusIcon} size="sm" className="mr-2" />
                  <Text className="text-primary-600">Add new school</Text>
                </Pressable>
              )}
            </VStack>
          </Box>
        )}

        {/* Backdrop to close dropdown when clicking outside */}
        {showSchoolMenu && (
          <Pressable
            className="fixed inset-0 z-40"
            onPress={() => setShowSchoolMenu(false)}
          />
        )}
      </Box>
    );
  };

  // Logout confirmation modal
  const LogoutModal = () => (
    <Modal isOpen={showLogoutModal} onClose={handleCancelLogout}>
      <ModalBackdrop />
      <ModalContent className="p-6">
        <ModalHeader>
          <Heading size="lg">Confirm Logout</Heading>
          <ModalCloseButton>
            <Icon as={AlertTriangleIcon} />
          </ModalCloseButton>
        </ModalHeader>
        <ModalBody>
          <Center>
            <Icon as={AlertTriangleIcon} className="w-14 h-14 mb-4 text-amber-500" />
            <Text className="text-center mb-2">Are you sure you want to log out?</Text>
            <Text className="text-center text-sm text-typography-500">
              You will need to sign in again to access your account.
            </Text>
          </Center>
        </ModalBody>
        <ModalFooter>
          <Button
            variant="outline"
            action="secondary"
            className="flex-1 mr-2"
            onPress={handleCancelLogout}
          >
            <ButtonText>Cancel</ButtonText>
          </Button>
          <Button action="negative" className="flex-1 ml-2" onPress={handleConfirmLogout}>
            <ButtonText>Logout</ButtonText>
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );

  if (variant === 'mobile') {
    return (
      <>
        <HStack
          className={`py-6 px-4 border-b border-border-50 items-center justify-between ${className}`}
          style={{ backgroundColor: NAVIGATION_COLORS.primary }}
        >
          <HStack space="md" className="items-center">
            <Pressable onPress={() => router.back()}>
              <Icon as={MenuIcon} className="text-white" />
            </Pressable>
            <SchoolSelector />
          </HStack>

          <Pressable className="bg-error-50 rounded-full p-2" onPress={handlePressLogout}>
            <Icon as={LogOutIcon} className="w-5 h-5 stroke-error-700" />
          </Pressable>
        </HStack>
        <LogoutModal />
      </>
    );
  }

  // Web variant
  return (
    <>
      <HStack
        className={`pt-4 pr-10 pb-3 items-center justify-between border-b border-border-300 ${className}`}
        style={{ backgroundColor: NAVIGATION_COLORS.primary }}
      >
        <HStack className="items-center" space="md">
          <Pressable onPress={() => onToggleSidebar && onToggleSidebar()}>
            <Icon as={MenuIcon} size="lg" className="mx-5 text-white" />
          </Pressable>
          <SchoolSelector />
        </HStack>

        {/* Center - Global Search */}
        {showSearch && (
          <Box className="flex-1 max-w-md mx-8">
            <GlobalSearch placeholder="Search teachers, students, classes..." />
          </Box>
        )}

        <HStack space="md" className="items-center">
          {/* Quick Actions - Only for admins */}
          {showQuickActions && isAdmin && <QuickActions variant="dropdown" />}

          <Button
            size="sm"
            variant="outline"
            action="negative"
            onPress={handlePressLogout}
            className="border-error-600"
          >
            <HStack space="xs" className="items-center">
              <Icon as={LogOutIcon} className="w-4 h-4 stroke-error-700" />
              <ButtonText className="text-error-700">Logout</ButtonText>
            </HStack>
          </Button>
          <Avatar className="h-9 w-9">
            <AvatarFallbackText className="font-light">
              {userProfile?.first_name?.charAt(0) || 'U'}
            </AvatarFallbackText>
          </Avatar>
        </HStack>
      </HStack>

      {/* Quick Actions FAB for mobile */}
      {showQuickActions && isAdmin && variant === 'mobile' && <QuickActions variant="fab" />}

      <LogoutModal />
    </>
  );
};
