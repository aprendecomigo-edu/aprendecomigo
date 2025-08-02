// Fallback implementation with Platform.OS conditional
// This file should be overridden by platform-specific files (.web.tsx, .native.tsx)
import { Platform } from 'react-native';

// Import platform-specific implementations
import { TeacherProfileWizard as WebTeacherProfileWizard } from './teacher-profile-wizard.web';
import { TeacherProfileWizard as NativeTeacherProfileWizard } from './teacher-profile-wizard.native';

// Export the appropriate implementation based on platform
export const TeacherProfileWizard = Platform.OS === 'web' ? WebTeacherProfileWizard : NativeTeacherProfileWizard;

// Re-export WIZARD_STEPS from common for compatibility
export { WIZARD_STEPS } from './teacher-profile-wizard-common';
