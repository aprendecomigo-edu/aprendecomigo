/**
 * TypeScript interfaces for payment monitoring and administrative functionality.
 * 
 * These interfaces define the data structures used throughout
 * the payment monitoring dashboards, transaction management, and administrative operations.
 */

// Dashboard metrics types
export interface PaymentMetrics {
  success_rate_24h: number;
  success_rate_7d: number;
  success_rate_30d: number;
  total_transactions_24h: number;
  total_transactions_7d: number;
  total_transactions_30d: number;
  total_revenue_24h: string; // Decimal as string
  total_revenue_7d: string;
  total_revenue_30d: string;
  average_transaction_value: string;
  failed_transactions_24h: number;
  pending_transactions: number;
  active_disputes: number;
  fraud_alerts: number;
}

export interface TimeSeriesDataPoint {
  timestamp: string;
  value: number;
  secondary_value?: number;
}

export interface PaymentTrendData {
  transactions: TimeSeriesDataPoint[];
  revenue: TimeSeriesDataPoint[];
  success_rate: TimeSeriesDataPoint[];
}

// Webhook monitoring types
export interface WebhookStatus {
  endpoint_url: string;
  is_healthy: boolean;
  last_success: string | null;
  last_failure: string | null;
  failure_count_24h: number;
  response_time_avg: number;
  status_code_last: number | null;
  error_message_last: string | null;
}

export interface WebhookEvent {
  id: string;
  event_type: string;
  status: 'pending' | 'succeeded' | 'failed' | 'retrying';
  attempts: number;
  max_attempts: number;
  received_at: string;
  processed_at: string | null;
  response_status: number | null;
  error_message: string | null;
  next_retry_at: string | null;
}

// Transaction monitoring types
export interface TransactionMonitoring {
  id: string;
  payment_intent_id: string;
  customer_email: string;
  amount: string;
  currency: string;
  status: 'requires_payment_method' | 'requires_confirmation' | 'requires_action' | 'processing' | 'succeeded' | 'canceled';
  status_display: string;
  created_at: string;
  updated_at: string;
  metadata: {
    student_name?: string;
    plan_name?: string;
    [key: string]: any;
  };
  failure_reason?: string;
  risk_score?: number;
  payment_method_type?: string;
  last_payment_error?: {
    code: string;
    message: string;
    type: string;
  };
}

export interface PaginatedTransactionMonitoring {
  count: number;
  next: string | null;
  previous: string | null;
  results: TransactionMonitoring[];
}

// Search and filter types
export interface TransactionSearchFilters {
  status?: string;
  payment_method_type?: string;
  customer_email?: string;
  amount_min?: string;
  amount_max?: string;
  date_from?: string;
  date_to?: string;
  search?: string;
  risk_level?: 'low' | 'medium' | 'high';
  has_failures?: boolean;
}

export interface SavedSearch {
  id: string;
  name: string;
  filters: TransactionSearchFilters;
  created_at: string;
  is_default: boolean;
}

// Refund management types
export interface RefundRequest {
  payment_intent_id: string;
  amount?: string; // Optional for partial refunds
  reason: 'duplicate' | 'fraudulent' | 'requested_by_customer' | 'other';
  reason_description?: string;
  notify_customer: boolean;
  reverse_platform_fee?: boolean;
}

export interface RefundResponse {
  success: boolean;
  refund_id?: string;
  amount_refunded?: string;
  status?: 'pending' | 'succeeded' | 'failed' | 'canceled';
  failure_reason?: string;
  estimated_arrival?: string;
  message?: string;
  error_type?: string;
}

export interface RefundRecord {
  id: string;
  refund_id: string;
  payment_intent_id: string;
  amount: string;
  currency: string;
  reason: string;
  reason_description?: string;
  status: 'pending' | 'succeeded' | 'failed' | 'canceled';
  created_at: string;
  updated_at: string;
  failure_reason?: string;
  customer_email: string;
  initiated_by: string;
  estimated_arrival?: string;
}

