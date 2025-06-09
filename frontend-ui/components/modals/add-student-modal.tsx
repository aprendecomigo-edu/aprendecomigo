import { X, User, Calendar, Mail, Phone, GraduationCap } from 'lucide-react-native';
import React, { useState } from 'react';

import apiClient from '@/api/apiClient';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
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
import { ScrollView } from '@/components/ui/scroll-view';
import {
  Select,
  SelectBackdrop,
  SelectContent,
  SelectDragIndicator,
  SelectDragIndicatorWrapper,
  SelectInput,
  SelectItem,
  SelectPortal,
  SelectTrigger,
} from '@/components/ui/select';
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

interface StudentFormData {
  name: string;
  email: string;
  phone_number: string;
  primary_contact: string;
  educational_system_id: number;
  school_year: string;
  birth_date: string;
}

const SCHOOL_YEARS = [
  '1º ano',
  '2º ano',
  '3º ano',
  '4º ano',
  '5º ano',
  '6º ano',
  '7º ano',
  '8º ano',
  '9º ano',
  '10º ano',
  '11º ano',
  '12º ano',
];

// API call to create student
const createStudent = async (studentData: StudentFormData): Promise<void> => {
  try {
    const response = await apiClient.post('/api/accounts/students/create_student/', studentData);
    console.log('Student created successfully:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error creating student:', error);
    throw error;
  }
};

interface AddStudentModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const AddStudentModal = ({ isOpen, onClose, onSuccess }: AddStudentModalProps) => {
  const [formData, setFormData] = useState<StudentFormData>({
    name: '',
    email: '',
    phone_number: '',
    primary_contact: 'email',
    educational_system_id: 1, // Default to 1, you might want to load this dynamically
    school_year: '',
    birth_date: '',
  });
  const [isSaving, setIsSaving] = useState(false);
  const [errors, setErrors] = useState<Partial<StudentFormData>>({});

