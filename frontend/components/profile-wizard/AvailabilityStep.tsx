import {
  Calendar,
  Clock,
  Globe,
  Plus,
  Minus,
  Settings,
  CheckCircle2,
  AlertCircle,
  Copy,
  Trash2,
  RotateCcw,
  Users,
  Timer,
} from 'lucide-react-native';
import React, { useState, useEffect } from 'react';
import { Platform, Dimensions } from 'react-native';

import { Badge, BadgeText } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import {
  FormControl,
  FormControlLabel,
  FormControlHelper,
  FormControlError,
} from '@/components/ui/form-control';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Input, InputField } from '@/components/ui/input';
import { Pressable } from '@/components/ui/pressable';
import { ScrollView } from '@/components/ui/scroll-view';
import {
  Select,
  SelectTrigger,
  SelectInput,
  SelectContent,
  SelectItem,
} from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

interface TimeSlot {
  start_time: string;
  end_time: string;
  timezone: string;
}

interface BookingPreferences {
  min_notice_hours: number;
  max_advance_days: number;
  session_duration_options: number[];
  auto_accept_bookings: boolean;
}

interface AvailabilityFormData {
  weekly_availability: {
    [key: string]: TimeSlot[];
  };
  booking_preferences: BookingPreferences;
  time_zone: string;
}

interface AvailabilityStepProps {
  formData: AvailabilityFormData;
  onFormDataChange: (data: Partial<AvailabilityFormData>) => void;
  validationErrors?: Record<string, string[]>;
  isLoading?: boolean;
}

const DAYS_OF_WEEK = [
  { key: 'monday', label: 'Monday', short: 'Mon' },
  { key: 'tuesday', label: 'Tuesday', short: 'Tue' },
  { key: 'wednesday', label: 'Wednesday', short: 'Wed' },
  { key: 'thursday', label: 'Thursday', short: 'Thu' },
  { key: 'friday', label: 'Friday', short: 'Fri' },
  { key: 'saturday', label: 'Saturday', short: 'Sat' },
  { key: 'sunday', label: 'Sunday', short: 'Sun' },
];

const TIMEZONES = [
  'Europe/Lisbon',
  'Europe/London',
  'Europe/Madrid',
  'Europe/Paris',
  'Europe/Berlin',
  'Europe/Rome',
  'Europe/Amsterdam',
  'America/New_York',
  'America/Los_Angeles',
  'America/Chicago',
  'America/Sao_Paulo',
  'America/Mexico_City',
  'Asia/Tokyo',
  'Asia/Shanghai',
  'Asia/Seoul',
  'Asia/Kolkata',
  'Australia/Sydney',
  'Australia/Melbourne',
];

const SESSION_DURATIONS = [30, 45, 60, 90, 120];

// Generate time options in 30-minute intervals
const generateTimeOptions = () => {
  const times: { value: string; label: string }[] = [];
  for (let hour = 0; hour < 24; hour++) {
    for (const minute of [0, 30]) {
      const timeString = `${hour.toString().padStart(2, '0')}:${minute
        .toString()
        .padStart(2, '0')}`;
      const displayTime = new Date(`2000-01-01T${timeString}`).toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
        hour12: true,
      });
      times.push({ value: timeString, label: displayTime });
    }
  }
  return times;
};

const TIME_OPTIONS = generateTimeOptions();

const { width: screenWidth } = Dimensions.get('window');
const isMobile = Platform.OS !== 'web' || screenWidth < 768;

