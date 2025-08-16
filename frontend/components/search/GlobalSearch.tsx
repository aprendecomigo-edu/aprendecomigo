import { cn } from '@gluestack-ui/nativewind-utils/cn';
import { router } from 'expo-router';
import type { Href } from 'expo-router';
import {
  SearchIcon,
  XIcon,
  ClockIcon,
  TrendingUpIcon,
  UserIcon,
  UsersIcon,
  BookOpenIcon,
  SettingsIcon,
  LoaderIcon,
} from 'lucide-react-native';
import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { Platform, Keyboard } from 'react-native';

import { navigationApi, type SearchResult, type GlobalSearchResponse } from '@/api/navigationApi';
import { Avatar, AvatarFallbackText } from '@/components/ui/avatar';
import { Box } from '@/components/ui/box';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Input, InputField } from '@/components/ui/input';
import { Modal, ModalBackdrop, ModalContent } from '@/components/ui/modal';
import { Pressable } from '@/components/ui/pressable';
import { ScrollView } from '@/components/ui/scroll-view';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import type { SearchCategory, SearchSuggestion, EnhancedSearchResult } from '@/types/navigation';

interface GlobalSearchProps {
  placeholder?: string;
  className?: string;
  onResultSelect?: (result: SearchResult) => void;
  maxResults?: number;
  categories?: SearchCategory[];
}

// Search categories configuration
const DEFAULT_CATEGORIES: SearchCategory[] = [
  {
    id: 'teacher',
    label: 'Teachers',
    type: 'teacher',
    icon: UserIcon,
    searchTypes: ['teacher'],
  },
  {
    id: 'student',
    label: 'Students',
    type: 'student',
    icon: UsersIcon,
    searchTypes: ['student'],
  },
  {
    id: 'class',
    label: 'Classes',
    type: 'class',
    icon: BookOpenIcon,
    searchTypes: ['class'],
  },
];

// Debounce hook
const useDebounce = (value: string, delay: number) => {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
};

/**
 * GlobalSearch component - provides real-time search with debouncing and categorized results
 */
