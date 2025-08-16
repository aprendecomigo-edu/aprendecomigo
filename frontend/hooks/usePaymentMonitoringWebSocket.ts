/**
 * WebSocket hooks for real-time payment monitoring updates.
 *
 * Provides real-time updates for dashboard metrics, transaction status changes,
 * webhook health, fraud alerts, and dispute notifications.
 */

import AsyncStorage from '@react-native-async-storage/async-storage';
import { useEffect, useState, useCallback, useRef } from 'react';

import type {
  PaymentWebSocketMessage,
  PaymentMetrics,
  PaymentTrendData,
  TransactionMonitoring,
  WebhookStatus,
  FraudAlert,
  DisputeRecord,
  MetricsUpdate,
  TransactionUpdate,
  WebhookStatusUpdate,
  FraudAlertUpdate,
  DisputeUpdate,
} from '@/types/paymentMonitoring';

/**
 * Main payment monitoring WebSocket hook for dashboard real-time updates.
 */
export function usePaymentMonitoringWebSocket(enabled: boolean = true) {
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastMessage, setLastMessage] = useState<PaymentWebSocketMessage | null>(null);

  // Data state
  const [metrics, setMetrics] = useState<PaymentMetrics | null>(null);
  const [trendData, setTrendData] = useState<PaymentTrendData | null>(null);
  const [webhookStatus, setWebhookStatus] = useState<WebhookStatus[]>([]);
  const [recentTransactions, setRecentTransactions] = useState<TransactionMonitoring[]>([]);
  const [activeFraudAlerts, setActiveFraudAlerts] = useState<FraudAlert[]>([]);
  const [activeDisputes, setActiveDisputes] = useState<DisputeRecord[]>([]);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 5;

  const handleWebSocketMessage = useCallback((message: PaymentWebSocketMessage) => {
    if (__DEV__) {
      console.log('Payment monitoring WebSocket message received:', message);
    }
    setLastMessage(message);

    switch (message.type) {
      case 'metrics_update':
        const metricsUpdate = message.data as MetricsUpdate;
        if (metricsUpdate.metrics) {
          setMetrics(current => (current ? { ...current, ...metricsUpdate.metrics } : null));
        }
        if (metricsUpdate.trend_data) {
          setTrendData(current => (current ? { ...current, ...metricsUpdate.trend_data } : null));
        }
        break;

      case 'transaction_update':
        const transactionUpdate = message.data as TransactionUpdate;
        setRecentTransactions(current => {
          const updated = [...current];
          const existingIndex = updated.findIndex(t => t.id === transactionUpdate.transaction.id);

          if (transactionUpdate.action === 'created') {
            if (existingIndex === -1) {
              updated.unshift(transactionUpdate.transaction);
              // Keep only the most recent 50 transactions
              return updated.slice(0, 50);
            }
          } else if (
            transactionUpdate.action === 'updated' ||
            transactionUpdate.action === 'status_changed'
          ) {
            if (existingIndex !== -1) {
              updated[existingIndex] = transactionUpdate.transaction;
            }
          }
          return updated;
        });
        break;

      case 'webhook_status':
        const webhookUpdate = message.data as WebhookStatusUpdate;
        setWebhookStatus(current => {
          const updated = [...current];
          const existingIndex = updated.findIndex(
            w => w.endpoint_url === webhookUpdate.webhook_status.endpoint_url,
          );

          if (existingIndex !== -1) {
            updated[existingIndex] = webhookUpdate.webhook_status;
          } else {
            updated.push(webhookUpdate.webhook_status);
          }
          return updated;
        });
        break;

      case 'fraud_alert':
        const fraudUpdate = message.data as FraudAlertUpdate;
        setActiveFraudAlerts(current => {
          const updated = [...current];
          const existingIndex = updated.findIndex(f => f.id === fraudUpdate.alert.id);

          if (fraudUpdate.action === 'created') {
            if (existingIndex === -1) {
              updated.unshift(fraudUpdate.alert);
              // Keep only active alerts
              return updated.filter(
                alert => alert.status === 'active' || alert.status === 'investigating',
              );
            }
          } else if (fraudUpdate.action === 'updated') {
            if (existingIndex !== -1) {
              updated[existingIndex] = fraudUpdate.alert;
            }
          } else if (fraudUpdate.action === 'resolved') {
            if (existingIndex !== -1) {
              updated.splice(existingIndex, 1);
            }
          }
          return updated;
        });
        break;

      case 'dispute_update':
        const disputeUpdate = message.data as DisputeUpdate;
        setActiveDisputes(current => {
          const updated = [...current];
          const existingIndex = updated.findIndex(d => d.id === disputeUpdate.dispute.id);

          if (disputeUpdate.action === 'created') {
            if (existingIndex === -1) {
              updated.unshift(disputeUpdate.dispute);
            }
          } else if (
            disputeUpdate.action === 'updated' ||
            disputeUpdate.action === 'evidence_required'
          ) {
            if (existingIndex !== -1) {
              updated[existingIndex] = disputeUpdate.dispute;
            }
          } else if (disputeUpdate.action === 'resolved') {
            if (existingIndex !== -1) {
              const dispute = disputeUpdate.dispute;
              // Keep resolved disputes but mark them as resolved
              updated[existingIndex] = dispute;
            }
          }
          return updated;
        });
        break;

      default:
        if (__DEV__) {
          console.warn('Unknown payment monitoring WebSocket message type:', message.type);
        }
    }
  }, []);

  const connect = useCallback(async () => {
    if (!enabled) {
      if (__DEV__) {
        console.log('Payment monitoring WebSocket disabled');
      }
      return;
    }

    try {
      // Get auth token for WebSocket connection
      const token = await AsyncStorage.getItem('auth_token');
      if (!token) {
        setError('No authentication token found');
        return;
      }

      // Build WebSocket URL for payment monitoring
      const wsUrl = `ws://localhost:8000/ws/admin/payments/?token=${token}`;
      if (__DEV__) {
        console.log('Connecting to payment monitoring WebSocket:', wsUrl);
      }

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        if (__DEV__) {
          console.log('Payment monitoring WebSocket connected');
        }
        setIsConnected(true);
        setError(null);
        reconnectAttemptsRef.current = 0;

        // Subscribe to real-time updates
        ws.send(
          JSON.stringify({
            type: 'subscribe',
            channels: ['metrics', 'transactions', 'webhooks', 'fraud_alerts', 'disputes'],
          }),
        );
      };

      ws.onmessage = event => {
        try {
          const message = JSON.parse(event.data) as PaymentWebSocketMessage;
          handleWebSocketMessage(message);
        } catch (err) {
          console.error('Error parsing payment monitoring WebSocket message:', err);
        }
      };

      ws.onclose = event => {
        if (__DEV__) {
          console.log('Payment monitoring WebSocket disconnected:', event.code, event.reason);
        }
        setIsConnected(false);
        wsRef.current = null;

        // Attempt to reconnect if not a normal closure
        if (enabled && event.code !== 1000 && reconnectAttemptsRef.current < maxReconnectAttempts) {
          const timeout = Math.pow(2, reconnectAttemptsRef.current) * 1000; // Exponential backoff
          if (__DEV__) {
            console.log(
              `Reconnecting payment monitoring WebSocket in ${timeout}ms (attempt ${
                reconnectAttemptsRef.current + 1
              })`,
            );
          }

          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttemptsRef.current++;
            connect();
          }, timeout);
        }
      };

      ws.onerror = event => {
        console.error('Payment monitoring WebSocket error:', event);
        setError('WebSocket connection error');
      };
    } catch (err) {
      console.error('Error creating payment monitoring WebSocket connection:', err);
      setError('Failed to create WebSocket connection');
    }
  }, [enabled, handleWebSocketMessage]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close(1000, 'User disconnected');
      wsRef.current = null;
    }

    setIsConnected(false);
    reconnectAttemptsRef.current = 0;
  }, []);

  const sendMessage = useCallback(
    (message: any) => {
      if (wsRef.current && isConnected) {
        try {
          wsRef.current.send(JSON.stringify(message));
          if (__DEV__) {
            console.log('Payment monitoring WebSocket message sent:', message);
          }
        } catch (err) {
          console.error('Error sending payment monitoring WebSocket message:', err);
        }
      } else {
        if (__DEV__) {
          console.warn('Payment monitoring WebSocket not connected, cannot send message');
        }
      }
    },
    [isConnected],
  );

  // Initialize connection
  useEffect(() => {
    if (enabled) {
      connect();
    } else {
      disconnect();
    }

    return () => {
      disconnect();
    };
  }, [enabled, connect, disconnect]);

  return {
    // Connection state
    isConnected,
    error,
    lastMessage,

    // Data
    metrics,
    trendData,
    webhookStatus,
    recentTransactions,
    activeFraudAlerts,
    activeDisputes,

    // Actions
    connect,
    disconnect,
    sendMessage,

    // Data setters for initial data loading
    setMetrics,
    setTrendData,
    setWebhookStatus,
    setRecentTransactions,
    setActiveFraudAlerts,
    setActiveDisputes,
  };
}

