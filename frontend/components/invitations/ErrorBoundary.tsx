import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Alert } from 'react-native';

import InvitationErrorDisplay from './InvitationErrorDisplay';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  resetOnPropsChange?: boolean;
  resetKeys?: Array<string | number>;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  prevResetKeys?: Array<string | number>;
}

export class InvitationErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      prevResetKeys: props.resetKeys,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    // Update state so the next render will show the fallback UI
    return {
      hasError: true,
      error,
    };
  }

  static getDerivedStateFromProps(props: Props, state: State): Partial<State> | null {
    const { resetKeys } = props;
    const { prevResetKeys, hasError } = state;

    // If resetKeys have changed and we had an error, reset the boundary
    if (hasError && resetKeys && prevResetKeys) {
      const hasResetKeyChanged = resetKeys.some((key, index) => prevResetKeys[index] !== key);

      if (hasResetKeyChanged) {
        return {
          hasError: false,
          error: null,
          errorInfo: null,
          prevResetKeys: resetKeys,
        };
      }
    }

    // Update prevResetKeys if they've changed
    if (resetKeys !== prevResetKeys) {
      return {
        prevResetKeys: resetKeys,
      };
    }

    return null;
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Update state with error info
    this.setState({
      error,
      errorInfo,
    });

    // Log error details
    console.error('InvitationErrorBoundary caught an error:', error, errorInfo);

    // Call custom error handler if provided
    this.props.onError?.(error, errorInfo);

    // In development, show more detailed error information
    if (__DEV__) {
      console.error('Error boundary details:', {
        error: error.message,
        stack: error.stack,
        componentStack: errorInfo.componentStack,
      });
    }
  }

  handleRetry = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  handleGoHome = () => {
    // This should be handled by the parent component or router
    // For now, we'll reset the error boundary
    this.handleRetry();
  };

  handleContactSupport = () => {
    const { error, errorInfo } = this.state;

    const errorReport = {
      message: error?.message || 'Unknown error',
      stack: error?.stack,
      componentStack: errorInfo?.componentStack,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
    };

    // In a real app, you would send this to your error reporting service
    if (__DEV__) {
      if (__DEV__) {
        console.log('Error report for support:', errorReport);
      }
    }

    Alert.alert(
      'Relatório de Erro',
      'As informações do erro foram coletadas. Por favor, entre em contato com nosso suporte através do email suporte@aprendecomigo.com',
      [{ text: 'OK', onPress: this.handleRetry }],
    );
  };

  render() {
    const { hasError, error } = this.state;
    const { children, fallback } = this.props;

    if (hasError) {
      // If a custom fallback is provided, use it
      if (fallback) {
        return fallback;
      }

      // Otherwise, show our default error display
      return (
        <InvitationErrorDisplay
          error={{
            code: 'REACT_ERROR_BOUNDARY',
            message: error?.message || 'Ocorreu um erro inesperado na aplicação',
            details: __DEV__
              ? {
                  stack: error?.stack,
                  componentStack: this.state.errorInfo?.componentStack,
                }
              : undefined,
            timestamp: new Date().toISOString(),
          }}
          onRetry={this.handleRetry}
          onGoHome={this.handleGoHome}
          onContactSupport={this.handleContactSupport}
          showRetry={true}
          showGoHome={false}
          showContactSupport={true}
        />
      );
    }

    return children;
  }
}

// Higher-order component wrapper for functional components
export interface WithErrorBoundaryProps {
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  resetKeys?: Array<string | number>;
}

export function withInvitationErrorBoundary<P extends object>(
  Component: React.ComponentType<P>,
  errorBoundaryProps?: WithErrorBoundaryProps,
) {
  const WrappedComponent = (props: P) => (
    <InvitationErrorBoundary {...errorBoundaryProps}>
      <Component {...props} />
    </InvitationErrorBoundary>
  );

  WrappedComponent.displayName = `withInvitationErrorBoundary(${
    Component.displayName || Component.name || 'Component'
  })`;

  return WrappedComponent;
}

export default InvitationErrorBoundary;
