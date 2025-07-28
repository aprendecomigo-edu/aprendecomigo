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