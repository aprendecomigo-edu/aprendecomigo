import { X, User, Calendar, Mail, Phone, GraduationCap } from 'lucide-react-native';
import React, { useState } from 'react';

import { useAuth } from '@/api/authContext';
import {
  createStudent,
  CreateStudentData,
  getEducationalSystems,
  EducationalSystem,
} from '@/api/userApi';
import { AuthGuard } from '@/components/auth/AuthGuard';
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

interface StudentFormData {
  name: string;
  email: string;
  phone_number: string;
  primary_contact: 'email' | 'phone';
  educational_system_id: number;
  school_year: string;
  birth_date: string;
  address: string;
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

// Helper function to get current school ID - throws error if not found for security
const getCurrentSchoolId = (userProfile: any): number => {
  // Get the first school where user has admin privileges
  if (userProfile?.school_memberships) {
    const adminMembership = userProfile.school_memberships.find(
      (membership: any) =>
        membership.is_active &&
        (membership.role === 'school_owner' || membership.role === 'school_admin')
    );
    if (adminMembership?.school?.id) {
      return adminMembership.school.id;
    }
  }

  // Security: throw error instead of fallback to prevent unauthorized access
  throw new Error(
    'Unable to determine school context. Please ensure you have proper school administration privileges.'
  );
};

interface AddStudentModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const AddStudentModal = ({ isOpen, onClose, onSuccess }: AddStudentModalProps) => {
  const { showToast } = useToast();
  const { userProfile } = useAuth();

  const [formData, setFormData] = useState<StudentFormData>({
    name: '',
    email: '',
    phone_number: '',
    primary_contact: 'email',
    educational_system_id: 1, // Default to Portugal system
    school_year: '',
    birth_date: '',
    address: '',
  });
  const [isSaving, setIsSaving] = useState(false);
  const [errors, setErrors] = useState<Partial<StudentFormData>>({});
  const [educationalSystems, setEducationalSystems] = useState<EducationalSystem[]>([]);

  // Load educational systems on mount
  React.useEffect(() => {
    const loadEducationalSystems = async () => {
      try {
        const systems = await getEducationalSystems();
        setEducationalSystems(systems);
      } catch (error) {
        console.error('Failed to load educational systems:', error);
      }
    };

    if (isOpen) {
      loadEducationalSystems();
    }
  }, [isOpen]);

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

  // Input sanitization helper
  const sanitizeInput = (input: string): string => {
    return input.trim().replace(/<[^>]*>/g, ''); // Remove HTML tags and trim
  };

