import { useLocalSearchParams, useRouter } from 'expo-router';
import {
  ArrowLeft,
  Edit,
  Save,
  X,
  User,
  Mail,
  Phone,
  Calendar,
  MapPin,
  GraduationCap,
  Users,
  AlertCircle,
} from 'lucide-react-native';
import React, { useState, useEffect } from 'react';

import {
  StudentProfile,
  getStudentById,
  updateStudent,
  UpdateStudentData,
  EducationalSystem,
} from '@/api/userApi';
import { MainLayout } from '@/components/layouts/main-layout';
import { Badge, BadgeText } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Center } from '@/components/ui/center';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Input, InputField } from '@/components/ui/input';
import { Pressable } from '@/components/ui/pressable';
import { ScrollView } from '@/components/ui/scroll-view';
import {
  Select,
  SelectBackdrop,
  SelectContent,
  SelectDragIndicator,
  SelectDragIndicatorWrapper,
  SelectIcon,
  SelectInput,
  SelectItem,
  SelectPortal,
  SelectTrigger,
} from '@/components/ui/select';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { useToast } from '@/components/ui/toast';
import { VStack } from '@/components/ui/vstack';
import { useStudents } from '@/hooks/useStudents';

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
  success: '#10B981',
  warning: '#F59E0B',
  error: '#EF4444',
} as const;

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

interface StudentProfileHeaderProps {
  student: StudentProfile;
  isEditing: boolean;
  onEditToggle: () => void;
  onSave: () => void;
  isSaving: boolean;
}

const StudentProfileHeader: React.FC<StudentProfileHeaderProps> = ({
  student,
  isEditing,
  onEditToggle,
  onSave,
  isSaving,
}) => {
  const router = useRouter();

  const getStatusBadge = (status?: string) => {
    switch (status) {
      case 'active':
        return (
          <Badge style={{ backgroundColor: `${COLORS.success}20` }}>
            <BadgeText style={{ color: COLORS.success }}>Ativo</BadgeText>
          </Badge>
        );
      case 'inactive':
        return (
          <Badge style={{ backgroundColor: `${COLORS.warning}20` }}>
            <BadgeText style={{ color: COLORS.warning }}>Inativo</BadgeText>
          </Badge>
        );
      case 'graduated':
        return (
          <Badge style={{ backgroundColor: `${COLORS.primary}20` }}>
            <BadgeText style={{ color: COLORS.primary }}>Formado</BadgeText>
          </Badge>
        );
      default:
        return (
          <Badge style={{ backgroundColor: `${COLORS.success}20` }}>
            <BadgeText style={{ color: COLORS.success }}>Ativo</BadgeText>
          </Badge>
        );
    }
  };

  return (
    <VStack space="md" className="p-6 border-b border-gray-200">
      {/* Breadcrumb */}
      <HStack className="items-center" space="sm">
        <Pressable onPress={() => router.back()}>
          <HStack className="items-center" space="xs">
            <Icon as={ArrowLeft} size="sm" className="text-gray-600" />
            <Text className="text-gray-600">Voltar para Lista</Text>
          </HStack>
        </Pressable>
      </HStack>

      {/* Profile Header */}
      <HStack className="items-center justify-between">
        <HStack className="items-center" space="md">
          <Box className="w-16 h-16 rounded-full bg-primary-100 items-center justify-center">
            <Icon as={User} size="lg" style={{ color: COLORS.primary }} />
          </Box>
          <VStack space="xs">
            <Heading size="xl" className="text-gray-900">
              {student.user.name}
            </Heading>
            <HStack space="sm" className="items-center">
              <Text className="text-gray-600">{student.user.email}</Text>
              {getStatusBadge(student.status)}
            </HStack>
          </VStack>
        </HStack>

        <HStack space="sm">
          {isEditing ? (
            <>
              <Button variant="outline" onPress={onEditToggle} disabled={isSaving}>
                <HStack space="xs" className="items-center">
                  <Icon as={X} size="sm" />
                  <ButtonText>Cancelar</ButtonText>
                </HStack>
              </Button>
              <Button
                onPress={onSave}
                disabled={isSaving}
                style={{ backgroundColor: COLORS.primary }}
              >
                {isSaving ? (
                  <HStack space="xs" className="items-center">
                    <Spinner size="small" />
                    <ButtonText className="text-white">Salvando...</ButtonText>
                  </HStack>
                ) : (
                  <HStack space="xs" className="items-center">
                    <Icon as={Save} size="sm" className="text-white" />
                    <ButtonText className="text-white">Salvar</ButtonText>
                  </HStack>
                )}
              </Button>
            </>
          ) : (
            <Button variant="outline" onPress={onEditToggle}>
              <HStack space="xs" className="items-center">
                <Icon as={Edit} size="sm" />
                <ButtonText>Editar</ButtonText>
              </HStack>
            </Button>
          )}
        </HStack>
      </HStack>
    </VStack>
  );
};

