import { AlertTriangle, RefreshCw } from 'lucide-react-native';
import React, { Component, ReactNode } from 'react';

import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Center } from '@/components/ui/center';
import { Heading } from '@/components/ui/heading';
import { Icon } from '@/components/ui/icon';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class InvitationErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('InvitationErrorBoundary caught an error:', error, errorInfo);

    // Call the optional error handler
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: undefined });
  };

  render() {
    if (this.state.hasError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default error UI
      return (
        <Box className="p-6 bg-red-50 border border-red-200 rounded-lg m-4">
          <Center>
            <VStack space="md" className="items-center max-w-md">
              <Icon as={AlertTriangle} size="xl" className="text-red-500" />
              <VStack space="sm" className="items-center">
                <Heading size="lg" className="text-red-900 text-center">
                  Erro no Sistema de Convites
                </Heading>
                <Text className="text-red-700 text-center">
                  Ocorreu um erro inesperado. Por favor, tente novamente.
                </Text>
                {__DEV__ && this.state.error && (
                  <Text className="text-xs text-red-600 font-mono text-center mt-2">
                    {this.state.error.message}
                  </Text>
                )}
              </VStack>
              <Button variant="outline" onPress={this.handleRetry} className="border-red-300">
                <Icon as={RefreshCw} size="sm" className="text-red-600 mr-2" />
                <ButtonText className="text-red-600">Tentar Novamente</ButtonText>
              </Button>
            </VStack>
          </Center>
        </Box>
      );
    }

    return this.props.children;
  }
}

// Higher-order component wrapper for functional components
export const withInvitationErrorBoundary = <P extends object>(
  Component: React.ComponentType<P>,
  errorBoundaryProps?: Omit<Props, 'children'>
) => {
  const WrappedComponent = (props: P) => (
    <InvitationErrorBoundary {...errorBoundaryProps}>
      <Component {...props} />
    </InvitationErrorBoundary>
  );

  WrappedComponent.displayName = `withInvitationErrorBoundary(${
    Component.displayName || Component.name
  })`;

  return WrappedComponent;
};
