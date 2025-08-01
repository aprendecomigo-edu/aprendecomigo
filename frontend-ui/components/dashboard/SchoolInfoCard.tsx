import { Check, Edit, Globe, Mail, MapPin, Phone, Save, School, X } from 'lucide-react-native';
import React, { useState } from 'react';

import { SchoolInfo } from '@/api/userApi';
import { Button, ButtonText } from '@/components/ui/button';
import { Card, CardBody, CardHeader } from '@/components/ui/card';
import { FormControl } from '@/components/ui/form-control';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Input, InputField } from '@/components/ui/input';
import { Pressable } from '@/components/ui/pressable';
import { Select, SelectTrigger, SelectInput, SelectPortal, SelectBackdrop, SelectContent, SelectDragIndicatorWrapper, SelectDragIndicator, SelectItem } from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { Text } from '@/components/ui/text';
import { Textarea, TextareaInput } from '@/components/ui/textarea';
import { VStack } from '@/components/ui/vstack';

interface SchoolInfoCardProps {
  schoolInfo: SchoolInfo | null;
  isLoading: boolean;
  onUpdate: (data: Partial<SchoolInfo>) => Promise<void>;
}

interface InfoRowProps {
  icon: React.ComponentType<any>;
  label: string;
  value: string;
  placeholder?: string;
}

const InfoRow: React.FC<InfoRowProps> = ({ icon: IconComponent, label, value, placeholder }) => (
  <HStack space="sm" className="items-start">
    <Icon as={IconComponent} size="sm" className="text-gray-500 mt-1" />
    <VStack space="xs" className="flex-1 min-w-0">
      <Text className="text-xs font-medium text-gray-600 uppercase tracking-wide">
        {label}
      </Text>
      <Text className="text-sm text-gray-900">
        {value || (
          <Text className="text-gray-500 italic">
            {placeholder || 'Não informado'}
          </Text>
        )}
      </Text>
    </VStack>
  </HStack>
);

const InfoRowSkeleton: React.FC = () => (
  <HStack space="sm" className="items-start">
    <Skeleton className="w-4 h-4 rounded mt-1" />
    <VStack space="xs" className="flex-1">
      <Skeleton className="h-3 w-16 rounded" />
      <Skeleton className="h-4 w-full rounded" />
    </VStack>
  </HStack>
);

