// Export all navigation components for easy importing
export { MobileNavigation } from './MobileNavigation';
export { SideNavigation } from './SideNavigation';
export { TopNavigation } from './TopNavigation';
export { QuickActions } from './QuickActions';

// Export navigation configuration and types
export {
  bottomTabNavItems,
  schools,
  sidebarNavItems,
  adminSidebarNavItems,
  getNavigationItems,
  hasRoutePermission,
  ROUTE_PERMISSIONS,
  type BottomTabItem,
  type NavigationItem,
  type School,
  type SidebarItem,
} from './navigation-config';