/**
 * WebSocket hook specifically for transaction monitoring updates.
 */
export function useTransactionWebSocket(enabled: boolean = true) {
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [transactionUpdates, setTransactionUpdates] = useState<TransactionUpdate[]>([]);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 5;

  const handleTransactionUpdate = useCallback((update: TransactionUpdate) => {
    if (__DEV__) {
      console.log('Transaction update received:', update);
    }
    setTransactionUpdates(current => [update, ...current.slice(0, 99)]); // Keep last 100 updates
  }, []);

  const connect = useCallback(async () => {
    if (!enabled) return;

    try {
      const token = await AsyncStorage.getItem('auth_token');
      if (!token) {
        setError('No authentication token found');
        return;
      }

      const wsUrl = `ws://localhost:8000/ws/admin/transactions/?token=${token}`;
      if (__DEV__) {
        console.log('Connecting to transaction monitoring WebSocket:', wsUrl);
      }

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        if (__DEV__) {
          console.log('Transaction monitoring WebSocket connected');
        }
        setIsConnected(true);
        setError(null);
        reconnectAttemptsRef.current = 0;
      };

      ws.onmessage = event => {
        try {
          const message = JSON.parse(event.data) as PaymentWebSocketMessage;
          if (message.type === 'transaction_update') {
            handleTransactionUpdate(message.data as TransactionUpdate);
          }
        } catch (err) {
          console.error('Error parsing transaction WebSocket message:', err);
        }
      };

      ws.onclose = event => {
        if (__DEV__) {
          console.log('Transaction monitoring WebSocket disconnected:', event.code, event.reason);
        }
        setIsConnected(false);
        wsRef.current = null;

        if (enabled && event.code !== 1000 && reconnectAttemptsRef.current < maxReconnectAttempts) {
          const timeout = Math.pow(2, reconnectAttemptsRef.current) * 1000;
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttemptsRef.current++;
            connect();
          }, timeout);
        }
      };

      ws.onerror = event => {
        console.error('Transaction monitoring WebSocket error:', event);
        setError('WebSocket connection error');
      };
    } catch (err) {
      console.error('Error creating transaction monitoring WebSocket connection:', err);
      setError('Failed to create WebSocket connection');
    }
  }, [enabled, handleTransactionUpdate]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close(1000, 'User disconnected');
      wsRef.current = null;
    }

    setIsConnected(false);
    reconnectAttemptsRef.current = 0;
  }, []);

  useEffect(() => {
    if (enabled) {
      connect();
    } else {
      disconnect();
    }

    return () => {
      disconnect();
    };
  }, [enabled, connect, disconnect]);

  return {
    isConnected,
    error,
    transactionUpdates,
    connect,
    disconnect,
    clearUpdates: () => setTransactionUpdates([]),
  };
}

