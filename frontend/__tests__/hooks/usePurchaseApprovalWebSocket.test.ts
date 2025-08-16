/**
 * usePurchaseApprovalWebSocket Hook Tests
 *
 * Comprehensive tests for purchase approval WebSocket functionality including:
 * - Real-time purchase approval notifications
 * - New approval requests from children
 * - Request status changes (approved/rejected)
 * - Budget threshold alerts and auto-approval notifications
 * - Push notification integration
 * - Notification management (read/unread, clearing)
 * - Acknowledgment system
 * - Error handling and edge cases
 */

import { renderHook, act, waitFor } from '@testing-library/react-native';

import { MockWebSocket, WebSocketTestUtils } from '../utils/websocket-test-utils';

import {
  usePurchaseApprovalWebSocket,
  usePurchaseApprovalPreferences,
  PurchaseApprovalNotification,
} from '@/hooks/usePurchaseApprovalWebSocket';

// Mock dependencies
jest.mock('@/hooks/useWebSocket', () => ({
  useWebSocket: jest.fn(),
}));

// Mock Notifications API
const mockNotification = {
  close: jest.fn(),
  onclick: null,
};

// Create a mock Notification constructor
const MockNotificationConstructor = jest.fn(() => mockNotification);
MockNotificationConstructor.permission = 'granted';
MockNotificationConstructor.requestPermission = jest.fn().mockResolvedValue('granted');

Object.defineProperty(global, 'Notification', {
  value: MockNotificationConstructor,
  writable: true,
  configurable: true,
});

// Mock window
Object.defineProperty(global, 'window', {
  value: {
    focus: jest.fn(),
    Notification: MockNotificationConstructor,
  },
  writable: true,
  configurable: true,
});

// Mock console methods
const originalConsoleLog = console.log;
const originalConsoleError = console.error;

