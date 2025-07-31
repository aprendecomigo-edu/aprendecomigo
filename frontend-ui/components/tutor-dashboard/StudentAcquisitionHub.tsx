import { 
  MailIcon, 
  LinkIcon, 
  QrCodeIcon, 
  ShareIcon, 
  UserPlusIcon,
  SendIcon,
  CopyIcon,
  CheckIcon
} from 'lucide-react-native';
import React, { useState, useCallback } from 'react';
import { Alert } from 'react-native';

import { Card, CardBody, CardHeader } from '@/components/ui/card';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { Button, ButtonText } from '@/components/ui/button';
import { Input, InputField } from '@/components/ui/input';
import { Badge, BadgeText } from '@/components/ui/badge';
import { Pressable } from '@/components/ui/pressable';

interface StudentAcquisitionHubProps {
  schoolId: number;
  tutorName: string;
}

interface InvitationStats {
  sent: number;
  pending: number;
  accepted: number;
  conversionRate: number;
}

const StudentAcquisitionHub: React.FC<StudentAcquisitionHubProps> = ({
  schoolId,
  tutorName,
}) => {
  const [emailInput, setEmailInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [copiedLink, setCopiedLink] = useState(false);
  
  // Mock invitation stats - in real app, fetch from API
  const invitationStats: InvitationStats = {
    sent: 12,
    pending: 3,
    accepted: 9,
    conversionRate: 75,
  };

  // Generate tutor discovery link
  const discoveryLink = `https://aprendecomigo.pt/tutor/${schoolId}`;

  const handleEmailInvitation = useCallback(async () => {
    if (!emailInput.trim()) {
      Alert.alert('Erro', 'Por favor, insira um endereço de email válido');
      return;
    }

    try {
      setIsLoading(true);
      
      // TODO: Implement actual email invitation API call
      // await sendStudentInvitation({ email: emailInput, schoolId });
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      Alert.alert(
        'Convite Enviado!', 
        `Convite enviado para ${emailInput}. O estudante receberá um email com instruções para se inscrever.`
      );
      setEmailInput('');
    } catch (error) {
      Alert.alert('Erro', 'Falha ao enviar convite. Tente novamente.');
    } finally {
      setIsLoading(false);
    }
  }, [emailInput, schoolId]);

  const handleCopyLink = useCallback(async () => {
    try {
      // On web, use navigator.clipboard, on mobile use expo-clipboard
      if (typeof navigator !== 'undefined' && navigator.clipboard) {
        await navigator.clipboard.writeText(discoveryLink);
      } else {
        // For mobile, you'd typically use expo-clipboard here
        console.log('Copy to clipboard:', discoveryLink);
      }
      
      setCopiedLink(true);
      setTimeout(() => setCopiedLink(false), 2000);
    } catch (error) {
      Alert.alert('Erro', 'Não foi possível copiar o link');
    }
  }, [discoveryLink]);

  const handleShareLink = useCallback(() => {
    // TODO: Implement native sharing (expo-sharing)
    const shareText = `Olá! Sou ${tutorName}, tutor(a) profissional. Convido-te a conhecer as minhas aulas personalizadas. Vê o meu perfil: ${discoveryLink}`;
    
    if (typeof navigator !== 'undefined' && navigator.share) {
      navigator.share({
        title: `Aulas com ${tutorName}`,
        text: shareText,
        url: discoveryLink,
      });
    } else {
      Alert.alert(
        'Partilhar Perfil',
        shareText,
        [
          { text: 'Cancelar', style: 'cancel' },
          { text: 'Copiar', onPress: handleCopyLink },
        ]
      );
    }
  }, [tutorName, discoveryLink, handleCopyLink]);

  const handleQRCode = useCallback(() => {
    // TODO: Generate and display QR code modal
    Alert.alert(
      'Código QR',
      'Funcionalidade de código QR será implementada em breve. Permite aos estudantes escanearem para aceder diretamente ao teu perfil.'
    );
  }, []);

  return (
    <Card variant="elevated" className="bg-white shadow-sm">
      <CardHeader>
        <VStack space="xs">
          <Heading size="md" className="text-gray-900">
            Aquisição de Estudantes
          </Heading>
          <Text className="text-sm text-gray-600">
            Convida novos estudantes e faz crescer o teu negócio
          </Text>
        </VStack>
      </CardHeader>
      
      <CardBody>
        <VStack space="lg">
          {/* Invitation Stats */}
          <VStack space="sm">
            <Text className="text-sm font-medium text-gray-700">
              Estatísticas de Convites
            </Text>
            <HStack space="md" className="flex-wrap">
              <Badge variant="outline" className="flex-row items-center space-x-1">
                <Icon as={SendIcon} size="xs" className="text-blue-600" />
                <BadgeText className="text-blue-600">{invitationStats.sent} enviados</BadgeText>
              </Badge>
              <Badge variant="outline" className="flex-row items-center space-x-1">
                <Icon as={UserPlusIcon} size="xs" className="text-green-600" />
                <BadgeText className="text-green-600">{invitationStats.accepted} aceites</BadgeText>
              </Badge>
              <Badge variant="outline" className="flex-row items-center space-x-1">
                <BadgeText className="text-purple-600">{invitationStats.conversionRate}% conversão</BadgeText>
              </Badge>
            </HStack>
          </VStack>

          {/* Email Invitation */}
          <VStack space="sm">
            <Text className="text-sm font-medium text-gray-700">
              Convite por Email
            </Text>
            <VStack space="sm">
              <Input variant="outline">
                <InputField
                  placeholder="email@exemplo.com"
                  value={emailInput}
                  onChangeText={setEmailInput}
                  keyboardType="email-address"
                  autoCapitalize="none"
                />
              </Input>
              <Button 
                onPress={handleEmailInvitation}
                disabled={isLoading || !emailInput.trim()}
                className="bg-blue-600"
              >
                <Icon as={MailIcon} size="sm" className="text-white mr-2" />
                <ButtonText>
                  {isLoading ? 'Enviando...' : 'Enviar Convite'}
                </ButtonText>
              </Button>
            </VStack>
          </VStack>

          {/* Shareable Link */}
          <VStack space="sm">
            <Text className="text-sm font-medium text-gray-700">
              Link de Descoberta
            </Text>
            <VStack space="sm">
              <VStack className="bg-gray-50 rounded-lg p-3 border border-gray-200">
                <Text className="text-sm text-gray-600 break-all">
                  {discoveryLink}
                </Text>
              </VStack>
              <HStack space="sm">
                <Button 
                  variant="outline"
                  className="flex-1"
                  onPress={handleCopyLink}
                >
                  <Icon 
                    as={copiedLink ? CheckIcon : CopyIcon} 
                    size="sm" 
                    className={copiedLink ? "text-green-600 mr-2" : "text-gray-600 mr-2"} 
                  />
                  <ButtonText className={copiedLink ? "text-green-600" : "text-gray-600"}>
                    {copiedLink ? 'Copiado!' : 'Copiar'}
                  </ButtonText>
                </Button>
                <Button 
                  variant="outline"
                  className="flex-1"
                  onPress={handleShareLink}
                >
                  <Icon as={ShareIcon} size="sm" className="text-blue-600 mr-2" />
                  <ButtonText className="text-blue-600">Partilhar</ButtonText>
                </Button>
              </HStack>
            </VStack>
          </VStack>

          {/* Quick Actions */}
          <VStack space="sm">
            <Text className="text-sm font-medium text-gray-700">
              Ferramentas Adicionais
            </Text>
            <HStack space="sm">
              <Pressable 
                onPress={handleQRCode}
                className="flex-1 bg-purple-50 border border-purple-200 rounded-lg p-4 items-center"
              >
                <Icon as={QrCodeIcon} size="sm" className="text-purple-600 mb-1" />
                <Text className="text-xs font-medium text-purple-600 text-center">
                  Código QR
                </Text>
              </Pressable>
              
              <Pressable 
                onPress={() => Alert.alert('Em Breve', 'Funcionalidades de redes sociais em desenvolvimento')}
                className="flex-1 bg-orange-50 border border-orange-200 rounded-lg p-4 items-center"
              >
                <Icon as={LinkIcon} size="sm" className="text-orange-600 mb-1" />
                <Text className="text-xs font-medium text-orange-600 text-center">
                  Redes Sociais
                </Text>
              </Pressable>
            </HStack>
          </VStack>

          {/* Tips */}
          <VStack space="xs" className="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <Text className="text-sm font-medium text-blue-900">
              💡 Dicas para Maximizar Conversões
            </Text>
            <VStack space="xs">
              <Text className="text-xs text-blue-700">
                • Personaliza a mensagem do convite com o nome do estudante
              </Text>
              <Text className="text-xs text-blue-700">
                • Menciona as disciplinas específicas que ensinas
              </Text>
              <Text className="text-xs text-blue-700">
                • Oferece uma primeira aula gratuita ou com desconto
              </Text>
            </VStack>
          </VStack>
        </VStack>
      </CardBody>
    </Card>
  );
};

export { StudentAcquisitionHub };
export default StudentAcquisitionHub;