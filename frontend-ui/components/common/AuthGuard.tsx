import React, { ReactNode } from 'react';
import { Shield, AlertTriangle } from 'lucide-react-native';

import { useAuth } from '@/api/authContext';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Center } from '@/components/ui/center';
import { Heading } from '@/components/ui/heading';
import { Icon } from '@/components/ui/icon';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

interface AuthGuardProps {
  children: ReactNode;
  requiredRoles?: string[];
  fallback?: ReactNode;
  showSpinner?: boolean;
}

export const AuthGuard: React.FC<AuthGuardProps> = ({
  children,
  requiredRoles = [],
  fallback,
  showSpinner = true,
}) => {
  const { userProfile, isLoading, isAuthenticated, logout } = useAuth();

  // Show loading spinner while authentication is being checked
  if (isLoading && showSpinner) {
    return (
      <Box className="flex-1 p-8">
        <Center>
          <VStack className="items-center" space="md">
            <Spinner size="large" />
            <Text className="text-gray-500">Verificando autenticação...</Text>
          </VStack>
        </Center>
      </Box>
    );
  }

  // User is not authenticated
  if (!isAuthenticated || !userProfile) {
    if (fallback) {
      return <>{fallback}</>;
    }

    return (
      <Box className="flex-1 p-8">
        <Center>
          <VStack className="items-center max-w-md" space="lg">
            <Icon as={Shield} size="xl" className="text-red-500" />
            
            <VStack className="items-center" space="sm">
              <Heading size="lg" className="text-gray-900 text-center">
                Acesso Negado
              </Heading>
              <Text className="text-gray-600 text-center">
                Você precisa estar logado para acessar esta página.
              </Text>
            </VStack>

            <Button
              onPress={() => {
                // Navigate to login - this would be handled by your router
                console.log('Navigate to login');
              }}
              className="w-full"
              accessibilityLabel="Fazer login"
              accessibilityHint="Toque para ir para a página de login"
            >
              <ButtonText>Fazer Login</ButtonText>
            </Button>
          </VStack>
        </Center>
      </Box>
    );
  }

  // Check if user has required roles
  if (requiredRoles.length > 0) {
    const userRoles = userProfile.school_memberships?.map(
      (membership: any) => membership.role
    ) || [];
    
    const hasRequiredRole = requiredRoles.some(role => userRoles.includes(role));
    
    if (!hasRequiredRole) {
      if (fallback) {
        return <>{fallback}</>;
      }

      return (
        <Box className="flex-1 p-8">
          <Center>
            <VStack className="items-center max-w-md" space="lg">
              <Icon as={AlertTriangle} size="xl" className="text-orange-500" />
              
              <VStack className="items-center" space="sm">
                <Heading size="lg" className="text-gray-900 text-center">
                  Permissão Insuficiente
                </Heading>
                <Text className="text-gray-600 text-center">
                  Você não tem as permissões necessárias para acessar esta funcionalidade.
                </Text>
                <Text className="text-sm text-gray-500 text-center">
                  Roles necessárias: {requiredRoles.join(', ')}
                </Text>
              </VStack>

              <VStack space="sm" className="w-full">
                <Button
                  variant="outline"
                  onPress={() => {
                    // Navigate back - this would be handled by your router
                    console.log('Navigate back');
                  }}
                  className="w-full"
                  accessibilityLabel="Voltar"
                  accessibilityHint="Toque para voltar à página anterior"
                >
                  <ButtonText>Voltar</ButtonText>
                </Button>

                <Button
                  variant="outline"
                  onPress={logout}
                  className="w-full"
                  accessibilityLabel="Fazer logout"
                  accessibilityHint="Toque para sair da conta atual"
                >
                  <ButtonText>Trocar Conta</ButtonText>
                </Button>
              </VStack>
            </VStack>
          </Center>
        </Box>
      );
    }
  }

  // Check if user has active school membership for admin features
  const hasActiveSchoolMembership = userProfile.school_memberships?.some(
    (membership: any) => 
      membership.is_active && 
      (membership.role === 'school_owner' || membership.role === 'school_admin')
  );

  if (requiredRoles.includes('school_admin') && !hasActiveSchoolMembership) {
    if (fallback) {
      return <>{fallback}</>;
    }

    return (
      <Box className="flex-1 p-8">
        <Center>
          <VStack className="items-center max-w-md" space="lg">
            <Icon as={AlertTriangle} size="xl" className="text-orange-500" />
            
            <VStack className="items-center" space="sm">
              <Heading size="lg" className="text-gray-900 text-center">
                Escola Não Configurada
              </Heading>
              <Text className="text-gray-600 text-center">
                Você precisa estar associado a uma escola ativa para acessar o gerenciamento de alunos.
              </Text>
            </VStack>

            <Button
              variant="outline"
              onPress={() => {
                // Navigate to school setup or contact support
                console.log('Navigate to school setup');
              }}
              className="w-full"
              accessibilityLabel="Configurar escola"
              accessibilityHint="Toque para configurar sua escola"
            >
              <ButtonText>Configurar Escola</ButtonText>
            </Button>
          </VStack>
        </Center>
      </Box>
    );
  }

  // User is authenticated and has required permissions
  return <>{children}</>;
};

// Higher-order component wrapper for easier usage
export function withAuthGuard<P extends object>(
  Component: React.ComponentType<P>,
  requiredRoles?: string[],
  fallback?: ReactNode
) {
  const WrappedComponent = (props: P) => (
    <AuthGuard requiredRoles={requiredRoles} fallback={fallback}>
      <Component {...props} />
    </AuthGuard>
  );

  WrappedComponent.displayName = `withAuthGuard(${Component.displayName || Component.name})`;
  
  return WrappedComponent;
}

export default AuthGuard;