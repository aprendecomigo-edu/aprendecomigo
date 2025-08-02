/**
 * Quick Actions Modal Component
 * 
 * Main modal that orchestrates renewal and top-up flows,
 * integrating all the quick action components together.
 */

import React, { useState, useEffect } from 'react';
import { X, RotateCcw, Zap, AlertCircle } from 'lucide-react-native';

import { 
  Modal, 
  ModalBackdrop, 
  ModalContent, 
  ModalHeader, 
  ModalCloseButton, 
  ModalBody 
} from '@/components/ui/modal';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { Alert, AlertIcon, AlertText } from '@/components/ui/alert';

import { OneClickRenewalButton } from './OneClickRenewalButton';
import { QuickTopUpPanel } from './QuickTopUpPanel';
import { RenewalConfirmationModal } from './RenewalConfirmationModal';
import { SavedPaymentSelector } from './SavedPaymentSelector';
import { PaymentSuccessHandler } from './PaymentSuccessHandler';

import { PurchaseApiClient } from '@/api/purchaseApi';
import { useStudentBalance } from '@/hooks/useStudentBalance';
import { usePaymentMethods } from '@/hooks/usePaymentMethods';
import type { 
  QuickActionState,
  PaymentMethod,
  TopUpPackage,
  PackageInfo,
  RenewalRequest,
  QuickTopUpRequest,
  RenewalResponse,
  QuickTopUpResponse
} from '@/types/purchase';

interface QuickActionsModalProps {
  /** Whether modal is open */
  isOpen: boolean;
  /** Close modal callback */
  onClose: () => void;
  /** Initial action type to show */
  initialAction?: 'renewal' | 'topup';
  /** Optional email for admin access */
  email?: string;
  /** Callback when successful transaction completes */
  onTransactionSuccess?: (type: 'renewal' | 'topup', response: RenewalResponse | QuickTopUpResponse) => void;
}

/**
 * Quick Actions Modal Component
 * 
 * Main modal that handles both renewal and top-up flows with state management.
 */
