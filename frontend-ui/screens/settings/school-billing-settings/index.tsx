import React, { useState, useEffect } from 'react';
import { Alert } from 'react-native';

import apiClient from '@/api/apiClient';
import MainLayout from '@/components/layouts/MainLayout';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import {
  FormControl,
  FormControlLabel,
  FormControlLabelText,
  FormControlHelper,
  FormControlHelperText,
  FormControlError,
  FormControlErrorText,
} from '@/components/ui/form-control';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { ChevronDownIcon } from '@/components/ui/icon';
import { Input, InputField } from '@/components/ui/input';
import { Radio, RadioGroup, RadioIndicator, RadioIcon, RadioLabel } from '@/components/ui/radio';
import {
  Select,
  SelectTrigger,
  SelectInput,
  SelectIcon,
  SelectPortal,
  SelectBackdrop,
  SelectContent,
  SelectDragIndicatorWrapper,
  SelectDragIndicator,
  SelectItem,
} from '@/components/ui/select';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

// Types based on the API specification
interface SchoolBillingSettings {
  id?: number;
  school: number;
  school_name?: string;
  trial_cost_absorption: 'school' | 'teacher' | 'split';
  teacher_payment_frequency: 'weekly' | 'biweekly' | 'monthly';
  payment_day_of_month: number;
  created_at?: string;
  updated_at?: string;
}

