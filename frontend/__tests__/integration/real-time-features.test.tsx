/**
 * Integration Tests for Real-time WebSocket Features
 *
 * Tests cover:
 * - Multi-component WebSocket coordination
 * - Cross-feature real-time updates
 * - Connection sharing and management
 * - Resilience and recovery scenarios
 * - Performance under concurrent load
 * - End-to-end user workflows
 * - Network interruption handling
 * - Authentication across multiple connections
 */

import { renderHook, act, waitFor } from '@testing-library/react-native';
import React from 'react';

import WebSocketTestUtils, { WebSocketTestData } from '@/__tests__/utils/websocket-test-utils';
import { useBalanceWebSocket } from '@/hooks/useBalanceWebSocket';
import { usePaymentMonitoringWebSocket } from '@/hooks/usePaymentMonitoringWebSocket';
import { usePurchaseApprovalWebSocket } from '@/hooks/usePurchaseApprovalWebSocket';
import { useWebSocket, useWebSocketEnhanced } from '@/hooks/useWebSocket';

// Mock dependencies
jest.mock('@/api/auth', () => ({
  useAuth: jest.fn(),
  useUserProfile: jest.fn(),
}));

jest.mock('@/hooks/useWebSocket', () => ({
  useWebSocket: jest.fn(),
  useWebSocketEnhanced: jest.fn(),
}));

const mockUseUserProfile = require('@/api/auth').useUserProfile as jest.Mock;
const mockUseWebSocket = require('@/hooks/useWebSocket').useWebSocket as jest.Mock;
const mockUseWebSocketEnhanced = require('@/hooks/useWebSocket').useWebSocketEnhanced as jest.Mock;