export function QuickActionsModal({
  isOpen,
  onClose,
  initialAction,
  email,
  onTransactionSuccess,
}: QuickActionsModalProps) {
  const { balance, refetch: refetchBalance } = useStudentBalance(email);
  const { paymentMethods } = usePaymentMethods(email);

  const [actionState, setActionState] = useState<QuickActionState>({
    isVisible: false,
    actionType: initialAction || null,
    isProcessing: false,
    error: null,
    selectedPackage: undefined,
    selectedPaymentMethod: undefined,
    confirmationStep: 'select',
  });

  const [showConfirmationModal, setShowConfirmationModal] = useState(false);
  const [successResponse, setSuccessResponse] = useState<RenewalResponse | QuickTopUpResponse | null>(null);
  const [expiredPackage, setExpiredPackage] = useState<PackageInfo | null>(null);

  // Reset state when modal opens/closes
  useEffect(() => {
    if (isOpen) {
      setActionState(prev => ({
        ...prev,
        actionType: initialAction || null,
        confirmationStep: 'select',
        error: null,
      }));
      setSuccessResponse(null);
      setShowConfirmationModal(false);
    } else {
      // Reset all state when closing
      setActionState({
        isVisible: false,
        actionType: null,
        isProcessing: false,
        error: null,
        selectedPackage: undefined,
        selectedPaymentMethod: undefined,
        confirmationStep: 'select',
      });
      setSuccessResponse(null);
      setShowConfirmationModal(false);
    }
  }, [isOpen, initialAction]);

  // Detect expired packages
  useEffect(() => {
    if (balance?.package_status.expired_packages.length) {
      const mostRecent = balance.package_status.expired_packages
        .sort((a, b) => new Date(b.expires_at || '').getTime() - new Date(a.expires_at || '').getTime())[0];
      setExpiredPackage(mostRecent);
    }
  }, [balance]);

  // Handle action type selection
  const handleActionSelect = (actionType: 'renewal' | 'topup') => {
    setActionState(prev => ({
      ...prev,
      actionType,
      confirmationStep: 'select',
      error: null,
    }));
  };

  // Handle package selection for top-up
  const handlePackageSelect = (pkg: TopUpPackage) => {
    setActionState(prev => ({
      ...prev,
      selectedPackage: pkg,
    }));
  };

  // Handle payment method selection
  const handlePaymentMethodSelect = (paymentMethod: PaymentMethod) => {
    setActionState(prev => ({
      ...prev,
      selectedPaymentMethod: paymentMethod,
    }));
    setShowConfirmationModal(true);
  };

  // Handle renewal confirmation
  const handleRenewalConfirm = async (request: RenewalRequest) => {
    setActionState(prev => ({ ...prev, isProcessing: true, error: null }));
    
    try {
      const response = await PurchaseApiClient.renewSubscription(request, email);
      
      if (response.success) {
        setSuccessResponse(response);
        setActionState(prev => ({ ...prev, confirmationStep: 'success' }));
        setShowConfirmationModal(false);
        onTransactionSuccess?.('renewal', response);
      } else {
        throw new Error(response.message || 'Renewal failed');
      }
    } catch (error: any) {
      setActionState(prev => ({ 
        ...prev, 
        error: error.message || 'Failed to process renewal',
        confirmationStep: 'error' 
      }));
    } finally {
      setActionState(prev => ({ ...prev, isProcessing: false }));
    }
  };

  // Handle top-up confirmation
  const handleTopUpConfirm = async (request: QuickTopUpRequest) => {
    setActionState(prev => ({ ...prev, isProcessing: true, error: null }));
    
    try {
      const response = await PurchaseApiClient.quickTopUp(request, email);
      
      if (response.success) {
        setSuccessResponse(response);
        setActionState(prev => ({ ...prev, confirmationStep: 'success' }));
        setShowConfirmationModal(false);
        onTransactionSuccess?.('topup', response);
      } else {
        throw new Error(response.message || 'Top-up failed');
      }
    } catch (error: any) {
      setActionState(prev => ({ 
        ...prev, 
        error: error.message || 'Failed to process top-up',
        confirmationStep: 'error' 
      }));
    } finally {
      setActionState(prev => ({ ...prev, isProcessing: false }));
    }
  };

  // Handle confirmation
  const handleConfirmation = async (request: RenewalRequest | QuickTopUpRequest) => {
    if (actionState.actionType === 'renewal') {
      await handleRenewalConfirm(request as RenewalRequest);
    } else {
      await handleTopUpConfirm(request as QuickTopUpRequest);
    }
  };

  // Handle success completion
  const handleSuccessDone = () => {
    onClose();
  };

  // Get modal title
  const getModalTitle = () => {
    if (actionState.confirmationStep === 'success') {
      return actionState.actionType === 'renewal' ? 'Renewal Successful' : 'Purchase Successful';
    }
    
    if (!actionState.actionType) {
      return 'Quick Actions';
    }
    
    return actionState.actionType === 'renewal' ? 'Renew Subscription' : 'Purchase Hours';
  };

  // Get modal icon
  const getModalIcon = () => {
    if (actionState.actionType === 'renewal') return RotateCcw;
    if (actionState.actionType === 'topup') return Zap;
    return null;
  };

  const ModalIcon = getModalIcon();

  return (
    <>
      <Modal isOpen={isOpen} onClose={onClose} size="lg">
        <ModalBackdrop />
        <ModalContent>
          <ModalHeader>
            <HStack className="items-center justify-between">
              <HStack space="sm" className="items-center">
                {ModalIcon && (
                  <Icon 
                    as={ModalIcon} 
                    size="sm" 
                    className={actionState.actionType === 'renewal' ? 'text-primary-600' : 'text-warning-600'} 
                  />
                )}
                <Heading size="lg">{getModalTitle()}</Heading>
              </HStack>
              <ModalCloseButton>
                <Icon as={X} />
              </ModalCloseButton>
            </HStack>
          </ModalHeader>

          <ModalBody>
            <VStack space="lg">
              {/* Error Display */}
              {actionState.error && (
                <Alert action="error" variant="outline">
                  <AlertIcon as={AlertCircle} />
                  <AlertText>{actionState.error}</AlertText>
                </Alert>
              )}

              {/* Success State */}
              {actionState.confirmationStep === 'success' && successResponse && (
                <PaymentSuccessHandler
                  transactionType={actionState.actionType!}
                  renewalResponse={actionState.actionType === 'renewal' ? successResponse as RenewalResponse : undefined}
                  topUpResponse={actionState.actionType === 'topup' ? successResponse as QuickTopUpResponse : undefined}
                  email={email}
                  onDone={handleSuccessDone}
                  autoRefreshBalance={true}
                />
              )}

              {/* Action Selection */}
              {actionState.confirmationStep === 'select' && !actionState.actionType && (
                <VStack space="md">
                  <Text className="text-typography-600 text-center">
                    Choose what you'd like to do:
                  </Text>
                  
                  <VStack space="sm">
                    {/* Show renewal if there's an expired package */}
                    {expiredPackage && (
                      <OneClickRenewalButton
                        email={email}
                        size="lg"
                        showPlanDetails={true}
                        onRenewalSuccess={(response) => {
                          setSuccessResponse(response);
                          setActionState(prev => ({ 
                            ...prev, 
                            actionType: 'renewal',
                            confirmationStep: 'success' 
                          }));
                        }}
                        onRenewalError={(error) => {
                          setActionState(prev => ({ ...prev, error }));
                        }}
                      />
                    )}
                    
                    {/* Quick Top-Up Panel */}
                    <QuickTopUpPanel
                      email={email}
                      onTopUpSuccess={(response) => {
                        setSuccessResponse(response);
                        setActionState(prev => ({ 
                          ...prev, 
                          actionType: 'topup',
                          confirmationStep: 'success' 
                        }));
                      }}
                      onTopUpError={(error) => {
                        setActionState(prev => ({ ...prev, error }));
                      }}
                    />
                  </VStack>
                </VStack>
              )}

              {/* Renewal Flow */}
              {actionState.confirmationStep === 'select' && actionState.actionType === 'renewal' && (
                <VStack space="lg">
                  <Text className="text-typography-600">
                    Select a payment method to renew your subscription:
                  </Text>
                  
                  <SavedPaymentSelector
                    email={email}
                    selectedPaymentMethodId={actionState.selectedPaymentMethod?.id}
                    onPaymentMethodSelect={handlePaymentMethodSelect}
                    size="md"
                    showCardDetails={true}
                  />
                </VStack>
              )}

              {/* Top-up Flow */}
              {actionState.confirmationStep === 'select' && actionState.actionType === 'topup' && (
                <QuickTopUpPanel
                  email={email}
                  onTopUpSuccess={(response) => {
                    setSuccessResponse(response);
                    setActionState(prev => ({ ...prev, confirmationStep: 'success' }));
                  }}
                  onTopUpError={(error) => {
                    setActionState(prev => ({ ...prev, error }));
                  }}
                />
              )}
            </VStack>
          </ModalBody>
        </ModalContent>
      </Modal>

      {/* Confirmation Modal */}
      {showConfirmationModal && actionState.selectedPaymentMethod && (
        <RenewalConfirmationModal
          isOpen={showConfirmationModal}
          onClose={() => setShowConfirmationModal(false)}
          transactionType={actionState.actionType!}
          expiredPackage={actionState.actionType === 'renewal' ? expiredPackage : undefined}
          topUpPackage={actionState.actionType === 'topup' ? actionState.selectedPackage : undefined}
          paymentMethod={actionState.selectedPaymentMethod}
          onConfirm={handleConfirmation}
          isProcessing={actionState.isProcessing}
          error={actionState.error}
          enableBiometricAuth={false} // Can be enabled based on user preferences
        />
      )}
    </>
  );
}