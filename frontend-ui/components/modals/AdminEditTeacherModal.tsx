import {
  X,
  Save,
  AlertTriangle,
  Info,
  User,
  Mail,
  Phone,
  MapPin,
  DollarSign,
  Clock,
  BookOpen,
} from 'lucide-react-native';
import React, { useState, useEffect } from 'react';

import { TeacherProfile, UpdateTeacherData } from '@/api/userApi';
import { Badge } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Divider } from '@/components/ui/divider';
import { FormControl } from '@/components/ui/form-control';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Input } from '@/components/ui/input';
import { Modal } from '@/components/ui/modal';
import { Pressable } from '@/components/ui/pressable';
import { ScrollView } from '@/components/ui/scroll-view';
import { Select } from '@/components/ui/select';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { Textarea } from '@/components/ui/textarea';
import { VStack } from '@/components/ui/vstack';
import { useTeacherProfile } from '@/hooks/useTeacherProfile';

interface AdminEditTeacherModalProps {
  isOpen: boolean;
  onClose: () => void;
  teacher: TeacherProfile;
  onSuccess?: (updatedTeacher: TeacherProfile) => void;
}

interface FormData {
  bio: string;
  specialty: string;
  education: string;
  hourly_rate: string;
  availability: string;
  address: string;
  phone_number: string;
  calendar_iframe: string;
  status: 'active' | 'inactive' | 'pending';
}

interface ValidationErrors {
  [key: string]: string;
}

// Admin-editable fields (respecting teacher autonomy)
const ADMIN_EDITABLE_FIELDS = [
  'bio',
  'specialty',
  'education',
  'address',
  'phone_number',
  'calendar_iframe',
  'status',
];

// Fields that require special permission or are critical
const SENSITIVE_FIELDS = [
  'hourly_rate', // Rates should typically be set by teachers
  'availability', // Availability is teacher's personal schedule
];

