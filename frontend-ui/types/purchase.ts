/**
 * TypeScript interfaces for purchase-related functionality.
 * 
 * These interfaces define the data structures used throughout
 * the purchase flow, from pricing plans to payment processing.
 */

export interface PricingPlan {
  id: number;
  name: string;
  description: string;
  plan_type: 'package' | 'subscription';
  plan_type_display: string;
  hours_included: string; // Decimal as string
  price_eur: string; // Decimal as string
  price_per_hour: string | null; // Calculated field
  validity_days: number | null;
  is_active: boolean;
  display_order: number;
}

export interface StudentInfo {
  name: string;
  email: string;
}

export interface PurchaseInitiationRequest {
  plan_id: number;
  student_info: StudentInfo;
}

export interface PurchaseInitiationResponse {
  success: boolean;
  client_secret?: string;
  transaction_id?: number;
  payment_intent_id?: string;
  plan_details?: PricingPlan;
  message?: string;
  // Error fields
  error_type?: string;
  field_errors?: Record<string, string[]>;
}

export interface StudentBalanceInfo {
  id: number;
  name: string;
  email: string;
}

export interface BalanceSummary {
  hours_purchased: string; // Decimal as string
  hours_consumed: string; // Decimal as string
  remaining_hours: string; // Decimal as string
  balance_amount: string; // Decimal as string
}

export interface PackageInfo {
  transaction_id: number;
  plan_name: string;
  hours_included: string; // Decimal as string
  hours_consumed: string; // Decimal as string
  hours_remaining: string; // Decimal as string
  expires_at: string | null;
  days_until_expiry: number | null;
  is_expired: boolean;
}

export interface PackageStatus {
  active_packages: PackageInfo[];
  expired_packages: PackageInfo[];
}

export interface StudentBalanceResponse {
  student_info: StudentBalanceInfo;
  balance_summary: BalanceSummary;
  package_status: PackageStatus;
  upcoming_expirations: Omit<PackageInfo, 'hours_included' | 'hours_consumed' | 'is_expired'>[];
}

export interface StripeConfig {
  public_key: string;
  success: boolean;
  error?: string;
}

export interface PurchaseFormData {
  selectedPlan: PricingPlan | null;
  studentName: string;
  studentEmail: string;
  isProcessing: boolean;
  errors: Record<string, string>;
}

export interface PurchaseFlowState {
  step: 'plan-selection' | 'user-info' | 'payment' | 'success' | 'error';
  formData: PurchaseFormData;
  stripeConfig: StripeConfig | null;
  paymentIntentSecret: string | null;
  transactionId: number | null;
  errorMessage: string | null;
}

// Stripe payment processing types
export interface StripePaymentElement {
  mount: (element: string | HTMLElement) => void;
  unmount: () => void;
  update: (options: any) => void;
  on: (event: string, handler: (event: any) => void) => void;
}

export interface StripeElements {
  create: (type: 'payment', options?: any) => StripePaymentElement;
  getElement: (type: 'payment') => StripePaymentElement | null;
}

export interface StripeInstance {
  elements: (options?: any) => StripeElements;
  confirmPayment: (options: {
    elements: StripeElements;
    confirmParams: {
      return_url: string;
    };
    redirect?: 'if_required' | 'always';
  }) => Promise<{
    error?: {
      type: string;
      code: string;
      message: string;
    };
    paymentIntent?: {
      status: string;
      id: string;
    };
  }>;
}

// Hook return types
export interface UsePurchaseFlowResult {
  state: PurchaseFlowState;
  actions: {
    selectPlan: (plan: PricingPlan) => void;
    updateStudentInfo: (name: string, email: string) => void;
    initiatePurchase: () => Promise<void>;
    confirmPayment: (stripe: StripeInstance, elements: StripeElements) => Promise<void>;
    resetFlow: () => void;
    setError: (message: string) => void;
  };
  isLoading: boolean;
  canProceed: boolean;
}

