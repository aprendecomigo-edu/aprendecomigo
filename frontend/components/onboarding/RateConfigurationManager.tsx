import { zodResolver } from '@hookform/resolvers/zod';
import {
  DollarSign,
  Euro,
  Info,
  AlertCircle,
  Check,
  TrendingUp,
  BookOpen,
  ChevronRight,
  Settings,
  Copy,
} from 'lucide-react-native';
import React, { useState, useEffect } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { ScrollView } from 'react-native';
import { z } from 'zod';

import { Course } from './course-catalog-browser';

import { Badge, BadgeText } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import {
  FormControl,
  FormControlError,
  FormControlErrorIcon,
  FormControlErrorText,
  FormControlLabel,
  FormControlLabelText,
  FormControlHelper,
  FormControlHelperText,
} from '@/components/ui/form-control';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Input, InputField } from '@/components/ui/input';
import {
  Modal,
  ModalBackdrop,
  ModalContent,
  ModalHeader,
  ModalCloseButton,
  ModalBody,
  ModalFooter,
} from '@/components/ui/modal';
import { Pressable } from '@/components/ui/pressable';
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
import { Switch } from '@/components/ui/switch';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

// Currency configuration
const CURRENCIES = [
  { code: 'EUR', symbol: '€', name: 'Euro' },
  { code: 'USD', symbol: '$', name: 'US Dollar' },
  { code: 'GBP', symbol: '£', name: 'British Pound' },
  { code: 'BRL', symbol: 'R$', name: 'Brazilian Real' },
] as const;

// Rate presets for different subjects and levels
const RATE_PRESETS = {
  mathematics: { beginner: 25, intermediate: 35, advanced: 45 },
  physics: { beginner: 30, intermediate: 40, advanced: 50 },
  chemistry: { beginner: 30, intermediate: 40, advanced: 50 },
  biology: { beginner: 25, intermediate: 35, advanced: 45 },
  portuguese: { beginner: 20, intermediate: 30, advanced: 40 },
  english: { beginner: 25, intermediate: 35, advanced: 45 },
  history: { beginner: 20, intermediate: 30, advanced: 40 },
  geography: { beginner: 20, intermediate: 30, advanced: 40 },
  default: { beginner: 25, intermediate: 35, advanced: 45 },
} as const;

interface CourseRate {
  courseId: number;
  rate: number;
  currency: string;
  isCustom: boolean;
}

interface RateConfigurationManagerProps {
  courses: Course[];
  initialRates?: CourseRate[];
  defaultRate?: number;
  defaultCurrency?: string;
  onRatesChange: (rates: CourseRate[]) => void;
  onContinue?: () => void;
  isLoading?: boolean;
  title?: string;
  subtitle?: string;
}

// Form schema for rate validation
const rateSchema = z.object({
  defaultRate: z
    .number()
    .min(10, 'Rate must be at least €10/hour')
    .max(200, 'Rate must be less than €200/hour'),
  currency: z.string().min(1, 'Please select a currency'),
  useDefaultForAll: z.boolean(),
});

const courseRateSchema = z.object({
  rate: z
    .number()
    .min(10, 'Rate must be at least €10/hour')
    .max(200, 'Rate must be less than €200/hour'),
});

type RateFormData = z.infer<typeof rateSchema>;
type CourseRateFormData = z.infer<typeof courseRateSchema>;

