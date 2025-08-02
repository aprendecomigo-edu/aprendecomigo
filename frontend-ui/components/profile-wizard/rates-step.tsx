import {
  DollarSign,
  Plus,
  X,
  TrendingUp,
  Users,
  User,
  Star,
  Package,
  Info,
  CheckCircle2,
  AlertCircle,
  Calculator,
  Target,
  Award,
} from 'lucide-react-native';
import React, { useState, useEffect } from 'react';
import { Platform } from 'react-native';

import {
  AlertDialog,
  AlertDialogBackdrop,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogFooter,
  AlertDialogBody,
} from '@/components/ui/alert-dialog';
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
import { Textarea, TextareaInput } from '@/components/ui/textarea';
import { VStack } from '@/components/ui/vstack';

interface PackageDeal {
  id: string;
  name: string;
  sessions: number;
  price: number;
  discount_percentage: number;
}

interface RateStructure {
  individual_rate: number;
  group_rate?: number;
  trial_lesson_rate?: number;
  package_deals?: PackageDeal[];
  currency: string;
}

interface RatesFormData {
  rate_structure: RateStructure;
  payment_methods: string[];
  cancellation_policy: string;
}

interface RatesStepProps {
  formData: RatesFormData;
  onFormDataChange: (data: Partial<RatesFormData>) => void;
  validationErrors?: Record<string, string[]>;
  isLoading?: boolean;
}

const CURRENCIES = [
  { value: 'EUR', label: 'Euro (€)', symbol: '€' },
  { value: 'USD', label: 'US Dollar ($)', symbol: '$' },
  { value: 'GBP', label: 'British Pound (£)', symbol: '£' },
  { value: 'BRL', label: 'Brazilian Real (R$)', symbol: 'R$' },
];

const PAYMENT_METHODS = ['Credit Card', 'Debit Card', 'PayPal', 'Bank Transfer', 'Stripe', 'Cash'];

const CANCELLATION_POLICIES = [
  {
    value: 'flexible',
    name: 'Flexible',
    description: 'Free cancellation up to 2 hours before lesson',
  },
  {
    value: 'moderate',
    name: 'Moderate',
    description: 'Free cancellation up to 24 hours before lesson',
  },
  {
    value: 'strict',
    name: 'Strict',
    description: 'Free cancellation up to 48 hours before lesson',
  },
];

const RATE_SUGGESTIONS = {
  beginner: { min: 15, max: 25, average: 20 },
  intermediate: { min: 20, max: 35, average: 27 },
  advanced: { min: 30, max: 50, average: 40 },
  expert: { min: 45, max: 80, average: 62 },
};

