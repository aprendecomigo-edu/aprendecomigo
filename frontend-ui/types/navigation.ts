import { type LucideIcon } from 'lucide-react-native';

// Re-export existing types for backward compatibility
export type { NavigationItem, SidebarItem, BottomTabItem, School } from '@/components/navigation/navigation-config';

// New types for enhanced navigation features

export interface BreadcrumbItem {
  id: string;
  label: string;
  route?: string;
  isActive?: boolean;
}

export interface QuickAction {
  id: string;
  label: string;
  icon: LucideIcon;
  route?: string;
  action?: () => void;
  variant?: 'primary' | 'secondary' | 'outline';
  permission?: string;
  context?: string[]; // Which pages this action is relevant for
}

export interface SearchCategory {
  id: string;
  label: string;
  type: 'teacher' | 'student' | 'class' | 'setting';
  icon: LucideIcon;
  searchTypes: string[];
}

export interface SearchSuggestion {
  id: string;
  query: string;
  type: 'recent' | 'popular' | 'suggestion';
  timestamp?: Date;
}

export interface NotificationBadgeProps {
  count: number;
  type?: 'primary' | 'warning' | 'error' | 'success';
  size?: 'sm' | 'md' | 'lg';
  showZero?: boolean;
  maxCount?: number;
  className?: string;
}

// Navigation context types
export interface NavigationState {
  currentRoute: string;
  breadcrumbs: BreadcrumbItem[];
  searchQuery: string;
  isSearchFocused: boolean;
  notificationCounts: Record<string, number>;
  quickActionsVisible: boolean;
  sidebarCollapsed: boolean;
}

export interface NavigationActions {
  updateRoute: (route: string) => void;
  setBreadcrumbs: (breadcrumbs: BreadcrumbItem[]) => void;
  setSearchQuery: (query: string) => void;
  setSearchFocused: (focused: boolean) => void;
  updateNotificationCounts: (counts: Record<string, number>) => void;
  toggleQuickActions: () => void;
  toggleSidebar: () => void;
}

export interface NavigationContextType {
  state: NavigationState;
  actions: NavigationActions;
}

// Route configuration types
export interface RouteConfig {
  path: string;
  title: string;
  breadcrumbs?: BreadcrumbItem[];
  quickActions?: QuickAction[];
  permissions?: string[];
  searchable?: boolean;
}

export interface NavigationPermission {
  role: 'school_admin' | 'teacher' | 'student' | 'parent';
  routes: string[];
  actions: string[];
}

// Search result types (extending the API types)
export interface EnhancedSearchResult {
  id: string;
  type: 'teacher' | 'student' | 'class' | 'setting';
  title: string;
  subtitle?: string;
  avatar?: string;
  route: string;
  metadata?: Record<string, any>;
  relevanceScore?: number;
  category: SearchCategory;
  highlighted?: {
    title?: string;
    subtitle?: string;
  };
}

// Mobile navigation gesture types
export interface SwipeGesture {
  direction: 'left' | 'right' | 'up' | 'down';
  distance: number;
  velocity: number;
}

export interface TouchFeedback {
  haptic?: boolean;
  visual?: boolean;
  sound?: boolean;
}

// Animation and transition types
export interface NavigationTransition {
  type: 'slide' | 'fade' | 'scale' | 'none';
  duration: number;
  easing?: 'ease-in' | 'ease-out' | 'ease-in-out' | 'linear';
}

// Accessibility types
export interface NavigationAccessibility {
  ariaLabel: string;
  ariaRole?: string;
  testID?: string;
  accessibilityHint?: string;
  accessibilityState?: {
    selected?: boolean;
    expanded?: boolean;
    disabled?: boolean;
  };
}

// Enhanced navigation item with all features
export interface EnhancedNavigationItem extends NavigationItem {
  notificationCount?: number;
  accessibility?: NavigationAccessibility;
  transition?: NavigationTransition;
  touchFeedback?: TouchFeedback;
  children?: EnhancedNavigationItem[];
  expanded?: boolean;
  permission?: string;
  badge?: {
    text?: string;
    color?: string;
    variant?: 'dot' | 'count' | 'text';
  };
}