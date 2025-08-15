import React, { memo } from 'react';
import { Controller, Control, FieldErrors } from 'react-hook-form';

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

import type { SchoolSettingsFormData } from '../types';

interface ProfileSectionProps {
  control: Control<SchoolSettingsFormData>;
  errors: FieldErrors<SchoolSettingsFormData>;
}

export const ProfileSection = memo<ProfileSectionProps>(({ control, errors }) => {
  return (
    <VStack space="md">
      <Heading size="lg">School Profile</Heading>

      <Controller
        control={control}
        name="school_profile.name"
        render={({ field: { onChange, onBlur, value } }) => (
          <FormControl isInvalid={!!errors.school_profile?.name}>
            <FormControlLabel>
              <Text>School Name *</Text>
            </FormControlLabel>
            <Input>
              <InputField
                placeholder="Enter school name"
                onBlur={onBlur}
                onChangeText={onChange}
                value={value}
              />
            </Input>
            <FormControlError>
              <FormControlErrorIcon as={AlertCircleIcon} />
              <FormControlErrorText>{errors.school_profile?.name?.message}</FormControlErrorText>
            </FormControlError>
          </FormControl>
        )}
      />

      <Controller
        control={control}
        name="school_profile.description"
        render={({ field: { onChange, onBlur, value } }) => (
          <FormControl>
            <FormControlLabel>
              <Text>Description</Text>
            </FormControlLabel>
            <Textarea>
              <TextareaInput
                placeholder="Brief description of your school"
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
        name="school_profile.address"
        render={({ field: { onChange, onBlur, value } }) => (
          <FormControl>
            <FormControlLabel>
              <Text>Address</Text>
            </FormControlLabel>
            <Textarea>
              <TextareaInput
                placeholder="School address"
                onBlur={onBlur}
                onChangeText={onChange}
                value={value}
              />
            </Textarea>
          </FormControl>
        )}
      />

      <VStack space="md" className="md:flex-row md:space-x-4 md:space-y-0">
        <Box className="flex-1">
          <Controller
            control={control}
            name="school_profile.contact_email"
            render={({ field: { onChange, onBlur, value } }) => (
              <FormControl isInvalid={!!errors.school_profile?.contact_email}>
                <FormControlLabel>
                  <Text>Contact Email</Text>
                </FormControlLabel>
                <Input>
                  <InputField
                    placeholder="contact@school.com"
                    onBlur={onBlur}
                    onChangeText={onChange}
                    value={value}
                    keyboardType="email-address"
                  />
                </Input>
                <FormControlError>
                  <FormControlErrorIcon as={AlertCircleIcon} />
                  <FormControlErrorText>
                    {errors.school_profile?.contact_email?.message}
                  </FormControlErrorText>
                </FormControlError>
              </FormControl>
            )}
          />
        </Box>

        <Box className="flex-1">
          <Controller
            control={control}
            name="school_profile.phone_number"
            render={({ field: { onChange, onBlur, value } }) => (
              <FormControl>
                <FormControlLabel>
                  <Text>Phone Number</Text>
                </FormControlLabel>
                <Input>
                  <InputField
                    placeholder="+351 123 456 789"
                    onBlur={onBlur}
                    onChangeText={onChange}
                    value={value}
                    keyboardType="phone-pad"
                  />
                </Input>
              </FormControl>
            )}
          />
        </Box>
      </VStack>

      <Controller
        control={control}
        name="school_profile.website"
        render={({ field: { onChange, onBlur, value } }) => (
          <FormControl isInvalid={!!errors.school_profile?.website}>
            <FormControlLabel>
              <Text>Website</Text>
            </FormControlLabel>
            <Input>
              <InputField
                placeholder="https://www.school.com"
                onBlur={onBlur}
                onChangeText={onChange}
                value={value}
                keyboardType="url"
              />
            </Input>
            <FormControlError>
              <FormControlErrorIcon as={AlertCircleIcon} />
              <FormControlErrorText>{errors.school_profile?.website?.message}</FormControlErrorText>
            </FormControlError>
          </FormControl>
        )}
      />

      <VStack space="md" className="md:flex-row md:space-x-4 md:space-y-0">
        <Box className="flex-1">
          <Controller
            control={control}
            name="school_profile.primary_color"
            render={({ field: { onChange, onBlur, value } }) => (
              <FormControl isInvalid={!!errors.school_profile?.primary_color}>
                <FormControlLabel>
                  <Text>Primary Color</Text>
                </FormControlLabel>
                <Input>
                  <InputField
                    placeholder="#3B82F6"
                    onBlur={onBlur}
                    onChangeText={onChange}
                    value={value}
                  />
                </Input>
                <FormControlHelper>
                  <Text size="sm">Hex color code (e.g., #3B82F6)</Text>
                </FormControlHelper>
                <FormControlError>
                  <FormControlErrorIcon as={AlertCircleIcon} />
                  <FormControlErrorText>
                    {errors.school_profile?.primary_color?.message}
                  </FormControlErrorText>
                </FormControlError>
              </FormControl>
            )}
          />
        </Box>

        <Box className="flex-1">
          <Controller
            control={control}
            name="school_profile.secondary_color"
            render={({ field: { onChange, onBlur, value } }) => (
              <FormControl isInvalid={!!errors.school_profile?.secondary_color}>
                <FormControlLabel>
                  <Text>Secondary Color</Text>
                </FormControlLabel>
                <Input>
                  <InputField
                    placeholder="#1F2937"
                    onBlur={onBlur}
                    onChangeText={onChange}
                    value={value}
                  />
                </Input>
                <FormControlHelper>
                  <Text size="sm">Hex color code (e.g., #1F2937)</Text>
                </FormControlHelper>
                <FormControlError>
                  <FormControlErrorIcon as={AlertCircleIcon} />
                  <FormControlErrorText>
                    {errors.school_profile?.secondary_color?.message}
                  </FormControlErrorText>
                </FormControlError>
              </FormControl>
            )}
          />
        </Box>
      </VStack>
    </VStack>
  );
});

ProfileSection.displayName = 'ProfileSection';