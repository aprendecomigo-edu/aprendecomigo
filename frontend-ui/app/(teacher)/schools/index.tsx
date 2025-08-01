import React from 'react';
import { useRouter } from 'expo-router';

import MainLayout from '@/components/layouts/main-layout';
import { MultiSchoolDashboard } from '@/components/multi-school';
import { InvitationErrorBoundary } from '@/components/invitations';
import { useMultiSchool, SchoolMembership, PendingInvitation } from '@/hooks/useMultiSchool';
import { useInvitationActions } from '@/hooks/useInvitations';

const TeacherSchoolsPage = () => {
  const router = useRouter();
  const { refresh } = useMultiSchool();
  const { acceptInvitation } = useInvitationActions();

  const handleSchoolSelect = (school: SchoolMembership) => {
    // Navigate to the teacher dashboard for the selected school
    router.push('/(teacher)/dashboard');
  };

  const handleManageInvitations = () => {
    // Navigate to invitations page or show modal
    router.push('/accept-invitation/pending');
  };

  const handleInvitationAccept = async (invitation: PendingInvitation) => {
    try {
      await acceptInvitation(invitation.token);
      // Refresh the schools list after accepting
      await refresh();
    } catch (error) {
      console.error('Failed to accept invitation:', error);
    }
  };

  return (
    <MainLayout _title="Minhas Escolas">
      <InvitationErrorBoundary>
        <MultiSchoolDashboard
          onSchoolSelect={handleSchoolSelect}
          onManageInvitations={handleManageInvitations}
          showStats={true}
          compact={false}
        />
      </InvitationErrorBoundary>
    </MainLayout>
  );
};

export default TeacherSchoolsPage;