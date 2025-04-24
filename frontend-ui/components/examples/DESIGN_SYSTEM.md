# AprendeComigo Design System

This document provides guidelines for maintaining a consistent design across the AprendeComigo educational platform.

## How to Use the Design System

The design system is implemented as a set of reusable components and styles that can be used throughout the application. To view a live reference implementation, visit the `/design-system` route in the application.

## Accessing the Design System Reference

1. Run the application in development mode:

```bash
yarn dev
```

2. Navigate to `/design-system` in your browser or app to view the complete design system reference.

## Design Principles

1. **Clarity**: Components should be easy to understand and use, with clear hierarchies of information.
2. **Consistency**: Use the same patterns, colors, and components across the platform.
3. **Responsive**: All designs should work well on all device sizes, from mobile to desktop.
4. **Accessibility**: Components should be accessible to all users, including those with disabilities.

## Color Palette

### Primary Colors

- **Primary Blue**: #3B82F6 (blue-600)
  - Darker shade: #2563EB (blue-700)
  - Lighter shade: #93C5FD (blue-300)
  - Background shade: #EFF6FF (blue-50)

### Secondary Colors

- **Green**: #22C55E (green-500) - Used for success indicators and completed items
- **Orange**: #F97316 (orange-500) - Used for warning or active indicators
- **Red**: #EF4444 (red-500) - Used for error states and urgent items
  - Background: #FEF2F2 (red-50)

### Neutral Colors

- Background: #FFFFFF
- Border color: #E5E7EB (gray-200)
- Text (primary): #111827 (gray-900)
- Text (secondary): #6B7280 (gray-500)

## Typography

### Font Family

- Primary font: System font (SF Pro for iOS, Roboto for Android)
- Use bold for headings, regular for body text

### Text Sizes

- Large heading: 24px (text-2xl)
- Section heading: 18px (text-lg)
- Card title: 16px (text-base, font-bold)
- Body text: 14px (text-sm)
- Caption/metadata: 12px (text-xs)

## Component Guidelines

### Student Profile Header

The student profile header should appear at the top of the student dashboard and contain:

- Student avatar with initials (left-aligned)
- Student name (bold)
- Student grade/class
- Notification indicator (right-aligned)

```jsx
<HStack className="bg-blue-600 rounded-lg p-4 items-center justify-between">
  <HStack space="md" className="items-center">
    <Avatar className="bg-blue-700 h-14 w-14">
      <AvatarFallbackText>{userInitials}</AvatarFallbackText>
    </Avatar>
    <VStack>
      <Text className="text-white font-bold text-xl">{userName}</Text>
      <Text className="text-white">Aluno • {userGrade}</Text>
    </VStack>
  </HStack>
  <Avatar className="bg-blue-500 h-9 w-9">
    <AvatarFallbackText>3</AvatarFallbackText>
  </Avatar>
</HStack>
```

### Class Cards

Class cards display information about upcoming or completed classes:

- Color indicator on the left edge (green for completed, orange for upcoming)
- Subject name
- Date and time information
- Teacher and room information
- Completion status indicator (if applicable)

```jsx
<HStack className="border border-gray-200 rounded-lg p-4 items-start">
  <Box className={`${classInfo.colorAccent} w-2 h-full rounded-full mr-4 self-stretch`} />
  <VStack className="flex-1">
    <HStack className="justify-between w-full">
      <Text className="font-bold text-lg">{classInfo.subject}</Text>
      {classInfo.completed && (
        <Box className="bg-blue-50 rounded-full p-1">
          <Icon as={CheckIcon} size="sm" color="#3B82F6" />
        </Box>
      )}
    </HStack>
    <Text>{classInfo.date} • {classInfo.timeStart} - {classInfo.timeEnd}</Text>
    <Text>{classInfo.teacher} • {classInfo.room}</Text>
  </VStack>
</HStack>
```

### Task Cards

Task cards display information about pending assignments:

- Task icon (left-aligned)
- Task name (bold)
- Due date information
- Urgency indicator (if applicable)

```jsx
<HStack className="border border-gray-200 rounded-lg p-4 items-center justify-between">
  <HStack space="md">
    <Avatar className="bg-red-50 h-12 w-12">
      <Icon as={MinusIcon} color="#EF4444" />
    </Avatar>
    <VStack>
      <Text className="font-semibold">{task.title}</Text>
      <Text>Entrega: {task.dueDate}</Text>
    </VStack>
  </HStack>
  {task.isUrgent && (
    <Text className="text-red-500 font-semibold">URGENTE</Text>
  )}
</HStack>
```

## Empty States

For sections without content, use a consistent empty state:

```jsx
<Box className="border border-gray-200 rounded-lg p-8 items-center">
  <Text className="text-center text-gray-500">Nenhuma mensagem recente</Text>
</Box>
```

## Spacing Guidelines

- **Container padding**: 16px (p-4)
- **Section spacing**: 24px (space="xl")
- **Item spacing within sections**: 12px (space="md")
- **Small spacing between related elements**: 8px (space="sm")

## Maintainance and Contribution

When adding new components to the application:

1. Check the design system reference first to see if a component already exists.
2. If creating a new component, follow the established patterns and styles.
3. If the new component represents a new pattern, consider adding it to the design system reference.
4. Keep documentation updated when the design system evolves.

## Accessibility Guidelines

- Maintain color contrast ratios of at least 4.5:1 for text.
- Ensure touch targets are at least 44x44 points for interactive elements.
- Provide appropriate text alternatives for non-text content.
- Design with screen readers in mind.
- Support keyboard navigation for web interfaces.

## Responsive Design

- Use responsive classes to adapt layouts to different screen sizes.
- Follow mobile-first approach, adding complexity for larger screens.
- Test designs on multiple device sizes.

---

For any questions or feedback about the design system, please contact the design team. 