import { useLocalSearchParams, useRouter } from 'expo-router';
import { CheckCircle, AlertCircle, ArrowLeft } from 'lucide-react-native';
import React, { useEffect, useState } from 'react';
import { Alert } from 'react-native';

import { useAuth, useUserProfile } from '@/api/auth';
import InvitationApi, { InvitationStatusResponse } from '@/api/invitationApi';
import MainLayout from '@/components/layouts/MainLayout';
import ProfileWizard from '@/components/profile-wizard/ProfileWizard';
import { Button, ButtonText } from '@/components/ui/button';
import { Center } from '@/components/ui/center';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

const AcceptInvitationProfileWizardPage = () => {
  const { token } = useLocalSearchParams<{ token: string }>();
  const router = useRouter();
  const { isLoggedIn } = useAuth();
  const { userProfile } = useUserProfile();

  const [invitationData, setInvitationData] = useState<InvitationStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (token) {
      fetchInvitationStatus();
    } else {
      setError('Token de convite não fornecido');
      setLoading(false);
    }
  }, [token]);

  const fetchInvitationStatus = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await InvitationApi.getInvitationStatus(token!);
      setInvitationData(response);

      // Validate invitation is for a teacher and requires profile wizard
      const invitation = response.invitation;
      if (invitation.role !== 'teacher') {
        setError('Este convite não é para um professor. Redirecionando...');
        setTimeout(() => {
          router.replace(`/accept-invitation/${token}`);
        }, 2000);
        return;
      }

      // Check if user needs to authenticate and if invitation email matches current user
      if (isLoggedIn && userProfile && invitation.email !== userProfile.email) {
        setError(
          'Este convite não é para o usuário atualmente autenticado. Por favor, faça login com o email correto.',
        );
        return;
      }

      if (!isLoggedIn) {
        Alert.alert(
          'Autenticação Necessária',
          'Você precisa estar logado para configurar seu perfil.',
          [
            { text: 'Cancelar', onPress: () => router.back() },
            {
              text: 'Fazer Login',
              onPress: () =>
                router.push(
                  `/auth/signin?redirect=/accept-invitation/profile-wizard?token=${token}`,
                ),
            },
          ],
        );
        return;
      }

      // Check if invitation can be accepted
      if (!response.can_accept) {
        setError(response.reason || 'Este convite não pode ser aceito');
        return;
      }
    } catch (err: any) {
      const errorMessage =
        err.response?.data?.error ||
        err.response?.data?.detail ||
        err.message ||
        'Falha ao carregar informações do convite';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleWizardSuccess = () => {
    // ProfileWizard already handles invitation acceptance and shows success alert
    // Navigate to teacher dashboard after successful profile creation
    router.replace('/(school-admin)/dashboard');
  };

  const handleWizardCancel = () => {
    Alert.alert(
      'Cancelar Configuração?',
      'Você pode configurar seu perfil mais tarde, mas algumas funcionalidades podem estar limitadas.',
      [
        { text: 'Continuar Configurando', style: 'cancel' },
        {
          text: 'Cancelar',
          style: 'destructive',
          onPress: () => {
            // Navigate back to invitation page
            router.back();
          },
        },
      ],
    );
  };

  const handleBackToInvitation = () => {
    router.back();
  };

  // Check if this invitation actually needs profile wizard
  const needsProfileWizard =
    invitationData?.needs_profile_wizard ||
    invitationData?.wizard_metadata?.requires_profile_completion;

  // Auto-redirect to regular invitation acceptance if profile wizard is not needed
  useEffect(() => {
    if (invitationData && !needsProfileWizard) {
      const timer = setTimeout(() => {
        router.replace(`/accept-invitation/${token}`);
      }, 2000);

      return () => clearTimeout(timer);
    }
  }, [invitationData, needsProfileWizard, router, token]);

  if (loading) {
    return (
      <MainLayout _title="Configuração do Perfil">
        <Center className="flex-1">
          <VStack space="md" className="items-center">
            <Spinner size="large" />
            <Text className="text-gray-600">Carregando dados do convite...</Text>
          </VStack>
        </Center>
      </MainLayout>
    );
  }

  if (error || !invitationData) {
    return (
      <MainLayout _title="Erro">
        <Center className="flex-1 p-6">
          <VStack space="lg" className="items-center max-w-md">
            <Icon as={AlertCircle} size="xl" className="text-red-500" />
            <VStack space="sm" className="items-center">
              <Heading size="lg" className="text-center text-gray-900">
                Erro ao carregar convite
              </Heading>
              <Text className="text-center text-gray-600">
                {error || 'O convite não pôde ser encontrado ou é inválido.'}
              </Text>
            </VStack>
            <VStack space="sm" className="w-full">
              <Button variant="outline" onPress={fetchInvitationStatus}>
                <ButtonText>Tentar novamente</ButtonText>
              </Button>
              <Button variant="outline" onPress={handleBackToInvitation}>
                <HStack space="xs" className="items-center">
                  <Icon as={ArrowLeft} size="sm" />
                  <ButtonText>Voltar ao Convite</ButtonText>
                </HStack>
              </Button>
            </VStack>
          </VStack>
        </Center>
      </MainLayout>
    );
  }

  if (!needsProfileWizard) {
    return (
      <MainLayout _title="Redirecionando">
        <Center className="flex-1 p-6">
          <VStack space="lg" className="items-center max-w-md">
            <Icon as={CheckCircle} size="xl" className="text-green-500" />
            <VStack space="sm" className="items-center">
              <Heading size="lg" className="text-center text-gray-900">
                Perfil já configurado
              </Heading>
              <Text className="text-center text-gray-600">
                Seu perfil já está configurado. Redirecionando para aceitar o convite...
              </Text>
            </VStack>
            <Spinner size="small" />
          </VStack>
        </Center>
      </MainLayout>
    );
  }

  return (
    <MainLayout _title="Configuração do Perfil">
      <ProfileWizard
        invitationToken={token!}
        invitationData={invitationData}
        onSuccess={handleWizardSuccess}
        onCancel={handleWizardCancel}
      />
    </MainLayout>
  );
};

export default AcceptInvitationProfileWizardPage;
