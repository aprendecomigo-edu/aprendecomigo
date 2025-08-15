import { X, Check, Search } from 'lucide-react-native';
import React, { useState } from 'react';

import apiClient from '@/api/apiClient';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Center } from '@/components/ui/center';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Input, InputField } from '@/components/ui/input';
import {
  Modal,
  ModalBackdrop,
  ModalContent,
  ModalHeader,
  ModalCloseButton,
  ModalBody,
  ModalFooter,
} from '@/components/ui/modal';
import { Pressable } from '@/components/ui/pressable';
import { ScrollView } from '@/components/ui/scroll-view';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { useToast } from '@/components/ui/toast';
import { VStack } from '@/components/ui/vstack';

// Color constants
const COLORS = {
  primary: '#156082',
  secondary: '#FFC000',
  white: '#FFFFFF',
  gray: {
    50: '#F9FAFB',
    100: '#F3F4F6',
    200: '#E5E7EB',
    300: '#D1D5DB',
    500: '#6B7280',
    600: '#4B5563',
    700: '#374151',
    900: '#111827',
  },
} as const;

interface Course {
  id: number;
  name: string;
  code: string;
  educational_system: string;
  education_level: string;
  description: string;
  created_at: string;
  updated_at: string;
}

// Real API calls using apiClient
const loadCourses = async (): Promise<Course[]> => {
  try {
    const response = await apiClient.get('/accounts/courses');
    if (__DEV__) {
      console.log('API Response:', response.data);
    } // Debug log

    // Handle paginated response - extract results
    if (response.data && Array.isArray(response.data.results)) {
      return response.data.results;
    } else if (Array.isArray(response.data)) {
      // Fallback for non-paginated response
      return response.data;
    } else {
      if (__DEV__) {
        console.warn('API did not return expected format:', response.data);
      }
      return [];
    }
  } catch (error) {
    console.error('Error loading courses:', error);
    return []; // Return empty array on error
  }
};

const saveTeacherProfile = async (selectedCourseIds: number[]): Promise<void> => {
  try {
    const response = await apiClient.post('/accounts/teachers/onboarding/', {
      course_ids: selectedCourseIds,
    });
    if (__DEV__) {
      console.log('Teacher profile created successfully:', response.data);
    }
    return response.data;
  } catch (error) {
    console.error('Error creating teacher profile:', error);
    throw error;
  }
};