const SchoolBillingSettingsContent = () => {
  const [settings, setSettings] = useState<SchoolBillingSettings | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load current settings
  const loadSettings = async () => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await apiClient.get('/api/finances/school-billing-settings/current_school/');
      setSettings(response.data);
    } catch (err: any) {
      console.error('Error loading school billing settings:', err);

      if (err.response?.status === 404) {
        // No settings exist yet, set defaults
        setSettings({
          school: 1, // Will be set by backend
          trial_cost_absorption: 'school',
          teacher_payment_frequency: 'monthly',
          payment_day_of_month: 1,
        });
      } else {
        setError(err.response?.data?.error || 'Failed to load settings');
      }
    } finally {
      setIsLoading(false);
    }
  };

  // Save settings
  const saveSettings = async () => {
    if (!settings) return;

    try {
      setIsSaving(true);
      setError(null);

      if (settings.id) {
        // Update existing settings
        const response = await apiClient.patch(
          `/api/finances/school-billing-settings/${settings.id}/`,
          {
            trial_cost_absorption: settings.trial_cost_absorption,
            teacher_payment_frequency: settings.teacher_payment_frequency,
            payment_day_of_month: settings.payment_day_of_month,
          }
        );
        setSettings(response.data);
      } else {
        // Create new settings
        const response = await apiClient.post('/api/finances/school-billing-settings/', settings);
        setSettings(response.data);
      }

      Alert.alert('Success', 'Settings saved successfully!');
    } catch (err: any) {
      console.error('Error saving settings:', err);

      if (err.response?.data?.details) {
        // Handle validation errors
        const errors = Object.entries(err.response.data.details)
          .map(([field, messages]) => `${field}: ${(messages as string[]).join(', ')}`)
          .join('\n');
        setError(`Validation errors:\n${errors}`);
      } else {
        setError(err.response?.data?.error || 'Failed to save settings');
      }
    } finally {
      setIsSaving(false);
    }
  };

  // Update settings state
  const updateSetting = (key: keyof SchoolBillingSettings, value: string | number) => {
    if (!settings) return;

    setSettings({
      ...settings,
      [key]: value,
    });
  };

  useEffect(() => {
    loadSettings();
  }, []);

  if (isLoading) {
    return (
      <VStack className="flex-1 justify-center items-center p-6">
        <Spinner size="large" />
        <Text className="mt-4 text-typography-600">Loading settings...</Text>
      </VStack>
    );
  }

  if (error && !settings) {
    return (
      <VStack className="flex-1 justify-center items-center p-6">
        <Text className="text-error-600 text-center mb-4">{error}</Text>
        <Button onPress={loadSettings}>
          <ButtonText>Retry</ButtonText>
        </Button>
      </VStack>
    );
  }

  return (
    <VStack className="flex-1 p-6" space="lg">
      <VStack space="sm">
        <Heading size="xl" className="text-typography-900">
          School Billing Settings
        </Heading>
        <Text className="text-typography-600">
          Configure how your school handles teacher payments and trial classes.
        </Text>
      </VStack>

      {error && (
        <Box className="p-4 bg-error-50 border border-error-200 rounded-lg">
          <Text className="text-error-600">{error}</Text>
        </Box>
      )}

      <VStack space="xl">
        {/* Trial Class Cost Handling */}
        <FormControl>
          <FormControlLabel>
            <FormControlLabelText className="text-lg font-medium">
              Who pays for trial classes?
            </FormControlLabelText>
          </FormControlLabel>
          <FormControlHelper>
            <FormControlHelperText>
              Choose how trial class costs are handled when teachers conduct free introductory
              sessions.
            </FormControlHelperText>
          </FormControlHelper>

          <RadioGroup
            value={settings?.trial_cost_absorption || 'school'}
            onChange={(value: string) => updateSetting('trial_cost_absorption', value)}
            className="mt-3"
          >
            <VStack space="sm">
              <Radio value="school">
                <RadioIndicator className="mr-3">
                  <RadioIcon />
                </RadioIndicator>
                <RadioLabel className="flex-1">
                  <VStack space="xs">
                    <Text className="font-medium">School absorbs cost (recommended)</Text>
                    <Text className="text-sm text-typography-600">
                      Teacher gets €0 for trial classes. School covers the cost to attract new
                      students.
                    </Text>
                  </VStack>
                </RadioLabel>
              </Radio>

              <Radio value="teacher">
                <RadioIndicator className="mr-3">
                  <RadioIcon />
                </RadioIndicator>
                <RadioLabel className="flex-1">
                  <VStack space="xs">
                    <Text className="font-medium">Teacher absorbs cost</Text>
                    <Text className="text-sm text-typography-600">
                      Teacher gets normal rate but it's their loss. Not recommended.
                    </Text>
                  </VStack>
                </RadioLabel>
              </Radio>

              <Radio value="split">
                <RadioIndicator className="mr-3">
                  <RadioIcon />
                </RadioIndicator>
                <RadioLabel className="flex-1">
                  <VStack space="xs">
                    <Text className="font-medium">Split cost 50/50</Text>
                    <Text className="text-sm text-typography-600">
                      Teacher gets 50% of normal rate. School and teacher share the cost.
                    </Text>
                  </VStack>
                </RadioLabel>
              </Radio>
            </VStack>
          </RadioGroup>
        </FormControl>

        {/* Payment Frequency */}
        <FormControl>
          <FormControlLabel>
            <FormControlLabelText className="text-lg font-medium">
              How often do you pay teachers?
            </FormControlLabelText>
          </FormControlLabel>
          <FormControlHelper>
            <FormControlHelperText>
              Choose how frequently teachers receive their payments.
            </FormControlHelperText>
          </FormControlHelper>

          <Select
            selectedValue={settings?.teacher_payment_frequency || 'monthly'}
            onValueChange={(value: string) => updateSetting('teacher_payment_frequency', value)}
          >
            <SelectTrigger variant="outline" size="md" className="mt-2">
              <SelectInput placeholder="Select payment frequency" />
              <SelectIcon className="mr-3" as={ChevronDownIcon} />
            </SelectTrigger>
            <SelectPortal>
              <SelectBackdrop />
              <SelectContent>
                <SelectDragIndicatorWrapper>
                  <SelectDragIndicator />
                </SelectDragIndicatorWrapper>
                <SelectItem label="Weekly" value="weekly" />
                <SelectItem label="Bi-weekly" value="biweekly" />
                <SelectItem label="Monthly" value="monthly" />
              </SelectContent>
            </SelectPortal>
          </Select>
        </FormControl>

        {/* Payment Day */}
        <FormControl>
          <FormControlLabel>
            <FormControlLabelText className="text-lg font-medium">
              Payment day of month
            </FormControlLabelText>
          </FormControlLabel>
          <FormControlHelper>
            <FormControlHelperText>
              Which day of the month should teachers be paid? (1-28)
            </FormControlHelperText>
          </FormControlHelper>

          <Input className="mt-2">
            <InputField
              placeholder="Day of month (1-28)"
              value={settings?.payment_day_of_month?.toString() || '1'}
              onChangeText={(text: string) => {
                const day = parseInt(text, 10);
                if (!isNaN(day) && day >= 1 && day <= 28) {
                  updateSetting('payment_day_of_month', day);
                }
              }}
              keyboardType="numeric"
            />
          </Input>

          {settings?.payment_day_of_month &&
            (settings.payment_day_of_month < 1 || settings.payment_day_of_month > 28) && (
              <FormControlError>
                <FormControlErrorText>Payment day must be between 1 and 28.</FormControlErrorText>
              </FormControlError>
            )}
        </FormControl>

        {/* Save Button */}
        <HStack className="pt-4" space="md">
          <Button onPress={saveSettings} disabled={isSaving} className="flex-1" size="lg">
            {isSaving && <Spinner size="small" className="mr-2" />}
            <ButtonText>{isSaving ? 'Saving...' : 'Save Settings'}</ButtonText>
          </Button>

          <Button variant="outline" onPress={loadSettings} disabled={isSaving} size="lg">
            <ButtonText>Reset</ButtonText>
          </Button>
        </HStack>
      </VStack>
    </VStack>
  );
};

export const SchoolBillingSettings = () => {
  return (
    <MainLayout _title="Settings">
      <SchoolBillingSettingsContent />
    </MainLayout>
  );
};

export default SchoolBillingSettings;
