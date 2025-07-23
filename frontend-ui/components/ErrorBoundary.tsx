import React, { Component, ReactNode } from 'react';
import { VStack } from '@/components/ui/vstack';
import { Heading } from '@/components/ui/heading';
import { Text } from '@/components/ui/text';
import { Button, ButtonText } from '@/components/ui/button';
import { Box } from '@/components/ui/box';
import { Icon } from '@/components/ui/icon';
import { AlertTriangle } from 'lucide-react-native';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    // Update state so the next render will show the fallback UI
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // Log the error for debugging
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    
    // Call the optional error handler
    this.props.onError?.(error, errorInfo);
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: undefined });
  };

  render() {
    if (this.state.hasError) {
      // Return custom fallback UI or the provided fallback
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <VStack className="flex-1 items-center justify-center p-6" space="lg">
          <Box className="w-16 h-16 bg-red-100 rounded-full items-center justify-center">
            <Icon 
              as={AlertTriangle} 
              size="xl" 
              className="text-red-600"
              accessibilityLabel="Error icon"
            />
          </Box>
          
          <VStack space="md" className="items-center">
            <Heading size="xl" className="text-gray-900 text-center">
              Something went wrong
            </Heading>
            <Text size="md" className="text-gray-600 text-center max-w-md">
              We encountered an unexpected error. Please try again or contact support if the problem persists.
            </Text>
          </VStack>

          <VStack space="sm" className="w-full max-w-xs">
            <Button 
              onPress={this.handleRetry}
              className="w-full"
              accessibilityLabel="Try again"
              accessibilityHint="Retry the previous action"
            >
              <ButtonText>Try Again</ButtonText>
            </Button>
            
            <Button 
              variant="outline"
              onPress={() => {
                // Reload the app - this will work in a real app environment
                if (typeof window !== 'undefined' && window.location) {
                  window.location.reload();
                }
              }}
              className="w-full"
              accessibilityLabel="Refresh page"
              accessibilityHint="Reload the application"
            >
              <ButtonText>Refresh Page</ButtonText>
            </Button>
          </VStack>

          {__DEV__ && this.state.error && (
            <VStack space="sm" className="mt-4 p-4 bg-gray-100 rounded-lg max-w-full">
              <Text size="sm" className="font-bold text-gray-800">
                Debug Info (Development Only):
              </Text>
              <Text size="xs" className="text-gray-600 font-mono">
                {this.state.error.toString()}
              </Text>
            </VStack>
          )}
        </VStack>
      );
    }

    return this.props.children;
  }
}

// Higher-order component for easy wrapping
export function withErrorBoundary<P extends object>(
  Component: React.ComponentType<P>,
  errorBoundaryProps?: Omit<Props, 'children'>
) {
  const WrappedComponent = (props: P) => (
    <ErrorBoundary {...errorBoundaryProps}>
      <Component {...props} />
    </ErrorBoundary>
  );

  WrappedComponent.displayName = `withErrorBoundary(${Component.displayName || Component.name})`;
  
  return WrappedComponent;
} 