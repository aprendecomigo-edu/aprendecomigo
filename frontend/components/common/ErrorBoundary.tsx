import { AlertTriangle } from 'lucide-react-native';
import React, { Component, ReactNode } from 'react';

import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Center } from '@/components/ui/center';
import { Heading } from '@/components/ui/heading';
import { Icon } from '@/components/ui/icon';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
  errorInfo?: React.ErrorInfo;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    // Update state so the next render will show the fallback UI
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // Log the error to monitoring service
    console.error('ErrorBoundary caught an error:', error, errorInfo);

    this.setState({
      error,
      errorInfo,
    });

    // In production, you would send this to your error monitoring service
    // Example: Sentry.captureException(error, { extra: errorInfo });
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: undefined, errorInfo: undefined });
  };

  render() {
    if (this.state.hasError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default fallback UI
      return (
        <Box className="flex-1 p-8">
          <Center>
            <VStack className="items-center max-w-md" space="lg">
              <Icon as={AlertTriangle} size="xl" className="text-red-500" />

              <VStack className="items-center" space="sm">
                <Heading size="lg" className="text-gray-900 text-center">
                  Algo deu errado
                </Heading>
                <Text className="text-gray-600 text-center">
                  Ocorreu um erro inesperado. Nossa equipe foi notificada e está trabalhando para
                  resolver o problema.
                </Text>
              </VStack>

              {__DEV__ && this.state.error && (
                <Box className="w-full p-3 bg-red-50 rounded-lg border border-red-200">
                  <Text className="text-xs text-red-800 font-mono">
                    {this.state.error.toString()}
                  </Text>
                  {this.state.errorInfo?.componentStack && (
                    <Text className="text-xs text-red-600 font-mono mt-2">
                      {this.state.errorInfo.componentStack}
                    </Text>
                  )}
                </Box>
              )}

              <VStack space="sm" className="w-full">
                <Button
                  onPress={this.handleRetry}
                  className="w-full"
                  accessibilityLabel="Tentar novamente"
                  accessibilityHint="Toque para recarregar a tela"
                >
                  <ButtonText>Tentar Novamente</ButtonText>
                </Button>

                <Button
                  variant="outline"
                  onPress={() => {
                    // In a real app, you might navigate to home or reload the app
                    if (typeof window !== 'undefined') {
                      window.location.reload();
                    }
                  }}
                  className="w-full"
                  accessibilityLabel="Recarregar aplicação"
                  accessibilityHint="Toque para recarregar toda a aplicação"
                >
                  <ButtonText>Recarregar App</ButtonText>
                </Button>
              </VStack>
            </VStack>
          </Center>
        </Box>
      );
    }

    return this.props.children;
  }
}

// Higher-order component wrapper for easier usage
export function withErrorBoundary<P extends object>(
  Component: React.ComponentType<P>,
  fallback?: ReactNode
) {
  const WrappedComponent = (props: P) => (
    <ErrorBoundary fallback={fallback}>
      <Component {...props} />
    </ErrorBoundary>
  );

  WrappedComponent.displayName = `withErrorBoundary(${Component.displayName || Component.name})`;

  return WrappedComponent;
}

export default ErrorBoundary;
