// Fallback implementation with Platform.OS conditional
// This file should be overridden by platform-specific files (.web.tsx, .native.tsx)
import { Platform } from 'react-native';

// Import platform-specific implementations
import { WelcomeScreen as WebWelcomeScreen } from './welcome-screen.web';
import { WelcomeScreen as NativeWelcomeScreen } from './welcome-screen.native';

// Export the appropriate implementation based on platform
export const WelcomeScreen = Platform.OS === 'web' ? WebWelcomeScreen : NativeWelcomeScreen;