export const AvailabilityStep: React.FC<AvailabilityStepProps> = ({
  formData,
  onFormDataChange,
  validationErrors = {},
  isLoading = false,
}) => {
  const [selectedDay, setSelectedDay] = useState<string>('monday');
  const [showAdvancedSettings, setShowAdvancedSettings] = useState(false);

  const handleFieldChange = (field: keyof AvailabilityFormData, value: any) => {
    onFormDataChange({ [field]: value });
  };

  const handleBookingPreferenceChange = (field: keyof BookingPreferences, value: any) => {
    handleFieldChange('booking_preferences', {
      ...formData.booking_preferences,
      [field]: value,
    });
  };

  const handleTimeSlotChange = (
    day: string,
    slotIndex: number,
    field: 'start_time' | 'end_time',
    value: string,
  ) => {
    const currentSlots = formData.weekly_availability[day] || [];
    const updatedSlots = [...currentSlots];
    updatedSlots[slotIndex] = {
      ...updatedSlots[slotIndex],
      [field]: value,
      timezone: formData.time_zone,
    };

    handleFieldChange('weekly_availability', {
      ...formData.weekly_availability,
      [day]: updatedSlots,
    });
  };

  const addTimeSlot = (day: string) => {
    const currentSlots = formData.weekly_availability[day] || [];
    const newSlot: TimeSlot = {
      start_time: '09:00',
      end_time: '10:00',
      timezone: formData.time_zone,
    };

    handleFieldChange('weekly_availability', {
      ...formData.weekly_availability,
      [day]: [...currentSlots, newSlot],
    });
  };

  const removeTimeSlot = (day: string, slotIndex: number) => {
    const currentSlots = formData.weekly_availability[day] || [];
    const updatedSlots = currentSlots.filter((_, index) => index !== slotIndex);

    handleFieldChange('weekly_availability', {
      ...formData.weekly_availability,
      [day]: updatedSlots,
    });
  };

  const copyDaySchedule = (fromDay: string, toDay: string) => {
    const sourceSlots = formData.weekly_availability[fromDay] || [];

    handleFieldChange('weekly_availability', {
      ...formData.weekly_availability,
      [toDay]: [...sourceSlots],
    });
  };

  const clearDaySchedule = (day: string) => {
    handleFieldChange('weekly_availability', {
      ...formData.weekly_availability,
      [day]: [],
    });
  };

  const applyToAllDays = (sourceDay: string) => {
    const sourceSlots = formData.weekly_availability[sourceDay] || [];
    const updatedAvailability: { [key: string]: TimeSlot[] } = {};

    DAYS_OF_WEEK.forEach(day => {
      updatedAvailability[day.key] = [...sourceSlots];
    });

    handleFieldChange('weekly_availability', updatedAvailability);
  };

  const toggleSessionDuration = (duration: number, enabled: boolean) => {
    const currentDurations = formData.booking_preferences.session_duration_options || [];
    const updatedDurations = enabled
      ? [...currentDurations, duration].sort((a, b) => a - b)
      : currentDurations.filter(d => d !== duration);

    handleBookingPreferenceChange('session_duration_options', updatedDurations);
  };

  const getTotalWeeklyHours = () => {
    let totalMinutes = 0;

    Object.values(formData.weekly_availability).forEach(daySlots => {
      daySlots.forEach(slot => {
        const start = new Date(`2000-01-01T${slot.start_time}`);
        const end = new Date(`2000-01-01T${slot.end_time}`);
        const diffMs = end.getTime() - start.getTime();
        totalMinutes += diffMs / (1000 * 60);
      });
    });

    return Math.round((totalMinutes / 60) * 10) / 10; // Round to 1 decimal place
  };

  const getDayHours = (day: string) => {
    const daySlots = formData.weekly_availability[day] || [];
    let totalMinutes = 0;

    daySlots.forEach(slot => {
      const start = new Date(`2000-01-01T${slot.start_time}`);
      const end = new Date(`2000-01-01T${slot.end_time}`);
      const diffMs = end.getTime() - start.getTime();
      totalMinutes += diffMs / (1000 * 60);
    });

    return totalMinutes / 60;
  };

  const isValidTimeSlot = (slot: TimeSlot) => {
    const start = new Date(`2000-01-01T${slot.start_time}`);
    const end = new Date(`2000-01-01T${slot.end_time}`);
    return start < end;
  };

  const getFieldError = (fieldName: string): string | undefined => {
    return validationErrors[fieldName]?.[0];
  };

  const hasFieldError = (fieldName: string): boolean => {
    return !!validationErrors[fieldName]?.length;
  };

  // Auto-set timezone if not already set
  useEffect(() => {
    if (!formData.time_zone) {
      const detectedTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
      handleFieldChange('time_zone', detectedTimezone);
    }
  }, [formData.time_zone]);

  const selectedDaySlots = formData.weekly_availability[selectedDay] || [];
  const totalWeeklyHours = getTotalWeeklyHours();

  return (
    <ScrollView className="flex-1">
      <Box className="p-6 max-w-6xl mx-auto">
        <VStack space="lg">
          {/* Header */}
          <VStack space="sm">
            <Heading size="xl" className="text-gray-900">
              Weekly Availability & Schedule
            </Heading>
            <Text className="text-gray-600">
              Set your teaching schedule and booking preferences. Students will see your available
              time slots in their local timezone.
            </Text>
          </VStack>

          {/* Weekly Summary Card */}
          <Card className="border-l-4 border-l-blue-500 bg-blue-50">
            <VStack space="md" className="p-6">
              <HStack className="items-center justify-between">
                <HStack space="sm" className="items-center">
                  <Icon as={Calendar} size={20} className="text-blue-600" />
                  <Heading size="md" className="text-blue-900">
                    Weekly Schedule Summary
                  </Heading>
                </HStack>
                <Badge className="bg-blue-600">
                  <BadgeText className="text-white">{totalWeeklyHours}h/week</BadgeText>
                </Badge>
              </HStack>

              <HStack space="md" className="flex-wrap">
                {DAYS_OF_WEEK.map(day => {
                  const dayHours = getDayHours(day.key);
                  const hasSlots = dayHours > 0;

                  return (
                    <VStack key={day.key} space="xs" className="items-center">
                      <Text
                        className={`text-xs font-medium ${
                          hasSlots ? 'text-blue-800' : 'text-gray-500'
                        }`}
                      >
                        {day.short}
                      </Text>
                      <Badge className={hasSlots ? 'bg-blue-100' : 'bg-gray-100'}>
                        <BadgeText className={hasSlots ? 'text-blue-800' : 'text-gray-500'}>
                          {dayHours > 0 ? `${dayHours}h` : '—'}
                        </BadgeText>
                      </Badge>
                    </VStack>
                  );
                })}
              </HStack>
            </VStack>
          </Card>

          {/* Timezone Selection */}
          <Card>
            <VStack space="md" className="p-6">
              <HStack className="items-center justify-between">
                <VStack space="xs">
                  <Heading size="md" className="text-gray-900">
                    Timezone
                  </Heading>
                  <Text className="text-gray-600 text-sm">
                    All your availability will be shown in this timezone
                  </Text>
                </VStack>
                <Icon as={Globe} size={24} className="text-blue-600" />
              </HStack>

              <FormControl isInvalid={hasFieldError('time_zone')}>
                <FormControlLabel>
                  <Text>Your Timezone *</Text>
                </FormControlLabel>
                <Select
                  selectedValue={formData.time_zone}
                  onValueChange={value => handleFieldChange('time_zone', value)}
                  isDisabled={isLoading}
                >
                  <SelectTrigger>
                    <SelectInput placeholder="Select your timezone" />
                  </SelectTrigger>
                  <SelectContent>
                    {TIMEZONES.map(timezone => (
                      <SelectItem key={timezone} label={timezone} value={timezone} />
                    ))}
                  </SelectContent>
                </Select>
                <FormControlHelper>
                  <Text>Students will see your availability converted to their local time</Text>
                </FormControlHelper>
                {hasFieldError('time_zone') && (
                  <FormControlError>
                    <Text>{getFieldError('time_zone')}</Text>
                  </FormControlError>
                )}
              </FormControl>
            </VStack>
          </Card>

          {/* Weekly Schedule */}
          <Card>
            <VStack space="md" className="p-6">
              <Heading size="md" className="text-gray-900">
                Weekly Schedule
              </Heading>

              {/* Day Selector - Mobile */}
              {isMobile && (
                <ScrollView horizontal showsHorizontalScrollIndicator={false}>
                  <HStack space="sm" className="pb-2">
                    {DAYS_OF_WEEK.map(day => {
                      const hasSlots = (formData.weekly_availability[day.key] || []).length > 0;
                      const isSelected = selectedDay === day.key;

                      return (
                        <Pressable
                          key={day.key}
                          onPress={() => setSelectedDay(day.key)}
                          className={`px-4 py-2 rounded-lg border ${
                            isSelected
                              ? 'border-blue-500 bg-blue-50'
                              : hasSlots
                                ? 'border-green-300 bg-green-50'
                                : 'border-gray-300 bg-white'
                          }`}
                        >
                          <VStack space="xs" className="items-center min-w-16">
                            <Text
                              className={`text-xs font-medium ${
                                isSelected
                                  ? 'text-blue-800'
                                  : hasSlots
                                    ? 'text-green-800'
                                    : 'text-gray-600'
                              }`}
                            >
                              {day.short}
                            </Text>
                            <Text
                              className={`text-xs ${
                                isSelected
                                  ? 'text-blue-600'
                                  : hasSlots
                                    ? 'text-green-600'
                                    : 'text-gray-500'
                              }`}
                            >
                              {getDayHours(day.key) > 0 ? `${getDayHours(day.key)}h` : '—'}
                            </Text>
                          </VStack>
                        </Pressable>
                      );
                    })}
                  </HStack>
                </ScrollView>
              )}

              {/* Desktop Day Tabs */}
              {!isMobile && (
                <HStack space="xs" className="border-b border-gray-200">
                  {DAYS_OF_WEEK.map(day => {
                    const hasSlots = (formData.weekly_availability[day.key] || []).length > 0;
                    const isSelected = selectedDay === day.key;

                    return (
                      <Pressable
                        key={day.key}
                        onPress={() => setSelectedDay(day.key)}
                        className={`px-4 py-3 border-b-2 ${
                          isSelected ? 'border-blue-500' : 'border-transparent'
                        }`}
                      >
                        <VStack space="xs" className="items-center">
                          <Text
                            className={`font-medium ${
                              isSelected
                                ? 'text-blue-600'
                                : hasSlots
                                  ? 'text-green-600'
                                  : 'text-gray-600'
                            }`}
                          >
                            {day.label}
                          </Text>
                          <Text className="text-xs text-gray-500">
                            {getDayHours(day.key) > 0 ? `${getDayHours(day.key)}h` : 'Not set'}
                          </Text>
                        </VStack>
                      </Pressable>
                    );
                  })}
                </HStack>
              )}

              {/* Selected Day Schedule */}
              <VStack space="md" className="mt-4">
                <HStack className="items-center justify-between">
                  <Text className="font-medium text-gray-900">
                    {DAYS_OF_WEEK.find(d => d.key === selectedDay)?.label} Schedule
                  </Text>
                  <HStack space="sm">
                    <Button size="sm" variant="outline" onPress={() => addTimeSlot(selectedDay)}>
                      <ButtonIcon as={Plus} className="text-gray-600 mr-1" />
                      <ButtonText>Add Time</ButtonText>
                    </Button>

                    {selectedDaySlots.length > 0 && (
                      <>
                        <Button
                          size="sm"
                          variant="outline"
                          onPress={() => applyToAllDays(selectedDay)}
                        >
                          <ButtonIcon as={Copy} className="text-gray-600 mr-1" />
                          <ButtonText>Copy to All</ButtonText>
                        </Button>

                        <Button
                          size="sm"
                          variant="outline"
                          onPress={() => clearDaySchedule(selectedDay)}
                        >
                          <ButtonIcon as={Trash2} className="text-red-500 mr-1" />
                          <ButtonText className="text-red-600">Clear</ButtonText>
                        </Button>
                      </>
                    )}
                  </HStack>
                </HStack>

                {selectedDaySlots.length > 0 ? (
                  <VStack space="sm">
                    {selectedDaySlots.map((slot, index) => (
                      <Card key={index} className="bg-gray-50">
                        <HStack space="md" className="items-center p-4">
                          <VStack className="flex-1">
                            <Text className="text-xs text-gray-600 mb-1">From</Text>
                            <Select
                              selectedValue={slot.start_time}
                              onValueChange={value =>
                                handleTimeSlotChange(selectedDay, index, 'start_time', value)
                              }
                            >
                              <SelectTrigger>
                                <SelectInput />
                              </SelectTrigger>
                              <SelectContent>
                                {TIME_OPTIONS.map(time => (
                                  <SelectItem
                                    key={time.value}
                                    label={time.label}
                                    value={time.value}
                                  />
                                ))}
                              </SelectContent>
                            </Select>
                          </VStack>

                          <Icon as={Clock} size={16} className="text-gray-400 mt-6" />

                          <VStack className="flex-1">
                            <Text className="text-xs text-gray-600 mb-1">To</Text>
                            <Select
                              selectedValue={slot.end_time}
                              onValueChange={value =>
                                handleTimeSlotChange(selectedDay, index, 'end_time', value)
                              }
                            >
                              <SelectTrigger>
                                <SelectInput />
                              </SelectTrigger>
                              <SelectContent>
                                {TIME_OPTIONS.map(time => (
                                  <SelectItem
                                    key={time.value}
                                    label={time.label}
                                    value={time.value}
                                  />
                                ))}
                              </SelectContent>
                            </Select>
                          </VStack>

                          <VStack className="items-center justify-center mt-6">
                            {!isValidTimeSlot(slot) && (
                              <Icon as={AlertCircle} size={16} className="text-red-500 mb-1" />
                            )}
                            <Button
                              size="sm"
                              variant="ghost"
                              onPress={() => removeTimeSlot(selectedDay, index)}
                            >
                              <ButtonIcon as={Minus} className="text-red-500" />
                            </Button>
                          </VStack>
                        </HStack>
                      </Card>
                    ))}
                  </VStack>
                ) : (
                  <Box className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
                    <VStack space="sm" className="items-center">
                      <Icon as={Calendar} size={32} className="text-gray-400" />
                      <Text className="text-gray-600">No availability set for this day</Text>
                      <Text className="text-sm text-gray-500">
                        Add time slots when you're available to teach
                      </Text>
                      <Button onPress={() => addTimeSlot(selectedDay)} className="mt-2">
                        <ButtonIcon as={Plus} className="text-white mr-2" />
                        <ButtonText>Add First Time Slot</ButtonText>
                      </Button>
                    </VStack>
                  </Box>
                )}
              </VStack>
            </VStack>
          </Card>

          {/* Booking Preferences */}
          <Card>
            <VStack space="md" className="p-6">
              <HStack className="items-center justify-between">
                <VStack space="xs">
                  <Heading size="md" className="text-gray-900">
                    Booking Preferences
                  </Heading>
                  <Text className="text-gray-600 text-sm">
                    Configure how students can book sessions with you
                  </Text>
                </VStack>
                <Button
                  size="sm"
                  variant="ghost"
                  onPress={() => setShowAdvancedSettings(!showAdvancedSettings)}
                >
                  <ButtonIcon as={Settings} className="text-gray-600 mr-1" />
                  <ButtonText>{showAdvancedSettings ? 'Hide' : 'Show'} Advanced</ButtonText>
                </Button>
              </HStack>

              <VStack space="md">
                {/* Minimum Notice */}
                <FormControl>
                  <FormControlLabel>
                    <Text>Minimum Advance Notice *</Text>
                  </FormControlLabel>
                  <Select
                    selectedValue={formData.booking_preferences.min_notice_hours.toString()}
                    onValueChange={value =>
                      handleBookingPreferenceChange('min_notice_hours', parseInt(value))
                    }
                  >
                    <SelectTrigger>
                      <SelectInput />
                    </SelectTrigger>
                    <SelectContent>
                      {[1, 2, 4, 8, 12, 24, 48, 72].map(hours => (
                        <SelectItem
                          key={hours}
                          label={
                            hours < 24
                              ? `${hours} hours`
                              : `${hours / 24} day${hours > 24 ? 's' : ''}`
                          }
                          value={hours.toString()}
                        />
                      ))}
                    </SelectContent>
                  </Select>
                  <FormControlHelper>
                    <Text>How far in advance must students book?</Text>
                  </FormControlHelper>
                </FormControl>

                {/* Session Duration Options */}
                <FormControl>
                  <FormControlLabel>
                    <Text>Available Session Durations *</Text>
                  </FormControlLabel>
                  <VStack space="sm">
                    {SESSION_DURATIONS.map(duration => (
                      <HStack key={duration} space="sm" className="items-center py-1">
                        <Switch
                          value={formData.booking_preferences.session_duration_options.includes(
                            duration,
                          )}
                          onValueChange={checked => toggleSessionDuration(duration, checked)}
                        />
                        <Text className="flex-1">{duration} minutes</Text>
                        {duration === 60 && (
                          <Badge className="bg-blue-100">
                            <BadgeText className="text-blue-800 text-xs">Most Popular</BadgeText>
                          </Badge>
                        )}
                      </HStack>
                    ))}
                  </VStack>
                  <FormControlHelper>
                    <Text>Select all session lengths you offer</Text>
                  </FormControlHelper>
                </FormControl>

                {/* Auto-Accept Bookings */}
                <HStack className="items-center justify-between py-2">
                  <VStack className="flex-1 mr-4">
                    <Text className="font-medium text-gray-900">Auto-Accept Bookings</Text>
                    <Text className="text-sm text-gray-600">
                      Automatically confirm bookings within your available hours
                    </Text>
                  </VStack>
                  <Switch
                    value={formData.booking_preferences.auto_accept_bookings}
                    onValueChange={value =>
                      handleBookingPreferenceChange('auto_accept_bookings', value)
                    }
                  />
                </HStack>

                {/* Advanced Settings */}
                {showAdvancedSettings && (
                  <VStack space="md" className="pt-4 border-t border-gray-200">
                    <Text className="font-medium text-gray-900">Advanced Settings</Text>

                    <FormControl>
                      <FormControlLabel>
                        <Text>Maximum Advance Booking</Text>
                      </FormControlLabel>
                      <Select
                        selectedValue={formData.booking_preferences.max_advance_days.toString()}
                        onValueChange={value =>
                          handleBookingPreferenceChange('max_advance_days', parseInt(value))
                        }
                      >
                        <SelectTrigger>
                          <SelectInput />
                        </SelectTrigger>
                        <SelectContent>
                          {[7, 14, 30, 60, 90].map(days => (
                            <SelectItem key={days} label={`${days} days`} value={days.toString()} />
                          ))}
                        </SelectContent>
                      </Select>
                      <FormControlHelper>
                        <Text>How far ahead can students book sessions?</Text>
                      </FormControlHelper>
                    </FormControl>
                  </VStack>
                )}
              </VStack>
            </VStack>
          </Card>

          {/* Availability Summary */}
          {totalWeeklyHours > 0 && (
            <Card className="border-l-4 border-l-green-500 bg-green-50">
              <VStack space="md" className="p-6">
                <HStack space="sm" className="items-center">
                  <Icon as={CheckCircle2} size={20} className="text-green-600" />
                  <Heading size="md" className="text-green-900">
                    Availability Summary
                  </Heading>
                </HStack>

                <VStack space="sm">
                  <HStack className="items-center justify-between">
                    <Text className="text-green-800">Total weekly hours:</Text>
                    <Text className="font-semibold text-green-900">{totalWeeklyHours} hours</Text>
                  </HStack>

                  <HStack className="items-center justify-between">
                    <Text className="text-green-800">Active days:</Text>
                    <Text className="font-semibold text-green-900">
                      {
                        Object.values(formData.weekly_availability).filter(
                          slots => slots.length > 0,
                        ).length
                      }{' '}
                      days
                    </Text>
                  </HStack>

                  <HStack className="items-center justify-between">
                    <Text className="text-green-800">Session durations:</Text>
                    <Text className="font-semibold text-green-900">
                      {formData.booking_preferences.session_duration_options.join(', ')} min
                    </Text>
                  </HStack>

                  <HStack className="items-center justify-between">
                    <Text className="text-green-800">Booking notice:</Text>
                    <Text className="font-semibold text-green-900">
                      {formData.booking_preferences.min_notice_hours < 24
                        ? `${formData.booking_preferences.min_notice_hours} hours`
                        : `${formData.booking_preferences.min_notice_hours / 24} day${
                            formData.booking_preferences.min_notice_hours > 24 ? 's' : ''
                          }`}
                    </Text>
                  </HStack>
                </VStack>
              </VStack>
            </Card>
          )}

          {/* Validation Errors */}
          {hasFieldError('weekly_availability') && (
            <Box className="bg-red-50 border-l-4 border-red-400 p-4">
              <HStack space="sm" className="items-center">
                <Icon as={AlertCircle} size={20} className="text-red-500" />
                <Text className="text-red-700">{getFieldError('weekly_availability')}</Text>
              </HStack>
            </Box>
          )}
        </VStack>
      </Box>
    </ScrollView>
  );
};
