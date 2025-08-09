/**
 * Tests for usePurchaseApprovalWebSocket hook
 *
 * Tests cover:
 * - Purchase approval notification handling
 * - Push notification integration
 * - Notification management (read, clear, acknowledge)
 * - WebSocket connection management
 * - Notification preferences and filtering
 * - Parent ID validation and security
 * - Cross-platform notification support
 */

import { renderHook, act, waitFor } from '@testing-library/react-native';

import { usePurchaseApprovalWebSocket, usePurchaseApprovalPreferences } from '@/hooks/usePurchaseApprovalWebSocket';
import WebSocketTestUtils, { mockPushNotifications } from '@/__tests__/utils/websocket-test-utils';

// Mock the useWebSocket hook
jest.mock('@/hooks/useWebSocket', () => ({
  useWebSocket: jest.fn(),
}));

const mockUseWebSocket = require('@/hooks/useWebSocket').useWebSocket as jest.Mock;

describe('usePurchaseApprovalWebSocket Hook', () => {
  const mockParentId = 'parent123';
  const mockWebSocketResult = {
    isConnected: false,
    sendMessage: jest.fn(),
    connect: jest.fn(),
    disconnect: jest.fn(),
  };

  beforeEach(() => {
    WebSocketTestUtils.setup();
    WebSocketTestUtils.setupFakeTimers();
    jest.clearAllMocks();

    mockUseWebSocket.mockReturnValue(mockWebSocketResult);

    // Mock environment variable
    process.env.EXPO_PUBLIC_WS_URL = 'ws://localhost:8000';
  });

  afterEach(() => {
    WebSocketTestUtils.cleanup();
    WebSocketTestUtils.cleanupFakeTimers();
    if ('EXPO_PUBLIC_WS_URL' in process.env) {
      delete process.env.EXPO_PUBLIC_WS_URL;
    }
  });

  describe('Initialization', () => {
    it('should initialize with empty notifications and disconnected state', () => {
      const { result } = renderHook(() =>
        usePurchaseApprovalWebSocket({ parentId: mockParentId })
      );

      expect(result.current.isConnected).toBe(false);
      expect(result.current.notifications).toEqual([]);
      expect(result.current.unreadCount).toBe(0);
    });

    it('should build correct WebSocket URL for parent approvals', () => {
      renderHook(() =>
        usePurchaseApprovalWebSocket({ parentId: mockParentId })
      );

      expect(mockUseWebSocket).toHaveBeenCalledWith({
        url: `ws://localhost:8000/ws/parent/${mockParentId}/approvals/`,
        channelName: 'purchase_approvals',
        onMessage: expect.any(Function),
        shouldConnect: true,
      });
    });

    it('should not connect when parentId is not provided', () => {
      renderHook(() =>
        usePurchaseApprovalWebSocket({})
      );

      expect(mockUseWebSocket).toHaveBeenCalledWith({
        url: '',
        channelName: 'purchase_approvals',
        onMessage: expect.any(Function),
        shouldConnect: false,
      });
    });

    it('should use fallback WebSocket URL when environment variable is not set', () => {
      if ('EXPO_PUBLIC_WS_URL' in process.env) {
        delete process.env.EXPO_PUBLIC_WS_URL;
      }

      renderHook(() =>
        usePurchaseApprovalWebSocket({ parentId: mockParentId })
      );

      expect(mockUseWebSocket).toHaveBeenCalledWith({
        url: `ws://localhost:8000/ws/parent/${mockParentId}/approvals/`,
        channelName: 'purchase_approvals',
        onMessage: expect.any(Function),
        shouldConnect: true,
      });
    });
  });

  describe('Notification Processing', () => {
    it('should process new purchase approval request notifications', () => {
      const onNewRequest = jest.fn();

      const { result } = renderHook(() =>
        usePurchaseApprovalWebSocket({
          parentId: mockParentId,
          onNewRequest,
        })
      );

      // Get the message handler and simulate a new request
      const onMessage = mockUseWebSocket.mock.calls[0][0].onMessage;
      const testNotification = {
        type: 'purchase_approval_notification',
        notification_type: 'new_request',
        notification_id: 'req_123',
        title: 'New Purchase Request',
        message: 'Your child wants to buy a study package',
        data: {
          request_id: 123,
          child_name: 'Alice',
          amount: '25.00',
          plan_name: 'Basic Package',
        },
        priority: 'high',
        timestamp: new Date().toISOString(),
      };

      act(() => {
        onMessage(testNotification);
      });

      expect(result.current.notifications).toHaveLength(1);
      expect(result.current.notifications[0]).toMatchObject({
        id: 'req_123',
        type: 'new_request',
        title: 'New Purchase Request',
        message: 'Your child wants to buy a study package',
        read: false,
        actionable: false,
      });
      expect(result.current.unreadCount).toBe(1);
      expect(onNewRequest).toHaveBeenCalledWith(expect.objectContaining({
        type: 'new_request',
        title: 'New Purchase Request',
      }));
    });

    it('should process request status change notifications', () => {
      const onRequestStatusChange = jest.fn();

      const { result } = renderHook(() =>
        usePurchaseApprovalWebSocket({
          parentId: mockParentId,
          onRequestStatusChange,
        })
      );

      const onMessage = mockUseWebSocket.mock.calls[0][0].onMessage;
      const statusChangeNotification = {
        type: 'purchase_approval_notification',
        notification_type: 'request_approved',
        notification_id: 'approved_123',
        title: 'Request Approved',
        message: 'Purchase request has been approved',
        data: {
          request_id: 123,
          child_name: 'Alice',
        },
        priority: 'medium',
        timestamp: new Date().toISOString(),
      };

      act(() => {
        onMessage(statusChangeNotification);
      });

      expect(result.current.notifications).toHaveLength(1);
      expect(result.current.notifications[0].type).toBe('request_approved');
      expect(onRequestStatusChange).toHaveBeenCalledWith(expect.objectContaining({
        type: 'request_approved',
      }));
    });

    it('should process budget alert notifications', () => {
      const onBudgetAlert = jest.fn();

      const { result } = renderHook(() =>
        usePurchaseApprovalWebSocket({
          parentId: mockParentId,
          onBudgetAlert,
        })
      );

      const onMessage = mockUseWebSocket.mock.calls[0][0].onMessage;
      const budgetAlert = {
        type: 'purchase_approval_notification',
        notification_type: 'budget_alert',
        notification_id: 'budget_123',
        title: 'Budget Alert',
        message: 'Monthly budget threshold reached',
        data: {
          budget_type: 'monthly',
          budget_percentage: 85,
        },
        priority: 'high',
        timestamp: new Date().toISOString(),
      };

      act(() => {
        onMessage(budgetAlert);
      });

      expect(result.current.notifications).toHaveLength(1);
      expect(result.current.notifications[0].type).toBe('budget_alert');
      expect(onBudgetAlert).toHaveBeenCalledWith(expect.objectContaining({
        type: 'budget_alert',
      }));
    });

    it('should process auto-approval notifications', () => {
      const onAutoApproval = jest.fn();

      const { result } = renderHook(() =>
        usePurchaseApprovalWebSocket({
          parentId: mockParentId,
          onAutoApproval,
        })
      );

      const onMessage = mockUseWebSocket.mock.calls[0][0].onMessage;
      const autoApprovalNotification = {
        type: 'purchase_approval_notification',
        notification_type: 'auto_approved',
        notification_id: 'auto_123',
        title: 'Auto-Approved Purchase',
        message: 'Purchase was automatically approved',
        data: {
          request_id: 123,
          child_name: 'Alice',
          amount: '15.00',
        },
        priority: 'low',
        timestamp: new Date().toISOString(),
      };

      act(() => {
        onMessage(autoApprovalNotification);
      });

      expect(result.current.notifications).toHaveLength(1);
      expect(result.current.notifications[0].type).toBe('auto_approved');
      expect(onAutoApproval).toHaveBeenCalledWith(expect.objectContaining({
        type: 'auto_approved',
      }));
    });

    it('should handle malformed notification data gracefully', () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

      const { result } = renderHook(() =>
        usePurchaseApprovalWebSocket({ parentId: mockParentId })
      );

      const onMessage = mockUseWebSocket.mock.calls[0][0].onMessage;

      // Test malformed JSON string
      act(() => {
        onMessage('invalid json {');
      });

      // Test invalid message structure
      act(() => {
        onMessage({ invalid: 'structure' });
      });

      expect(result.current.notifications).toHaveLength(0);
      expect(consoleSpy).toHaveBeenCalledWith(
        'Error processing purchase approval notification:',
        expect.any(Error)
      );

      consoleSpy.mockRestore();
    });

    it('should limit notifications to maximum of 50', () => {
      const { result } = renderHook(() =>
        usePurchaseApprovalWebSocket({ parentId: mockParentId })
      );

      const onMessage = mockUseWebSocket.mock.calls[0][0].onMessage;

      // Add 52 notifications
      act(() => {
        for (let i = 0; i < 52; i++) {
          onMessage({
            type: 'purchase_approval_notification',
            notification_type: 'new_request',
            notification_id: `req_${i}`,
            title: `Request ${i}`,
            message: `Message ${i}`,
            priority: 'medium',
            timestamp: new Date().toISOString(),
          });
        }
      });

      // Should only keep the most recent 50
      expect(result.current.notifications).toHaveLength(50);
      expect(result.current.notifications[0].id).toBe('req_51'); // Most recent
      expect(result.current.notifications[49].id).toBe('req_2'); // 50th most recent
    });
  });

  describe('Push Notifications', () => {
    beforeEach(() => {
      // Mock the Notification API
      mockPushNotifications();
    });

    it('should show push notification for high priority notifications', () => {
      renderHook(() =>
        usePurchaseApprovalWebSocket({
          parentId: mockParentId,
          enablePushNotifications: true,
        })
      );

      const onMessage = mockUseWebSocket.mock.calls[0][0].onMessage;
      const highPriorityNotification = {
        type: 'purchase_approval_notification',
        notification_type: 'new_request',
        notification_id: 'urgent_123',
        title: 'Urgent Purchase Request',
        message: 'High-value purchase requires approval',
        priority: 'urgent',
        timestamp: new Date().toISOString(),
      };

      act(() => {
        onMessage(highPriorityNotification);
      });

      expect(global.Notification).toHaveBeenCalledWith(
        'Urgent Purchase Request',
        expect.objectContaining({
          body: 'High-value purchase requires approval',
          icon: '/icon.png',
          badge: '/badge.png',
          tag: 'approval_urgent_123',
          requireInteraction: true, // For urgent notifications
          data: {
            notificationId: 'urgent_123',
            requestId: undefined,
          },
        })
      );
    });

    it('should not show push notifications when disabled', () => {
      renderHook(() =>
        usePurchaseApprovalWebSocket({
          parentId: mockParentId,
          enablePushNotifications: false,
        })
      );

      const onMessage = mockUseWebSocket.mock.calls[0][0].onMessage;
      const notification = {
        type: 'purchase_approval_notification',
        notification_type: 'new_request',
        notification_id: 'req_123',
        title: 'Purchase Request',
        message: 'New purchase request',
        priority: 'high',
        timestamp: new Date().toISOString(),
      };

      act(() => {
        onMessage(notification);
      });

      expect(global.Notification).not.toHaveBeenCalled();
    });

    it('should request push notification permission on mount', () => {
      global.Notification.permission = 'default';

      renderHook(() =>
        usePurchaseApprovalWebSocket({
          parentId: mockParentId,
          enablePushNotifications: true,
        })
      );

      expect(global.Notification.requestPermission).toHaveBeenCalled();
    });

    it('should not request permission when already granted', () => {
      global.Notification.permission = 'granted';
      global.Notification.requestPermission = jest.fn();

      renderHook(() =>
        usePurchaseApprovalWebSocket({
          parentId: mockParentId,
          enablePushNotifications: true,
        })
      );

      expect(global.Notification.requestPermission).not.toHaveBeenCalled();
    });
  });

  describe('Notification Management', () => {
    it('should mark individual notification as read', () => {
      const { result } = renderHook(() =>
        usePurchaseApprovalWebSocket({ parentId: mockParentId })
      );

      const onMessage = mockUseWebSocket.mock.calls[0][0].onMessage;

      // Add a notification
      act(() => {
        onMessage({
          type: 'purchase_approval_notification',
          notification_type: 'new_request',
          notification_id: 'req_123',
          title: 'Test Request',
          message: 'Test message',
          priority: 'medium',
          timestamp: new Date().toISOString(),
        });
      });

      expect(result.current.unreadCount).toBe(1);

      // Mark as read
      act(() => {
        result.current.markAsRead('req_123');
      });

      expect(result.current.unreadCount).toBe(0);
      expect(result.current.notifications[0].read).toBe(true);
    });

    it('should mark all notifications as read', () => {
      const { result } = renderHook(() =>
        usePurchaseApprovalWebSocket({ parentId: mockParentId })
      );

      const onMessage = mockUseWebSocket.mock.calls[0][0].onMessage;

      // Add multiple notifications
      act(() => {
        for (let i = 0; i < 3; i++) {
          onMessage({
            type: 'purchase_approval_notification',
            notification_type: 'new_request',
            notification_id: `req_${i}`,
            title: `Request ${i}`,
            message: `Message ${i}`,
            priority: 'medium',
            timestamp: new Date().toISOString(),
          });
        }
      });

      expect(result.current.unreadCount).toBe(3);

      // Mark all as read
      act(() => {
        result.current.markAllAsRead();
      });

      expect(result.current.unreadCount).toBe(0);
      expect(result.current.notifications.every(n => n.read)).toBe(true);
    });

    it('should clear individual notification', () => {
      const { result } = renderHook(() =>
        usePurchaseApprovalWebSocket({ parentId: mockParentId })
      );

      const onMessage = mockUseWebSocket.mock.calls[0][0].onMessage;

      // Add notifications
      act(() => {
        onMessage({
          type: 'purchase_approval_notification',
          notification_type: 'new_request',
          notification_id: 'req_1',
          title: 'Request 1',
          message: 'Message 1',
          priority: 'medium',
          timestamp: new Date().toISOString(),
        });
        onMessage({
          type: 'purchase_approval_notification',
          notification_type: 'new_request',
          notification_id: 'req_2',
          title: 'Request 2',
          message: 'Message 2',
          priority: 'medium',
          timestamp: new Date().toISOString(),
        });
      });

      expect(result.current.notifications).toHaveLength(2);

      // Clear one notification
      act(() => {
        result.current.clearNotification('req_1');
      });

      expect(result.current.notifications).toHaveLength(1);
      expect(result.current.notifications[0].id).toBe('req_2');
    });

    it('should clear all notifications', () => {
      const { result } = renderHook(() =>
        usePurchaseApprovalWebSocket({ parentId: mockParentId })
      );

      const onMessage = mockUseWebSocket.mock.calls[0][0].onMessage;

      // Add notifications
      act(() => {
        for (let i = 0; i < 5; i++) {
          onMessage({
            type: 'purchase_approval_notification',
            notification_type: 'new_request',
            notification_id: `req_${i}`,
            title: `Request ${i}`,
            message: `Message ${i}`,
            priority: 'medium',
            timestamp: new Date().toISOString(),
          });
        }
      });

      expect(result.current.notifications).toHaveLength(5);

      // Clear all
      act(() => {
        result.current.clearAllNotifications();
      });

      expect(result.current.notifications).toHaveLength(0);
      expect(result.current.unreadCount).toBe(0);
    });
  });

  describe('WebSocket Communication', () => {
    it('should send acknowledgment messages', () => {
      mockUseWebSocket.mockReturnValue({
        ...mockWebSocketResult,
        isConnected: true,
      });

      const { result } = renderHook(() =>
        usePurchaseApprovalWebSocket({ parentId: mockParentId })
      );

      act(() => {
        result.current.sendAcknowledgment('req_123', 'received');
      });

      expect(mockWebSocketResult.sendMessage).toHaveBeenCalledWith({
        type: 'purchase_approval_ack',
        request_id: 'req_123',
        action: 'received',
        timestamp: expect.any(String),
      });
    });

    it('should not send acknowledgment when disconnected', () => {
      mockUseWebSocket.mockReturnValue({
        ...mockWebSocketResult,
        isConnected: false,
      });

      const { result } = renderHook(() =>
        usePurchaseApprovalWebSocket({ parentId: mockParentId })
      );

      act(() => {
        result.current.sendAcknowledgment('req_123', 'viewed');
      });

      expect(mockWebSocketResult.sendMessage).not.toHaveBeenCalled();
    });

    it('should reflect WebSocket connection state', () => {
      mockUseWebSocket.mockReturnValue({
        ...mockWebSocketResult,
        isConnected: true,
      });

      const { result } = renderHook(() =>
        usePurchaseApprovalWebSocket({ parentId: mockParentId })
      );

      expect(result.current.isConnected).toBe(true);
    });
  });

  describe('Performance and Edge Cases', () => {
    it('should handle rapid notification processing efficiently', () => {
      const { result } = renderHook(() =>
        usePurchaseApprovalWebSocket({ parentId: mockParentId })
      );

      const onMessage = mockUseWebSocket.mock.calls[0][0].onMessage;
      const startTime = Date.now();

      // Process 100 notifications rapidly
      act(() => {
        for (let i = 0; i < 100; i++) {
          onMessage({
            type: 'purchase_approval_notification',
            notification_type: 'new_request',
            notification_id: `req_${i}`,
            title: `Request ${i}`,
            message: `Message ${i}`,
            priority: 'medium',
            timestamp: new Date().toISOString(),
          });
        }
      });

      const endTime = Date.now();
      expect(endTime - startTime).toBeLessThan(100); // Should complete quickly
      expect(result.current.notifications).toHaveLength(50); // Limited to 50
    });

    it('should handle notification ID generation for notifications without IDs', () => {
      const { result } = renderHook(() =>
        usePurchaseApprovalWebSocket({ parentId: mockParentId })
      );

      const onMessage = mockUseWebSocket.mock.calls[0][0].onMessage;

      act(() => {
        onMessage({
          type: 'purchase_approval_notification',
          notification_type: 'new_request',
          // No notification_id provided
          title: 'Request without ID',
          message: 'Message without ID',
          priority: 'medium',
          timestamp: new Date().toISOString(),
        });
      });

      expect(result.current.notifications).toHaveLength(1);
      expect(result.current.notifications[0].id).toMatch(/^notif_\d+$/);
    });
  });
});

