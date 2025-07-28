# Teacher Invitation Management System

This module implements a comprehensive teacher invitation management system for the Aprende Comigo platform, addressing GitHub issue #62.

## Features Implemented

### 1. Enhanced InviteTeacherModal
- **Fixed API Endpoint**: Updated from `/accounts/teachers/invite-email/` to `/accounts/teachers/invite_existing/`
- **Role Selection**: Added dropdown to select teacher role (Professor, Administrador)
- **Bulk Invitations**: Support for sending multiple invitations at once
- **Custom Messages**: Optional personalized messages for invitations
- **Progress Tracking**: Real-time progress indicators for bulk operations
- **Enhanced Validation**: Proper email validation and error handling

### 2. Invitation Management Dashboard
- **InvitationStatusDashboard**: Complete dashboard showing all school invitations
- **Real-time Updates**: Optional polling for automatic status updates
- **Filtering & Search**: Filter by status, role, email, and custom ordering
- **Statistics Overview**: Visual summary of invitation statistics
- **Pagination**: Efficient handling of large invitation lists

### 3. Individual Invitation Management
- **InvitationListItem**: Detailed view of each invitation with status badges
- **Action Menu**: Resend, cancel, and copy link actions
- **Status Indicators**: Visual status badges with icons and colors
- **Expiration Warnings**: Clear indicators for expired invitations
- **Custom Messages**: Display of personalized invitation messages

### 4. API Integration
- **invitationApi.ts**: Complete API service with all backend endpoints
- **Custom Hooks**: Reusable hooks for invitation operations
- **Error Handling**: Comprehensive error handling with user feedback
- **TypeScript Interfaces**: Full type safety for all invitation data

### 5. Navigation Integration
- **Dashboard Integration**: Added "Manage Invitations" to QuickActionsPanel
- **Dedicated Route**: `/school-admin/invitations` for invitation management
- **Acceptance Page**: Public page for invitation acceptance

## File Structure

```
components/invitations/
├── index.ts                      # Export barrel
├── InvitationStatusDashboard.tsx # Main dashboard component
├── InvitationListItem.tsx        # Individual invitation display
├── InvitationFilters.tsx         # Filtering component
└── README.md                     # This documentation

api/
└── invitationApi.ts              # API service and interfaces

hooks/
└── useInvitations.ts             # Custom hooks for invitation management

app/
├── (school-admin)/
│   └── invitations.tsx           # Invitation management page
└── accept-invitation/
    └── [token].tsx               # Public invitation acceptance page

components/modals/
└── invite-teacher-modal.tsx      # Enhanced invitation modal
```

## Usage

### Basic Dashboard Usage
```tsx
import { InvitationStatusDashboard } from '@/components/invitations';

<InvitationStatusDashboard
  onInvitePress={() => setShowInviteModal(true)}
  autoRefresh={true}
  refreshInterval={30000}
/>
```

### Custom Hooks Usage
```tsx
import { useInvitations, useInviteTeacher } from '@/hooks/useInvitations';

const { invitations, loading, refreshInvitations } = useInvitations();
const { inviteTeacher, loading: inviting } = useInviteTeacher();

// Send single invitation
await inviteTeacher({
  email: 'teacher@example.com',
  school_id: 1,
  role: SchoolRole.TEACHER,
  custom_message: 'Welcome to our team!'
});
```

### Bulk Invitations
```tsx
import { useBulkInvitations } from '@/hooks/useInvitations';

const { sendBulkInvitations, progress } = useBulkInvitations();

await sendBulkInvitations({
  school_id: 1,
  invitations: [
    { email: 'teacher1@example.com', role: SchoolRole.TEACHER },
    { email: 'admin@example.com', role: SchoolRole.SCHOOL_ADMIN },
  ]
});
```

## Backend Integration

The system integrates with these backend endpoints:
- `POST /api/accounts/teachers/invite_bulk/` - Bulk invitation sending
- `POST /api/accounts/teachers/invite_existing/` - Single invitation
- `GET /api/accounts/teacher-invitations/list_for_school/` - List invitations
- `GET /api/accounts/teacher-invitations/{token}/status/` - Check status
- `POST /api/accounts/teacher-invitations/{token}/accept/` - Accept invitation
- `POST /api/accounts/teacher-invitations/{token}/resend/` - Resend invitation
- `PATCH /api/accounts/teacher-invitations/{token}/` - Update/cancel invitation

## Key Simplifications

As requested, the implementation focuses on:
- **No WebSocket**: Uses simple polling for real-time updates
- **Simple UI**: Clean, professional interface using Gluestack UI
- **Reliability**: Comprehensive error handling and validation
- **Cross-platform**: Works on web, iOS, and Android
- **Performance**: Efficient pagination and lazy loading

## Status Indicators

The system supports these invitation statuses:
- **Pending**: Just created, not yet sent
- **Sent**: Email sent successfully
- **Delivered**: Email delivered to recipient
- **Viewed**: Recipient opened the invitation
- **Accepted**: Invitation accepted by recipient
- **Declined**: Invitation declined by recipient
- **Expired**: Invitation passed expiration date
- **Cancelled**: Invitation cancelled by admin

Each status has appropriate visual indicators and available actions.

## Future Enhancements

Potential improvements for future iterations:
- WebSocket integration for real-time updates
- Advanced analytics and reporting
- Invitation templates management
- Bulk operations via CSV import
- Email tracking and analytics
- Custom invitation branding