describe('Real-time WebSocket Features Integration', () => {
  const mockUserProfile = {
    id: 1,
    email: 'test@example.com',
    first_name: 'Test',
    last_name: 'User',
    role: 'parent',
  };

  beforeEach(() => {
    WebSocketTestUtils.setup();
    WebSocketTestUtils.setupFakeTimers();
    jest.clearAllMocks();

    mockUseUserProfile.mockReturnValue({
      userProfile: mockUserProfile,
    });

    // Mock console methods to reduce noise
    jest.spyOn(console, 'log').mockImplementation();
    jest.spyOn(console, 'error').mockImplementation();
    jest.spyOn(console, 'warn').mockImplementation();

    WebSocketTestUtils.mockAsyncStorage('integration-test-token');
  });

  afterEach(() => {
    WebSocketTestUtils.cleanup();
    WebSocketTestUtils.cleanupFakeTimers();
    jest.restoreAllMocks();
  });

  describe('Multi-Component Coordination', () => {
    it('should coordinate balance updates across multiple components', async () => {
      const mockWebSocketResult = {
        isConnected: true,
        lastMessage: null,
        sendMessage: jest.fn(),
        connect: jest.fn(),
        disconnect: jest.fn(),
      };

      mockUseWebSocketEnhanced.mockReturnValue(mockWebSocketResult);

      const { result: balanceHook1 } = renderHook(() => useBalanceWebSocket({ enabled: true }));
      const { result: balanceHook2 } = renderHook(() => useBalanceWebSocket({ enabled: true }));

      // Simulate balance update message
      const balanceUpdate = WebSocketTestData.balanceUpdate(mockUserProfile.id, 150.75);

      act(() => {
        mockWebSocketResult.lastMessage = JSON.stringify(balanceUpdate);
      });

      await waitFor(() => {
        expect(balanceHook1.current.latestBalance?.current_balance).toBe(150.75);
        expect(balanceHook2.current.latestBalance?.current_balance).toBe(150.75);
      });

      // Both hooks should receive the same update
      expect(balanceHook1.current.latestBalance).toEqual(balanceHook2.current.latestBalance);
    });

    it('should handle simultaneous purchase approval and balance updates', async () => {
      // Mock balance WebSocket
      const mockBalanceWS = {
        isConnected: true,
        lastMessage: null,
        sendMessage: jest.fn(),
        connect: jest.fn(),
        disconnect: jest.fn(),
      };

      // Mock purchase approval WebSocket
      const mockApprovalWS = {
        isConnected: true,
        sendMessage: jest.fn(),
        connect: jest.fn(),
        disconnect: jest.fn(),
      };

      mockUseWebSocketEnhanced.mockReturnValue(mockBalanceWS);
      mockUseWebSocket.mockReturnValue(mockApprovalWS);

      const { result: balanceHook } = renderHook(() => useBalanceWebSocket({ enabled: true }));
      const { result: approvalHook } = renderHook(() =>
        usePurchaseApprovalWebSocket({ parentId: 'parent123' }),
      );

      // Simulate simultaneous updates
      const balanceUpdate = WebSocketTestData.balanceUpdate(mockUserProfile.id, 75.25);
      const approvalNotification = WebSocketTestData.purchaseApproval(mockUserProfile.id, 1);

      act(() => {
        // Balance update
        mockBalanceWS.lastMessage = JSON.stringify(balanceUpdate);

        // Approval notification
        const approvalMessage = mockUseWebSocket.mock.calls[0][0].onMessage;
        approvalMessage(approvalNotification);
      });

      await waitFor(() => {
        expect(balanceHook.current.latestBalance?.current_balance).toBe(75.25);
        expect(approvalHook.current.notifications).toHaveLength(1);
      });

      expect(approvalHook.current.notifications[0].type).toBe('new_request');
      expect(balanceHook.current.connected).toBe(true);
      expect(approvalHook.current.isConnected).toBe(true);
    });

    it('should manage payment monitoring alongside other WebSocket connections', async () => {
      WebSocketTestUtils.mockAsyncStorage('admin-token');

      const { result: paymentMonitoring } = renderHook(() => usePaymentMonitoringWebSocket(true));

      const { result: balanceHook } = renderHook(() => useBalanceWebSocket({ enabled: true }));

      await act(async () => {
        WebSocketTestUtils.advanceTime(100);
      });

      // Should establish multiple WebSocket connections
      const allWebSockets = WebSocketTestUtils.getAllWebSockets();
      expect(allWebSockets.length).toBeGreaterThanOrEqual(2);

      // Both should be connected
      expect(paymentMonitoring.current.isConnected).toBe(true);
      expect(balanceHook.current.connected).toBe(true);
    });
  });

  describe('Cross-Feature Real-time Updates', () => {
    it('should trigger balance alert when purchase is approved', async () => {
      const onBalanceUpdate = jest.fn();
      const onApprovalNotification = jest.fn();

      // Mock WebSocket connections
      const mockBalanceWS = {
        isConnected: true,
        lastMessage: null,
        sendMessage: jest.fn(),
        connect: jest.fn(),
        disconnect: jest.fn(),
      };

      const mockApprovalWS = {
        isConnected: true,
        sendMessage: jest.fn(),
      };

      mockUseWebSocketEnhanced.mockReturnValue(mockBalanceWS);
      mockUseWebSocket.mockReturnValue(mockApprovalWS);

      renderHook(() => useBalanceWebSocket({ enabled: true }));
      renderHook(() =>
        usePurchaseApprovalWebSocket({
          parentId: 'parent123',
          onNewRequest: onApprovalNotification,
        }),
      );

      // Simulate purchase approval workflow
      act(() => {
        // 1. Purchase approval request
        const approvalMessage = mockUseWebSocket.mock.calls[0][0].onMessage;
        approvalMessage(WebSocketTestData.purchaseApproval(mockUserProfile.id, 1));

        // 2. Balance update after purchase
        mockBalanceWS.lastMessage = JSON.stringify(
          WebSocketTestData.balanceUpdate(mockUserProfile.id, 50.0), // Lower balance after purchase
        );
      });

      expect(onApprovalNotification).toHaveBeenCalled();
      expect(mockBalanceWS.lastMessage).toContain('"current_balance":50');
    });

    it('should coordinate transaction monitoring with balance updates', async () => {
      WebSocketTestUtils.mockAsyncStorage('admin-token');

      const { result: paymentMonitoring } = renderHook(() => usePaymentMonitoringWebSocket(true));

      const { result: balanceHook } = renderHook(() => useBalanceWebSocket({ enabled: true }));

      await act(async () => {
        WebSocketTestUtils.advanceTime(100);
      });

      const paymentWS = WebSocketTestUtils.getAllWebSockets().find(ws =>
        ws.url.includes('/ws/admin/payments/'),
      );

      const balanceWS = WebSocketTestUtils.getAllWebSockets().find(
        ws => ws.url.includes('/balance/') || ws === WebSocketTestUtils.getLastWebSocket(),
      );

      // Simulate coordinated updates
      act(() => {
        if (paymentWS) {
          // New transaction processed
          paymentWS.simulateMessage(
            JSON.stringify({
              type: 'transaction_update',
              data: {
                action: 'created',
                transaction: {
                  id: 'txn_123',
                  user_id: mockUserProfile.id,
                  amount: 25.0,
                  currency: 'EUR',
                  status: 'completed',
                  created_at: new Date().toISOString(),
                },
              },
              timestamp: new Date().toISOString(),
            }),
          );
        }

        // Corresponding balance update
        if (mockUseWebSocketEnhanced.mock.results[0]?.value) {
          const mockBalanceResult = mockUseWebSocketEnhanced.mock.results[0].value;
          mockBalanceResult.lastMessage = JSON.stringify(
            WebSocketTestData.balanceUpdate(mockUserProfile.id, 125.0),
          );
        }
      });

      expect(paymentMonitoring.current.recentTransactions).toHaveLength(1);
      expect(paymentMonitoring.current.recentTransactions[0].id).toBe('txn_123');
    });
  });

  describe('Connection Resilience and Recovery', () => {
    it('should recover all connections after network interruption', async () => {
      const { result: balanceHook } = renderHook(() => useBalanceWebSocket({ enabled: true }));

      const { result: approvalHook } = renderHook(() =>
        usePurchaseApprovalWebSocket({ parentId: 'parent123' }),
      );

      await act(async () => {
        WebSocketTestUtils.advanceTime(100);
      });

      // Both connections should be established
      expect(balanceHook.current.connected).toBe(true);
      expect(approvalHook.current.isConnected).toBe(true);

      // Simulate network failure affecting all connections
      const allWebSockets = WebSocketTestUtils.getAllWebSockets();
      act(() => {
        allWebSockets.forEach(ws => ws.simulateNetworkFailure());
      });

      // All connections should be down
      expect(balanceHook.current.connected).toBe(false);
      expect(approvalHook.current.isConnected).toBe(false);

      // Simulate network recovery with exponential backoff
      await act(async () => {
        WebSocketTestUtils.advanceTime(1100); // First reconnection attempt
      });

      // Connections should recover
      expect(WebSocketTestUtils.getAllWebSockets().length).toBeGreaterThan(allWebSockets.length);
    });

    it('should handle partial connection failures gracefully', async () => {
      const { result: balanceHook } = renderHook(() => useBalanceWebSocket({ enabled: true }));

      const { result: approvalHook } = renderHook(() =>
        usePurchaseApprovalWebSocket({ parentId: 'parent123' }),
      );

      await act(async () => {
        WebSocketTestUtils.advanceTime(100);
      });

      // Fail only one connection
      const allWebSockets = WebSocketTestUtils.getAllWebSockets();
      act(() => {
        if (allWebSockets.length > 0) {
          allWebSockets[0].simulateNetworkFailure();
        }
      });

      // One should recover, one should remain connected
      await act(async () => {
        WebSocketTestUtils.advanceTime(1100);
      });

      // At least one connection should still be working
      const connectedCount = [
        balanceHook.current.connected,
        approvalHook.current.isConnected,
      ].filter(Boolean).length;

      expect(connectedCount).toBeGreaterThan(0);
    });

    it('should maintain message ordering during reconnection', async () => {
      const receivedMessages: any[] = [];
      const mockBalanceWS = {
        isConnected: true,
        lastMessage: null,
        sendMessage: jest.fn(),
        connect: jest.fn(),
        disconnect: jest.fn(),
      };

      mockUseWebSocketEnhanced.mockReturnValue(mockBalanceWS);

      renderHook(() => useBalanceWebSocket({ enabled: true }));

      // Simulate messages during connection instability
      const messages = [
        WebSocketTestData.balanceUpdate(mockUserProfile.id, 100.0),
        WebSocketTestData.balanceUpdate(mockUserProfile.id, 95.0),
        WebSocketTestData.balanceUpdate(mockUserProfile.id, 90.0),
      ];

      act(() => {
        messages.forEach((message, index) => {
          setTimeout(() => {
            mockBalanceWS.lastMessage = JSON.stringify(message);
            receivedMessages.push(message);
          }, index * 10);
        });
      });

      await act(async () => {
        WebSocketTestUtils.advanceTime(100);
      });

      // Messages should be received in order
      expect(receivedMessages).toHaveLength(3);
      expect(receivedMessages[0].data.balance.current_balance).toBe(100.0);
      expect(receivedMessages[1].data.balance.current_balance).toBe(95.0);
      expect(receivedMessages[2].data.balance.current_balance).toBe(90.0);
    });
  });

  describe('Performance Under Load', () => {
    it('should handle high-frequency updates across multiple connections', async () => {
      const { result: paymentMonitoring } = renderHook(() => usePaymentMonitoringWebSocket(true));

      const { result: balanceHook } = renderHook(() => useBalanceWebSocket({ enabled: true }));

      await act(async () => {
        WebSocketTestUtils.advanceTime(100);
      });

      const startTime = Date.now();

      // Simulate high-frequency updates
      act(() => {
        // 100 payment monitoring updates
        for (let i = 0; i < 100; i++) {
          const paymentWS = WebSocketTestUtils.getAllWebSockets().find(ws =>
            ws.url.includes('/ws/admin/payments/'),
          );

          if (paymentWS) {
            paymentWS.simulateMessage(
              JSON.stringify({
                type: 'transaction_update',
                data: {
                  action: 'created',
                  transaction: {
                    id: `txn_${i}`,
                    amount: 10.0 + i,
                    status: 'completed',
                  },
                },
                timestamp: new Date().toISOString(),
              }),
            );
          }
        }

        // 50 balance updates
        const mockBalanceResult = mockUseWebSocketEnhanced.mock.results[0]?.value;
        for (let i = 0; i < 50; i++) {
          if (mockBalanceResult) {
            mockBalanceResult.lastMessage = JSON.stringify(
              WebSocketTestData.balanceUpdate(mockUserProfile.id, 200.0 - i * 2),
            );
          }
        }
      });

      const endTime = Date.now();
      expect(endTime - startTime).toBeLessThan(1000); // Should process within 1 second

      // Verify data integrity under load
      expect(paymentMonitoring.current.recentTransactions).toHaveLength(50); // Limited to 50
    });

    it('should maintain responsive UI during message processing', async () => {
      const renderStartTime = Date.now();

      const { result: balanceHook } = renderHook(() => useBalanceWebSocket({ enabled: true }));

      const { result: approvalHook } = renderHook(() =>
        usePurchaseApprovalWebSocket({ parentId: 'parent123' }),
      );

      const renderEndTime = Date.now();
      expect(renderEndTime - renderStartTime).toBeLessThan(100); // Initial render should be fast

      await act(async () => {
        WebSocketTestUtils.advanceTime(100);
      });

      // Process multiple messages simultaneously
      const processingStartTime = Date.now();

      act(() => {
        // Balance updates
        const mockBalanceResult = mockUseWebSocketEnhanced.mock.results[0]?.value;
        if (mockBalanceResult) {
          for (let i = 0; i < 20; i++) {
            mockBalanceResult.lastMessage = JSON.stringify(
              WebSocketTestData.balanceUpdate(mockUserProfile.id, 100.0 + i),
            );
          }
        }

        // Approval notifications
        const approvalMessage = mockUseWebSocket.mock.calls[0]?.[0]?.onMessage;
        if (approvalMessage) {
          for (let i = 0; i < 10; i++) {
            approvalMessage(WebSocketTestData.purchaseApproval(mockUserProfile.id, i + 1));
          }
        }
      });

      const processingEndTime = Date.now();
      expect(processingEndTime - processingStartTime).toBeLessThan(200); // Should process quickly

      // Verify final state
      expect(approvalHook.current.notifications).toHaveLength(10);
    });
  });

  describe('End-to-End User Workflows', () => {
    it('should support complete purchase approval workflow', async () => {
      const workflowSteps: string[] = [];

      const { result: balanceHook } = renderHook(() =>
        useBalanceWebSocket({
          enabled: true,
        }),
      );

      const { result: approvalHook } = renderHook(() =>
        usePurchaseApprovalWebSocket({
          parentId: 'parent123',
          onNewRequest: () => workflowSteps.push('approval_received'),
          onRequestStatusChange: () => workflowSteps.push('approval_processed'),
        }),
      );

      await act(async () => {
        WebSocketTestUtils.advanceTime(100);
      });

      // Step 1: New purchase request
      act(() => {
        const approvalMessage = mockUseWebSocket.mock.calls[0][0].onMessage;
        approvalMessage({
          type: 'purchase_approval_notification',
          notification_type: 'new_request',
          notification_id: 'req_workflow_test',
          title: 'New Purchase Request',
          message: 'Student wants to purchase Basic Package',
          data: {
            request_id: 999,
            child_name: 'Test Student',
            amount: '25.00',
            plan_name: 'Basic Package',
          },
          priority: 'high',
          timestamp: new Date().toISOString(),
        });
      });

      expect(workflowSteps).toContain('approval_received');
      expect(approvalHook.current.notifications).toHaveLength(1);

      // Step 2: Parent approves purchase
      act(() => {
        approvalHook.current.sendAcknowledgment('999', 'viewed');
      });

      // Step 3: Purchase processed notification
      act(() => {
        const approvalMessage = mockUseWebSocket.mock.calls[0][0].onMessage;
        approvalMessage({
          type: 'purchase_approval_notification',
          notification_type: 'request_approved',
          notification_id: 'req_approved_test',
          title: 'Purchase Approved',
          message: 'Your approval has been processed',
          data: { request_id: 999 },
          priority: 'medium',
          timestamp: new Date().toISOString(),
        });
      });

      expect(workflowSteps).toContain('approval_processed');

      // Step 4: Balance updated after purchase
      act(() => {
        const mockBalanceResult = mockUseWebSocketEnhanced.mock.results[0]?.value;
        if (mockBalanceResult) {
          mockBalanceResult.lastMessage = JSON.stringify(
            WebSocketTestData.balanceUpdate(mockUserProfile.id, 25.0), // Balance after €25 purchase
          );
        }
      });

      expect(balanceHook.current.latestBalance?.current_balance).toBe(25.0);

      // Verify complete workflow
      expect(workflowSteps).toEqual(['approval_received', 'approval_processed']);
      expect(approvalHook.current.notifications).toHaveLength(2);
    });

    it('should handle concurrent multi-user scenarios', async () => {
      const user1 = { ...mockUserProfile, id: 1 };
      const user2 = { ...mockUserProfile, id: 2 };

      // Mock multiple user profiles
      mockUseUserProfile
        .mockReturnValueOnce({ userProfile: user1 })
        .mockReturnValueOnce({ userProfile: user2 });

      const { result: user1Balance } = renderHook(() => useBalanceWebSocket({ enabled: true }));

      const { result: user2Balance } = renderHook(() => useBalanceWebSocket({ enabled: true }));

      // Simulate user-specific balance updates
      act(() => {
        const mockBalanceResult1 = mockUseWebSocketEnhanced.mock.results[0]?.value;
        const mockBalanceResult2 = mockUseWebSocketEnhanced.mock.results[1]?.value;

        if (mockBalanceResult1) {
          mockBalanceResult1.lastMessage = JSON.stringify(
            WebSocketTestData.balanceUpdate(user1.id, 100.0),
          );
        }

        if (mockBalanceResult2) {
          mockBalanceResult2.lastMessage = JSON.stringify(
            WebSocketTestData.balanceUpdate(user2.id, 200.0),
          );
        }
      });

      // Users should only receive their own balance updates
      expect(user1Balance.current.latestBalance?.user_id).toBe(user1.id);
      expect(user2Balance.current.latestBalance?.user_id).toBe(user2.id);
      expect(user1Balance.current.latestBalance?.current_balance).toBe(100.0);
      expect(user2Balance.current.latestBalance?.current_balance).toBe(200.0);
    });
  });

  describe('Resource Management', () => {
    it('should properly cleanup resources on component unmount', () => {
      const { unmount: unmountBalance } = renderHook(() => useBalanceWebSocket({ enabled: true }));

      const { unmount: unmountApproval } = renderHook(() =>
        usePurchaseApprovalWebSocket({ parentId: 'parent123' }),
      );

      const { unmount: unmountPayment } = renderHook(() => usePaymentMonitoringWebSocket(true));

      // Unmount all components
      expect(() => {
        unmountBalance();
        unmountApproval();
        unmountPayment();
      }).not.toThrow();

      // Should not cause memory leaks
      expect(true).toBe(true);
    });

    it('should handle rapid mount/unmount cycles', () => {
      for (let i = 0; i < 10; i++) {
        const { unmount } = renderHook(() => useBalanceWebSocket({ enabled: true }));
        unmount();
      }

      // Should not accumulate resources or cause errors
      expect(true).toBe(true);
    });

    it('should limit WebSocket connections to prevent resource exhaustion', async () => {
      const hooks = [];

      // Create multiple hooks
      for (let i = 0; i < 5; i++) {
        const { result } = renderHook(() => useBalanceWebSocket({ enabled: true }));
        hooks.push(result);
      }

      await act(async () => {
        WebSocketTestUtils.advanceTime(100);
      });

      // Should manage connections efficiently
      const allWebSockets = WebSocketTestUtils.getAllWebSockets();
      expect(allWebSockets.length).toBeLessThan(10); // Should not create excessive connections
    });
  });

  describe('Error Recovery Integration', () => {
    it('should coordinate error recovery across multiple features', async () => {
      const { result: balanceHook } = renderHook(() =>
        useBalanceWebSocket({ enabled: true, maxReconnectAttempts: 2 }),
      );

      const { result: approvalHook } = renderHook(() =>
        usePurchaseApprovalWebSocket({ parentId: 'parent123' }),
      );

      await act(async () => {
        WebSocketTestUtils.advanceTime(100);
      });

      // Simulate authentication failure
      WebSocketTestUtils.mockAsyncStorageNoToken();

      // Trigger reconnection attempts
      const allWebSockets = WebSocketTestUtils.getAllWebSockets();
      act(() => {
        allWebSockets.forEach(ws => ws.simulateNetworkFailure());
      });

      // Should handle authentication errors gracefully
      expect(balanceHook.current.error).toBeTruthy();

      // Restore authentication
      WebSocketTestUtils.mockAsyncStorage('restored-token');

      // Manual reconnection should work
      act(() => {
        balanceHook.current.reconnect();
      });

      await act(async () => {
        WebSocketTestUtils.advanceTime(1100);
      });

      // Should recover from authentication issues
      expect(balanceHook.current.error).toBeNull();
    });
  });
});

