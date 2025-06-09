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

import type { School } from './navigation-config';
import { schools, NAVIGATION_COLORS } from './navigation-config';

import { useAuth } from '@/api/authContext';
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
  onSchoolChange?: (school: School) => void;
  className?: string;
}

/**
 * TopNavigation component - renders the top header navigation
 * Adapts its layout based on the variant prop (web or mobile)
 *
 * @param variant Layout variant - 'web' shows menu toggle, 'mobile' shows back button
 * @param onToggleSidebar Callback for sidebar toggle (web only)
 * @param onSchoolChange Callback when school is changed
 * @param className Additional CSS classes
 */
export const TopNavigation = ({
  variant = 'web',
  onToggleSidebar,
  onSchoolChange,
  className = '',
}: TopNavigationProps) => {
  const { logout } = useAuth();
  const [selectedSchool, setSelectedSchool] = useState<School>(schools[2]); // Default to 3ponto14
  const [showSchoolMenu, setShowSchoolMenu] = useState(false);
  const [showLogoutModal, setShowLogoutModal] = useState(false);

  // School selector handlers
  const handleSelectSchool = (school: School) => {
    setSelectedSchool(school);
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
    const modalPosition = Platform.OS === 'web' ? { top: 60, left: 50 } : { top: 70, left: 10 };

    return (
      <Box className="relative">
        <Pressable
          onPress={() => setShowSchoolMenu(!showSchoolMenu)}
          className="flex-row items-center"
        >
          <Text className="text-2xl font-medium text-white">{selectedSchool.name}</Text>
          <Icon as={ChevronDownIcon} size="sm" className="ml-2 mt-1 text-white" />
        </Pressable>

        <Modal isOpen={showSchoolMenu} onClose={() => setShowSchoolMenu(false)}>
          <ModalBackdrop />
          <ModalContent
            style={{
              position: 'absolute',
              top: modalPosition.top,
              left: modalPosition.left,
              margin: 0,
              width: 250,
              backgroundColor: 'transparent',
              borderWidth: 0,
              zIndex: 9999,
            }}
          >
            <Box className="bg-background-0 border border-border-200 rounded-md shadow-md w-full">
              <VStack>
                {schools.map(school => (
                  <Pressable
                    key={school.id}
                    className={`p-3 hover:bg-background-50 ${
                      selectedSchool.id === school.id ? 'bg-background-50' : ''
                    }`}
                    onPress={() => handleSelectSchool(school)}
                  >
                    <Text>{school.name}</Text>
                  </Pressable>
                ))}
                <Pressable
                  className="p-3 flex-row items-center border-t border-border-200 hover:bg-background-50"
                  onPress={handleAddNewSchool}
                >
                  <Icon as={PlusIcon} size="sm" className="mr-2" />
                  <Text className="text-primary-600">Add new school</Text>
                </Pressable>
              </VStack>
            </Box>
          </ModalContent>
        </Modal>
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
        <HStack className="items-center">
          <Pressable onPress={() => onToggleSidebar && onToggleSidebar()}>
            <Icon as={MenuIcon} size="lg" className="mx-5 text-white" />
          </Pressable>
          <SchoolSelector />
        </HStack>

        <HStack space="md" className="items-center">
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
            <AvatarFallbackText className="font-light">A</AvatarFallbackText>
          </Avatar>
        </HStack>
      </HStack>
      <LogoutModal />
    </>
  );
};
