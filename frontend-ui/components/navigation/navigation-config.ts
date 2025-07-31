import type { LucideIcon } from 'lucide-react-native';
import { 
  HomeIcon, 
  Calendar, 
  MessagesSquare, 
  Users, 
  Settings,
  GraduationCapIcon,
  UsersIcon,
  BookOpenIcon,
  BarChart3Icon,
  MailIcon,
  TrendingUpIcon,
  UserPlusIcon
} from 'lucide-react-native';

// Color constants
export const NAVIGATION_COLORS = {
  primary: '#156082',
  accent: '#F59E0B', // Orange/yellow for active states
  textPrimary: '#F8FAFC', // Off-white
  textSecondary: '#CBD5E1', // Light gray
} as const;

export interface NavigationItem {
  id: string;
  label: string;
  icon: LucideIcon | any;
  route: string;
  section?: 'main' | 'secondary';
  permission?: string;
  notificationCount?: number;
  badge?: {
    text?: string;
    color?: string;
    variant?: 'dot' | 'count' | 'text';
  };
}

export interface SidebarItem {
  id: string;
  icon: LucideIcon | any;
  route: string;
  permission?: string;
  notificationCount?: number;
  badge?: {
    text?: string;
    color?: string;
    variant?: 'dot' | 'count' | 'text';
  };
}

export interface BottomTabItem {
  id: string;
  label: string;
  icon: LucideIcon | any;
  route: string;
  permission?: string;
  notificationCount?: number;
  badge?: {
    text?: string;
    color?: string;
    variant?: 'dot' | 'count' | 'text';
  };
}

// Admin-specific navigation items for school administrators
export const adminSidebarNavItems: SidebarItem[] = [
  {
    id: 'dashboard',
    icon: HomeIcon,
    route: '/school-admin/dashboard',
    permission: 'school_admin',
  },
  {
    id: 'teachers',
    icon: GraduationCapIcon,
    route: '/teachers',
    permission: 'school_admin',
  },
  {
    id: 'students',
    icon: UsersIcon,
    route: '/students',
    permission: 'school_admin',
  },
  {
    id: 'classes',
    icon: BookOpenIcon,
    route: '/classes',
    permission: 'school_admin',
  },
  {
    id: 'calendar',
    icon: Calendar,
    route: '/calendar',
  },
  {
    id: 'analytics',
    icon: BarChart3Icon,
    route: '/analytics',
    permission: 'school_admin',
  },
  {
    id: 'invitations',
    icon: MailIcon,
    route: '/invitations',
    permission: 'school_admin',
  },
  {
    id: 'chat',
    icon: MessagesSquare,
    route: '/chat',
  },
  {
    id: 'settings',
    icon: Settings,
    route: '/settings',
  },
];

// Tutor-specific navigation items for individual tutors
export const tutorSidebarNavItems: SidebarItem[] = [
  {
    id: 'dashboard',
    icon: HomeIcon,
    route: '/(tutor)/dashboard',
    permission: 'tutor',
  },
  {
    id: 'students',
    icon: UsersIcon,
    route: '/(tutor)/students',
    permission: 'tutor',
  },
  {
    id: 'sessions', 
    icon: Calendar,
    route: '/(tutor)/sessions',
    permission: 'tutor',
  },
  {
    id: 'analytics',
    icon: TrendingUpIcon,
    route: '/(tutor)/analytics',
    permission: 'tutor',
  },
  {
    id: 'acquisition',
    icon: UserPlusIcon,
    route: '/(tutor)/acquisition',
    permission: 'tutor',
  },
  {
    id: 'calendar',
    icon: Calendar,
    route: '/calendar',
  },
  {
    id: 'chat',
    icon: MessagesSquare,
    route: '/chat',
  },
  {
    id: 'settings',
    icon: Settings,
    route: '/settings',
  },
];

// Default sidebar navigation items (for non-admin users)
export const sidebarNavItems: SidebarItem[] = [
  {
    id: 'home',
    icon: HomeIcon,
    route: '/home',
  },
  {
    id: 'calendar',
    icon: Calendar,
    route: '/calendar',
  },
  {
    id: 'chat',
    icon: MessagesSquare,
    route: '/chat',
  },
  {
    id: 'users',
    icon: Users,
    route: '/users',
  },
  {
    id: 'settings',
    icon: Settings,
    route: '/settings',
  },
];

// Bottom tab navigation items (mobile footer)
export const bottomTabNavItems: BottomTabItem[] = [
  {
    id: 'home',
    label: 'Home',
    icon: HomeIcon,
    route: '/home',
  },
  {
    id: 'calendar',
    label: 'Agenda',
    icon: Calendar,
    route: '/calendar',
  },
  {
    id: 'chat',
    label: 'Chats',
    icon: MessagesSquare,
    route: '/chat',
  },
  {
    id: 'users',
    label: 'Usuários',
    icon: Users,
    route: '/users',
  },
  {
    id: 'settings',
    label: 'Config',
    icon: Settings,
    route: '/settings',
  },
];

// School data interface and mock data
export interface School {
  id: string;
  name: string;
}

export const schools: School[] = [
  {
    id: '1',
    name: 'Escola São Paulo',
  },
  {
    id: '2',
    name: 'Colégio Rio de Janeiro',
  },
  {
    id: '3',
    name: '3ponto14',
  },
];

// Route permissions for role-based access control
export const ROUTE_PERMISSIONS: Record<string, string[]> = {
  '/school-admin': ['school_admin'],
  '/(school-admin)': ['school_admin'],
  '/(tutor)': ['tutor', 'teacher'],
  '/teachers': ['school_admin'],
  '/students': ['school_admin', 'teacher'],
  '/analytics': ['school_admin', 'tutor'],
  '/invitations': ['school_admin'],
  '/classes': ['school_admin', 'teacher'],
  '/calendar': ['school_admin', 'teacher', 'student', 'tutor'],
  '/chat': ['school_admin', 'teacher', 'student', 'tutor'],
  '/settings': ['school_admin', 'teacher', 'student', 'tutor'],
  '/home': ['school_admin', 'teacher', 'student', 'parent', 'tutor'],
};

// Navigation items getter based on user role
export const getNavigationItems = (userRole: string): SidebarItem[] => {
  if (userRole === 'school_admin') {
    return adminSidebarNavItems.filter(item => 
      !item.permission || item.permission === userRole
    );
  }
  if (userRole === 'tutor' || userRole === 'teacher') {
    return tutorSidebarNavItems.filter(item => 
      !item.permission || item.permission === 'tutor' || !item.permission
    );
  }
  return sidebarNavItems;
};

// Check if user has permission for a route
export const hasRoutePermission = (route: string, userRole: string): boolean => {
  const permissions = ROUTE_PERMISSIONS[route];
  if (!permissions) {
    return true; // Allow access if no permissions defined
  }
  return permissions.includes(userRole);
};
