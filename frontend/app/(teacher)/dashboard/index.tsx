import { lazy, Suspense } from 'react';

import LoadingScreen from '@/components/ui/loading-screen';

// Lazy load the TeacherDashboardContent component
const TeacherDashboardContent = lazy(() => import('./TeacherDashboardContent'));

export default function TeacherDashboard() {
  return (
    <Suspense fallback={<LoadingScreen message="Loading teacher dashboard..." />}>
      <TeacherDashboardContent />
    </Suspense>
  );
}
