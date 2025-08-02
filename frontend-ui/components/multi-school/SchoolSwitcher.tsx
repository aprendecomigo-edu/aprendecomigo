import { ChevronDown, School, Users, Crown, Shield, Check, Plus, Clock } from 'lucide-react-native';
import React, { useState } from 'react';

import { Avatar } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Divider } from '@/components/ui/divider';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Modal, ModalBackdrop, ModalContent, ModalHeader, ModalBody } from '@/components/ui/modal';
import { Pressable } from '@/components/ui/pressable';
import {
  ResponsiveContainer,
  TouchFriendly,
  isMobile,
  getResponsiveTextSize,
} from '@/components/ui/responsive';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { useMultiSchool, SchoolMembership, PendingInvitation } from '@/hooks/useMultiSchool';

interface SchoolSwitcherProps {
  compact?: boolean;
  showPendingInvitations?: boolean;
  onInvitationAccept?: (invitation: PendingInvitation) => void;
  className?: string;
}

export const SchoolSwitcher: React.FC<SchoolSwitcherProps> = ({
  compact = false,
  showPendingInvitations = true,
  onInvitationAccept,
  className = '',
}) => {
  const {
    memberships,
    pendingInvitations,
    currentSchool,
    loading,
    switchSchool,
    hasMultipleSchools,
    hasPendingInvitations,
  } = useMultiSchool();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [switchingSchool, setSwitchingSchool] = useState<number | null>(null);

  const getRoleIcon = (role: string) => {
    switch (role) {
      case 'school_owner':
        return Crown;
      case 'school_admin':
        return Shield;
      case 'teacher':
        return Users;
      default:
        return Users;
    }
  };

  const getRoleLabel = (role: string) => {
    switch (role) {
      case 'school_owner':
        return 'Proprietário';
      case 'school_admin':
        return 'Administrador';
      case 'teacher':
        return 'Professor';
      default:
        return role;
    }
  };

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'school_owner':
        return 'text-yellow-600 bg-yellow-100';
      case 'school_admin':
        return 'text-blue-600 bg-blue-100';
      case 'teacher':
        return 'text-green-600 bg-green-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const handleSchoolSwitch = async (membership: SchoolMembership) => {
    if (membership.id === currentSchool?.id) {
      setIsModalOpen(false);
      return;
    }

    setSwitchingSchool(membership.id);
    try {
      await switchSchool(membership);
      setIsModalOpen(false);
    } finally {
      setSwitchingSchool(null);
    }
  };

  if (!currentSchool) {
    return null;
  }

  // Compact version for headers/nav bars
  if (compact) {
    return (
      <Pressable
        onPress={() => hasMultipleSchools && setIsModalOpen(true)}
        className={`${className} ${hasMultipleSchools ? 'cursor-pointer' : ''}`}
      >
        <HStack space="sm" className="items-center">
          <Avatar size="sm">
            {currentSchool.school.logo_url ? (
              <Avatar.Image source={{ uri: currentSchool.school.logo_url }} />
            ) : (
              <Avatar.FallbackText>{currentSchool.school.name}</Avatar.FallbackText>
            )}
          </Avatar>

          <VStack className="flex-1">
            <Text className="font-semibold text-sm truncate" numberOfLines={1}>
              {currentSchool.school.name}
            </Text>
            <Text className="text-xs text-gray-500">{getRoleLabel(currentSchool.role)}</Text>
          </VStack>

          {hasMultipleSchools && <Icon as={ChevronDown} size="sm" className="text-gray-400" />}

          {hasPendingInvitations && (
            <Badge className="bg-red-500">
              <Text className="text-white text-xs">{pendingInvitations.length}</Text>
            </Badge>
          )}
        </HStack>
      </Pressable>
    );
  }

  // Full version for settings/profile pages
  return (
    <Box className={className}>
      <VStack space="md">
        {/* Current School Display */}
        <Pressable
          onPress={() => hasMultipleSchools && setIsModalOpen(true)}
          className={hasMultipleSchools ? 'cursor-pointer' : ''}
        >
          <Box className="p-4 bg-white rounded-lg border border-gray-200 shadow-sm">
            <HStack space="md" className="items-center">
              <Avatar size="md">
                {currentSchool.school.logo_url ? (
                  <Avatar.Image source={{ uri: currentSchool.school.logo_url }} />
                ) : (
                  <Avatar.FallbackText>{currentSchool.school.name}</Avatar.FallbackText>
                )}
              </Avatar>

              <VStack className="flex-1">
                <Text className="font-semibold text-base">{currentSchool.school.name}</Text>
                <HStack space="xs" className="items-center">
                  <Icon
                    as={getRoleIcon(currentSchool.role)}
                    size="xs"
                    className={getRoleColor(currentSchool.role).split(' ')[0]}
                  />
                  <Text className="text-sm text-gray-600">{getRoleLabel(currentSchool.role)}</Text>
                </HStack>
              </VStack>

              {hasMultipleSchools && <Icon as={ChevronDown} size="sm" className="text-gray-400" />}
            </HStack>
          </Box>
        </Pressable>

        {/* Pending Invitations Alert */}
        {showPendingInvitations && hasPendingInvitations && (
          <Box className="p-3 bg-blue-50 rounded-lg border border-blue-200">
            <HStack space="sm" className="items-center">
              <Icon as={Clock} size="sm" className="text-blue-600" />
              <VStack className="flex-1">
                <Text className="text-sm font-medium text-blue-900">
                  {pendingInvitations.length} convite(s) pendente(s)
                </Text>
                <Text className="text-xs text-blue-700">
                  Você tem convites de outras escolas aguardando resposta.
                </Text>
              </VStack>
              <Button
                size="sm"
                variant="outline"
                onPress={() => setIsModalOpen(true)}
                className="border-blue-300"
              >
                <ButtonText className="text-blue-600">Ver</ButtonText>
              </Button>
            </HStack>
          </Box>
        )}
      </VStack>

      {/* School Switcher Modal */}
      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)}>
        <ModalBackdrop />
        <ModalContent className="max-w-md">
          <ModalHeader>
            <Heading size="lg">Suas Escolas</Heading>
          </ModalHeader>

          <ModalBody>
            <VStack space="md">
              {/* Current Schools */}
              {memberships.length > 0 && (
                <VStack space="sm">
                  <Text className="font-medium text-gray-700">Escolas Ativas</Text>
                  {memberships.map(membership => (
                    <Pressable
                      key={membership.id}
                      onPress={() => handleSchoolSwitch(membership)}
                      className="cursor-pointer"
                    >
                      <Box
                        className={`p-3 rounded-lg border ${
                          membership.id === currentSchool?.id
                            ? 'border-blue-500 bg-blue-50'
                            : 'border-gray-200 bg-white hover:bg-gray-50'
                        }`}
                      >
                        <HStack space="sm" className="items-center">
                          <Avatar size="sm">
                            {membership.school.logo_url ? (
                              <Avatar.Image source={{ uri: membership.school.logo_url }} />
                            ) : (
                              <Avatar.FallbackText>{membership.school.name}</Avatar.FallbackText>
                            )}
                          </Avatar>

                          <VStack className="flex-1">
                            <Text className="font-medium text-sm">{membership.school.name}</Text>
                            <HStack space="xs" className="items-center">
                              <Icon
                                as={getRoleIcon(membership.role)}
                                size="xs"
                                className={getRoleColor(membership.role).split(' ')[0]}
                              />
                              <Text className="text-xs text-gray-600">
                                {getRoleLabel(membership.role)}
                              </Text>
                            </HStack>
                          </VStack>

                          {switchingSchool === membership.id ? (
                            <Spinner size="small" />
                          ) : membership.id === currentSchool?.id ? (
                            <Icon as={Check} size="sm" className="text-blue-600" />
                          ) : null}
                        </HStack>
                      </Box>
                    </Pressable>
                  ))}
                </VStack>
              )}

              {/* Pending Invitations */}
              {showPendingInvitations && pendingInvitations.length > 0 && (
                <>
                  <Divider className="my-2" />
                  <VStack space="sm">
                    <Text className="font-medium text-gray-700">Convites Pendentes</Text>
                    {pendingInvitations.map(invitation => (
                      <Box
                        key={invitation.id}
                        className="p-3 bg-yellow-50 rounded-lg border border-yellow-200"
                      >
                        <HStack space="sm" className="items-center">
                          <Avatar size="sm">
                            {invitation.school.logo_url ? (
                              <Avatar.Image source={{ uri: invitation.school.logo_url }} />
                            ) : (
                              <Avatar.FallbackText>{invitation.school.name}</Avatar.FallbackText>
                            )}
                          </Avatar>

                          <VStack className="flex-1">
                            <Text className="font-medium text-sm">{invitation.school.name}</Text>
                            <Text className="text-xs text-gray-600">
                              {getRoleLabel(invitation.role)} • Convidado por{' '}
                              {invitation.invited_by.name}
                            </Text>
                            <Text className="text-xs text-gray-500">
                              Expira em{' '}
                              {new Date(invitation.expires_at).toLocaleDateString('pt-BR')}
                            </Text>
                          </VStack>

                          <Button
                            size="sm"
                            variant="solid"
                            onPress={() => onInvitationAccept?.(invitation)}
                            className="bg-green-600"
                          >
                            <ButtonText className="text-white">Aceitar</ButtonText>
                          </Button>
                        </HStack>
                      </Box>
                    ))}
                  </VStack>
                </>
              )}

              {/* No Schools State */}
              {memberships.length === 0 && pendingInvitations.length === 0 && (
                <Box className="p-6 text-center">
                  <Icon as={School} size="xl" className="text-gray-400 mx-auto mb-3" />
                  <Text className="text-gray-600 mb-2">Nenhuma escola encontrada</Text>
                  <Text className="text-sm text-gray-500">
                    Aguarde um convite de uma escola ou entre em contato com o administrador.
                  </Text>
                </Box>
              )}
            </VStack>
          </ModalBody>
        </ModalContent>
      </Modal>
    </Box>
  );
};

export default SchoolSwitcher;
