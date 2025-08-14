import { Euro, TrendingUp, CreditCard, Calendar, ChevronDownIcon, Info } from 'lucide-react-native';
import React, { useState } from 'react';
import { Alert } from 'react-native';

import { TeacherProfileData, PaymentPreferences } from '@/api/invitationApi';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { FormControl } from '@/components/ui/form-control';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Input, InputField } from '@/components/ui/input';
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
import { Slider, SliderTrack, SliderFilledTrack, SliderThumb } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

interface RatesCompensationStepProps {
  profileData: TeacherProfileData;
  updateProfileData: (updates: Partial<TeacherProfileData>) => void;
  validationErrors: { [key: string]: string };
  invitationData: any;
}

const RatesCompensationStep: React.FC<RatesCompensationStepProps> = ({
  profileData,
  updateProfileData,
  validationErrors,
  invitationData,
}) => {
  const [showAdvancedOptions, setShowAdvancedOptions] = useState(false);

  const paymentPreferences = profileData.payment_preferences || {
    preferred_payment_method: 'bank_transfer',
    invoice_frequency: 'monthly',
    tax_information_provided: false,
  };

  const updatePaymentPreference = (key: keyof PaymentPreferences, value: any) => {
    const updatedPreferences = {
      ...paymentPreferences,
      [key]: value,
    };
    updateProfileData({ payment_preferences: updatedPreferences });
  };

  const handleHourlyRateChange = (value: string) => {
    const numValue = parseFloat(value);
    if (!isNaN(numValue)) {
      updateProfileData({ hourly_rate: numValue });
    }
  };

  const handleSliderChange = (value: number[]) => {
    updateProfileData({ hourly_rate: value[0] });
  };

  const getRateCategory = (rate: number): { label: string; color: string; description: string } => {
    if (rate < 15) {
      return {
        label: 'Iniciante',
        color: 'text-green-600',
        description: 'Ideal para professores começando ou com pouca experiência',
      };
    } else if (rate < 30) {
      return {
        label: 'Intermediário',
        color: 'text-blue-600',
        description: 'Para professores com experiência moderada',
      };
    } else if (rate < 50) {
      return {
        label: 'Avançado',
        color: 'text-purple-600',
        description: 'Para professores experientes com especialização',
      };
    } else {
      return {
        label: 'Especialista',
        color: 'text-orange-600',
        description: 'Para especialistas altamente qualificados',
      };
    }
  };

  const suggestedRates = [
    { label: 'Iniciante', range: '€10-15', value: 12 },
    { label: 'Intermediário', range: '€15-30', value: 22 },
    { label: 'Avançado', range: '€30-50', value: 40 },
    { label: 'Especialista', range: '€50+', value: 65 },
  ];

  const rateCategory = getRateCategory(profileData.hourly_rate);

  return (
    <Box className="flex-1">
      <VStack space="lg">
        {/* Header */}
        <VStack space="sm">
          <Heading size="xl" className="text-gray-900">
            Taxas e Compensação
          </Heading>
          <Text className="text-gray-600">
            Defina sua taxa por hora/aula e configure suas preferências de pagamento.
          </Text>
        </VStack>

        {/* Market Rate Information */}
        <Box className="bg-blue-50 p-4 rounded-lg border border-blue-200">
          <VStack space="sm">
            <HStack className="items-center" space="sm">
              <Icon as={TrendingUp} size="sm" className="text-blue-600" />
              <Text className="font-medium text-blue-800">Taxas de Mercado</Text>
            </HStack>
            <VStack space="xs">
              {suggestedRates.map(rate => (
                <HStack key={rate.label} className="justify-between items-center">
                  <Text className="text-sm text-blue-700">{rate.label}:</Text>
                  <HStack space="sm" className="items-center">
                    <Text className="text-sm font-medium text-blue-800">{rate.range}</Text>
                    <Button
                      variant="outline"
                      size="xs"
                      onPress={() => updateProfileData({ hourly_rate: rate.value })}
                    >
                      <ButtonText className="text-xs">Usar</ButtonText>
                    </Button>
                  </HStack>
                </HStack>
              ))}
            </VStack>
          </VStack>
        </Box>

        {/* Hourly Rate */}
        <FormControl className={validationErrors.hourly_rate ? 'error' : ''}>
          <VStack space="md">
            <VStack space="sm">
              <HStack className="items-center justify-between">
                <VStack>
                  <Text className="font-medium">Taxa por Hora/Aula *</Text>
                  <Text className="text-sm text-gray-600">
                    Defina quanto você cobra por hora de aula
                  </Text>
                </VStack>
                <HStack className="items-center" space="sm">
                  <Icon as={Euro} size="sm" className="text-gray-600" />
                  <Text className="text-2xl font-bold text-gray-900">
                    {profileData.hourly_rate.toFixed(0)}
                  </Text>
                  <Text className="text-lg text-gray-600">/hora</Text>
                </HStack>
              </HStack>

              {/* Rate Category */}
              <Box className="bg-gray-50 p-3 rounded-lg">
                <HStack className="items-center justify-between">
                  <VStack>
                    <Text className={`font-medium ${rateCategory.color}`}>
                      Categoria: {rateCategory.label}
                    </Text>
                    <Text className="text-sm text-gray-600">{rateCategory.description}</Text>
                  </VStack>
                </HStack>
              </Box>
            </VStack>

            {/* Slider */}
            <VStack space="sm">
              <Slider
                value={[profileData.hourly_rate]}
                onValueChange={handleSliderChange}
                minValue={5}
                maxValue={100}
                step={1}
                className="w-full"
              >
                <SliderTrack>
                  <SliderFilledTrack />
                </SliderTrack>
                <SliderThumb />
              </Slider>
              <HStack className="justify-between">
                <Text className="text-xs text-gray-500">€5</Text>
                <Text className="text-xs text-gray-500">€100</Text>
              </HStack>
            </VStack>

            {/* Manual Input */}
            <VStack space="sm">
              <Text className="text-sm font-medium">Ou digite o valor exato:</Text>
              <HStack space="sm" className="items-center">
                <Text className="text-lg">€</Text>
                <Input className="flex-1">
                  <InputField
                    placeholder="25"
                    value={profileData.hourly_rate.toString()}
                    onChangeText={handleHourlyRateChange}
                    keyboardType="numeric"
                  />
                </Input>
                <Text className="text-gray-600">/hora</Text>
              </HStack>
            </VStack>

            {validationErrors.hourly_rate && (
              <Text className="text-red-600 text-sm">{validationErrors.hourly_rate}</Text>
            )}
          </VStack>
        </FormControl>

        {/* Rate Negotiable */}
        <HStack className="justify-between items-center py-2">
          <VStack className="flex-1">
            <Text className="font-medium">Taxa Negociável</Text>
            <Text className="text-sm text-gray-600">
              Permitir que a escola negocie um valor diferente
            </Text>
          </VStack>
          <Switch
            value={profileData.rate_negotiable}
            onValueChange={value => updateProfileData({ rate_negotiable: value })}
          />
        </HStack>

        {/* Payment Preferences */}
        <VStack space="md">
          <Heading size="md" className="text-gray-800">
            Preferências de Pagamento
          </Heading>

          {/* Payment Method */}
          <FormControl>
            <VStack space="sm">
              <HStack className="items-center" space="sm">
                <Icon as={CreditCard} size="sm" className="text-gray-600" />
                <Text className="font-medium">Método Preferido de Pagamento</Text>
              </HStack>
              <Select
                selectedValue={paymentPreferences.preferred_payment_method}
                onValueChange={value => updatePaymentPreference('preferred_payment_method', value)}
              >
                <SelectTrigger variant="outline" size="md">
                  <SelectInput placeholder="Selecione o método de pagamento" />
                  <SelectIcon className="mr-3" as={ChevronDownIcon} />
                </SelectTrigger>
                <SelectPortal>
                  <SelectBackdrop />
                  <SelectContent>
                    <SelectDragIndicatorWrapper>
                      <SelectDragIndicator />
                    </SelectDragIndicatorWrapper>
                    <SelectItem label="Transferência Bancária" value="bank_transfer" />
                    <SelectItem label="PayPal" value="paypal" />
                    <SelectItem label="Stripe (Cartão)" value="stripe" />
                  </SelectContent>
                </SelectPortal>
              </Select>
            </VStack>
          </FormControl>

          {/* Invoice Frequency */}
          <FormControl>
            <VStack space="sm">
              <HStack className="items-center" space="sm">
                <Icon as={Calendar} size="sm" className="text-gray-600" />
                <Text className="font-medium">Frequência de Faturamento</Text>
              </HStack>
              <Select
                selectedValue={paymentPreferences.invoice_frequency}
                onValueChange={value => updatePaymentPreference('invoice_frequency', value)}
              >
                <SelectTrigger variant="outline" size="md">
                  <SelectInput placeholder="Selecione a frequência" />
                  <SelectIcon className="mr-3" as={ChevronDownIcon} />
                </SelectTrigger>
                <SelectPortal>
                  <SelectBackdrop />
                  <SelectContent>
                    <SelectDragIndicatorWrapper>
                      <SelectDragIndicator />
                    </SelectDragIndicatorWrapper>
                    <SelectItem label="Semanal" value="weekly" />
                    <SelectItem label="Quinzenal" value="biweekly" />
                    <SelectItem label="Mensal" value="monthly" />
                  </SelectContent>
                </SelectPortal>
              </Select>
            </VStack>
          </FormControl>

          {/* Tax Information */}
          <HStack className="justify-between items-center py-2">
            <VStack className="flex-1">
              <Text className="font-medium">Informações Fiscais Fornecidas</Text>
              <Text className="text-sm text-gray-600">
                Marque se você já forneceu NIF/documento fiscal
              </Text>
            </VStack>
            <Switch
              value={paymentPreferences.tax_information_provided}
              onValueChange={value => updatePaymentPreference('tax_information_provided', value)}
            />
          </HStack>
        </VStack>

        {/* Earnings Projection */}
        <Box className="bg-green-50 p-4 rounded-lg border border-green-200">
          <VStack space="sm">
            <Text className="font-medium text-green-800">Projeção de Ganhos</Text>
            <VStack space="xs">
              <HStack className="justify-between">
                <Text className="text-sm text-green-700">10 horas/semana:</Text>
                <Text className="text-sm font-medium text-green-800">
                  €{(profileData.hourly_rate * 10 * 4).toFixed(0)}/mês
                </Text>
              </HStack>
              <HStack className="justify-between">
                <Text className="text-sm text-green-700">20 horas/semana:</Text>
                <Text className="text-sm font-medium text-green-800">
                  €{(profileData.hourly_rate * 20 * 4).toFixed(0)}/mês
                </Text>
              </HStack>
              <HStack className="justify-between">
                <Text className="text-sm text-green-700">30 horas/semana:</Text>
                <Text className="text-sm font-medium text-green-800">
                  €{(profileData.hourly_rate * 30 * 4).toFixed(0)}/mês
                </Text>
              </HStack>
            </VStack>
          </VStack>
        </Box>

        {/* Help Text */}
        <Box className="bg-yellow-50 p-4 rounded-lg border border-yellow-200">
          <VStack space="sm">
            <HStack className="items-center" space="sm">
              <Icon as={Info} size="sm" className="text-yellow-600" />
              <Text className="font-medium text-yellow-800">Dicas Importantes:</Text>
            </HStack>
            <VStack space="xs" className="ml-2">
              <Text className="text-sm text-yellow-700">
                • Considere sua experiência, qualificações e demanda da matéria
              </Text>
              <Text className="text-sm text-yellow-700">
                • Você pode ajustar suas taxas a qualquer momento
              </Text>
              <Text className="text-sm text-yellow-700">
                • Taxas competitivas ajudam a atrair mais alunos inicialmente
              </Text>
              <Text className="text-sm text-yellow-700">
                • A escola pode ter uma taxa máxima ou faixa recomendada
              </Text>
            </VStack>
          </VStack>
        </Box>
      </VStack>
    </Box>
  );
};

export default RatesCompensationStep;
