/**
 * Tests for usePaymentMonitoringWebSocket hook
 *
 * Tests cover:
 * - Payment monitoring dashboard WebSocket connections
 * - Real-time metrics and trend data updates
 * - Transaction monitoring with state management
 * - Webhook health monitoring
 * - Fraud alert processing
 * - Dispute tracking and updates
 * - Authentication and reconnection logic
 * - Performance with high-frequency updates
 */

import { renderHook, act, waitFor } from '@testing-library/react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

import {
  usePaymentMonitoringWebSocket,
  useTransactionWebSocket,
  useWebhookMonitoringWebSocket,
} from '@/hooks/usePaymentMonitoringWebSocket';
import WebSocketTestUtils, { WebSocketTestData } from '@/__tests__/utils/websocket-test-utils';

// Mock AsyncStorage
jest.mock('@react-native-async-storage/async-storage', () => ({
  getItem: jest.fn(),
  setItem: jest.fn(),
}));

describe('usePaymentMonitoringWebSocket Hook', () => {
  beforeEach(() => {
    WebSocketTestUtils.setup();
    WebSocketTestUtils.setupFakeTimers();
    jest.clearAllMocks();

    // Mock console methods to avoid test output noise
    jest.spyOn(console, 'log').mockImplementation();
    jest.spyOn(console, 'error').mockImplementation();
    jest.spyOn(console, 'warn').mockImplementation();

    WebSocketTestUtils.mockAsyncStorage('test-auth-token');
  });

  afterEach(() => {
    WebSocketTestUtils.cleanup();
    WebSocketTestUtils.cleanupFakeTimers();
    jest.restoreAllMocks();
  });

  describe('Connection Management', () => {
    it('should initialize with default state when enabled', () => {
      const { result } = renderHook(() => usePaymentMonitoringWebSocket(true));

      expect(result.current.isConnected).toBe(false);
      expect(result.current.error).toBeNull();
      expect(result.current.lastMessage).toBeNull();
      expect(result.current.metrics).toBeNull();
      expect(result.current.trendData).toBeNull();
      expect(result.current.webhookStatus).toEqual([]);
      expect(result.current.recentTransactions).toEqual([]);
      expect(result.current.activeFraudAlerts).toEqual([]);
      expect(result.current.activeDisputes).toEqual([]);
    });

    it('should establish WebSocket connection with authentication', async () => {
      const { result } = renderHook(() => usePaymentMonitoringWebSocket(true));

      await act(async () => {
        WebSocketTestUtils.advanceTime(100);
      });

      const ws = WebSocketTestUtils.getLastWebSocket();
      expect(ws).toBeTruthy();
      expect(ws?.url).toBe('ws://localhost:8000/ws/admin/payments/?token=test-auth-token');
      expect(result.current.isConnected).toBe(true);
    });

    it('should not connect when disabled', () => {
      const { result } = renderHook(() => usePaymentMonitoringWebSocket(false));

      expect(result.current.isConnected).toBe(false);
    });

    it('should handle missing authentication token', async () => {
      WebSocketTestUtils.mockAsyncStorageNoToken();

      const { result } = renderHook(() => usePaymentMonitoringWebSocket(true));

      await act(async () => {
        WebSocketTestUtils.advanceTime(100);
      });

      expect(result.current.isConnected).toBe(false);
      expect(result.current.error).toBe('No authentication token found');
    });

    it('should send subscription message on connection', async () => {
      const { result } = renderHook(() => usePaymentMonitoringWebSocket(true));

      await act(async () => {
        WebSocketTestUtils.advanceTime(100);
      });

      const ws = WebSocketTestUtils.getLastWebSocket()!;
      const sentMessages = ws.getMessageQueue();
      
      expect(sentMessages).toContain(JSON.stringify({
        type: 'subscribe',
        channels: ['metrics', 'transactions', 'webhooks', 'fraud_alerts', 'disputes'],
      }));
    });
  });

  describe('Metrics Updates', () => {
    it('should process metrics update messages', async () => {
      const { result } = renderHook(() => usePaymentMonitoringWebSocket(true));

      await act(async () => {
        WebSocketTestUtils.advanceTime(100);
      });

      const ws = WebSocketTestUtils.getLastWebSocket()!;
      const metricsUpdate = {
        type: 'metrics_update',
        data: {
          metrics: {
            total_revenue: 15000.00,
            successful_transactions: 1250,
            failed_transactions: 35,
            success_rate: 97.3,
            avg_transaction_value: 12.00,
          },
          trend_data: {
            daily_revenue: [120, 135, 148, 162, 155],
            weekly_transactions: [850, 920, 1050, 1250],
          },
        },
        timestamp: new Date().toISOString(),
      };

      act(() => {
        ws.simulateMessage(JSON.stringify(metricsUpdate));
      });

      expect(result.current.metrics).toMatchObject({
        total_revenue: 15000.00,
        successful_transactions: 1250,
        success_rate: 97.3,
      });
      expect(result.current.trendData).toMatchObject({
        daily_revenue: [120, 135, 148, 162, 155],
      });
    });

    it('should merge partial metrics updates', async () => {
      const { result } = renderHook(() => usePaymentMonitoringWebSocket(true));

      await act(async () => {
        WebSocketTestUtils.advanceTime(100);
      });

      // Set initial metrics using the provided setter
      act(() => {
        result.current.setMetrics({
          total_revenue: 10000.00,
          successful_transactions: 1000,
          failed_transactions: 20,
          success_rate: 98.0,
          avg_transaction_value: 10.00,
        });
      });

      const ws = WebSocketTestUtils.getLastWebSocket()!;
      const partialUpdate = {
        type: 'metrics_update',
        data: {
          metrics: {
            total_revenue: 15000.00,
            successful_transactions: 1250,
          },
        },
        timestamp: new Date().toISOString(),
      };

      act(() => {
        ws.simulateMessage(JSON.stringify(partialUpdate));
      });

      expect(result.current.metrics).toMatchObject({
        total_revenue: 15000.00,
        successful_transactions: 1250,
        failed_transactions: 20, // Should retain original value
        success_rate: 98.0, // Should retain original value
      });
    });
  });

  describe('Transaction Updates', () => {
    it('should process new transaction creation', async () => {
      const { result } = renderHook(() => usePaymentMonitoringWebSocket(true));

      await act(async () => {
        WebSocketTestUtils.advanceTime(100);
      });

      const ws = WebSocketTestUtils.getLastWebSocket()!;
      const transactionUpdate = {
        type: 'transaction_update',
        data: {
          action: 'created',
          transaction: {
            id: 'txn_123',
            amount: 25.00,
            currency: 'EUR',
            status: 'pending',
            created_at: new Date().toISOString(),
            customer_email: 'test@example.com',
          },
        },
        timestamp: new Date().toISOString(),
      };

      act(() => {
        ws.simulateMessage(JSON.stringify(transactionUpdate));
      });

      expect(result.current.recentTransactions).toHaveLength(1);
      expect(result.current.recentTransactions[0]).toMatchObject({
        id: 'txn_123',
        amount: 25.00,
        status: 'pending',
      });
    });

    it('should update existing transactions', async () => {
      const { result } = renderHook(() => usePaymentMonitoringWebSocket(true));

      await act(async () => {
        WebSocketTestUtils.advanceTime(100);
      });

      // Set initial transaction
      const initialTransaction = {
        id: 'txn_123',
        amount: 25.00,
        currency: 'EUR',
        status: 'pending',
        created_at: new Date().toISOString(),
      };

      act(() => {
        result.current.setRecentTransactions([initialTransaction]);
      });

      const ws = WebSocketTestUtils.getLastWebSocket()!;
      const updateMessage = {
        type: 'transaction_update',
        data: {
          action: 'status_changed',
          transaction: {
            ...initialTransaction,
            status: 'completed',
          },
        },
        timestamp: new Date().toISOString(),
      };

      act(() => {
        ws.simulateMessage(JSON.stringify(updateMessage));
      });

      expect(result.current.recentTransactions).toHaveLength(1);
      expect(result.current.recentTransactions[0].status).toBe('completed');
    });

    it('should limit recent transactions to 50', async () => {
      const { result } = renderHook(() => usePaymentMonitoringWebSocket(true));

      await act(async () => {
        WebSocketTestUtils.advanceTime(100);
      });

      const ws = WebSocketTestUtils.getLastWebSocket()!;

      // Add 52 transactions
      act(() => {
        for (let i = 0; i < 52; i++) {
          const transactionUpdate = {
            type: 'transaction_update',
            data: {
              action: 'created',
              transaction: {
                id: `txn_${i}`,
                amount: 25.00,
                currency: 'EUR',
                status: 'completed',
                created_at: new Date().toISOString(),
              },
            },
            timestamp: new Date().toISOString(),
          };
          ws.simulateMessage(JSON.stringify(transactionUpdate));
        }
      });

      expect(result.current.recentTransactions).toHaveLength(50);
      expect(result.current.recentTransactions[0].id).toBe('txn_51'); // Most recent
    });
  });

  describe('Webhook Status Updates', () => {
    it('should process webhook status updates', async () => {
      const { result } = renderHook(() => usePaymentMonitoringWebSocket(true));

      await act(async () => {
        WebSocketTestUtils.advanceTime(100);
      });

      const ws = WebSocketTestUtils.getLastWebSocket()!;
      const webhookUpdate = {
        type: 'webhook_status',
        data: {
          webhook_status: {
            endpoint_url: 'https://example.com/webhook',
            status: 'healthy',
            last_success: new Date().toISOString(),
            success_rate: 98.5,
            avg_response_time: 125,
            last_failure: null,
            failure_reason: null,
          },
        },
        timestamp: new Date().toISOString(),
      };

      act(() => {
        ws.simulateMessage(JSON.stringify(webhookUpdate));
      });

      expect(result.current.webhookStatus).toHaveLength(1);
      expect(result.current.webhookStatus[0]).toMatchObject({
        endpoint_url: 'https://example.com/webhook',
        status: 'healthy',
        success_rate: 98.5,
      });
    });

    it('should update existing webhook status', async () => {
      const { result } = renderHook(() => usePaymentMonitoringWebSocket(true));

      await act(async () => {
        WebSocketTestUtils.advanceTime(100);
      });

      const initialWebhook = {
        endpoint_url: 'https://example.com/webhook',
        status: 'healthy',
        success_rate: 98.5,
      };

      act(() => {
        result.current.setWebhookStatus([initialWebhook]);
      });

      const ws = WebSocketTestUtils.getLastWebSocket()!;
      const updateMessage = {
        type: 'webhook_status',
        data: {
          webhook_status: {
            endpoint_url: 'https://example.com/webhook',
            status: 'degraded',
            success_rate: 85.2,
            last_failure: new Date().toISOString(),
          },
        },
        timestamp: new Date().toISOString(),
      };

      act(() => {
        ws.simulateMessage(JSON.stringify(updateMessage));
      });

      expect(result.current.webhookStatus).toHaveLength(1);
      expect(result.current.webhookStatus[0].status).toBe('degraded');
      expect(result.current.webhookStatus[0].success_rate).toBe(85.2);
    });
  });

  describe('Fraud Alert Processing', () => {
    it('should process new fraud alerts', async () => {
      const { result } = renderHook(() => usePaymentMonitoringWebSocket(true));

      await act(async () => {
        WebSocketTestUtils.advanceTime(100);
      });

      const ws = WebSocketTestUtils.getLastWebSocket()!;
      const fraudAlert = {
        type: 'fraud_alert',
        data: {
          action: 'created',
          alert: {
            id: 'fraud_001',
            severity: 'high',
            status: 'active',
            description: 'Multiple failed payment attempts detected',
            transaction_id: 'txn_suspicious',
            risk_score: 85,
            created_at: new Date().toISOString(),
          },
        },
        timestamp: new Date().toISOString(),
      };

      act(() => {
        ws.simulateMessage(JSON.stringify(fraudAlert));
      });

      expect(result.current.activeFraudAlerts).toHaveLength(1);
      expect(result.current.activeFraudAlerts[0]).toMatchObject({
        id: 'fraud_001',
        severity: 'high',
        status: 'active',
        risk_score: 85,
      });
    });

    it('should update existing fraud alerts', async () => {
      const { result } = renderHook(() => usePaymentMonitoringWebSocket(true));

      await act(async () => {
        WebSocketTestUtils.advanceTime(100);
      });

      const initialAlert = {
        id: 'fraud_001',
        severity: 'high',
        status: 'active',
        description: 'Suspicious activity detected',
      };

      act(() => {
        result.current.setActiveFraudAlerts([initialAlert]);
      });

      const ws = WebSocketTestUtils.getLastWebSocket()!;
      const updateMessage = {
        type: 'fraud_alert',
        data: {
          action: 'updated',
          alert: {
            ...initialAlert,
            status: 'investigating',
            investigation_notes: 'Under review by security team',
          },
        },
        timestamp: new Date().toISOString(),
      };

      act(() => {
        ws.simulateMessage(JSON.stringify(updateMessage));
      });

      expect(result.current.activeFraudAlerts).toHaveLength(1);
      expect(result.current.activeFraudAlerts[0].status).toBe('investigating');
    });

    it('should remove resolved fraud alerts', async () => {
      const { result } = renderHook(() => usePaymentMonitoringWebSocket(true));

      await act(async () => {
        WebSocketTestUtils.advanceTime(100);
      });

      const initialAlert = {
        id: 'fraud_001',
        severity: 'medium',
        status: 'active',
      };

      act(() => {
        result.current.setActiveFraudAlerts([initialAlert]);
      });

      const ws = WebSocketTestUtils.getLastWebSocket()!;
      const resolvedMessage = {
        type: 'fraud_alert',
        data: {
          action: 'resolved',
          alert: {
            ...initialAlert,
            status: 'resolved',
          },
        },
        timestamp: new Date().toISOString(),
      };

      act(() => {
        ws.simulateMessage(JSON.stringify(resolvedMessage));
      });

      expect(result.current.activeFraudAlerts).toHaveLength(0);
    });

    it('should filter alerts to keep only active and investigating', async () => {
      const { result } = renderHook(() => usePaymentMonitoringWebSocket(true));

      await act(async () => {
        WebSocketTestUtils.advanceTime(100);
      });

      const ws = WebSocketTestUtils.getLastWebSocket()!;

      // Add multiple alerts with different statuses
      const alerts = [
        { id: 'fraud_001', status: 'active' },
        { id: 'fraud_002', status: 'investigating' },
        { id: 'fraud_003', status: 'resolved' },
        { id: 'fraud_004', status: 'false_positive' },
      ];

      act(() => {
        alerts.forEach(alert => {
          const message = {
            type: 'fraud_alert',
            data: {
              action: 'created',
              alert: {
                ...alert,
                severity: 'medium',
                description: 'Test alert',
                created_at: new Date().toISOString(),
              },
            },
            timestamp: new Date().toISOString(),
          };
          ws.simulateMessage(JSON.stringify(message));
        });
      });

      // Should only keep active and investigating alerts
      expect(result.current.activeFraudAlerts).toHaveLength(2);
      const alertIds = result.current.activeFraudAlerts.map(a => a.id);
      expect(alertIds).toContain('fraud_001');
      expect(alertIds).toContain('fraud_002');
    });
  });

  describe('Dispute Management', () => {
    it('should process new disputes', async () => {
      const { result } = renderHook(() => usePaymentMonitoringWebSocket(true));

      await act(async () => {
        WebSocketTestUtils.advanceTime(100);
      });

      const ws = WebSocketTestUtils.getLastWebSocket()!;
      const disputeMessage = {
        type: 'dispute_update',
        data: {
          action: 'created',
          dispute: {
            id: 'dispute_001',
            transaction_id: 'txn_disputed',
            amount: 50.00,
            currency: 'EUR',
            reason: 'unauthorized',
            status: 'open',
            created_at: new Date().toISOString(),
            evidence_due_by: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
          },
        },
        timestamp: new Date().toISOString(),
      };

      act(() => {
        ws.simulateMessage(JSON.stringify(disputeMessage));
      });

      expect(result.current.activeDisputes).toHaveLength(1);
      expect(result.current.activeDisputes[0]).toMatchObject({
        id: 'dispute_001',
        status: 'open',
        reason: 'unauthorized',
        amount: 50.00,
      });
    });

    it('should update existing disputes', async () => {
      const { result } = renderHook(() => usePaymentMonitoringWebSocket(true));

      await act(async () => {
        WebSocketTestUtils.advanceTime(100);
      });

      const initialDispute = {
        id: 'dispute_001',
        status: 'open',
        reason: 'unauthorized',
        amount: 50.00,
      };

      act(() => {
        result.current.setActiveDisputes([initialDispute]);
      });

      const ws = WebSocketTestUtils.getLastWebSocket()!;
      const updateMessage = {
        type: 'dispute_update',
        data: {
          action: 'evidence_required',
          dispute: {
            ...initialDispute,
            status: 'evidence_required',
            evidence_due_by: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000).toISOString(),
          },
        },
        timestamp: new Date().toISOString(),
      };

      act(() => {
        ws.simulateMessage(JSON.stringify(updateMessage));
      });

      expect(result.current.activeDisputes).toHaveLength(1);
      expect(result.current.activeDisputes[0].status).toBe('evidence_required');
    });

    it('should handle resolved disputes', async () => {
      const { result } = renderHook(() => usePaymentMonitoringWebSocket(true));

      await act(async () => {
        WebSocketTestUtils.advanceTime(100);
      });

      const initialDispute = {
        id: 'dispute_001',
        status: 'open',
        amount: 50.00,
      };

      act(() => {
        result.current.setActiveDisputes([initialDispute]);
      });

      const ws = WebSocketTestUtils.getLastWebSocket()!;
      const resolvedMessage = {
        type: 'dispute_update',
        data: {
          action: 'resolved',
          dispute: {
            ...initialDispute,
            status: 'won',
            resolved_at: new Date().toISOString(),
          },
        },
        timestamp: new Date().toISOString(),
      };

      act(() => {
        ws.simulateMessage(JSON.stringify(resolvedMessage));
      });

      // Resolved disputes should still be kept in the list but marked as resolved
      expect(result.current.activeDisputes).toHaveLength(1);
      expect(result.current.activeDisputes[0].status).toBe('won');
    });
  });

  describe('Error Handling and Reconnection', () => {
    it('should implement exponential backoff reconnection', async () => {
      const { result } = renderHook(() => usePaymentMonitoringWebSocket(true));

      await act(async () => {
        WebSocketTestUtils.advanceTime(100);
      });

      expect(result.current.isConnected).toBe(true);

      const ws = WebSocketTestUtils.getLastWebSocket()!;

      // Simulate connection failure
      act(() => {
        ws.simulateNetworkFailure();
      });

      expect(result.current.isConnected).toBe(false);

      // Wait for first reconnection attempt (1 second)
      await act(async () => {
        WebSocketTestUtils.advanceTime(1100);
      });

      // Should have attempted reconnection
      expect(WebSocketTestUtils.getAllWebSockets().length).toBeGreaterThan(1);
    });

    it('should handle malformed messages gracefully', async () => {
      const { result } = renderHook(() => usePaymentMonitoringWebSocket(true));

      await act(async () => {
        WebSocketTestUtils.advanceTime(100);
      });

      const ws = WebSocketTestUtils.getLastWebSocket()!;
      const consoleSpy = jest.spyOn(console, 'error');

      act(() => {
        ws.simulateMessage('invalid json {');
      });

      expect(result.current.isConnected).toBe(true); // Should remain connected
      expect(consoleSpy).toHaveBeenCalledWith(
        'Error parsing payment monitoring WebSocket message:',
        expect.any(Error)
      );
    });

    it('should handle unknown message types gracefully', async () => {
      const { result } = renderHook(() => usePaymentMonitoringWebSocket(true));

      await act(async () => {
        WebSocketTestUtils.advanceTime(100);
      });

      const ws = WebSocketTestUtils.getLastWebSocket()!;
      const consoleSpy = jest.spyOn(console, 'warn');

      act(() => {
        ws.simulateMessage(JSON.stringify({
          type: 'unknown_message_type',
          data: {},
          timestamp: new Date().toISOString(),
        }));
      });

      expect(consoleSpy).toHaveBeenCalledWith(
        'Unknown payment monitoring WebSocket message type:',
        'unknown_message_type'
      );
    });
  });

  describe('Manual Connection Control', () => {
    it('should allow manual connection and disconnection', async () => {
      const { result } = renderHook(() => usePaymentMonitoringWebSocket(false));

      expect(result.current.isConnected).toBe(false);

      // Manual connect
      await act(async () => {
        result.current.connect();
        WebSocketTestUtils.advanceTime(100);
      });

      expect(result.current.isConnected).toBe(true);

      // Manual disconnect
      act(() => {
        result.current.disconnect();
      });

      expect(result.current.isConnected).toBe(false);
    });

    it('should allow manual message sending', async () => {
      const { result } = renderHook(() => usePaymentMonitoringWebSocket(true));

      await act(async () => {
        WebSocketTestUtils.advanceTime(100);
      });

      const ws = WebSocketTestUtils.getLastWebSocket()!;
      const testMessage = { type: 'test', data: 'hello' };

      act(() => {
        result.current.sendMessage(testMessage);
      });

      expect(ws.getMessageQueue()).toContain(JSON.stringify(testMessage));
    });
  });

  describe('Performance with High-Frequency Updates', () => {
    it('should handle rapid message processing efficiently', async () => {
      const { result } = renderHook(() => usePaymentMonitoringWebSocket(true));

      await act(async () => {
        WebSocketTestUtils.advanceTime(100);
      });

      const ws = WebSocketTestUtils.getLastWebSocket()!;
      const startTime = Date.now();

      // Process 100 transaction updates rapidly
      act(() => {
        for (let i = 0; i < 100; i++) {
          const message = {
            type: 'transaction_update',
            data: {
              action: 'created',
              transaction: {
                id: `txn_${i}`,
                amount: 25.00,
                currency: 'EUR',
                status: 'completed',
                created_at: new Date().toISOString(),
              },
            },
            timestamp: new Date().toISOString(),
          };
          ws.simulateMessage(JSON.stringify(message));
        }
      });

      const endTime = Date.now();
      expect(endTime - startTime).toBeLessThan(500); // Should process quickly

      // Should be limited to 50 transactions
      expect(result.current.recentTransactions).toHaveLength(50);
    });
  });

  describe('Data Setters and Initial Loading', () => {
    it('should provide setters for initial data loading', () => {
      const { result } = renderHook(() => usePaymentMonitoringWebSocket(true));

      const mockMetrics = {
        total_revenue: 10000,
        successful_transactions: 800,
        failed_transactions: 20,
        success_rate: 97.5,
        avg_transaction_value: 12.5,
      };

      act(() => {
        result.current.setMetrics(mockMetrics);
      });

      expect(result.current.metrics).toEqual(mockMetrics);
    });

    it('should allow setting initial trend data', () => {
      const { result } = renderHook(() => usePaymentMonitoringWebSocket(true));

      const mockTrendData = {
        daily_revenue: [100, 120, 110, 130, 125],
        hourly_transactions: [10, 15, 12, 18, 20],
      };

      act(() => {
        result.current.setTrendData(mockTrendData);
      });

      expect(result.current.trendData).toEqual(mockTrendData);
    });
  });
});

