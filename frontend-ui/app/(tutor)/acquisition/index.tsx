import { router } from 'expo-router';
import {
  UserPlusIcon,
  MailIcon,
  LinkIcon,
  QrCodeIcon,
  ShareIcon,
  TrendingUpIcon,
  SendIcon,
  UsersIcon,
  TargetIcon,
  MessageSquareIcon,
  InstagramIcon,
  FacebookIcon,
  TwitterIcon,
} from 'lucide-react-native';
import React, { useState } from 'react';

import MainLayout from '@/components/layouts/MainLayout';
import StudentAcquisitionHub from '@/components/tutor-dashboard/StudentAcquisitionHub';
import { Badge, BadgeText } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Card, CardBody, CardHeader } from '@/components/ui/card';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Input, InputField } from '@/components/ui/input';
import { Pressable } from '@/components/ui/pressable';
import { ScrollView } from '@/components/ui/scroll-view';
import { Text } from '@/components/ui/text';
import { Textarea, TextareaInput } from '@/components/ui/textarea';
import { VStack } from '@/components/ui/vstack';

const TutorAcquisitionPage = () => {
  const [bulkEmails, setBulkEmails] = useState('');
  const [customMessage, setCustomMessage] = useState('');

  // Mock data - in real app, fetch from API
  const acquisitionStats = {
    totalInvitations: 45,
    pendingInvitations: 8,
    acceptedInvitations: 32,
    conversionRate: 71,
    topChannel: 'Email Direto',
    monthlyGrowth: 23,
  };

  const channelPerformance = [
    { name: 'Email Direto', sent: 25, accepted: 21, rate: 84 },
    { name: 'Link Partilhado', sent: 12, accepted: 7, rate: 58 },
    { name: 'Referências', sent: 5, accepted: 4, rate: 80 },
    { name: 'Redes Sociais', sent: 3, accepted: 0, rate: 0 },
  ];

  const handleBulkInvitation = () => {
    // TODO: Implement bulk invitation logic
    console.log('Bulk invitation:', { emails: bulkEmails, message: customMessage });
  };

  const handleSocialShare = (platform: 'instagram' | 'facebook' | 'twitter' | 'whatsapp') => {
    // TODO: Implement social sharing
    console.log('Share on:', platform);
  };

  return (
    <MainLayout _title="Aquisição de Estudantes">
      <ScrollView className="flex-1 bg-gray-50" contentContainerStyle={{ paddingBottom: 100 }}>
        <VStack className="p-6" space="lg">
          {/* Header */}
          <VStack space="sm">
            <HStack className="justify-between items-center">
              <VStack>
                <Heading size="xl" className="text-gray-900">
                  Aquisição de Estudantes
                </Heading>
                <Text className="text-gray-600">
                  Ferramentas para fazer crescer o seu negócio de tutoria
                </Text>
              </VStack>
              <Button variant="outline" onPress={() => router.push('/(tutor)/analytics')}>
                <Icon as={TrendingUpIcon} size="sm" className="text-blue-600 mr-1" />
                <ButtonText className="text-blue-600">Ver Analytics</ButtonText>
              </Button>
            </HStack>
          </VStack>

          {/* Acquisition Stats Overview */}
          <Card
            variant="elevated"
            className="bg-gradient-to-r from-blue-500 to-purple-600 shadow-lg"
          >
            <CardBody>
              <VStack space="md">
                <Text className="text-white font-semibold text-lg">Resumo de Aquisição</Text>
                <HStack space="lg" className="flex-wrap">
                  <VStack className="items-center">
                    <Text className="text-2xl font-bold text-white">
                      {acquisitionStats.totalInvitations}
                    </Text>
                    <Text className="text-blue-100 text-sm">Convites Enviados</Text>
                  </VStack>
                  <VStack className="items-center">
                    <Text className="text-2xl font-bold text-white">
                      {acquisitionStats.acceptedInvitations}
                    </Text>
                    <Text className="text-blue-100 text-sm">Aceites</Text>
                  </VStack>
                  <VStack className="items-center">
                    <Text className="text-2xl font-bold text-white">
                      {acquisitionStats.conversionRate}%
                    </Text>
                    <Text className="text-blue-100 text-sm">Taxa Conversão</Text>
                  </VStack>
                  <VStack className="items-center">
                    <Text className="text-2xl font-bold text-white">
                      +{acquisitionStats.monthlyGrowth}%
                    </Text>
                    <Text className="text-blue-100 text-sm">Crescimento</Text>
                  </VStack>
                </HStack>
              </VStack>
            </CardBody>
          </Card>

          {/* Main Acquisition Hub */}
          <StudentAcquisitionHub
            schoolId={1} // Mock school ID
            tutorName="Professor(a)"
          />

          {/* Bulk Invitation Tool */}
          <Card variant="elevated" className="bg-white shadow-sm">
            <CardHeader>
              <VStack space="xs">
                <Heading size="md" className="text-gray-900">
                  Convites em Massa
                </Heading>
                <Text className="text-sm text-gray-600">
                  Envie convites para múltiplos contactos de uma vez
                </Text>
              </VStack>
            </CardHeader>
            <CardBody>
              <VStack space="md">
                {/* Email List Input */}
                <VStack space="sm">
                  <Text className="text-sm font-medium text-gray-700">
                    Lista de Emails (separados por vírgula ou linha)
                  </Text>
                  <Textarea>
                    <TextareaInput
                      placeholder="email1@exemplo.com, email2@exemplo.com&#10;email3@exemplo.com"
                      value={bulkEmails}
                      onChangeText={setBulkEmails}
                      // @ts-ignore
                      numberOfLines={4}
                    />
                  </Textarea>
                </VStack>

                {/* Custom Message */}
                <VStack space="sm">
                  <Text className="text-sm font-medium text-gray-700">
                    Mensagem Personalizada (Opcional)
                  </Text>
                  <Textarea>
                    <TextareaInput
                      placeholder="Olá! Sou professor(a) especializado(a) em... Convido-te a conhecer as minhas aulas personalizadas."
                      value={customMessage}
                      onChangeText={setCustomMessage}
                      // @ts-ignore
                      numberOfLines={3}
                    />
                  </Textarea>
                </VStack>

                {/* Send Button */}
                <Button
                  variant="solid"
                  onPress={handleBulkInvitation}
                  disabled={!bulkEmails.trim()}
                  className="bg-blue-600"
                >
                  <Icon as={SendIcon} size="sm" className="text-white mr-2" />
                  <ButtonText>Enviar Convites em Massa</ButtonText>
                </Button>

                {/* Tips */}
                <VStack className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                  <Text className="text-sm font-medium text-blue-900">
                    💡 Dicas para Convites Eficazes
                  </Text>
                  <VStack space="xs">
                    <Text className="text-xs text-blue-700">
                      • Personalize a mensagem com o seu nome e especialidades
                    </Text>
                    <Text className="text-xs text-blue-700">
                      • Mencione benefícios específicos (flexibilidade, resultados)
                    </Text>
                    <Text className="text-xs text-blue-700">
                      • Inclua uma oferta especial para novos estudantes
                    </Text>
                  </VStack>
                </VStack>
              </VStack>
            </CardBody>
          </Card>

          {/* Social Media Sharing */}
          <Card variant="elevated" className="bg-white shadow-sm">
            <CardHeader>
              <VStack space="xs">
                <Heading size="md" className="text-gray-900">
                  Partilha em Redes Sociais
                </Heading>
                <Text className="text-sm text-gray-600">
                  Promova os seus serviços de tutoria nas redes sociais
                </Text>
              </VStack>
            </CardHeader>
            <CardBody>
              <VStack space="md">
                <Text className="text-sm font-medium text-gray-700">Partilhar Perfil de Tutor</Text>

                <HStack space="sm" className="flex-wrap">
                  <Pressable
                    onPress={() => handleSocialShare('instagram')}
                    className="flex-1 min-w-[120px] bg-pink-50 border border-pink-200 rounded-lg p-4 items-center"
                  >
                    <Icon as={InstagramIcon} size="md" className="text-pink-600 mb-2" />
                    <Text className="text-sm font-medium text-pink-600">Instagram</Text>
                    <Text className="text-xs text-pink-500">Stories & Posts</Text>
                  </Pressable>

                  <Pressable
                    onPress={() => handleSocialShare('facebook')}
                    className="flex-1 min-w-[120px] bg-blue-50 border border-blue-200 rounded-lg p-4 items-center"
                  >
                    <Icon as={FacebookIcon} size="md" className="text-blue-600 mb-2" />
                    <Text className="text-sm font-medium text-blue-600">Facebook</Text>
                    <Text className="text-xs text-blue-500">Páginas & Grupos</Text>
                  </Pressable>

                  <Pressable
                    onPress={() => handleSocialShare('twitter')}
                    className="flex-1 min-w-[120px] bg-sky-50 border border-sky-200 rounded-lg p-4 items-center"
                  >
                    <Icon as={TwitterIcon} size="md" className="text-sky-600 mb-2" />
                    <Text className="text-sm font-medium text-sky-600">Twitter</Text>
                    <Text className="text-xs text-sky-500">Threads</Text>
                  </Pressable>

                  <Pressable
                    onPress={() => handleSocialShare('whatsapp')}
                    className="flex-1 min-w-[120px] bg-green-50 border border-green-200 rounded-lg p-4 items-center"
                  >
                    <Icon as={MessageSquareIcon} size="md" className="text-green-600 mb-2" />
                    <Text className="text-sm font-medium text-green-600">WhatsApp</Text>
                    <Text className="text-xs text-green-500">Contactos</Text>
                  </Pressable>
                </HStack>

                <VStack className="bg-green-50 border border-green-200 rounded-lg p-3">
                  <Text className="text-sm font-medium text-green-900">
                    📱 Conteúdo Sugerido para Redes Sociais
                  </Text>
                  <VStack space="xs">
                    <Text className="text-xs text-green-700">
                      • Partilhe testemunhos de estudantes satisfeitos
                    </Text>
                    <Text className="text-xs text-green-700">
                      • Publique dicas educativas relacionadas com as suas disciplinas
                    </Text>
                    <Text className="text-xs text-green-700">
                      • Mostre os seus resultados e certificações
                    </Text>
                  </VStack>
                </VStack>
              </VStack>
            </CardBody>
          </Card>

          {/* Channel Performance Analysis */}
          <Card variant="elevated" className="bg-white shadow-sm">
            <CardHeader>
              <Heading size="md" className="text-gray-900">
                Performance dos Canais
              </Heading>
            </CardHeader>
            <CardBody>
              <VStack space="sm">
                {channelPerformance.map((channel, index) => (
                  <VStack key={channel.name} space="xs">
                    <HStack className="justify-between items-center">
                      <VStack>
                        <Text className="text-sm font-medium text-gray-900">{channel.name}</Text>
                        <Text className="text-xs text-gray-600">
                          {channel.sent} enviados • {channel.accepted} aceites
                        </Text>
                      </VStack>
                      <VStack className="items-end">
                        <Badge
                          variant="outline"
                          className={
                            channel.rate >= 70
                              ? 'bg-green-50'
                              : channel.rate >= 40
                              ? 'bg-yellow-50'
                              : 'bg-red-50'
                          }
                        >
                          <BadgeText
                            className={
                              channel.rate >= 70
                                ? 'text-green-700'
                                : channel.rate >= 40
                                ? 'text-yellow-700'
                                : 'text-red-700'
                            }
                          >
                            {channel.rate}%
                          </BadgeText>
                        </Badge>
                      </VStack>
                    </HStack>
                    <VStack className="w-full bg-gray-200 rounded-full h-2">
                      <VStack
                        className={`h-2 rounded-full ${
                          channel.rate >= 70
                            ? 'bg-green-500'
                            : channel.rate >= 40
                            ? 'bg-yellow-500'
                            : 'bg-red-500'
                        }`}
                        style={{ width: `${channel.rate}%` }}
                      />
                    </VStack>
                  </VStack>
                ))}
              </VStack>
            </CardBody>
          </Card>

          {/* Call to Action */}
          <Card
            variant="elevated"
            className="bg-gradient-to-r from-green-50 to-blue-50 border-2 border-dashed border-green-200 shadow-sm"
          >
            <CardBody>
              <VStack space="md" className="items-center text-center">
                <Icon as={TargetIcon} size="lg" className="text-green-600" />
                <VStack space="sm">
                  <Text className="text-lg font-bold text-gray-900">
                    Objetivo: 50 Estudantes até Final do Ano
                  </Text>
                  <Text className="text-sm text-gray-600">
                    Está a {Math.round((32 / 50) * 100)}% do seu objetivo. Continue convidando
                    estudantes!
                  </Text>
                </VStack>
                <HStack space="sm">
                  <Button variant="solid" onPress={() => router.push('/(tutor)/dashboard')}>
                    <ButtonText>Voltar ao Dashboard</ButtonText>
                  </Button>
                  <Button variant="outline" onPress={() => router.push('/(tutor)/analytics')}>
                    <ButtonText className="text-blue-600">Ver Progresso</ButtonText>
                  </Button>
                </HStack>
              </VStack>
            </CardBody>
          </Card>
        </VStack>
      </ScrollView>
    </MainLayout>
  );
};

export default TutorAcquisitionPage;
