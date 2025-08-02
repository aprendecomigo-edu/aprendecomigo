/**
 * ChildAccountSelector Component
 *
 * Multi-child switching component with visual indicators
 * for quick navigation between child accounts.
 */

import { User, ChevronDown, CheckCircle, AlertCircle, Clock } from 'lucide-react-native';
import React, { useMemo } from 'react';

import { ChildProfile } from '@/api/parentApi';
import { Badge } from '@/components/ui/badge';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Pressable } from '@/components/ui/pressable';
import { ScrollView } from '@/components/ui/scroll-view';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

interface ChildAccountSelectorProps {
  children: ChildProfile[];
  selectedChildId: string | null;
  onSelectChild: (childId: string | null) => void;
  showAllOption?: boolean;
  disabled?: boolean;
}

interface ChildStatusIndicator {
  status: 'active' | 'inactive' | 'warning';
  color: string;
  icon: React.ComponentType<any>;
  label: string;
}

export const ChildAccountSelector: React.FC<ChildAccountSelectorProps> = ({
  children,
  selectedChildId,
  onSelectChild,
  showAllOption = true,
  disabled = false,
}) => {
  // Get child status indicator
  const getChildStatus = (child: ChildProfile): ChildStatusIndicator => {
    // TODO: Add logic based on child's recent activity, balance, etc.
    // For now, return active status for all children
    return {
      status: 'active',
      color: 'text-green-600',
      icon: CheckCircle,
      label: 'Active',
    };
  };

  // Memoized child options
  const childOptions = useMemo(() => {
    const options = children.map(child => ({
      id: child.id.toString(),
      label:
        child.child_user.name ||
        `${child.child_user.first_name} ${child.child_user.last_name}`.trim(),
      email: child.child_user.email,
      status: getChildStatus(child),
      isPrimary: child.is_primary_contact,
    }));

    if (showAllOption) {
      options.unshift({
        id: 'all',
        label: 'All Children',
        email: '',
        status: {
          status: 'active' as const,
          color: 'text-blue-600',
          icon: User,
          label: 'Overview',
        },
        isPrimary: false,
      });
    }

    return options;
  }, [children, showAllOption]);

  // Selected child display info
  const selectedChild = useMemo(() => {
    if (!selectedChildId) {
      return showAllOption ? childOptions[0] : null;
    }
    return childOptions.find(child => child.id === selectedChildId) || null;
  }, [selectedChildId, childOptions, showAllOption]);

  // Handle child selection
  const handleSelectChild = (childId: string) => {
    if (disabled) return;
    onSelectChild(childId === 'all' ? null : childId);
  };

  return (
    <VStack className="space-y-2">
      {/* Selected Child Display */}
      <Pressable
        className={`
          bg-gray-50 rounded-lg px-4 py-3 border border-gray-200
          ${disabled ? 'opacity-50' : 'active:bg-gray-100'}
        `}
        disabled={disabled}
      >
        <HStack className="justify-between items-center">
          <HStack className="flex-1 space-x-3">
            <VStack className="items-center justify-center w-8 h-8 bg-blue-100 rounded-full">
              <Icon as={selectedChild?.status.icon || User} size={16} className="text-blue-600" />
            </VStack>

            <VStack className="flex-1">
              <Text className="text-gray-900 font-medium">
                {selectedChild?.label || 'Select Child'}
              </Text>
              {selectedChild?.email && (
                <Text className="text-sm text-gray-600">{selectedChild.email}</Text>
              )}
            </VStack>
          </HStack>

          <HStack className="items-center space-x-2">
            {selectedChild?.isPrimary && (
              <Badge variant="solid" action="info" size="sm">
                <Text className="text-xs font-medium">Primary</Text>
              </Badge>
            )}

            <Badge
              variant="outline"
              action={selectedChild?.status.status === 'active' ? 'success' : 'warning'}
              size="sm"
            >
              <Text className="text-xs font-medium">{selectedChild?.status.label}</Text>
            </Badge>

            <Icon as={ChevronDown} size={16} className="text-gray-400" />
          </HStack>
        </HStack>
      </Pressable>

      {/* Child Options (could be dropdown in web, horizontal scroll on mobile) */}
      <ScrollView horizontal showsHorizontalScrollIndicator={false} className="flex-grow-0">
        <HStack className="space-x-2 px-1 py-1">
          {childOptions.map(child => {
            const isSelected =
              selectedChildId === child.id || (!selectedChildId && child.id === 'all');

            return (
              <Pressable
                key={child.id}
                className={`
                  px-3 py-2 rounded-lg border min-w-24
                  ${
                    isSelected
                      ? 'bg-blue-100 border-blue-300'
                      : 'bg-white border-gray-200 active:bg-gray-50'
                  }
                  ${disabled ? 'opacity-50' : ''}
                `}
                onPress={() => handleSelectChild(child.id)}
                disabled={disabled}
              >
                <VStack className="items-center space-y-1">
                  <HStack className="items-center space-x-1">
                    <Icon
                      as={child.status.icon}
                      size={14}
                      className={isSelected ? 'text-blue-600' : child.status.color}
                    />
                    {child.isPrimary && <VStack className="w-2 h-2 bg-orange-400 rounded-full" />}
                  </HStack>

                  <Text
                    className={`
                      text-xs font-medium text-center
                      ${isSelected ? 'text-blue-900' : 'text-gray-700'}
                    `}
                    numberOfLines={1}
                  >
                    {child.label.split(' ')[0]} {/* Show first name only */}
                  </Text>
                </VStack>
              </Pressable>
            );
          })}
        </HStack>
      </ScrollView>

      {/* Child Count & Status Summary */}
      {children.length > 0 && (
        <HStack className="justify-between items-center px-1">
          <Text className="text-sm text-gray-600">
            {children.length} child{children.length === 1 ? '' : 'ren'} total
          </Text>

          <HStack className="space-x-3">
            <HStack className="items-center space-x-1">
              <VStack className="w-2 h-2 bg-green-400 rounded-full" />
              <Text className="text-xs text-gray-600">
                {children.filter(c => getChildStatus(c).status === 'active').length} active
              </Text>
            </HStack>

            {children.some(c => c.is_primary_contact) && (
              <HStack className="items-center space-x-1">
                <VStack className="w-2 h-2 bg-orange-400 rounded-full" />
                <Text className="text-xs text-gray-600">Primary contact</Text>
              </HStack>
            )}
          </HStack>
        </HStack>
      )}
    </VStack>
  );
};
