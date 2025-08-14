import { X } from 'lucide-react-native';
import React from 'react';

import { InvitationStatus, SchoolRole } from '@/api/invitationApi';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { HStack } from '@/components/ui/hstack';
import { Icon, ChevronDownIcon } from '@/components/ui/icon';
import {
  Select,
  SelectTrigger,
  SelectInput,
  SelectIcon,
  SelectPortal,
  SelectBackdrop,
  SelectContent,
  SelectDragIndicatorWrapper,
  SelectDragIndicator,
  SelectItem,
} from '@/components/ui/select';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

interface InvitationFiltersProps {
  filters: {
    status?: InvitationStatus;
    role?: SchoolRole;
    ordering?: string;
  };
  onFiltersChange: (filters: any) => void;
  onClearFilters: () => void;
}

const STATUS_OPTIONS = [
  { value: '', label: 'Todos os status' },
  { value: InvitationStatus.PENDING, label: 'Pendente' },
  { value: InvitationStatus.SENT, label: 'Enviado' },
  { value: InvitationStatus.DELIVERED, label: 'Entregue' },
  { value: InvitationStatus.VIEWED, label: 'Visualizado' },
  { value: InvitationStatus.ACCEPTED, label: 'Aceito' },
  { value: InvitationStatus.DECLINED, label: 'Recusado' },
  { value: InvitationStatus.EXPIRED, label: 'Expirado' },
  { value: InvitationStatus.CANCELLED, label: 'Cancelado' },
];

const ROLE_OPTIONS = [
  { value: '', label: 'Todas as funções' },
  { value: SchoolRole.TEACHER, label: 'Professor' },
  { value: SchoolRole.SCHOOL_ADMIN, label: 'Administrador' },
  { value: SchoolRole.SCHOOL_OWNER, label: 'Proprietário' },
];

const ORDERING_OPTIONS = [
  { value: '', label: 'Padrão' },
  { value: '-created_at', label: 'Mais recentes primeiro' },
  { value: 'created_at', label: 'Mais antigos primeiro' },
  { value: '-expires_at', label: 'Expira primeiro' },
  { value: 'expires_at', label: 'Expira por último' },
  { value: 'email', label: 'Email (A-Z)' },
  { value: '-email', label: 'Email (Z-A)' },
  { value: 'status', label: 'Status' },
];

export const InvitationFilters: React.FC<InvitationFiltersProps> = ({
  filters,
  onFiltersChange,
  onClearFilters,
}) => {
  const handleStatusChange = (value: string) => {
    onFiltersChange({
      ...filters,
      status: value || undefined,
    });
  };

  const handleRoleChange = (value: string) => {
    onFiltersChange({
      ...filters,
      role: value || undefined,
    });
  };

  const handleOrderingChange = (value: string) => {
    onFiltersChange({
      ...filters,
      ordering: value || undefined,
    });
  };

  const hasActiveFilters = () => {
    return filters.status || filters.role || filters.ordering;
  };

  return (
    <Box className="p-4 bg-white rounded-lg border">
      <VStack space="md">
        <HStack className="justify-between items-center">
          <Text className="font-medium text-gray-900">Filtros</Text>
          {hasActiveFilters() && (
            <Button variant="outline" size="xs" onPress={onClearFilters}>
              <HStack space="xs" className="items-center">
                <Icon as={X} size="xs" />
                <ButtonText>Limpar</ButtonText>
              </HStack>
            </Button>
          )}
        </HStack>

        <VStack space="sm">
          {/* Status Filter */}
          <VStack space="xs">
            <Text className="text-sm font-medium text-gray-700">Status</Text>
            <Select selectedValue={filters.status || ''} onValueChange={handleStatusChange}>
              <SelectTrigger variant="outline" size="sm">
                <SelectInput placeholder="Selecionar status" />
                <SelectIcon className="mr-3" as={ChevronDownIcon} />
              </SelectTrigger>
              <SelectPortal>
                <SelectBackdrop />
                <SelectContent>
                  <SelectDragIndicatorWrapper>
                    <SelectDragIndicator />
                  </SelectDragIndicatorWrapper>
                  {STATUS_OPTIONS.map(option => (
                    <SelectItem key={option.value} label={option.label} value={option.value} />
                  ))}
                </SelectContent>
              </SelectPortal>
            </Select>
          </VStack>

          {/* Role Filter */}
          <VStack space="xs">
            <Text className="text-sm font-medium text-gray-700">Função</Text>
            <Select selectedValue={filters.role || ''} onValueChange={handleRoleChange}>
              <SelectTrigger variant="outline" size="sm">
                <SelectInput placeholder="Selecionar função" />
                <SelectIcon className="mr-3" as={ChevronDownIcon} />
              </SelectTrigger>
              <SelectPortal>
                <SelectBackdrop />
                <SelectContent>
                  <SelectDragIndicatorWrapper>
                    <SelectDragIndicator />
                  </SelectDragIndicatorWrapper>
                  {ROLE_OPTIONS.map(option => (
                    <SelectItem key={option.value} label={option.label} value={option.value} />
                  ))}
                </SelectContent>
              </SelectPortal>
            </Select>
          </VStack>

          {/* Ordering Filter */}
          <VStack space="xs">
            <Text className="text-sm font-medium text-gray-700">Ordenação</Text>
            <Select selectedValue={filters.ordering || ''} onValueChange={handleOrderingChange}>
              <SelectTrigger variant="outline" size="sm">
                <SelectInput placeholder="Selecionar ordenação" />
                <SelectIcon className="mr-3" as={ChevronDownIcon} />
              </SelectTrigger>
              <SelectPortal>
                <SelectBackdrop />
                <SelectContent>
                  <SelectDragIndicatorWrapper>
                    <SelectDragIndicator />
                  </SelectDragIndicatorWrapper>
                  {ORDERING_OPTIONS.map(option => (
                    <SelectItem key={option.value} label={option.label} value={option.value} />
                  ))}
                </SelectContent>
              </SelectPortal>
            </Select>
          </VStack>
        </VStack>

        {/* Active Filters Summary */}
        {hasActiveFilters() && (
          <Box className="p-2 bg-blue-50 rounded border border-blue-200">
            <VStack space="xs">
              <Text className="text-xs font-medium text-blue-900">Filtros ativos:</Text>
              <HStack space="xs" className="flex-wrap">
                {filters.status && (
                  <Box className="px-2 py-1 bg-blue-100 rounded">
                    <Text className="text-xs text-blue-700">
                      Status: {STATUS_OPTIONS.find(opt => opt.value === filters.status)?.label}
                    </Text>
                  </Box>
                )}
                {filters.role && (
                  <Box className="px-2 py-1 bg-blue-100 rounded">
                    <Text className="text-xs text-blue-700">
                      Função: {ROLE_OPTIONS.find(opt => opt.value === filters.role)?.label}
                    </Text>
                  </Box>
                )}
                {filters.ordering && (
                  <Box className="px-2 py-1 bg-blue-100 rounded">
                    <Text className="text-xs text-blue-700">
                      Ordem: {ORDERING_OPTIONS.find(opt => opt.value === filters.ordering)?.label}
                    </Text>
                  </Box>
                )}
              </HStack>
            </VStack>
          </Box>
        )}
      </VStack>
    </Box>
  );
};