describe('usePurchaseApprovalPreferences Hook', () => {
  beforeEach(() => {
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

  it('should allow updating preferences', () => {
    const { result } = renderHook(() => usePurchaseApprovalPreferences());

    act(() => {
      result.current.updatePreferences({
        enablePushNotifications: false,
        enableSMSNotifications: true,
        quietHours: {
          enabled: true,
          start: '21:00',
          end: '07:00',
        },
      });
    });

    expect(result.current.preferences.enablePushNotifications).toBe(false);
    expect(result.current.preferences.enableSMSNotifications).toBe(true);
    expect(result.current.preferences.quietHours.enabled).toBe(true);
    expect(result.current.preferences.quietHours.start).toBe('21:00');
  });

  it('should preserve existing preferences when partially updating', () => {
    const { result } = renderHook(() => usePurchaseApprovalPreferences());

    act(() => {
      result.current.updatePreferences({
        enablePushNotifications: false,
      });
    });

    expect(result.current.preferences.enablePushNotifications).toBe(false);
    expect(result.current.preferences.enableEmailNotifications).toBe(true); // Should remain unchanged
    expect(result.current.preferences.notificationTypes.new_request).toBe(true); // Should remain unchanged
  });

  it('should allow updating nested preference objects', () => {
    const { result } = renderHook(() => usePurchaseApprovalPreferences());

    act(() => {
      result.current.updatePreferences({
        notificationTypes: {
          ...result.current.preferences.notificationTypes,
          new_request: false,
          status_changes: true,
        },
      });
    });

    expect(result.current.preferences.notificationTypes.new_request).toBe(false);
    expect(result.current.preferences.notificationTypes.status_changes).toBe(true);
    expect(result.current.preferences.notificationTypes.budget_alerts).toBe(true); // Should remain unchanged
  });
});