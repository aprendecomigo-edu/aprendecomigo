/**
 * Individual Child Account Route
 * 
 * Detailed view of a specific child's account showing their progress,
 * balance, activity history, and parent management options.
 */

import React from 'react';
import { useLocalSearchParams } from 'expo-router';
import { ChildAccountView } from '@/components/parent';

export default function ChildAccountPage() {
  const { childId } = useLocalSearchParams<{ childId: string }>();

  if (!childId) {
    return null; // Or redirect to parent dashboard
  }

  return <ChildAccountView childId={childId} />;
}