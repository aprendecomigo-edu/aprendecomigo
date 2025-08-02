import { Globe, School, Users, Check, ChevronRight, Info } from 'lucide-react-native';
import React, { useState, useEffect } from 'react';

import { getEducationalSystems } from '@/api/tutorApi';
import { EducationalSystem } from '@/api/userApi';
import {
  AlertDialog,
  AlertDialogBackdrop,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogBody,
  AlertDialogFooter,
} from '@/components/ui/alert-dialog';
import { Badge, BadgeText } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Pressable } from '@/components/ui/pressable';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

// Pre-configured educational systems with enhanced metadata
const FEATURED_SYSTEMS = {
  portugal: {
    id: 'portugal',
    name: 'Portuguese Educational System',
    country: 'Portugal',
    flag: '🇵🇹',
    description: 'Complete curriculum from Ensino Básico to Ensino Secundário',
    subjects_count: 45,
    grade_levels: ['1º Ciclo', '2º Ciclo', '3º Ciclo', 'Secundário'],
    popular_subjects: ['Matemática', 'Português', 'Inglês', 'Física', 'Química'],
    market_info: {
      demand: 'high' as const,
      tutors: 1250,
      avg_rate: 15,
      currency: '€',
    },
    benefits: [
      'Structured national curriculum',
      'High student demand',
      'Competitive rates',
      'Established assessment methods',
    ],
  },
  brazil: {
    id: 'brazil',
    name: 'Brazilian Educational System',
    country: 'Brazil',
    flag: '🇧🇷',
    description: 'Ensino Fundamental and Ensino Médio curriculum structure',
    subjects_count: 38,
    grade_levels: ['Fund. I', 'Fund. II', 'Ensino Médio'],
    popular_subjects: ['Matemática', 'Português', 'História', 'Geografia', 'Ciências'],
    market_info: {
      demand: 'high' as const,
      tutors: 890,
      avg_rate: 25,
      currency: 'R$',
    },
    benefits: [
      'Large student population',
      'Growing online education market',
      'Diverse subject offerings',
      'Strong demand for quality tutoring',
    ],
  },
  custom: {
    id: 'custom',
    name: 'Custom Subjects',
    country: 'International',
    flag: '🌍',
    description: 'Create your own curriculum for specialized or unique subjects',
    subjects_count: 0,
    grade_levels: ['Customizable'],
    popular_subjects: ['Music', 'Art', 'Programming', 'Languages', 'Skills'],
    market_info: {
      demand: 'medium' as const,
      tutors: 340,
      avg_rate: 20,
      currency: '€',
    },
    benefits: [
      'Complete flexibility',
      'Unique value proposition',
      'Higher pricing potential',
      'Less competition',
    ],
  },
} as const;

interface EducationalSystemSelectorProps {
  selectedSystemId?: number;
  onSystemSelect: (system: EducationalSystem | null) => void;
  onContinue?: () => void;
  isLoading?: boolean;
  title?: string;
  subtitle?: string;
  showContinueButton?: boolean;
}