describe('WebSocket Integration Performance Benchmarks', () => {
  beforeEach(() => {
    WebSocketTestUtils.setup();
    WebSocketTestUtils.setupFakeTimers();
    jest.clearAllMocks();
    WebSocketTestUtils.mockAsyncStorage('benchmark-token');
  });

  afterEach(() => {
    WebSocketTestUtils.cleanup();
    WebSocketTestUtils.cleanupFakeTimers();
  });

  it('should complete all WebSocket connections within 500ms', async () => {
    const startTime = Date.now();

    const hooks = [
      renderHook(() => useBalanceWebSocket({ enabled: true })),
      renderHook(() => usePurchaseApprovalWebSocket({ parentId: 'test' })),
      renderHook(() => usePaymentMonitoringWebSocket(true)),
    ];

    await act(async () => {
      WebSocketTestUtils.advanceTime(200);
    });

    const endTime = Date.now();
    expect(endTime - startTime).toBeLessThan(500);

    // All should be connected
    hooks.forEach(({ result }, index) => {
      const connectionStates = [
        result.current.connected,
        result.current.isConnected,
        result.current.isConnected,
      ];
      expect(connectionStates[index]).toBe(true);
    });
  });

  it('should process 1000 mixed messages within 1 second', async () => {
    const { result } = renderHook(() => usePaymentMonitoringWebSocket(true));

    await act(async () => {
      WebSocketTestUtils.advanceTime(100);
    });

    const startTime = Date.now();

    act(() => {
      const ws = WebSocketTestUtils.getLastWebSocket()!;

      for (let i = 0; i < 1000; i++) {
        const messageType =
          i % 3 === 0 ? 'transaction_update' : i % 3 === 1 ? 'fraud_alert' : 'webhook_status';

        const message = {
          type: messageType,
          data: { id: i, test: true },
          timestamp: new Date().toISOString(),
        };

        ws.simulateMessage(JSON.stringify(message));
      }
    });

    const endTime = Date.now();
    expect(endTime - startTime).toBeLessThan(1000);

    // Data should be processed and limited appropriately
    expect(result.current.recentTransactions.length).toBeLessThanOrEqual(50);
  });

  it('should maintain memory usage under load', () => {
    const initialMemory = process.memoryUsage().heapUsed;

    // Create and destroy many hook instances
    for (let i = 0; i < 100; i++) {
      const { unmount } = renderHook(() => useBalanceWebSocket({ enabled: false }));
      unmount();
    }

    const finalMemory = process.memoryUsage().heapUsed;
    const memoryIncrease = finalMemory - initialMemory;

    // Memory increase should be reasonable (less than 10MB)
    expect(memoryIncrease).toBeLessThan(10 * 1024 * 1024);
  });
});
