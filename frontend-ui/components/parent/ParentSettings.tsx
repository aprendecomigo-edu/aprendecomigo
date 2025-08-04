/**
 * ParentSettings Component
 *
 * Parent account settings including notification preferences,
 * family budget controls, and account management options.
 */

import React, { useState } from 'react';
import { router } from 'expo-router';
import { Alert } from 'react-native';
import {
  Bell,
  Users,
  CreditCard,
  Shield,
  Clock,
  Settings,
  Baby,
  DollarSign,
  Smartphone,
  Mail,
} from 'lucide-react-native';

import {
  SettingsLayout,
  SettingsSection,
  SettingsToggleItem,
  SettingsActionItem,
} from '@/components/settings';

export const ParentSettings: React.FC = () => {
  // Settings state - in a real app, these would come from API
  const [settings, setSettings] = useState({
    notifications: {
      emailUpdates: true,
      smsAlerts: false,
      pushNotifications: true,
      classReminders: true,
      progressReports: true,
      paymentReminders: true,
    },
    privacy: {
      shareProgressWithTeachers: true,
      allowDirectTeacherContact: true,
      shareAnalytics: false,
      marketingEmails: false,
    },
    budget: {
      monthlyBudgetAlerts: true,
      sessionLimitAlerts: true,
      autoTopUp: false,
    },
  });

  const updateNotificationSetting = (key: string, value: boolean) => {
    setSettings(prev => ({
      ...prev,
      notifications: {
        ...prev.notifications,
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

  const updateBudgetSetting = (key: string, value: boolean) => {
    setSettings(prev => ({
      ...prev,
      budget: {
        ...prev.budget,
        [key]: value,
      },
    }));
  };

  const handleChildrenManagement = () => {
    router.push('/(parent)/children');
  };

  const handlePaymentMethods = () => {
    router.push('/(parent)/payment-methods');
  };

  const handleBudgetSettings = () => {
    router.push('/(parent)/budget');
  };

  const handlePrivacySettings = () => {
    Alert.alert('Privacy Settings', 'Advanced privacy settings coming soon');
  };

  const handleAccountSettings = () => {
    router.push('/(parent)/account');
  };

  return (
    <SettingsLayout 
      title="Parent Settings" 
      subtitle="Manage your family account preferences"
    >
      {/* Children & Family Section */}
      <SettingsSection
        title="Children & Family"
        description="Manage your children's accounts and permissions"
        icon={Baby}
      >
        <SettingsActionItem
          title="Manage Children"
          description="Add, edit, or remove children from your account"
          icon={Users}
          onPress={handleChildrenManagement}
        />
        <SettingsActionItem
          title="Family Budget"
          description="Set spending limits and budget alerts"
          icon={DollarSign}
          onPress={handleBudgetSettings}
        />
      </SettingsSection>

      {/* Notifications Section */}
      <SettingsSection
        title="Notifications"
        description="Control how you receive updates about your children"
        icon={Bell}
      >
        <SettingsToggleItem
          title="Email Updates"
          description="Receive updates and reports via email"
          icon={Mail}
          value={settings.notifications.emailUpdates}
          onValueChange={(value) => updateNotificationSetting('emailUpdates', value)}
        />
        <SettingsToggleItem
          title="SMS Alerts"
          description="Get important alerts via SMS"
          icon={Smartphone}
          value={settings.notifications.smsAlerts}
          onValueChange={(value) => updateNotificationSetting('smsAlerts', value)}
        />
        <SettingsToggleItem
          title="Push Notifications"
          description="Receive notifications on your mobile device"
          icon={Bell}
          value={settings.notifications.pushNotifications}
          onValueChange={(value) => updateNotificationSetting('pushNotifications', value)}
        />
        <SettingsToggleItem
          title="Class Reminders"
          description="Reminders before your child's scheduled classes"
          icon={Clock}
          value={settings.notifications.classReminders}
          onValueChange={(value) => updateNotificationSetting('classReminders', value)}
        />
        <SettingsToggleItem
          title="Progress Reports"
          description="Weekly and monthly progress updates"
          icon={Bell}
          value={settings.notifications.progressReports}
          onValueChange={(value) => updateNotificationSetting('progressReports', value)}
        />
        <SettingsToggleItem
          title="Payment Reminders"
          description="Alerts about upcoming payments and low balance"
          icon={CreditCard}
          value={settings.notifications.paymentReminders}
          onValueChange={(value) => updateNotificationSetting('paymentReminders', value)}
        />
      </SettingsSection>

      {/* Budget & Payments Section */}
      <SettingsSection
        title="Budget & Payments"
        description="Manage your family's learning budget and payment preferences"
        icon={CreditCard}
      >
        <SettingsToggleItem
          title="Monthly Budget Alerts"
          description="Notify when approaching monthly spending limit"
          icon={DollarSign}
          value={settings.budget.monthlyBudgetAlerts}
          onValueChange={(value) => updateBudgetSetting('monthlyBudgetAlerts', value)}
        />
        <SettingsToggleItem
          title="Session Limit Alerts"
          description="Notify when child reaches session limits"
          icon={Clock}
          value={settings.budget.sessionLimitAlerts}
          onValueChange={(value) => updateBudgetSetting('sessionLimitAlerts', value)}
        />
        <SettingsToggleItem
          title="Auto Top-Up"
          description="Automatically add funds when balance is low"
          icon={CreditCard}
          value={settings.budget.autoTopUp}
          onValueChange={(value) => updateBudgetSetting('autoTopUp', value)}
        />
        <SettingsActionItem
          title="Payment Methods"
          description="Manage credit cards and payment options"
          icon={CreditCard}
          onPress={handlePaymentMethods}
        />
      </SettingsSection>

      {/* Privacy & Sharing Section */}
      <SettingsSection
        title="Privacy & Sharing"
        description="Control how your family's information is shared"
        icon={Shield}
      >
        <SettingsToggleItem
          title="Share Progress with Teachers"
          description="Allow teachers to see detailed progress reports"
          icon={Users}
          value={settings.privacy.shareProgressWithTeachers}
          onValueChange={(value) => updatePrivacySetting('shareProgressWithTeachers', value)}
        />
        <SettingsToggleItem
          title="Direct Teacher Contact"
          description="Allow teachers to contact you directly"
          icon={Mail}
          value={settings.privacy.allowDirectTeacherContact}
          onValueChange={(value) => updatePrivacySetting('allowDirectTeacherContact', value)}
        />
        <SettingsToggleItem
          title="Anonymous Analytics"
          description="Help improve the platform with anonymous usage data"
          icon={Shield}
          value={settings.privacy.shareAnalytics}
          onValueChange={(value) => updatePrivacySetting('shareAnalytics', value)}
        />
        <SettingsToggleItem
          title="Marketing Emails"
          description="Receive updates about new features and promotions"
          icon={Mail}
          value={settings.privacy.marketingEmails}
          onValueChange={(value) => updatePrivacySetting('marketingEmails', value)}
        />
      </SettingsSection>

      {/* Account Settings Section */}
      <SettingsSection
        title="Account Settings"
        description="Manage your account preferences and security"
        icon={Settings}
      >
        <SettingsActionItem
          title="Account Information"
          description="Update your personal details and contact info"
          icon={Settings}
          onPress={handleAccountSettings}
        />
        <SettingsActionItem
          title="Privacy Policy"
          description="Review our privacy policy and data handling"
          icon={Shield}
          onPress={handlePrivacySettings}
        />
      </SettingsSection>
    </SettingsLayout>
  );
};
