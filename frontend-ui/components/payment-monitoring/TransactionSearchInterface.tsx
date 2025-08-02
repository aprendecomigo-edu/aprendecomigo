/**
 * Transaction Search Interface Component - GitHub Issue #118
 *
 * Advanced search interface for transaction management with filters,
 * saved searches, and real-time query building.
 */

import {
  Search,
  Filter,
  X,
  Save,
  Bookmark,
  Calendar,
  DollarSign,
  CreditCard,
  AlertTriangle,
} from 'lucide-react-native';
import React, { useState, useCallback } from 'react';

import { Badge } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { FormControl, FormControlLabel } from '@/components/ui/form-control';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Input } from '@/components/ui/input';
import {
  Modal,
  ModalBackdrop,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
} from '@/components/ui/modal';
import { Pressable } from '@/components/ui/pressable';
import { Select, SelectTrigger, SelectContent, SelectItem } from '@/components/ui/select';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import type { TransactionSearchFilters, SavedSearch } from '@/types/paymentMonitoring';

interface TransactionSearchInterfaceProps {
  filters: TransactionSearchFilters;
  onFiltersChange: (filters: TransactionSearchFilters) => void;
  savedSearches: SavedSearch[];
  activeSavedSearch?: string;
  loading?: boolean;
  onSaveSearch?: (name: string, filters: TransactionSearchFilters) => void;
  onDeleteSearch?: (searchId: string) => void;
}

const statusOptions = [
  { value: '', label: 'All Statuses' },
  { value: 'succeeded', label: 'Succeeded' },
  { value: 'processing', label: 'Processing' },
  { value: 'requires_payment_method', label: 'Requires Payment Method' },
  { value: 'requires_confirmation', label: 'Requires Confirmation' },
  { value: 'requires_action', label: 'Requires Action' },
  { value: 'canceled', label: 'Canceled' },
];

const paymentMethodOptions = [
  { value: '', label: 'All Payment Methods' },
  { value: 'card', label: 'Card' },
  { value: 'bank_transfer', label: 'Bank Transfer' },
  { value: 'digital_wallet', label: 'Digital Wallet' },
];

const riskLevelOptions = [
  { value: '', label: 'All Risk Levels' },
  { value: 'low', label: 'Low Risk' },
  { value: 'medium', label: 'Medium Risk' },
  { value: 'high', label: 'High Risk' },
];

