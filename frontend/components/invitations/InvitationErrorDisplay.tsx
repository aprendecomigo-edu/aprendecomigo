import { AlertCircle, RefreshCw, Clock, UserX, Shield, AlertTriangle } from 'lucide-react-native';
import React from 'react';

import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Card, CardBody, CardHeader } from '@/components/ui/card';
import { Center } from '@/components/ui/center';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

export interface InvitationError {
  code?: string;
  message: string;
  details?: Record<string, any>;
  timestamp?: string;
  path?: string;
}

interface InvitationErrorDisplayProps {
  error: InvitationError | string;
  onRetry?: () => void;
  onGoHome?: () => void;
  onContactSupport?: () => void;
  retrying?: boolean;
  showRetry?: boolean;
  showGoHome?: boolean;
  showContactSupport?: boolean;
}

export const InvitationErrorDisplay: React.FC<InvitationErrorDisplayProps> = ({
  error,
  onRetry,
  onGoHome,
  onContactSupport,
  retrying = false,
  showRetry = true,
  showGoHome = true,
  showContactSupport = false,
}) => {
  const errorData: InvitationError = typeof error === 'string' ? { message: error } : error;

  const getErrorConfig = (code?: string) => {
    switch (code) {
      case 'INVITATION_NOT_FOUND':
        return {
          icon: AlertCircle,
          color: '#EF4444',
          title: 'Convite Não Encontrado',
          description:
            'Este convite não existe ou o link pode estar incorreto. Verifique o link recebido por email.',
          severity: 'error' as const,
          showRetry: false,
          showContactSupport: true,
        };

      case 'INVITATION_EXPIRED':
        return {
          icon: Clock,
          color: '#F59E0B',
          title: 'Convite Expirado',
          description:
            'Este convite expirou. Entre em contato com a escola para solicitar um novo convite.',
          severity: 'warning' as const,
          showRetry: false,
          showContactSupport: true,
        };

      case 'AUTHENTICATION_REQUIRED':
        return {
          icon: Shield,
          color: '#3B82F6',
          title: 'Autenticação Necessária',
          description: 'Você precisa fazer login com o email correto para aceitar este convite.',
          severity: 'info' as const,
          showRetry: true,
          showContactSupport: false,
        };

      case 'DUPLICATE_MEMBERSHIP':
        return {
          icon: UserX,
          color: '#F59E0B',
          title: 'Já Faz Parte da Escola',
          description: 'Você já é membro desta escola. Verifique seu dashboard de escolas.',
          severity: 'warning' as const,
          showRetry: false,
          showContactSupport: false,
        };

      case 'INVITATION_ALREADY_PROCESSED':
        return {
          icon: AlertTriangle,
          color: '#F59E0B',
          title: 'Convite Já Processado',
          description: 'Este convite já foi aceito ou recusado anteriormente.',
          severity: 'warning' as const,
          showRetry: false,
          showContactSupport: false,
        };

      case 'NETWORK_ERROR':
        return {
          icon: RefreshCw,
          color: '#6B7280',
          title: 'Erro de Conexão',
          description:
            'Não foi possível conectar ao servidor. Verifique sua conexão e tente novamente.',
          severity: 'error' as const,
          showRetry: true,
          showContactSupport: false,
        };

      case 'SERVER_ERROR':
        return {
          icon: AlertCircle,
          color: '#EF4444',
          title: 'Erro do Servidor',
          description: 'Ocorreu um erro interno no servidor. Tente novamente em alguns minutos.',
          severity: 'error' as const,
          showRetry: true,
          showContactSupport: true,
        };

      default:
        return {
          icon: AlertCircle,
          color: '#EF4444',
          title: 'Erro Inesperado',
          description: errorData.message || 'Ocorreu um erro inesperado. Tente novamente.',
          severity: 'error' as const,
          showRetry: true,
          showContactSupport: true,
        };
    }
  };

  const config = getErrorConfig(errorData.code);
  const IconComponent = config.icon;

  const getSeverityColors = (severity: string) => {
    switch (severity) {
      case 'error':
        return {
          bg: 'bg-red-50',
          border: 'border-red-200',
          icon: 'text-red-500',
          title: 'text-red-900',
          description: 'text-red-700',
        };
      case 'warning':
        return {
          bg: 'bg-yellow-50',
          border: 'border-yellow-200',
          icon: 'text-yellow-500',
          title: 'text-yellow-900',
          description: 'text-yellow-700',
        };
      case 'info':
        return {
          bg: 'bg-blue-50',
          border: 'border-blue-200',
          icon: 'text-blue-500',
          title: 'text-blue-900',
          description: 'text-blue-700',
        };
      default:
        return {
          bg: 'bg-gray-50',
          border: 'border-gray-200',
          icon: 'text-gray-500',
          title: 'text-gray-900',
          description: 'text-gray-700',
        };
    }
  };

  const colors = getSeverityColors(config.severity);

  return (
    <Center className="flex-1 p-6">
      <Box className="w-full max-w-md">
        <Card variant="elevated" className={`${colors.bg} ${colors.border} border shadow-lg`}>
          <CardHeader className="text-center">
            <VStack space="md" className="items-center">
              <Box className={`${colors.icon} w-12 h-12 flex items-center justify-center`}>
                <IconComponent size={48} color="inherit" />
              </Box>
              <VStack space="xs" className="items-center">
                <Heading size="lg" className={colors.title}>
                  {config.title}
                </Heading>
                <Text className={`${colors.description} text-center`}>{config.description}</Text>
              </VStack>
            </VStack>
          </CardHeader>

          <CardBody>
            <VStack space="md">
              {/* Technical Details (Development Only) */}
              {__DEV__ && errorData.details && (
                <Box className="p-3 bg-gray-100 rounded border">
                  <Text className="text-xs text-gray-600 font-mono">
                    Code: {errorData.code || 'UNKNOWN'}
                  </Text>
                  {errorData.timestamp && (
                    <Text className="text-xs text-gray-600 font-mono">
                      Time: {errorData.timestamp}
                    </Text>
                  )}
                  {errorData.path && (
                    <Text className="text-xs text-gray-600 font-mono">Path: {errorData.path}</Text>
                  )}
                </Box>
              )}

              {/* Action Buttons */}
              <VStack space="sm">
                {showRetry && (config.showRetry || onRetry) && (
                  <Button
                    variant="solid"
                    onPress={onRetry}
                    disabled={retrying}
                    className={
                      config.severity === 'error'
                        ? 'bg-red-600'
                        : config.severity === 'warning'
                          ? 'bg-yellow-600'
                          : config.severity === 'info'
                            ? 'bg-blue-600'
                            : 'bg-gray-600'
                    }
                  >
                    {retrying ? (
                      <HStack space="xs" className="items-center">
                        <Spinner size="small" />
                        <ButtonText className="text-white">Tentando novamente...</ButtonText>
                      </HStack>
                    ) : (
                      <HStack space="xs" className="items-center">
                        <RefreshCw size={16} color="white" />
                        <ButtonText className="text-white">Tentar Novamente</ButtonText>
                      </HStack>
                    )}
                  </Button>
                )}

                {showContactSupport && (config.showContactSupport || onContactSupport) && (
                  <Button
                    variant="outline"
                    onPress={onContactSupport}
                    className={
                      config.severity === 'error'
                        ? 'border-red-300'
                        : config.severity === 'warning'
                          ? 'border-yellow-300'
                          : config.severity === 'info'
                            ? 'border-blue-300'
                            : 'border-gray-300'
                    }
                  >
                    <ButtonText
                      className={
                        config.severity === 'error'
                          ? 'text-red-600'
                          : config.severity === 'warning'
                            ? 'text-yellow-600'
                            : config.severity === 'info'
                              ? 'text-blue-600'
                              : 'text-gray-600'
                      }
                    >
                      Entrar em Contato com Suporte
                    </ButtonText>
                  </Button>
                )}

                {showGoHome && onGoHome && (
                  <Button variant="outline" onPress={onGoHome} className="border-gray-300">
                    <ButtonText className="text-gray-600">Voltar ao Início</ButtonText>
                  </Button>
                )}
              </VStack>
            </VStack>
          </CardBody>
        </Card>
      </Box>
    </Center>
  );
};

export default InvitationErrorDisplay;
