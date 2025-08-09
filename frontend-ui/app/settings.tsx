import { router } from 'expo-router';
import {
  Settings,
  Bell,
  Shield,
  User,
  Globe,
  Smartphone,
  Moon,
  Volume2,
  Database,
  HelpCircle,
  LogOut,
} from 'lucide-react-native';
import React, { useState } from 'react';
import { Alert } from 'react-native';

import { useAuth, useUserProfile } from '@/api/auth';
import {
  SettingsLayout,
  SettingsSection,
  SettingsToggleItem,
  SettingsActionItem,
} from '@/components/settings';

export default function SettingsPage() {
  const { signOut } = useAuth();
  const { userProfile } = useUserProfile();

  // Settings state - in a real app, these would come from API
  const [settings, setSettings] = useState({
    general: {
      darkMode: false,
      soundEnabled: true,
      pushNotifications: true,
      emailNotifications: true,
      language: 'pt',
    },
    privacy: {
      shareAnalytics: false,
      marketingEmails: false,
      dataProcessingConsent: true,
    },
  });

  const updateGeneralSetting = (key: string, value: boolean | string) => {
    setSettings(prev => ({
      ...prev,
      general: {
        ...prev.general,
        [key]: value,
      },
    }));
  };

  const updatePrivacySetting = (key: string, value: boolean) => {
    setSettings(prev => ({
      ...prev,
      privacy: {
        ...prev.privacy,
        [key]: value,
      },
    }));
  };

  const handleProfileEdit = () => {
    router.push('/profile');
  };

  const handleLanguageSettings = () => {
    Alert.alert('Language Settings', 'Language selection coming soon');
  };

  const handleHelpSupport = () => {
    router.push('/help');
  };

  const handlePrivacyPolicy = () => {
    router.push('/privacy-policy');
  };

  const handleSignOut = async () => {
    Alert.alert('Sign Out', 'Are you sure you want to sign out?', [
      {
        text: 'Cancel',
        style: 'cancel',
      },
      {
        text: 'Sign Out',
        style: 'destructive',
        onPress: () => signOut(),
      },
    ]);
  };

  return (
    <SettingsLayout title="Settings" subtitle="Manage your account and preferences">
      {/* Profile Section */}
      <SettingsSection title="Profile" description="Manage your account information" icon={User}>
        <SettingsActionItem
          title="Edit Profile"
          description="Update your personal information and avatar"
          icon={User}
          onPress={handleProfileEdit}
        />
        <SettingsActionItem
          title="Language & Region"
          description="Change language and regional settings"
          icon={Globe}
          onPress={handleLanguageSettings}
        />
      </SettingsSection>

      {/* Notifications Section */}
      <SettingsSection
        title="Notifications"
        description="Control how you receive alerts and updates"
        icon={Bell}
      >
        <SettingsToggleItem
          title="Push Notifications"
          description="Receive notifications on your mobile device"
          icon={Bell}
          value={settings.general.pushNotifications}
          onValueChange={value => updateGeneralSetting('pushNotifications', value)}
        />
        <SettingsToggleItem
          title="Email Notifications"
          description="Receive updates and alerts via email"
          icon={Bell}
          value={settings.general.emailNotifications}
          onValueChange={value => updateGeneralSetting('emailNotifications', value)}
        />
        <SettingsToggleItem
          title="Sound Effects"
          description="Play sounds for notifications and interactions"
          icon={Volume2}
          value={settings.general.soundEnabled}
          onValueChange={value => updateGeneralSetting('soundEnabled', value)}
        />
      </SettingsSection>

      {/* Appearance Section */}
      <SettingsSection
        title="Appearance"
        description="Customize the look and feel of the app"
        icon={Moon}
      >
        <SettingsToggleItem
          title="Dark Mode"
          description="Use dark theme for better viewing in low light"
          icon={Moon}
          value={settings.general.darkMode}
          onValueChange={value => updateGeneralSetting('darkMode', value)}
        />
      </SettingsSection>

      {/* Privacy & Data Section */}
      <SettingsSection
        title="Privacy & Data"
        description="Control your privacy and data sharing preferences"
        icon={Shield}
      >
        <SettingsToggleItem
          title="Share Anonymous Analytics"
          description="Help improve the app with anonymous usage data"
          icon={Database}
          value={settings.privacy.shareAnalytics}
          onValueChange={value => updatePrivacySetting('shareAnalytics', value)}
        />
        <SettingsToggleItem
          title="Marketing Emails"
          description="Receive updates about new features and promotions"
          icon={Bell}
          value={settings.privacy.marketingEmails}
          onValueChange={value => updatePrivacySetting('marketingEmails', value)}
        />
        <SettingsActionItem
          title="Privacy Policy"
          description="Review our privacy policy and data handling"
          icon={Shield}
          onPress={handlePrivacyPolicy}
        />
      </SettingsSection>

      {/* Support Section */}
      <SettingsSection
        title="Support"
        description="Get help and manage your account"
        icon={HelpCircle}
      >
        <SettingsActionItem
          title="Help & Support"
          description="Get help, report issues, or contact support"
          icon={HelpCircle}
          onPress={handleHelpSupport}
        />
        <SettingsActionItem
          title="Sign Out"
          description="Sign out of your account"
          icon={LogOut}
          onPress={handleSignOut}
          showChevron={false}
        />
      </SettingsSection>
    </SettingsLayout>
  );
}
