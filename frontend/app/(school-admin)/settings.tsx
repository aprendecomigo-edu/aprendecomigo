import { router } from 'expo-router';
import {
  Settings,
  School,
  Bell,
  Users,
  Clock,
  Shield,
  Palette,
  Globe,
  CreditCard,
  Database,
  Smartphone,
} from 'lucide-react-native';
import React, { useEffect, useState } from 'react';
import { Alert } from 'react-native';

import { useUserProfile } from '@/api/auth';
import { getUserAdminSchools, SchoolMembership } from '@/api/userApi';
import {
  SettingsLayout,
  SettingsSection,
  SettingsToggleItem,
  SettingsActionItem,
} from '@/components/settings';
import { Center } from '@/components/ui/center';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

export default function SchoolSettingsPage() {
  const [adminSchools, setAdminSchools] = useState<SchoolMembership[]>([]);
  const [selectedSchoolId, setSelectedSchoolId] = useState<number | null>(null);
  const [schoolsLoading, setSchoolsLoading] = useState(true);
  const [authorizationError, setAuthorizationError] = useState<string | null>(null);
  const { userProfile } = useUserProfile();

  // Settings state - in a real app, these would come from API
  const [settings, setSettings] = useState({
    notifications: {
      emailNotifications: true,
      smsNotifications: false,
      pushNotifications: true,
      classReminders: true,
      adminAlerts: true,
    },
    permissions: {
      allowStudentSelfEnrollment: false,
      requireParentApproval: true,
      autoAssignTeachers: false,
      enableGuestAccess: false,
    },
    privacy: {
      gdprCompliance: true,
      allowDataExport: true,
      requireDataConsent: true,
      enableAnalytics: true,
    },
  });

  // Load admin schools on mount
  useEffect(() => {
    const loadAdminSchools = async () => {
      try {
        setSchoolsLoading(true);
        const schools = await getUserAdminSchools();
        setAdminSchools(schools);

        if (schools.length > 0) {
          setSelectedSchoolId(schools[0].school.id);
          setAuthorizationError(null);
        } else {
          setAuthorizationError(
            'You do not have administrative access to any schools. Please contact your system administrator.'
          );
          setSelectedSchoolId(null);
        }
      } catch (error) {
        setAuthorizationError(
          'Failed to load school information. Please try again or contact support.'
        );
        setSelectedSchoolId(null);
        setAdminSchools([]);
      } finally {
        setSchoolsLoading(false);
      }
    };

    if (userProfile) {
      loadAdminSchools();
    }
  }, [userProfile]);

  const updateNotificationSetting = (key: string, value: boolean) => {
    setSettings(prev => ({
      ...prev,
      notifications: {
        ...prev.notifications,
        [key]: value,
      },
    }));
  };

  const updatePermissionSetting = (key: string, value: boolean) => {
    setSettings(prev => ({
      ...prev,
      permissions: {
        ...prev.permissions,
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

  const handleSchoolProfileEdit = () => {
    router.push('/(school-admin)/profile');
  };

  const handleAdvancedSettings = () => {
    // TODO: Navigate to advanced settings form
    Alert.alert('Advanced Settings', 'Advanced settings panel coming soon');
  };

  const handleBillingSettings = () => {
    router.push('/(school-admin)/billing');
  };

  const handleIntegrations = () => {
    router.push('/(school-admin)/integrations');
  };

  if (schoolsLoading) {
    return (
      <Center className="flex-1 bg-gradient-page">
        <VStack space="md" className="items-center">
          <Spinner size="large" />
          <Text>Loading school settings...</Text>
        </VStack>
      </Center>
    );
  }

  if (authorizationError) {
    return (
      <SettingsLayout title="Settings" subtitle="Access Denied">
        <Center className="flex-1">
          <VStack space="lg" className="items-center px-6 max-w-md">
            <Text className="text-center text-gray-600">{authorizationError}</Text>
          </VStack>
        </Center>
      </SettingsLayout>
    );
  }

  const currentSchool = adminSchools.find(s => s.school.id === selectedSchoolId)?.school;

  return (
    <SettingsLayout
      title="School Settings"
      subtitle={currentSchool?.name || 'Configure your school'}
    >
      {/* School Profile Section */}
      <SettingsSection
        title="School Profile"
        description="Manage your school information and branding"
        icon={School}
      >
        <SettingsActionItem
          title="Edit School Profile"
          description="Update school name, address, and contact details"
          icon={School}
          onPress={handleSchoolProfileEdit}
        />
        <SettingsActionItem
          title="Branding & Appearance"
          description="Customize colors, logo, and visual identity"
          icon={Palette}
          onPress={() => router.push('/(school-admin)/branding')}
        />
      </SettingsSection>

      {/* Notifications Section */}
      <SettingsSection
        title="Notifications"
        description="Control how and when you receive alerts"
        icon={Bell}
      >
        <SettingsToggleItem
          title="Email Notifications"
          description="Receive updates and alerts via email"
          icon={Bell}
          value={settings.notifications.emailNotifications}
          onValueChange={value => updateNotificationSetting('emailNotifications', value)}
        />
        <SettingsToggleItem
          title="SMS Notifications"
          description="Get important alerts via SMS"
          icon={Smartphone}
          value={settings.notifications.smsNotifications}
          onValueChange={value => updateNotificationSetting('smsNotifications', value)}
        />
        <SettingsToggleItem
          title="Push Notifications"
          description="Receive notifications on your mobile device"
          icon={Bell}
          value={settings.notifications.pushNotifications}
          onValueChange={value => updateNotificationSetting('pushNotifications', value)}
        />
        <SettingsToggleItem
          title="Class Reminders"
          description="Automatic reminders before scheduled classes"
          icon={Clock}
          value={settings.notifications.classReminders}
          onValueChange={value => updateNotificationSetting('classReminders', value)}
        />
        <SettingsToggleItem
          title="Admin Alerts"
          description="Important administrative notifications"
          icon={Shield}
          value={settings.notifications.adminAlerts}
          onValueChange={value => updateNotificationSetting('adminAlerts', value)}
        />
      </SettingsSection>

      {/* Permissions & Access Section */}
      <SettingsSection
        title="Permissions & Access"
        description="Control user access and enrollment settings"
        icon={Users}
      >
        <SettingsToggleItem
          title="Student Self-Enrollment"
          description="Allow students to enroll themselves in classes"
          icon={Users}
          value={settings.permissions.allowStudentSelfEnrollment}
          onValueChange={value => updatePermissionSetting('allowStudentSelfEnrollment', value)}
        />
        <SettingsToggleItem
          title="Require Parent Approval"
          description="Parent consent required for student actions"
          icon={Shield}
          value={settings.permissions.requireParentApproval}
          onValueChange={value => updatePermissionSetting('requireParentApproval', value)}
        />
        <SettingsToggleItem
          title="Auto-Assign Teachers"
          description="Automatically assign teachers to new classes"
          icon={Users}
          value={settings.permissions.autoAssignTeachers}
          onValueChange={value => updatePermissionSetting('autoAssignTeachers', value)}
        />
        <SettingsToggleItem
          title="Guest Access"
          description="Allow guest users to view public content"
          icon={Globe}
          value={settings.permissions.enableGuestAccess}
          onValueChange={value => updatePermissionSetting('enableGuestAccess', value)}
        />
      </SettingsSection>

      {/* Privacy & Data Section */}
      <SettingsSection
        title="Privacy & Data"
        description="Manage data protection and compliance settings"
        icon={Shield}
      >
        <SettingsToggleItem
          title="GDPR Compliance"
          description="Enable GDPR compliance features"
          icon={Shield}
          value={settings.privacy.gdprCompliance}
          onValueChange={value => updatePrivacySetting('gdprCompliance', value)}
        />
        <SettingsToggleItem
          title="Allow Data Export"
          description="Users can request and download their data"
          icon={Database}
          value={settings.privacy.allowDataExport}
          onValueChange={value => updatePrivacySetting('allowDataExport', value)}
        />
        <SettingsToggleItem
          title="Require Data Consent"
          description="Explicit consent required for data processing"
          icon={Shield}
          value={settings.privacy.requireDataConsent}
          onValueChange={value => updatePrivacySetting('requireDataConsent', value)}
        />
        <SettingsToggleItem
          title="Analytics"
          description="Collect anonymous usage data to improve the platform"
          icon={Database}
          value={settings.privacy.enableAnalytics}
          onValueChange={value => updatePrivacySetting('enableAnalytics', value)}
        />
      </SettingsSection>

      {/* Advanced Settings Section */}
      <SettingsSection
        title="Advanced Settings"
        description="Additional configuration options"
        icon={Settings}
      >
        <SettingsActionItem
          title="Billing & Payments"
          description="Manage billing information and payment settings"
          icon={CreditCard}
          onPress={handleBillingSettings}
        />
        <SettingsActionItem
          title="Integrations"
          description="Connect with external tools and services"
          icon={Globe}
          onPress={handleIntegrations}
        />
        <SettingsActionItem
          title="Advanced Configuration"
          description="Educational systems, schedules, and detailed settings"
          icon={Settings}
          onPress={handleAdvancedSettings}
          badge={{ text: 'Pro', variant: 'solid', action: 'primary' }}
        />
      </SettingsSection>
    </SettingsLayout>
  );
}
