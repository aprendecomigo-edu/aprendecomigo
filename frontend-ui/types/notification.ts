/**
 * Notification Type Definitions
 * 
 * TypeScript interfaces for the notification system integrated with
 * the backend notification API endpoints.
 */

export interface NotificationResponse {
  id: number;
  notification_type: NotificationType;
  title: string;
  message: string;
  priority: NotificationPriority;
  is_read: boolean;
  created_at: string;
  read_at?: string;
  data?: Record<string, any>;
  related_transaction?: {
    id: number;
    amount: string;
    hours_purchased: string;
  };
}

export interface NotificationListResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: NotificationResponse[];
}

export interface NotificationUnreadCountResponse {
  unread_count: number;
}

export interface NotificationMarkReadResponse {
  message: string;
}

export type NotificationType = 
  | 'low_balance' 
  | 'package_expiring' 
  | 'balance_depleted'
  | 'renewal_prompt'
  | 'session_reminder'
  | 'learning_insight';

export type NotificationPriority = 'low' | 'medium' | 'high' | 'urgent';

export interface NotificationFilters {
  notification_type?: NotificationType;
  is_read?: boolean;
}

export interface NotificationSettings {
  low_balance_alerts: boolean;
  package_expiration: boolean;
  renewal_prompts: boolean;
  session_reminders: boolean;
  learning_insights: boolean;
  weekly_reports: boolean;
  in_app_notifications: boolean;
  email_notifications: boolean;
}

// Toast notification types for the low balance notification system
export interface ToastNotificationData {
  id: string;
  type: 'low_balance' | 'package_expiring' | 'balance_depleted' | 'success' | 'error';
  title: string;
  message: string;
  duration?: number;
  actionLabel?: string;
  actionUrl?: string;
  priority: NotificationPriority;
}

// Balance alert context types
export interface BalanceAlertState {
  currentBalance: number;
  totalHours: number;
  isLowBalance: boolean;
  isCriticalBalance: boolean;
  daysUntilExpiry?: number | null;
  lastBalanceCheck: Date | null;
  notifications: NotificationResponse[];
  unreadCount: number;
  wsConnected?: boolean;
}

export interface BalanceAlertActions {
  checkBalance: () => Promise<void>;
  markNotificationAsRead: (id: number) => Promise<void>;
  markAllAsRead: () => Promise<void>;
  dismissToast: (id: string) => void;
  showToast: (data: ToastNotificationData) => void;
  updateSettings: (settings: Partial<NotificationSettings>) => Promise<void>;
}

export interface BalanceAlertContextType {
  state: BalanceAlertState;
  actions: BalanceAlertActions;
  settings: NotificationSettings | null;
  loading: boolean;
  error: string | null;
}