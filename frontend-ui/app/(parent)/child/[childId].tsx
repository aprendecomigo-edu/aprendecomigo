/**
 * Individual Child Account Route
 *
 * Detailed view of a specific child's account showing their progress,
 * balance, activity history, and parent management options.
 */

import { useLocalSearchParams } from 'expo-router';
import React from 'react';

import { ChildAccountView } from '@/components/parent';

export default function ChildAccountPage() {
  const { childId } = useLocalSearchParams<{ childId: string }>();

  if (!childId) {
    return null; // Or redirect to parent dashboard
  }

  return <ChildAccountView childId={childId} />;
}
