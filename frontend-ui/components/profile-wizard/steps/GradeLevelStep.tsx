import { Check, GraduationCap, Users, BookOpen, School } from 'lucide-react-native';
import React from 'react';
import { Alert } from 'react-native';

import { TeacherProfileData, GradeLevel } from '@/api/invitationApi';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Checkbox, CheckboxIndicator, CheckboxIcon, CheckboxLabel } from '@/components/ui/checkbox';
import { FormControl } from '@/components/ui/form-control';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

interface GradeLevelStepProps {
  profileData: TeacherProfileData;
  updateProfileData: (updates: Partial<TeacherProfileData>) => void;
  validationErrors: { [key: string]: string };
  invitationData: any;
}

const GradeLevelStep: React.FC<GradeLevelStepProps> = ({
  profileData,
  updateProfileData,
  validationErrors,
  invitationData,
}) => {
  const gradeLevelOptions = [
    {
      value: GradeLevel.ELEMENTARY,
      label: 'Ensino Fundamental I',
      description: '1º ao 5º ano (6-10 anos)',
      icon: Users,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
      borderColor: 'border-green-200',
    },
    {
      value: GradeLevel.MIDDLE_SCHOOL,
      label: 'Ensino Fundamental II',
      description: '6º ao 9º ano (11-14 anos)',
      icon: BookOpen,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
      borderColor: 'border-blue-200',
    },
    {
      value: GradeLevel.HIGH_SCHOOL,
      label: 'Ensino Médio',
      description: '1º ao 3º ano (15-17 anos)',
      icon: School,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
      borderColor: 'border-purple-200',
    },
    {
      value: GradeLevel.UNIVERSITY,
      label: 'Ensino Superior',
      description: 'Graduação e Pós-graduação',
      icon: GraduationCap,
      color: 'text-orange-600',
      bgColor: 'bg-orange-50',
      borderColor: 'border-orange-200',
    },
  ];

  const isGradeLevelSelected = (gradeLevel: GradeLevel): boolean => {
    return profileData.grade_levels.includes(gradeLevel);
  };

  const toggleGradeLevel = (gradeLevel: GradeLevel) => {
    const currentLevels = [...profileData.grade_levels];
    const index = currentLevels.indexOf(gradeLevel);

    if (index > -1) {
      // Remove if already selected
      currentLevels.splice(index, 1);
    } else {
      // Add if not selected
      currentLevels.push(gradeLevel);
    }

    updateProfileData({ grade_levels: currentLevels });
  };

  const selectAllLevels = () => {
    const allLevels = gradeLevelOptions.map(option => option.value);
    updateProfileData({ grade_levels: allLevels });
  };

  const clearAllLevels = () => {
    updateProfileData({ grade_levels: [] });
  };

  return (
    <Box className="flex-1">
      <VStack space="lg">
        {/* Header */}
        <VStack space="sm">
          <Heading size="xl" className="text-gray-900">
            Níveis de Ensino
          </Heading>
          <Text className="text-gray-600">
            Selecione os níveis de ensino em que você tem experiência e se sente confortável
            lecionando.
          </Text>
        </VStack>

        {/* Quick Actions */}
        <HStack space="sm" className="justify-end">
          <Button variant="outline" size="sm" onPress={clearAllLevels}>
            <ButtonText>Limpar Tudo</ButtonText>
          </Button>
          <Button variant="outline" size="sm" onPress={selectAllLevels}>
            <ButtonText>Selecionar Todos</ButtonText>
          </Button>
        </HStack>

        {/* Grade Level Options */}
        <FormControl className={validationErrors.grade_levels ? 'error' : ''}>
          <VStack space="md">
            {gradeLevelOptions.map(option => {
              const isSelected = isGradeLevelSelected(option.value);
              const IconComponent = option.icon;

              return (
                <Box
                  key={option.value}
                  className={`border-2 rounded-lg p-4 ${
                    isSelected
                      ? `${option.borderColor} ${option.bgColor}`
                      : 'border-gray-200 bg-white'
                  }`}
                >
                  <Checkbox
                    value={option.value}
                    isChecked={isSelected}
                    onChange={() => toggleGradeLevel(option.value)}
                    className="w-full"
                  >
                    <HStack className="items-start space-x-3 flex-1">
                      <CheckboxIndicator className="mt-1">
                        <CheckboxIcon as={Check} />
                      </CheckboxIndicator>

                      <Icon
                        as={IconComponent}
                        size="lg"
                        className={isSelected ? option.color : 'text-gray-400'}
                      />

                      <VStack className="flex-1" space="xs">
                        <CheckboxLabel>
                          <Text
                            className={`font-semibold ${
                              isSelected ? 'text-gray-900' : 'text-gray-700'
                            }`}
                          >
                            {option.label}
                          </Text>
                        </CheckboxLabel>
                        <Text
                          className={`text-sm ${isSelected ? 'text-gray-700' : 'text-gray-500'}`}
                        >
                          {option.description}
                        </Text>
                      </VStack>
                    </HStack>
                  </Checkbox>
                </Box>
              );
            })}
          </VStack>

          {validationErrors.grade_levels && (
            <Text className="text-red-600 text-sm mt-2">{validationErrors.grade_levels}</Text>
          )}
        </FormControl>

        {/* Selection Summary */}
        {profileData.grade_levels.length > 0 && (
          <Box className="bg-green-50 p-4 rounded-lg border border-green-200">
            <VStack space="sm">
              <Text className="font-medium text-green-800">
                Selecionados ({profileData.grade_levels.length} níveis):
              </Text>
              <VStack space="xs">
                {profileData.grade_levels.map(level => {
                  const option = gradeLevelOptions.find(opt => opt.value === level);
                  return option ? (
                    <Text key={level} className="text-sm text-green-700">
                      • {option.label}
                    </Text>
                  ) : null;
                })}
              </VStack>
            </VStack>
          </Box>
        )}

        {/* Help Text */}
        <Box className="bg-blue-50 p-4 rounded-lg border border-blue-200">
          <VStack space="sm">
            <Text className="font-medium text-blue-800">Dicas para escolher:</Text>
            <VStack space="xs" className="ml-2">
              <Text className="text-sm text-blue-700">
                • Considere sua formação acadêmica e experiência prática
              </Text>
              <Text className="text-sm text-blue-700">
                • Pense nos grupos etários com os quais você se sente mais confortável
              </Text>
              <Text className="text-sm text-blue-700">
                • Lembre-se de que você pode adicionar mais níveis posteriormente
              </Text>
              <Text className="text-sm text-blue-700">
                • Cada nível tem metodologias e desafios pedagógicos específicos
              </Text>
            </VStack>
          </VStack>
        </Box>

        {/* Age Group Information */}
        <Box className="bg-gray-50 p-4 rounded-lg">
          <VStack space="sm">
            <Text className="font-medium text-gray-800">Informação sobre faixas etárias:</Text>
            <VStack space="xs">
              <Text className="text-sm text-gray-600">
                <Text className="font-medium">Fundamental I:</Text> Foco em alfabetização e
                conceitos básicos
              </Text>
              <Text className="text-sm text-gray-600">
                <Text className="font-medium">Fundamental II:</Text> Desenvolvimento de pensamento
                crítico
              </Text>
              <Text className="text-sm text-gray-600">
                <Text className="font-medium">Ensino Médio:</Text> Preparação para vestibular e ENEM
              </Text>
              <Text className="text-sm text-gray-600">
                <Text className="font-medium">Superior:</Text> Aprofundamento técnico e acadêmico
              </Text>
            </VStack>
          </VStack>
        </Box>
      </VStack>
    </Box>
  );
};

export default GradeLevelStep;
