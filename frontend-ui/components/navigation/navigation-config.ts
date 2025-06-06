import type { LucideIcon } from 'lucide-react-native';
import { HomeIcon, Calendar, MessagesSquare, Users, Settings } from 'lucide-react-native';

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
}

export interface SidebarItem {
  id: string;
  icon: LucideIcon | any;
  route: string;
}

export interface BottomTabItem {
  id: string;
  label: string;
  icon: LucideIcon | any;
  route: string;
}

// Sidebar navigation items (desktop left sidebar)
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
