import FontAwesome from '@expo/vector-icons/FontAwesome';
import { DarkTheme, DefaultTheme, ThemeProvider } from '@react-navigation/native';
import { useFonts } from 'expo-font';
import { Stack, Redirect, type Href } from 'expo-router';
import * as SplashScreen from 'expo-splash-screen';
import { useEffect } from 'react';
import { Platform } from 'react-native';

import { GluestackUIProvider } from '@/components/ui/gluestack-ui-provider';
import '../global.css';
import { AuthProvider, useAuth } from '@/api/authContext';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { ToastProvider } from '@/components/ui/toast';
import { View } from '@/components/ui/view';
import { useColorScheme } from '@/components/useColorScheme';
import { TutorialProvider, TutorialOverlay } from '@/components/tutorial';

export {
  // Catch any errors thrown by the Layout component.
  ErrorBoundary,
} from 'expo-router';

export const unstable_settings = {
  // Ensure that reloading on `/modal` keeps a back button present.
  initialRouteName: 'index',
};

// Prevent the splash screen from auto-hiding before asset loading is complete.
SplashScreen.preventAutoHideAsync();

export default function RootLayout() {
  const [loaded, error] = useFonts({
    SpaceMono: require('../assets/fonts/SpaceMono-Regular.ttf'),
    ...FontAwesome.font,
  });

  // Expo Router uses Error Boundaries to catch errors in the navigation tree.
  useEffect(() => {
    if (error) throw error;
  }, [error]);

  useEffect(() => {
    if (loaded) {
      SplashScreen.hideAsync();
    }
  }, [loaded]);

  if (!loaded) {
    return null;
  }

  return <RootLayoutNav />;
}

// Loading screen component to display while checking auth status
function LoadingScreen() {
  return (
    <View className="flex-1 justify-center items-center">
      <Spinner size="large" />
      <Text className="mt-4">Loading...</Text>
    </View>
  );
}

// This component will handle protected routes
function ProtectedRoutes() {
  const { isLoggedIn, isLoading } = useAuth();

  if (isLoading) {
    return <LoadingScreen />;
  }

  if (!isLoggedIn) {
    return <Redirect href="/auth/signin" />;
  }

  return (
    <Stack screenOptions={{ headerShown: false }}>
      <Stack.Screen name="home" />
      <Stack.Screen name="profile" />
      <Stack.Screen name="admin" />
      <Stack.Screen name="student" />
      <Stack.Screen name="chat" />
    </Stack>
  );
}

// This component will handle public routes
function PublicRoutes() {
  const { isLoggedIn, isLoading } = useAuth();

  if (isLoading) {
    return <LoadingScreen />;
  }

  if (isLoggedIn) {
    return <Redirect href={'home' as Href} />;
  }

  return (
    <Stack screenOptions={{ headerShown: false }}>
      <Stack.Screen name="index" />
      <Stack.Screen name="auth/signin" />
      <Stack.Screen name="auth/signup" />
      <Stack.Screen name="auth/verify-code" />
    </Stack>
  );
}

function RootLayoutNav() {
  const colorScheme = useColorScheme();

  // CSS Fix for NativeWind v4 + React Native Web compatibility
  useEffect(() => {
    if (Platform.OS === 'web' && typeof window !== 'undefined') {
      console.log('🔧 Applying CSS compatibility patch for NativeWind v4 + React Native Web...');

      // Global error handler for CSS-related errors
      const handleError = (event: ErrorEvent) => {
        if (event.error && event.error.message &&
            event.error.message.includes('CSSStyleDeclaration') &&
            event.error.message.includes('Indexed property setter')) {
          console.warn('Prevented CSS StyleDeclaration error:', event.error.message);
          event.preventDefault();
          event.stopPropagation();
          return false;
        }
      };

      window.addEventListener('error', handleError);

      // Prevent React error boundary triggers from CSS errors
      const originalConsoleError = console.error;
      console.error = function(...args) {
        const message = args.join(' ');
        if (message.includes('CSSStyleDeclaration') && message.includes('Indexed property setter')) {
          console.warn('Suppressed CSS error:', message);
          return;
        }
        return originalConsoleError.apply(console, args);
      };

      console.log('✅ CSS compatibility patch applied successfully');

      return () => {
        window.removeEventListener('error', handleError);
        console.error = originalConsoleError;
      };
    }
  }, []);

  return (
    <GluestackUIProvider mode={(colorScheme ?? 'light') as 'light' | 'dark'}>
      <ThemeProvider value={colorScheme === 'dark' ? DarkTheme : DefaultTheme}>
        <ToastProvider>
          <AuthProvider>
            <TutorialProvider>
              <Stack screenOptions={{ headerShown: false }}>
                <Stack.Screen name="index" />
                <Stack.Screen name="landing" />
                <Stack.Screen name="auth" />
                <Stack.Screen name="home" />
                <Stack.Screen name="profile" />
                <Stack.Screen name="settings" />
                <Stack.Screen name="chat" />
                <Stack.Screen name="purchase" />
                <Stack.Screen name="onboarding" />
                <Stack.Screen name="accept-invitation" />
                <Stack.Screen 
                  name="(school-admin)" 
                  options={{
                    headerShown: false,
                  }}
                />
                <Stack.Screen 
                  name="(tutor)" 
                  options={{
                    headerShown: false,
                  }}
                />
                <Stack.Screen name="parents" />
                <Stack.Screen name="admin" />
                <Stack.Screen name="student" />
                <Stack.Screen name="students" />
                <Stack.Screen name="teachers" />
                <Stack.Screen name="calendar" />
                <Stack.Screen name="users" />
              </Stack>
              <TutorialOverlay />
            </TutorialProvider>
          </AuthProvider>
        </ToastProvider>
      </ThemeProvider>
    </GluestackUIProvider>
  );
}
