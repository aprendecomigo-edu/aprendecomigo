import { Stack } from 'expo-router';

export default function AuthLayout() {
  return (
    <Stack screenOptions={{ headerShown: false }}>
      <Stack.Screen name="signin" />
      <Stack.Screen name="signup" />
      <Stack.Screen name="verify-code" />
      <Stack.Screen name="forgot-password" />
      <Stack.Screen name="create-password" />
      <Stack.Screen name="splash-screen" />
    </Stack>
  );
}