// Dispute management types
export interface DisputeRecord {
  id: string;
  dispute_id: string;
  payment_intent_id: string;
  amount: string;
  currency: string;
  reason: string;
  status: 'warning_needs_response' | 'warning_under_review' | 'warning_closed' | 'needs_response' | 'under_review' | 'charge_refunded' | 'won' | 'lost';
  status_display: string;
  evidence_due_by: string | null;
  created_at: string;
  updated_at: string;
  customer_email: string;
  evidence_submitted: boolean;
  evidence_details?: {
    customer_communication?: string;
    receipt?: string;
    shipping_documentation?: string;
    uncategorized_text?: string;
    [key: string]: any;
  };
}

export interface DisputeEvidenceRequest {
  dispute_id: string;
  evidence: {
    customer_communication?: string;
    receipt?: string;
    shipping_documentation?: string;
    uncategorized_text?: string;
  };
  submit_immediately?: boolean;
}

export interface DisputeEvidenceResponse {
  success: boolean;
  message: string;
  evidence_status?: 'pending' | 'submitted' | 'too_late';
  error_type?: string;
}

// Fraud detection types
export interface FraudAlert {
  id: string;
  payment_intent_id: string;
  alert_type: 'high_risk_score' | 'velocity_check' | 'card_testing' | 'unusual_pattern' | 'blacklisted_card';
  risk_score: number;
  description: string;
  status: 'active' | 'investigating' | 'resolved' | 'false_positive';
  created_at: string;
  resolved_at: string | null;
  resolved_by: string | null;
  resolution_notes?: string;
  customer_email: string;
  amount: string;
  metadata: {
    ip_address?: string;
    user_agent?: string;
    velocity_count?: number;
    [key: string]: any;
  };
}

export interface FraudAlertAction {
  alert_id: string;
  action: 'investigate' | 'resolve' | 'mark_false_positive' | 'block_customer';
  notes?: string;
}

export interface FraudAlertResponse {
  success: boolean;
  message: string;
  error_type?: string;
}

// Payment retry types
export interface PaymentRetryRecord {
  id: string;
  payment_intent_id: string;
  original_failure_reason: string;
  retry_strategy: 'manual' | 'automatic' | 'scheduled';
  retry_count: number;
  max_retries: number;
  next_retry_at: string | null;
  status: 'pending' | 'retrying' | 'succeeded' | 'failed' | 'abandoned';
  last_attempt_at: string | null;
  created_at: string;
  customer_email: string;
  amount: string;
}

export interface PaymentRetryRequest {
  payment_intent_id: string;
  retry_strategy: 'immediate' | 'scheduled';
  retry_delay_hours?: number;
  max_retries?: number;
  notify_customer?: boolean;
}

export interface PaymentRetryResponse {
  success: boolean;
  retry_id?: string;
  status?: string;
  next_attempt_at?: string;
  message?: string;
  error_type?: string;
}

// Audit trail types
export interface AuditLogEntry {
  id: string;
  action_type: 'refund_initiated' | 'dispute_responded' | 'fraud_investigated' | 'payment_retried' | 'transaction_viewed' | 'webhook_resent';
  resource_type: 'payment_intent' | 'refund' | 'dispute' | 'fraud_alert' | 'webhook_event';
  resource_id: string;
  performed_by: string;
  performed_at: string;
  ip_address: string;
  user_agent: string;
  details: {
    description: string;
    previous_values?: Record<string, any>;
    new_values?: Record<string, any>;
    [key: string]: any;
  };
  risk_level: 'low' | 'medium' | 'high';
}

export interface PaginatedAuditLog {
  count: number;
  next: string | null;
  previous: string | null;
  results: AuditLogEntry[];
}

// Dashboard state types
export interface PaymentMonitoringState {
  activeView: 'dashboard' | 'transactions' | 'refunds' | 'disputes' | 'fraud' | 'webhooks' | 'audit';
  timeRange: 'last_24h' | 'last_7d' | 'last_30d' | 'custom';
  customDateRange?: {
    start_date: string;
    end_date: string;
  };
  refreshInterval: number; // seconds
  autoRefresh: boolean;
}

export interface TransactionManagementState {
  selectedTransactions: string[];
  bulkAction: 'refund' | 'retry' | 'mark_fraudulent' | null;
  searchFilters: TransactionSearchFilters;
  savedSearches: SavedSearch[];
  activeSavedSearch?: string;
  sortBy: 'created_at' | 'amount' | 'status' | 'risk_score';
  sortOrder: 'asc' | 'desc';
}