/**
 * WebSocket hook for webhook health monitoring.
 */
export function useWebhookMonitoringWebSocket(enabled: boolean = true) {
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [webhookStatus, setWebhookStatus] = useState<WebhookStatus[]>([]);
  const [recentEvents, setRecentEvents] = useState<any[]>([]);

  const wsRef = useRef<WebSocket | null>(null);

  const connect = useCallback(async () => {
    if (!enabled) return;

    try {
      const token = await AsyncStorage.getItem('auth_token');
      if (!token) {
        setError('No authentication token found');
        return;
      }

      const wsUrl = `ws://localhost:8000/ws/admin/webhooks/?token=${token}`;
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        if (__DEV__) {
          console.log('Webhook monitoring WebSocket connected');
        }
        setIsConnected(true);
        setError(null);
      };

      ws.onmessage = event => {
        try {
          const message = JSON.parse(event.data) as PaymentWebSocketMessage;
          if (message.type === 'webhook_status') {
            const update = message.data as WebhookStatusUpdate;
            setWebhookStatus(current => {
              const updated = [...current];
              const existingIndex = updated.findIndex(
                w => w.endpoint_url === update.webhook_status.endpoint_url,
              );

              if (existingIndex !== -1) {
                updated[existingIndex] = update.webhook_status;
              } else {
                updated.push(update.webhook_status);
              }
              return updated;
            });
          } else if (message.type === 'webhook_event') {
            setRecentEvents(current => [message.data, ...current.slice(0, 49)]); // Keep last 50 events
          }
        } catch (err) {
          console.error('Error parsing webhook monitoring WebSocket message:', err);
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        wsRef.current = null;
      };

      ws.onerror = event => {
        console.error('Webhook monitoring WebSocket error:', event);
        setError('WebSocket connection error');
      };
    } catch (err) {
      console.error('Error creating webhook monitoring WebSocket connection:', err);
      setError('Failed to create WebSocket connection');
    }
  }, [enabled]);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close(1000, 'User disconnected');
      wsRef.current = null;
    }
    setIsConnected(false);
  }, []);

  useEffect(() => {
    if (enabled) {
      connect();
    } else {
      disconnect();
    }

    return () => {
      disconnect();
    };
  }, [enabled, connect, disconnect]);

  return {
    isConnected,
    error,
    webhookStatus,
    recentEvents,
    connect,
    disconnect,
    setWebhookStatus,
    clearEvents: () => setRecentEvents([]),
  };
}
