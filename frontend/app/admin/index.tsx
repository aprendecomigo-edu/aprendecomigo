import { lazy, Suspense } from 'react';

import LoadingScreen from '@/components/ui/loading-screen';

// Lazy load the AdminDashboard component
const AdminDashboardPage = lazy(() => import('@/components/dashboard/AdminDashboard'));

export default function AdminRoute() {
  return (
    <Suspense fallback={<LoadingScreen message="Loading admin dashboard..." />}>
      <AdminDashboardPage />
    </Suspense>
  );
}
