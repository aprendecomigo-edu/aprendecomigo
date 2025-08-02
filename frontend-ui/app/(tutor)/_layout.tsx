import { Slot } from 'expo-router';
import React from 'react';

import { Box } from '@/components/ui/box';

export default function TutorLayout() {
  return (
    <Box className="flex-1">
      <Slot />
    </Box>
  );
}
