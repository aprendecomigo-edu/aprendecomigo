import { Plus, X, ChevronDownIcon } from 'lucide-react-native';
import React, { useState } from 'react';
import { Alert } from 'react-native';

import { TeacherProfileData, SubjectExpertise } from '@/api/invitationApi';
import { Badge } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { FormControl } from '@/components/ui/form-control';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Input, InputField } from '@/components/ui/input';
import {
  Select,
  SelectTrigger,
  SelectInput,
  SelectIcon,
  SelectPortal,
  SelectBackdrop,
  SelectContent,
  SelectDragIndicatorWrapper,
  SelectDragIndicator,
  SelectItem,
} from '@/components/ui/select';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { COMMON_SUBJECTS } from '@/hooks/useInvitationProfileWizard';

interface TeachingSubjectsStepProps {
  profileData: TeacherProfileData;
  updateProfileData: (updates: Partial<TeacherProfileData>) => void;
  validationErrors: { [key: string]: string };
  invitationData: any;
  onAddSubject: (subject: SubjectExpertise) => void;
  onRemoveSubject: (index: number) => void;
}

const TeachingSubjectsStep: React.FC<TeachingSubjectsStepProps> = ({
  profileData,
  updateProfileData,
  validationErrors,
  invitationData,
  onAddSubject,
  onRemoveSubject,
}) => {
  const [newSubject, setNewSubject] = useState('');
  const [newSubjectLevel, setNewSubjectLevel] = useState<
    'beginner' | 'intermediate' | 'advanced' | 'expert'
  >('intermediate');
  const [newSubjectExperience, setNewSubjectExperience] = useState('');
  const [showCustomInput, setShowCustomInput] = useState(false);

  const handleAddSubject = () => {
    if (!newSubject.trim()) {
      Alert.alert('Erro', 'Por favor, selecione ou digite uma matéria');
      return;
    }

    const experienceYears = newSubjectExperience ? parseInt(newSubjectExperience) : undefined;

    const subjectToAdd: SubjectExpertise = {
      subject: newSubject.trim(),
      level: newSubjectLevel,
      years_experience: experienceYears && experienceYears > 0 ? experienceYears : undefined,
    };

    onAddSubject(subjectToAdd);

    // Reset form
    setNewSubject('');
    setNewSubjectLevel('intermediate');
    setNewSubjectExperience('');
    setShowCustomInput(false);
  };

  const handleQuickAddSubject = (subject: string) => {
    const subjectToAdd: SubjectExpertise = {
      subject,
      level: 'intermediate',
    };
    onAddSubject(subjectToAdd);
  };

  const getLevelLabel = (level: string) => {
    switch (level) {
      case 'beginner':
        return 'Iniciante';
      case 'intermediate':
        return 'Intermediário';
      case 'advanced':
        return 'Avançado';
      case 'expert':
        return 'Especialista';
      default:
        return level;
    }
  };

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'beginner':
        return 'bg-blue-100 text-blue-800';
      case 'intermediate':
        return 'bg-green-100 text-green-800';
      case 'advanced':
        return 'bg-orange-100 text-orange-800';
      case 'expert':
        return 'bg-purple-100 text-purple-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <Box className="flex-1">
      <VStack space="lg">
        {/* Header */}
        <VStack space="sm">
          <Heading size="xl" className="text-gray-900">
            Matérias de Ensino
          </Heading>
          <Text className="text-gray-600">
            Selecione as matérias que você ensina e seu nível de experiência em cada uma.
          </Text>
        </VStack>

        {/* Quick Add Popular Subjects */}
        <VStack space="sm">
          <Text className="font-medium">Matérias Populares</Text>
          <Text className="text-sm text-gray-600">Toque para adicionar rapidamente:</Text>
          <Box className="flex-row flex-wrap">
            {COMMON_SUBJECTS.filter(
              subject => !profileData.teaching_subjects.some(ts => ts.subject === subject)
            )
              .slice(0, 8)
              .map(subject => (
                <Button
                  key={subject}
                  variant="outline"
                  size="sm"
                  className="m-1"
                  onPress={() => handleQuickAddSubject(subject)}
                >
                  <ButtonText className="text-sm">{subject}</ButtonText>
                </Button>
              ))}
          </Box>
        </VStack>

        {/* Add Custom Subject */}
        <VStack space="sm">
          <HStack className="justify-between items-center">
            <Text className="font-medium">Adicionar Matéria Personalizada</Text>
            <Button
              variant="outline"
              size="sm"
              onPress={() => setShowCustomInput(!showCustomInput)}
            >
              <Icon as={Plus} size="sm" />
              <ButtonText className="ml-1">Adicionar</ButtonText>
            </Button>
          </HStack>

          {showCustomInput && (
            <VStack space="md" className="bg-gray-50 p-4 rounded-lg">
              <FormControl>
                <VStack space="sm">
                  <Text className="text-sm font-medium">Nome da Matéria *</Text>
                  <Input>
                    <InputField
                      placeholder="Ex: Programação Web, Xadrez, etc."
                      value={newSubject}
                      onChangeText={setNewSubject}
                    />
                  </Input>
                </VStack>
              </FormControl>

              <FormControl>
                <VStack space="sm">
                  <Text className="text-sm font-medium">Nível de Experiência</Text>
                  <Select
                    selectedValue={newSubjectLevel}
                    onValueChange={value => setNewSubjectLevel(value as any)}
                  >
                    <SelectTrigger variant="outline" size="md">
                      <SelectInput placeholder="Selecione o nível" />
                      <SelectIcon className="mr-3" as={ChevronDownIcon} />
                    </SelectTrigger>
                    <SelectPortal>
                      <SelectBackdrop />
                      <SelectContent>
                        <SelectDragIndicatorWrapper>
                          <SelectDragIndicator />
                        </SelectDragIndicatorWrapper>
                        <SelectItem label="Iniciante" value="beginner" />
                        <SelectItem label="Intermediário" value="intermediate" />
                        <SelectItem label="Avançado" value="advanced" />
                        <SelectItem label="Especialista" value="expert" />
                      </SelectContent>
                    </SelectPortal>
                  </Select>
                </VStack>
              </FormControl>

              <FormControl>
                <VStack space="sm">
                  <Text className="text-sm font-medium">Anos de Experiência (opcional)</Text>
                  <Input>
                    <InputField
                      placeholder="Ex: 5"
                      value={newSubjectExperience}
                      onChangeText={setNewSubjectExperience}
                      keyboardType="numeric"
                    />
                  </Input>
                </VStack>
              </FormControl>

              <HStack space="sm">
                <Button variant="outline" size="sm" onPress={() => setShowCustomInput(false)}>
                  <ButtonText>Cancelar</ButtonText>
                </Button>
                <Button size="sm" onPress={handleAddSubject}>
                  <ButtonText>Adicionar Matéria</ButtonText>
                </Button>
              </HStack>
            </VStack>
          )}
        </VStack>

        {/* Current Subjects */}
        <VStack space="sm">
          <Text className="font-medium">
            Suas Matérias ({profileData.teaching_subjects.length})
          </Text>
          {validationErrors.teaching_subjects && (
            <Text className="text-red-600 text-sm">{validationErrors.teaching_subjects}</Text>
          )}

          {profileData.teaching_subjects.length === 0 ? (
            <Box className="bg-gray-50 p-4 rounded-lg border border-dashed border-gray-300">
              <Text className="text-gray-600 text-center">
                Nenhuma matéria adicionada ainda. Adicione pelo menos uma matéria acima.
              </Text>
            </Box>
          ) : (
            <VStack space="sm">
              {profileData.teaching_subjects.map((subject, index) => (
                <Box key={index} className="bg-white p-3 rounded-lg border border-gray-200">
                  <HStack className="justify-between items-start">
                    <VStack space="xs" className="flex-1">
                      <Text className="font-medium text-gray-900">{subject.subject}</Text>
                      <HStack space="sm" className="items-center">
                        <Badge className={getLevelColor(subject.level)}>
                          <Text className="text-xs font-medium">
                            {getLevelLabel(subject.level)}
                          </Text>
                        </Badge>
                        {subject.years_experience && (
                          <Text className="text-xs text-gray-600">
                            {subject.years_experience} anos de experiência
                          </Text>
                        )}
                      </HStack>
                    </VStack>
                    <Button variant="outline" size="sm" onPress={() => onRemoveSubject(index)}>
                      <Icon as={X} size="sm" className="text-red-600" />
                    </Button>
                  </HStack>
                </Box>
              ))}
            </VStack>
          )}
        </VStack>

        {/* Help Text */}
        <Box className="bg-blue-50 p-4 rounded-lg border border-blue-200">
          <VStack space="sm">
            <Text className="font-medium text-blue-800">Dica:</Text>
            <Text className="text-sm text-blue-700">
              Seja específico sobre suas matérias. Por exemplo, ao invés de "Ciências", considere
              "Física", "Química" ou "Biologia" separadamente. Isso ajuda os alunos a encontrarem
              exatamente o que precisam.
            </Text>
          </VStack>
        </Box>
      </VStack>
    </Box>
  );
};

export default TeachingSubjectsStep;