interface AddTeacherModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const AddTeacherModal = ({ isOpen, onClose, onSuccess }: AddTeacherModalProps) => {
  const { showToast } = useToast();
  const [courses, setCourses] = useState<Course[]>([]);
  const [selectedCourseIds, setSelectedCourseIds] = useState<number[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  React.useEffect(() => {
    if (isOpen) {
      loadCoursesData();
    }
  }, [isOpen]);

  const loadCoursesData = async () => {
    try {
      setIsLoading(true);
      const coursesData = await loadCourses();
      setCourses(coursesData);
    } catch (error) {
      console.error('Error loading courses:', error);
      setCourses([]); // Ensure courses is always an array
    } finally {
      setIsLoading(false);
    }
  };

  const filteredCourses = Array.isArray(courses)
    ? courses.filter(
        course =>
          course.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          course.description.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : [];

  const toggleCourseSelection = (courseId: number) => {
    setSelectedCourseIds(prev =>
      prev.includes(courseId) ? prev.filter(id => id !== courseId) : [...prev, courseId]
    );
  };

  const handleSave = async () => {
    if (selectedCourseIds.length === 0) {
      showToast('error', 'Selecione pelo menos uma disciplina');
      return; // Don't save if no courses selected
    }

    try {
      setIsSaving(true);
      await saveTeacherProfile(selectedCourseIds);

      // Show success feedback
      showToast('success', 'Perfil de professor criado com sucesso!');

      // Call success callback and close modal
      onSuccess();
      onClose();

      // Reset form
      setSelectedCourseIds([]);
      setSearchQuery('');
    } catch (error: any) {
      console.error('Error saving teacher profile:', error);

      // Show error feedback
      const errorMessage =
        error.response?.data?.message ||
        error.response?.data?.detail ||
        'Erro ao criar perfil de professor. Tente novamente.';
      showToast('error', errorMessage);
    } finally {
      setIsSaving(false);
    }
  };

  const handleClose = () => {
    setSelectedCourseIds([]);
    setSearchQuery('');
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose} size="lg">
      <ModalBackdrop />
      <ModalContent>
        <ModalHeader>
          <Heading size="lg">Adicionar-me como Professor</Heading>
          <ModalCloseButton>
            <Icon as={X} />
          </ModalCloseButton>
        </ModalHeader>

        <ModalBody>
          <VStack space="md">
            <Text className="text-gray-600">
              Selecione as disciplinas que você ensina para criar seu perfil de professor:
            </Text>

            {/* Search Input */}
            <Box>
              <Input>
                <HStack className="items-center px-3">
                  <Icon as={Search} size="sm" className="text-gray-400" />
                  <InputField
                    placeholder="Buscar disciplinas..."
                    value={searchQuery}
                    onChangeText={setSearchQuery}
                    className="flex-1 ml-2"
                  />
                </HStack>
              </Input>
            </Box>

            {isLoading ? (
              <Center className="py-8">
                <VStack className="items-center" space="md">
                  <Spinner size="large" />
                  <Text className="text-gray-500">Carregando disciplinas...</Text>
                </VStack>
              </Center>
            ) : (
              <>
                {/* Results counter */}
                {searchQuery && (
                  <Text className="text-sm text-gray-500">
                    {filteredCourses.length} disciplina(s) encontrada(s)
                  </Text>
                )}

                <ScrollView style={{ maxHeight: 300 }}>
                  <VStack space="sm">
                    {filteredCourses.length === 0 && searchQuery ? (
                      <Center className="py-8">
                        <VStack className="items-center" space="xs">
                          <Icon as={Search} size="lg" className="text-gray-400" />
                          <Text className="text-gray-500">Nenhuma disciplina encontrada</Text>
                          <Text className="text-gray-400 text-sm text-center">
                            Tente buscar por outro termo
                          </Text>
                        </VStack>
                      </Center>
                    ) : (
                      filteredCourses.map(course => {
                        const isSelected = selectedCourseIds.includes(course.id);
                        return (
                          <Pressable
                            key={course.id}
                            className="rounded-lg border p-3"
                            style={{
                              backgroundColor: isSelected ? COLORS.primary : COLORS.white,
                              borderColor: isSelected ? COLORS.primary : COLORS.gray[200],
                            }}
                            onPress={() => toggleCourseSelection(course.id)}
                          >
                            <HStack className="items-center justify-between">
                              <VStack className="flex-1">
                                <HStack className="items-center mb-1" space="xs">
                                  <Text
                                    className={`font-medium ${
                                      isSelected ? 'text-white' : 'text-gray-900'
                                    }`}
                                  >
                                    {course.name}
                                  </Text>
                                  <Text
                                    className={`text-xs px-2 py-1 rounded ${
                                      isSelected
                                        ? 'text-white bg-white bg-opacity-20'
                                        : 'text-gray-500 bg-gray-100'
                                    }`}
                                  >
                                    {course.code}
                                  </Text>
                                </HStack>
                                <Text
                                  className={`text-sm ${
                                    isSelected ? 'text-white' : 'text-gray-600'
                                  }`}
                                >
                                  {course.description}
                                </Text>
                              </VStack>
                              {isSelected && (
                                <Icon as={Check} size="sm" className="text-white ml-2" />
                              )}
                            </HStack>
                          </Pressable>
                        );
                      })
                    )}
                  </VStack>
                </ScrollView>
              </>
            )}

            {selectedCourseIds.length > 0 && (
              <Box className="rounded-lg p-3" style={{ backgroundColor: COLORS.gray[50] }}>
                <Text className="text-sm text-gray-600">
                  {selectedCourseIds.length} disciplina(s) selecionada(s)
                </Text>
              </Box>
            )}
          </VStack>
        </ModalBody>

        <ModalFooter>
          <HStack space="sm" className="justify-end">
            <Button variant="outline" onPress={handleClose} disabled={isSaving}>
              <ButtonText>Cancelar</ButtonText>
            </Button>
            <Button
              onPress={handleSave}
              disabled={selectedCourseIds.length === 0 || isSaving}
              style={{ backgroundColor: COLORS.primary }}
            >
              {isSaving ? (
                <HStack space="xs" className="items-center">
                  <Spinner size="small" />
                  <ButtonText className="text-white">Salvando...</ButtonText>
                </HStack>
              ) : (
                <ButtonText className="text-white">Salvar Perfil</ButtonText>
              )}
            </Button>
          </HStack>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};
