import { CheckCircle, AlertCircle, Clock, X, UserCheck, UserX } from 'lucide-react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import React, { useEffect, useState } from 'react';
import { Alert } from 'react-native';

import { useInvitationActions } from '@/hooks/useInvitations';
import InvitationApi, { TeacherInvitation, InvitationStatusResponse } from '@/api/invitationApi';
import MainLayout from '@/components/layouts/main-layout';
import { useAuth } from '@/api/authContext';

import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Center } from '@/components/ui/center';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { Card, CardBody, CardHeader } from '@/components/ui/card';

const AcceptInvitationPage = () => {
  const { token } = useLocalSearchParams<{ token: string }>();
  const router = useRouter();
  const { userProfile, isLoggedIn } = useAuth();
  
  const [invitationData, setInvitationData] = useState<InvitationStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [accepting, setAccepting] = useState(false);
  const [declining, setDeclining] = useState(false);
  const [accepted, setAccepted] = useState(false);
  const [declined, setDeclined] = useState(false);
  const [needsAuth, setNeedsAuth] = useState(false);

  const { acceptInvitation, declineInvitation } = useInvitationActions();

  useEffect(() => {
    if (token) {
      fetchInvitationStatus();
    }
  }, [token]);

  const fetchInvitationStatus = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await InvitationApi.getInvitationStatus(token!);
      setInvitationData(response);
      
      // Check if user needs to authenticate and if invitation email matches current user
      if (isLoggedIn && userProfile && response.invitation.email !== userProfile.email) {
        setError('Este convite não é para o usuário atualmente autenticado. Por favor, faça login com o email correto.');
      } else if (!isLoggedIn) {
        setNeedsAuth(true);
      }
    } catch (err: any) {
      const errorMessage = err.response?.data?.error || 
                          err.response?.data?.detail || 
                          err.message || 
                          'Falha ao carregar informações do convite';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleAcceptInvitation = async () => {
    if (!isLoggedIn) {
      Alert.alert(
        'Autenticação Necessária',
        'Você precisa estar logado para aceitar este convite.',
        [
          { text: 'Cancelar', style: 'cancel' },
          { 
            text: 'Fazer Login', 
            onPress: () => router.push(`/auth/signin?redirect=/accept-invitation/${token}`)
          }
        ]
      );
      return;
    }

    if (!invitationData?.can_accept) {
      Alert.alert('Erro', invitationData?.reason || 'Não é possível aceitar este convite');
      return;
    }

    // For teacher invitations, check if we need to go through profile wizard
    const invitation = invitationData.invitation;
    if (invitation.role === 'teacher') {
      // Check if teacher profile needs to be created/completed
      const needsProfileWizard = invitationData.needs_profile_wizard || 
                               invitationData.wizard_metadata?.requires_profile_completion;
      
      if (needsProfileWizard) {
        // Navigate to profile wizard instead of accepting directly
        router.push(`/accept-invitation/profile-wizard?token=${token}` as any);
        return;
      }
    }

    try {
      setAccepting(true);
      const result = await acceptInvitation(token!);
      setAccepted(true);
      
      Alert.alert(
        'Sucesso!', 
        'Convite aceito com sucesso! Você já faz parte da escola.',
        [
          {
            text: 'Ir para Dashboard',
            onPress: () => {
              // Navigate to appropriate dashboard based on role
              if (result.school_membership.role === 'teacher') {
                router.push('/(tutor)/dashboard');
              } else {
                router.push('/(school-admin)/dashboard');
              }
            }
          }
        ]
      );
    } catch (err) {
      // Error handling is done in the hook
    } finally {
      setAccepting(false);
    }
  };

  const handleDeclineInvitation = async () => {
    Alert.alert(
      'Declinar Convite',
      'Tem certeza de que deseja declinar este convite? Esta ação não pode ser desfeita.',
      [
        { text: 'Cancelar', style: 'cancel' },
        {
          text: 'Declinar',
          style: 'destructive',
          onPress: async () => {
            try {
              setDeclining(true);
              await declineInvitation(token!);
              setDeclined(true);
              Alert.alert('Convite Declinado', 'O convite foi declinado com sucesso.');
            } catch (err) {
              // Error handling is done in the hook
            } finally {
              setDeclining(false);
            }
          }
        }
      ]
    );
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'accepted':
        return { icon: CheckCircle, color: '#10B981' };
      case 'expired':
      case 'cancelled':
        return { icon: X, color: '#EF4444' };
      default:
        return { icon: Clock, color: '#F59E0B' };
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: 'long',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (loading) {
    return (
      <Center className="flex-1">
        <VStack space="md" className="items-center">
          <Spinner size="large" />
          <Text className="text-gray-600">Carregando convite...</Text>
        </VStack>
      </Center>
    );
  }

  if (error || !invitationData) {
    return (
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
          <Button variant="outline" onPress={fetchInvitationStatus}>
            <ButtonText>Tentar novamente</ButtonText>
          </Button>
        </VStack>
      </Center>
    );
  }

  const invitation = invitationData.invitation;
  const statusConfig = getStatusIcon(invitation.status);

  if (accepted || invitation.status === 'accepted') {
    return (
      <Center className="flex-1 p-6">
        <VStack space="lg" className="items-center max-w-md">
          <Icon as={CheckCircle} size="xl" className="text-green-500" />
          <VStack space="sm" className="items-center">
            <Heading size="lg" className="text-center text-gray-900">
              Convite Aceito!
            </Heading>
            <Text className="text-center text-gray-600">
              Você já faz parte da escola {invitation.school.name}.
            </Text>
          </VStack>
          <Button 
            variant="solid"
            onPress={() => {
              // Navigate to dashboard based on role
              if (invitation.role === 'teacher') {
                router.push('/(tutor)/dashboard');
              } else {
                router.push('/(school-admin)/dashboard');
              }
            }}
          >
            <ButtonText>Ir para Dashboard</ButtonText>
          </Button>
        </VStack>
      </Center>
    );
  }

  if (declined || invitation.status === 'declined') {
    return (
      <Center className="flex-1 p-6">
        <VStack space="lg" className="items-center max-w-md">
          <Icon as={UserX} size="xl" className="text-red-500" />
          <VStack space="sm" className="items-center">
            <Heading size="lg" className="text-center text-gray-900">
              Convite Declinado
            </Heading>
            <Text className="text-center text-gray-600">
              Você declinou o convite para se juntar à escola {invitation.school.name}.
            </Text>
          </VStack>
          <Button 
            variant="outline"
            onPress={() => router.push('/')}
          >
            <ButtonText>Voltar ao Início</ButtonText>
          </Button>
        </VStack>
      </Center>
    );
  }

  // Show authentication prompt if user needs to log in
  if (needsAuth) {
    return (
      <Center className="flex-1 p-6">
        <VStack space="lg" className="items-center max-w-md">
          <Icon as={UserCheck} size="xl" className="text-blue-500" />
          <VStack space="sm" className="items-center">
            <Heading size="lg" className="text-center text-gray-900">
              Autenticação Necessária
            </Heading>
            <Text className="text-center text-gray-600">
              Para aceitar este convite, você precisa fazer login com o email {invitation?.email}.
            </Text>
          </VStack>
          <VStack space="sm" className="w-full">
            <Button 
              variant="solid"
              onPress={() => router.push(`/auth/signin?redirect=/accept-invitation/${token}`)}
            >
              <ButtonText>Fazer Login</ButtonText>
            </Button>
            <Button 
              variant="outline"
              onPress={() => router.push(`/auth/signup?email=${invitation?.email}&redirect=/accept-invitation/${token}`)}
            >
              <ButtonText>Criar Conta</ButtonText>
            </Button>
          </VStack>
        </VStack>
      </Center>
    );
  }

  return (
    <Box className="flex-1 bg-gray-50 p-6">
      <Center className="flex-1">
        <Box className="w-full max-w-md">
          <Card variant="elevated" className="bg-white shadow-lg">
            <CardHeader className="text-center">
              <VStack space="md" className="items-center">
                <Icon 
                  as={statusConfig.icon} 
                  size="xl" 
                  className={`text-[${statusConfig.color}]`}
                />
                <VStack space="xs" className="items-center">
                  <Heading size="lg" className="text-gray-900">
                    Convite para Professor
                  </Heading>
                  <Text className="text-gray-600">
                    {invitation.school.name}
                  </Text>
                </VStack>
              </VStack>
            </CardHeader>

            <CardBody>
              <VStack space="lg">
                {/* Invitation Details */}
                <VStack space="md">
                  <Box className="p-4 bg-gray-50 rounded-lg">
                    <VStack space="sm">
                      <HStack className="justify-between">
                        <Text className="text-sm text-gray-500">Email:</Text>
                        <Text className="text-sm font-medium">{invitation.email}</Text>
                      </HStack>
                      
                      <HStack className="justify-between">
                        <Text className="text-sm text-gray-500">Função:</Text>
                        <Text className="text-sm font-medium">
                          {invitation.role === 'teacher' ? 'Professor' : 
                           invitation.role === 'school_admin' ? 'Administrador' : 
                           invitation.role}
                        </Text>
                      </HStack>
                      
                      <HStack className="justify-between">
                        <Text className="text-sm text-gray-500">Convidado por:</Text>
                        <Text className="text-sm font-medium">{invitation.invited_by.name}</Text>
                      </HStack>
                      
                      <HStack className="justify-between">
                        <Text className="text-sm text-gray-500">Data do convite:</Text>
                        <Text className="text-sm font-medium">
                          {formatDate(invitation.created_at)}
                        </Text>
                      </HStack>
                      
                      <HStack className="justify-between">
                        <Text className="text-sm text-gray-500">Expira em:</Text>
                        <Text className={`text-sm font-medium ${
                          new Date(invitation.expires_at) < new Date() ? 'text-red-600' : ''
                        }`}>
                          {formatDate(invitation.expires_at)}
                        </Text>
                      </HStack>
                    </VStack>
                  </Box>

                  {/* Custom Message */}
                  {invitation.custom_message && (
                    <Box className="p-4 bg-blue-50 rounded-lg border-l-4 border-blue-400">
                      <VStack space="xs">
                        <Text className="text-sm font-medium text-blue-900">
                          Mensagem pessoal:
                        </Text>
                        <Text className="text-sm text-blue-800 italic">
                          "{invitation.custom_message}"
                        </Text>
                      </VStack>
                    </Box>
                  )}
                </VStack>

                {/* Action Buttons */}
                <VStack space="sm">
                  {invitationData.can_accept ? (
                    <>
                      <Button 
                        onPress={handleAcceptInvitation}
                        disabled={accepting || declining}
                        className="bg-green-600"
                      >
                        {accepting ? (
                          <HStack space="xs" className="items-center">
                            <Spinner size="small" />
                            <ButtonText className="text-white">Processando...</ButtonText>
                          </HStack>
                        ) : (
                          <ButtonText className="text-white">
                            {invitation.role === 'teacher' && (invitationData.needs_profile_wizard || invitationData.wizard_metadata?.requires_profile_completion) 
                              ? 'Configurar Perfil' 
                              : 'Aceitar Convite'}
                          </ButtonText>
                        )}
                      </Button>
                      
                      <Button 
                        variant="outline"
                        onPress={handleDeclineInvitation}
                        disabled={accepting || declining}
                        className="border-red-300"
                      >
                        {declining ? (
                          <HStack space="xs" className="items-center">
                            <Spinner size="small" />
                            <ButtonText className="text-red-600">Declinando...</ButtonText>
                          </HStack>
                        ) : (
                          <ButtonText className="text-red-600">Declinar Convite</ButtonText>
                        )}
                      </Button>
                    </>
                  ) : (
                    <Box className="p-3 bg-red-50 rounded border border-red-200">
                      <Text className="text-sm text-red-700 text-center">
                        {invitationData.reason || 'Este convite não pode ser aceito'}
                      </Text>
                    </Box>
                  )}
                  
                  <Button 
                    variant="outline"
                    onPress={() => router.push('/')}
                  >
                    <ButtonText>Voltar ao Início</ButtonText>
                  </Button>
                </VStack>
              </VStack>
            </CardBody>
          </Card>
        </Box>
      </Center>
    </Box>
  );
};

// Export wrapped with MainLayout
export const AcceptInvitationPageWithLayout = () => {
  return (
    <MainLayout _title="Aceitar Convite">
      <AcceptInvitationPage />
    </MainLayout>
  );
};

export default AcceptInvitationPageWithLayout;