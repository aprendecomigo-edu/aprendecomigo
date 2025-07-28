import { X, Mail, Copy, Check, MessageCircle, QrCode, Users } from 'lucide-react-native';
import React, { useState } from 'react';
import { Platform, Alert, Linking } from 'react-native';

import { useInviteTeacher, useBulkInvitations } from '@/hooks/useInvitations';
import { SchoolRole } from '@/api/invitationApi';
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
import { Select, SelectTrigger, SelectInput, SelectIcon, SelectPortal, SelectBackdrop, SelectContent, SelectDragIndicatorWrapper, SelectDragIndicator, SelectItem } from '@/components/ui/select';
import { ChevronDownIcon } from '@/components/ui/icon';
import { Textarea, TextareaInput } from '@/components/ui/textarea';
import { Divider } from '@/components/ui/divider';
import { Badge, BadgeText } from '@/components/ui/badge';

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

// Role options for dropdown
const ROLE_OPTIONS = [
  { value: SchoolRole.TEACHER, label: 'Professor', description: 'Pode dar aulas e gerenciar estudantes' },
  { value: SchoolRole.SCHOOL_ADMIN, label: 'Administrador', description: 'Pode gerenciar escola e professores' },
];

// Invitation mode
type InvitationMode = 'single' | 'bulk';

// API calls (keeping link functionality for now)
const getSchoolInvitationLink = async (schoolId: number): Promise<InvitationLink> => {
  try {
    // This endpoint might not exist yet, using mock data
    return {
      url: 'https://aprendecomigo.com/join-school/xyz789abc123',
      expires_at: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
      usage_count: 5,
    };
  } catch (error) {
    console.error('Error getting school invitation link:', error);
    throw error;
  }
};

