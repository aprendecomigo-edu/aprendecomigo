import React from 'react';
import { ScrollView, Platform } from 'react-native';
import { Box } from '@/components/ui/box';
import { HStack } from '@/components/ui/hstack';
import { VStack } from '@/components/ui/vstack';
import { Text } from '@/components/ui/text';
import { Heading } from '@/components/ui/heading';
import { 
  Avatar, 
  AvatarFallbackText, 
  AvatarImage 
} from '@/components/ui/avatar';
import { Icon } from '@/components/ui/icon';
import { Divider } from '@/components/ui/divider';
import { Button, ButtonText } from '@/components/ui/button';
import { SafeAreaView } from '@/components/ui/safe-area-view';
import { 
  CheckIcon, 
  MinusIcon, 
  InfoIcon,
  AlertCircleIcon, 
  BookOpenIcon,
  CalendarIcon,
  ClockIcon
} from 'lucide-react-native';

/**
 * AprendeComigo Design System Reference
 * 
 * This component serves as a visual reference and documentation for the design system
 * used in the AprendeComigo educational platform.
 * 
 * It includes:
 * - Color palette
 * - Typography scale
 * - Component examples (headers, cards, etc.)
 * - Layout patterns
 */
export const DesignSystemReference = () => {
  return (
    <SafeAreaView className="h-full w-full bg-white">
      <ScrollView 
        contentContainerStyle={{ 
          paddingBottom: Platform.OS === 'web' ? 40 : 100 
        }}
        className="flex-1"
      >
        <VStack className="p-4 pb-0 md:px-6 md:pt-6 w-full" space="xl">
          {/* Introduction */}
          <VStack space="md">
            <Heading className="text-2xl font-bold">AprendeComigo Design System</Heading>
            <Text className="text-gray-500">
              This is a reference implementation of the AprendeComigo design system based on the student dashboard design.
            </Text>
          </VStack>

          {/* Color Palette */}
          <VStack space="md">
            <Heading className="text-xl font-semibold">Color Palette</Heading>
            
            <VStack space="xs">
              <Heading className="text-lg font-medium">Primary Colors</Heading>
              <HStack className="flex-wrap">
                <ColorSwatch color="bg-blue-700" name="Blue 700" hex="#2563EB" />
                <ColorSwatch color="bg-blue-600" name="Blue 600" hex="#3B82F6" />
                <ColorSwatch color="bg-blue-300" name="Blue 300" hex="#93C5FD" />
                <ColorSwatch color="bg-blue-50" name="Blue 50" hex="#EFF6FF" />
              </HStack>
            </VStack>
            
            <VStack space="xs">
              <Heading className="text-lg font-medium">Secondary Colors</Heading>
              <HStack className="flex-wrap">
                <ColorSwatch color="bg-green-500" name="Green 500" hex="#22C55E" />
                <ColorSwatch color="bg-orange-500" name="Orange 500" hex="#F97316" />
                <ColorSwatch color="bg-red-500" name="Red 500" hex="#EF4444" />
                <ColorSwatch color="bg-red-50" name="Red 50" hex="#FEF2F2" />
              </HStack>
            </VStack>
            
            <VStack space="xs">
              <Heading className="text-lg font-medium">Neutral Colors</Heading>
              <HStack className="flex-wrap">
                <ColorSwatch color="bg-white" name="White" hex="#FFFFFF" borderVisible />
                <ColorSwatch color="bg-gray-200" name="Gray 200" hex="#E5E7EB" />
                <ColorSwatch color="bg-gray-500" name="Gray 500" hex="#6B7280" />
                <ColorSwatch color="bg-gray-900" name="Gray 900" hex="#111827" />
              </HStack>
            </VStack>
          </VStack>

          {/* Typography */}
          <VStack space="md">
            <Heading className="text-xl font-semibold">Typography</Heading>
            
            <VStack space="xs" className="border border-gray-200 rounded-lg p-4">
              <Heading className="text-2xl font-bold">Large Heading (24px)</Heading>
              <Heading className="text-xl font-semibold">Section Heading (20px)</Heading>
              <Heading className="text-lg font-semibold">Sub-Section Heading (18px)</Heading>
              <Text className="text-base font-bold">Card Title (16px Bold)</Text>
              <Text className="text-base">Body Text (16px)</Text>
              <Text className="text-sm">Small Text (14px)</Text>
              <Text className="text-xs text-gray-500">Caption/Metadata (12px)</Text>
            </VStack>
          </VStack>

          {/* Components */}
          <VStack space="lg">
            <Heading className="text-xl font-semibold">Components</Heading>
            
            {/* Student Profile Header */}
            <VStack space="xs">
              <Heading className="text-lg font-medium">Student Profile Header</Heading>
              <HStack className="bg-blue-600 rounded-lg p-4 items-center justify-between">
                <HStack space="md" className="items-center">
                  <Avatar className="bg-blue-700 h-14 w-14">
                    <AvatarFallbackText>JS</AvatarFallbackText>
                  </Avatar>
                  <VStack>
                    <Text className="text-white font-bold text-xl">João Silva</Text>
                    <Text className="text-white">Aluno • 9° Ano</Text>
                  </VStack>
                </HStack>
                <Avatar className="bg-blue-500 h-9 w-9">
                  <AvatarFallbackText>3</AvatarFallbackText>
                </Avatar>
              </HStack>
            </VStack>
            
            {/* Class Cards */}
            <VStack space="xs">
              <Heading className="text-lg font-medium">Class Cards</Heading>
              
              {/* Completed Class */}
              <HStack className="border border-gray-200 rounded-lg p-4 items-start">
                <Box className="bg-green-500 w-2 h-full rounded-full mr-4 self-stretch" />
                <VStack className="flex-1">
                  <HStack className="justify-between w-full">
                    <Text className="font-bold text-lg">Matemática</Text>
                    <Box className="bg-blue-50 rounded-full p-1">
                      <Icon as={CheckIcon} size="sm" color="#3B82F6" />
                    </Box>
                  </HStack>
                  <Text>Hoje • 14:30 - 16:00</Text>
                  <Text>Prof. Ana Santos • Sala 203</Text>
                </VStack>
              </HStack>
              
              {/* Upcoming Class */}
              <HStack className="border border-gray-200 rounded-lg p-4 items-start">
                <Box className="bg-orange-500 w-2 h-full rounded-full mr-4 self-stretch" />
                <VStack className="flex-1">
                  <HStack className="justify-between w-full">
                    <Text className="font-bold text-lg">Física</Text>
                  </HStack>
                  <Text>Amanhã • 09:00 - 10:30</Text>
                  <Text>Prof. Carlos Lima • Sala 105</Text>
                </VStack>
              </HStack>
            </VStack>
            
            {/* Task Cards */}
            <VStack space="xs">
              <Heading className="text-lg font-medium">Task Cards</Heading>
              
              {/* Urgent Task */}
              <HStack className="border border-gray-200 rounded-lg p-4 items-center justify-between">
                <HStack space="md">
                  <Avatar className="bg-red-50 h-12 w-12">
                    <Icon as={MinusIcon} color="#EF4444" />
                  </Avatar>
                  <VStack>
                    <Text className="font-semibold">Relatório de Laboratório</Text>
                    <Text>Entrega: Hoje às 18:00</Text>
                  </VStack>
                </HStack>
                <Text className="text-red-500 font-semibold">URGENTE</Text>
              </HStack>
              
              {/* Regular Task */}
              <HStack className="border border-gray-200 rounded-lg p-4 items-center justify-between">
                <HStack space="md">
                  <Avatar className="bg-blue-50 h-12 w-12">
                    <Icon as={BookOpenIcon} color="#3B82F6" />
                  </Avatar>
                  <VStack>
                    <Text className="font-semibold">Lista de Exercícios</Text>
                    <Text>Entrega: Em 3 dias</Text>
                  </VStack>
                </HStack>
              </HStack>
            </VStack>
            
            {/* Empty States */}
            <VStack space="xs">
              <Heading className="text-lg font-medium">Empty States</Heading>
              <Box className="border border-gray-200 rounded-lg p-8 items-center">
                <Text className="text-center text-gray-500">Nenhuma mensagem recente</Text>
              </Box>
            </VStack>
            
            {/* Status Indicators */}
            <VStack space="xs">
              <Heading className="text-lg font-medium">Status Indicators</Heading>
              <HStack className="flex-wrap" space="md">
                <StatusIndicator 
                  label="Completed" 
                  icon={CheckIcon} 
                  color="#22C55E" 
                  bgColor="#DCFCE7" 
                />
                <StatusIndicator 
                  label="In Progress" 
                  icon={ClockIcon}
                  color="#F97316" 
                  bgColor="#FFF7ED" 
                />
                <StatusIndicator 
                  label="Urgent" 
                  icon={AlertCircleIcon} 
                  color="#EF4444" 
                  bgColor="#FEF2F2" 
                />
                <StatusIndicator 
                  label="Info" 
                  icon={InfoIcon} 
                  color="#3B82F6" 
                  bgColor="#EFF6FF" 
                />
              </HStack>
            </VStack>
            
            {/* Buttons */}
            <VStack space="xs">
              <Heading className="text-lg font-medium">Buttons</Heading>
              <HStack className="flex-wrap" space="md">
                <Button className="bg-blue-600">
                  <ButtonText>Primary Button</ButtonText>
                </Button>
                
                <Button variant="outline" className="border-blue-600">
                  <ButtonText className="text-blue-600">Outline Button</ButtonText>
                </Button>
                
                <Button variant="link">
                  <ButtonText className="text-blue-600">Link Button</ButtonText>
                </Button>
                
                <Button action="negative" className="bg-red-500">
                  <ButtonText>Negative Button</ButtonText>
                </Button>
              </HStack>
            </VStack>
          </VStack>
          
          {/* Spacing Reference */}
          <VStack space="md">
            <Heading className="text-xl font-semibold">Spacing Reference</Heading>
            <VStack className="border border-gray-200 rounded-lg p-4" space="md">
              <Heading className="text-lg font-medium">Margins and Padding</Heading>
              <VStack>
                <SpacingExample label="xs (4px)" size="xs" />
                <SpacingExample label="sm (8px)" size="sm" />
                <SpacingExample label="md (12px)" size="md" />
                <SpacingExample label="lg (16px)" size="lg" />
                <SpacingExample label="xl (24px)" size="xl" />
                <SpacingExample label="2xl (32px)" size="2xl" />
              </VStack>
            </VStack>
          </VStack>
        </VStack>
      </ScrollView>
    </SafeAreaView>
  );
};

// Helper Components

const ColorSwatch = ({ color, name, hex, borderVisible = false }) => (
  <VStack className="m-1 items-center">
    <Box className={`${color} ${borderVisible ? 'border border-gray-300' : ''} w-16 h-16 rounded-md`} />
    <Text className="text-xs mt-1 font-medium">{name}</Text>
    <Text className="text-xs text-gray-500">{hex}</Text>
  </VStack>
);

const StatusIndicator = ({ label, icon, color, bgColor }) => (
  <HStack className="border border-gray-200 rounded-lg p-2 m-1 items-center" space="sm">
    <Box style={{ backgroundColor: bgColor }} className="rounded-full p-1">
      <Icon as={icon} size="sm" color={color} />
    </Box>
    <Text className="text-sm">{label}</Text>
  </HStack>
);

const SpacingExample = ({ label, size }) => (
  <HStack className="items-center my-1">
    <Text className="text-sm w-20">{label}</Text>
    <HStack space={size} className="items-center">
      <Box className="bg-blue-500 w-4 h-4 rounded-full" />
      <Box className="bg-blue-500 w-4 h-4 rounded-full" />
    </HStack>
  </HStack>
);

export default DesignSystemReference; 