export const GlobalSearch: React.FC<GlobalSearchProps> = ({
  placeholder = 'Search teachers, students, classes...',
  className = '',
  onResultSelect,
  maxResults = 10,
  categories = DEFAULT_CATEGORIES,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [recentSearches, setRecentSearches] = useState<SearchSuggestion[]>([]);
  const [error, setError] = useState<string | null>(null);

  const inputRef = useRef<any>(null);
  const debouncedQuery = useDebounce(query, 300);

  // Enhanced results with category information
  const enhancedResults = useMemo(() => {
    return results.map(result => {
      const category = categories.find(cat => cat.type === result.type);
      return {
        ...result,
        category,
      } as EnhancedSearchResult;
    });
  }, [results, categories]);

  // Perform search
  const performSearch = useCallback(
    async (searchQuery: string) => {
      if (!searchQuery.trim()) {
        setResults([]);
        setIsLoading(false);
        return;
      }

      setIsLoading(true);
      setError(null);

      try {
        const response: GlobalSearchResponse = await navigationApi.globalSearch(
          searchQuery,
          categories.flatMap(cat => cat.searchTypes),
          maxResults,
        );
        setResults(response.results);
      } catch (err) {
        console.error('Search error:', err);
        setError('Search failed. Please try again.');
        setResults([]);
      } finally {
        setIsLoading(false);
      }
    },
    [categories, maxResults],
  );

  // Effect for debounced search
  useEffect(() => {
    if (isOpen && debouncedQuery) {
      performSearch(debouncedQuery);
    }
  }, [debouncedQuery, isOpen, performSearch]);

  // Load recent searches when modal opens
  useEffect(() => {
    if (isOpen) {
      // In a real app, load from API or AsyncStorage
      // For now, use mock data
      setRecentSearches([
        { id: '1', query: 'Math teacher', type: 'recent', timestamp: new Date() },
        { id: '2', query: 'Physics class', type: 'recent', timestamp: new Date() },
        { id: '3', query: 'Student progress', type: 'popular', timestamp: new Date() },
      ]);
    }
  }, [isOpen]);

  // Handle result selection
  const handleResultSelect = useCallback(
    (result: SearchResult) => {
      // Save to recent searches
      navigationApi.saveRecentSearch(query).catch(console.error);

      // Close modal
      setIsOpen(false);
      setQuery('');
      setSelectedIndex(-1);

      // Navigate to result
      if (result.route) {
        router.push(result.route as Href<string>);
      }

      // Call custom handler
      if (onResultSelect) {
        onResultSelect(result);
      }
    },
    [query, onResultSelect],
  );

  // Handle recent search selection
  const handleRecentSearchSelect = useCallback(
    (suggestion: SearchSuggestion) => {
      setQuery(suggestion.query);
      performSearch(suggestion.query);
    },
    [performSearch],
  );

  // Keyboard navigation
  const handleKeyPress = useCallback(
    (key: string) => {
      if (!isOpen) return;

      switch (key) {
        case 'ArrowDown':
          setSelectedIndex(prev => (prev < enhancedResults.length - 1 ? prev + 1 : prev));
          break;
        case 'ArrowUp':
          setSelectedIndex(prev => (prev > 0 ? prev - 1 : -1));
          break;
        case 'Enter':
          if (selectedIndex >= 0 && enhancedResults[selectedIndex]) {
            handleResultSelect(enhancedResults[selectedIndex]);
          }
          break;
        case 'Escape':
          setIsOpen(false);
          break;
      }
    },
    [isOpen, enhancedResults, selectedIndex, handleResultSelect],
  );

  // Clear search
  const clearSearch = useCallback(() => {
    setQuery('');
    setResults([]);
    setSelectedIndex(-1);
    setError(null);
  }, []);

  return (
    <>
      {/* Search Input */}
      <Pressable
        onPress={() => setIsOpen(true)}
        className={cn(
          'flex-row items-center bg-background-50 border border-border-200 rounded-lg px-3 py-2',
          'hover:border-border-300 focus:border-primary-300',
          className,
        )}
      >
        <Icon as={SearchIcon} size="sm" className="text-typography-400 mr-2" />
        <Text className="flex-1 text-typography-500" numberOfLines={1}>
          {query || placeholder}
        </Text>
        {Platform.OS === 'web' && <Text className="text-xs text-typography-400 ml-2">⌘K</Text>}
      </Pressable>

      {/* Search Modal */}
      <Modal isOpen={isOpen} onClose={() => setIsOpen(false)}>
        <ModalBackdrop />
        <ModalContent
          className={cn(
            'mx-4 my-8 max-w-2xl w-full',
            Platform.OS === 'web' ? 'max-h-[80vh]' : 'max-h-[70vh]',
          )}
        >
          <VStack space="sm" className="p-4">
            {/* Search Input */}
            <HStack space="sm" className="items-center">
              <Icon as={SearchIcon} size="sm" className="text-typography-400" />
              <Input variant="outline" className="flex-1">
                <InputField
                  ref={inputRef}
                  placeholder={placeholder}
                  value={query}
                  onChangeText={setQuery}
                  autoFocus
                  returnKeyType="search"
                  onSubmitEditing={() => {
                    if (enhancedResults.length > 0) {
                      handleResultSelect(enhancedResults[0]);
                    }
                  }}
                />
              </Input>
              {query.length > 0 && (
                <Pressable onPress={clearSearch} className="p-1">
                  <Icon as={XIcon} size="sm" className="text-typography-400" />
                </Pressable>
              )}
            </HStack>

            {/* Content Area */}
            <ScrollView className="max-h-96" showsVerticalScrollIndicator={false}>
              {error && (
                <Box className="p-4 bg-error-50 rounded-lg mb-4">
                  <Text className="text-error-700">{error}</Text>
                </Box>
              )}

              {isLoading && (
                <HStack space="sm" className="p-4 items-center justify-center">
                  <Icon as={LoaderIcon} size="sm" className="text-primary-500 animate-spin" />
                  <Text className="text-typography-500">Searching...</Text>
                </HStack>
              )}

              {!query && recentSearches.length > 0 && (
                <VStack space="xs">
                  <Text className="text-sm font-semibold text-typography-700 px-2">
                    Recent Searches
                  </Text>
                  {recentSearches.map(suggestion => (
                    <SearchSuggestionItem
                      key={suggestion.id}
                      suggestion={suggestion}
                      onSelect={handleRecentSearchSelect}
                    />
                  ))}
                </VStack>
              )}

              {query && !isLoading && enhancedResults.length === 0 && (
                <Box className="p-8 text-center">
                  <Icon as={SearchIcon} size="xl" className="text-typography-300 mb-2" />
                  <Text className="text-typography-500">No results found for "{query}"</Text>
                  <Text className="text-sm text-typography-400 mt-1">
                    Try a different search term
                  </Text>
                </Box>
              )}

              {enhancedResults.length > 0 && (
                <VStack space="xs">
                  {enhancedResults.map((result, index) => (
                    <SearchResultItem
                      key={result.id}
                      result={result}
                      isSelected={index === selectedIndex}
                      onSelect={handleResultSelect}
                    />
                  ))}
                </VStack>
              )}
            </ScrollView>

            {/* Footer */}
            {Platform.OS === 'web' && (
              <HStack
                space="md"
                className="justify-between items-center pt-2 border-t border-border-200"
              >
                <HStack space="sm" className="items-center">
                  <Text className="text-xs text-typography-400">↑↓ Navigate</Text>
                  <Text className="text-xs text-typography-400">↵ Select</Text>
                  <Text className="text-xs text-typography-400">ESC Close</Text>
                </HStack>
                <Text className="text-xs text-typography-400">
                  {enhancedResults.length} results
                </Text>
              </HStack>
            )}
          </VStack>
        </ModalContent>
      </Modal>
    </>
  );
};

// Search Result Item Component
interface SearchResultItemProps {
  result: EnhancedSearchResult;
  isSelected: boolean;
  onSelect: (result: SearchResult) => void;
}

const SearchResultItem: React.FC<SearchResultItemProps> = ({ result, isSelected, onSelect }) => {
  return (
    <Pressable
      onPress={() => onSelect(result)}
      className={cn(
        'p-3 rounded-lg flex-row items-center space-x-3',
        isSelected ? 'bg-primary-50 border border-primary-200' : 'hover:bg-background-50',
      )}
    >
      {/* Avatar or Icon */}
      <Box className="w-10 h-10 items-center justify-center">
        {result.avatar ? (
          <Avatar size="sm">
            <AvatarFallbackText>{result.title.charAt(0)}</AvatarFallbackText>
          </Avatar>
        ) : (
          <Box className="w-8 h-8 bg-primary-100 rounded-full items-center justify-center">
            <Icon as={result.category?.icon || SearchIcon} size="sm" className="text-primary-600" />
          </Box>
        )}
      </Box>

      {/* Content */}
      <VStack className="flex-1" space="xs">
        <Text className="font-medium text-typography-900" numberOfLines={1}>
          {result.title}
        </Text>
        {result.subtitle && (
          <Text className="text-sm text-typography-500" numberOfLines={1}>
            {result.subtitle}
          </Text>
        )}
      </VStack>

      {/* Category Badge */}
      {result.category && (
        <Box className="px-2 py-1 bg-background-100 rounded">
          <Text className="text-xs text-typography-600">{result.category.label}</Text>
        </Box>
      )}
    </Pressable>
  );
};

// Search Suggestion Item Component
interface SearchSuggestionItemProps {
  suggestion: SearchSuggestion;
  onSelect: (suggestion: SearchSuggestion) => void;
}

const SearchSuggestionItem: React.FC<SearchSuggestionItemProps> = ({ suggestion, onSelect }) => {
  const IconComponent = suggestion.type === 'recent' ? ClockIcon : TrendingUpIcon;

  return (
    <Pressable
      onPress={() => onSelect(suggestion)}
      className="p-3 rounded-lg flex-row items-center space-x-3 hover:bg-background-50"
    >
      <Icon as={IconComponent} size="sm" className="text-typography-400" />
      <Text className="flex-1 text-typography-700">{suggestion.query}</Text>
    </Pressable>
  );
};

export default GlobalSearch;
