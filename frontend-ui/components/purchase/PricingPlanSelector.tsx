/**
 * Pricing Plan Selector Component
 * 
 * Displays a grid of pricing plan cards with loading and error states.
 * Handles plan selection and provides responsive layout across platforms.
 */

import React from 'react';
import { RefreshCw, AlertCircle } from 'lucide-react-native';
import { Alert } from '@/components/ui/alert';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Grid } from '@/components/ui/grid';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { PricingPlanCard } from './PricingPlanCard';
import { usePricingPlans } from '@/hooks/usePricingPlans';
import type { PricingPlan } from '@/types/purchase';

interface PricingPlanSelectorProps {
  selectedPlan?: PricingPlan | null;
  onPlanSelect: (plan: PricingPlan) => void;
  disabled?: boolean;
  className?: string;
}

/**
 * Component for selecting pricing plans with comprehensive loading and error handling.
 */
export function PricingPlanSelector({
  selectedPlan,
  onPlanSelect,
  disabled = false,
  className = '',
}: PricingPlanSelectorProps) {
  const { plans, loading, error, refetch } = usePricingPlans();

  // Determine which plan should be marked as "popular"
  const getPopularPlanId = (plans: PricingPlan[]): number | null => {
    if (plans.length === 0) return null;
    
    // Look for a plan explicitly marked as popular in the backend
    // For now, we'll use the one-time package as popular choice
    const oneTimePackage = plans.find(plan => plan.plan_type === 'package');
    return oneTimePackage?.id || plans[0]?.id || null;
  };

  const popularPlanId = getPopularPlanId(plans);

  if (loading) {
    return (
      <VStack space="lg" className={`items-center py-12 ${className}`}>
        <Spinner size="large" />
        <Text className="text-typography-600 text-center">
          Loading pricing plans...
        </Text>
      </VStack>
    );
  }

  if (error) {
    return (
      <VStack space="lg" className={`py-8 ${className}`}>
        <Alert action="error" variant="solid" className="w-full">
          <Icon as={AlertCircle} className="text-error-600" />
          <VStack space="sm" className="flex-1">
            <Heading size="sm" className="text-error-900">
              Failed to Load Pricing Plans
            </Heading>
            <Text className="text-error-800 text-sm">
              {error}
            </Text>
          </VStack>
        </Alert>
        
        <Button
          action="secondary"
          variant="outline"
          onPress={refetch}
          className="self-center"
        >
          <ButtonIcon as={RefreshCw} />
          <ButtonText>Try Again</ButtonText>
        </Button>
      </VStack>
    );
  }

  if (plans.length === 0) {
    return (
      <VStack space="lg" className={`items-center py-12 ${className}`}>
        <Icon as={AlertCircle} size="xl" className="text-typography-400" />
        <VStack space="sm" className="items-center">
          <Heading size="lg" className="text-typography-600">
            No Plans Available
          </Heading>
          <Text className="text-typography-500 text-center max-w-80">
            There are currently no pricing plans available. Please check back later.
          </Text>
        </VStack>
        <Button
          action="secondary"
          variant="outline"
          onPress={refetch}
        >
          <ButtonIcon as={RefreshCw} />
          <ButtonText>Refresh</ButtonText>
        </Button>
      </VStack>
    );
  }

  return (
    <VStack space="lg" className={className}>
      {/* Section header */}
      <VStack space="sm" className="text-center">
        <Heading size="2xl" className="text-typography-900">
          Choose Your Plan
        </Heading>
        <Text className="text-lg text-typography-600 max-w-2xl mx-auto">
          Select the tutoring plan that best fits your learning needs and budget.
        </Text>
      </VStack>

      {/* Plans grid */}
      <Grid
        className="w-full gap-6 grid-cols-1 md:grid-cols-2 max-w-4xl mx-auto"
        // For smaller screens, stack vertically; for larger screens, use 2 columns
      >
        {plans.map((plan) => (
          <PricingPlanCard
            key={plan.id}
            plan={plan}
            isSelected={selectedPlan?.id === plan.id}
            isPopular={plan.id === popularPlanId}
            onSelect={onPlanSelect}
            disabled={disabled}
          />
        ))}
      </Grid>

      {/* Help text */}
      <VStack space="xs" className="items-center mt-8">
        <Text className="text-sm text-typography-500 text-center">
          Need help choosing? Contact us for personalized recommendations.
        </Text>
        <HStack space="xs" className="items-center">
          <Text className="text-xs text-typography-400">
            All plans include access to qualified tutors and secure scheduling.
          </Text>
        </HStack>
      </VStack>
    </VStack>
  );
}