export interface UsePricingPlansResult {
  plans: PricingPlan[];
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export interface UseStudentBalanceResult {
  balance: StudentBalanceResponse | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

// Payment status types for tracking
export type PaymentStatus = 'idle' | 'processing' | 'succeeded' | 'failed';

export interface PaymentState {
  status: PaymentStatus;
  error: string | null;
  paymentIntent: {
    id: string;
    status: string;
  } | null;
}

// Transaction history types
export interface TransactionHistoryItem {
  id: number;
  transaction_id: string;
  transaction_type: 'purchase' | 'consumption' | 'refund' | 'adjustment';
  transaction_type_display: string;
  amount: string;
  hours_changed: string;
  payment_status: 'pending' | 'succeeded' | 'failed' | 'refunded';
  payment_status_display: string;
  plan_name?: string;
  description: string;
  created_at: string;
  processed_at?: string;
}

export interface PaginatedTransactionHistory {
  count: number;
  next: string | null;
  previous: string | null;
  results: TransactionHistoryItem[];
}

// Purchase history types
export interface PurchaseHistoryItem {
  id: number;
  transaction_id: string;
  plan_id: number;
  plan_name: string;
  plan_type: 'package' | 'subscription';
  hours_included: string;
  hours_consumed: string;
  hours_remaining: string;
  amount_paid: string;
  payment_status: 'pending' | 'succeeded' | 'failed' | 'refunded';
  payment_status_display: string;
  purchase_date: string;
  expires_at: string | null;
  days_until_expiry: number | null;
  is_expired: boolean;
  is_active: boolean;
  consumption_history?: ConsumptionRecord[];
}

export interface ConsumptionRecord {
  id: number;
  session_id: string;
  hours_consumed: string;
  session_date: string;
  teacher_name?: string;
  subject?: string;
  session_type: 'individual' | 'group';
  description: string;
}

export interface PaginatedPurchaseHistory {
  count: number;
  next: string | null;
  previous: string | null;
  results: PurchaseHistoryItem[];
}

// Dashboard filter types
export interface TransactionFilterOptions {
  payment_status?: string;
  transaction_type?: string;
  date_from?: string;
  date_to?: string;
  search?: string;
}

export interface PurchaseFilterOptions {
  active_only?: boolean;
  include_consumption?: boolean;
  date_from?: string;
  date_to?: string;
  search?: string;
}

// Dashboard state types
export interface DashboardState {
  activeTab: 'overview' | 'transactions' | 'purchases' | 'settings';
  transactionFilters: TransactionFilterOptions;
  purchaseFilters: PurchaseFilterOptions;
  searchQuery: string;
}

// User profile types
export interface UserProfile {
  id: number;
  name: string;
  email: string;
  phone?: string;
  avatar_url?: string;
  roles: string[];
  preferences?: {
    notifications: {
      email: boolean;
      push: boolean;
      sms: boolean;
    };
    language: string;
    timezone: string;
  };
}

// Receipt types
export interface Receipt {
  id: string;
  transaction_id: string;
  purchase_date: string;
  amount: string;
  plan_name: string;
  receipt_number: string;
  status: 'pending' | 'generated' | 'failed';
  download_url?: string;
  generated_at?: string;
}

export interface ReceiptGenerationResponse {
  success: boolean;
  receipt_id: string;
  message: string;
  status: 'pending' | 'generated' | 'failed';
}

// Payment method types
export interface PaymentMethod {
  id: string;
  type: 'card';
  card: {
    brand: string;
    last4: string;
    exp_month: number;
    exp_year: number;
    funding: string;
  };
  billing_details: {
    name?: string;
    email?: string;
    address?: {
      line1?: string;
      line2?: string;
      city?: string;
      state?: string;
      postal_code?: string;
      country?: string;
    };
  };
  is_default: boolean;
  created_at: string;
}

export interface AddPaymentMethodRequest {
  payment_method_id: string;
  set_as_default?: boolean;
}

export interface AddPaymentMethodResponse {
  success: boolean;
  payment_method: PaymentMethod;
  message: string;
}

// Analytics types
export interface UsageStatistics {
  total_sessions: number;
  total_hours_consumed: number;
  average_session_duration: number;
  sessions_this_month: number;
  hours_this_month: number;
  most_active_subject?: string;
  preferred_time_slot?: string;
  streak_days: number;
}

export interface LearningInsight {
  id: string;
  type: 'achievement' | 'suggestion' | 'milestone' | 'warning';
  title: string;
  description: string;
  icon: string;
  created_at: string;
  is_read: boolean;
}

export interface UsagePattern {
  hour: number;
  day_of_week: number;
  session_count: number;
  average_duration: number;
  subjects: {
    [subject: string]: {
      session_count: number;
      total_hours: number;
    };
  };
}

export interface AnalyticsTimeRange {
  start_date: string;
  end_date: string;
}

// Notification types
export interface NotificationPreferences {
  low_balance_alerts: boolean;
  session_reminders: boolean;
  package_expiration: boolean;
  weekly_reports: boolean;
  learning_insights: boolean;
  renewal_prompts: boolean;
  email_notifications: boolean;
  in_app_notifications: boolean;
}

export interface Notification {
  id: string;
  type: 'low_balance' | 'renewal_prompt' | 'package_expiry' | 'session_reminder' | 'insight';
  title: string;
  message: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  timestamp: Date;
  isRead: boolean;
  actionLabel?: string;
  actionUrl?: string;
}

// One-Click Renewal & Quick Top-Up Types
export interface TopUpPackage {
  id: number;
  name: string;
  hours: number;
  price_eur: string;
  price_per_hour: string;
  is_popular: boolean;
  discount_percentage?: number;
  display_order: number;
}

export interface RenewalRequest {
  payment_method_id?: string;
  use_default_payment_method?: boolean;
  plan_id?: number;
  confirm_immediately?: boolean;
}

export interface RenewalResponse {
  success: boolean;
  transaction_id?: number;
  payment_intent_id?: string;
  renewal_details?: {
    plan_name: string;
    hours_included: string;
    amount_paid: string;
    expires_at: string;
  };
  message?: string;
  client_secret?: string;
  // Error fields
  error_type?: string;
  field_errors?: Record<string, string[]>;
}

export interface QuickTopUpRequest {
  package_id: number;
  payment_method_id?: string;
  use_default_payment_method?: boolean;
  confirm_immediately?: boolean;
}

export interface QuickTopUpResponse {
  success: boolean;
  transaction_id?: number;
  payment_intent_id?: string;
  package_details?: {
    package_name: string;
    hours_purchased: number;
    amount_paid: string;
  };
  message?: string;
  client_secret?: string;
  // Error fields
  error_type?: string;
  field_errors?: Record<string, string[]>;
}

// Quick actions and UI state types
export interface QuickActionState {
  isVisible: boolean;
  actionType: 'renewal' | 'topup' | null;
  isProcessing: boolean;
  error: string | null;
  selectedPackage?: TopUpPackage;
  selectedPaymentMethod?: PaymentMethod;
  confirmationStep: 'select' | 'confirm' | 'processing' | 'success' | 'error';
}

export interface BiometricAuthState {
  isSupported: boolean;
  isEnabled: boolean;
  isAuthenticating: boolean;
  error: string | null;
}