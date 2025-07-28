/**
 * Pricing Plan Card Component
 * 
 * Displays individual pricing plan information in a visually appealing card format
 * with responsive design and interactive selection capabilities.
 */

import React, { memo } from 'react';
import { CheckCircle2, Clock, Users, Star } from 'lucide-react-native';
import { Badge } from '@/components/ui/badge';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import type { PricingPlan } from '@/types/purchase';

interface PricingPlanCardProps {
  plan: PricingPlan;
  isSelected?: boolean;
  isPopular?: boolean;
  onSelect: (plan: PricingPlan) => void;
  disabled?: boolean;
  loading?: boolean;
}

/**
 * Individual pricing plan card with selection functionality.
 */
export const PricingPlanCard = memo(function PricingPlanCard({
  plan,
  isSelected = false,
  isPopular = false,
  onSelect,
  disabled = false,
  loading = false,
}: PricingPlanCardProps) {
  const handleSelect = () => {
    if (!disabled && !loading) {
      onSelect(plan);
    }
  };

  // Get plan-specific icon and styling
  const planIcon = plan.plan_type === 'subscription' ? Clock : Users;
  const planColor = plan.plan_type === 'subscription' ? 'text-primary-600' : 'text-secondary-600';
  const buttonVariant = isPopular ? 'solid' : 'outline';
  const buttonAction = isPopular ? 'primary' : 'secondary';

  // Format price display
  const formatPrice = (price: string) => {
    const numPrice = parseFloat(price);
    return numPrice % 1 === 0 ? numPrice.toString() : numPrice.toFixed(2);
  };

  // Calculate value proposition text
  const getValueText = () => {
    if (plan.price_per_hour) {
      const perHour = parseFloat(plan.price_per_hour);
      return `€${formatPrice(plan.price_per_hour)} per hour`;
    }
    return `${plan.hours_included} hours included`;
  };

  return (
    <Card 
      className={`
        relative p-6 border-2 transition-all duration-300 transform hover:scale-105
        ${isSelected ? 'border-primary-500 shadow-lg bg-primary-50' : 'border-outline-200 hover:border-primary-300'}
        ${isPopular ? 'ring-2 ring-primary-500 shadow-xl' : ''}
        ${disabled ? 'opacity-50' : ''}
      `}
    >
      {/* Popular badge */}
      {isPopular && (
        <Badge
          variant="solid"
          action="primary"
          className="absolute -top-3 left-1/2 transform -translate-x-1/2 px-3 py-1"
        >
          <Icon as={Star} size="xs" className="text-white mr-1" />
          <Text className="text-xs font-semibold text-white">Most Popular</Text>
        </Badge>
      )}

      <VStack space="lg" className="flex-1">
        {/* Plan header */}
        <VStack space="sm">
          <HStack space="sm" className="items-center">
            <Icon as={planIcon} size="lg" className={planColor} />
            <Heading size="lg" className="text-typography-900 flex-1">
              {plan.name}
            </Heading>
            {isSelected && (
              <Icon as={CheckCircle2} size="md" className="text-primary-600" />
            )}
          </HStack>

          {/* Price display */}
          <HStack className="items-baseline">
            <Text className="text-4xl font-extrabold text-typography-900">
              €{formatPrice(plan.price_eur)}
            </Text>
            <Text className="text-lg font-medium text-typography-600 ml-1">
              {plan.plan_type === 'subscription' ? '/month' : 'one-time'}
            </Text>
          </HStack>

          {/* Value proposition */}
          <Text className="text-sm font-medium text-typography-700">
            {getValueText()}
          </Text>
        </VStack>

        {/* Plan description */}
        <Text className="text-typography-600 leading-relaxed">
          {plan.description}
        </Text>

        {/* Plan features */}
        <VStack space="sm" className="flex-1">
          <HStack space="xs" className="items-center">
            <Icon as={CheckCircle2} size="sm" className="text-success-600 flex-shrink-0" />
            <Text className="text-sm text-typography-700 flex-1">
              {plan.hours_included} tutoring hours
            </Text>
          </HStack>

          <HStack space="xs" className="items-center">
            <Icon as={CheckCircle2} size="sm" className="text-success-600 flex-shrink-0" />
            <Text className="text-sm text-typography-700 flex-1">
              Access to all subjects
            </Text>
          </HStack>

          {plan.plan_type === 'subscription' ? (
            <HStack space="xs" className="items-center">
              <Icon as={CheckCircle2} size="sm" className="text-success-600 flex-shrink-0" />
              <Text className="text-sm text-typography-700 flex-1">
                Cancel anytime
              </Text>
            </HStack>
          ) : (
            <>
              <HStack space="xs" className="items-center">
                <Icon as={CheckCircle2} size="sm" className="text-success-600 flex-shrink-0" />
                <Text className="text-sm text-typography-700 flex-1">
                  No recurring charges
                </Text>
              </HStack>
              {plan.validity_days && (
                <HStack space="xs" className="items-center">
                  <Icon as={CheckCircle2} size="sm" className="text-success-600 flex-shrink-0" />
                  <Text className="text-sm text-typography-700 flex-1">
                    Valid for {Math.round(plan.validity_days / 30)} months
                  </Text>
                </HStack>
              )}
            </>
          )}
        </VStack>

        {/* Selection button */}
        <Button
          action={buttonAction}
          variant={buttonVariant}
          size="lg"
          className="w-full mt-4"
          onPress={handleSelect}
          disabled={disabled || loading}
        >
          <ButtonText className="font-semibold">
            {isSelected ? 'Selected' : 'Choose Plan'}
          </ButtonText>
        </Button>
      </VStack>
    </Card>
  );
});