describe('useTransactionWebSocket Hook (Enhanced)', () => {
  beforeEach(() => {
    WebSocketTestUtils.setup();
    WebSocketTestUtils.setupFakeTimers();
    jest.clearAllMocks();

    WebSocketTestUtils.mockAsyncStorage('test-auth-token');
  });

  afterEach(() => {
    WebSocketTestUtils.cleanup();
    WebSocketTestUtils.cleanupFakeTimers();
  });

  it('should connect to transaction-specific WebSocket', async () => {
    const { result } = renderHook(() => useTransactionWebSocket(true));

    await act(async () => {
      WebSocketTestUtils.advanceTime(100);
    });

    const ws = WebSocketTestUtils.getLastWebSocket();
    expect(ws?.url).toBe('ws://localhost:8000/ws/admin/transactions/?token=test-auth-token');
    expect(result.current.isConnected).toBe(true);
  });

  it('should process transaction updates and maintain history', async () => {
    const { result } = renderHook(() => useTransactionWebSocket(true));

    await act(async () => {
      WebSocketTestUtils.advanceTime(100);
    });

    const ws = WebSocketTestUtils.getLastWebSocket()!;
    
    // Send multiple transaction updates
    act(() => {
      for (let i = 0; i < 5; i++) {
        const update = {
          type: 'transaction_update',
          data: {
            action: 'status_changed',
            transaction: {
              id: `txn_${i}`,
              status: 'completed',
              amount: 25.00 * (i + 1),
            },
          },
          timestamp: new Date().toISOString(),
        };
        ws.simulateMessage(JSON.stringify(update));
      }
    });

    expect(result.current.transactionUpdates).toHaveLength(5);
    expect(result.current.transactionUpdates[0].transaction.id).toBe('txn_4'); // Most recent first
  });

  it('should limit transaction updates to 100', async () => {
    const { result } = renderHook(() => useTransactionWebSocket(true));

    await act(async () => {
      WebSocketTestUtils.advanceTime(100);
    });

    const ws = WebSocketTestUtils.getLastWebSocket()!;

    act(() => {
      for (let i = 0; i < 105; i++) {
        const update = {
          type: 'transaction_update',
          data: {
            action: 'created',
            transaction: { id: `txn_${i}`, amount: 25.00 },
          },
          timestamp: new Date().toISOString(),
        };
        ws.simulateMessage(JSON.stringify(update));
      }
    });

    expect(result.current.transactionUpdates).toHaveLength(100);
  });

  it('should clear transaction updates', () => {
    const { result } = renderHook(() => useTransactionWebSocket(true));

    act(() => {
      result.current.clearUpdates();
    });

    expect(result.current.transactionUpdates).toHaveLength(0);
  });
});

