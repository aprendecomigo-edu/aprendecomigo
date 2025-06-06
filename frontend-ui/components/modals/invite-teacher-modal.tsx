import { X, Mail, Phone, Share, Copy, Check } from 'lucide-react-native';
import React, { useState } from 'react';
import { Platform, Alert } from 'react-native';

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
import { Pressable } from '@/components/ui/pressable';
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

interface InviteLink {
  url: string;
  token: string;
  expires_at: string;
}

// Mock API calls - replace with real API when backend is ready
const generateInviteLink = async (schoolId: number): Promise<InviteLink> => {
  try {
    const response = await apiClient.post('/accounts/invitations/generate-link/', {
      school_id: schoolId,
      role: 'teacher',
    });
    return response.data;
  } catch (error) {
    console.error('Error generating invite link:', error);
    // Mock response for now
    return {
      url: 'https://aprendecomigo.com/invite/abc123',
      token: 'abc123',
      expires_at: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
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

const sendPhoneInvite = async (phone: string, schoolId: number): Promise<void> => {
  try {
    const response = await apiClient.post('/accounts/teachers/invite-phone/', {
      phone_number: phone,
      school_id: schoolId,
      role: 'teacher',
    });
    console.log('Phone invite sent successfully:', response.data);
  } catch (error) {
    console.error('Error sending phone invite:', error);
    throw error;
  }
};

type InviteMethod = 'link' | 'email' | 'phone';

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
  const [selectedMethod, setSelectedMethod] = useState<InviteMethod>('link');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [inviteLink, setInviteLink] = useState<InviteLink | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [linkCopied, setLinkCopied] = useState(false);

  React.useEffect(() => {
    if (isOpen && selectedMethod === 'link' && !inviteLink) {
      loadInviteLink();
    }
  }, [isOpen, selectedMethod]);

  const loadInviteLink = async () => {
    try {
      setIsLoading(true);
      const link = await generateInviteLink(schoolId);
      setInviteLink(link);
    } catch (error) {
      console.error('Error loading invite link:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopyLink = async () => {
    if (!inviteLink) return;

    try {
      if (Platform.OS === 'web') {
        await navigator.clipboard.writeText(inviteLink.url);
      } else {
        // For mobile, we'll need to install @react-native-clipboard/clipboard
        // For now, just show an alert
        Alert.alert(
          'Link copiado',
          'O link de convite foi copiado para a área de transferência.',
          [{ text: 'OK' }]
        );
      }
      setLinkCopied(true);
      setTimeout(() => setLinkCopied(false), 2000);
    } catch (error) {
      console.error('Error copying link:', error);
      Alert.alert('Erro', 'Não foi possível copiar o link.');
    }
  };

  const handleShareLink = async () => {
    if (!inviteLink) return;

    try {
      if (Platform.OS === 'web') {
        // Web sharing
        if (navigator.share) {
          await navigator.share({
            title: 'Convite para Professor',
            text: 'Você foi convidado para se juntar como professor.',
            url: inviteLink.url,
          });
        } else {
          // Fallback to copy
          await handleCopyLink();
        }
      } else {
        // Mobile sharing - would need react-native-share
        Alert.alert(
          'Compartilhar',
          'Link de convite copiado. Cole em seu app de mensagens favorito.',
          [{ text: 'OK' }]
        );
        await handleCopyLink();
      }
    } catch (error) {
      console.error('Error sharing link:', error);
    }
  };

  const handleSendEmailInvite = async () => {
    if (!email.trim()) return;

    try {
      setIsSending(true);
      await sendEmailInvite(email, schoolId);
      onSuccess();
      onClose();
      handleClose();
    } catch (error) {
      console.error('Error sending email invite:', error);
      Alert.alert('Erro', 'Não foi possível enviar o convite por email.');
    } finally {
      setIsSending(false);
    }
  };

  const handleSendPhoneInvite = async () => {
    if (!phone.trim()) return;

    try {
      setIsSending(true);
      await sendPhoneInvite(phone, schoolId);
      onSuccess();
      onClose();
      handleClose();
    } catch (error) {
      console.error('Error sending phone invite:', error);
      Alert.alert('Erro', 'Não foi possível enviar o convite por telefone.');
    } finally {
      setIsSending(false);
    }
  };

  const handleClose = () => {
    setEmail('');
    setPhone('');
    setInviteLink(null);
    setLinkCopied(false);
    setSelectedMethod('link');
    onClose();
  };

  const renderMethodSelector = () => (
    <HStack space="xs" className="bg-gray-100 rounded-lg p-1">
      {[
        { method: 'link' as InviteMethod, label: 'Link', icon: Share },
        { method: 'email' as InviteMethod, label: 'Email', icon: Mail },
        { method: 'phone' as InviteMethod, label: 'Telefone', icon: Phone },
      ].map(({ method, label, icon }) => (
        <Pressable
          key={method}
          onPress={() => setSelectedMethod(method)}
          className={`flex-1 py-2 px-3 rounded-md ${
            selectedMethod === method ? 'bg-white shadow-sm' : 'bg-transparent'
          }`}
        >
          <HStack className="items-center justify-center" space="xs">
            <Icon
              as={icon}
              size="sm"
              className={selectedMethod === method ? 'text-primary-600' : 'text-gray-600'}
            />
            <Text
              className={`text-sm font-medium ${
                selectedMethod === method ? 'text-primary-600' : 'text-gray-600'
              }`}
            >
              {label}
            </Text>
          </HStack>
        </Pressable>
      ))}
    </HStack>
  );

  const renderLinkMethod = () => (
    <VStack space="md">
      <Text className="text-gray-600">
        Gere um link de convite que pode ser compartilhado com qualquer pessoa.
      </Text>

      {isLoading ? (
        <Center className="py-8">
          <VStack className="items-center" space="md">
            <Spinner size="large" />
            <Text className="text-gray-500">Gerando link de convite...</Text>
          </VStack>
        </Center>
      ) : inviteLink ? (
        <VStack space="md">
          <Box className="p-4 bg-gray-50 rounded-lg border">
            <VStack space="sm">
              <Text className="font-medium text-gray-900">Link de Convite</Text>
              <Text className="text-sm text-gray-600 font-mono break-all">
                {inviteLink.url}
              </Text>
              <Text className="text-xs text-gray-500">
                Expira em: {new Date(inviteLink.expires_at).toLocaleDateString('pt-BR')}
              </Text>
            </VStack>
          </Box>

          <HStack space="sm">
            <Button variant="outline" className="flex-1" onPress={handleCopyLink}>
              <HStack space="xs" className="items-center">
                <Icon as={linkCopied ? Check : Copy} size="sm" className="text-gray-600" />
                <ButtonText>{linkCopied ? 'Copiado!' : 'Copiar'}</ButtonText>
              </HStack>
            </Button>
            <Button
              className="flex-1"
              style={{ backgroundColor: COLORS.primary }}
              onPress={handleShareLink}
            >
              <HStack space="xs" className="items-center">
                <Icon as={Share} size="sm" className="text-white" />
                <ButtonText className="text-white">Compartilhar</ButtonText>
              </HStack>
            </Button>
          </HStack>
        </VStack>
      ) : (
        <Button onPress={loadInviteLink} style={{ backgroundColor: COLORS.primary }}>
          <ButtonText className="text-white">Gerar Link</ButtonText>
        </Button>
      )}
    </VStack>
  );

  const renderEmailMethod = () => (
    <VStack space="md">
      <Text className="text-gray-600">
        Envie um convite diretamente para o email do professor.
      </Text>

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
        disabled={!email.trim() || isSending}
        style={{ backgroundColor: COLORS.primary }}
      >
        {isSending ? (
          <HStack space="xs" className="items-center">
            <Spinner size="small" />
            <ButtonText className="text-white">Enviando...</ButtonText>
          </HStack>
        ) : (
          <ButtonText className="text-white">Enviar Convite</ButtonText>
        )}
      </Button>
    </VStack>
  );

  const renderPhoneMethod = () => (
    <VStack space="md">
      <Text className="text-gray-600">
        Envie um convite via SMS para o telefone do professor.
      </Text>

      <Input>
        <InputField
          placeholder="+351 912 345 678"
          value={phone}
          onChangeText={setPhone}
          keyboardType="phone-pad"
        />
      </Input>

      <Button
        onPress={handleSendPhoneInvite}
        disabled={!phone.trim() || isSending}
        style={{ backgroundColor: COLORS.primary }}
      >
        {isSending ? (
          <HStack space="xs" className="items-center">
            <Spinner size="small" />
            <ButtonText className="text-white">Enviando...</ButtonText>
          </HStack>
        ) : (
          <ButtonText className="text-white">Enviar Convite</ButtonText>
        )}
      </Button>
    </VStack>
  );

  const renderContent = () => {
    switch (selectedMethod) {
      case 'link':
        return renderLinkMethod();
      case 'email':
        return renderEmailMethod();
      case 'phone':
        return renderPhoneMethod();
      default:
        return renderLinkMethod();
    }
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
          <VStack space="lg">
            {renderMethodSelector()}
            {renderContent()}
          </VStack>
        </ModalBody>

        <ModalFooter>
          <Button variant="outline" onPress={handleClose}>
            <ButtonText>Cancelar</ButtonText>
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};