interface StudentInfoCardProps {
  student: StudentProfile;
  isEditing: boolean;
  formData: any;
  onFormDataChange: (field: string, value: string) => void;
  educationalSystems: EducationalSystem[];
}

const StudentInfoCard: React.FC<StudentInfoCardProps> = ({
  student,
  isEditing,
  formData,
  onFormDataChange,
  educationalSystems,
}) => {
  if (isEditing) {
    return (
      <Box
        className="rounded-lg border border-gray-200 p-6"
        style={{ backgroundColor: COLORS.white }}
      >
        <VStack space="lg">
          <Heading size="lg" className="text-gray-900">
            Informações do Aluno
          </Heading>

          {/* Name */}
          <VStack space="xs">
            <Text className="text-sm font-medium text-gray-700">Nome Completo</Text>
            <Input>
              <HStack className="items-center px-3">
                <Icon as={User} size="sm" className="text-gray-400" />
                <InputField
                  value={formData.name}
                  onChangeText={text => onFormDataChange('name', text)}
                  className="flex-1 ml-2"
                />
              </HStack>
            </Input>
          </VStack>

          {/* Email */}
          <VStack space="xs">
            <Text className="text-sm font-medium text-gray-700">Email</Text>
            <Input>
              <HStack className="items-center px-3">
                <Icon as={Mail} size="sm" className="text-gray-400" />
                <InputField
                  value={formData.email}
                  onChangeText={text => onFormDataChange('email', text)}
                  keyboardType="email-address"
                  autoCapitalize="none"
                  className="flex-1 ml-2"
                />
              </HStack>
            </Input>
          </VStack>

          {/* Phone */}
          <VStack space="xs">
            <Text className="text-sm font-medium text-gray-700">Telefone</Text>
            <Input>
              <HStack className="items-center px-3">
                <Icon as={Phone} size="sm" className="text-gray-400" />
                <InputField
                  value={formData.phone_number}
                  onChangeText={text => onFormDataChange('phone_number', text)}
                  keyboardType="phone-pad"
                  className="flex-1 ml-2"
                />
              </HStack>
            </Input>
          </VStack>

          {/* School Year */}
          <VStack space="xs">
            <Text className="text-sm font-medium text-gray-700">Ano Escolar</Text>
            <Select
              selectedValue={formData.school_year}
              onValueChange={value => onFormDataChange('school_year', value)}
            >
              <SelectTrigger>
                <HStack className="items-center px-3">
                  <Icon as={GraduationCap} size="sm" className="text-gray-400" />
                  <SelectInput placeholder="Selecione o ano escolar" className="flex-1 ml-2" />
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
          </VStack>

          {/* Educational System */}
          <VStack space="xs">
            <Text className="text-sm font-medium text-gray-700">Sistema Educacional</Text>
            <Select
              selectedValue={formData.educational_system_id?.toString()}
              onValueChange={value => onFormDataChange('educational_system_id', value)}
            >
              <SelectTrigger>
                <SelectInput placeholder="Selecione o sistema educacional" />
                <SelectIcon />
              </SelectTrigger>
              <SelectPortal>
                <SelectBackdrop />
                <SelectContent>
                  <SelectDragIndicatorWrapper>
                    <SelectDragIndicator />
                  </SelectDragIndicatorWrapper>
                  {educationalSystems.map(system => (
                    <SelectItem key={system.id} label={system.name} value={system.id.toString()} />
                  ))}
                </SelectContent>
              </SelectPortal>
            </Select>
          </VStack>

          {/* Birth Date */}
          <VStack space="xs">
            <Text className="text-sm font-medium text-gray-700">Data de Nascimento</Text>
            <Input>
              <HStack className="items-center px-3">
                <Icon as={Calendar} size="sm" className="text-gray-400" />
                <InputField
                  value={formData.birth_date}
                  onChangeText={text => onFormDataChange('birth_date', text)}
                  placeholder="AAAA-MM-DD"
                  className="flex-1 ml-2"
                />
              </HStack>
            </Input>
          </VStack>

          {/* Address */}
          <VStack space="xs">
            <Text className="text-sm font-medium text-gray-700">Endereço</Text>
            <Input>
              <HStack className="items-center px-3">
                <Icon as={MapPin} size="sm" className="text-gray-400" />
                <InputField
                  value={formData.address}
                  onChangeText={text => onFormDataChange('address', text)}
                  multiline
                  className="flex-1 ml-2"
                />
              </HStack>
            </Input>
          </VStack>

          {/* Status */}
          <VStack space="xs">
            <Text className="text-sm font-medium text-gray-700">Status</Text>
            <Select
              selectedValue={formData.status}
              onValueChange={value => onFormDataChange('status', value)}
            >
              <SelectTrigger>
                <SelectInput placeholder="Selecione o status" />
                <SelectIcon />
              </SelectTrigger>
              <SelectPortal>
                <SelectBackdrop />
                <SelectContent>
                  <SelectDragIndicatorWrapper>
                    <SelectDragIndicator />
                  </SelectDragIndicatorWrapper>
                  <SelectItem label="Ativo" value="active" />
                  <SelectItem label="Inativo" value="inactive" />
                  <SelectItem label="Formado" value="graduated" />
                </SelectContent>
              </SelectPortal>
            </Select>
          </VStack>
        </VStack>
      </Box>
    );
  }

  return (
    <Box
      className="rounded-lg border border-gray-200 p-6"
      style={{ backgroundColor: COLORS.white }}
    >
      <VStack space="lg">
        <Heading size="lg" className="text-gray-900">
          Informações do Aluno
        </Heading>

        <VStack space="md">
          <HStack className="justify-between">
            <Text className="text-gray-600">Nome:</Text>
            <Text className="font-medium text-gray-900">{student.user.name}</Text>
          </HStack>

          <HStack className="justify-between">
            <Text className="text-gray-600">Email:</Text>
            <Text className="font-medium text-gray-900">{student.user.email}</Text>
          </HStack>

          <HStack className="justify-between">
            <Text className="text-gray-600">Telefone:</Text>
            <Text className="font-medium text-gray-900">{student.user.phone_number || 'N/A'}</Text>
          </HStack>

          <HStack className="justify-between">
            <Text className="text-gray-600">Ano Escolar:</Text>
            <Text className="font-medium text-gray-900">{student.school_year}</Text>
          </HStack>

          <HStack className="justify-between">
            <Text className="text-gray-600">Sistema Educacional:</Text>
            <Text className="font-medium text-gray-900">
              {student.educational_system?.name || 'N/A'}
            </Text>
          </HStack>

          <HStack className="justify-between">
            <Text className="text-gray-600">Data de Nascimento:</Text>
            <Text className="font-medium text-gray-900">
              {student.birth_date
                ? new Date(student.birth_date).toLocaleDateString('pt-PT')
                : 'N/A'}
            </Text>
          </HStack>

          {student.address && (
            <VStack space="xs">
              <Text className="text-gray-600">Endereço:</Text>
              <Text className="font-medium text-gray-900">{student.address}</Text>
            </VStack>
          )}
        </VStack>
      </VStack>
    </Box>
  );
};

