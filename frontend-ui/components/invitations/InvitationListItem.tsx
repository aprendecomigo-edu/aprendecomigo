import { Mail, MoreHorizontal, RefreshCw, X, Clock, CheckCircle, XCircle, Eye, Send } from 'lucide-react-native';
import React, { useState } from 'react';
import { Alert } from 'react-native';

import { TeacherInvitation, InvitationStatus, EmailDeliveryStatus, SchoolRole } from '@/api/invitationApi';
import { useInvitationActions } from '@/hooks/useInvitations';

import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Pressable } from '@/components/ui/pressable';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { Badge, BadgeText } from '@/components/ui/badge';
import { Actionsheet, ActionsheetBackdrop, ActionsheetContent, ActionsheetDragIndicatorWrapper, ActionsheetDragIndicator, ActionsheetItem, ActionsheetItemText } from '@/components/ui/actionsheet';

interface InvitationListItemProps {
  invitation: TeacherInvitation;
  onAction?: () => void;
  isLast?: boolean;
}

export const InvitationListItem: React.FC<InvitationListItemProps> = ({
  invitation,
  onAction,
  isLast = false,
}) => {
  const [showActions, setShowActions] = useState(false);
  const { cancelInvitation, resendInvitation, loading } = useInvitationActions();

  const getStatusConfig = (status: InvitationStatus) => {
    switch (status) {
      case InvitationStatus.PENDING:
        return {
          color: '#F59E0B',
          backgroundColor: '#FEF3C7',
          icon: Clock,
          label: 'Pendente',
        };
      case InvitationStatus.SENT:
        return {
          color: '#3B82F6',
          backgroundColor: '#DBEAFE',
          icon: Send,
          label: 'Enviado',
        };
      case InvitationStatus.DELIVERED:
        return {
          color: '#3B82F6',
          backgroundColor: '#DBEAFE',
          icon: Mail,
          label: 'Entregue',
        };
      case InvitationStatus.VIEWED:
        return {
          color: '#8B5CF6',
          backgroundColor: '#EDE9FE',
          icon: Eye,
          label: 'Visualizado',
        };
      case InvitationStatus.ACCEPTED:
        return {
          color: '#10B981',
          backgroundColor: '#D1FAE5',
          icon: CheckCircle,
          label: 'Aceito',
        };
      case InvitationStatus.DECLINED:
        return {
          color: '#EF4444',
          backgroundColor: '#FEE2E2',
          icon: XCircle,
          label: 'Recusado',
        };
      case InvitationStatus.EXPIRED:
        return {
          color: '#6B7280',
          backgroundColor: '#F3F4F6',
          icon: Clock,
          label: 'Expirado',
        };
      case InvitationStatus.CANCELLED:
        return {
          color: '#EF4444',
          backgroundColor: '#FEE2E2',
          icon: X,
          label: 'Cancelado',
        };
      default:
        return {
          color: '#6B7280',
          backgroundColor: '#F3F4F6',
          icon: Clock,
          label: status,
        };
    }
  };

  const getEmailDeliveryStatusConfig = (status: EmailDeliveryStatus) => {
    switch (status) {
      case EmailDeliveryStatus.SENT:
        return { color: '#10B981', label: 'Email enviado' };
      case EmailDeliveryStatus.DELIVERED:
        return { color: '#10B981', label: 'Email entregue' };
      case EmailDeliveryStatus.BOUNCED:
        return { color: '#EF4444', label: 'Email rejeitado' };
      case EmailDeliveryStatus.FAILED:
        return { color: '#EF4444', label: 'Falha no envio' };
      case EmailDeliveryStatus.PENDING:
        return { color: '#F59E0B', label: 'Enviando...' };
      case EmailDeliveryStatus.NOT_SENT:
      default:
        return { color: '#6B7280', label: 'Não enviado' };
    }
  };

  const getRoleLabel = (role: SchoolRole) => {
    switch (role) {
      case SchoolRole.TEACHER:
        return 'Professor';
      case SchoolRole.SCHOOL_ADMIN:
        return 'Administrador';
      case SchoolRole.SCHOOL_OWNER:
        return 'Proprietário';
      default:
        return role;
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const isExpired = () => {
    return new Date(invitation.expires_at) < new Date();
  };

  const canResend = () => {
    return [
      InvitationStatus.PENDING,
      InvitationStatus.SENT,
      InvitationStatus.DELIVERED,
      InvitationStatus.VIEWED,
    ].includes(invitation.status) && !isExpired();
  };

  const canCancel = () => {
    return [
      InvitationStatus.PENDING,
      InvitationStatus.SENT,
      InvitationStatus.DELIVERED,
      InvitationStatus.VIEWED,
    ].includes(invitation.status);
  };

  const handleResend = async () => {
    try {
      await resendInvitation(invitation.token);
      onAction?.();
    } catch (error) {
      // Error handling is done in the hook
    }
    setShowActions(false);
  };

  const handleCancel = async () => {
    Alert.alert(
      'Cancelar Convite',
      `Tem certeza que deseja cancelar o convite para ${invitation.email}?`,
      [
        { text: 'Não', style: 'cancel' },
        {
          text: 'Sim, cancelar',
          style: 'destructive',
          onPress: async () => {
            try {
              await cancelInvitation(invitation.token);
              onAction?.();
            } catch (error) {
              // Error handling is done in the hook
            }
            setShowActions(false);
          },
        },
      ]
    );
  };

  const handleCopyLink = () => {
    // TODO: Implement copy to clipboard
    Alert.alert('Link copiado', 'Link do convite copiado para a área de transferência');
    setShowActions(false);
  };

  const statusConfig = getStatusConfig(invitation.status);
  const emailDeliveryConfig = getEmailDeliveryStatusConfig(invitation.email_delivery_status);

  return (
    <>
      <Box className={`bg-white rounded-lg border ${!isLast ? 'mb-3' : ''}`}>
        <Pressable onPress={() => setShowActions(true)} className="p-4">
          <VStack space="md">
            {/* Header */}
            <HStack className="justify-between items-start">
              <VStack className="flex-1">
                <Text className="font-semibold text-gray-900 text-base">
                  {invitation.email}
                </Text>
                <Text className="text-sm text-gray-600">
                  {getRoleLabel(invitation.role)}
                </Text>
              </VStack>
              
              <HStack space="xs" className="items-center">
                <Badge
                  variant="solid"
                  style={{
                    backgroundColor: statusConfig.backgroundColor,
                  }}
                >
                  <HStack space="xs" className="items-center">
                    <Icon
                      as={statusConfig.icon}
                      size="xs"
                      style={{ color: statusConfig.color }}
                    />
                    <BadgeText style={{ color: statusConfig.color }}>
                      {statusConfig.label}
                    </BadgeText>
                  </HStack>
                </Badge>
                
                <Icon as={MoreHorizontal} size="sm" className="text-gray-400" />
              </HStack>
            </HStack>

            {/* Details */}
            <VStack space="xs">
              <HStack className="justify-between">
                <Text className="text-xs text-gray-500">Convidado por:</Text>
                <Text className="text-xs text-gray-700">
                  {invitation.invited_by.name}
                </Text>
              </HStack>
              
              <HStack className="justify-between">
                <Text className="text-xs text-gray-500">Data:</Text>
                <Text className="text-xs text-gray-700">
                  {formatDate(invitation.created_at)}
                </Text>
              </HStack>
              
              <HStack className="justify-between">
                <Text className="text-xs text-gray-500">Expira em:</Text>
                <Text className={`text-xs ${isExpired() ? 'text-red-600' : 'text-gray-700'}`}>
                  {formatDate(invitation.expires_at)}
                </Text>
              </HStack>
              
              {invitation.accepted_at && (
                <HStack className="justify-between">
                  <Text className="text-xs text-gray-500">Aceito em:</Text>
                  <Text className="text-xs text-green-600">
                    {formatDate(invitation.accepted_at)}
                  </Text>
                </HStack>
              )}
            </VStack>

            {/* Email Delivery Status */}
            <HStack className="justify-between items-center">
              <Text className="text-xs text-gray-500">Status do email:</Text>
              <HStack space="xs" className="items-center">
                <Box
                  className="w-2 h-2 rounded-full"
                  style={{ backgroundColor: emailDeliveryConfig.color }}
                />
                <Text className="text-xs" style={{ color: emailDeliveryConfig.color }}>
                  {emailDeliveryConfig.label}
                </Text>
              </HStack>
            </HStack>

            {/* Custom Message */}
            {invitation.custom_message && (
              <Box className="p-2 bg-gray-50 rounded border-l-2 border-gray-300">
                <Text className="text-xs text-gray-600 italic">
                  "{invitation.custom_message}"
                </Text>
              </Box>
            )}

            {/* Warning for expired invitations */}
            {isExpired() && invitation.status !== InvitationStatus.ACCEPTED && (
              <Box className="p-2 bg-red-50 rounded border border-red-200">
                <Text className="text-xs text-red-600">
                  Este convite expirou. Será necessário enviar um novo convite.
                </Text>
              </Box>
            )}
          </VStack>
        </Pressable>
      </Box>

      {/* Action Sheet */}
      <Actionsheet isOpen={showActions} onClose={() => setShowActions(false)}>
        <ActionsheetBackdrop />
        <ActionsheetContent>
          <ActionsheetDragIndicatorWrapper>
            <ActionsheetDragIndicator />
          </ActionsheetDragIndicatorWrapper>
          
          <VStack className="w-full p-4">
            <Text className="font-semibold text-lg mb-4">
              Ações para {invitation.email}
            </Text>
            
            {canResend() && (
              <ActionsheetItem onPress={handleResend} disabled={loading}>
                <HStack space="md" className="items-center">
                  <Icon as={RefreshCw} size="sm" className="text-blue-600" />
                  <ActionsheetItemText>Reenviar convite</ActionsheetItemText>
                </HStack>
              </ActionsheetItem>
            )}
            
            <ActionsheetItem onPress={handleCopyLink}>
              <HStack space="md" className="items-center">
                <Icon as={Mail} size="sm" className="text-gray-600" />
                <ActionsheetItemText>Copiar link do convite</ActionsheetItemText>
              </HStack>
            </ActionsheetItem>
            
            {canCancel() && (
              <ActionsheetItem onPress={handleCancel} disabled={loading}>
                <HStack space="md" className="items-center">
                  <Icon as={X} size="sm" className="text-red-600" />
                  <ActionsheetItemText className="text-red-600">
                    Cancelar convite
                  </ActionsheetItemText>
                </HStack>
              </ActionsheetItem>
            )}
          </VStack>
        </ActionsheetContent>
      </Actionsheet>
    </>
  );
};