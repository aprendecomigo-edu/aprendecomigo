import { NavigatorScreenParams } from '@react-navigation/native';

// Auth Stack Parameters
export type AuthStackParamList = {
  Login: undefined;
  VerifyCode: { email: string };
};

// Main Tab Parameters
export type MainTabParamList = {
  Home: undefined;
  Profile: undefined;
  Settings: undefined;
};

// Root Stack Parameters
export type RootStackParamList = {
  Auth: NavigatorScreenParams<AuthStackParamList>;
  Main: NavigatorScreenParams<MainTabParamList>;
}; 