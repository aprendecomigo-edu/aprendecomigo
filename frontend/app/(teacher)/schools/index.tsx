import { useRouter } from 'expo-router';
import React from 'react';

import { InvitationErrorBoundary } from '@/components/invitations';
import MainLayout from '@/components/layouts/MainLayout';
import { MultiSchoolDashboard } from '@/components/multi-school';
import { useInvitationActions } from '@/hooks/useInvitations';
import { useMultiSchool, SchoolMembership } from '@/hooks/useMultiSchool';

const TeacherSchoolsPage = () => {
  const router = useRouter();
  useMultiSchool();
  useInvitationActions();

  const handleSchoolSelect = (_school: SchoolMembership) => {
    // Navigate to the teacher dashboard for the selected school
    router.push('/(teacher)/dashboard');
  };

  const handleManageInvitations = () => {
    // Navigate to invitations page or show modal
    router.push('/accept-invitation/pending');
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
