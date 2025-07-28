// Export all navigation components for easy importing
export { MobileNavigation } from './mobile-navigation';
export { SideNavigation } from './side-navigation';
export { TopNavigation } from './top-navigation';
export { Breadcrumb } from './breadcrumb';
export { QuickActions } from './quick-actions';

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
