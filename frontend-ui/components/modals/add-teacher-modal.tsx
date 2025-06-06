import { X, Check, Search } from 'lucide-react-native';
import React, { useState } from 'react';

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
  id: string;
  name: string;
  description: string;
}

// Mock API calls - replace with real API when backend is ready
const mockCourses: Course[] = [
  { id: '1', name: 'Matemática', description: 'Ensino fundamental e médio' },
  { id: '2', name: 'Português', description: 'Língua portuguesa e literatura' },
  { id: '3', name: 'História', description: 'História geral e do Brasil' },
  { id: '4', name: 'Geografia', description: 'Geografia física e humana' },
  { id: '5', name: 'Ciências', description: 'Ciências naturais' },
  { id: '6', name: 'Inglês', description: 'Língua inglesa' },
  { id: '7', name: 'Educação Física', description: 'Atividades físicas e esportes' },
  { id: '8', name: 'Artes', description: 'Artes visuais e música' },
  { id: '9', name: 'Química', description: 'Química geral e orgânica' },
  { id: '10', name: 'Física', description: 'Mecânica, termodinâmica e eletromagnetismo' },
  { id: '11', name: 'Biologia', description: 'Ciências da vida' },
  { id: '12', name: 'Filosofia', description: 'Pensamento crítico e ética' },
];

const loadCourses = async (): Promise<Course[]> => {
  // Mock API call - simulate network delay
  await new Promise(resolve => setTimeout(resolve, 1000));
  return mockCourses;
};

const saveTeacherProfile = async (selectedCourseIds: string[]): Promise<void> => {
  // Mock API call - simulate network delay
  await new Promise(resolve => setTimeout(resolve, 1500));
  console.log('Saving teacher profile with courses:', selectedCourseIds);
  // TODO: Replace with actual API call when backend is ready
};

interface AddTeacherModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const AddTeacherModal = ({ isOpen, onClose, onSuccess }: AddTeacherModalProps) => {
  const [courses, setCourses] = useState<Course[]>([]);
  const [selectedCourseIds, setSelectedCourseIds] = useState<string[]>([]);
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
    } finally {
      setIsLoading(false);
    }
  };

  const filteredCourses = courses.filter(
    course =>
      course.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      course.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const toggleCourseSelection = (courseId: string) => {
    setSelectedCourseIds(prev =>
      prev.includes(courseId) ? prev.filter(id => id !== courseId) : [...prev, courseId]
    );
  };

  const handleSave = async () => {
    if (selectedCourseIds.length === 0) {
      return; // Don't save if no courses selected
    }

    try {
      setIsSaving(true);
      await saveTeacherProfile(selectedCourseIds);
      onSuccess();
      onClose();
      // Reset form
      setSelectedCourseIds([]);
      setSearchQuery('');
    } catch (error) {
      console.error('Error saving teacher profile:', error);
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
                                <Text
                                  className={`font-medium ${
                                    isSelected ? 'text-white' : 'text-gray-900'
                                  }`}
                                >
                                  {course.name}
                                </Text>
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