const SchoolInfoCard: React.FC<SchoolInfoCardProps> = ({
  schoolInfo,
  isLoading,
  onUpdate,
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [editData, setEditData] = useState<Partial<SchoolInfo>>({});

  const handleEdit = () => {
    if (schoolInfo) {
      setEditData({
        name: schoolInfo.name,
        description: schoolInfo.description,
        address: schoolInfo.address,
        contact_email: schoolInfo.contact_email,
        phone_number: schoolInfo.phone_number,
        website: schoolInfo.website,
        settings: {
          ...schoolInfo.settings,
        },
      });
      setIsEditing(true);
    }
  };

  const handleCancel = () => {
    setEditData({});
    setIsEditing(false);
  };

  const handleSave = async () => {
    try {
      setIsSaving(true);
      await onUpdate(editData);
      setIsEditing(false);
      setEditData({});
    } catch (error) {
      console.error('Error updating school info:', error);
      // Error handling is done in the parent component
    } finally {
      setIsSaving(false);
    }
  };

  const updateField = (field: string, value: string) => {
    setEditData(prev => ({
      ...prev,
      [field]: value,
    }));
  };

  const updateSetting = (setting: string, value: string | number) => {
    setEditData(prev => ({
      ...prev,
      settings: {
        ...prev.settings,
        ...schoolInfo?.settings,
        [setting]: value,
      },
    }));
  };

  if (isLoading) {
    return (
      <Card variant="elevated" className="bg-white shadow-sm">
        <CardHeader>
          <HStack className="justify-between items-center">
            <Skeleton className="h-6 w-40 rounded" />
            <Skeleton className="h-8 w-16 rounded" />
          </HStack>
        </CardHeader>
        <CardBody>
          <VStack space="lg">
            <InfoRowSkeleton />
            <InfoRowSkeleton />
            <InfoRowSkeleton />
            <InfoRowSkeleton />
          </VStack>
        </CardBody>
      </Card>
    );
  }

  if (!schoolInfo) {
    return (
      <Card variant="elevated" className="bg-white shadow-sm">
        <CardBody>
          <VStack space="md" className="items-center py-8">
            <Icon as={School} size="xl" className="text-gray-300" />
            <Text className="text-lg font-medium text-gray-600">
              Informações indisponíveis
            </Text>
            <Text className="text-sm text-gray-500 text-center">
              Não foi possível carregar as informações da escola
            </Text>
          </VStack>
        </CardBody>
      </Card>
    );
  }

  return (
    <Card variant="elevated" className="bg-white shadow-sm">
      <CardHeader>
        <HStack className="justify-between items-center">
          <Heading size="md" className="text-gray-900">
            Informações da Escola
          </Heading>
          
          {!isEditing ? (
            <Pressable
              onPress={handleEdit}
              className="p-2 rounded-md bg-blue-50 hover:bg-blue-100"
            >
              <Icon as={Edit} size="sm" className="text-blue-600" />
            </Pressable>
          ) : (
            <HStack space="xs">
              <Pressable
                onPress={handleCancel}
                disabled={isSaving}
                className="p-2 rounded-md bg-gray-50 hover:bg-gray-100"
              >
                <Icon as={X} size="sm" className="text-gray-600" />
              </Pressable>
              <Pressable
                onPress={handleSave}
                disabled={isSaving}
                className="p-2 rounded-md bg-green-50 hover:bg-green-100"
              >
                <Icon as={isSaving ? Save : Check} size="sm" className="text-green-600" />
              </Pressable>
            </HStack>
          )}
        </HStack>
      </CardHeader>
      
      <CardBody>
        {isEditing ? (
          <VStack space="lg">
            <FormControl>
              <Text className="text-sm font-medium text-gray-700 mb-2">Nome da Escola</Text>
              <Input>
                <InputField
                  value={editData.name || ''}
                  onChangeText={(text: string) => updateField('name', text)}
                  placeholder="Nome da escola"
                />
              </Input>
            </FormControl>

            <FormControl>
              <Text className="text-sm font-medium text-gray-700 mb-2">Descrição</Text>
              <Textarea>
                <TextareaInput
                  value={editData.description || ''}
                  onChangeText={(text: string) => updateField('description', text)}
                  placeholder="Descrição da escola"
                />
              </Textarea>
            </FormControl>

            <FormControl>
              <Text className="text-sm font-medium text-gray-700 mb-2">Endereço</Text>
              <Input>
                <InputField
                  value={editData.address || ''}
                  onChangeText={(text: string) => updateField('address', text)}
                  placeholder="Endereço completo"
                />
              </Input>
            </FormControl>

            <HStack space="md" className="flex-wrap">
              <VStack className="flex-1 min-w-0">
                <FormControl>
                  <Text className="text-sm font-medium text-gray-700 mb-2">Email</Text>
                  <Input>
                    <InputField
                      value={editData.contact_email || ''}
                      onChangeText={(text: string) => updateField('contact_email', text)}
                      placeholder="email@escola.com"
                    />
                  </Input>
                </FormControl>
              </VStack>

              <VStack className="flex-1 min-w-0">
                <FormControl>
                  <Text className="text-sm font-medium text-gray-700 mb-2">Telefone</Text>
                  <Input
                    value={editData.phone_number || ''}
                    onChangeText={(text: string) => updateField('phone_number', text)}
                    placeholder="+351 123 456 789"
                  />
                </FormControl>
              </VStack>
            </HStack>

            <FormControl>
              <Text className="text-sm font-medium text-gray-700 mb-2">Website</Text>
              <Input
                value={editData.website || ''}
                onChangeText={(text: string) => updateField('website', text)}
                placeholder="https://www.escola.com"
              />
            </FormControl>

            <FormControl>
              <Text className="text-sm font-medium text-gray-700 mb-2">Política de Custo de Teste</Text>
              <Select
                selectedValue={editData.settings?.trial_cost_absorption || schoolInfo.settings.trial_cost_absorption}
                onValueChange={(value) => updateSetting('trial_cost_absorption', value)}
              >
                <SelectTrigger>
                  <SelectInput placeholder="Selecionar política" />
                </SelectTrigger>
                <SelectPortal>
                  <SelectBackdrop />
                  <SelectContent>
                    <SelectDragIndicatorWrapper>
                      <SelectDragIndicator />
                    </SelectDragIndicatorWrapper>
                    <SelectItem label="Escola absorve" value="school" />
                    <SelectItem label="Professor absorve" value="teacher" />
                    <SelectItem label="Dividir 50/50" value="split" />
                  </SelectContent>
                </SelectPortal>
              </Select>
            </FormControl>
          </VStack>
        ) : (
          <VStack space="lg">
            <InfoRow
              icon={School}
              label="Nome"
              value={schoolInfo.name}
              placeholder="Nome da escola não informado"
            />
            
            {schoolInfo.description && (
              <InfoRow
                icon={School}
                label="Descrição"
                value={schoolInfo.description}
              />
            )}

            <InfoRow
              icon={MapPin}
              label="Endereço"
              value={schoolInfo.address}
              placeholder="Endereço não informado"
            />

            <HStack space="lg" className="flex-wrap">
              <VStack className="flex-1 min-w-0">
                <InfoRow
                  icon={Mail}
                  label="Email"
                  value={schoolInfo.contact_email}
                  placeholder="Email não informado"
                />
              </VStack>

              <VStack className="flex-1 min-w-0">
                <InfoRow
                  icon={Phone}
                  label="Telefone"
                  value={schoolInfo.phone_number}
                  placeholder="Telefone não informado"
                />
              </VStack>
            </HStack>

            {schoolInfo.website && (
              <InfoRow
                icon={Globe}
                label="Website"
                value={schoolInfo.website}
              />
            )}

            <VStack space="xs">
              <Text className="text-xs font-medium text-gray-600 uppercase tracking-wide">
                Configurações
              </Text>
              <VStack space="xs" className="bg-gray-50 p-3 rounded-lg">
                <HStack className="justify-between">
                  <Text className="text-sm text-gray-600">Política de Custo de Teste:</Text>
                  <Text className="text-sm font-medium text-gray-900">
                    {schoolInfo.settings.trial_cost_absorption === 'school'
                      ? 'Escola absorve'
                      : schoolInfo.settings.trial_cost_absorption === 'teacher'
                      ? 'Professor absorve'
                      : 'Dividir 50/50'}
                  </Text>
                </HStack>
                <HStack className="justify-between">
                  <Text className="text-sm text-gray-600">Duração padrão da sessão:</Text>
                  <Text className="text-sm font-medium text-gray-900">
                    {schoolInfo.settings.default_session_duration} min
                  </Text>
                </HStack>
              </VStack>
            </VStack>
          </VStack>
        )}
      </CardBody>
    </Card>
  );
};

export { SchoolInfoCard };
export default SchoolInfoCard;