const SystemCard: React.FC<{
  system: (typeof FEATURED_SYSTEMS)[keyof typeof FEATURED_SYSTEMS];
  actualSystem?: EducationalSystem;
  isSelected: boolean;
  onSelect: () => void;
  isLoading?: boolean;
}> = ({ system, actualSystem, isSelected, onSelect, isLoading }) => {
  const [showDetails, setShowDetails] = useState(false);

  const getDemandColor = (demand: string) => {
    switch (demand) {
      case 'high':
        return 'bg-green-100 text-green-700';
      case 'medium':
        return 'bg-yellow-100 text-yellow-700';
      case 'low':
        return 'bg-red-100 text-red-700';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  };

  return (
    <>
      <Pressable
        onPress={onSelect}
        disabled={isLoading}
        className={`w-full ${isLoading ? 'opacity-50' : ''}`}
        accessibilityRole="button"
        accessibilityLabel={`Select ${system.name}`}
        accessibilityState={{ selected: isSelected }}
      >
        <Card
          className={`
            border-2 transition-all duration-200 mb-4
            ${
              isSelected
                ? 'border-blue-500 bg-blue-50 shadow-lg'
                : 'border-gray-200 bg-white hover:border-blue-300 hover:bg-blue-50'
            }
          `}
        >
          <CardHeader className="pb-4">
            <HStack className="items-start justify-between">
              <HStack space="md" className="items-start flex-1">
                <Box className="w-12 h-12 rounded-full bg-gray-100 items-center justify-center">
                  <Text className="text-2xl">{system.flag}</Text>
                </Box>

                <VStack className="flex-1" space="xs">
                  <VStack space="xs">
                    <Heading size="md" className="text-gray-900">
                      {system.name}
                    </Heading>
                    <Text className="text-gray-600 text-sm">{system.description}</Text>
                  </VStack>

                  <HStack space="xs" className="flex-wrap">
                    <Badge className={getDemandColor(system.market_info.demand)}>
                      <BadgeText className="text-xs capitalize">
                        {system.market_info.demand} Demand
                      </BadgeText>
                    </Badge>

                    <Badge className="bg-blue-100 text-blue-700">
                      <BadgeText className="text-xs">{system.subjects_count} Subjects</BadgeText>
                    </Badge>

                    <Badge className="bg-purple-100 text-purple-700">
                      <BadgeText className="text-xs">
                        ~{system.market_info.avg_rate}
                        {system.market_info.currency}/h
                      </BadgeText>
                    </Badge>
                  </HStack>

                  <Text className="text-gray-500 text-xs">
                    {system.market_info.tutors} active tutors • {system.grade_levels.join(', ')}
                  </Text>
                </VStack>
              </HStack>

              <VStack space="sm" className="items-end">
                {isSelected && (
                  <Box className="w-6 h-6 rounded-full bg-blue-600 items-center justify-center">
                    <Icon as={Check} className="text-white" size="sm" />
                  </Box>
                )}

                <Pressable
                  onPress={() => setShowDetails(true)}
                  className="p-1"
                  accessibilityLabel="View details"
                >
                  <Icon as={Info} className="text-gray-400" size="sm" />
                </Pressable>
              </VStack>
            </HStack>
          </CardHeader>

          <CardContent className="pt-0">
            <VStack space="sm">
              <VStack space="xs">
                <Text className="text-gray-700 text-xs font-medium">Popular Subjects:</Text>
                <Text className="text-gray-600 text-xs">{system.popular_subjects.join(' • ')}</Text>
              </VStack>
            </VStack>
          </CardContent>
        </Card>
      </Pressable>

      {/* Details Modal */}
      <AlertDialog isOpen={showDetails} onClose={() => setShowDetails(false)}>
        <AlertDialogBackdrop />
        <AlertDialogContent className="max-w-lg">
          <AlertDialogHeader className="border-b border-gray-200 pb-4">
            <HStack space="md" className="items-center">
              <Text className="text-2xl">{system.flag}</Text>
              <VStack>
                <Heading size="lg" className="text-gray-900">
                  {system.name}
                </Heading>
                <Text className="text-gray-600 text-sm">{system.country}</Text>
              </VStack>
            </HStack>
          </AlertDialogHeader>

          <AlertDialogBody className="py-6">
            <VStack space="lg">
              <VStack space="sm">
                <Heading size="sm" className="text-gray-900">
                  Market Overview
                </Heading>
                <HStack space="lg" className="justify-between">
                  <VStack space="xs" className="items-center">
                    <Icon as={Users} className="text-blue-600" size="lg" />
                    <Text className="text-lg font-semibold text-gray-900">
                      {system.market_info.tutors}
                    </Text>
                    <Text className="text-gray-600 text-xs text-center">Active Tutors</Text>
                  </VStack>

                  <VStack space="xs" className="items-center">
                    <Icon as={School} className="text-green-600" size="lg" />
                    <Text className="text-lg font-semibold text-gray-900">
                      {system.subjects_count}
                    </Text>
                    <Text className="text-gray-600 text-xs text-center">Subjects</Text>
                  </VStack>

                  <VStack space="xs" className="items-center">
                    <Icon as={Globe} className="text-purple-600" size="lg" />
                    <Text className="text-lg font-semibold text-gray-900">
                      {system.market_info.avg_rate}
                      {system.market_info.currency}
                    </Text>
                    <Text className="text-gray-600 text-xs text-center">Avg. Rate/Hour</Text>
                  </VStack>
                </HStack>
              </VStack>

              <VStack space="sm">
                <Heading size="sm" className="text-gray-900">
                  Key Benefits
                </Heading>
                <VStack space="xs">
                  {system.benefits.map((benefit, index) => (
                    <HStack key={index} space="xs" className="items-start">
                      <Text className="text-green-600 text-sm">✓</Text>
                      <Text className="text-gray-700 text-sm flex-1">{benefit}</Text>
                    </HStack>
                  ))}
                </VStack>
              </VStack>

              <VStack space="sm">
                <Heading size="sm" className="text-gray-900">
                  Grade Levels
                </Heading>
                <HStack space="xs" className="flex-wrap">
                  {system.grade_levels.map((level, index) => (
                    <Badge key={index} className="bg-gray-100">
                      <BadgeText className="text-gray-700 text-xs">{level}</BadgeText>
                    </Badge>
                  ))}
                </HStack>
              </VStack>
            </VStack>
          </AlertDialogBody>

          <AlertDialogFooter className="border-t border-gray-200 pt-4">
            <Button onPress={() => setShowDetails(false)} className="w-full bg-blue-600">
              <ButtonText className="text-white">Close</ButtonText>
            </Button>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
};

export const EducationalSystemSelector: React.FC<EducationalSystemSelectorProps> = ({
  selectedSystemId,
  onSystemSelect,
  onContinue,
  isLoading = false,
  title = 'Choose Your Educational System',
  subtitle = "Select the curriculum and standards you'll be teaching",
  showContinueButton = true,
}) => {
  const [systems, setSystems] = useState<EducationalSystem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadSystems = async () => {
      try {
        setLoading(true);
        const systemsData = await getEducationalSystems();
        setSystems(systemsData);
      } catch (err) {
        console.error('Error loading educational systems:', err);
        setError('Failed to load educational systems. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    loadSystems();
  }, []);

  const handleSystemSelect = (systemKey: string) => {
    if (isLoading) return;

    // Find the actual system from backend data
    let selectedSystem: EducationalSystem | null = null;

    if (systemKey === 'portugal') {
      selectedSystem =
        systems.find(
          s => s.country?.toLowerCase() === 'portugal' || s.name.toLowerCase().includes('portug')
        ) || null;
    } else if (systemKey === 'brazil') {
      selectedSystem =
        systems.find(
          s => s.country?.toLowerCase() === 'brazil' || s.name.toLowerCase().includes('brazil')
        ) || null;
    } else if (systemKey === 'custom') {
      selectedSystem =
        systems.find(
          s => s.name.toLowerCase().includes('custom') || s.name.toLowerCase().includes('other')
        ) || null;
    }

    onSystemSelect(selectedSystem);
  };

  const selectedSystem = systems.find(s => s.id === selectedSystemId);
  const canContinue = selectedSystemId !== undefined && selectedSystemId !== null;

  if (loading) {
    return (
      <VStack className="flex-1 items-center justify-center p-8" space="md">
        <Spinner size="large" />
        <Text className="text-gray-600">Loading educational systems...</Text>
      </VStack>
    );
  }

  if (error) {
    return (
      <VStack className="flex-1 items-center justify-center p-8" space="md">
        <Text className="text-red-600 text-center">{error}</Text>
        <Button onPress={() => window.location.reload()} variant="outline">
          <ButtonText>Try Again</ButtonText>
        </Button>
      </VStack>
    );
  }

  return (
    <VStack className="flex-1 bg-gray-50" space="md">
      {/* Header */}
      <Box className="bg-white px-6 py-8 border-b border-gray-200">
        <VStack className="items-center text-center" space="md">
          <Box className="w-16 h-16 rounded-full bg-blue-100 items-center justify-center">
            <Icon as={Globe} className="text-blue-600" size="xl" />
          </Box>

          <VStack space="sm">
            <Heading size="xl" className="text-gray-900 text-center">
              {title}
            </Heading>
            <Text className="text-gray-600 text-center max-w-md">{subtitle}</Text>
          </VStack>

          {selectedSystem && (
            <Badge className="bg-green-100">
              <BadgeText className="text-green-700">Selected: {selectedSystem.name}</BadgeText>
            </Badge>
          )}
        </VStack>
      </Box>

      {/* System Options */}
      <Box className="flex-1 px-6">
        <VStack space="md">
          {Object.entries(FEATURED_SYSTEMS).map(([key, system]) => {
            const actualSystem = systems.find(s => {
              if (key === 'portugal')
                return (
                  s.country?.toLowerCase() === 'portugal' || s.name.toLowerCase().includes('portug')
                );
              if (key === 'brazil')
                return (
                  s.country?.toLowerCase() === 'brazil' || s.name.toLowerCase().includes('brazil')
                );
              if (key === 'custom')
                return (
                  s.name.toLowerCase().includes('custom') || s.name.toLowerCase().includes('other')
                );
              return false;
            });

            return (
              <SystemCard
                key={key}
                system={system}
                actualSystem={actualSystem}
                isSelected={selectedSystemId === actualSystem?.id}
                onSelect={() => handleSystemSelect(key)}
                isLoading={isLoading}
              />
            );
          })}
        </VStack>
      </Box>

      {/* Continue Button */}
      {showContinueButton && onContinue && (
        <Box className="bg-white px-6 py-4 border-t border-gray-200">
          <Button
            onPress={onContinue}
            disabled={!canContinue || isLoading}
            className={`w-full ${canContinue ? 'bg-blue-600 hover:bg-blue-700' : 'bg-gray-300'}`}
          >
            {isLoading ? (
              <>
                <Spinner size="small" className="text-white mr-2" />
                <ButtonText className="text-white">Loading...</ButtonText>
              </>
            ) : (
              <>
                <ButtonText className={canContinue ? 'text-white' : 'text-gray-500'}>
                  Continue to Course Selection
                </ButtonText>
                <ButtonIcon
                  as={ChevronRight}
                  className={canContinue ? 'text-white ml-1' : 'text-gray-500 ml-1'}
                />
              </>
            )}
          </Button>
        </Box>
      )}
    </VStack>
  );
};
