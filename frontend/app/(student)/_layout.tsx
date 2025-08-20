import { Stack } from 'expo-router';
import React from 'react';

import { AuthGuard } from '@/components/auth/AuthGuard';
import { isWeb } from '@/utils/platform';

export default function StudentLayout() {
  return (
    <AuthGuard allowedRoles={['student']} redirectTo="/dashboard">
      <Stack
        screenOptions={{
          headerShown: false,
          animation: isWeb ? 'none' : 'slide_from_right',
        }}
      >
        <Stack.Screen name="index" options={{ title: 'Dashboard' }} />
        <Stack.Screen name="dashboard/index" options={{ title: 'Dashboard Completo' }} />
        <Stack.Screen name="balance" options={{ title: 'Saldo' }} />
      </Stack>
    </AuthGuard>
  );
}
