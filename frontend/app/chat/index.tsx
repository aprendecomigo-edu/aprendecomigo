import { lazy, Suspense } from 'react';
import LoadingScreen from '@/components/ui/loading-screen';

// Lazy load the ChatList component
const ChatList = lazy(() => import('@/components/chat/ChatList'));

export default function ChatRoute() {
  return (
    <Suspense fallback={<LoadingScreen message="Loading chat..." />}>
      <ChatList />
    </Suspense>
  );
}