export const RatesStep: React.FC<RatesStepProps> = ({
  formData,
  onFormDataChange,
  validationErrors = {},
  isLoading = false,
}) => {
  const [showPackageDialog, setShowPackageDialog] = useState(false);
  const [editingPackage, setEditingPackage] = useState<PackageDeal | null>(null);
  const [newPackage, setNewPackage] = useState<Partial<PackageDeal>>({
    name: '',
    sessions: 4,
    price: 0,
    discount_percentage: 10,
  });
  const [showRateSuggestions, setShowRateSuggestions] = useState(true);
  const [hasTrialLesson, setHasTrialLesson] = useState(!!formData.rate_structure.trial_lesson_rate);
  const [hasGroupRate, setHasGroupRate] = useState(!!formData.rate_structure.group_rate);

  const currency =
    CURRENCIES.find(c => c.value === formData.rate_structure.currency) || CURRENCIES[0];

  const handleFieldChange = (field: keyof RatesFormData, value: any) => {
    onFormDataChange({ [field]: value });
  };

  const handleRateStructureChange = (field: keyof RateStructure, value: any) => {
    handleFieldChange('rate_structure', {
      ...formData.rate_structure,
      [field]: value,
    });
  };

  const handlePaymentMethodToggle = (method: string, checked: boolean) => {
    const currentMethods = formData.payment_methods || [];
    const updatedMethods = checked
      ? [...currentMethods, method]
      : currentMethods.filter(m => m !== method);

    handleFieldChange('payment_methods', updatedMethods);
  };

  const calculatePackagePrice = (
    sessions: number,
    individualRate: number,
    discountPercent: number
  ) => {
    const totalBeforeDiscount = sessions * individualRate;
    const discountAmount = totalBeforeDiscount * (discountPercent / 100);
    return totalBeforeDiscount - discountAmount;
  };

  const handleSavePackage = () => {
    if (!newPackage.name || !newPackage.sessions || !newPackage.discount_percentage) {
      return;
    }

    const calculatedPrice = calculatePackagePrice(
      newPackage.sessions!,
      formData.rate_structure.individual_rate,
      newPackage.discount_percentage!
    );

    const packageDeal: PackageDeal = {
      id: editingPackage?.id || Date.now().toString(),
      name: newPackage.name!,
      sessions: newPackage.sessions!,
      price: newPackage.price || calculatedPrice,
      discount_percentage: newPackage.discount_percentage!,
    };

    const currentPackages = formData.rate_structure.package_deals || [];
    let updatedPackages;

    if (editingPackage) {
      updatedPackages = currentPackages.map(p => (p.id === editingPackage.id ? packageDeal : p));
    } else {
      updatedPackages = [...currentPackages, packageDeal];
    }

    handleRateStructureChange('package_deals', updatedPackages);
    resetPackageForm();
  };

  const handleEditPackage = (packageDeal: PackageDeal) => {
    setNewPackage(packageDeal);
    setEditingPackage(packageDeal);
    setShowPackageDialog(true);
  };

  const handleDeletePackage = (packageId: string) => {
    const updatedPackages = (formData.rate_structure.package_deals || []).filter(
      p => p.id !== packageId
    );
    handleRateStructureChange('package_deals', updatedPackages);
  };

  const resetPackageForm = () => {
    setNewPackage({
      name: '',
      sessions: 4,
      price: 0,
      discount_percentage: 10,
    });
    setEditingPackage(null);
    setShowPackageDialog(false);
  };

  const getRateSuggestion = () => {
    // This would typically come from an API call based on subject, location, experience
    return RATE_SUGGESTIONS.intermediate; // Default suggestion
  };

  const handleTrialLessonToggle = (enabled: boolean) => {
    setHasTrialLesson(enabled);
    if (enabled && !formData.rate_structure.trial_lesson_rate) {
      // Set default trial rate to 50% of regular rate
      const trialRate = Math.round(formData.rate_structure.individual_rate * 0.5);
      handleRateStructureChange('trial_lesson_rate', trialRate);
    } else if (!enabled) {
      handleRateStructureChange('trial_lesson_rate', undefined);
    }
  };

  const handleGroupRateToggle = (enabled: boolean) => {
    setHasGroupRate(enabled);
    if (enabled && !formData.rate_structure.group_rate) {
      // Set default group rate to 75% of individual rate
      const groupRate = Math.round(formData.rate_structure.individual_rate * 0.75);
      handleRateStructureChange('group_rate', groupRate);
    } else if (!enabled) {
      handleRateStructureChange('group_rate', undefined);
    }
  };

  // Auto-calculate package price when discount changes
  useEffect(() => {
    if (
      newPackage.sessions &&
      newPackage.discount_percentage &&
      formData.rate_structure.individual_rate
    ) {
      const calculatedPrice = calculatePackagePrice(
        newPackage.sessions,
        formData.rate_structure.individual_rate,
        newPackage.discount_percentage
      );
      setNewPackage(prev => ({ ...prev, price: calculatedPrice }));
    }
  }, [
    newPackage.sessions,
    newPackage.discount_percentage,
    formData.rate_structure.individual_rate,
  ]);

  const getFieldError = (fieldName: string): string | undefined => {
    return validationErrors[fieldName]?.[0];
  };

  const hasFieldError = (fieldName: string): boolean => {
    return !!validationErrors[fieldName]?.length;
  };

  const rateSuggestion = getRateSuggestion();

  return (
    <ScrollView className="flex-1">
      <Box className="p-6 max-w-4xl mx-auto">
        <VStack space="lg">
          {/* Header */}
          <VStack space="sm">
            <Heading size="xl" className="text-gray-900">
              Rates & Pricing Structure
            </Heading>
            <Text className="text-gray-600">
              Set competitive rates that reflect your expertise and attract students. You can always
              adjust these later as you gain experience.
            </Text>
          </VStack>

          {/* Rate Suggestions */}
          {showRateSuggestions && (
            <Card className="border-l-4 border-l-blue-500 bg-blue-50">
              <VStack space="md" className="p-6">
                <HStack className="items-center justify-between">
                  <HStack space="sm" className="items-center">
                    <Icon as={TrendingUp} size={20} className="text-blue-600" />
                    <Heading size="md" className="text-blue-900">
                      Market Rate Suggestions
                    </Heading>
                  </HStack>
                  <Button size="sm" variant="ghost" onPress={() => setShowRateSuggestions(false)}>
                    <ButtonIcon as={X} className="text-blue-600" />
                  </Button>
                </HStack>

                <VStack space="sm">
                  <Text className="text-blue-800">
                    Based on your experience level and subject expertise:
                  </Text>
                  <HStack space="md" className="flex-wrap">
                    <Badge className="bg-blue-100">
                      <BadgeText className="text-blue-800">
                        Average: {currency.symbol}
                        {rateSuggestion.average}/hour
                      </BadgeText>
                    </Badge>
                    <Badge className="bg-blue-100">
                      <BadgeText className="text-blue-800">
                        Range: {currency.symbol}
                        {rateSuggestion.min}-{rateSuggestion.max}/hour
                      </BadgeText>
                    </Badge>
                  </HStack>
                  <Text className="text-sm text-blue-700">
                    Consider starting at the lower end and increasing rates as you build reviews and
                    experience.
                  </Text>
                </VStack>
              </VStack>
            </Card>
          )}

          {/* Currency Selection */}
          <Card>
            <VStack space="md" className="p-6">
              <Heading size="md" className="text-gray-900">
                Currency
              </Heading>

              <FormControl isInvalid={hasFieldError('rate_structure.currency')}>
                <FormControlLabel>
                  <Text>Primary Currency *</Text>
                </FormControlLabel>
                <Select
                  selectedValue={formData.rate_structure.currency}
                  onValueChange={value => handleRateStructureChange('currency', value)}
                  isDisabled={isLoading}
                >
                  <SelectTrigger>
                    <SelectInput placeholder="Select currency" />
                  </SelectTrigger>
                  <SelectContent>
                    {CURRENCIES.map(currency => (
                      <SelectItem
                        key={currency.value}
                        label={currency.label}
                        value={currency.value}
                      />
                    ))}
                  </SelectContent>
                </Select>
                <FormControlHelper>
                  <Text>All your rates will be displayed in this currency</Text>
                </FormControlHelper>
                {hasFieldError('rate_structure.currency') && (
                  <FormControlError>
                    <Text>{getFieldError('rate_structure.currency')}</Text>
                  </FormControlError>
                )}
              </FormControl>
            </VStack>
          </Card>

          {/* Individual Rate */}
          <Card>
            <VStack space="md" className="p-6">
              <HStack className="items-center justify-between">
                <VStack space="xs">
                  <Heading size="md" className="text-gray-900">
                    Individual Lesson Rate
                  </Heading>
                  <Text className="text-gray-600 text-sm">
                    Your standard rate for one-on-one tutoring sessions
                  </Text>
                </VStack>
                <Icon as={User} size={24} className="text-blue-600" />
              </HStack>

              <FormControl isInvalid={hasFieldError('rate_structure.individual_rate')}>
                <FormControlLabel>
                  <Text>Hourly Rate *</Text>
                </FormControlLabel>
                <HStack space="sm" className="items-center">
                  <Text className="text-lg font-medium text-gray-700">{currency.symbol}</Text>
                  <Input className="flex-1">
                    <InputField
                      value={formData.rate_structure.individual_rate?.toString() || ''}
                      onChangeText={value =>
                        handleRateStructureChange('individual_rate', parseFloat(value) || 0)
                      }
                      placeholder="0"
                      keyboardType="numeric"
                      isDisabled={isLoading}
                    />
                  </Input>
                  <Text className="text-gray-600">/hour</Text>
                </HStack>
                <FormControlHelper>
                  <Text>This is your main tutoring rate that students will see</Text>
                </FormControlHelper>
                {hasFieldError('rate_structure.individual_rate') && (
                  <FormControlError>
                    <Text>{getFieldError('rate_structure.individual_rate')}</Text>
                  </FormControlError>
                )}
              </FormControl>
            </VStack>
          </Card>

          {/* Trial Lesson Rate */}
          <Card>
            <VStack space="md" className="p-6">
              <HStack className="items-center justify-between">
                <VStack space="xs">
                  <Heading size="md" className="text-gray-900">
                    Trial Lesson (Optional)
                  </Heading>
                  <Text className="text-gray-600 text-sm">
                    Offer a discounted first lesson to attract new students
                  </Text>
                </VStack>
                <Switch
                  value={hasTrialLesson}
                  onValueChange={handleTrialLessonToggle}
                  isDisabled={isLoading}
                />
              </HStack>

              {hasTrialLesson && (
                <FormControl>
                  <FormControlLabel>
                    <Text>Trial Lesson Rate</Text>
                  </FormControlLabel>
                  <HStack space="sm" className="items-center">
                    <Text className="text-lg font-medium text-gray-700">{currency.symbol}</Text>
                    <Input className="flex-1">
                      <InputField
                        value={formData.rate_structure.trial_lesson_rate?.toString() || ''}
                        onChangeText={value =>
                          handleRateStructureChange('trial_lesson_rate', parseFloat(value) || 0)
                        }
                        placeholder="0"
                        keyboardType="numeric"
                        isDisabled={isLoading}
                      />
                    </Input>
                    <Text className="text-gray-600">/hour</Text>
                  </HStack>
                  {formData.rate_structure.individual_rate > 0 &&
                    formData.rate_structure.trial_lesson_rate && (
                      <FormControlHelper>
                        <Text className="text-green-600">
                          {Math.round(
                            ((formData.rate_structure.individual_rate -
                              formData.rate_structure.trial_lesson_rate) /
                              formData.rate_structure.individual_rate) *
                              100
                          )}
                          % discount from regular rate
                        </Text>
                      </FormControlHelper>
                    )}
                </FormControl>
              )}
            </VStack>
          </Card>

          {/* Group Rate */}
          <Card>
            <VStack space="md" className="p-6">
              <HStack className="items-center justify-between">
                <VStack space="xs">
                  <Heading size="md" className="text-gray-900">
                    Group Lessons (Optional)
                  </Heading>
                  <Text className="text-gray-600 text-sm">
                    Per-student rate for group sessions (2+ students)
                  </Text>
                </VStack>
                <Switch
                  value={hasGroupRate}
                  onValueChange={handleGroupRateToggle}
                  isDisabled={isLoading}
                />
              </HStack>

              {hasGroupRate && (
                <FormControl>
                  <FormControlLabel>
                    <Text>Per Student Rate (Group)</Text>
                  </FormControlLabel>
                  <HStack space="sm" className="items-center">
                    <Text className="text-lg font-medium text-gray-700">{currency.symbol}</Text>
                    <Input className="flex-1">
                      <InputField
                        value={formData.rate_structure.group_rate?.toString() || ''}
                        onChangeText={value =>
                          handleRateStructureChange('group_rate', parseFloat(value) || 0)
                        }
                        placeholder="0"
                        keyboardType="numeric"
                        isDisabled={isLoading}
                      />
                    </Input>
                    <Text className="text-gray-600">/student/hour</Text>
                  </HStack>
                  <FormControlHelper>
                    <Text>Typically 60-80% of your individual rate per student</Text>
                  </FormControlHelper>
                </FormControl>
              )}
            </VStack>
          </Card>

          {/* Package Deals */}
          <Card>
            <VStack space="md" className="p-6">
              <HStack className="items-center justify-between">
                <VStack space="xs">
                  <Heading size="md" className="text-gray-900">
                    Package Deals
                  </Heading>
                  <Text className="text-gray-600 text-sm">
                    Offer discounted rates for bulk lesson purchases
                  </Text>
                </VStack>
                <Button
                  onPress={() => setShowPackageDialog(true)}
                  className="bg-blue-600"
                  size="sm"
                >
                  <ButtonIcon as={Plus} className="text-white mr-2" />
                  <ButtonText className="text-white">Add Package</ButtonText>
                </Button>
              </HStack>

              {formData.rate_structure.package_deals &&
              formData.rate_structure.package_deals.length > 0 ? (
                <VStack space="sm">
                  {formData.rate_structure.package_deals.map(packageDeal => (
                    <Card key={packageDeal.id} className="bg-gray-50">
                      <VStack space="sm" className="p-4">
                        <HStack className="items-start justify-between">
                          <VStack space="xs" className="flex-1">
                            <HStack space="sm" className="items-center">
                              <Text className="font-semibold text-gray-900">
                                {packageDeal.name}
                              </Text>
                              <Badge className="bg-green-100">
                                <BadgeText className="text-green-800">
                                  {packageDeal.discount_percentage}% OFF
                                </BadgeText>
                              </Badge>
                            </HStack>
                            <HStack space="md" className="items-center">
                              <Text className="text-sm text-gray-600">
                                {packageDeal.sessions} sessions
                              </Text>
                              <Text className="text-sm font-medium text-gray-900">
                                {currency.symbol}
                                {packageDeal.price} total
                              </Text>
                              <Text className="text-sm text-gray-600">
                                ({currency.symbol}
                                {Math.round(packageDeal.price / packageDeal.sessions)}/session)
                              </Text>
                            </HStack>
                          </VStack>

                          <HStack space="xs">
                            <Button
                              size="sm"
                              variant="ghost"
                              onPress={() => handleEditPackage(packageDeal)}
                            >
                              <ButtonText className="text-blue-600">Edit</ButtonText>
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              onPress={() => handleDeletePackage(packageDeal.id)}
                            >
                              <ButtonIcon as={X} className="text-red-500" />
                            </Button>
                          </HStack>
                        </HStack>
                      </VStack>
                    </Card>
                  ))}
                </VStack>
              ) : (
                <Box className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                  <VStack space="sm" className="items-center">
                    <Icon as={Package} size={32} className="text-gray-400" />
                    <Text className="text-gray-600">No package deals yet</Text>
                    <Text className="text-sm text-gray-500">
                      Create package deals to encourage students to book multiple sessions
                    </Text>
                  </VStack>
                </Box>
              )}
            </VStack>
          </Card>

          {/* Payment Methods */}
          <Card>
            <VStack space="md" className="p-6">
              <Heading size="md" className="text-gray-900">
                Accepted Payment Methods
              </Heading>

              <VStack space="sm">
                {PAYMENT_METHODS.map(method => (
                  <HStack key={method} space="sm" className="items-center py-2">
                    <Switch
                      value={formData.payment_methods?.includes(method) || false}
                      onValueChange={checked => handlePaymentMethodToggle(method, checked)}
                      isDisabled={isLoading}
                    />
                    <Text className="flex-1">{method}</Text>
                  </HStack>
                ))}
              </VStack>

              <FormControlHelper>
                <Text>Select all payment methods you're comfortable accepting</Text>
              </FormControlHelper>
            </VStack>
          </Card>

          {/* Cancellation Policy */}
          <Card>
            <VStack space="md" className="p-6">
              <Heading size="md" className="text-gray-900">
                Cancellation Policy
              </Heading>

              <FormControl isInvalid={hasFieldError('cancellation_policy')}>
                <VStack space="sm">
                  {CANCELLATION_POLICIES.map(policy => (
                    <Pressable
                      key={policy.value}
                      onPress={() => handleFieldChange('cancellation_policy', policy.value)}
                      className={`p-4 border rounded-lg ${
                        formData.cancellation_policy === policy.value
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-300 bg-white'
                      }`}
                    >
                      <VStack space="xs">
                        <HStack className="items-center justify-between">
                          <Text
                            className={`font-medium ${
                              formData.cancellation_policy === policy.value
                                ? 'text-blue-900'
                                : 'text-gray-900'
                            }`}
                          >
                            {policy.name}
                          </Text>
                          {formData.cancellation_policy === policy.value && (
                            <Icon as={CheckCircle2} size={20} className="text-blue-600" />
                          )}
                        </HStack>
                        <Text
                          className={`text-sm ${
                            formData.cancellation_policy === policy.value
                              ? 'text-blue-700'
                              : 'text-gray-600'
                          }`}
                        >
                          {policy.description}
                        </Text>
                      </VStack>
                    </Pressable>
                  ))}
                </VStack>
                {hasFieldError('cancellation_policy') && (
                  <FormControlError>
                    <Text>{getFieldError('cancellation_policy')}</Text>
                  </FormControlError>
                )}
              </FormControl>
            </VStack>
          </Card>

          {/* Rate Summary */}
          {formData.rate_structure.individual_rate > 0 && (
            <Card className="border-l-4 border-l-green-500 bg-green-50">
              <VStack space="md" className="p-6">
                <HStack space="sm" className="items-center">
                  <Icon as={Calculator} size={20} className="text-green-600" />
                  <Heading size="md" className="text-green-900">
                    Rate Summary
                  </Heading>
                </HStack>

                <VStack space="sm">
                  <HStack className="items-center justify-between">
                    <Text className="text-green-800">Individual lessons:</Text>
                    <Text className="font-semibold text-green-900">
                      {currency.symbol}
                      {formData.rate_structure.individual_rate}/hour
                    </Text>
                  </HStack>

                  {hasTrialLesson && formData.rate_structure.trial_lesson_rate && (
                    <HStack className="items-center justify-between">
                      <Text className="text-green-800">Trial lesson:</Text>
                      <Text className="font-semibold text-green-900">
                        {currency.symbol}
                        {formData.rate_structure.trial_lesson_rate}/hour
                      </Text>
                    </HStack>
                  )}

                  {hasGroupRate && formData.rate_structure.group_rate && (
                    <HStack className="items-center justify-between">
                      <Text className="text-green-800">Group lessons:</Text>
                      <Text className="font-semibold text-green-900">
                        {currency.symbol}
                        {formData.rate_structure.group_rate}/student/hour
                      </Text>
                    </HStack>
                  )}

                  {formData.rate_structure.package_deals &&
                    formData.rate_structure.package_deals.length > 0 && (
                      <HStack className="items-center justify-between">
                        <Text className="text-green-800">Package deals:</Text>
                        <Text className="font-semibold text-green-900">
                          {formData.rate_structure.package_deals.length} available
                        </Text>
                      </HStack>
                    )}
                </VStack>
              </VStack>
            </Card>
          )}

          {/* Validation Errors */}
          {hasFieldError('rate_structure') && (
            <Box className="bg-red-50 border-l-4 border-red-400 p-4">
              <HStack space="sm" className="items-center">
                <Icon as={AlertCircle} size={20} className="text-red-500" />
                <Text className="text-red-700">{getFieldError('rate_structure')}</Text>
              </HStack>
            </Box>
          )}
        </VStack>
      </Box>

      {/* Package Deal Dialog */}
      <AlertDialog isOpen={showPackageDialog} onClose={resetPackageForm}>
        <AlertDialogBackdrop />
        <AlertDialogContent className="max-w-md">
          <AlertDialogHeader>
            <Heading size="lg" className="text-gray-900">
              {editingPackage ? 'Edit Package Deal' : 'Create Package Deal'}
            </Heading>
          </AlertDialogHeader>
          <AlertDialogBody>
            <VStack space="md">
              <FormControl>
                <FormControlLabel>
                  <Text>Package Name *</Text>
                </FormControlLabel>
                <Input>
                  <InputField
                    value={newPackage.name || ''}
                    onChangeText={value => setNewPackage(prev => ({ ...prev, name: value }))}
                    placeholder="e.g., Starter Package, Monthly Bundle"
                  />
                </Input>
              </FormControl>

              <FormControl>
                <FormControlLabel>
                  <Text>Number of Sessions *</Text>
                </FormControlLabel>
                <Select
                  selectedValue={newPackage.sessions?.toString() || '4'}
                  onValueChange={value =>
                    setNewPackage(prev => ({
                      ...prev,
                      sessions: parseInt(value),
                    }))
                  }
                >
                  <SelectTrigger>
                    <SelectInput placeholder="Select sessions" />
                  </SelectTrigger>
                  <SelectContent>
                    {[4, 8, 12, 16, 20, 24].map(num => (
                      <SelectItem key={num} label={`${num} sessions`} value={num.toString()} />
                    ))}
                  </SelectContent>
                </Select>
              </FormControl>

              <FormControl>
                <FormControlLabel>
                  <Text>Discount Percentage *</Text>
                </FormControlLabel>
                <HStack space="sm" className="items-center">
                  <Input className="flex-1">
                    <InputField
                      value={newPackage.discount_percentage?.toString() || ''}
                      onChangeText={value =>
                        setNewPackage(prev => ({
                          ...prev,
                          discount_percentage: parseFloat(value) || 0,
                        }))
                      }
                      placeholder="10"
                      keyboardType="numeric"
                    />
                  </Input>
                  <Text>%</Text>
                </HStack>
                <FormControlHelper>
                  <Text>Typical discounts range from 5-20%</Text>
                </FormControlHelper>
              </FormControl>

              <FormControl>
                <FormControlLabel>
                  <Text>Total Package Price</Text>
                </FormControlLabel>
                <HStack space="sm" className="items-center">
                  <Text>{currency.symbol}</Text>
                  <Input className="flex-1">
                    <InputField
                      value={newPackage.price?.toFixed(2) || '0.00'}
                      onChangeText={value =>
                        setNewPackage(prev => ({
                          ...prev,
                          price: parseFloat(value) || 0,
                        }))
                      }
                      placeholder="0.00"
                      keyboardType="numeric"
                    />
                  </Input>
                </HStack>
                <FormControlHelper>
                  <Text>Auto-calculated based on discount. You can override this value.</Text>
                </FormControlHelper>
              </FormControl>
            </VStack>
          </AlertDialogBody>
          <AlertDialogFooter>
            <HStack space="sm" className="w-full">
              <Button variant="outline" onPress={resetPackageForm} className="flex-1">
                <ButtonText>Cancel</ButtonText>
              </Button>
              <Button
                onPress={handleSavePackage}
                className="flex-1 bg-blue-600"
                isDisabled={!newPackage.name || !newPackage.sessions}
              >
                <ButtonText>{editingPackage ? 'Update Package' : 'Create Package'}</ButtonText>
              </Button>
            </HStack>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </ScrollView>
  );
};
