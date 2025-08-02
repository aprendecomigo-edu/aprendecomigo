import React, { useState } from 'react';

import { InvitationStatusDashboard } from '@/components/invitations';
import MainLayout from '@/components/layouts/main-layout';
import { InviteTeacherModal } from '@/components/modals/invite-teacher-modal';

const InvitationsPage = () => {
  const [showInviteModal, setShowInviteModal] = useState(false);

  const handleInvitePress = () => {
    setShowInviteModal(true);
  };

  const handleInviteSuccess = () => {
    setShowInviteModal(false);
    // The dashboard will refresh automatically
  };

  const handleInviteClose = () => {
    setShowInviteModal(false);
  };

  return (
    <>
      <InvitationStatusDashboard
        onInvitePress={handleInvitePress}
        autoRefresh={true}
        refreshInterval={30000}
      />

      {/* Invite Teacher Modal */}
      <InviteTeacherModal
        isOpen={showInviteModal}
        onClose={handleInviteClose}
        onSuccess={handleInviteSuccess}
        schoolId={1} // TODO: Get this from user context or selected school
      />
    </>
  );
};

// Export wrapped with MainLayout
export const InvitationsPageWithLayout = () => {
  return (
    <MainLayout _title="Gerenciar Convites">
      <InvitationsPage />
    </MainLayout>
  );
};

export default InvitationsPageWithLayout;