describe('usePurchaseApprovalWebSocket', () => {
  let mockUseWebSocket: jest.Mock;
  let mockSendMessage: jest.Mock;

  beforeEach(() => {
    mockSendMessage = jest.fn();
    mockUseWebSocket = require('@/hooks/useWebSocket').useWebSocket;

    mockUseWebSocket.mockReturnValue({
      isConnected: false,
      sendMessage: mockSendMessage,
    });

    // Suppress console logs during tests
    if (__DEV__) {
      // Suppress console logs during tests
      console.log = jest.fn();
      // Suppress console logs during tests
    }
    console.error = jest.fn();

    // Reset Notification mock
    jest.clearAllMocks();
    const MockNotificationConstructor = global.Notification as any;
    MockNotificationConstructor.permission = 'granted';
    MockNotificationConstructor.requestPermission.mockResolvedValue('granted');

    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
    if (__DEV__) {
      jest.useRealTimers();
      console.log = originalConsoleLog;
      jest.useRealTimers();
    }
    console.error = originalConsoleError;
    jest.clearAllMocks();
  });

  describe('Initialization', () => {
    it('should initialize with correct default values', () => {
      const { result } = renderHook(() => usePurchaseApprovalWebSocket({ parentId: 'parent_123' }));

      expect(result.current.isConnected).toBe(false);
      expect(result.current.notifications).toEqual([]);
      expect(result.current.unreadCount).toBe(0);
      expect(typeof result.current.markAsRead).toBe('function');
      expect(typeof result.current.markAllAsRead).toBe('function');
      expect(typeof result.current.clearNotification).toBe('function');
      expect(typeof result.current.clearAllNotifications).toBe('function');
      expect(typeof result.current.sendAcknowledgment).toBe('function');
    });

    it('should construct correct WebSocket URL', () => {
      const parentId = 'parent_123';

      renderHook(() => usePurchaseApprovalWebSocket({ parentId }));

      expect(mockUseWebSocket).toHaveBeenCalledWith({
        url: 'ws://localhost:8000/ws/parent/parent_123/approvals/',
        channelName: 'purchase_approvals',
        onMessage: expect.any(Function),
        shouldConnect: true,
      });
    });

    it('should not connect when parentId is not provided', () => {
      renderHook(() => usePurchaseApprovalWebSocket({}));

      expect(mockUseWebSocket).toHaveBeenCalledWith({
        url: '',
        channelName: 'purchase_approvals',
        onMessage: expect.any(Function),
        shouldConnect: false,
      });
    });

    it('should request push notification permission on mount', async () => {
      const MockNotificationConstructor = global.Notification as any;
      MockNotificationConstructor.permission = 'default';

      renderHook(() =>
        usePurchaseApprovalWebSocket({
          parentId: 'parent_123',
          enablePushNotifications: true,
        }),
      );

      await act(async () => {
        jest.advanceTimersByTime(100);
      });

      expect(MockNotificationConstructor.requestPermission).toHaveBeenCalled();
    });
  });

  describe('Message Handling', () => {
    it('should handle new request notifications', () => {
      const mockOnNewRequest = jest.fn();

      const { result } = renderHook(() =>
        usePurchaseApprovalWebSocket({
          parentId: 'parent_123',
          onNewRequest: mockOnNewRequest,
        }),
      );

      // Simulate incoming message
      const testMessage = WebSocketTestUtils.createTestMessage.purchaseApproval({
        notification_type: 'new_request',
        title: 'New Purchase Request',
        message: 'Your child wants to buy a lesson package',
        data: {
          request_id: 123,
          child_name: 'Alice',
          amount: '25.00',
          plan_name: 'Math Tutoring Package',
        },
      });

      // Get the onMessage callback and call it
      const onMessageCallback = mockUseWebSocket.mock.calls[0][0].onMessage;
      act(() => {
        onMessageCallback({
          type: 'purchase_approval_notification',
          ...testMessage,
        });
      });

      expect(result.current.notifications).toHaveLength(1);
      expect(result.current.unreadCount).toBe(1);
      expect(mockOnNewRequest).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'new_request',
          title: 'New Purchase Request',
          read: false,
        }),
      );
    });

    it('should handle request status change notifications', () => {
      const mockOnRequestStatusChange = jest.fn();

      const { result } = renderHook(() =>
        usePurchaseApprovalWebSocket({
          parentId: 'parent_123',
          onRequestStatusChange: mockOnRequestStatusChange,
        }),
      );

      const testMessage = WebSocketTestUtils.createTestMessage.purchaseApproval({
        notification_type: 'request_approved',
        title: 'Request Approved',
        message: 'Purchase request has been approved',
        data: {
          request_id: 123,
          child_name: 'Alice',
          amount: '25.00',
        },
      });

      const onMessageCallback = mockUseWebSocket.mock.calls[0][0].onMessage;
      act(() => {
        onMessageCallback({
          type: 'purchase_approval_notification',
          ...testMessage,
        });
      });

      expect(result.current.notifications).toHaveLength(1);
      expect(mockOnRequestStatusChange).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'request_approved',
          title: 'Request Approved',
        }),
      );
    });

    it('should handle budget alert notifications', () => {
      const mockOnBudgetAlert = jest.fn();

      const { result } = renderHook(() =>
        usePurchaseApprovalWebSocket({
          parentId: 'parent_123',
          onBudgetAlert: mockOnBudgetAlert,
        }),
      );

      const testMessage = WebSocketTestUtils.createTestMessage.purchaseApproval({
        notification_type: 'budget_alert',
        title: 'Budget Alert',
        message: '80% of monthly budget reached',
        data: {
          budget_type: 'monthly',
          budget_percentage: 80,
        },
        priority: 'high',
      });

      const onMessageCallback = mockUseWebSocket.mock.calls[0][0].onMessage;
      act(() => {
        onMessageCallback({
          type: 'purchase_approval_notification',
          ...testMessage,
        });
      });

      expect(result.current.notifications).toHaveLength(1);
      expect(mockOnBudgetAlert).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'budget_alert',
          priority: 'high',
        }),
      );
    });

    it('should handle auto-approval notifications', () => {
      const mockOnAutoApproval = jest.fn();

      const { result } = renderHook(() =>
        usePurchaseApprovalWebSocket({
          parentId: 'parent_123',
          onAutoApproval: mockOnAutoApproval,
        }),
      );

      const testMessage = WebSocketTestUtils.createTestMessage.purchaseApproval({
        notification_type: 'auto_approved',
        title: 'Auto-Approved Purchase',
        message: 'Purchase was automatically approved',
        data: {
          request_id: 123,
          child_name: 'Alice',
          amount: '15.00',
        },
      });

      const onMessageCallback = mockUseWebSocket.mock.calls[0][0].onMessage;
      act(() => {
        onMessageCallback({
          type: 'purchase_approval_notification',
          ...testMessage,
        });
      });

      expect(result.current.notifications).toHaveLength(1);
      expect(mockOnAutoApproval).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'auto_approved',
          title: 'Auto-Approved Purchase',
        }),
      );
    });

    it('should limit notifications to maximum of 50', () => {
      const { result } = renderHook(() =>
        usePurchaseApprovalWebSocket({
          parentId: 'parent_123',
        }),
      );

      const onMessageCallback = mockUseWebSocket.mock.calls[0][0].onMessage;

      // Send 60 notifications
      act(() => {
        for (let i = 0; i < 60; i++) {
          const testMessage = WebSocketTestUtils.createTestMessage.purchaseApproval({
            notification_id: `notif_${i}`,
            notification_type: 'new_request',
            title: `Request ${i}`,
            message: `Purchase request ${i}`,
          });

          onMessageCallback({
            type: 'purchase_approval_notification',
            ...testMessage,
          });
        }
      });

      expect(result.current.notifications).toHaveLength(50);
    });

    it('should handle malformed messages gracefully', () => {
      const { result } = renderHook(() =>
        usePurchaseApprovalWebSocket({
          parentId: 'parent_123',
        }),
      );

      const onMessageCallback = mockUseWebSocket.mock.calls[0][0].onMessage;

      act(() => {
        // Send invalid message
        onMessageCallback('invalid message');
      });

      expect(result.current.notifications).toHaveLength(0);
      expect(console.error).toHaveBeenCalledWith(
        'Error processing purchase approval notification:',
        expect.any(Error),
      );
    });
  });

  describe('Push Notifications', () => {
    it('should show push notification when enabled and permission granted', () => {
      renderHook(() =>
        usePurchaseApprovalWebSocket({
          parentId: 'parent_123',
          enablePushNotifications: true,
        }),
      );

      const testMessage = WebSocketTestUtils.createTestMessage.purchaseApproval({
        notification_type: 'new_request',
        title: 'New Purchase Request',
        message: 'Your child wants to buy a lesson package',
        priority: 'medium',
      });

      const onMessageCallback = mockUseWebSocket.mock.calls[0][0].onMessage;
      act(() => {
        onMessageCallback({
          type: 'purchase_approval_notification',
          ...testMessage,
        });
      });

      expect(global.Notification).toHaveBeenCalledWith(
        'New Purchase Request',
        expect.objectContaining({
          body: 'Your child wants to buy a lesson package',
          icon: '/icon.png',
          badge: '/badge.png',
          requireInteraction: false,
        }),
      );
    });

    it('should require interaction for urgent notifications', () => {
      renderHook(() =>
        usePurchaseApprovalWebSocket({
          parentId: 'parent_123',
          enablePushNotifications: true,
        }),
      );

      const testMessage = WebSocketTestUtils.createTestMessage.purchaseApproval({
        notification_type: 'budget_alert',
        title: 'Critical Budget Alert',
        message: 'Budget exceeded!',
        priority: 'urgent',
      });

      const onMessageCallback = mockUseWebSocket.mock.calls[0][0].onMessage;
      act(() => {
        onMessageCallback({
          type: 'purchase_approval_notification',
          ...testMessage,
        });
      });

      expect(global.Notification).toHaveBeenCalledWith(
        'Critical Budget Alert',
        expect.objectContaining({
          requireInteraction: true,
        }),
      );
    });

    it('should not show push notifications when disabled', () => {
      renderHook(() =>
        usePurchaseApprovalWebSocket({
          parentId: 'parent_123',
          enablePushNotifications: false,
        }),
      );

      const testMessage = WebSocketTestUtils.createTestMessage.purchaseApproval({
        notification_type: 'new_request',
        title: 'New Purchase Request',
        message: 'Your child wants to buy a lesson package',
      });

      const onMessageCallback = mockUseWebSocket.mock.calls[0][0].onMessage;
      act(() => {
        onMessageCallback({
          type: 'purchase_approval_notification',
          ...testMessage,
        });
      });

      expect(global.Notification).not.toHaveBeenCalled();
    });

    it('should not show push notifications when permission denied', () => {
      const MockNotificationConstructor = global.Notification as any;
      MockNotificationConstructor.permission = 'denied';

      renderHook(() =>
        usePurchaseApprovalWebSocket({
          parentId: 'parent_123',
          enablePushNotifications: true,
        }),
      );

      const testMessage = WebSocketTestUtils.createTestMessage.purchaseApproval({
        notification_type: 'new_request',
        title: 'New Purchase Request',
        message: 'Your child wants to buy a lesson package',
      });

      const onMessageCallback = mockUseWebSocket.mock.calls[0][0].onMessage;
      act(() => {
        onMessageCallback({
          type: 'purchase_approval_notification',
          ...testMessage,
        });
      });

      expect(MockNotificationConstructor).not.toHaveBeenCalled();
    });

    it('should handle push notification click events', () => {
      const { result } = renderHook(() =>
        usePurchaseApprovalWebSocket({
          parentId: 'parent_123',
          enablePushNotifications: true,
        }),
      );

      const testMessage = WebSocketTestUtils.createTestMessage.purchaseApproval({
        notification_id: 'test_123',
        notification_type: 'new_request',
        title: 'New Purchase Request',
        message: 'Your child wants to buy a lesson package',
      });

      const onMessageCallback = mockUseWebSocket.mock.calls[0][0].onMessage;
      act(() => {
        onMessageCallback({
          type: 'purchase_approval_notification',
          ...testMessage,
        });
      });

      // Simulate clicking the push notification
      act(() => {
        mockNotification.onclick();
      });

      // Should focus window and mark as read
      expect(global.window.focus).toHaveBeenCalled();
      expect(mockNotification.close).toHaveBeenCalled();
      expect(result.current.notifications[0].read).toBe(true);
    });
  });

  describe('Notification Management', () => {
    it('should mark notification as read', () => {
      const { result } = renderHook(() =>
        usePurchaseApprovalWebSocket({
          parentId: 'parent_123',
        }),
      );

      // Add a notification
      const testMessage = WebSocketTestUtils.createTestMessage.purchaseApproval({
        notification_id: 'test_123',
        notification_type: 'new_request',
        title: 'Test Notification',
      });

      const onMessageCallback = mockUseWebSocket.mock.calls[0][0].onMessage;
      act(() => {
        onMessageCallback({
          type: 'purchase_approval_notification',
          ...testMessage,
        });
      });

      expect(result.current.unreadCount).toBe(1);

      // Mark as read
      act(() => {
        result.current.markAsRead('test_123');
      });

      expect(result.current.unreadCount).toBe(0);
      expect(result.current.notifications[0].read).toBe(true);
    });

    it('should mark all notifications as read', () => {
      const { result } = renderHook(() =>
        usePurchaseApprovalWebSocket({
          parentId: 'parent_123',
        }),
      );

      // Add multiple notifications
      const onMessageCallback = mockUseWebSocket.mock.calls[0][0].onMessage;
      act(() => {
        for (let i = 0; i < 3; i++) {
          const testMessage = WebSocketTestUtils.createTestMessage.purchaseApproval({
            notification_id: `test_${i}`,
            notification_type: 'new_request',
            title: `Test Notification ${i}`,
          });

          onMessageCallback({
            type: 'purchase_approval_notification',
            ...testMessage,
          });
        }
      });

      expect(result.current.unreadCount).toBe(3);

      // Mark all as read
      act(() => {
        result.current.markAllAsRead();
      });

      expect(result.current.unreadCount).toBe(0);
      result.current.notifications.forEach(notification => {
        expect(notification.read).toBe(true);
      });
    });

    it('should clear specific notification', () => {
      const { result } = renderHook(() =>
        usePurchaseApprovalWebSocket({
          parentId: 'parent_123',
        }),
      );

      // Add notifications
      const onMessageCallback = mockUseWebSocket.mock.calls[0][0].onMessage;
      act(() => {
        const testMessage1 = WebSocketTestUtils.createTestMessage.purchaseApproval({
          notification_id: 'test_1',
          title: 'Notification 1',
        });
        const testMessage2 = WebSocketTestUtils.createTestMessage.purchaseApproval({
          notification_id: 'test_2',
          title: 'Notification 2',
        });

        onMessageCallback({
          type: 'purchase_approval_notification',
          ...testMessage1,
        });
        onMessageCallback({
          type: 'purchase_approval_notification',
          ...testMessage2,
        });
      });

      expect(result.current.notifications).toHaveLength(2);

      // Clear specific notification
      act(() => {
        result.current.clearNotification('test_1');
      });

      expect(result.current.notifications).toHaveLength(1);
      expect(result.current.notifications[0].id).toBe('test_2');
    });

    it('should clear all notifications', () => {
      const { result } = renderHook(() =>
        usePurchaseApprovalWebSocket({
          parentId: 'parent_123',
        }),
      );

      // Add notifications
      const onMessageCallback = mockUseWebSocket.mock.calls[0][0].onMessage;
      act(() => {
        for (let i = 0; i < 5; i++) {
          const testMessage = WebSocketTestUtils.createTestMessage.purchaseApproval({
            notification_id: `test_${i}`,
            title: `Notification ${i}`,
          });

          onMessageCallback({
            type: 'purchase_approval_notification',
            ...testMessage,
          });
        }
      });

      expect(result.current.notifications).toHaveLength(5);

      // Clear all notifications
      act(() => {
        result.current.clearAllNotifications();
      });

      expect(result.current.notifications).toHaveLength(0);
      expect(result.current.unreadCount).toBe(0);
    });
  });

  describe('Acknowledgment System', () => {
    it('should send acknowledgment when connected', () => {
      mockUseWebSocket.mockReturnValue({
        isConnected: true,
        sendMessage: mockSendMessage,
      });

      const { result } = renderHook(() =>
        usePurchaseApprovalWebSocket({
          parentId: 'parent_123',
        }),
      );

      act(() => {
        result.current.sendAcknowledgment('request_123', 'received');
      });

      expect(mockSendMessage).toHaveBeenCalledWith({
        type: 'purchase_approval_ack',
        request_id: 'request_123',
        action: 'received',
        timestamp: expect.any(String),
      });
    });

    it('should not send acknowledgment when disconnected', () => {
      mockUseWebSocket.mockReturnValue({
        isConnected: false,
        sendMessage: mockSendMessage,
      });

      const { result } = renderHook(() =>
        usePurchaseApprovalWebSocket({
          parentId: 'parent_123',
        }),
      );

      act(() => {
        result.current.sendAcknowledgment('request_123', 'viewed');
      });

      expect(mockSendMessage).not.toHaveBeenCalled();
    });
  });

  describe('Connection State', () => {
    it('should reflect WebSocket connection state', () => {
      mockUseWebSocket.mockReturnValue({
        isConnected: true,
        sendMessage: mockSendMessage,
      });

      const { result } = renderHook(() =>
        usePurchaseApprovalWebSocket({
          parentId: 'parent_123',
        }),
      );

      expect(result.current.isConnected).toBe(true);
    });
  });
});