  const updateFormData = (field: keyof StudentFormData, value: string | number) => {
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: undefined,
      }));
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Partial<StudentFormData> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Nome é obrigatório';
    }

    if (!formData.email.trim()) {
      newErrors.email = 'Email é obrigatório';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Email inválido';
    }

    if (!formData.phone_number.trim()) {
      newErrors.phone_number = 'Telefone é obrigatório';
    }

    if (!formData.school_year) {
      newErrors.school_year = 'Ano escolar é obrigatório';
    }

    if (!formData.birth_date.trim()) {
      newErrors.birth_date = 'Data de nascimento é obrigatória';
    } else if (!/^\d{4}-\d{2}-\d{2}$/.test(formData.birth_date)) {
      newErrors.birth_date = 'Data deve estar no formato AAAA-MM-DD';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSave = async () => {
    if (!validateForm()) {
      return;
    }

    try {
      setIsSaving(true);
      await createStudent(formData);
      onSuccess();
      onClose();
      // Reset form
      setFormData({
        name: '',
        email: '',
        phone_number: '',
        primary_contact: 'email',
        educational_system_id: 1,
        school_year: '',
        birth_date: '',
      });
      setErrors({});
    } catch (error) {
      console.error('Error saving student:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleClose = () => {
    setFormData({
      name: '',
      email: '',
      phone_number: '',
      primary_contact: 'email',
      educational_system_id: 1,
      school_year: '',
      birth_date: '',
    });
    setErrors({});
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose} size="lg">
      <ModalBackdrop />
      <ModalContent>
        <ModalHeader>
          <Heading size="lg">Adicionar Novo Aluno</Heading>
          <ModalCloseButton>
            <Icon as={X} />
          </ModalCloseButton>
        </ModalHeader>

        <ModalBody>
          <ScrollView showsVerticalScrollIndicator={false}>
            <VStack space="lg">
              <Text className="text-gray-600">
                Preencha as informações do aluno para criar um novo cadastro:
              </Text>

              {/* Name Field */}
              <VStack space="xs">
                <Text className="text-sm font-medium text-gray-700">Nome Completo *</Text>
                <Input>
                  <HStack className="items-center px-3">
                    <Icon as={User} size="sm" className="text-gray-400" />
                    <InputField
                      placeholder="João Silva"
                      value={formData.name}
                                             onChangeText={text => updateFormData('name', text)}
                      className="flex-1 ml-2"
                    />
                  </HStack>
                </Input>
                {errors.name && <Text className="text-xs text-red-500">{errors.name}</Text>}
              </VStack>

              {/* Email Field */}
              <VStack space="xs">
                <Text className="text-sm font-medium text-gray-700">Email *</Text>
                <Input>
                  <HStack className="items-center px-3">
                    <Icon as={Mail} size="sm" className="text-gray-400" />
                    <InputField
                      placeholder="joao.silva@example.com"
                      value={formData.email}
                      onChangeText={(text) => updateFormData('email', text)}
                      keyboardType="email-address"
                      autoCapitalize="none"
                      className="flex-1 ml-2"
                    />
                  </HStack>
                </Input>
                {errors.email && <Text className="text-xs text-red-500">{errors.email}</Text>}
              </VStack>

              {/* Phone Field */}
              <VStack space="xs">
                <Text className="text-sm font-medium text-gray-700">Telefone *</Text>
                <Input>
                  <HStack className="items-center px-3">
                    <Icon as={Phone} size="sm" className="text-gray-400" />
                    <InputField
                      placeholder="+351912345678"
                      value={formData.phone_number}
                      onChangeText={(text) => updateFormData('phone_number', text)}
                      keyboardType="phone-pad"
                      className="flex-1 ml-2"
                    />
                  </HStack>
                </Input>
                {errors.phone_number && <Text className="text-xs text-red-500">{errors.phone_number}</Text>}
              </VStack>

              {/* School Year Field */}
              <VStack space="xs">
                <Text className="text-sm font-medium text-gray-700">Ano Escolar *</Text>
                <Select
                  selectedValue={formData.school_year}
                  onValueChange={(value) => updateFormData('school_year', value)}
                >
                  <SelectTrigger>
                    <HStack className="items-center px-3">
                      <Icon as={GraduationCap} size="sm" className="text-gray-400" />
                      <SelectInput
                        placeholder="Selecione o ano escolar"
                        className="flex-1 ml-2"
                      />
                    </HStack>
                  </SelectTrigger>
                  <SelectPortal>
                    <SelectBackdrop />
                    <SelectContent>
                      <SelectDragIndicatorWrapper>
                        <SelectDragIndicator />
                      </SelectDragIndicatorWrapper>
                      {SCHOOL_YEARS.map((year) => (
                        <SelectItem key={year} label={year} value={year} />
                      ))}
                    </SelectContent>
                  </SelectPortal>
                </Select>
                {errors.school_year && <Text className="text-xs text-red-500">{errors.school_year}</Text>}
              </VStack>

              {/* Birth Date Field */}
              <VStack space="xs">
                <Text className="text-sm font-medium text-gray-700">Data de Nascimento *</Text>
                <Input>
                  <HStack className="items-center px-3">
                    <Icon as={Calendar} size="sm" className="text-gray-400" />
                    <InputField
                      placeholder="2005-06-15"
                      value={formData.birth_date}
                      onChangeText={(text) => updateFormData('birth_date', text)}
                      className="flex-1 ml-2"
                    />
                  </HStack>
                </Input>
                <Text className="text-xs text-gray-500">Formato: AAAA-MM-DD</Text>
                {errors.birth_date && <Text className="text-xs text-red-500">{errors.birth_date}</Text>}
              </VStack>

              {/* Info Box */}
              <Box className="rounded-lg p-3" style={{ backgroundColor: COLORS.gray[50] }}>
                <Text className="text-sm text-gray-600">
                  O aluno receberá um email com as instruções para acessar a plataforma.
                </Text>
              </Box>
            </VStack>
          </ScrollView>
        </ModalBody>

        <ModalFooter>
          <HStack space="sm" className="justify-end">
            <Button variant="outline" onPress={handleClose} disabled={isSaving}>
              <ButtonText>Cancelar</ButtonText>
            </Button>
            <Button
              onPress={handleSave}
              disabled={isSaving}
              style={{ backgroundColor: COLORS.primary }}
            >
              {isSaving ? (
                <HStack space="xs" className="items-center">
                  <Spinner size="small" />
                  <ButtonText className="text-white">Salvando...</ButtonText>
                </HStack>
              ) : (
                <ButtonText className="text-white">Criar Aluno</ButtonText>
              )}
            </Button>
          </HStack>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};