export default function TransactionSearchInterface({
  filters,
  onFiltersChange,
  savedSearches,
  activeSavedSearch,
  loading,
  onSaveSearch,
  onDeleteSearch,
}: TransactionSearchInterfaceProps) {
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const [saveSearchModal, setSaveSearchModal] = useState(false);
  const [saveSearchName, setSaveSearchName] = useState('');

  // Count active filters
  const activeFilterCount = Object.values(filters).filter(
    value => value !== undefined && value !== '' && value !== null
  ).length;

  // Handle filter changes
  const updateFilter = useCallback(
    (key: keyof TransactionSearchFilters, value: any) => {
      const updatedFilters = { ...filters, [key]: value || undefined };

      // Remove empty values
      Object.keys(updatedFilters).forEach(k => {
        if (
          updatedFilters[k as keyof TransactionSearchFilters] === '' ||
          updatedFilters[k as keyof TransactionSearchFilters] === null
        ) {
          delete updatedFilters[k as keyof TransactionSearchFilters];
        }
      });

      onFiltersChange(updatedFilters);
    },
    [filters, onFiltersChange]
  );

  // Clear all filters
  const clearAllFilters = useCallback(() => {
    onFiltersChange({});
  }, [onFiltersChange]);

  // Apply saved search
  const applySavedSearch = useCallback(
    (search: SavedSearch) => {
      onFiltersChange(search.filters);
    },
    [onFiltersChange]
  );

  // Save current search
  const handleSaveSearch = useCallback(() => {
    if (saveSearchName.trim() && onSaveSearch) {
      onSaveSearch(saveSearchName.trim(), filters);
      setSaveSearchName('');
      setSaveSearchModal(false);
    }
  }, [saveSearchName, filters, onSaveSearch]);

  // Format date for input
  const formatDateForInput = (dateString?: string) => {
    if (!dateString) return '';
    return new Date(dateString).toISOString().split('T')[0];
  };

  return (
    <Card className="p-6">
      <VStack space="lg">
        {/* Main Search Bar */}
        <VStack space="md">
          <HStack space="md" className="items-center">
            <Box className="flex-1 relative">
              <Input
                placeholder="Search by customer email, transaction ID, or payment intent..."
                value={filters.search || ''}
                onChangeText={text => updateFilter('search', text)}
                className="pl-10"
              />
              <Icon
                as={Search}
                size="sm"
                className="absolute left-3 top-1/2 transform -translate-y-1/2 text-typography-500"
              />
            </Box>

            <Button
              variant={showAdvancedFilters ? 'solid' : 'outline'}
              size="md"
              onPress={() => setShowAdvancedFilters(!showAdvancedFilters)}
            >
              <Icon as={Filter} size="sm" />
              <Text size="sm" className="ml-2">
                Filters {activeFilterCount > 0 && `(${activeFilterCount})`}
              </Text>
            </Button>

            {activeFilterCount > 0 && (
              <Button variant="ghost" size="md" onPress={clearAllFilters}>
                <Icon as={X} size="sm" />
                <Text size="sm" className="ml-1">
                  Clear
                </Text>
              </Button>
            )}
          </HStack>

          {/* Quick Filter Badges */}
          {activeFilterCount > 0 && (
            <HStack space="xs" className="flex-wrap">
              {filters.status && (
                <Badge variant="info" className="flex-row items-center">
                  <Text size="xs">
                    Status: {statusOptions.find(o => o.value === filters.status)?.label}
                  </Text>
                  <Pressable onPress={() => updateFilter('status', '')} className="ml-1">
                    <Icon as={X} size="xs" />
                  </Pressable>
                </Badge>
              )}

              {filters.payment_method_type && (
                <Badge variant="info" className="flex-row items-center">
                  <Text size="xs">
                    Method:{' '}
                    {paymentMethodOptions.find(o => o.value === filters.payment_method_type)?.label}
                  </Text>
                  <Pressable
                    onPress={() => updateFilter('payment_method_type', '')}
                    className="ml-1"
                  >
                    <Icon as={X} size="xs" />
                  </Pressable>
                </Badge>
              )}

              {filters.risk_level && (
                <Badge variant="info" className="flex-row items-center">
                  <Text size="xs">
                    Risk: {riskLevelOptions.find(o => o.value === filters.risk_level)?.label}
                  </Text>
                  <Pressable onPress={() => updateFilter('risk_level', '')} className="ml-1">
                    <Icon as={X} size="xs" />
                  </Pressable>
                </Badge>
              )}

              {(filters.amount_min || filters.amount_max) && (
                <Badge variant="info" className="flex-row items-center">
                  <Text size="xs">
                    Amount: {filters.amount_min && `€${filters.amount_min}`}
                    {filters.amount_min && filters.amount_max && ' - '}
                    {filters.amount_max && `€${filters.amount_max}`}
                  </Text>
                  <Pressable
                    onPress={() => {
                      updateFilter('amount_min', '');
                      updateFilter('amount_max', '');
                    }}
                    className="ml-1"
                  >
                    <Icon as={X} size="xs" />
                  </Pressable>
                </Badge>
              )}

              {(filters.date_from || filters.date_to) && (
                <Badge variant="info" className="flex-row items-center">
                  <Text size="xs">
                    Date: {filters.date_from && new Date(filters.date_from).toLocaleDateString()}
                    {filters.date_from && filters.date_to && ' - '}
                    {filters.date_to && new Date(filters.date_to).toLocaleDateString()}
                  </Text>
                  <Pressable
                    onPress={() => {
                      updateFilter('date_from', '');
                      updateFilter('date_to', '');
                    }}
                    className="ml-1"
                  >
                    <Icon as={X} size="xs" />
                  </Pressable>
                </Badge>
              )}
            </HStack>
          )}
        </VStack>

        {/* Advanced Filters */}
        {showAdvancedFilters && (
          <Box className="p-4 bg-background-50 rounded-lg border border-border-200">
            <VStack space="md">
              <Text size="md" className="font-semibold text-typography-900">
                Advanced Filters
              </Text>

              {/* Row 1: Status and Payment Method */}
              <HStack space="md">
                <FormControl className="flex-1">
                  <FormControlLabel>
                    <Text size="sm" className="text-typography-700">
                      Status
                    </Text>
                  </FormControlLabel>
                  <Select
                    selectedValue={filters.status || ''}
                    onValueChange={value => updateFilter('status', value)}
                  >
                    <SelectTrigger>
                      <Text>
                        {statusOptions.find(o => o.value === filters.status)?.label ||
                          'All Statuses'}
                      </Text>
                    </SelectTrigger>
                    <SelectContent>
                      {statusOptions.map(option => (
                        <SelectItem key={option.value} value={option.value}>
                          <Text>{option.label}</Text>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </FormControl>

                <FormControl className="flex-1">
                  <FormControlLabel>
                    <Text size="sm" className="text-typography-700">
                      Payment Method
                    </Text>
                  </FormControlLabel>
                  <Select
                    selectedValue={filters.payment_method_type || ''}
                    onValueChange={value => updateFilter('payment_method_type', value)}
                  >
                    <SelectTrigger>
                      <Text>
                        {paymentMethodOptions.find(o => o.value === filters.payment_method_type)
                          ?.label || 'All Methods'}
                      </Text>
                    </SelectTrigger>
                    <SelectContent>
                      {paymentMethodOptions.map(option => (
                        <SelectItem key={option.value} value={option.value}>
                          <Text>{option.label}</Text>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </FormControl>
              </HStack>

              {/* Row 2: Amount Range */}
              <HStack space="md">
                <FormControl className="flex-1">
                  <FormControlLabel>
                    <Text size="sm" className="text-typography-700">
                      Minimum Amount (€)
                    </Text>
                  </FormControlLabel>
                  <Input
                    placeholder="0.00"
                    value={filters.amount_min || ''}
                    onChangeText={text => updateFilter('amount_min', text)}
                    keyboardType="decimal-pad"
                  />
                </FormControl>

                <FormControl className="flex-1">
                  <FormControlLabel>
                    <Text size="sm" className="text-typography-700">
                      Maximum Amount (€)
                    </Text>
                  </FormControlLabel>
                  <Input
                    placeholder="1000.00"
                    value={filters.amount_max || ''}
                    onChangeText={text => updateFilter('amount_max', text)}
                    keyboardType="decimal-pad"
                  />
                </FormControl>
              </HStack>

              {/* Row 3: Date Range */}
              <HStack space="md">
                <FormControl className="flex-1">
                  <FormControlLabel>
                    <Text size="sm" className="text-typography-700">
                      From Date
                    </Text>
                  </FormControlLabel>
                  <Input
                    placeholder="YYYY-MM-DD"
                    value={formatDateForInput(filters.date_from)}
                    onChangeText={text => updateFilter('date_from', text)}
                  />
                </FormControl>

                <FormControl className="flex-1">
                  <FormControlLabel>
                    <Text size="sm" className="text-typography-700">
                      To Date
                    </Text>
                  </FormControlLabel>
                  <Input
                    placeholder="YYYY-MM-DD"
                    value={formatDateForInput(filters.date_to)}
                    onChangeText={text => updateFilter('date_to', text)}
                  />
                </FormControl>
              </HStack>

              {/* Row 4: Risk Level and Special Filters */}
              <HStack space="md">
                <FormControl className="flex-1">
                  <FormControlLabel>
                    <Text size="sm" className="text-typography-700">
                      Risk Level
                    </Text>
                  </FormControlLabel>
                  <Select
                    selectedValue={filters.risk_level || ''}
                    onValueChange={value => updateFilter('risk_level', value)}
                  >
                    <SelectTrigger>
                      <Text>
                        {riskLevelOptions.find(o => o.value === filters.risk_level)?.label ||
                          'All Risk Levels'}
                      </Text>
                    </SelectTrigger>
                    <SelectContent>
                      {riskLevelOptions.map(option => (
                        <SelectItem key={option.value} value={option.value}>
                          <Text>{option.label}</Text>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </FormControl>

                <FormControl className="flex-1">
                  <FormControlLabel>
                    <Text size="sm" className="text-typography-700">
                      Customer Email
                    </Text>
                  </FormControlLabel>
                  <Input
                    placeholder="customer@example.com"
                    value={filters.customer_email || ''}
                    onChangeText={text => updateFilter('customer_email', text)}
                    keyboardType="email-address"
                    autoCapitalize="none"
                  />
                </FormControl>
              </HStack>
            </VStack>
          </Box>
        )}

        {/* Saved Searches */}
        {savedSearches.length > 0 && (
          <VStack space="sm">
            <HStack className="justify-between items-center">
              <Text size="sm" className="font-medium text-typography-700">
                Saved Searches
              </Text>
              {onSaveSearch && activeFilterCount > 0 && (
                <Button variant="ghost" size="sm" onPress={() => setSaveSearchModal(true)}>
                  <Icon as={Save} size="xs" />
                  <Text size="sm" className="ml-1">
                    Save Current
                  </Text>
                </Button>
              )}
            </HStack>

            <HStack space="xs" className="flex-wrap">
              {savedSearches.map(search => (
                <Pressable
                  key={search.id}
                  onPress={() => applySavedSearch(search)}
                  className={`
                    px-3 py-2 rounded-lg border flex-row items-center
                    ${
                      activeSavedSearch === search.id
                        ? 'bg-primary-50 border-primary-200'
                        : 'bg-background-50 border-border-200 hover:bg-background-100'
                    }
                  `}
                >
                  <Icon as={Bookmark} size="xs" className="mr-2 text-primary-600" />
                  <Text
                    size="sm"
                    className={
                      activeSavedSearch === search.id ? 'text-primary-700' : 'text-typography-700'
                    }
                  >
                    {search.name}
                  </Text>
                  {onDeleteSearch && (
                    <Pressable
                      onPress={() => onDeleteSearch(search.id)}
                      className="ml-2 p-1"
                      hitSlop={{ top: 5, bottom: 5, left: 5, right: 5 }}
                    >
                      <Icon as={X} size="xs" className="text-typography-400" />
                    </Pressable>
                  )}
                </Pressable>
              ))}
            </HStack>
          </VStack>
        )}
      </VStack>

      {/* Save Search Modal */}
      <Modal isOpen={saveSearchModal} onClose={() => setSaveSearchModal(false)}>
        <ModalBackdrop />
        <ModalContent>
          <ModalHeader>
            <Text size="lg" className="font-semibold">
              Save Search
            </Text>
          </ModalHeader>
          <ModalBody>
            <VStack space="md">
              <Text size="sm" className="text-typography-600">
                Save your current search filters for quick access later.
              </Text>
              <FormControl>
                <FormControlLabel>
                  <Text size="sm" className="text-typography-700">
                    Search Name
                  </Text>
                </FormControlLabel>
                <Input
                  placeholder="Enter a name for this search..."
                  value={saveSearchName}
                  onChangeText={setSaveSearchName}
                  autoFocus
                />
              </FormControl>
            </VStack>
          </ModalBody>
          <ModalFooter>
            <HStack space="sm">
              <Button variant="outline" onPress={() => setSaveSearchModal(false)}>
                <Text>Cancel</Text>
              </Button>
              <Button onPress={handleSaveSearch} disabled={!saveSearchName.trim()}>
                <Text>Save Search</Text>
              </Button>
            </HStack>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Card>
  );
}
