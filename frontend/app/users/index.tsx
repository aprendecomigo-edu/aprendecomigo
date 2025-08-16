import { lazy, Suspense } from 'react';

import LoadingScreen from '@/components/ui/loading-screen';

// Lazy load the UsersPageContent component
const UsersPageContent = lazy(() => import('./UsersPageContent'));

export default function UsersPage() {
  return (
    <Suspense fallback={<LoadingScreen message="Loading users..." />}>
      <UsersPageContent />
    </Suspense>
  );
}
