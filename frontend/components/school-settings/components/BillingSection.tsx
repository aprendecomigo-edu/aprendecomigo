import React, { memo } from 'react';
import { Controller, Control, FieldErrors } from 'react-hook-form';

import type { SchoolSettingsFormData } from '../types';

import { Box } from '@/components/ui/box';
import {
  FormControl,
  FormControlLabel,
  FormControlHelper,
  FormControlError,
  FormControlErrorIcon,
  FormControlErrorText,
} from '@/components/ui/form-control';
import { Heading } from '@/components/ui/heading';
import { Icon, AlertCircleIcon } from '@/components/ui/icon';
import { Input, InputField } from '@/components/ui/input';
import { Text } from '@/components/ui/text';
import { Textarea, TextareaInput } from '@/components/ui/textarea';
import { VStack } from '@/components/ui/vstack';

interface BillingSectionProps {
  control: Control<SchoolSettingsFormData>;
  errors: FieldErrors<SchoolSettingsFormData>;
}

export const BillingSection = memo<BillingSectionProps>(({ control, errors }) => {
  return (
    <VStack space="md">
      <Heading size="lg">Billing Configuration</Heading>

      <VStack space="md" className="md:flex-row md:space-x-4 md:space-y-0">
        <Box className="flex-1">
          <Controller
            control={control}
            name="settings.billing_contact_name"
            render={({ field: { onChange, onBlur, value } }) => (
              <FormControl>
                <FormControlLabel>
                  <Text>Billing Contact Name</Text>
                </FormControlLabel>
                <Input>
                  <InputField
                    placeholder="John Doe"
                    onBlur={onBlur}
                    onChangeText={onChange}
                    value={value}
                  />
                </Input>
              </FormControl>
            )}
          />
        </Box>

        <Box className="flex-1">
          <Controller
            control={control}
            name="settings.billing_contact_email"
            render={({ field: { onChange, onBlur, value } }) => (
              <FormControl isInvalid={!!errors.settings?.billing_contact_email}>
                <FormControlLabel>
                  <Text>Billing Contact Email</Text>
                </FormControlLabel>
                <Input>
                  <InputField
                    placeholder="billing@school.com"
                    onBlur={onBlur}
                    onChangeText={onChange}
                    value={value}
                    keyboardType="email-address"
                  />
                </Input>
                <FormControlError>
                  <FormControlErrorIcon as={AlertCircleIcon} />
                  <FormControlErrorText>
                    {errors.settings?.billing_contact_email?.message}
                  </FormControlErrorText>
                </FormControlError>
              </FormControl>
            )}
          />
        </Box>
      </VStack>

      <Controller
        control={control}
        name="settings.billing_address"
        render={({ field: { onChange, onBlur, value } }) => (
          <FormControl>
            <FormControlLabel>
              <Text>Billing Address</Text>
            </FormControlLabel>
            <Textarea>
              <TextareaInput
                placeholder="Complete billing address for invoices"
                onBlur={onBlur}
                onChangeText={onChange}
                value={value}
              />
            </Textarea>
          </FormControl>
        )}
      />

      <Controller
        control={control}
        name="settings.tax_id"
        render={({ field: { onChange, onBlur, value } }) => (
          <FormControl>
            <FormControlLabel>
              <Text>Tax ID / VAT Number</Text>
            </FormControlLabel>
            <Input>
              <InputField
                placeholder="PT123456789"
                onBlur={onBlur}
                onChangeText={onChange}
                value={value}
              />
            </Input>
            <FormControlHelper>
              <Text size="sm">Tax identification number for billing purposes</Text>
            </FormControlHelper>
          </FormControl>
        )}
      />
    </VStack>
  );
});

BillingSection.displayName = 'BillingSection';