export const AdminEditTeacherModal: React.FC<AdminEditTeacherModalProps> = ({
  isOpen,
  onClose,
  teacher,
  onSuccess,
}) => {
  const { updateProfile, updating } = useTeacherProfile({ teacherId: teacher.id });

  const [formData, setFormData] = useState<FormData>({
    bio: teacher.bio || '',
    specialty: teacher.specialty || '',
    education: teacher.education || '',
    hourly_rate: teacher.hourly_rate?.toString() || '',
    availability: teacher.availability || '',
    address: teacher.address || '',
    phone_number: teacher.phone_number || '',
    calendar_iframe: teacher.calendar_iframe || '',
    status: teacher.status || 'active',
  });

  const [errors, setErrors] = useState<ValidationErrors>({});
  const [showSensitiveWarning, setShowSensitiveWarning] = useState(false);
  const [changedFields, setChangedFields] = useState<Set<string>>(new Set());

  // Reset form when teacher changes
  useEffect(() => {
    if (teacher) {
      setFormData({
        bio: teacher.bio || '',
        specialty: teacher.specialty || '',
        education: teacher.education || '',
        hourly_rate: teacher.hourly_rate?.toString() || '',
        availability: teacher.availability || '',
        address: teacher.address || '',
        phone_number: teacher.phone_number || '',
        calendar_iframe: teacher.calendar_iframe || '',
        status: teacher.status || 'active',
      });
      setChangedFields(new Set());
      setErrors({});
    }
  }, [teacher]);

  const handleFieldChange = (field: keyof FormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));

    // Track changed fields
    const originalValue = getOriginalValue(field);
    if (value !== originalValue) {
      setChangedFields(prev => new Set(prev).add(field));
    } else {
      setChangedFields(prev => {
        const newSet = new Set(prev);
        newSet.delete(field);
        return newSet;
      });
    }

    // Clear error for this field
    if (errors[field]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }

    // Check if sensitive field is being modified
    if (SENSITIVE_FIELDS.includes(field) && value !== getOriginalValue(field)) {
      setShowSensitiveWarning(true);
    }
  };

  const getOriginalValue = (field: keyof FormData): string => {
    switch (field) {
      case 'bio':
        return teacher.bio || '';
      case 'specialty':
        return teacher.specialty || '';
      case 'education':
        return teacher.education || '';
      case 'hourly_rate':
        return teacher.hourly_rate?.toString() || '';
      case 'availability':
        return teacher.availability || '';
      case 'address':
        return teacher.address || '';
      case 'phone_number':
        return teacher.phone_number || '';
      case 'calendar_iframe':
        return teacher.calendar_iframe || '';
      case 'status':
        return teacher.status || 'active';
      default:
        return '';
    }
  };

  const validateForm = (): boolean => {
    const newErrors: ValidationErrors = {};

    // Validate hourly rate if changed
    if (changedFields.has('hourly_rate') && formData.hourly_rate) {
      const rate = parseFloat(formData.hourly_rate);
      if (isNaN(rate) || rate < 0) {
        newErrors.hourly_rate = 'Taxa horária deve ser um número válido';
      } else if (rate > 500) {
        newErrors.hourly_rate = 'Taxa horária parece muito alta (máx. €500/hora)';
      }
    }

    // Validate phone number format
    if (changedFields.has('phone_number') && formData.phone_number) {
      const phoneRegex = /^[+]?[\d\s\-\(\)]{9,15}$/;
      if (!phoneRegex.test(formData.phone_number)) {
        newErrors.phone_number = 'Formato de telefone inválido';
      }
    }

    // Validate bio length
    if (changedFields.has('bio') && formData.bio && formData.bio.length < 50) {
      newErrors.bio = 'Biografia deve ter pelo menos 50 caracteres';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSave = async () => {
    if (!validateForm()) {
      return;
    }

    if (changedFields.size === 0) {
      onClose();
      return;
    }

    try {
      // Only send changed fields to API
      const updateData: Partial<UpdateTeacherData> = {};

      changedFields.forEach(field => {
        const value = formData[field as keyof FormData];

        if (field === 'hourly_rate') {
          updateData.hourly_rate = value ? parseFloat(value) : undefined;
        } else {
          (updateData as any)[field] = value || undefined;
        }
      });

      const updatedTeacher = await updateProfile(updateData);

      if (onSuccess) {
        onSuccess(updatedTeacher);
      }

      onClose();
    } catch (error: any) {
      console.error('Error updating teacher:', error);
      setErrors({ general: error.message || 'Erro ao atualizar professor' });
    }
  };

  const handleClose = () => {
    if (changedFields.size > 0) {
      // TODO: Show confirmation dialog for unsaved changes
      console.log('Warning: Unsaved changes will be lost');
    }
    onClose();
  };

  const hasChanges = changedFields.size > 0;
  const hasSensitiveChanges = Array.from(changedFields).some(field =>
    SENSITIVE_FIELDS.includes(field)
  );

  return (
    <Modal isOpen={isOpen} onClose={handleClose}>
      <Box className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-5/6">
        <ScrollView showsVerticalScrollIndicator={false}>
          <VStack space="lg" className="p-6">
            {/* Header */}
            <HStack className="items-center justify-between">
              <VStack>
                <Heading size="lg" className="text-gray-900">
                  Editar Professor
                </Heading>
                <Text className="text-sm text-gray-600">
                  {teacher.user.name} • {teacher.user.email}
                </Text>
              </VStack>

              <Pressable onPress={handleClose} className="p-2 -mr-2">
                <Icon as={X} size="md" className="text-gray-500" />
              </Pressable>
            </HStack>

            {/* Sensitive Fields Warning */}
            {showSensitiveWarning && hasSensitiveChanges && (
              <Box className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
                <HStack space="sm" className="items-start">
                  <Icon as={AlertTriangle} size="sm" className="text-amber-600 mt-1" />
                  <VStack className="flex-1">
                    <Text className="text-sm font-medium text-amber-800">
                      Atenção: Campos sensíveis
                    </Text>
                    <Text className="text-xs text-amber-700">
                      Você está modificando campos que normalmente são gerenciados pelo próprio
                      professor. Considere entrar em contato antes de fazer alterações.
                    </Text>
                  </VStack>
                </HStack>
              </Box>
            )}

            {/* General Error */}
            {errors.general && (
              <Box className="p-4 bg-red-50 border border-red-200 rounded-lg">
                <Text className="text-sm text-red-800">{errors.general}</Text>
              </Box>
            )}

            {/* Form Fields */}
            <VStack space="lg">
              {/* Basic Information */}
              <VStack space="md">
                <HStack className="items-center" space="xs">
                  <Icon as={User} size="sm" className="text-gray-600" />
                  <Heading size="md" className="text-gray-900">
                    Informações Básicas
                  </Heading>
                </HStack>

                <FormControl isInvalid={!!errors.bio}>
                  <Text className="text-sm font-medium text-gray-700 mb-2">
                    Biografia
                    {changedFields.has('bio') && (
                      <Badge variant="secondary" size="sm" className="ml-2">
                        Modificado
                      </Badge>
                    )}
                  </Text>
                  <Textarea
                    placeholder="Biografia profissional do professor..."
                    value={formData.bio}
                    onChangeText={value => handleFieldChange('bio', value)}
                    numberOfLines={4}
                  />
                  {errors.bio && <Text className="text-xs text-red-600 mt-1">{errors.bio}</Text>}
                </FormControl>

                <FormControl>
                  <Text className="text-sm font-medium text-gray-700 mb-2">
                    Especialidade
                    {changedFields.has('specialty') && (
                      <Badge variant="secondary" size="sm" className="ml-2">
                        Modificado
                      </Badge>
                    )}
                  </Text>
                  <Input
                    placeholder="Ex: Matemática, Física, Inglês"
                    value={formData.specialty}
                    onChangeText={value => handleFieldChange('specialty', value)}
                  />
                </FormControl>

                <FormControl>
                  <Text className="text-sm font-medium text-gray-700 mb-2">
                    Formação
                    {changedFields.has('education') && (
                      <Badge variant="secondary" size="sm" className="ml-2">
                        Modificado
                      </Badge>
                    )}
                  </Text>
                  <Input
                    placeholder="Formação acadêmica e qualificações"
                    value={formData.education}
                    onChangeText={value => handleFieldChange('education', value)}
                  />
                </FormControl>
              </VStack>

              <Divider />

              {/* Contact Information */}
              <VStack space="md">
                <HStack className="items-center" space="xs">
                  <Icon as={Phone} size="sm" className="text-gray-600" />
                  <Heading size="md" className="text-gray-900">
                    Informações de Contato
                  </Heading>
                </HStack>

                <FormControl isInvalid={!!errors.phone_number}>
                  <Text className="text-sm font-medium text-gray-700 mb-2">
                    Telefone
                    {changedFields.has('phone_number') && (
                      <Badge variant="secondary" size="sm" className="ml-2">
                        Modificado
                      </Badge>
                    )}
                  </Text>
                  <Input
                    placeholder="+351 xxx xxx xxx"
                    value={formData.phone_number}
                    onChangeText={value => handleFieldChange('phone_number', value)}
                  />
                  {errors.phone_number && (
                    <Text className="text-xs text-red-600 mt-1">{errors.phone_number}</Text>
                  )}
                </FormControl>

                <FormControl>
                  <Text className="text-sm font-medium text-gray-700 mb-2">
                    Endereço
                    {changedFields.has('address') && (
                      <Badge variant="secondary" size="sm" className="ml-2">
                        Modificado
                      </Badge>
                    )}
                  </Text>
                  <Input
                    placeholder="Endereço para aulas presenciais"
                    value={formData.address}
                    onChangeText={value => handleFieldChange('address', value)}
                  />
                </FormControl>
              </VStack>

              <Divider />

              {/* Teaching Information */}
              <VStack space="md">
                <HStack className="items-center" space="xs">
                  <Icon as={BookOpen} size="sm" className="text-gray-600" />
                  <Heading size="md" className="text-gray-900">
                    Informações de Ensino
                  </Heading>
                </HStack>

                <FormControl isInvalid={!!errors.hourly_rate}>
                  <HStack className="items-center justify-between mb-2">
                    <Text className="text-sm font-medium text-gray-700">
                      Taxa Horária (€)
                      {changedFields.has('hourly_rate') && (
                        <Badge variant="secondary" size="sm" className="ml-2">
                          Modificado
                        </Badge>
                      )}
                    </Text>
                    {SENSITIVE_FIELDS.includes('hourly_rate') && (
                      <Badge variant="outline" size="sm">
                        Sensível
                      </Badge>
                    )}
                  </HStack>
                  <Input
                    placeholder="25.00"
                    value={formData.hourly_rate}
                    onChangeText={value => handleFieldChange('hourly_rate', value)}
                    keyboardType="numeric"
                  />
                  {errors.hourly_rate && (
                    <Text className="text-xs text-red-600 mt-1">{errors.hourly_rate}</Text>
                  )}
                </FormControl>

                <FormControl>
                  <HStack className="items-center justify-between mb-2">
                    <Text className="text-sm font-medium text-gray-700">
                      Disponibilidade
                      {changedFields.has('availability') && (
                        <Badge variant="secondary" size="sm" className="ml-2">
                          Modificado
                        </Badge>
                      )}
                    </Text>
                    {SENSITIVE_FIELDS.includes('availability') && (
                      <Badge variant="outline" size="sm">
                        Sensível
                      </Badge>
                    )}
                  </HStack>
                  <Textarea
                    placeholder="Horários disponíveis para aulas"
                    value={formData.availability}
                    onChangeText={value => handleFieldChange('availability', value)}
                    numberOfLines={3}
                  />
                </FormControl>

                <FormControl>
                  <Text className="text-sm font-medium text-gray-700 mb-2">
                    Calendário (iframe)
                    {changedFields.has('calendar_iframe') && (
                      <Badge variant="secondary" size="sm" className="ml-2">
                        Modificado
                      </Badge>
                    )}
                  </Text>
                  <Input
                    placeholder="URL do iframe do calendário"
                    value={formData.calendar_iframe}
                    onChangeText={value => handleFieldChange('calendar_iframe', value)}
                  />
                </FormControl>
              </VStack>

              <Divider />

              {/* Administrative */}
              <VStack space="md">
                <HStack className="items-center" space="xs">
                  <Icon as={Info} size="sm" className="text-gray-600" />
                  <Heading size="md" className="text-gray-900">
                    Administrativo
                  </Heading>
                </HStack>

                <FormControl>
                  <Text className="text-sm font-medium text-gray-700 mb-2">
                    Status
                    {changedFields.has('status') && (
                      <Badge variant="secondary" size="sm" className="ml-2">
                        Modificado
                      </Badge>
                    )}
                  </Text>
                  <Select
                    selectedValue={formData.status}
                    onValueChange={value => handleFieldChange('status', value)}
                  >
                    <Select.Item value="active" label="Ativo" />
                    <Select.Item value="inactive" label="Inativo" />
                    <Select.Item value="pending" label="Pendente" />
                  </Select>
                </FormControl>
              </VStack>
            </VStack>
          </VStack>
        </ScrollView>

        {/* Footer Actions */}
        <Box className="p-6 border-t border-gray-200 bg-gray-50">
          <HStack className="justify-between items-center">
            <VStack>
              {hasChanges && (
                <Text className="text-xs text-gray-600">
                  {changedFields.size} campo{changedFields.size > 1 ? 's' : ''} modificado
                  {changedFields.size > 1 ? 's' : ''}
                </Text>
              )}
              {hasSensitiveChanges && (
                <Text className="text-xs text-amber-600">Inclui campos sensíveis</Text>
              )}
            </VStack>

            <HStack space="sm">
              <Button variant="outline" onPress={handleClose} disabled={updating}>
                <ButtonText>Cancelar</ButtonText>
              </Button>

              <Button
                onPress={handleSave}
                disabled={updating || !hasChanges}
                className="bg-blue-600"
              >
                {updating ? (
                  <Spinner size="small" />
                ) : (
                  <Icon as={Save} size="sm" className="text-white" />
                )}
                <ButtonText className="text-white ml-2">
                  {updating ? 'Salvando...' : 'Salvar'}
                </ButtonText>
              </Button>
            </HStack>
          </HStack>
        </Box>
      </Box>
    </Modal>
  );
};

export default AdminEditTeacherModal;
