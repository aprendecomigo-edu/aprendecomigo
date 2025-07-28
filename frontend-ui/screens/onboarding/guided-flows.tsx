import { UserPlus, GraduationCap, Building2, X, CheckCircle, AlertCircle } from 'lucide-react-native';
import React, { useState } from 'react';
import { Platform, Dimensions } from 'react-native';

import { useOnboarding } from '@/hooks/useOnboarding';
import { InviteTeacherModal } from '@/components/modals/invite-teacher-modal';
import { AddStudentModal } from '@/components/modals/add-student-modal';
import { Box } from '@/components/ui/box';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import {
  Modal,
  ModalBackdrop,
  ModalContent,
  ModalHeader,
  ModalCloseButton,
  ModalBody,
  ModalFooter,
} from '@/components/ui/modal';
import { Badge, BadgeText } from '@/components/ui/badge';
import { Divider } from '@/components/ui/divider';

const { width: screenWidth } = Dimensions.get('window');
const isMobile = Platform.OS !== 'web' || screenWidth < 768;

interface GuidedFlowProps {
  isOpen: boolean;
  onClose: () => void;
  onComplete?: () => void;
}

// Guided flow for adding first teacher
export const AddFirstTeacherFlow: React.FC<GuidedFlowProps> = ({
  isOpen,
  onClose,
  onComplete,
}) => {
  const { completeStep } = useOnboarding();
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [isCompleted, setIsCompleted] = useState(false);

  const handleInviteSuccess = async () => {
    try {
      await completeStep('invite_first_teacher');
      setIsCompleted(true);
      if (onComplete) {
        onComplete();
      }
    } catch (error) {
      console.error('Error completing invite teacher step:', error);
    }
  };

  const handleClose = () => {
    setShowInviteModal(false);
    onClose();
  };

  return (
    <>
      <Modal isOpen={isOpen} onClose={handleClose}>
        <ModalBackdrop />
        <ModalContent className="max-w-md">
          <ModalHeader>
            <VStack space="sm">
              <HStack className="items-center justify-between">
                <Icon as={UserPlus} size={24} className="text-blue-600" />
                <ModalCloseButton />
              </HStack>
              <Heading size="lg" className="text-gray-900">
                Invite Your First Teacher
              </Heading>
            </VStack>
          </ModalHeader>
          
          <ModalBody>
            <VStack space="lg">
              {!isCompleted ? (
                <>
                  <VStack space="sm">
                    <Text className="text-gray-700">
                      Teachers are the backbone of your educational platform. Let's start by inviting your first teacher to join.
                    </Text>
                    <Text className="text-gray-600 text-sm">
                      They'll receive an email invitation with instructions to set up their account.
                    </Text>
                  </VStack>

                  <Card className="bg-blue-50 border-blue-200">
                    <VStack space="sm" className="p-4">
                      <Heading size="sm" className="text-blue-900">
                        What you'll need:
                      </Heading>
                      <VStack space="xs">
                        <Text className="text-blue-800 text-sm">• Teacher's email address</Text>
                        <Text className="text-blue-800 text-sm">• Their role (Teacher, Head Teacher, etc.)</Text>
                        <Text className="text-blue-800 text-sm">• Optional: Personal message</Text>
                      </VStack>
                    </VStack>
                  </Card>
                </>
              ) : (
                <VStack space="md" className="items-center text-center">
                  <Icon as={CheckCircle} size={48} className="text-green-500" />
                  <VStack space="sm">
                    <Heading size="md" className="text-gray-900">
                      Teacher Invited Successfully!
                    </Heading>
                    <Text className="text-gray-600">
                      Your teacher invitation has been sent. They'll receive an email with instructions to join your school.
                    </Text>
                  </VStack>
                </VStack>
              )}
            </VStack>
          </ModalBody>
          
          <ModalFooter>
            <HStack space="sm" className="w-full">
              {!isCompleted ? (
                <>
                  <Button
                    variant="outline"
                    onPress={handleClose}
                    className="flex-1"
                  >
                    <ButtonText>Cancel</ButtonText>
                  </Button>
                  <Button
                    onPress={() => setShowInviteModal(true)}
                    className="flex-1 bg-blue-600"
                  >
                    <ButtonIcon as={UserPlus} className="text-white mr-2" />
                    <ButtonText className="text-white">Send Invitation</ButtonText>
                  </Button>
                </>
              ) : (
                <Button
                  onPress={handleClose}
                  className="w-full bg-green-600"
                >
                  <ButtonText className="text-white">Continue</ButtonText>
                </Button>
              )}
            </HStack>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* Teacher Invitation Modal */}
      <InviteTeacherModal
        isOpen={showInviteModal}
        onClose={() => setShowInviteModal(false)}
        onSuccess={handleInviteSuccess}
      />
    </>
  );
};

