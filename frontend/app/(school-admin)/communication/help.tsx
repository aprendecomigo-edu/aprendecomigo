import { lazy, Suspense } from 'react';

import LoadingScreen from '@/components/ui/loading-screen';

// Lazy load the HelpPageContent component
const HelpPageContent = lazy(() => import('./HelpPageContent'));

export default function HelpPage() {
  return (
    <Suspense fallback={<LoadingScreen message="Loading help center..." />}>
      <HelpPageContent />
    </Suspense>
  );
}
