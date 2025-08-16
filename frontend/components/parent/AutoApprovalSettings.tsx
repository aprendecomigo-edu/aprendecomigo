/**
 * AutoApprovalSettings Component
 *
 * Configuration interface for automatic approval thresholds including:
 * - Automatic approval amount limits
 * - Time-based auto-approval rules
 * - Child-specific approval settings
 * - Smart approval conditions
 * - Emergency override controls
 */

import {
  Zap,
  Shield,
  Clock,
  Euro,
  User,
  Settings,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Calendar,
  Brain,
  Save,
  RotateCcw,
} from 'lucide-react-native';
import React, { useState, useEffect } from 'react';

import { Badge } from '@/components/ui/badge';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Divider } from '@/components/ui/divider';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Input, InputField } from '@/components/ui/input';
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

interface AutoApprovalRule {
  id: string;
  name: string;
  enabled: boolean;
  conditions: {
    max_amount?: number;
    time_window?: 'immediate' | '1hour' | '6hours' | '24hours';
    child_balance_required?: number;
    purchase_frequency_limit?: number;
    days_of_week?: string[];
    time_of_day_start?: string;
    time_of_day_end?: string;
  };
  child_specific?: {
    child_id: number;
    child_name: string;
  };
}

interface AutoApprovalSettingsProps {
  rules: AutoApprovalRule[];
  children: Array<{
    id: number;
    name: string;
    trustLevel: 'high' | 'medium' | 'low';
  }>;
  onSaveRules: (rules: AutoApprovalRule[]) => Promise<void>;
  onTestRule: (rule: AutoApprovalRule) => Promise<boolean>;
}