// Guided flow for adding first student
export const AddFirstStudentFlow: React.FC<GuidedFlowProps> = ({
  isOpen,
  onClose,
  onComplete,
}) => {
  const { completeStep } = useOnboarding();
  const [showStudentModal, setShowStudentModal] = useState(false);
  const [isCompleted, setIsCompleted] = useState(false);

  const handleStudentSuccess = async () => {
    try {
      await completeStep('add_first_student');
      setIsCompleted(true);
      if (onComplete) {
        onComplete();
      }
    } catch (error) {
      console.error('Error completing add student step:', error);
    }
  };

  const handleClose = () => {
    setShowStudentModal(false);
    onClose();
  };

  return (
    <>
      <Modal isOpen={isOpen} onClose={handleClose}>
        <ModalBackdrop />
        <ModalContent className="max-w-md">
          <ModalHeader>
            <VStack space="sm">
              <HStack className="items-center justify-between">
                <Icon as={GraduationCap} size={24} className="text-blue-600" />
                <ModalCloseButton />
              </HStack>
              <Heading size="lg" className="text-gray-900">
                Add Your First Student
              </Heading>
            </VStack>
          </ModalHeader>
          
          <ModalBody>
            <VStack space="lg">
              {!isCompleted ? (
                <>
                  <VStack space="sm">
                    <Text className="text-gray-700">
                      Students are at the heart of your educational mission. Let's add your first student to get started with enrollment management.
                    </Text>
                    <Text className="text-gray-600 text-sm">
                      You can add students individually or import them in bulk later.
                    </Text>
                  </VStack>

                  <Card className="bg-green-50 border-green-200">
                    <VStack space="sm" className="p-4">
                      <Heading size="sm" className="text-green-900">
                        Student information needed:
                      </Heading>
                      <VStack space="xs">
                        <Text className="text-green-800 text-sm">• Full name and contact details</Text>
                        <Text className="text-green-800 text-sm">• Grade level and subjects</Text>
                        <Text className="text-green-800 text-sm">• Parent/guardian information</Text>
                        <Text className="text-green-800 text-sm">• Optional: Special requirements</Text>
                      </VStack>
                    </VStack>
                  </Card>
                </>
              ) : (
                <VStack space="md" className="items-center text-center">
                  <Icon as={CheckCircle} size={48} className="text-green-500" />
                  <VStack space="sm">
                    <Heading size="md" className="text-gray-900">
                      Student Added Successfully!
                    </Heading>
                    <Text className="text-gray-600">
                      Your first student has been added to your school. You can now manage their enrollment and schedule classes.
                    </Text>
                  </VStack>
                </VStack>
              )}
            </VStack>
          </ModalBody>
          
          <ModalFooter>
            <HStack space="sm" className="w-full">
              {!isCompleted ? (
                <>
                  <Button
                    variant="outline"
                    onPress={handleClose}
                    className="flex-1"
                  >
                    <ButtonText>Cancel</ButtonText>
                  </Button>
                  <Button
                    onPress={() => setShowStudentModal(true)}
                    className="flex-1 bg-green-600"
                  >
                    <ButtonIcon as={GraduationCap} className="text-white mr-2" />
                    <ButtonText className="text-white">Add Student</ButtonText>
                  </Button>
                </>
              ) : (
                <Button
                  onPress={handleClose}
                  className="w-full bg-green-600"
                >
                  <ButtonText className="text-white">Continue</ButtonText>
                </Button>
              )}
            </HStack>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* Student Addition Modal */}
      <AddStudentModal
        isOpen={showStudentModal}
        onClose={() => setShowStudentModal(false)}
        onSuccess={handleStudentSuccess}
      />
    </>
  );
};

