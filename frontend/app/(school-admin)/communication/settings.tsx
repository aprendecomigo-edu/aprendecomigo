import { isWeb } from '@/utils/platform';
import {
  SettingsIcon,
  ClockIcon,
  MailIcon,
  BellIcon,
  SaveIcon,
  RefreshCwIcon,
  InfoIcon,
  CheckCircleIcon,
} from 'lucide-react-native';
import React, { useState, useCallback, useEffect } from 'react';
import { Alert } from 'react-native';

import MainLayout from '@/components/layouts/MainLayout';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Center } from '@/components/ui/center';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Input, InputField } from '@/components/ui/input';
import { ScrollView } from '@/components/ui/scroll-view';
import { Select, SelectContent, SelectItem, SelectTrigger } from '@/components/ui/select';
import { Spinner } from '@/components/ui/spinner';
import { Switch } from '@/components/ui/switch';
import { Text } from '@/components/ui/text';
import { Textarea, TextareaInput } from '@/components/ui/textarea';
import { VStack } from '@/components/ui/vstack';
import { useSchoolSettings } from '@/hooks/useSchoolSettings';

// Mock settings interface (would come from backend)
interface CommunicationSettings {
  id: number;
  school: number;

  // Email sending settings
  default_send_time: string;
  max_emails_per_day: number;
  retry_failed_emails: boolean;
  retry_attempts: number;
  retry_delay_hours: number;

  // Notification settings
  email_notifications_enabled: boolean;
  admin_notification_email: string;
  notify_on_delivery_failure: boolean;
  notify_on_low_engagement: boolean;
  engagement_threshold: number;

  // Sequence settings
  invitation_sequence_enabled: boolean;
  invitation_follow_up_days: number[];
  reminder_sequence_enabled: boolean;
  reminder_intervals_days: number[];

  // Template defaults
  default_invitation_template: number | null;
  default_reminder_template: number | null;
  default_welcome_template: number | null;

  // Rate limiting
  rate_limit_enabled: boolean;
  max_emails_per_hour: number;
  burst_limit: number;

  // Advanced settings
  track_email_opens: boolean;
  track_email_clicks: boolean;
  auto_suppress_bounces: boolean;
  suppress_after_bounces: number;

  created_at: string;
  updated_at: string;
}