// Real-time WebSocket types
export interface PaymentWebSocketMessage {
  type: 'metrics_update' | 'transaction_update' | 'webhook_status' | 'fraud_alert' | 'dispute_update';
  data: any;
  timestamp: string;
}

export interface MetricsUpdate {
  metrics: Partial<PaymentMetrics>;
  trend_data?: Partial<PaymentTrendData>;
}

export interface TransactionUpdate {
  transaction: TransactionMonitoring;
  action: 'created' | 'updated' | 'status_changed';
}

export interface WebhookStatusUpdate {
  webhook_status: WebhookStatus;
}

export interface FraudAlertUpdate {
  alert: FraudAlert;
  action: 'created' | 'updated' | 'resolved';
}

export interface DisputeUpdate {
  dispute: DisputeRecord;
  action: 'created' | 'updated' | 'evidence_required' | 'resolved';
}

// Hook return types
export interface UsePaymentMonitoringResult {
  metrics: PaymentMetrics | null;
  trendData: PaymentTrendData | null;
  webhookStatus: WebhookStatus[];
  loading: boolean;
  error: string | null;
  lastUpdated: Date | null;
  refetch: () => Promise<void>;
}

export interface UseTransactionManagementResult {
  transactions: PaginatedTransactionMonitoring | null;
  loading: boolean;
  error: string | null;
  searchFilters: TransactionSearchFilters;
  updateFilters: (filters: Partial<TransactionSearchFilters>) => void;
  refetch: () => Promise<void>;
  selectTransaction: (id: string) => void;
  bulkSelectTransactions: (ids: string[]) => void;
  clearSelection: () => void;
  selectedTransactions: string[];
}

export interface UseRefundManagementResult {
  refunds: RefundRecord[];
  loading: boolean;
  error: string | null;
  processRefund: (request: RefundRequest) => Promise<RefundResponse>;
  refetch: () => Promise<void>;
}

export interface UseDisputeManagementResult {
  disputes: DisputeRecord[];
  loading: boolean;
  error: string | null;
  submitEvidence: (request: DisputeEvidenceRequest) => Promise<DisputeEvidenceResponse>;
  refetch: () => Promise<void>;
}

export interface UseFraudManagementResult {
  alerts: FraudAlert[];
  loading: boolean;
  error: string | null;
  updateAlert: (action: FraudAlertAction) => Promise<FraudAlertResponse>;
  refetch: () => Promise<void>;
}

// Component props types
export interface PaymentMetricsGridProps {
  metrics: PaymentMetrics;
  timeRange: PaymentMonitoringState['timeRange'];
  loading?: boolean;
}

export interface PaymentTrendChartProps {
  data: PaymentTrendData;
  metric: 'transactions' | 'revenue' | 'success_rate';
  timeRange: PaymentMonitoringState['timeRange'];
  height?: number;
}

export interface WebhookStatusIndicatorProps {
  status: WebhookStatus[];
  compact?: boolean;
}

export interface TransactionDetailModalProps {
  transaction: TransactionMonitoring | null;
  isOpen: boolean;
  onClose: () => void;
  onRefund?: (transaction: TransactionMonitoring) => void;
  onRetry?: (transaction: TransactionMonitoring) => void;
}

export interface RefundConfirmationModalProps {
  transaction: TransactionMonitoring | null;
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (request: RefundRequest) => Promise<void>;
  loading?: boolean;
}

export interface BulkActionModalProps {
  selectedTransactions: TransactionMonitoring[];
  action: 'refund' | 'retry' | 'mark_fraudulent';
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (action: string, options: any) => Promise<void>;
  loading?: boolean;
}

// Error types
export interface PaymentMonitoringError {
  code: string;
  message: string;
  field?: string;
  context?: Record<string, any>;
}

export interface PaymentMonitoringValidationError {
  field: string;
  message: string;
  code: string;
}

// Authorization types
export interface AdminPermissions {
  can_view_transactions: boolean;
  can_process_refunds: boolean;
  can_manage_disputes: boolean;
  can_investigate_fraud: boolean;
  can_retry_payments: boolean;
  can_view_audit_log: boolean;
  can_manage_webhooks: boolean;
  requires_two_factor: boolean;
}

export interface TwoFactorAuthState {
  isRequired: boolean;
  isAuthenticated: boolean;
  expiresAt: Date | null;
  challenge: string | null;
}