// Guided flow for school profile setup
export const SchoolProfileFlow: React.FC<GuidedFlowProps> = ({
  isOpen,
  onClose,
  onComplete,
}) => {
  const { completeStep } = useOnboarding();
  const [currentStep, setCurrentStep] = useState(0);
  const [isCompleted, setIsCompleted] = useState(false);

  const profileSteps = [
    {
      title: 'Basic Information',
      description: 'Add your school name, description, and contact information'
    },
    {
      title: 'School Logo & Branding',
      description: 'Upload your school logo and customize the appearance'
    },
    {
      title: 'Contact & Location',
      description: 'Add address, phone numbers, and website information'
    },
    {
      title: 'Educational Settings',
      description: 'Configure grade levels, subjects, and academic year settings'
    }
  ];

  const handleComplete = async () => {
    try {
      await completeStep('complete_school_profile');
      setIsCompleted(true);
      if (onComplete) {
        onComplete();
      }
    } catch (error) {
      console.error('Error completing school profile step:', error);
    }
  };

  const handleClose = () => {
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose}>
      <ModalBackdrop />
      <ModalContent className="max-w-lg">
        <ModalHeader>
          <VStack space="sm">
            <HStack className="items-center justify-between">
              <Icon as={Building2} size={24} className="text-blue-600" />
              <ModalCloseButton />
            </HStack>
            <Heading size="lg" className="text-gray-900">
              Complete School Profile
            </Heading>
          </VStack>
        </ModalHeader>
        
        <ModalBody>
          <VStack space="lg">
            {!isCompleted ? (
              <>
                <VStack space="sm">
                  <Text className="text-gray-700">
                    Let's set up your school profile to personalize the platform and provide essential information to teachers, students, and parents.
                  </Text>
                </VStack>

                <Card className="bg-blue-50 border-blue-200">
                  <VStack space="md" className="p-4">
                    <Heading size="sm" className="text-blue-900">
                      Profile Setup Steps:
                    </Heading>
                    <VStack space="sm">
                      {profileSteps.map((step, index) => (
                        <HStack key={index} space="sm" className="items-start">
                          <Box className="mt-1">
                            <Icon 
                              as={currentStep > index ? CheckCircle : AlertCircle} 
                              size={16} 
                              className={currentStep > index ? 'text-green-500' : 'text-blue-500'}
                            />
                          </Box>
                          <VStack className="flex-1" space="xs">
                            <Text className="text-blue-900 text-sm font-medium">
                              {step.title}
                            </Text>
                            <Text className="text-blue-700 text-xs">
                              {step.description}
                            </Text>
                          </VStack>
                        </HStack>
                      ))}
                    </VStack>
                  </VStack>
                </Card>

                <Card className="bg-yellow-50 border-yellow-200">
                  <HStack space="sm" className="p-4 items-start">
                    <Icon as={AlertCircle} size={16} className="text-yellow-600 mt-0.5" />
                    <Text className="text-yellow-800 text-sm">
                      Don't worry if you don't have all information ready. You can always update your profile later from the settings page.
                    </Text>
                  </HStack>
                </Card>
              </>
            ) : (
              <VStack space="md" className="items-center text-center">
                <Icon as={CheckCircle} size={48} className="text-green-500" />
                <VStack space="sm">
                  <Heading size="md" className="text-gray-900">
                    School Profile Updated!
                  </Heading>
                  <Text className="text-gray-600">
                    Your school profile has been set up successfully. This information will be visible to your teachers, students, and parents.
                  </Text>
                </VStack>
              </VStack>
            )}
          </VStack>
        </ModalBody>
        
        <ModalFooter>
          <HStack space="sm" className="w-full">
            {!isCompleted ? (
              <>
                <Button
                  variant="outline"
                  onPress={handleClose}
                  className="flex-1"
                >
                  <ButtonText>Skip for Now</ButtonText>
                </Button>
                <Button
                  onPress={handleComplete}
                  className="flex-1 bg-blue-600"
                >
                  <ButtonIcon as={Building2} className="text-white mr-2" />
                  <ButtonText className="text-white">Open Settings</ButtonText>
                </Button>
              </>
            ) : (
              <Button
                onPress={handleClose}
                className="w-full bg-green-600"
              >
                <ButtonText className="text-white">Continue</ButtonText>
              </Button>
            )}
          </HStack>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};