describe('usePurchaseApprovalPreferences', () => {
  beforeEach(() => {
    if (__DEV__) {
      console.log = jest.fn();
    }
    console.error = jest.fn();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
    if (__DEV__) {
      console.log = originalConsoleLog;
    }
    console.error = originalConsoleError;
    jest.clearAllMocks();
  });

  it('should initialize with default preferences', () => {
    const { result } = renderHook(() => usePurchaseApprovalPreferences());

    expect(result.current.preferences).toEqual({
      enablePushNotifications: true,
      enableEmailNotifications: true,
      enableSMSNotifications: false,
      notificationTypes: {
        new_request: true,
        budget_alerts: true,
        auto_approvals: true,
        status_changes: false,
      },
      quietHours: {
        enabled: false,
        start: '22:00',
        end: '08:00',
      },
      priorityFiltering: {
        showLowPriority: true,
        showMediumPriority: true,
        showHighPriority: true,
        showUrgentPriority: true,
      },
    });
  });

  it('should update preferences correctly', () => {
    const { result } = renderHook(() => usePurchaseApprovalPreferences());

    act(() => {
      result.current.updatePreferences({
        enablePushNotifications: false,
        notificationTypes: {
          new_request: false,
          budget_alerts: true,
          auto_approvals: true,
          status_changes: true,
        },
      });
    });

    expect(result.current.preferences.enablePushNotifications).toBe(false);
    expect(result.current.preferences.notificationTypes.new_request).toBe(false);
    expect(result.current.preferences.notificationTypes.status_changes).toBe(true);
    // Other preferences should remain unchanged
    expect(result.current.preferences.enableEmailNotifications).toBe(true);
  });

  it('should update quiet hours settings', () => {
    const { result } = renderHook(() => usePurchaseApprovalPreferences());

    act(() => {
      result.current.updatePreferences({
        quietHours: {
          enabled: true,
          start: '23:00',
          end: '07:00',
        },
      });
    });

    expect(result.current.preferences.quietHours).toEqual({
      enabled: true,
      start: '23:00',
      end: '07:00',
    });
  });

  it('should update priority filtering', () => {
    const { result } = renderHook(() => usePurchaseApprovalPreferences());

    act(() => {
      result.current.updatePreferences({
        priorityFiltering: {
          showLowPriority: false,
          showMediumPriority: true,
          showHighPriority: true,
          showUrgentPriority: true,
        },
      });
    });

    expect(result.current.preferences.priorityFiltering.showLowPriority).toBe(false);
    expect(result.current.preferences.priorityFiltering.showMediumPriority).toBe(true);
  });
});
