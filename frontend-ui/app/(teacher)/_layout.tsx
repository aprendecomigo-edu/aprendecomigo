import { isWeb } from '@gluestack-ui/nativewind-utils/IsWeb';
import { Stack } from 'expo-router';
import React from 'react';

import { useSchool } from '@/api/auth';

export default function TeacherLayout() {
  const { isTeacher } = useSchool();

  return (
    <Stack
      screenOptions={{
        headerShown: false,
        animation: isWeb ? 'none' : 'slide_from_right',
      }}
    >
      <Stack.Protected guard={isTeacher}>
        <Stack.Screen name="dashboard/index" options={{ title: 'Dashboard' }} />
        <Stack.Screen name="students/index" options={{ title: 'Estudantes' }} />
        <Stack.Screen name="students/[id]" options={{ title: 'Detalhes do Estudante' }} />
        <Stack.Screen name="sessions/index" options={{ title: 'Sessões' }} />
        <Stack.Screen name="analytics/index" options={{ title: 'Analytics' }} />
        <Stack.Screen name="profile/index" options={{ title: 'Perfil' }} />
        <Stack.Screen name="schools/index" options={{ title: 'Minhas Escolas' }} />
      </Stack.Protected>
    </Stack>
  );
}
