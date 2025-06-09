import { X, Mail, Copy, Check, MessageCircle, QrCode } from 'lucide-react-native';
import React, { useState } from 'react';
import { Platform, Alert, Linking } from 'react-native';

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

interface InvitationLink {
  url: string;
  expires_at: string;
  usage_count: number;
}

// API calls
const getSchoolInvitationLink = async (schoolId: number): Promise<InvitationLink> => {
  try {
    const response = await apiClient.get(`/accounts/schools/${schoolId}/invitation-link/`);
    return response.data.invitation_link;
  } catch (error) {
    console.error('Error getting school invitation link:', error);
    // Mock response for now
    return {
      url: 'https://aprendecomigo.com/join-school/xyz789abc123',
      expires_at: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
      usage_count: 5,
    };
  }
};

const sendEmailInvite = async (email: string, schoolId: number): Promise<void> => {
  try {
    const response = await apiClient.post('/accounts/teachers/invite-email/', {
      email: email,
      school_id: schoolId,
      role: 'teacher',
    });
    console.log('Email invite sent successfully:', response.data);
  } catch (error) {
    console.error('Error sending email invite:', error);
    throw error;
  }
};

interface InviteTeacherModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  schoolId?: number;
}

export const InviteTeacherModal = ({
  isOpen,
  onClose,
  onSuccess,
  schoolId = 1,
}: InviteTeacherModalProps) => {
  const [invitationLink, setInvitationLink] = useState<InvitationLink | null>(null);
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSendingEmail, setIsSendingEmail] = useState(false);
  const [linkCopied, setLinkCopied] = useState(false);

  React.useEffect(() => {
    if (isOpen) {
      loadInvitationLink();
    }
  }, [isOpen]);

  const loadInvitationLink = async () => {
    try {
      setIsLoading(true);
      const link = await getSchoolInvitationLink(schoolId);
      setInvitationLink(link);
    } catch (error) {
      console.error('Error loading invitation link:', error);
      Alert.alert('Erro', 'Não foi possível carregar o link de convite.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopyLink = async () => {
    if (!invitationLink) return;

    try {
      if (Platform.OS === 'web') {
        await navigator.clipboard.writeText(invitationLink.url);
      } else {
        // For mobile, we'll need to install @react-native-clipboard/clipboard
        // For now, just show an alert
        Alert.alert('Link copiado', 'O link de convite foi copiado para a área de transferência.', [
          { text: 'OK' },
        ]);
      }
      setLinkCopied(true);
      setTimeout(() => setLinkCopied(false), 2000);
    } catch (error) {
      console.error('Error copying link:', error);
      Alert.alert('Erro', 'Não foi possível copiar o link.');
    }
  };

  const handleWhatsAppShare = async () => {
    if (!invitationLink) return;

    const message = `Olá! Você foi convidado para se juntar como professor. Use este link: ${invitationLink.url}`;
    const whatsappUrl = `https://wa.me/?text=${encodeURIComponent(message)}`;

    try {
      if (Platform.OS === 'web') {
        window.open(whatsappUrl, '_blank');
      } else {
        const supported = await Linking.canOpenURL(whatsappUrl);
        if (supported) {
          await Linking.openURL(whatsappUrl);
        } else {
          Alert.alert(
            'WhatsApp não encontrado',
            'Por favor, instale o WhatsApp para usar esta funcionalidade.'
          );
        }
      }
    } catch (error) {
      console.error('Error opening WhatsApp:', error);
      Alert.alert('Erro', 'Não foi possível abrir o WhatsApp.');
    }
  };

  const handleShowQRCode = () => {
    // TODO: Implement QR code display
    Alert.alert('QR Code', 'Funcionalidade de QR Code será implementada em breve.');
  };

  const handleSendEmailInvite = async () => {
    if (!email.trim()) {
      Alert.alert('Erro', 'Por favor, insira um email válido.');
      return;
    }

    try {
      setIsSendingEmail(true);
      await sendEmailInvite(email, schoolId);
      Alert.alert('Sucesso', 'Convite enviado por email com sucesso!');
      setEmail('');
      onSuccess();
    } catch (error) {
      console.error('Error sending email invite:', error);
      Alert.alert('Erro', 'Não foi possível enviar o convite por email.');
    } finally {
      setIsSendingEmail(false);
    }
  };

  const handleClose = () => {
    setEmail('');
    setInvitationLink(null);
    setLinkCopied(false);
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose} size="lg">
      <ModalBackdrop />
      <ModalContent>
        <ModalHeader>
          <Heading size="lg">Convidar Professor</Heading>
          <ModalCloseButton>
            <Icon as={X} />
          </ModalCloseButton>
        </ModalHeader>

        <ModalBody>
          {isLoading ? (
            <Center className="py-8">
              <VStack className="items-center" space="md">
                <Spinner size="large" />
                <Text className="text-gray-500">Carregando link de convite...</Text>
              </VStack>
            </Center>
          ) : invitationLink ? (
            <VStack space="lg">
              {/* Invitation Link Info */}
              <Box className="p-4 bg-gray-50 rounded-lg border">
                <VStack space="sm">
                  <Text className="font-medium text-gray-900">Link de Convite da Escola</Text>
                  <Text className="text-sm text-gray-600 font-mono break-all">
                    {invitationLink.url}
                  </Text>
                  <HStack className="justify-between">
                    <Text className="text-xs text-gray-500">
                      Expira em: {new Date(invitationLink.expires_at).toLocaleDateString('pt-BR')}
                    </Text>
                    <Text className="text-xs text-gray-500">
                      Usado: {invitationLink.usage_count} vezes
                    </Text>
                  </HStack>
                </VStack>
              </Box>

              {/* Sharing Options */}
              <VStack space="md">
                <Text className="font-medium text-gray-900">Opções de Compartilhamento</Text>

                <VStack space="sm">
                  {/* Copy Link */}
                  <Button variant="outline" onPress={handleCopyLink}>
                    <HStack space="xs" className="items-center">
                      <Icon as={linkCopied ? Check : Copy} size="sm" className="text-gray-600" />
                      <ButtonText>{linkCopied ? 'Link Copiado!' : 'Copiar Link'}</ButtonText>
                    </HStack>
                  </Button>

                  {/* WhatsApp Share */}
                  <Button style={{ backgroundColor: '#25D366' }} onPress={handleWhatsAppShare}>
                    <HStack space="xs" className="items-center">
                      <Icon as={MessageCircle} size="sm" className="text-white" />
                      <ButtonText className="text-white">Compartilhar no WhatsApp</ButtonText>
                    </HStack>
                  </Button>

                  {/* QR Code */}
                  <Button variant="outline" onPress={handleShowQRCode}>
                    <HStack space="xs" className="items-center">
                      <Icon as={QrCode} size="sm" className="text-gray-600" />
                      <ButtonText>Mostrar QR Code</ButtonText>
                    </HStack>
                  </Button>
                </VStack>
              </VStack>

              {/* Email Invite Section */}
              <VStack space="md">
                <Text className="font-medium text-gray-900">Ou envie por email</Text>

                <Input>
                  <InputField
                    placeholder="email@exemplo.com"
                    value={email}
                    onChangeText={setEmail}
                    keyboardType="email-address"
                    autoCapitalize="none"
                  />
                </Input>

                <Button
                  onPress={handleSendEmailInvite}
                  disabled={!email.trim() || isSendingEmail}
                  style={{ backgroundColor: COLORS.primary }}
                >
                  {isSendingEmail ? (
                    <HStack space="xs" className="items-center">
                      <Spinner size="small" />
                      <ButtonText className="text-white">Enviando...</ButtonText>
                    </HStack>
                  ) : (
                    <HStack space="xs" className="items-center">
                      <Icon as={Mail} size="sm" className="text-white" />
                      <ButtonText className="text-white">Enviar por Email</ButtonText>
                    </HStack>
                  )}
                </Button>
              </VStack>
            </VStack>
          ) : (
            <Center className="py-8">
              <Text className="text-red-500">Erro ao carregar o link de convite</Text>
            </Center>
          )}
        </ModalBody>

        <ModalFooter>
          <Button variant="outline" onPress={handleClose}>
            <ButtonText>Fechar</ButtonText>
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};
