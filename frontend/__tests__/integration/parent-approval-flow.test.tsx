/**
 * Parent Approval Integration Flow Tests
 *
 * Tests the complete parent approval flow for student purchases,
 * including request submission, notification handling, approval/rejection,
 * and completion workflows.
 */

import React from 'react';

import {
  createMockPricingPlans,
  createMockStripeConfig,
  createMockPurchaseInitiationResponse,
  createMockStripe,
  createMockElements,
  createMockStripeSuccess,
  createMockPaymentMethods,
  createMockWebSocket,
  VALID_TEST_DATA,
  cleanupMocks,
} from '@/__tests__/utils/payment-test-utils';
import { render, fireEvent, waitFor, act } from '@/__tests__/utils/test-utils';
import { NotificationApiClient } from '@/api/notificationApi';
import { PaymentMethodApiClient } from '@/api/paymentMethodApi';
import { PurchaseApiClient } from '@/api/purchaseApi';
import { PurchaseFlow } from '@/components/purchase/PurchaseFlow';

// Mock APIs
jest.mock('@/api/purchaseApi');
jest.mock('@/api/paymentMethodApi');
jest.mock('@/api/notificationApi');
const mockPurchaseApiClient = PurchaseApiClient as jest.Mocked<typeof PurchaseApiClient>;
const mockPaymentMethodApiClient = PaymentMethodApiClient as jest.Mocked<
  typeof PaymentMethodApiClient
>;
const mockNotificationApiClient = NotificationApiClient as jest.Mocked<
  typeof NotificationApiClient
>;

// Mock Stripe
jest.mock('@stripe/react-stripe-js', () => ({
  Elements: ({ children }: any) => children,
  PaymentElement: () => <div testID="stripe-payment-element">Payment Element</div>,
  useStripe: () => mockStripe,
  useElements: () => mockElements,
}));

// Mock router
const mockPush = jest.fn();
const mockReplace = jest.fn();
jest.mock('@unitools/router', () => ({
  __esModule: true,
  default: () => ({ push: mockPush, replace: mockReplace }),
}));

// Mock push notifications
const mockPushNotifications = {
  scheduleNotificationAsync: jest.fn(),
  cancelNotificationAsync: jest.fn(),
  getAllScheduledNotificationsAsync: jest.fn(),
};
jest.mock('expo-notifications', () => mockPushNotifications);

// Mock email service
const mockEmailService = {
  sendParentApprovalRequest: jest.fn(),
  sendApprovalReminder: jest.fn(),
  sendApprovalConfirmation: jest.fn(),
};
jest.mock('@/services/emailService', () => mockEmailService);

// Global test data
const mockPlans = createMockPricingPlans();
const mockStripe = createMockStripe();
const mockElements = createMockElements();

// Parent approval test data
const createMockStudentUser = () => ({
  id: 1,
  email: 'student@example.com',
  name: 'Student User',
  role: 'student',
  age: 16,
  parent_email: 'parent@example.com',
  requires_parent_approval: true,
});

const createMockParentUser = () => ({
  id: 2,
  email: 'parent@example.com',
  name: 'Parent User',
  role: 'parent',
  children: [1],
});

const createMockApprovalRequest = (overrides = {}) => ({
  id: 1,
  student_id: 1,
  parent_email: 'parent@example.com',
  plan_id: 2,
  amount: '100.00',
  currency: 'EUR',
  status: 'pending',
  requested_at: '2024-01-15T10:00:00Z',
  expires_at: '2024-01-22T10:00:00Z',
  approval_token: 'approval_token_123',
  ...overrides,
});

const createMockApprovalResponse = (approved: boolean) => ({
  success: true,
  approved,
  approval_id: 1,
  message: approved ? 'Purchase approved successfully' : 'Purchase request has been declined',
  transaction_id: approved ? 123 : null,
});