interface ParentContactCardProps {
  student: StudentProfile;
  isEditing: boolean;
  formData: any;
  onFormDataChange: (field: string, value: any) => void;
}

const ParentContactCard: React.FC<ParentContactCardProps> = ({
  student,
  isEditing,
  formData,
  onFormDataChange,
}) => {
  const updateParentContact = (field: string, value: string) => {
    onFormDataChange('parent_contact', {
      ...formData.parent_contact,
      [field]: value,
    });
  };

  if (isEditing) {
    return (
      <Box
        className="rounded-lg border border-gray-200 p-6"
        style={{ backgroundColor: COLORS.white }}
      >
        <VStack space="lg">
          <Heading size="lg" className="text-gray-900">
            Contato dos Pais/Responsáveis
          </Heading>

          <VStack space="md">
            {/* Parent Name */}
            <VStack space="xs">
              <Text className="text-sm font-medium text-gray-700">Nome do Responsável</Text>
              <Input>
                <InputField
                  value={formData.parent_contact?.name || ''}
                  onChangeText={text => updateParentContact('name', text)}
                  placeholder="Nome completo"
                />
              </Input>
            </VStack>

            {/* Parent Email */}
            <VStack space="xs">
              <Text className="text-sm font-medium text-gray-700">Email do Responsável</Text>
              <Input>
                <InputField
                  value={formData.parent_contact?.email || ''}
                  onChangeText={text => updateParentContact('email', text)}
                  placeholder="email@exemplo.com"
                  keyboardType="email-address"
                  autoCapitalize="none"
                />
              </Input>
            </VStack>

            {/* Parent Phone */}
            <VStack space="xs">
              <Text className="text-sm font-medium text-gray-700">Telefone do Responsável</Text>
              <Input>
                <InputField
                  value={formData.parent_contact?.phone || ''}
                  onChangeText={text => updateParentContact('phone', text)}
                  placeholder="+351912345678"
                  keyboardType="phone-pad"
                />
              </Input>
            </VStack>

            {/* Relationship */}
            <VStack space="xs">
              <Text className="text-sm font-medium text-gray-700">Relação</Text>
              <Select
                selectedValue={formData.parent_contact?.relationship || ''}
                onValueChange={value => updateParentContact('relationship', value)}
              >
                <SelectTrigger>
                  <SelectInput placeholder="Selecione a relação" />
                  <SelectIcon />
                </SelectTrigger>
                <SelectPortal>
                  <SelectBackdrop />
                  <SelectContent>
                    <SelectDragIndicatorWrapper>
                      <SelectDragIndicator />
                    </SelectDragIndicatorWrapper>
                    <SelectItem label="Pai" value="father" />
                    <SelectItem label="Mãe" value="mother" />
                    <SelectItem label="Responsável Legal" value="guardian" />
                    <SelectItem label="Outro" value="other" />
                  </SelectContent>
                </SelectPortal>
              </Select>
            </VStack>
          </VStack>
        </VStack>
      </Box>
    );
  }

  return (
    <Box
      className="rounded-lg border border-gray-200 p-6"
      style={{ backgroundColor: COLORS.white }}
    >
      <VStack space="lg">
        <Heading size="lg" className="text-gray-900">
          Contato dos Pais/Responsáveis
        </Heading>

        {student.parent_contact ? (
          <VStack space="md">
            <HStack className="justify-between">
              <Text className="text-gray-600">Nome:</Text>
              <Text className="font-medium text-gray-900">{student.parent_contact.name}</Text>
            </HStack>

            <HStack className="justify-between">
              <Text className="text-gray-600">Email:</Text>
              <Text className="font-medium text-gray-900">{student.parent_contact.email}</Text>
            </HStack>

            <HStack className="justify-between">
              <Text className="text-gray-600">Telefone:</Text>
              <Text className="font-medium text-gray-900">{student.parent_contact.phone}</Text>
            </HStack>

            <HStack className="justify-between">
              <Text className="text-gray-600">Relação:</Text>
              <Text className="font-medium text-gray-900">
                {student.parent_contact.relationship === 'father'
                  ? 'Pai'
                  : student.parent_contact.relationship === 'mother'
                  ? 'Mãe'
                  : student.parent_contact.relationship === 'guardian'
                  ? 'Responsável Legal'
                  : 'Outro'}
              </Text>
            </HStack>
          </VStack>
        ) : (
          <Box className="p-4 rounded-lg bg-gray-50">
            <Center>
              <VStack className="items-center" space="sm">
                <Icon as={Users} className="text-gray-400" />
                <Text className="text-gray-500">Nenhum contato de responsável registrado</Text>
              </VStack>
            </Center>
          </Box>
        )}
      </VStack>
    </Box>
  );
};