describe('useWebhookMonitoringWebSocket Hook', () => {
  beforeEach(() => {
    WebSocketTestUtils.setup();
    WebSocketTestUtils.setupFakeTimers();
    jest.clearAllMocks();

    WebSocketTestUtils.mockAsyncStorage('test-auth-token');
  });

  afterEach(() => {
    WebSocketTestUtils.cleanup();
    WebSocketTestUtils.cleanupFakeTimers();
  });

  it('should connect to webhook monitoring WebSocket', async () => {
    const { result } = renderHook(() => useWebhookMonitoringWebSocket(true));

    await act(async () => {
      WebSocketTestUtils.advanceTime(100);
    });

    const ws = WebSocketTestUtils.getLastWebSocket();
    expect(ws?.url).toBe('ws://localhost:8000/ws/admin/webhooks/?token=test-auth-token');
    expect(result.current.isConnected).toBe(true);
  });

  it('should process webhook status updates', async () => {
    const { result } = renderHook(() => useWebhookMonitoringWebSocket(true));

    await act(async () => {
      WebSocketTestUtils.advanceTime(100);
    });

    const ws = WebSocketTestUtils.getLastWebSocket()!;
    const statusUpdate = {
      type: 'webhook_status',
      data: {
        webhook_status: {
          endpoint_url: 'https://api.example.com/webhook',
          status: 'healthy',
          last_success: new Date().toISOString(),
          success_rate: 99.5,
          avg_response_time: 100,
        },
      },
      timestamp: new Date().toISOString(),
    };

    act(() => {
      ws.simulateMessage(JSON.stringify(statusUpdate));
    });

    expect(result.current.webhookStatus).toHaveLength(1);
    expect(result.current.webhookStatus[0].endpoint_url).toBe('https://api.example.com/webhook');
    expect(result.current.webhookStatus[0].status).toBe('healthy');
  });

  it('should process webhook events', async () => {
    const { result } = renderHook(() => useWebhookMonitoringWebSocket(true));

    await act(async () => {
      WebSocketTestUtils.advanceTime(100);
    });

    const ws = WebSocketTestUtils.getLastWebSocket()!;

    act(() => {
      for (let i = 0; i < 10; i++) {
        const event = {
          type: 'webhook_event',
          data: {
            event_id: `evt_${i}`,
            endpoint_url: 'https://api.example.com/webhook',
            event_type: 'payment.completed',
            status: 'delivered',
            response_time: 120 + i * 10,
            timestamp: new Date().toISOString(),
          },
        };
        ws.simulateMessage(JSON.stringify(event));
      }
    });

    expect(result.current.recentEvents).toHaveLength(10);
  });

  it('should limit webhook events to 50', async () => {
    const { result } = renderHook(() => useWebhookMonitoringWebSocket(true));

    await act(async () => {
      WebSocketTestUtils.advanceTime(100);
    });

    const ws = WebSocketTestUtils.getLastWebSocket()!;

    act(() => {
      for (let i = 0; i < 55; i++) {
        const event = {
          type: 'webhook_event',
          data: { event_id: `evt_${i}`, timestamp: new Date().toISOString() },
        };
        ws.simulateMessage(JSON.stringify(event));
      }
    });

    expect(result.current.recentEvents).toHaveLength(50);
  });

  it('should provide clearEvents function', () => {
    const { result } = renderHook(() => useWebhookMonitoringWebSocket(true));

    act(() => {
      result.current.clearEvents();
    });

    expect(result.current.recentEvents).toHaveLength(0);
  });
});