const CommunicationSettingsPage = () => {
  // Mock settings state (in real app, this would come from API)
  const [settings, setSettings] = useState<CommunicationSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  // Mock data loading
  useEffect(() => {
    // Simulate API call
    setTimeout(() => {
      setSettings({
        id: 1,
        school: 1,
        default_send_time: '09:00',
        max_emails_per_day: 100,
        retry_failed_emails: true,
        retry_attempts: 3,
        retry_delay_hours: 24,
        email_notifications_enabled: true,
        admin_notification_email: 'admin@school.com',
        notify_on_delivery_failure: true,
        notify_on_low_engagement: true,
        engagement_threshold: 0.1,
        invitation_sequence_enabled: true,
        invitation_follow_up_days: [1, 3, 7],
        reminder_sequence_enabled: true,
        reminder_intervals_days: [1, 3],
        default_invitation_template: null,
        default_reminder_template: null,
        default_welcome_template: null,
        rate_limit_enabled: true,
        max_emails_per_hour: 50,
        burst_limit: 10,
        track_email_opens: true,
        track_email_clicks: true,
        auto_suppress_bounces: true,
        suppress_after_bounces: 3,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      });
      setLoading(false);
    }, 1000);
  }, []);

  // Update setting field
  const updateSetting = useCallback(
    (field: keyof CommunicationSettings, value: any) => {
      if (settings) {
        setSettings({
          ...settings,
          [field]: value,
        });
        setHasUnsavedChanges(true);
      }
    },
    [settings],
  );

  // Save settings
  const handleSaveSettings = useCallback(async () => {
    if (!settings) return;

    setSaving(true);
    setError(null);

    try {
      // Mock API call
      await new Promise(resolve => setTimeout(resolve, 1000));

      setHasUnsavedChanges(false);
      Alert.alert('Success', 'Communication settings saved successfully');
    } catch (err: any) {
      setError(err.message || 'Failed to save settings');
      Alert.alert('Error', 'Failed to save settings');
    } finally {
      setSaving(false);
    }
  }, [settings]);

  // Reset settings
  const handleResetSettings = useCallback(() => {
    Alert.alert('Reset Settings', 'Are you sure you want to discard all unsaved changes?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Reset',
        style: 'destructive',
        onPress: () => {
          // Reload settings
          setHasUnsavedChanges(false);
          // In real app, refetch from API
        },
      },
    ]);
  }, []);

  // Update follow-up days array
  const updateFollowUpDays = useCallback(
    (type: 'invitation' | 'reminder', index: number, value: string) => {
      if (!settings) return;

      const field = type === 'invitation' ? 'invitation_follow_up_days' : 'reminder_intervals_days';
      const currentArray = settings[field];
      const newArray = [...currentArray];
      newArray[index] = parseInt(value) || 0;

      updateSetting(field, newArray);
    },
    [settings, updateSetting],
  );

  // Add/remove follow-up day
  const addFollowUpDay = useCallback(
    (type: 'invitation' | 'reminder') => {
      if (!settings) return;

      const field = type === 'invitation' ? 'invitation_follow_up_days' : 'reminder_intervals_days';
      const currentArray = settings[field];

      updateSetting(field, [...currentArray, 1]);
    },
    [settings, updateSetting],
  );

  const removeFollowUpDay = useCallback(
    (type: 'invitation' | 'reminder', index: number) => {
      if (!settings) return;

      const field = type === 'invitation' ? 'invitation_follow_up_days' : 'reminder_intervals_days';
      const currentArray = settings[field];

      if (currentArray.length > 1) {
        const newArray = currentArray.filter((_, i) => i !== index);
        updateSetting(field, newArray);
      }
    },
    [settings, updateSetting],
  );

  // Loading state
  if (loading) {
    return (
      <MainLayout _title="Communication Settings">
        <Center className="flex-1">
          <VStack space="md" className="items-center">
            <Spinner size="large" />
            <Text className="text-gray-600">Loading settings...</Text>
          </VStack>
        </Center>
      </MainLayout>
    );
  }

  // Error state
  if (!settings && error) {
    return (
      <MainLayout _title="Communication Settings">
        <Center className="flex-1">
          <VStack space="md" className="items-center max-w-md">
            <Icon as={SettingsIcon} size="xl" className="text-red-400" />
            <Text className="text-red-600 font-semibold text-center">Error Loading Settings</Text>
            <Text className="text-gray-600 text-center">{error}</Text>
            <Button onPress={() => window.location.reload()} variant="outline">
              <ButtonText>Try Again</ButtonText>
            </Button>
          </VStack>
        </Center>
      </MainLayout>
    );
  }

  if (!settings) return null;

  return (
    <ScrollView
      showsVerticalScrollIndicator={false}
      contentContainerStyle={{
        paddingBottom: isWeb ? 0 : 100,
        flexGrow: 1,
      }}
      className="flex-1 bg-gray-50"
    >
      <VStack className="p-6" space="lg">
        {/* Header */}
        <HStack className="justify-between items-center">
          <VStack space="xs">
            <Heading size="xl" className="text-gray-900">
              Communication Settings
            </Heading>
            <Text className="text-gray-600">
              Configure how your school sends and manages email communications
            </Text>
          </VStack>

          <HStack space="sm">
            <Button
              onPress={handleSaveSettings}
              disabled={saving || !hasUnsavedChanges}
              className="bg-blue-600"
            >
              <HStack space="xs" className="items-center">
                <Icon as={SaveIcon} size="sm" className="text-white" />
                <ButtonText className="text-white">
                  {saving ? 'Saving...' : 'Save Settings'}
                </ButtonText>
              </HStack>
            </Button>
          </HStack>
        </HStack>

        {/* Error Display */}
        {error && (
          <Card className="p-4 bg-red-50 border-red-200">
            <HStack space="sm" className="items-start">
              <Icon as={InfoIcon} size="sm" className="text-red-600 mt-0.5" />
              <VStack space="xs" className="flex-1">
                <Text className="font-medium text-red-800">Error Saving Settings</Text>
                <Text className="text-sm text-red-600">{error}</Text>
              </VStack>
            </HStack>
          </Card>
        )}

        {/* Unsaved Changes Warning */}
        {hasUnsavedChanges && (
          <Card className="p-4 bg-orange-50 border-orange-200">
            <HStack className="justify-between items-center">
              <HStack space="sm" className="items-center flex-1">
                <Icon as={SaveIcon} size="sm" className="text-orange-600" />
                <Text className="font-medium text-orange-800">You have unsaved changes</Text>
              </HStack>
              <HStack space="sm">
                <Button onPress={handleSaveSettings} size="sm" className="bg-orange-600">
                  <ButtonText className="text-white">Save</ButtonText>
                </Button>
                <Button
                  onPress={handleResetSettings}
                  size="sm"
                  variant="outline"
                  className="border-orange-300"
                >
                  <ButtonText>Reset</ButtonText>
                </Button>
              </HStack>
            </HStack>
          </Card>
        )}

        {/* Email Sending Settings */}
        <Card className="p-6">
          <VStack space="lg">
            <VStack space="xs">
              <Heading size="md" className="text-gray-900">
                Email Sending
              </Heading>
              <Text className="text-gray-600">Configure when and how emails are sent</Text>
            </VStack>

            {/* Default Send Time */}
            <VStack space="sm">
              <Text className="font-medium text-gray-900">Default Send Time</Text>
              <Input className="max-w-xs">
                <InputField
                  type="time"
                  value={settings.default_send_time}
                  onChangeText={value => updateSetting('default_send_time', value)}
                />
              </Input>
              <Text className="text-xs text-gray-500">
                Preferred time to send emails (school's local timezone)
              </Text>
            </VStack>

            {/* Daily Email Limit */}
            <VStack space="sm">
              <Text className="font-medium text-gray-900">Daily Email Limit</Text>
              <Input className="max-w-xs">
                <InputField
                  type="number"
                  placeholder="100"
                  value={settings.max_emails_per_day.toString()}
                  onChangeText={value => updateSetting('max_emails_per_day', parseInt(value) || 0)}
                />
              </Input>
              <Text className="text-xs text-gray-500">
                Maximum number of emails to send per day
              </Text>
            </VStack>

            {/* Failed Email Retry */}
            <VStack space="md">
              <HStack className="justify-between items-center">
                <VStack space="xs" className="flex-1">
                  <Text className="font-medium text-gray-900">Retry Failed Emails</Text>
                  <Text className="text-xs text-gray-500">
                    Automatically retry sending failed emails
                  </Text>
                </VStack>
                <Switch
                  value={settings.retry_failed_emails}
                  onValueChange={value => updateSetting('retry_failed_emails', value)}
                />
              </HStack>

              {settings.retry_failed_emails && (
                <HStack space="md" className="ml-4">
                  <VStack space="xs" className="flex-1">
                    <Text className="text-sm text-gray-700">Retry Attempts</Text>
                    <Input>
                      <InputField
                        type="number"
                        placeholder="3"
                        value={settings.retry_attempts.toString()}
                        onChangeText={value =>
                          updateSetting('retry_attempts', parseInt(value) || 0)
                        }
                      />
                    </Input>
                  </VStack>
                  <VStack space="xs" className="flex-1">
                    <Text className="text-sm text-gray-700">Delay (hours)</Text>
                    <Input>
                      <InputField
                        type="number"
                        placeholder="24"
                        value={settings.retry_delay_hours.toString()}
                        onChangeText={value =>
                          updateSetting('retry_delay_hours', parseInt(value) || 0)
                        }
                      />
                    </Input>
                  </VStack>
                </HStack>
              )}
            </VStack>
          </VStack>
        </Card>

        {/* Notification Settings */}
        <Card className="p-6">
          <VStack space="lg">
            <VStack space="xs">
              <Heading size="md" className="text-gray-900">
                Notifications
              </Heading>
              <Text className="text-gray-600">Configure admin notifications and alerts</Text>
            </VStack>

            {/* Email Notifications */}
            <HStack className="justify-between items-center">
              <VStack space="xs" className="flex-1">
                <Text className="font-medium text-gray-900">Email Notifications</Text>
                <Text className="text-xs text-gray-500">
                  Receive email notifications about communication system events
                </Text>
              </VStack>
              <Switch
                value={settings.email_notifications_enabled}
                onValueChange={value => updateSetting('email_notifications_enabled', value)}
              />
            </HStack>

            {settings.email_notifications_enabled && (
              <>
                {/* Admin Email */}
                <VStack space="sm">
                  <Text className="font-medium text-gray-900">Admin Email</Text>
                  <Input>
                    <InputField
                      type="email"
                      placeholder="admin@school.com"
                      value={settings.admin_notification_email}
                      onChangeText={value => updateSetting('admin_notification_email', value)}
                    />
                  </Input>
                  <Text className="text-xs text-gray-500">
                    Email address to receive notifications
                  </Text>
                </VStack>

                {/* Delivery Failure Notifications */}
                <HStack className="justify-between items-center">
                  <VStack space="xs" className="flex-1">
                    <Text className="font-medium text-gray-900">Delivery Failure Alerts</Text>
                    <Text className="text-xs text-gray-500">
                      Get notified when emails fail to deliver
                    </Text>
                  </VStack>
                  <Switch
                    value={settings.notify_on_delivery_failure}
                    onValueChange={value => updateSetting('notify_on_delivery_failure', value)}
                  />
                </HStack>

                {/* Low Engagement Notifications */}
                <VStack space="md">
                  <HStack className="justify-between items-center">
                    <VStack space="xs" className="flex-1">
                      <Text className="font-medium text-gray-900">Low Engagement Alerts</Text>
                      <Text className="text-xs text-gray-500">
                        Get notified when email engagement is low
                      </Text>
                    </VStack>
                    <Switch
                      value={settings.notify_on_low_engagement}
                      onValueChange={value => updateSetting('notify_on_low_engagement', value)}
                    />
                  </HStack>

                  {settings.notify_on_low_engagement && (
                    <VStack space="xs" className="ml-4">
                      <Text className="text-sm text-gray-700">Engagement Threshold</Text>
                      <Input className="max-w-xs">
                        <InputField
                          type="number"
                          placeholder="0.1"
                          value={settings.engagement_threshold.toString()}
                          onChangeText={value =>
                            updateSetting('engagement_threshold', parseFloat(value) || 0)
                          }
                        />
                      </Input>
                      <Text className="text-xs text-gray-500">
                        Alert when open rate falls below this threshold (0.1 = 10%)
                      </Text>
                    </VStack>
                  )}
                </VStack>
              </>
            )}
          </VStack>
        </Card>

        {/* Email Sequences */}
        <Card className="p-6">
          <VStack space="lg">
            <VStack space="xs">
              <Heading size="md" className="text-gray-900">
                Email Sequences
              </Heading>
              <Text className="text-gray-600">
                Configure automated email sequences and follow-ups
              </Text>
            </VStack>

            {/* Invitation Sequence */}
            <VStack space="md">
              <HStack className="justify-between items-center">
                <VStack space="xs" className="flex-1">
                  <Text className="font-medium text-gray-900">Invitation Sequence</Text>
                  <Text className="text-xs text-gray-500">
                    Automatically send follow-up emails to teachers who haven't responded
                  </Text>
                </VStack>
                <Switch
                  value={settings.invitation_sequence_enabled}
                  onValueChange={value => updateSetting('invitation_sequence_enabled', value)}
                />
              </HStack>

              {settings.invitation_sequence_enabled && (
                <VStack space="sm" className="ml-4">
                  <Text className="text-sm text-gray-700">
                    Follow-up Schedule (days after invitation)
                  </Text>
                  <VStack space="xs">
                    {settings.invitation_follow_up_days.map((days, index) => (
                      <HStack key={index} space="sm" className="items-center">
                        <Input className="flex-1">
                          <InputField
                            type="number"
                            placeholder="1"
                            value={days.toString()}
                            onChangeText={value => updateFollowUpDays('invitation', index, value)}
                          />
                        </Input>
                        <Text className="text-sm text-gray-600">days</Text>
                        {settings.invitation_follow_up_days.length > 1 && (
                          <Button
                            size="sm"
                            variant="outline"
                            onPress={() => removeFollowUpDay('invitation', index)}
                          >
                            <ButtonText>Remove</ButtonText>
                          </Button>
                        )}
                      </HStack>
                    ))}
                    <Button
                      size="sm"
                      variant="outline"
                      onPress={() => addFollowUpDay('invitation')}
                      className="self-start"
                    >
                      <ButtonText>Add Follow-up</ButtonText>
                    </Button>
                  </VStack>
                </VStack>
              )}
            </VStack>

            {/* Reminder Sequence */}
            <VStack space="md">
              <HStack className="justify-between items-center">
                <VStack space="xs" className="flex-1">
                  <Text className="font-medium text-gray-900">Reminder Sequence</Text>
                  <Text className="text-xs text-gray-500">
                    Send reminders for incomplete profile setup or other tasks
                  </Text>
                </VStack>
                <Switch
                  value={settings.reminder_sequence_enabled}
                  onValueChange={value => updateSetting('reminder_sequence_enabled', value)}
                />
              </HStack>

              {settings.reminder_sequence_enabled && (
                <VStack space="sm" className="ml-4">
                  <Text className="text-sm text-gray-700">Reminder Intervals (days)</Text>
                  <VStack space="xs">
                    {settings.reminder_intervals_days.map((days, index) => (
                      <HStack key={index} space="sm" className="items-center">
                        <Input className="flex-1">
                          <InputField
                            type="number"
                            placeholder="1"
                            value={days.toString()}
                            onChangeText={value => updateFollowUpDays('reminder', index, value)}
                          />
                        </Input>
                        <Text className="text-sm text-gray-600">days</Text>
                        {settings.reminder_intervals_days.length > 1 && (
                          <Button
                            size="sm"
                            variant="outline"
                            onPress={() => removeFollowUpDay('reminder', index)}
                          >
                            <ButtonText>Remove</ButtonText>
                          </Button>
                        )}
                      </HStack>
                    ))}
                    <Button
                      size="sm"
                      variant="outline"
                      onPress={() => addFollowUpDay('reminder')}
                      className="self-start"
                    >
                      <ButtonText>Add Reminder</ButtonText>
                    </Button>
                  </VStack>
                </VStack>
              )}
            </VStack>
          </VStack>
        </Card>

        {/* Rate Limiting */}
        <Card className="p-6">
          <VStack space="lg">
            <VStack space="xs">
              <Heading size="md" className="text-gray-900">
                Rate Limiting
              </Heading>
              <Text className="text-gray-600">
                Control email sending rate to prevent overwhelming recipients
              </Text>
            </VStack>

            {/* Rate Limiting Enable */}
            <HStack className="justify-between items-center">
              <VStack space="xs" className="flex-1">
                <Text className="font-medium text-gray-900">Enable Rate Limiting</Text>
                <Text className="text-xs text-gray-500">
                  Limit the number of emails sent per hour
                </Text>
              </VStack>
              <Switch
                value={settings.rate_limit_enabled}
                onValueChange={value => updateSetting('rate_limit_enabled', value)}
              />
            </HStack>

            {settings.rate_limit_enabled && (
              <>
                <VStack space="sm">
                  <Text className="font-medium text-gray-900">Max Emails per Hour</Text>
                  <Input className="max-w-xs">
                    <InputField
                      type="number"
                      placeholder="50"
                      value={settings.max_emails_per_hour.toString()}
                      onChangeText={value =>
                        updateSetting('max_emails_per_hour', parseInt(value) || 0)
                      }
                    />
                  </Input>
                  <Text className="text-xs text-gray-500">
                    Maximum emails that can be sent in one hour
                  </Text>
                </VStack>

                <VStack space="sm">
                  <Text className="font-medium text-gray-900">Burst Limit</Text>
                  <Input className="max-w-xs">
                    <InputField
                      type="number"
                      placeholder="10"
                      value={settings.burst_limit.toString()}
                      onChangeText={value => updateSetting('burst_limit', parseInt(value) || 0)}
                    />
                  </Input>
                  <Text className="text-xs text-gray-500">
                    Maximum emails that can be sent in quick succession
                  </Text>
                </VStack>
              </>
            )}
          </VStack>
        </Card>

        {/* Advanced Settings */}
        <Card className="p-6">
          <VStack space="lg">
            <VStack space="xs">
              <Heading size="md" className="text-gray-900">
                Advanced Settings
              </Heading>
              <Text className="text-gray-600">Additional configuration options</Text>
            </VStack>

            {/* Email Tracking */}
            <HStack className="justify-between items-center">
              <VStack space="xs" className="flex-1">
                <Text className="font-medium text-gray-900">Track Email Opens</Text>
                <Text className="text-xs text-gray-500">
                  Track when recipients open emails for analytics
                </Text>
              </VStack>
              <Switch
                value={settings.track_email_opens}
                onValueChange={value => updateSetting('track_email_opens', value)}
              />
            </HStack>

            <HStack className="justify-between items-center">
              <VStack space="xs" className="flex-1">
                <Text className="font-medium text-gray-900">Track Email Clicks</Text>
                <Text className="text-xs text-gray-500">
                  Track when recipients click links in emails
                </Text>
              </VStack>
              <Switch
                value={settings.track_email_clicks}
                onValueChange={value => updateSetting('track_email_clicks', value)}
              />
            </HStack>

            {/* Bounce Management */}
            <VStack space="md">
              <HStack className="justify-between items-center">
                <VStack space="xs" className="flex-1">
                  <Text className="font-medium text-gray-900">Auto-suppress Bounces</Text>
                  <Text className="text-xs text-gray-500">
                    Automatically stop sending to email addresses that bounce
                  </Text>
                </VStack>
                <Switch
                  value={settings.auto_suppress_bounces}
                  onValueChange={value => updateSetting('auto_suppress_bounces', value)}
                />
              </HStack>

              {settings.auto_suppress_bounces && (
                <VStack space="xs" className="ml-4">
                  <Text className="text-sm text-gray-700">Suppress after bounces</Text>
                  <Input className="max-w-xs">
                    <InputField
                      type="number"
                      placeholder="3"
                      value={settings.suppress_after_bounces.toString()}
                      onChangeText={value =>
                        updateSetting('suppress_after_bounces', parseInt(value) || 0)
                      }
                    />
                  </Input>
                  <Text className="text-xs text-gray-500">
                    Number of bounces before suppressing the email address
                  </Text>
                </VStack>
              )}
            </VStack>
          </VStack>
        </Card>

        {/* Save Section */}
        <Card className="p-6">
          <VStack space="md">
            <Text className="font-medium text-gray-900">Save Your Settings</Text>

            <HStack space="sm" className="flex-wrap">
              <Button
                onPress={handleSaveSettings}
                disabled={saving || !hasUnsavedChanges}
                className="bg-blue-600 flex-1"
              >
                <ButtonText className="text-white">
                  {saving ? 'Saving Settings...' : 'Save All Settings'}
                </ButtonText>
              </Button>

              {hasUnsavedChanges && (
                <Button onPress={handleResetSettings} variant="outline" className="flex-1">
                  <HStack space="xs" className="items-center">
                    <Icon as={RefreshCwIcon} size="sm" className="text-gray-600" />
                    <ButtonText>Reset Changes</ButtonText>
                  </HStack>
                </Button>
              )}
            </HStack>

            <Text className="text-xs text-gray-500 text-center">
              Settings will take effect immediately after saving
            </Text>
          </VStack>
        </Card>
      </VStack>
    </ScrollView>
  );
};

const CommunicationSettingsPageWrapper = () => {
  return (
    <MainLayout _title="Communication Settings">
      <CommunicationSettingsPage />
    </MainLayout>
  );
};

export default CommunicationSettingsPageWrapper;