export default function StudentProfilePage() {
  const { id, edit } = useLocalSearchParams<{ id: string; edit?: string }>();
  const router = useRouter();
  const { showToast } = useToast();
  const { educationalSystems } = useStudents({ autoLoad: false });

  // State
  const [student, setStudent] = useState<StudentProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(edit === 'true');
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState<any>({});

  // Load student data
  useEffect(() => {
    const loadStudent = async () => {
      if (!id) return;

      try {
        setIsLoading(true);
        setError(null);
        const studentData = await getStudentById(parseInt(id));
        setStudent(studentData);

        // Initialize form data
        setFormData({
          name: studentData.user.name,
          email: studentData.user.email,
          phone_number: studentData.user.phone_number || '',
          educational_system_id: studentData.educational_system?.id,
          school_year: studentData.school_year,
          birth_date: studentData.birth_date,
          address: studentData.address || '',
          status: studentData.status || 'active',
          parent_contact: studentData.parent_contact || {
            name: '',
            email: '',
            phone: '',
            relationship: '',
          },
        });
      } catch (err: any) {
        console.error('Failed to load student:', err);
        setError(err.message || 'Falha ao carregar dados do aluno');
      } finally {
        setIsLoading(false);
      }
    };

    loadStudent();
  }, [id]);

  // Handle form data change
  const handleFormDataChange = (field: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }));
  };

  // Handle edit toggle
  const handleEditToggle = () => {
    if (isEditing) {
      // Reset form data when canceling edit
      if (student) {
        setFormData({
          name: student.user.name,
          email: student.user.email,
          phone_number: student.user.phone_number || '',
          educational_system_id: student.educational_system?.id,
          school_year: student.school_year,
          birth_date: student.birth_date,
          address: student.address || '',
          status: student.status || 'active',
          parent_contact: student.parent_contact || {
            name: '',
            email: '',
            phone: '',
            relationship: '',
          },
        });
      }
    }
    setIsEditing(!isEditing);
  };

  // Handle save
  const handleSave = async () => {
    if (!student) return;

    try {
      setIsSaving(true);

      const updateData: UpdateStudentData = {
        name: formData.name,
        email: formData.email,
        phone_number: formData.phone_number,
        educational_system_id: parseInt(formData.educational_system_id),
        school_year: formData.school_year,
        birth_date: formData.birth_date,
        address: formData.address,
        status: formData.status,
        parent_contact: formData.parent_contact.name ? formData.parent_contact : undefined,
      };

      const updatedStudent = await updateStudent(student.id, updateData);
      setStudent(updatedStudent);
      setIsEditing(false);
      showToast('success', 'Perfil do aluno atualizado com sucesso');
    } catch (err: any) {
      console.error('Failed to update student:', err);
      showToast('error', err.message || 'Erro ao atualizar perfil do aluno');
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <MainLayout>
        <Box className="flex-1" style={{ backgroundColor: COLORS.gray[50] }}>
          <Center className="flex-1">
            <VStack className="items-center" space="md">
              <Spinner size="large" />
              <Text className="text-gray-500">Carregando perfil do aluno...</Text>
            </VStack>
          </Center>
        </Box>
      </MainLayout>
    );
  }

  if (error || !student) {
    return (
      <MainLayout>
        <Box className="flex-1" style={{ backgroundColor: COLORS.gray[50] }}>
          <Center className="flex-1">
            <VStack className="items-center max-w-sm mx-auto" space="lg">
              <Icon as={AlertCircle} size="xl" className="text-red-500" />
              <VStack className="items-center" space="sm">
                <Heading size="lg" className="text-gray-900 text-center">
                  Erro ao Carregar Perfil
                </Heading>
                <Text className="text-gray-600 text-center">{error || 'Aluno não encontrado'}</Text>
              </VStack>
              <Button onPress={() => router.back()}>
                <ButtonText>Voltar</ButtonText>
              </Button>
            </VStack>
          </Center>
        </Box>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <ScrollView
        className="flex-1"
        style={{ backgroundColor: COLORS.gray[50] }}
        showsVerticalScrollIndicator={false}
      >
        <VStack className="flex-1">
          {/* Header */}
          <StudentProfileHeader
            student={student}
            isEditing={isEditing}
            onEditToggle={handleEditToggle}
            onSave={handleSave}
            isSaving={isSaving}
          />

          {/* Content */}
          <VStack className="p-6" space="lg">
            {/* Student Info */}
            <StudentInfoCard
              student={student}
              isEditing={isEditing}
              formData={formData}
              onFormDataChange={handleFormDataChange}
              educationalSystems={educationalSystems}
            />

            {/* Parent Contact */}
            <ParentContactCard
              student={student}
              isEditing={isEditing}
              formData={formData}
              onFormDataChange={handleFormDataChange}
            />
          </VStack>
        </VStack>
      </ScrollView>
    </MainLayout>
  );
}
