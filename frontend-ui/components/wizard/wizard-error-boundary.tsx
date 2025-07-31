import React, { Component, ErrorInfo, ReactNode } from 'react';
import { RefreshCw, AlertTriangle, Home, Save } from 'lucide-react-native';

import { Box } from '@/components/ui/box';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Heading } from '@/components/ui/heading';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';

interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
  errorInfo?: ErrorInfo;
  errorId: string;
  retryCount: number;
}

interface WizardErrorBoundaryProps {
  children: ReactNode;
  onReset?: () => void;
  onSaveAndExit?: () => Promise<void>;
  onGoToDashboard?: () => void;
  fallback?: ReactNode;
  maxRetries?: number;
}

interface ErrorDetails {
  message: string;
  stack?: string;
  componentStack?: string;
  timestamp: number;
  userAgent: string;
  url: string;
}

class WizardErrorBoundary extends Component<WizardErrorBoundaryProps, ErrorBoundaryState> {
  private retryTimeouts: NodeJS.Timeout[] = [];

  constructor(props: WizardErrorBoundaryProps) {
    super(props);
    
    this.state = {
      hasError: false,
      errorId: '',
      retryCount: 0,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    // Generate unique error ID for tracking
    const errorId = `wizard_error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    return {
      hasError: true,
      error,
      errorId,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({
      error,
      errorInfo,
    });

    // Log error for debugging
    this.logError(error, errorInfo);
  }

  componentWillUnmount() {
    // Clear any pending retry timeouts
    this.retryTimeouts.forEach(timeout => clearTimeout(timeout));
  }

  private logError = (error: Error, errorInfo: ErrorInfo) => {
    const errorDetails: ErrorDetails = {
      message: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      timestamp: Date.now(),
      userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : 'unknown',
      url: typeof window !== 'undefined' ? window.location.href : 'unknown',
    };

    // Log to console in development
    if (__DEV__) {
      console.group('🚨 Wizard Error Boundary Caught Error');
      console.error('Error:', error);
      console.error('Error Info:', errorInfo);
      console.error('Error Details:', errorDetails);
      console.groupEnd();
    }

    // In production, you might want to send this to an error reporting service
    // Example: Sentry, Bugsnag, or custom logging endpoint
    try {
      if (!__DEV__) {
        // Send error to logging service
        // this.sendErrorToService(errorDetails);
      }
    } catch (loggingError) {
      console.error('Failed to log error:', loggingError);
    }
  };

  private handleRetry = () => {
    const { maxRetries = 3 } = this.props;
    const { retryCount } = this.state;

    if (retryCount >= maxRetries) {
      console.warn(`Maximum retry attempts (${maxRetries}) exceeded for wizard error boundary`);
      return;
    }

    // Implement exponential backoff for retries
    const delay = Math.min(1000 * Math.pow(2, retryCount), 5000);
    
    const timeout = setTimeout(() => {
      this.setState({
        hasError: false,
        error: undefined,
        errorInfo: undefined,
        retryCount: retryCount + 1,
      });
    }, delay);

    this.retryTimeouts.push(timeout);
  };

  private handleReset = () => {
    this.setState({
      hasError: false,
      error: undefined,
      errorInfo: undefined,
      errorId: '',
      retryCount: 0,
    });

    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  private handleSaveAndExit = async () => {
    if (this.props.onSaveAndExit) {
      try {
        await this.props.onSaveAndExit();
      } catch (error) {
        console.error('Failed to save data before exit:', error);
        // Still allow exit even if save fails
      }
    }
  };

  private handleGoToDashboard = () => {
    if (this.props.onGoToDashboard) {
      this.props.onGoToDashboard();
    }
  };

  private getErrorSeverity = (error: Error): 'critical' | 'moderate' | 'minor' => {
    const message = error.message.toLowerCase();
    
    // Critical errors that make the wizard unusable
    if (message.includes('network') || message.includes('api') || message.includes('server')) {
      return 'critical';
    }
    
    // UI rendering errors
    if (message.includes('render') || message.includes('component') || message.includes('hook')) {
      return 'moderate';
    }
    
    // Other errors
    return 'minor';
  };

  private getErrorMessage = (error: Error): { title: string; description: string; suggestions: string[] } => {
    const severity = this.getErrorSeverity(error);
    const message = error.message.toLowerCase();

    if (message.includes('network') || message.includes('fetch') || message.includes('api')) {
      return {
        title: 'Connection Problem',
        description: 'We\'re having trouble connecting to our servers. Your progress may not be saved.',
        suggestions: [
          'Check your internet connection',
          'Try again in a few moments',
          'Save your work and return later'
        ]
      };
    }

    if (message.includes('validation') || message.includes('invalid')) {
      return {
        title: 'Form Validation Error',
        description: 'There was an issue validating your form data.',
        suggestions: [
          'Review your entered information',
          'Try simplifying complex entries',
          'Save your progress and continue'
        ]
      };
    }

    if (severity === 'critical') {
      return {
        title: 'Critical Error',
        description: 'A serious error occurred that prevents the wizard from continuing.',
        suggestions: [
          'Save your progress immediately',
          'Contact support if the problem persists',
          'Try accessing from a different device or browser'
        ]
      };
    }

    return {
      title: 'Unexpected Error',
      description: 'Something went wrong while setting up your profile.',
      suggestions: [
        'Try the action again',
        'Save your current progress',
        'Refresh the page if the problem continues'
      ]
    };
  };

  render() {
    const { children, fallback, maxRetries = 3 } = this.props;
    const { hasError, error, retryCount } = this.state;

    if (hasError && error) {
      // Use custom fallback if provided
      if (fallback) {
        return fallback;
      }

      const { title, description, suggestions } = this.getErrorMessage(error);
      const canRetry = retryCount < maxRetries;

      return (
        <Box className="flex-1 items-center justify-center p-6 bg-gray-50">
          <Card className="max-w-md w-full p-6">
            <VStack space="lg" className="items-center">
              {/* Error Icon */}
              <Box className="w-16 h-16 bg-red-100 rounded-full items-center justify-center">
                <Icon as={AlertTriangle} size="xl" className="text-red-600" />
              </Box>

              {/* Error Content */}
              <VStack space="md" className="items-center">
                <Heading size="lg" className="text-gray-900 text-center">
                  {title}
                </Heading>
                
                <Text className="text-gray-600 text-center">
                  {description}
                </Text>

                {/* Error Suggestions */}
                <VStack space="xs" className="w-full">
                  <Text className="text-sm font-medium text-gray-900">
                    What you can try:
                  </Text>
                  {suggestions.map((suggestion, index) => (
                    <Text key={index} className="text-sm text-gray-600">
                      • {suggestion}
                    </Text>
                  ))}
                </VStack>

                {/* Development Info */}
                {__DEV__ && (
                  <Box className="w-full p-3 bg-gray-100 rounded-lg">
                    <Text className="text-xs font-mono text-gray-800">
                      {error.message}
                    </Text>
                    {retryCount > 0 && (
                      <Text className="text-xs text-gray-600 mt-1">
                        Retry attempts: {retryCount}/{maxRetries}
                      </Text>
                    )}
                  </Box>
                )}
              </VStack>

              {/* Action Buttons */}
              <VStack space="sm" className="w-full">
                {canRetry && (
                  <Button
                    onPress={this.handleRetry}
                    className="w-full bg-blue-600 hover:bg-blue-700"
                  >
                    <ButtonIcon as={RefreshCw} className="text-white mr-2" />
                    <ButtonText className="text-white">
                      Try Again {retryCount > 0 ? `(${maxRetries - retryCount} left)` : ''}
                    </ButtonText>
                  </Button>
                )}

                <HStack space="sm" className="w-full">
                  <Button
                    variant="outline"
                    onPress={this.handleSaveAndExit}
                    className="flex-1"
                  >
                    <ButtonIcon as={Save} className="text-gray-600 mr-1" />
                    <ButtonText className="text-gray-600">Save & Exit</ButtonText>
                  </Button>

                  <Button
                    variant="outline"
                    onPress={this.handleGoToDashboard}
                    className="flex-1"
                  >
                    <ButtonIcon as={Home} className="text-gray-600 mr-1" />
                    <ButtonText className="text-gray-600">Dashboard</ButtonText>
                  </Button>
                </HStack>

                <Button
                  variant="outline"
                  onPress={this.handleReset}
                  className="w-full"
                >
                  <ButtonText className="text-gray-500">Reset Wizard</ButtonText>
                </Button>
              </VStack>
            </VStack>
          </Card>
        </Box>
      );
    }

    return children;
  }
}

export default WizardErrorBoundary;