// Helper function to parse bulk emails
const parseBulkEmails = (text: string): string[] => {
  return text
    .split(/[,\n;]+/) // Split by comma, newline, or semicolon
    .map(email => email.trim())
    .filter(email => email.length > 0 && email.includes('@'));
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
  const [bulkEmails, setBulkEmails] = useState('');
  const [selectedRole, setSelectedRole] = useState<SchoolRole>(SchoolRole.TEACHER);
  const [customMessage, setCustomMessage] = useState('');
  const [invitationMode, setInvitationMode] = useState<InvitationMode>('single');
  const [isLoading, setIsLoading] = useState(false);
  const [linkCopied, setLinkCopied] = useState(false);
  
  // Use hooks
  const { inviteTeacher, loading: inviteLoading } = useInviteTeacher();
  const { sendBulkInvitations, loading: bulkLoading, progress, resetProgress } = useBulkInvitations();

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
      await inviteTeacher({
        email: email.trim(),
        school_id: schoolId,
        role: selectedRole,
        custom_message: customMessage.trim() || undefined,
      });
      
      Alert.alert('Sucesso', 'Convite enviado por email com sucesso!');
      setEmail('');
      setCustomMessage('');
      onSuccess();
    } catch (error) {
      // Error handling is done in the hook
      console.error('Error sending email invite:', error);
    }
  };

  const handleBulkInvite = async () => {
    const emails = parseBulkEmails(bulkEmails);
    
    if (emails.length === 0) {
      Alert.alert('Erro', 'Por favor, insira pelo menos um email válido.');
      return;
    }

    if (emails.length > 50) {
      Alert.alert('Erro', 'Máximo de 50 convites por vez.');
      return;
    }

    try {
      const response = await sendBulkInvitations({
        school_id: schoolId,
        invitations: emails.map(email => ({
          email,
          role: selectedRole,
          custom_message: customMessage.trim() || undefined,
        })),
      });

      // Show results
      const { summary } = response;
      let message = `Processados: ${summary.total_requested}\n`;
      message += `Sucesso: ${summary.total_created}\n`;
      if (summary.total_duplicates > 0) {
        message += `Duplicados: ${summary.total_duplicates}\n`;
      }
      if (summary.total_errors > 0) {
        message += `Erros: ${summary.total_errors}`;
      }

      Alert.alert('Convites Enviados', message);
      setBulkEmails('');
      setCustomMessage('');
      resetProgress();
      onSuccess();
    } catch (error) {
      // Error handling is done in the hook
      console.error('Error sending bulk invites:', error);
    }
  };

  const handleClose = () => {
    setEmail('');
    setBulkEmails('');
    setCustomMessage('');
    setSelectedRole(SchoolRole.TEACHER);
    setInvitationMode('single');
    setInvitationLink(null);
    setLinkCopied(false);
    resetProgress();
    onClose();
  };

  const getCurrentEmails = () => {
    if (invitationMode === 'bulk') {
      return parseBulkEmails(bulkEmails);
    }
    return email.trim() ? [email.trim()] : [];
  };

  const isFormValid = () => {
    const emails = getCurrentEmails();
    return emails.length > 0 && emails.every(e => e.includes('@'));
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

              <Divider className="my-4" />
              
              {/* Email Invite Section */}
              <VStack space="lg">
                <Text className="font-medium text-gray-900">Convitar por Email</Text>

                {/* Mode Selection */}
                <HStack space="sm">
                  <Button
                    variant={invitationMode === 'single' ? 'solid' : 'outline'}
                    size="sm"
                    onPress={() => setInvitationMode('single')}
                    style={invitationMode === 'single' ? { backgroundColor: COLORS.primary } : {}}
                  >
                    <HStack space="xs" className="items-center">
                      <Icon as={Mail} size="sm" className={invitationMode === 'single' ? 'text-white' : 'text-gray-600'} />
                      <ButtonText className={invitationMode === 'single' ? 'text-white' : 'text-gray-600'}>
                        Único
                      </ButtonText>
                    </HStack>
                  </Button>
                  
                  <Button
                    variant={invitationMode === 'bulk' ? 'solid' : 'outline'}
                    size="sm"
                    onPress={() => setInvitationMode('bulk')}
                    style={invitationMode === 'bulk' ? { backgroundColor: COLORS.primary } : {}}
                  >
                    <HStack space="xs" className="items-center">
                      <Icon as={Users} size="sm" className={invitationMode === 'bulk' ? 'text-white' : 'text-gray-600'} />
                      <ButtonText className={invitationMode === 'bulk' ? 'text-white' : 'text-gray-600'}>
                        Múltiplos
                      </ButtonText>
                    </HStack>
                  </Button>
                </HStack>

                {/* Role Selection */}
                <VStack space="sm">
                  <Text className="text-sm font-medium text-gray-700">Função</Text>
                  <Select selectedValue={selectedRole} onValueChange={setSelectedRole}>
                    <SelectTrigger variant="outline" size="md">
                      <SelectInput placeholder="Selecionar função" />
                      <SelectIcon className="mr-3" as={ChevronDownIcon} />
                    </SelectTrigger>
                    <SelectPortal>
                      <SelectBackdrop />
                      <SelectContent>
                        <SelectDragIndicatorWrapper>
                          <SelectDragIndicator />
                        </SelectDragIndicatorWrapper>
                        {ROLE_OPTIONS.map((option) => (
                          <SelectItem key={option.value} label={option.label} value={option.value}>
                            <VStack>
                              <Text className="font-medium">{option.label}</Text>
                              <Text className="text-xs text-gray-500">{option.description}</Text>
                            </VStack>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </SelectPortal>
                  </Select>
                </VStack>

                {/* Email Input - Single Mode */}
                {invitationMode === 'single' && (
                  <VStack space="sm">
                    <Text className="text-sm font-medium text-gray-700">Email</Text>
                    <Input>
                      <InputField
                        placeholder="email@exemplo.com"
                        value={email}
                        onChangeText={setEmail}
                        keyboardType="email-address"
                        autoCapitalize="none"
                      />
                    </Input>
                  </VStack>
                )}

                {/* Bulk Email Input */}
                {invitationMode === 'bulk' && (
                  <VStack space="sm">
                    <HStack className="justify-between items-center">
                      <Text className="text-sm font-medium text-gray-700">Emails</Text>
                      <Text className="text-xs text-gray-500">
                        {parseBulkEmails(bulkEmails).length} emails válidos
                      </Text>
                    </HStack>
                    <Textarea>
                      <TextareaInput
                        placeholder="email1@exemplo.com, email2@exemplo.com
ou um por linha"
                        value={bulkEmails}
                        onChangeText={setBulkEmails}
                        numberOfLines={4}
                        textAlignVertical="top"
                      />
                    </Textarea>
                    <Text className="text-xs text-gray-500">
                      Separe os emails por vírgula, ponto e vírgula ou quebra de linha. Máximo 50 emails.
                    </Text>
                  </VStack>
                )}

                {/* Custom Message */}
                <VStack space="sm">
                  <Text className="text-sm font-medium text-gray-700">Mensagem personalizada (opcional)</Text>
                  <Textarea>
                    <TextareaInput
                      placeholder="Adicione uma mensagem personalizada ao convite..."
                      value={customMessage}
                      onChangeText={setCustomMessage}
                      numberOfLines={3}
                      textAlignVertical="top"
                      maxLength={500}
                    />
                  </Textarea>
                  <Text className="text-xs text-gray-500">
                    {customMessage.length}/500 caracteres
                  </Text>
                </VStack>

                {/* Progress indicator for bulk */}
                {invitationMode === 'bulk' && (progress.total > 0) && (
                  <Box className="p-3 bg-blue-50 rounded-lg">
                    <VStack space="xs">
                      <Text className="text-sm font-medium">Progresso do envio:</Text>
                      <HStack space="md">
                        <Badge variant="solid" className="bg-green-500">
                          <BadgeText className="text-white">Sucesso: {progress.completed}</BadgeText>
                        </Badge>
                        {progress.failed > 0 && (
                          <Badge variant="solid" className="bg-red-500">
                            <BadgeText className="text-white">Falha: {progress.failed}</BadgeText>
                          </Badge>
                        )}
                      </HStack>
                    </VStack>
                  </Box>
                )}

                {/* Send Button */}
                <Button
                  onPress={invitationMode === 'single' ? handleSendEmailInvite : handleBulkInvite}
                  disabled={!isFormValid() || inviteLoading || bulkLoading}
                  style={{ backgroundColor: COLORS.primary }}
                >
                  {(inviteLoading || bulkLoading) ? (
                    <HStack space="xs" className="items-center">
                      <Spinner size="small" />
                      <ButtonText className="text-white">
                        {invitationMode === 'bulk' ? 'Enviando...' : 'Enviando...'}
                      </ButtonText>
                    </HStack>
                  ) : (
                    <HStack space="xs" className="items-center">
                      <Icon as={invitationMode === 'bulk' ? Users : Mail} size="sm" className="text-white" />
                      <ButtonText className="text-white">
                        {invitationMode === 'bulk' 
                          ? `Enviar ${getCurrentEmails().length} Convites` 
                          : 'Enviar Convite'
                        }
                      </ButtonText>
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
