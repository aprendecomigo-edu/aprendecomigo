/**
 * Parent API Client
 *
 * API client functions for parent-specific operations including
 * child account management, family metrics, and purchase approvals.
 */

import apiClient from './apiClient';

// Types for Parent API responses
export interface ParentProfile {
  id: number;
  user: number;
  notification_preferences: {
    email_notifications: boolean;
    sms_notifications: boolean;
    push_notifications: boolean;
    weekly_summary: boolean;
    spending_alerts: boolean;
    achievement_notifications: boolean;
  };
  preferred_language: 'en' | 'pt' | 'es';
  created_at: string;
  updated_at: string;
}

export interface ChildProfile {
  id: number;
  child_user: {
    id: number;
    email: string;
    first_name: string;
    last_name: string;
    name: string;
  };
  relationship_type: 'parent' | 'guardian' | 'family_member';
  is_primary_contact: boolean;
  created_at: string;
  updated_at: string;
}

export interface FamilyBudgetControl {
  id: number;
  parent_profile: number;
  child_profile: number;
  monthly_limit: string; // Decimal as string
  weekly_limit: string | null;
  daily_limit: string | null;
  requires_approval_above: string; // Decimal as string
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface PurchaseApprovalRequest {
  id: number;
  parent_profile: number;
  child_profile: number;
  pricing_plan: {
    id: number;
    name: string;
    price: string;
    hours: number;
  };
  amount: string;
  status: 'pending' | 'approved' | 'rejected';
  requested_at: string;
  responded_at: string | null;
  response_notes: string | null;
  expires_at: string;
}

export interface FamilyMetrics {
  total_children: number;
  active_children: number;
  total_spent_this_month: string;
  total_hours_consumed_this_month: number;
  pending_approvals: number;
  children_summary: Array<{
    child_id: number;
    child_name: string;
    current_balance: string;
    hours_consumed_this_month: number;
    last_activity: string | null;
    status: 'active' | 'inactive' | 'suspended';
  }>;
}

export interface ParentApprovalDashboard {
  pending_requests: PurchaseApprovalRequest[];
  recent_approvals: PurchaseApprovalRequest[];
  budget_controls: FamilyBudgetControl[];
  family_metrics: FamilyMetrics;
}

// Parent Profile API functions
export const getParentProfile = async (): Promise<ParentProfile> => {
  const response = await apiClient.get('/accounts/parent-profiles/me/');
  return response.data;
};

export const updateParentProfile = async (
  profileData: Partial<ParentProfile>,
): Promise<ParentProfile> => {
  const response = await apiClient.patch('/accounts/parent-profiles/me/', profileData);
  return response.data;
};

// Parent-Child Relationship API functions
export const getChildrenProfiles = async (): Promise<ChildProfile[]> => {
  const response = await apiClient.get('/accounts/parent-child-relationships/');
  return response.data.results || response.data;
};

export const getChildProfile = async (childId: string): Promise<ChildProfile> => {
  const response = await apiClient.get(`/accounts/parent-child-relationships/${childId}/`);
  return response.data;
};

export const addChildToFamily = async (childData: {
  child_email: string;
  relationship_type: 'parent' | 'guardian' | 'family_member';
  is_primary_contact?: boolean;
}): Promise<ChildProfile> => {
  const response = await apiClient.post('/accounts/parent-child-relationships/', childData);
  return response.data;
};

export const removeChildFromFamily = async (childId: string): Promise<void> => {
  await apiClient.delete(`/accounts/parent-child-relationships/${childId}/`);
};

// Family Budget Control API functions
export const getFamilyBudgetControls = async (): Promise<FamilyBudgetControl[]> => {
  const response = await apiClient.get('/finances/budget-controls/');
  return response.data.results || response.data;
};

export const getBudgetControlForChild = async (childId: string): Promise<FamilyBudgetControl> => {
  const response = await apiClient.get(`/finances/budget-controls/?child_profile=${childId}`);
  return response.data.results?.[0] || response.data[0];
};

export const createBudgetControl = async (budgetData: {
  child_profile: number;
  monthly_limit?: string;
  weekly_limit?: string;
  daily_limit?: string;
  requires_approval_above: string;
  is_active?: boolean;
}): Promise<FamilyBudgetControl> => {
  const response = await apiClient.post('/finances/budget-controls/', budgetData);
  return response.data;
};

export const updateBudgetControl = async (
  budgetId: string,
  budgetData: Partial<FamilyBudgetControl>,
): Promise<FamilyBudgetControl> => {
  const response = await apiClient.patch(`/finances/budget-controls/${budgetId}/`, budgetData);
  return response.data;
};

export const deleteBudgetControl = async (budgetId: string): Promise<void> => {
  await apiClient.delete(`/finances/budget-controls/${budgetId}/`);
};

// Purchase Approval API functions
export const getPurchaseApprovalRequests = async (params?: {
  status?: 'pending' | 'approved' | 'rejected';
  child_profile?: string;
}): Promise<PurchaseApprovalRequest[]> => {
  const response = await apiClient.get('/finances/approval-requests/', { params });
  return response.data.results || response.data;
};

export const approvePurchaseRequest = async (
  requestId: string,
  responseNotes?: string,
): Promise<PurchaseApprovalRequest> => {
  const response = await apiClient.post(`/finances/approval-requests/${requestId}/approve/`, {
    response_notes: responseNotes,
  });
  return response.data;
};

export const rejectPurchaseRequest = async (
  requestId: string,
  responseNotes?: string,
): Promise<PurchaseApprovalRequest> => {
  const response = await apiClient.post(`/finances/approval-requests/${requestId}/reject/`, {
    response_notes: responseNotes,
  });
  return response.data;
};

// Parent Dashboard API functions
export const getParentApprovalDashboard = async (): Promise<ParentApprovalDashboard> => {
  const response = await apiClient.get('/finances/parent-approval-dashboard/');
  return response.data;
};

export const getFamilyMetrics = async (
  timeframe?: 'week' | 'month' | 'quarter',
): Promise<FamilyMetrics> => {
  const params = timeframe ? { timeframe } : {};
  const response = await apiClient.get('/finances/family-metrics/', { params });
  return response.data;
};

// Child Account Balance API functions (for parent view)
export const getChildAccountBalance = async (childId: string) => {
  const response = await apiClient.get(`/finances/student-balance/?student_id=${childId}`);
  return response.data;
};

export const getChildTransactionHistory = async (
  childId: string,
  params?: {
    page?: number;
    limit?: number;
    transaction_type?: string;
  },
) => {
  const response = await apiClient.get(
    `/finances/student-balance/transaction-history/?student_id=${childId}`,
    { params },
  );
  return response.data;
};

export const getChildPurchaseHistory = async (
  childId: string,
  params?: {
    page?: number;
    limit?: number;
  },
) => {
  const response = await apiClient.get(
    `/finances/student-balance/purchase-history/?student_id=${childId}`,
    { params },
  );
  return response.data;
};

// Student Purchase Request API function (child initiates, parent approves)
export const createStudentPurchaseRequest = async (requestData: {
  child_profile: number;
  pricing_plan: number;
  notes?: string;
}): Promise<PurchaseApprovalRequest> => {
  const response = await apiClient.post('/finances/student-purchase-request/', requestData);
  return response.data;
};
