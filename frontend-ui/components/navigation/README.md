# Navigation System

This directory contains a modular and maintainable navigation system for the application. The navigation components are designed to be easily configurable and reusable across different parts of the app.

## Structure

```
navigation/
├── index.ts                 # Export file for all navigation components
├── navigation-config.ts     # Central configuration for all navigation items
├── logout-button.tsx       # Reusable logout button with confirmation modal
├── mobile-navigation.tsx   # Bottom tab navigation for mobile devices
├── school-selector.tsx     # School selection dropdown component
├── side-navigation.tsx     # Left sidebar navigation for desktop
├── top-navigation.tsx      # Top header navigation (web/mobile variants)
└── README.md              # This file
```

## Components

### 1. TopNavigation
Renders the top header navigation with two variants:
- **Web variant**: Shows hamburger menu, school selector, logout button, and avatar
- **Mobile variant**: Shows back button, school selector, and logout icon

```tsx
import { TopNavigation } from '@/components/navigation';

<TopNavigation
  title="Page Title"
  variant="web" // or "mobile"
  onToggleSidebar={() => setSidebarVisible(!sidebarVisible)}
  onSchoolChange={(school) => handleSchoolChange(school)}
/>
```

### 2. SideNavigation
Left sidebar navigation for desktop with icon-based navigation items.

```tsx
import { SideNavigation } from '@/components/navigation';

<SideNavigation className="custom-class" />
```

### 3. MobileNavigation
Bottom tab navigation for mobile devices, hidden on desktop.

```tsx
import { MobileNavigation } from '@/components/navigation';

<MobileNavigation className="custom-class" />
```

### 4. SchoolSelector
Dropdown component for selecting and switching between schools.

```tsx
import { SchoolSelector } from '@/components/navigation';

<SchoolSelector
  onSchoolChange={(school) => handleSchoolChange(school)}
  initialSchool={schools[0]}
/>
```

### 5. LogoutButton
Reusable logout button with confirmation modal in three display styles:

```tsx
import { LogoutButton } from '@/components/navigation';

<LogoutButton displayStyle="button" />        // Full button with text
<LogoutButton displayStyle="icon-with-text" /> // Icon with small text
<LogoutButton displayStyle="icon-only" />      // Icon only (default)
```

## Configuration

All navigation items are centrally configured in `navigation-config.ts`:

### Adding Navigation Items

#### Sidebar Navigation (Desktop)
```typescript
export const sidebarNavItems: SidebarItem[] = [
  {
    id: 'home',
    icon: HomeIcon,
    route: '/home',
  },
  {
    id: 'new-page',
    icon: NewPageIcon,
    route: '/new-page',
  },
];
```

#### Bottom Tab Navigation (Mobile)
```typescript
export const bottomTabNavItems: BottomTabItem[] = [
  {
    id: 'home',
    label: 'Home',
    icon: HomeIcon,
    route: '/home',
  },
  {
    id: 'new-tab',
    label: 'New Tab',
    icon: NewTabIcon,
    route: '/new-tab',
  },
];
```

#### Schools Data
```typescript
export const schools: School[] = [
  {
    id: '1',
    name: 'School Name',
  },
  {
    id: '2',
    name: 'Another School',
  },
];
```

## Usage in MainLayout

The navigation components are integrated into the `MainLayout` component:

```tsx
import { MainLayout } from '@/components/layouts/main-layout';

export default function Page() {
  return (
    <MainLayout showSidebar={true}>
      <YourPageContent />
    </MainLayout>
  );
}
```

## Best Practices

### 1. Configuration-Driven
- All navigation items are defined in `navigation-config.ts`
- Makes it easy to add, remove, or modify navigation items
- Centralizes navigation logic

### 2. Component Separation
- Each navigation component has a single responsibility
- Components are reusable and testable
- Clear interfaces and props

### 3. Responsive Design
- Different components for mobile and desktop experiences
- Conditional rendering based on screen size
- Consistent styling with Tailwind classes

### 4. Type Safety
- Full TypeScript support with proper interfaces
- Type-safe navigation item configuration
- Compile-time error checking

## Customization

### Adding Icons
1. Import the icon from `lucide-react-native`
2. Add it to the navigation configuration
3. The icon will automatically be rendered

### Changing Styles
- Use the `className` prop to add custom styles
- Modify base styles in the component files
- Follow the existing Tailwind class patterns

### Adding New Navigation Types
1. Define the interface in `navigation-config.ts`
2. Create the navigation items array
3. Create a new component or extend existing ones
4. Export from `index.ts`

## Testing

Each navigation component should be tested for:
- Rendering with different props
- Navigation functionality
- Responsive behavior
- Accessibility features

Example test structure:
```tsx
describe('TopNavigation', () => {
  it('renders web variant correctly', () => {
    // Test implementation
  });

  it('renders mobile variant correctly', () => {
    // Test implementation
  });

  it('calls onToggleSidebar when menu is clicked', () => {
    // Test implementation
  });
});
```
