/**
 * BudgetControlSettings Component
 *
 * Component for managing child budget controls including
 * spending limits and approval thresholds.
 */

import {
  Shield,
  Edit,
  Save,
  X,
  AlertCircle,
  CheckCircle,
  Euro,
  Calendar,
  Clock,
} from 'lucide-react-native';
import React, { useState } from 'react';

import { FamilyBudgetControl } from '@/api/parentApi';
import { Badge } from '@/components/ui/badge';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Input, InputField } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

interface BudgetControlSettingsProps {
  childId: string;
  budgetControl: FamilyBudgetControl | null;
  onUpdate: (budgetData: Partial<FamilyBudgetControl>) => Promise<void>;
}

export const BudgetControlSettings: React.FC<BudgetControlSettingsProps> = ({
  childId,
  budgetControl,
  onUpdate,
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [formData, setFormData] = useState({
    monthly_limit: budgetControl?.monthly_limit || '',
    weekly_limit: budgetControl?.weekly_limit || '',
    daily_limit: budgetControl?.daily_limit || '',
    requires_approval_above: budgetControl?.requires_approval_above || '50.00',
    is_active: budgetControl?.is_active ?? true,
  });

  // Handle form field changes
  const handleFieldChange = (field: string, value: string | boolean) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  // Validate form data
  const validateForm = () => {
    const errors: string[] = [];

    // Check for valid numbers
    const numericFields = [
      'monthly_limit',
      'weekly_limit',
      'daily_limit',
      'requires_approval_above',
    ];
    numericFields.forEach(field => {
      const value = formData[field as keyof typeof formData] as string;
      if (value && (isNaN(parseFloat(value)) || parseFloat(value) < 0)) {
        errors.push(`${field.replace('_', ' ')} must be a valid positive number`);
      }
    });

    // Check logical constraints
    if (formData.weekly_limit && formData.monthly_limit) {
      const weekly = parseFloat(formData.weekly_limit);
      const monthly = parseFloat(formData.monthly_limit);
      if (weekly * 4 > monthly) {
        errors.push('Weekly limit should be reasonable compared to monthly limit');
      }
    }

    return errors;
  };

  // Handle save
  const handleSave = async () => {
    const errors = validateForm();
    if (errors.length > 0) {
      // TODO: Show validation errors
      console.error('Validation errors:', errors);
      return;
    }

    try {
      setIsLoading(true);

      // Convert empty strings to null for optional fields
      const cleanData = {
        ...formData,
        monthly_limit: formData.monthly_limit || null,
        weekly_limit: formData.weekly_limit || null,
        daily_limit: formData.daily_limit || null,
      };

      await onUpdate(cleanData);
      setIsEditing(false);
    } catch (error) {
      console.error('Error updating budget control:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle cancel
  const handleCancel = () => {
    setFormData({
      monthly_limit: budgetControl?.monthly_limit || '',
      weekly_limit: budgetControl?.weekly_limit || '',
      daily_limit: budgetControl?.daily_limit || '',
      requires_approval_above: budgetControl?.requires_approval_above || '50.00',
      is_active: budgetControl?.is_active ?? true,
    });
    setIsEditing(false);
  };

  return (
    <Card className="bg-white">
      <CardHeader className="pb-3">
        <HStack className="justify-between items-center">
          <HStack className="space-x-2">
            <Icon as={Shield} size={20} className="text-blue-600" />
            <Heading size="md" className="text-gray-900">
              Budget Controls
            </Heading>
          </HStack>

          <HStack className="space-x-2">
            {budgetControl && (
              <Badge
                variant="outline"
                action={budgetControl.is_active ? 'success' : 'secondary'}
                size="sm"
              >
                <Text className="text-xs font-medium">
                  {budgetControl.is_active ? 'Active' : 'Inactive'}
                </Text>
              </Badge>
            )}

            {!isEditing ? (
              <Button variant="outline" size="sm" onPress={() => setIsEditing(true)}>
                <ButtonIcon as={Edit} size={14} />
                <ButtonText className="ml-1">{budgetControl ? 'Edit' : 'Set up'}</ButtonText>
              </Button>
            ) : (
              <HStack className="space-x-1">
                <Button variant="outline" size="sm" onPress={handleCancel} disabled={isLoading}>
                  <ButtonIcon as={X} size={14} />
                </Button>
                <Button action="primary" size="sm" onPress={handleSave} disabled={isLoading}>
                  <ButtonIcon as={Save} size={14} />
                </Button>
              </HStack>
            )}
          </HStack>
        </HStack>
      </CardHeader>

      <CardContent>
        {!budgetControl && !isEditing ? (
          // No budget controls set up
          <VStack className="items-center py-8 space-y-4">
            <Icon as={Shield} size={48} className="text-gray-400" />
            <Heading size="sm" className="text-gray-900 text-center">
              No Budget Controls Set
            </Heading>
            <Text className="text-gray-600 text-center max-w-sm">
              Set spending limits and approval thresholds to manage your child's purchases.
            </Text>
            <Button action="primary" size="sm" onPress={() => setIsEditing(true)}>
              <ButtonText>Set Up Controls</ButtonText>
            </Button>
          </VStack>
        ) : (
          // Budget controls form/display
          <VStack className="space-y-4">
            {/* Active/Inactive Toggle */}
            <HStack className="justify-between items-center p-3 bg-gray-50 rounded-lg">
              <VStack className="flex-1">
                <Text className="text-sm font-medium text-gray-900">Budget Controls</Text>
                <Text className="text-xs text-gray-600">
                  Enable spending limits and approval requirements
                </Text>
              </VStack>
              <Switch
                value={formData.is_active}
                onValueChange={value => handleFieldChange('is_active', value)}
                disabled={!isEditing}
              />
            </HStack>

            {/* Spending Limits */}
            <VStack className="space-y-3">
              <Text className="text-sm font-medium text-gray-700">Spending Limits</Text>

              {/* Monthly Limit */}
              <VStack className="space-y-1">
                <Text className="text-xs text-gray-600">Monthly Limit (€)</Text>
                <HStack className="items-center space-x-2">
                  <Icon as={Calendar} size={16} className="text-gray-500" />
                  <Input className="flex-1">
                    <InputField
                      placeholder="No limit"
                      value={formData.monthly_limit}
                      onChangeText={value => handleFieldChange('monthly_limit', value)}
                      keyboardType="numeric"
                      editable={isEditing}
                    />
                  </Input>
                </HStack>
              </VStack>

              {/* Weekly Limit */}
              <VStack className="space-y-1">
                <Text className="text-xs text-gray-600">Weekly Limit (€)</Text>
                <HStack className="items-center space-x-2">
                  <Icon as={Calendar} size={16} className="text-gray-500" />
                  <Input className="flex-1">
                    <InputField
                      placeholder="No limit"
                      value={formData.weekly_limit}
                      onChangeText={value => handleFieldChange('weekly_limit', value)}
                      keyboardType="numeric"
                      editable={isEditing}
                    />
                  </Input>
                </HStack>
              </VStack>

              {/* Daily Limit */}
              <VStack className="space-y-1">
                <Text className="text-xs text-gray-600">Daily Limit (€)</Text>
                <HStack className="items-center space-x-2">
                  <Icon as={Clock} size={16} className="text-gray-500" />
                  <Input className="flex-1">
                    <InputField
                      placeholder="No limit"
                      value={formData.daily_limit}
                      onChangeText={value => handleFieldChange('daily_limit', value)}
                      keyboardType="numeric"
                      editable={isEditing}
                    />
                  </Input>
                </HStack>
              </VStack>
            </VStack>

            {/* Approval Threshold */}
            <VStack className="space-y-3">
              <Text className="text-sm font-medium text-gray-700">Approval Settings</Text>

              <VStack className="space-y-1">
                <Text className="text-xs text-gray-600">
                  Require approval for purchases above (€)
                </Text>
                <HStack className="items-center space-x-2">
                  <Icon as={Euro} size={16} className="text-gray-500" />
                  <Input className="flex-1">
                    <InputField
                      value={formData.requires_approval_above}
                      onChangeText={value => handleFieldChange('requires_approval_above', value)}
                      keyboardType="numeric"
                      editable={isEditing}
                    />
                  </Input>
                </HStack>
                <Text className="text-xs text-gray-500">
                  Purchases above this amount will require your approval
                </Text>
              </VStack>
            </VStack>

            {/* Current Status Summary */}
            {budgetControl && !isEditing && (
              <VStack className="p-3 bg-blue-50 rounded-lg space-y-2">
                <HStack className="items-center space-x-2">
                  <Icon as={CheckCircle} size={16} className="text-blue-600" />
                  <Text className="text-sm font-medium text-blue-900">Budget Controls Active</Text>
                </HStack>

                <VStack className="space-y-1">
                  {budgetControl.monthly_limit && (
                    <Text className="text-xs text-blue-800">
                      • Monthly limit: €{budgetControl.monthly_limit}
                    </Text>
                  )}
                  {budgetControl.weekly_limit && (
                    <Text className="text-xs text-blue-800">
                      • Weekly limit: €{budgetControl.weekly_limit}
                    </Text>
                  )}
                  {budgetControl.daily_limit && (
                    <Text className="text-xs text-blue-800">
                      • Daily limit: €{budgetControl.daily_limit}
                    </Text>
                  )}
                  <Text className="text-xs text-blue-800">
                    • Approval required above: €{budgetControl.requires_approval_above}
                  </Text>
                </VStack>
              </VStack>
            )}
          </VStack>
        )}
      </CardContent>
    </Card>
  );
};