const RatePresetModal: React.FC<{
  isOpen: boolean;
  onClose: () => void;
  onApplyPreset: (rates: Record<number, number>) => void;
  courses: Course[];
  currency: string;
}> = ({ isOpen, onClose, onApplyPreset, courses, currency }) => {
  const [selectedLevel, setSelectedLevel] = useState<'beginner' | 'intermediate' | 'advanced'>(
    'intermediate',
  );

  const handleApplyPresets = () => {
    const rates: Record<number, number> = {};

    courses.forEach(course => {
      const subjectKey = course.subject_area?.toLowerCase() || 'default';
      const presets = RATE_PRESETS[subjectKey as keyof typeof RATE_PRESETS] || RATE_PRESETS.default;
      rates[course.id] = presets[selectedLevel];
    });

    onApplyPreset(rates);
    onClose();
  };

  const getCurrencySymbol = (code: string) => {
    return CURRENCIES.find(c => c.code === code)?.symbol || '€';
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="md">
      <ModalBackdrop />
      <ModalContent>
        <ModalHeader>
          <HStack className="items-center justify-between w-full">
            <Heading size="lg">Apply Rate Presets</Heading>
            <ModalCloseButton onPress={onClose} />
          </HStack>
        </ModalHeader>

        <ModalBody className="p-6">
          <VStack space="lg">
            <VStack space="sm">
              <Text className="text-gray-700 font-medium">
                Choose a difficulty level to apply suggested rates:
              </Text>
              <Text className="text-gray-600 text-sm">
                These are market-average rates for different subject complexities.
              </Text>
            </VStack>

            <VStack space="md">
              {(['beginner', 'intermediate', 'advanced'] as const).map(level => (
                <Pressable key={level} onPress={() => setSelectedLevel(level)} className="w-full">
                  <Card
                    className={`border-2 ${
                      selectedLevel === level
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 bg-white'
                    }`}
                  >
                    <CardContent className="p-4">
                      <HStack className="items-center justify-between">
                        <VStack space="xs">
                          <Text
                            className={`font-medium capitalize ${
                              selectedLevel === level ? 'text-blue-900' : 'text-gray-900'
                            }`}
                          >
                            {level} Level
                          </Text>
                          <Text
                            className={`text-sm ${
                              selectedLevel === level ? 'text-blue-700' : 'text-gray-600'
                            }`}
                          >
                            Average: {getCurrencySymbol(currency)}
                            {RATE_PRESETS.default[level]}/hour
                          </Text>
                        </VStack>

                        {selectedLevel === level && (
                          <Box className="w-6 h-6 rounded-full bg-blue-600 items-center justify-center">
                            <Icon as={Check} className="text-white" size="sm" />
                          </Box>
                        )}
                      </HStack>
                    </CardContent>
                  </Card>
                </Pressable>
              ))}
            </VStack>

            <Box className="bg-yellow-50 border border-yellow-200 p-4 rounded-lg">
              <HStack space="sm" className="items-start">
                <Icon as={Info} className="text-yellow-600 mt-0.5" size="sm" />
                <Text className="text-yellow-800 text-sm">
                  These are suggested starting rates. You can adjust individual course rates after
                  applying the preset.
                </Text>
              </HStack>
            </Box>
          </VStack>
        </ModalBody>

        <ModalFooter className="p-4 border-t border-gray-200">
          <HStack space="sm" className="w-full justify-end">
            <Button variant="outline" onPress={onClose}>
              <ButtonText>Cancel</ButtonText>
            </Button>
            <Button onPress={handleApplyPresets} className="bg-blue-600">
              <ButtonText className="text-white">Apply Presets</ButtonText>
            </Button>
          </HStack>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};

const CourseRateCard: React.FC<{
  course: Course;
  rate: number;
  currency: string;
  onRateChange: (courseId: number, rate: number) => void;
  isDefault?: boolean;
}> = ({ course, rate, currency, onRateChange, isDefault = false }) => {
  const [localRate, setLocalRate] = useState(rate.toString());
  const [hasError, setHasError] = useState(false);

  const {
    control,
    handleSubmit,
    formState: { errors },
    setValue,
    watch,
  } = useForm<CourseRateFormData>({
    resolver: zodResolver(courseRateSchema),
    defaultValues: { rate },
    mode: 'onChange',
  });

  const watchedRate = watch('rate');

  useEffect(() => {
    setValue('rate', rate);
    setLocalRate(rate.toString());
  }, [rate, setValue]);

  const handleRateSubmit = (data: CourseRateFormData) => {
    onRateChange(course.id, data.rate);
    setHasError(false);
  };

  const handleRateBlur = () => {
    const numericRate = parseFloat(localRate);
    if (!isNaN(numericRate) && numericRate >= 10 && numericRate <= 200) {
      onRateChange(course.id, numericRate);
      setHasError(false);
    } else {
      setHasError(true);
    }
  };

  const getCurrencySymbol = (code: string) => {
    return CURRENCIES.find(c => c.code === code)?.symbol || '€';
  };

  return (
    <Card className={`border-2 ${hasError ? 'border-red-300' : 'border-gray-200'} bg-white mb-3`}>
      <CardContent className="p-4">
        <VStack space="md">
          <HStack className="items-start justify-between">
            <HStack space="sm" className="items-start flex-1">
              <Box className="w-10 h-10 rounded-full bg-blue-100 items-center justify-center">
                <Icon as={BookOpen} className="text-blue-600" size="sm" />
              </Box>

              <VStack className="flex-1" space="xs">
                <VStack space="xs">
                  <Heading size="sm" className="text-gray-900">
                    {course.name}
                  </Heading>
                  {course.code && (
                    <Text className="text-gray-500 text-xs font-mono">{course.code}</Text>
                  )}
                </VStack>

                <HStack space="xs" className="flex-wrap">
                  <Badge className="bg-blue-100">
                    <BadgeText className="text-blue-700 text-xs">
                      {course.education_level?.replace('_', ' ') || 'Unknown Level'}
                    </BadgeText>
                  </Badge>
                  {course.subject_area && (
                    <Badge className="bg-green-100">
                      <BadgeText className="text-green-700 text-xs">
                        {course.subject_area}
                      </BadgeText>
                    </Badge>
                  )}
                  {isDefault && (
                    <Badge className="bg-gray-100">
                      <BadgeText className="text-gray-700 text-xs">Default Rate</BadgeText>
                    </Badge>
                  )}
                </HStack>
              </VStack>
            </HStack>

            <Box className="ml-4">
              <FormControl isInvalid={hasError} className="w-32">
                <HStack className="items-center">
                  <Text className="text-gray-600 font-medium">{getCurrencySymbol(currency)}</Text>
                  <Controller
                    name="rate"
                    control={control}
                    render={({ field: { onChange, onBlur, value } }) => (
                      <Input className="flex-1">
                        <InputField
                          placeholder="25.00"
                          value={localRate}
                          onChangeText={text => {
                            setLocalRate(text);
                            const numericValue = parseFloat(text);
                            if (!isNaN(numericValue)) {
                              onChange(numericValue);
                            }
                          }}
                          onBlur={handleRateBlur}
                          keyboardType="decimal-pad"
                          textAlign="right"
                        />
                      </Input>
                    )}
                  />
                  <Text className="text-gray-600 text-sm ml-1">/h</Text>
                </HStack>

                {hasError && (
                  <FormControlError>
                    <FormControlErrorIcon as={AlertCircle} />
                    <FormControlErrorText className="text-xs">
                      Rate must be between €10-200/hour
                    </FormControlErrorText>
                  </FormControlError>
                )}
              </FormControl>
            </Box>
          </HStack>

          {course.description && (
            <Text className="text-gray-600 text-sm">{course.description}</Text>
          )}
        </VStack>
      </CardContent>
    </Card>
  );
};

export const RateConfigurationManager: React.FC<RateConfigurationManagerProps> = ({
  courses,
  initialRates = [],
  defaultRate = 30,
  defaultCurrency = 'EUR',
  onRatesChange,
  onContinue,
  isLoading = false,
  title = 'Set Your Teaching Rates',
  subtitle = 'Configure hourly rates for each subject to attract the right students',
}) => {
  const [showPresetModal, setShowPresetModal] = useState(false);
  const [courseRates, setCourseRates] = useState<Record<number, CourseRate>>({});

  const {
    control,
    handleSubmit,
    formState: { errors },
    setValue,
    watch,
  } = useForm<RateFormData>({
    resolver: zodResolver(rateSchema),
    defaultValues: {
      defaultRate,
      currency: defaultCurrency,
      useDefaultForAll: false,
    },
    mode: 'onChange',
  });

  const watchedValues = watch();

  // Initialize course rates
  useEffect(() => {
    const rates: Record<number, CourseRate> = {};

    courses.forEach(course => {
      const existingRate = initialRates.find(r => r.courseId === course.id);
      rates[course.id] = {
        courseId: course.id,
        rate: existingRate?.rate || defaultRate,
        currency: existingRate?.currency || defaultCurrency,
        isCustom: !existingRate,
      };
    });

    setCourseRates(rates);
  }, [courses, initialRates, defaultRate, defaultCurrency]);

  // Update all rates when default changes
  useEffect(() => {
    if (watchedValues.useDefaultForAll) {
      const updatedRates = { ...courseRates };
      Object.keys(updatedRates).forEach(courseIdStr => {
        const courseId = parseInt(courseIdStr);
        updatedRates[courseId] = {
          ...updatedRates[courseId],
          rate: watchedValues.defaultRate,
          currency: watchedValues.currency,
          isCustom: false,
        };
      });
      setCourseRates(updatedRates);
    }
  }, [watchedValues.useDefaultForAll, watchedValues.defaultRate, watchedValues.currency]);

  // Update rates when currency changes
  useEffect(() => {
    const updatedRates = { ...courseRates };
    Object.keys(updatedRates).forEach(courseIdStr => {
      const courseId = parseInt(courseIdStr);
      updatedRates[courseId] = {
        ...updatedRates[courseId],
        currency: watchedValues.currency,
      };
    });
    setCourseRates(updatedRates);
  }, [watchedValues.currency]);

  const handleCourseRateChange = (courseId: number, newRate: number) => {
    setCourseRates(prev => ({
      ...prev,
      [courseId]: {
        ...prev[courseId],
        rate: newRate,
        isCustom: true,
      },
    }));

    // Disable "use default for all" when individual rates are changed
    if (watchedValues.useDefaultForAll) {
      setValue('useDefaultForAll', false);
    }
  };

  const handleApplyPresets = (presetRates: Record<number, number>) => {
    const updatedRates = { ...courseRates };
    Object.entries(presetRates).forEach(([courseIdStr, rate]) => {
      const courseId = parseInt(courseIdStr);
      updatedRates[courseId] = {
        ...updatedRates[courseId],
        rate,
        isCustom: true,
      };
    });
    setCourseRates(updatedRates);
    setValue('useDefaultForAll', false);
  };

  const handleCopyDefaultToAll = () => {
    const updatedRates = { ...courseRates };
    Object.keys(updatedRates).forEach(courseIdStr => {
      const courseId = parseInt(courseIdStr);
      updatedRates[courseId] = {
        ...updatedRates[courseId],
        rate: watchedValues.defaultRate,
        isCustom: false,
      };
    });
    setCourseRates(updatedRates);
  };

  const handleContinue = () => {
    const rates = Object.values(courseRates);
    onRatesChange(rates);
    if (onContinue) {
      onContinue();
    }
  };

  const getCurrencySymbol = (code: string) => {
    return CURRENCIES.find(c => c.code === code)?.symbol || '€';
  };

  const averageRate =
    Object.values(courseRates).reduce((sum, rate) => sum + rate.rate, 0) / courses.length || 0;
  const minRate = Math.min(...Object.values(courseRates).map(r => r.rate));
  const maxRate = Math.max(...Object.values(courseRates).map(r => r.rate));

  return (
    <VStack className="flex-1 bg-gray-50" space="md">
      {/* Header */}
      <Box className="bg-white px-4 py-6 border-b border-gray-200">
        <VStack space="md">
          <VStack className="items-center text-center" space="sm">
            <Box className="w-12 h-12 rounded-full bg-green-100 items-center justify-center">
              <Icon as={DollarSign} className="text-green-600" size="lg" />
            </Box>
            <VStack space="xs">
              <Heading size="xl" className="text-gray-900 text-center">
                {title}
              </Heading>
              <Text className="text-gray-600 text-center">{subtitle}</Text>
            </VStack>
          </VStack>

          {/* Rate Summary */}
          <HStack className="items-center justify-center bg-gray-50 p-4 rounded-lg" space="lg">
            <VStack className="items-center" space="xs">
              <Text className="text-gray-500 text-xs uppercase tracking-wide">Average</Text>
              <Text className="text-gray-900 font-bold text-lg">
                {getCurrencySymbol(watchedValues.currency)}
                {averageRate.toFixed(0)}/h
              </Text>
            </VStack>
            <VStack className="items-center" space="xs">
              <Text className="text-gray-500 text-xs uppercase tracking-wide">Range</Text>
              <Text className="text-gray-900 font-medium">
                {getCurrencySymbol(watchedValues.currency)}
                {minRate}-{maxRate}/h
              </Text>
            </VStack>
            <VStack className="items-center" space="xs">
              <Text className="text-gray-500 text-xs uppercase tracking-wide">Subjects</Text>
              <Text className="text-gray-900 font-medium">{courses.length}</Text>
            </VStack>
          </HStack>
        </VStack>
      </Box>

      {/* Configuration */}
      <ScrollView className="flex-1" showsVerticalScrollIndicator={false}>
        <VStack className="px-4" space="lg">
          {/* Default Rate Configuration */}
          <Card className="bg-white border border-gray-200">
            <CardHeader>
              <Heading size="md" className="text-gray-900">
                Rate Configuration
              </Heading>
            </CardHeader>
            <CardContent className="pt-0">
              <VStack space="md">
                {/* Currency Selection */}
                <FormControl isInvalid={!!errors.currency}>
                  <FormControlLabel>
                    <FormControlLabelText>Currency</FormControlLabelText>
                  </FormControlLabel>
                  <Controller
                    name="currency"
                    control={control}
                    render={({ field: { onChange, value } }) => (
                      <Select selectedValue={value} onValueChange={onChange}>
                        <SelectTrigger>
                          <SelectInput placeholder="Select currency" />
                          <SelectIcon as={ChevronRight} />
                        </SelectTrigger>
                        <SelectPortal>
                          <SelectBackdrop />
                          <SelectContent>
                            <SelectDragIndicatorWrapper>
                              <SelectDragIndicator />
                            </SelectDragIndicatorWrapper>
                            {CURRENCIES.map(currency => (
                              <SelectItem
                                key={currency.code}
                                value={currency.code}
                                label={`${currency.symbol} ${currency.name}`}
                              />
                            ))}
                          </SelectContent>
                        </SelectPortal>
                      </Select>
                    )}
                  />
                  <FormControlError>
                    <FormControlErrorIcon as={AlertCircle} />
                    <FormControlErrorText>{errors.currency?.message}</FormControlErrorText>
                  </FormControlError>
                </FormControl>

                {/* Default Rate */}
                <FormControl isInvalid={!!errors.defaultRate}>
                  <FormControlLabel>
                    <FormControlLabelText>Default Hourly Rate</FormControlLabelText>
                  </FormControlLabel>
                  <Controller
                    name="defaultRate"
                    control={control}
                    render={({ field: { onChange, onBlur, value } }) => (
                      <HStack className="items-center">
                        <Text className="text-gray-600 font-medium mr-2">
                          {getCurrencySymbol(watchedValues.currency)}
                        </Text>
                        <Input className="flex-1 max-w-32">
                          <InputField
                            placeholder="30.00"
                            value={value?.toString() || ''}
                            onChangeText={text => {
                              const numericValue = parseFloat(text);
                              if (!isNaN(numericValue)) {
                                onChange(numericValue);
                              }
                            }}
                            onBlur={onBlur}
                            keyboardType="decimal-pad"
                          />
                        </Input>
                        <Text className="text-gray-600 text-sm ml-2">/hour</Text>
                      </HStack>
                    )}
                  />
                  <FormControlError>
                    <FormControlErrorIcon as={AlertCircle} />
                    <FormControlErrorText>{errors.defaultRate?.message}</FormControlErrorText>
                  </FormControlError>
                  <FormControlHelper>
                    <FormControlHelperText>
                      This will be used as your base rate for all subjects
                    </FormControlHelperText>
                  </FormControlHelper>
                </FormControl>

                {/* Use Default for All Toggle */}
                <HStack className="items-center justify-between">
                  <VStack className="flex-1">
                    <Text className="text-gray-900 font-medium">
                      Use same rate for all subjects
                    </Text>
                    <Text className="text-gray-600 text-sm">
                      Apply the default rate to all your teaching subjects
                    </Text>
                  </VStack>
                  <Controller
                    name="useDefaultForAll"
                    control={control}
                    render={({ field: { onChange, value } }) => (
                      <Switch value={value} onValueChange={onChange} />
                    )}
                  />
                </HStack>

                {/* Quick Actions */}
                <HStack space="sm" className="flex-wrap">
                  <Button
                    variant="outline"
                    size="sm"
                    onPress={() => setShowPresetModal(true)}
                    disabled={watchedValues.useDefaultForAll}
                  >
                    <ButtonIcon as={TrendingUp} className="text-blue-600 mr-1" />
                    <ButtonText className="text-blue-600">Apply Presets</ButtonText>
                  </Button>

                  <Button
                    variant="outline"
                    size="sm"
                    onPress={handleCopyDefaultToAll}
                    disabled={watchedValues.useDefaultForAll}
                  >
                    <ButtonIcon as={Copy} className="text-gray-600 mr-1" />
                    <ButtonText className="text-gray-600">Copy to All</ButtonText>
                  </Button>
                </HStack>
              </VStack>
            </CardContent>
          </Card>

          {/* Individual Course Rates */}
          {!watchedValues.useDefaultForAll && (
            <VStack space="md">
              <HStack className="items-center justify-between">
                <Heading size="md" className="text-gray-900">
                  Subject-Specific Rates
                </Heading>
                <Badge className="bg-blue-100">
                  <BadgeText className="text-blue-700 text-xs">{courses.length} subjects</BadgeText>
                </Badge>
              </HStack>

              <VStack space="sm">
                {courses.map(course => (
                  <CourseRateCard
                    key={course.id}
                    course={course}
                    rate={courseRates[course.id]?.rate || defaultRate}
                    currency={watchedValues.currency}
                    onRateChange={handleCourseRateChange}
                    isDefault={!courseRates[course.id]?.isCustom}
                  />
                ))}
              </VStack>
            </VStack>
          )}

          {/* Help Section */}
          <Box className="bg-blue-50 border border-blue-200 p-4 rounded-lg mb-6">
            <HStack space="sm" className="items-start">
              <Icon as={Info} className="text-blue-600 mt-0.5" size="sm" />
              <VStack space="xs" className="flex-1">
                <Text className="text-blue-900 font-medium text-sm">Pricing Tips</Text>
                <VStack space="xs">
                  <Text className="text-blue-800 text-sm">
                    • Research local market rates for your subjects
                  </Text>
                  <Text className="text-blue-800 text-sm">
                    • Consider your experience level and qualifications
                  </Text>
                  <Text className="text-blue-800 text-sm">
                    • You can adjust rates anytime in your profile settings
                  </Text>
                  <Text className="text-blue-800 text-sm">
                    • Higher complexity subjects typically command higher rates
                  </Text>
                </VStack>
              </VStack>
            </HStack>
          </Box>
        </VStack>
      </ScrollView>

      {/* Continue Button */}
      {onContinue && (
        <Box className="bg-white px-4 py-4 border-t border-gray-200">
          <Button
            onPress={handleContinue}
            disabled={isLoading || Object.keys(courseRates).length === 0}
            className="w-full bg-green-600 hover:bg-green-700"
          >
            <ButtonText className="text-white font-medium">
              Continue with Rate Configuration
            </ButtonText>
            <ButtonIcon as={ChevronRight} className="text-white ml-2" />
          </Button>
        </Box>
      )}

      {/* Rate Preset Modal */}
      <RatePresetModal
        isOpen={showPresetModal}
        onClose={() => setShowPresetModal(false)}
        onApplyPreset={handleApplyPresets}
        courses={courses}
        currency={watchedValues.currency}
      />
    </VStack>
  );
};