describe('Parent Approval Integration Flow Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    cleanupMocks();

    // Setup successful API responses
    mockPurchaseApiClient.getStripeConfig.mockResolvedValue(createMockStripeConfig());
    mockPurchaseApiClient.getPricingPlans.mockResolvedValue(mockPlans);
    mockPaymentMethodApiClient.getPaymentMethods.mockResolvedValue(createMockPaymentMethods());

    // Reset notification mocks
    mockPushNotifications.scheduleNotificationAsync.mockReset();
    mockEmailService.sendParentApprovalRequest.mockReset();
  });

  describe('Student Purchase Request Flow', () => {
    it('creates parent approval request for minor student', async () => {
      const mockStudent = createMockStudentUser();

      // Mock student authentication
      const mockAuth = {
        user: mockStudent,
        isAuthenticated: true,
        requiresParentApproval: true,
      };

      const onPurchaseComplete = jest.fn();
      const { getByText, getByPlaceholderText, queryByText } = render(<PurchaseFlow />);

      // Complete purchase flow
      await waitFor(() => getByText('Select Plan'));
      fireEvent.press(getByText('Standard Package'));

      await waitFor(() => getByText('Student Information'));
      fireEvent.changeText(getByPlaceholderText('Student name'), mockStudent.name);
      fireEvent.changeText(getByPlaceholderText('Student email'), mockStudent.email);

      // Mock approval request creation instead of direct purchase
      const approvalRequest = createMockApprovalRequest();
      mockPurchaseApiClient.createApprovalRequest = jest.fn().mockResolvedValue(approvalRequest);

      fireEvent.press(getByText('Request Parent Approval'));

      await waitFor(() => {
        expect(getByText('Approval Request Sent')).toBeTruthy();
        expect(getByText('Waiting for parent approval')).toBeTruthy();
        expect(queryByText('Payment')).toBeNull(); // Should not proceed to payment
      });

      // Verify approval request was created
      expect(mockPurchaseApiClient.createApprovalRequest).toHaveBeenCalledWith({
        plan_id: expect.any(Number),
        student_info: {
          name: mockStudent.name,
          email: mockStudent.email,
        },
        parent_email: mockStudent.parent_email,
      });

      // Verify parent notification was sent
      expect(mockEmailService.sendParentApprovalRequest).toHaveBeenCalledWith({
        parent_email: mockStudent.parent_email,
        student_name: mockStudent.name,
        plan_name: 'Standard Package',
        amount: '100.00',
        approval_url: expect.stringContaining('approval_token_123'),
      });
    });

    it('shows approval request status and allows cancellation', async () => {
      const mockStudent = createMockStudentUser();
      const approvalRequest = createMockApprovalRequest();

      // Mock existing approval request
      mockPurchaseApiClient.getApprovalRequest = jest.fn().mockResolvedValue(approvalRequest);
      mockPurchaseApiClient.cancelApprovalRequest = jest.fn().mockResolvedValue({ success: true });

      const { getByText, queryByText } = render(<PurchaseFlow />);

      await waitFor(() => {
        expect(getByText('Approval Request Pending')).toBeTruthy();
        expect(getByText('Request sent to parent@example.com')).toBeTruthy();
        expect(getByText('Expires in 7 days')).toBeTruthy();
      });

      // Test cancellation
      fireEvent.press(getByText('Cancel Request'));

      await waitFor(() => {
        expect(getByText('Are you sure you want to cancel this request?')).toBeTruthy();
      });

      fireEvent.press(getByText('Yes, Cancel'));

      await waitFor(() => {
        expect(mockPurchaseApiClient.cancelApprovalRequest).toHaveBeenCalledWith(
          approvalRequest.id
        );
        expect(queryByText('Approval Request Pending')).toBeNull();
        expect(getByText('Select Plan')).toBeTruthy(); // Back to plan selection
      });
    });

    it('handles approval request expiration', async () => {
      const mockStudent = createMockStudentUser();
      const expiredRequest = createMockApprovalRequest({
        status: 'expired',
        expires_at: '2024-01-01T10:00:00Z', // Past date
      });

      mockPurchaseApiClient.getApprovalRequest = jest.fn().mockResolvedValue(expiredRequest);

      const { getByText, queryByText } = render(<PurchaseFlow />);

      await waitFor(() => {
        expect(getByText('Approval Request Expired')).toBeTruthy();
        expect(getByText('The approval request has expired')).toBeTruthy();
        expect(queryByText('Waiting for parent approval')).toBeNull();
      });

      // Should allow creating new request
      fireEvent.press(getByText('Request New Approval'));

      await waitFor(() => {
        expect(getByText('Select Plan')).toBeTruthy();
      });
    });
  });

  describe('Parent Approval Response Flow', () => {
    it('handles parent approval and completes purchase', async () => {
      const mockWs = createMockWebSocket();
      const approvalRequest = createMockApprovalRequest();
      const mockStudent = createMockStudentUser();

      // Mock WebSocket for real-time updates
      mockPurchaseApiClient.getApprovalRequest = jest.fn().mockResolvedValue(approvalRequest);

      const onPurchaseComplete = jest.fn();
      const { getByText, queryByText } = render(
        <PurchaseFlow onPurchaseComplete={onPurchaseComplete} />
      );

      // Show waiting state
      await waitFor(() => {
        expect(getByText('Approval Request Pending')).toBeTruthy();
      });

      // Simulate parent approval via WebSocket
      const approvalResponse = createMockApprovalResponse(true);
      act(() => {
        mockWs.onmessage?.({
          data: JSON.stringify({
            type: 'approval_response',
            data: approvalResponse,
          }),
        } as any);
      });

      // Should automatically proceed to payment completion
      await waitFor(() => {
        expect(getByText('Purchase Approved!')).toBeTruthy();
        expect(getByText('Your parent has approved the purchase')).toBeTruthy();
      });

      // Should complete purchase automatically
      mockStripe.confirmPayment.mockResolvedValue(createMockStripeSuccess());

      await waitFor(() => {
        expect(getByText('Purchase Successful!')).toBeTruthy();
        expect(onPurchaseComplete).toHaveBeenCalledWith(approvalResponse.transaction_id);
      });

      // Verify completion notification sent
      expect(mockEmailService.sendApprovalConfirmation).toHaveBeenCalledWith({
        student_email: mockStudent.email,
        parent_email: mockStudent.parent_email,
        transaction_id: approvalResponse.transaction_id,
        plan_name: 'Standard Package',
      });
    });

    it('handles parent rejection and notifies student', async () => {
      const mockWs = createMockWebSocket();
      const approvalRequest = createMockApprovalRequest();

      mockPurchaseApiClient.getApprovalRequest = jest.fn().mockResolvedValue(approvalRequest);

      const { getByText, queryByText } = render(<PurchaseFlow />);

      // Show waiting state
      await waitFor(() => {
        expect(getByText('Approval Request Pending')).toBeTruthy();
      });

      // Simulate parent rejection via WebSocket
      const rejectionResponse = createMockApprovalResponse(false);
      act(() => {
        mockWs.onmessage?.({
          data: JSON.stringify({
            type: 'approval_response',
            data: {
              ...rejectionResponse,
              rejection_reason: 'Not needed at this time',
            },
          }),
        } as any);
      });

      // Should show rejection message
      await waitFor(() => {
        expect(getByText('Purchase Request Declined')).toBeTruthy();
        expect(getByText('Your parent has declined the purchase request')).toBeTruthy();
        expect(getByText('Reason: Not needed at this time')).toBeTruthy();
      });

      // Should not proceed to payment
      expect(queryByText('Payment')).toBeNull();
      expect(queryByText('Purchase Successful!')).toBeNull();

      // Should allow creating new request
      fireEvent.press(getByText('Make New Request'));

      await waitFor(() => {
        expect(getByText('Select Plan')).toBeTruthy();
      });
    });

    it('handles approval with parent payment method', async () => {
      const approvalRequest = createMockApprovalRequest();
      const mockParent = createMockParentUser();

      // Mock parent payment methods
      const parentPaymentMethods = createMockPaymentMethods();
      mockPaymentMethodApiClient.getParentPaymentMethods = jest
        .fn()
        .mockResolvedValue(parentPaymentMethods);

      mockPurchaseApiClient.getApprovalRequest = jest.fn().mockResolvedValue(approvalRequest);

      const { getByText, queryByText } = render(<PurchaseFlow />);

      // Simulate approval with parent's payment method
      const mockWs = createMockWebSocket();
      act(() => {
        mockWs.onmessage?.({
          data: JSON.stringify({
            type: 'approval_response',
            data: {
              ...createMockApprovalResponse(true),
              payment_method: 'parent_card_ending_4242',
              use_parent_payment: true,
            },
          }),
        } as any);
      });

      await waitFor(() => {
        expect(getByText('Purchase Approved!')).toBeTruthy();
        expect(getByText("Payment will be charged to parent's card •••• 4242")).toBeTruthy();
      });

      // Should complete purchase with parent's payment method
      await waitFor(() => {
        expect(getByText('Purchase Successful!')).toBeTruthy();
      });

      // Verify parent was charged
      expect(mockPaymentMethodApiClient.getParentPaymentMethods).toHaveBeenCalled();
    });
  });

  describe('Parent Dashboard Integration', () => {
    it('shows pending approval requests in parent dashboard', async () => {
      const mockParent = createMockParentUser();
      const pendingRequests = [
        createMockApprovalRequest({
          id: 1,
          student_id: 1,
          plan_name: 'Standard Package',
          status: 'pending',
        }),
        createMockApprovalRequest({
          id: 2,
          student_id: 1,
          plan_name: 'Premium Package',
          status: 'pending',
        }),
      ];

      mockPurchaseApiClient.getParentApprovalRequests = jest
        .fn()
        .mockResolvedValue(pendingRequests);

      // Mock parent dashboard component
      const ParentDashboard = () => {
        const [requests, setRequests] = React.useState(pendingRequests);

        return (
          <div>
            <h2>Pending Approvals</h2>
            {requests.map(request => (
              <div key={request.id} testID={`approval-request-${request.id}`}>
                <span>
                  {request.plan_name} - €{request.amount}
                </span>
                <button onClick={() => handleApproval(request.id, true)}>Approve</button>
                <button onClick={() => handleApproval(request.id, false)}>Decline</button>
              </div>
            ))}
          </div>
        );
      };

      const handleApproval = jest.fn();
      const { getByText, getByTestId } = render(<ParentDashboard />);

      await waitFor(() => {
        expect(getByText('Pending Approvals')).toBeTruthy();
        expect(getByTestId('approval-request-1')).toBeTruthy();
        expect(getByTestId('approval-request-2')).toBeTruthy();
        expect(getByText('Standard Package - €100.00')).toBeTruthy();
        expect(getByText('Premium Package - €180.00')).toBeTruthy();
      });
    });

    it('handles batch approval actions', async () => {
      const mockParent = createMockParentUser();
      const multipleRequests = [
        createMockApprovalRequest({ id: 1, plan_name: 'Plan A' }),
        createMockApprovalRequest({ id: 2, plan_name: 'Plan B' }),
        createMockApprovalRequest({ id: 3, plan_name: 'Plan C' }),
      ];

      mockPurchaseApiClient.batchApprovalAction = jest.fn().mockResolvedValue({
        success: true,
        approved_count: 2,
        declined_count: 1,
      });

      // Mock batch approval UI
      const BatchApprovalUI = () => (
        <div>
          <button onClick={() => mockPurchaseApiClient.batchApprovalAction([1, 2], 'approve')}>
            Approve Selected
          </button>
          <button onClick={() => mockPurchaseApiClient.batchApprovalAction([3], 'decline')}>
            Decline Selected
          </button>
        </div>
      );

      const { getByText } = render(<BatchApprovalUI />);

      fireEvent.press(getByText('Approve Selected'));
      fireEvent.press(getByText('Decline Selected'));

      await waitFor(() => {
        expect(mockPurchaseApiClient.batchApprovalAction).toHaveBeenCalledTimes(2);
        expect(mockPurchaseApiClient.batchApprovalAction).toHaveBeenCalledWith([1, 2], 'approve');
        expect(mockPurchaseApiClient.batchApprovalAction).toHaveBeenCalledWith([3], 'decline');
      });
    });
  });

  describe('Notification and Communication Flow', () => {
    it('sends reminder notifications for pending approvals', async () => {
      const approvalRequest = createMockApprovalRequest({
        requested_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(), // 1 day ago
      });

      // Mock reminder service
      mockEmailService.sendApprovalReminder = jest.fn().mockResolvedValue({ success: true });
      mockPushNotifications.scheduleNotificationAsync.mockResolvedValue('notification-id');

      // Simulate reminder trigger (would be a background job)
      await waitFor(() => {
        expect(mockEmailService.sendApprovalReminder).toHaveBeenCalledWith({
          parent_email: approvalRequest.parent_email,
          student_name: expect.any(String),
          plan_name: expect.any(String),
          days_pending: 1,
          approval_url: expect.stringContaining('approval_token_123'),
        });
      });
    });

    it('handles parent offline/unreachable scenarios', async () => {
      const approvalRequest = createMockApprovalRequest();

      // Mock email delivery failure
      mockEmailService.sendParentApprovalRequest.mockRejectedValue(
        new Error('Email delivery failed')
      );

      const { getByText, queryByText } = render(<PurchaseFlow />);

      // Try to create approval request
      await waitFor(() => getByText('Select Plan'));
      fireEvent.press(getByText('Standard Package'));

      // Should show email delivery error
      await waitFor(() => {
        expect(getByText('Unable to send approval request')).toBeTruthy();
        expect(getByText('Please verify parent email address')).toBeTruthy();
      });

      // Should offer alternative contact methods
      expect(getByText('Try SMS instead')).toBeTruthy();
      expect(getByText('Update parent email')).toBeTruthy();
    });

    it('tracks approval request analytics', async () => {
      const mockAnalytics = {
        track: jest.fn(),
        identify: jest.fn(),
      };
      jest.doMock('@/services/analytics', () => mockAnalytics);

      const approvalRequest = createMockApprovalRequest();
      mockPurchaseApiClient.createApprovalRequest = jest.fn().mockResolvedValue(approvalRequest);

      const { getByText } = render(<PurchaseFlow />);

      // Create approval request
      await waitFor(() => getByText('Select Plan'));
      fireEvent.press(getByText('Standard Package'));
      fireEvent.press(getByText('Request Parent Approval'));

      await waitFor(() => {
        expect(mockAnalytics.track).toHaveBeenCalledWith('approval_request_created', {
          plan_id: expect.any(Number),
          student_id: expect.any(Number),
          amount: expect.any(String),
        });
      });

      // Simulate approval
      const mockWs = createMockWebSocket();
      act(() => {
        mockWs.onmessage?.({
          data: JSON.stringify({
            type: 'approval_response',
            data: createMockApprovalResponse(true),
          }),
        } as any);
      });

      await waitFor(() => {
        expect(mockAnalytics.track).toHaveBeenCalledWith('approval_request_approved', {
          approval_id: expect.any(Number),
          response_time_hours: expect.any(Number),
        });
      });
    });
  });

  describe('Edge Cases and Error Handling', () => {
    it('handles multiple pending requests from same student', async () => {
      const multipleRequests = [
        createMockApprovalRequest({ id: 1, plan_name: 'Plan A' }),
        createMockApprovalRequest({ id: 2, plan_name: 'Plan B' }),
      ];

      mockPurchaseApiClient.getApprovalRequests = jest.fn().mockResolvedValue(multipleRequests);

      const { getByText, queryByText } = render(<PurchaseFlow />);

      await waitFor(() => {
        expect(getByText('Multiple Pending Requests')).toBeTruthy();
        expect(getByText('You have 2 pending approval requests')).toBeTruthy();
        expect(queryByText('Request Parent Approval')).toBeNull(); // Should not allow new requests
      });

      // Should show list of pending requests
      expect(getByText('Plan A - €100.00')).toBeTruthy();
      expect(getByText('Plan B - €100.00')).toBeTruthy();
    });

    it('handles approval token security validation', async () => {
      const invalidTokenResponse = {
        success: false,
        error: 'Invalid or expired approval token',
      };

      mockPurchaseApiClient.validateApprovalToken = jest
        .fn()
        .mockResolvedValue(invalidTokenResponse);

      // Mock parent clicking approval link with invalid token
      const mockApprovalLink = () => {
        return (
          <div>
            <button onClick={() => handleApprovalClick('invalid_token')}>Approve Purchase</button>
          </div>
        );
      };

      const handleApprovalClick = async (token: string) => {
        const result = await mockPurchaseApiClient.validateApprovalToken(token);
        if (!result.success) {
          throw new Error(result.error);
        }
      };

      const { getByText } = render(mockApprovalLink());

      // Should reject invalid token
      await expect(handleApprovalClick('invalid_token')).rejects.toThrow(
        'Invalid or expired approval token'
      );
    });

    it('handles network failures during approval flow', async () => {
      const approvalRequest = createMockApprovalRequest();

      // Mock network failure
      mockPurchaseApiClient.createApprovalRequest.mockRejectedValue(
        new Error('Network request failed')
      );

      const { getByText } = render(<PurchaseFlow />);

      await waitFor(() => getByText('Select Plan'));
      fireEvent.press(getByText('Standard Package'));
      fireEvent.press(getByText('Request Parent Approval'));

      await waitFor(() => {
        expect(getByText('Network Error')).toBeTruthy();
        expect(getByText('Failed to send approval request')).toBeTruthy();
      });

      // Should allow retry
      mockPurchaseApiClient.createApprovalRequest.mockResolvedValue(approvalRequest);
      fireEvent.press(getByText('Retry'));

      await waitFor(() => {
        expect(getByText('Approval Request Sent')).toBeTruthy();
      });
    });
  });

  afterEach(() => {
    cleanupMocks();
    jest.clearAllMocks();
  });
});