  const validateForm = (): boolean => {
    const newErrors: Partial<StudentFormData> = {};

    // Name validation with length limits
    const sanitizedName = sanitizeInput(formData.name);
    if (!sanitizedName) {
      newErrors.name = 'Nome é obrigatório';
    } else if (sanitizedName.length < 2) {
      newErrors.name = 'Nome deve ter pelo menos 2 caracteres';
    } else if (sanitizedName.length > 100) {
      newErrors.name = 'Nome deve ter no máximo 100 caracteres';
    } else if (!/^[a-zA-ZÀ-ÿ\s'-]+$/.test(sanitizedName)) {
      newErrors.name = 'Nome deve conter apenas letras, espaços, hífens e apostrofos';
    }

    // Email validation with enhanced patterns
    const sanitizedEmail = sanitizeInput(formData.email.toLowerCase());
    if (!sanitizedEmail) {
      newErrors.email = 'Email é obrigatório';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(sanitizedEmail)) {
      newErrors.email = 'Formato de email inválido';
    } else if (sanitizedEmail.length > 254) {
      newErrors.email = 'Email muito longo (máximo 254 caracteres)';
    }

    // Phone number validation
    const sanitizedPhone = sanitizeInput(formData.phone_number);
    if (!sanitizedPhone) {
      newErrors.phone_number = 'Telefone é obrigatório';
    } else if (!/^[\+]?[0-9\s\-\(\)]{8,20}$/.test(sanitizedPhone)) {
      newErrors.phone_number = 'Formato de telefone inválido (8-20 dígitos)';
    }

    // School year validation
    if (!formData.school_year) {
      newErrors.school_year = 'Ano escolar é obrigatório';
    }

    // Birth date validation with age constraints
    if (!formData.birth_date.trim()) {
      newErrors.birth_date = 'Data de nascimento é obrigatória';
    } else if (!/^\d{4}-\d{2}-\d{2}$/.test(formData.birth_date)) {
      newErrors.birth_date = 'Data deve estar no formato AAAA-MM-DD';
    } else {
      const birthDate = new Date(formData.birth_date);
      const today = new Date();
      const age = today.getFullYear() - birthDate.getFullYear();

      if (birthDate > today) {
        newErrors.birth_date = 'Data de nascimento não pode ser no futuro';
      } else if (age < 5 || age > 25) {
        newErrors.birth_date = 'Idade deve estar entre 5 e 25 anos';
      }
    }

    // Address validation (optional but with limits)
    if (formData.address.trim() && formData.address.length > 500) {
      newErrors.address = 'Endereço deve ter no máximo 500 caracteres';
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

      // Validate school context first
      let schoolId: number;
      try {
        schoolId = getCurrentSchoolId(userProfile);
      } catch (schoolError: any) {
        showToast('error', schoolError.message || 'Erro ao validar permissões de escola');
        return;
      }

      // Sanitize all form data before submission
      const createData: CreateStudentData = {
        name: sanitizeInput(formData.name),
        email: sanitizeInput(formData.email.toLowerCase()),
        phone_number: sanitizeInput(formData.phone_number),
        primary_contact: formData.primary_contact,
        educational_system_id: formData.educational_system_id,
        school_year: formData.school_year,
        birth_date: formData.birth_date.trim(),
        address: sanitizeInput(formData.address),
        school_id: schoolId,
      };

      await createStudent(createData);

      // Show success feedback
      showToast('success', 'Aluno criado com sucesso!');

      // Call success callback and close modal
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
        address: '',
      });
      setErrors({});
    } catch (error: any) {
      console.error('Error saving student:', error);

      // Show specific error feedback based on error type
      let errorMessage = 'Erro ao criar aluno. Tente novamente.';

      if (error.response?.status === 403) {
        errorMessage = 'Você não tem permissão para criar alunos nesta escola.';
      } else if (error.response?.status === 401) {
        errorMessage = 'Sua sessão expirou. Faça login novamente.';
      } else if (error.response?.status === 400) {
        errorMessage =
          error.response?.data?.message ||
          error.response?.data?.detail ||
          'Dados inválidos. Verifique as informações fornecidas.';
      } else if (error.response?.status >= 500) {
        errorMessage = 'Erro interno do servidor. Tente novamente em alguns minutos.';
      } else if (error.response?.data?.message || error.response?.data?.detail) {
        errorMessage = error.response.data.message || error.response.data.detail;
      }

      showToast('error', errorMessage);
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
      address: '',
    });
    setErrors({});
    onClose();
  };

  return (
    <AuthGuard requiredRoles={['school_owner', 'school_admin']}>
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
                        onChangeText={text => updateFormData('email', text)}
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
                        onChangeText={text => updateFormData('phone_number', text)}
                        keyboardType="phone-pad"
                        className="flex-1 ml-2"
                      />
                    </HStack>
                  </Input>
                  {errors.phone_number && (
                    <Text className="text-xs text-red-500">{errors.phone_number}</Text>
                  )}
                </VStack>

                {/* School Year Field */}
                <VStack space="xs">
                  <Text className="text-sm font-medium text-gray-700">Ano Escolar *</Text>
                  <Select
                    selectedValue={formData.school_year}
                    onValueChange={value => updateFormData('school_year', value)}
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
                        {SCHOOL_YEARS.map(year => (
                          <SelectItem key={year} label={year} value={year} />
                        ))}
                      </SelectContent>
                    </SelectPortal>
                  </Select>
                  {errors.school_year && (
                    <Text className="text-xs text-red-500">{errors.school_year}</Text>
                  )}
                </VStack>

                {/* Educational System Field */}
                <VStack space="xs">
                  <Text className="text-sm font-medium text-gray-700">Sistema Educacional</Text>
                  <Select
                    selectedValue={formData.educational_system_id?.toString()}
                    onValueChange={value =>
                      updateFormData('educational_system_id', parseInt(value))
                    }
                  >
                    <SelectTrigger>
                      <SelectInput placeholder="Selecione o sistema educacional" />
                    </SelectTrigger>
                    <SelectPortal>
                      <SelectBackdrop />
                      <SelectContent>
                        <SelectDragIndicatorWrapper>
                          <SelectDragIndicator />
                        </SelectDragIndicatorWrapper>
                        {educationalSystems.map(system => (
                          <SelectItem
                            key={system.id}
                            label={system.name}
                            value={system.id.toString()}
                          />
                        ))}
                      </SelectContent>
                    </SelectPortal>
                  </Select>
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
                        onChangeText={text => updateFormData('birth_date', text)}
                        className="flex-1 ml-2"
                      />
                    </HStack>
                  </Input>
                  <Text className="text-xs text-gray-500">Formato: AAAA-MM-DD</Text>
                  {errors.birth_date && (
                    <Text className="text-xs text-red-500">{errors.birth_date}</Text>
                  )}
                </VStack>

                {/* Address Field */}
                <VStack space="xs">
                  <Text className="text-sm font-medium text-gray-700">Endereço</Text>
                  <Input>
                    <InputField
                      placeholder="Rua, número, código postal e localidade"
                      value={formData.address}
                      onChangeText={text => updateFormData('address', text)}
                      multiline
                    />
                  </Input>
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
              <Button
                variant="outline"
                onPress={handleClose}
                disabled={isSaving}
                accessibilityLabel="Cancelar criação de aluno"
                accessibilityHint="Toque para fechar o formulário sem salvar"
              >
                <ButtonText>Cancelar</ButtonText>
              </Button>
              <Button
                onPress={handleSave}
                disabled={isSaving}
                style={{ backgroundColor: COLORS.primary }}
                accessibilityLabel={isSaving ? 'Salvando aluno...' : 'Criar aluno'}
                accessibilityHint={
                  isSaving ? 'Aguarde enquanto o aluno é criado' : 'Toque para salvar o novo aluno'
                }
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
    </AuthGuard>
  );
};