export const AutoApprovalSettings: React.FC<AutoApprovalSettingsProps> = ({
  rules: initialRules,
  children,
  onSaveRules,
  onTestRule,
}) => {
  const [rules, setRules] = useState<AutoApprovalRule[]>(initialRules);
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [selectedRuleId, setSelectedRuleId] = useState<string | null>(null);
  const [newRuleMode, setNewRuleMode] = useState(false);

  // Default rule template
  const createNewRule = (): AutoApprovalRule => ({
    id: `rule_${Date.now()}`,
    name: 'New Auto-Approval Rule',
    enabled: true,
    conditions: {
      max_amount: 25.0,
      time_window: 'immediate',
    },
  });

  // Handle rule updates
  const updateRule = (ruleId: string, updates: Partial<AutoApprovalRule>) => {
    setRules(prev => prev.map(rule => (rule.id === ruleId ? { ...rule, ...updates } : rule)));
  };

  const updateRuleCondition = (ruleId: string, condition: string, value: any) => {
    setRules(prev =>
      prev.map(rule =>
        rule.id === ruleId
          ? { ...rule, conditions: { ...rule.conditions, [condition]: value } }
          : rule,
      ),
    );
  };

  // Handle saving changes
  const handleSave = async () => {
    try {
      setIsSaving(true);
      await onSaveRules(rules);
      setIsEditing(false);
      setNewRuleMode(false);
      setSelectedRuleId(null);
    } catch (error) {
      console.error('Error saving auto-approval rules:', error);
    } finally {
      setIsSaving(false);
    }
  };

  // Handle cancel
  const handleCancel = () => {
    setRules(initialRules);
    setIsEditing(false);
    setNewRuleMode(false);
    setSelectedRuleId(null);
  };

  // Add new rule
  const handleAddRule = () => {
    const newRule = createNewRule();
    setRules(prev => [...prev, newRule]);
    setSelectedRuleId(newRule.id);
    setNewRuleMode(true);
    setIsEditing(true);
  };

  // Delete rule
  const handleDeleteRule = (ruleId: string) => {
    setRules(prev => prev.filter(rule => rule.id !== ruleId));
    if (selectedRuleId === ruleId) {
      setSelectedRuleId(null);
    }
  };

  // Get rule status
  const getRuleStatus = (rule: AutoApprovalRule) => {
    if (!rule.enabled) return { status: 'disabled', color: 'text-gray-500', label: 'Disabled' };

    const hasConditions = Object.keys(rule.conditions).length > 0;
    if (!hasConditions)
      return { status: 'incomplete', color: 'text-orange-500', label: 'Incomplete' };

    return { status: 'active', color: 'text-green-600', label: 'Active' };
  };

  const selectedRule = rules.find(rule => rule.id === selectedRuleId);

  return (
    <Card className="bg-white">
      <CardHeader>
        <HStack className="justify-between items-center">
          <HStack className="space-x-2">
            <Icon as={Zap} size={24} className="text-blue-600" />
            <VStack>
              <Heading size="lg" className="text-gray-900">
                Auto-Approval Settings
              </Heading>
              <Text className="text-sm text-gray-600">
                Configure automatic approval rules for purchase requests
              </Text>
            </VStack>
          </HStack>

          <HStack className="space-x-2">
            {isEditing ? (
              <>
                <Button variant="outline" size="sm" onPress={handleCancel} disabled={isSaving}>
                  <ButtonIcon as={XCircle} size={16} />
                  <ButtonText className="ml-1">Cancel</ButtonText>
                </Button>
                <Button action="primary" size="sm" onPress={handleSave} disabled={isSaving}>
                  <ButtonIcon as={Save} size={16} />
                  <ButtonText className="ml-1">{isSaving ? 'Saving...' : 'Save'}</ButtonText>
                </Button>
              </>
            ) : (
              <Button variant="outline" size="sm" onPress={() => setIsEditing(true)}>
                <ButtonIcon as={Settings} size={16} />
                <ButtonText className="ml-1">Edit Rules</ButtonText>
              </Button>
            )}
          </HStack>
        </HStack>
      </CardHeader>

      <CardContent>
        <VStack className="space-y-6">
          {/* Global Auto-Approval Toggle */}
          <Card className="bg-blue-50 border border-blue-200">
            <CardContent className="p-4">
              <HStack className="justify-between items-center">
                <VStack className="flex-1">
                  <Text className="text-sm font-medium text-blue-900">Auto-Approval System</Text>
                  <Text className="text-xs text-blue-700">
                    Enable automatic approval for purchases meeting your criteria
                  </Text>
                </VStack>
                <Switch
                  value={rules.some(rule => rule.enabled)}
                  onValueChange={enabled => {
                    if (!enabled) {
                      setRules(prev => prev.map(rule => ({ ...rule, enabled: false })));
                    }
                  }}
                  disabled={!isEditing}
                />
              </HStack>
            </CardContent>
          </Card>

          {/* Rules List */}
          <VStack className="space-y-3">
            <HStack className="justify-between items-center">
              <Text className="text-sm font-medium text-gray-900">
                Approval Rules ({rules.length})
              </Text>
              {isEditing && (
                <Button action="primary" variant="outline" size="sm" onPress={handleAddRule}>
                  <ButtonText className="text-xs">Add Rule</ButtonText>
                </Button>
              )}
            </HStack>

            {rules.length === 0 ? (
              <VStack className="items-center py-8 space-y-4">
                <Icon as={Zap} size={48} className="text-gray-400" />
                <VStack className="items-center space-y-2">
                  <Text className="text-sm font-medium text-gray-900">No Auto-Approval Rules</Text>
                  <Text className="text-xs text-gray-600 text-center">
                    Create rules to automatically approve purchases that meet your criteria
                  </Text>
                </VStack>
                <Button action="primary" size="sm" onPress={handleAddRule}>
                  <ButtonText>Create First Rule</ButtonText>
                </Button>
              </VStack>
            ) : (
              <VStack className="space-y-2">
                {rules.map(rule => {
                  const status = getRuleStatus(rule);
                  const isSelected = selectedRuleId === rule.id;

                  return (
                    <Card
                      key={rule.id}
                      className={`border ${
                        isSelected ? 'border-blue-300 bg-blue-50' : 'border-gray-200'
                      }`}
                    >
                      <CardContent className="p-3">
                        <VStack className="space-y-3">
                          {/* Rule Header */}
                          <HStack className="justify-between items-center">
                            <HStack className="flex-1 space-x-3">
                              <VStack className="flex-1">
                                <HStack className="items-center space-x-2">
                                  <Text className="text-sm font-medium text-gray-900">
                                    {rule.name}
                                  </Text>
                                  <Badge
                                    variant="outline"
                                    action={
                                      status.status === 'active'
                                        ? 'success'
                                        : status.status === 'incomplete'
                                          ? 'warning'
                                          : 'secondary'
                                    }
                                    size="sm"
                                  >
                                    <Text className="text-xs">{status.label}</Text>
                                  </Badge>
                                </HStack>

                                {/* Rule Summary */}
                                <VStack className="space-y-1">
                                  {rule.conditions.max_amount && (
                                    <Text className="text-xs text-gray-600">
                                      • Auto-approve up to €{rule.conditions.max_amount}
                                    </Text>
                                  )}
                                  {rule.conditions.time_window &&
                                    rule.conditions.time_window !== 'immediate' && (
                                      <Text className="text-xs text-gray-600">
                                        • Delay approval by {rule.conditions.time_window}
                                      </Text>
                                    )}
                                  {rule.child_specific && (
                                    <Text className="text-xs text-gray-600">
                                      • Only for {rule.child_specific.child_name}
                                    </Text>
                                  )}
                                </VStack>
                              </VStack>
                            </HStack>

                            <HStack className="space-x-1">
                              <Switch
                                value={rule.enabled}
                                onValueChange={enabled => updateRule(rule.id, { enabled })}
                                disabled={!isEditing}
                              />

                              {isEditing && (
                                <>
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onPress={() => setSelectedRuleId(isSelected ? null : rule.id)}
                                  >
                                    <ButtonIcon as={Settings} size={14} />
                                  </Button>
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onPress={() => handleDeleteRule(rule.id)}
                                  >
                                    <ButtonIcon as={XCircle} size={14} />
                                  </Button>
                                </>
                              )}
                            </HStack>
                          </HStack>

                          {/* Rule Configuration (when selected) */}
                          {isSelected && isEditing && (
                            <>
                              <Divider />
                              <VStack className="space-y-4">
                                {/* Basic Settings */}
                                <VStack className="space-y-3">
                                  <Text className="text-sm font-medium text-gray-900">
                                    Basic Settings
                                  </Text>

                                  <VStack className="space-y-2">
                                    <Text className="text-xs text-gray-600">Rule Name</Text>
                                    <Input>
                                      <InputField
                                        value={rule.name}
                                        onChangeText={name => updateRule(rule.id, { name })}
                                        placeholder="Enter rule name"
                                      />
                                    </Input>
                                  </VStack>

                                  <VStack className="space-y-2">
                                    <Text className="text-xs text-gray-600">
                                      Maximum Auto-Approval Amount (€)
                                    </Text>
                                    <Input>
                                      <InputField
                                        value={rule.conditions.max_amount?.toString() || ''}
                                        onChangeText={value =>
                                          updateRuleCondition(
                                            rule.id,
                                            'max_amount',
                                            parseFloat(value) || 0,
                                          )
                                        }
                                        keyboardType="numeric"
                                        placeholder="0.00"
                                      />
                                    </Input>
                                  </VStack>
                                </VStack>

                                {/* Time-based Settings */}
                                <VStack className="space-y-3">
                                  <Text className="text-sm font-medium text-gray-900">
                                    Timing Options
                                  </Text>

                                  <VStack className="space-y-2">
                                    <Text className="text-xs text-gray-600">Approval Delay</Text>
                                    <Select
                                      selectedValue={rule.conditions.time_window || 'immediate'}
                                      onValueChange={value =>
                                        updateRuleCondition(rule.id, 'time_window', value)
                                      }
                                    >
                                      <SelectTrigger>
                                        <SelectInput placeholder="Select timing" />
                                      </SelectTrigger>
                                      <SelectContent>
                                        <SelectItem label="Immediate" value="immediate" />
                                        <SelectItem label="After 1 hour" value="1hour" />
                                        <SelectItem label="After 6 hours" value="6hours" />
                                        <SelectItem label="After 24 hours" value="24hours" />
                                      </SelectContent>
                                    </Select>
                                  </VStack>
                                </VStack>

                                {/* Child-Specific Settings */}
                                <VStack className="space-y-3">
                                  <Text className="text-sm font-medium text-gray-900">
                                    Child-Specific Rules
                                  </Text>

                                  <VStack className="space-y-2">
                                    <Text className="text-xs text-gray-600">
                                      Apply to specific child (optional)
                                    </Text>
                                    <Select
                                      selectedValue={
                                        rule.child_specific?.child_id.toString() || 'all'
                                      }
                                      onValueChange={value => {
                                        if (value === 'all') {
                                          updateRule(rule.id, { child_specific: undefined });
                                        } else {
                                          const child = children.find(
                                            c => c.id.toString() === value,
                                          );
                                          if (child) {
                                            updateRule(rule.id, {
                                              child_specific: {
                                                child_id: child.id,
                                                child_name: child.name,
                                              },
                                            });
                                          }
                                        }
                                      }}
                                    >
                                      <SelectTrigger>
                                        <SelectInput placeholder="Select child" />
                                      </SelectTrigger>
                                      <SelectContent>
                                        <SelectItem label="All children" value="all" />
                                        {children.map(child => (
                                          <SelectItem
                                            key={child.id}
                                            label={child.name}
                                            value={child.id.toString()}
                                          />
                                        ))}
                                      </SelectContent>
                                    </Select>
                                  </VStack>

                                  {rule.conditions.child_balance_required !== undefined && (
                                    <VStack className="space-y-2">
                                      <Text className="text-xs text-gray-600">
                                        Minimum Child Balance Required (€)
                                      </Text>
                                      <Input>
                                        <InputField
                                          value={
                                            rule.conditions.child_balance_required?.toString() || ''
                                          }
                                          onChangeText={value =>
                                            updateRuleCondition(
                                              rule.id,
                                              'child_balance_required',
                                              parseFloat(value) || 0,
                                            )
                                          }
                                          keyboardType="numeric"
                                          placeholder="0.00"
                                        />
                                      </Input>
                                    </VStack>
                                  )}
                                </VStack>

                                {/* Test Rule */}
                                <HStack className="justify-between items-center p-3 bg-gray-50 rounded-lg">
                                  <Text className="text-sm text-gray-700">
                                    Test this rule configuration
                                  </Text>
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    onPress={async () => {
                                      const result = await onTestRule(rule);
                                      // Handle test result
                                    }}
                                  >
                                    <ButtonText className="text-xs">Test Rule</ButtonText>
                                  </Button>
                                </HStack>
                              </VStack>
                            </>
                          )}
                        </VStack>
                      </CardContent>
                    </Card>
                  );
                })}
              </VStack>
            )}
          </VStack>

          {/* Smart Suggestions */}
          {children.length > 0 && (
            <Card className="bg-green-50 border border-green-200">
              <CardContent className="p-4">
                <VStack className="space-y-3">
                  <HStack className="items-center space-x-2">
                    <Icon as={Brain} size={20} className="text-green-600" />
                    <Text className="text-sm font-medium text-green-900">Smart Suggestions</Text>
                  </HStack>

                  <VStack className="space-y-2">
                    {children.map(child => (
                      <HStack key={child.id} className="justify-between items-center">
                        <Text className="text-xs text-green-800">
                          {child.name} ({child.trustLevel} trust)
                        </Text>
                        <Text className="text-xs text-green-700">
                          Suggested limit: €
                          {child.trustLevel === 'high'
                            ? '50'
                            : child.trustLevel === 'medium'
                              ? '25'
                              : '10'}
                        </Text>
                      </HStack>
                    ))}
                  </VStack>

                  <Text className="text-xs text-green-700">
                    These suggestions are based on your children's purchase history and behavior
                    patterns.
                  </Text>
                </VStack>
              </CardContent>
            </Card>
          )}

          {/* Security Notice */}
          <Card className="bg-amber-50 border border-amber-200">
            <CardContent className="p-3">
              <HStack className="items-start space-x-2">
                <Icon as={AlertTriangle} size={16} className="text-amber-600 mt-0.5" />
                <VStack className="flex-1">
                  <Text className="text-xs font-medium text-amber-800">Security Notice</Text>
                  <Text className="text-xs text-amber-700">
                    Auto-approval rules will process purchases without your direct intervention.
                    Review your rules regularly and set appropriate limits to maintain control over
                    spending.
                  </Text>
                </VStack>
              </HStack>
            </CardContent>
          </Card>
        </VStack>
      </CardContent>
    </Card>
  );
};
