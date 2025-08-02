import { Plus, X, Star, Target, Lightbulb, Trophy } from 'lucide-react-native';
import React, { useState } from 'react';
import { Alert } from 'react-native';

import { TeacherProfileData } from '@/api/invitationApi';
import { Badge } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { FormControl } from '@/components/ui/form-control';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Input, InputField } from '@/components/ui/input';
import { Text } from '@/components/ui/text';
import { Textarea, TextareaInput } from '@/components/ui/textarea';
import { VStack } from '@/components/ui/vstack';

interface ProfileMarketingStepProps {
  profileData: TeacherProfileData;
  updateProfileData: (updates: Partial<TeacherProfileData>) => void;
  validationErrors: { [key: string]: string };
  invitationData: any;
}

const ProfileMarketingStep: React.FC<ProfileMarketingStepProps> = ({
  profileData,
  updateProfileData,
  validationErrors,
  invitationData,
}) => {
  const [newSpecialization, setNewSpecialization] = useState('');
  const [newAchievement, setNewAchievement] = useState('');

  const philosophyExamples = [
    'Acredito que cada aluno tem seu próprio ritmo de aprendizado e deve ser respeitado',
    'O ensino deve ser prático e conectado com o mundo real',
    'Aprender deve ser divertido e envolvente para ser eficaz',
    'Cada erro é uma oportunidade de crescimento e aprendizado',
  ];

  const approachExamples = [
    'Uso métodos visuais e exemplos práticos para explicar conceitos abstratos',
    'Adapto meu estilo de ensino às necessidades individuais de cada aluno',
    'Incorporo tecnologia e ferramentas interativas nas minhas aulas',
    'Foco em construir confiança antes de avançar para tópicos mais complexos',
  ];

  const commonSpecializations = [
    'Preparação para Exames',
    'Dificuldades de Aprendizagem',
    'Ensino Online',
    'Métodos Visuais',
    'Gamificação',
    'Educação Inclusiva',
    'STEM',
    'Línguas Estrangeiras',
  ];

  const handleAddSpecialization = () => {
    if (!newSpecialization.trim()) {
      Alert.alert('Erro', 'Por favor, digite uma especialização');
      return;
    }

    const currentSpecializations = profileData.specializations || [];
    if (currentSpecializations.includes(newSpecialization.trim())) {
      Alert.alert('Erro', 'Esta especialização já foi adicionada');
      return;
    }

    updateProfileData({
      specializations: [...currentSpecializations, newSpecialization.trim()],
    });
    setNewSpecialization('');
  };

  const removeSpecialization = (index: number) => {
    const currentSpecializations = [...profileData.specializations];
    currentSpecializations.splice(index, 1);
    updateProfileData({ specializations: currentSpecializations });
  };

  const addQuickSpecialization = (specialization: string) => {
    const currentSpecializations = profileData.specializations || [];
    if (currentSpecializations.includes(specialization)) {
      return;
    }
    updateProfileData({
      specializations: [...currentSpecializations, specialization],
    });
  };

  const handleAddAchievement = () => {
    if (!newAchievement.trim()) {
      Alert.alert('Erro', 'Por favor, digite uma conquista');
      return;
    }

    const currentAchievements = profileData.achievements || [];
    updateProfileData({
      achievements: [...currentAchievements, newAchievement.trim()],
    });
    setNewAchievement('');
  };

  const removeAchievement = (index: number) => {
    const currentAchievements = [...(profileData.achievements || [])];
    currentAchievements.splice(index, 1);
    updateProfileData({ achievements: currentAchievements });
  };

  const useExampleText = (field: 'teaching_philosophy' | 'teaching_approach', example: string) => {
    updateProfileData({ [field]: example });
  };

  return (
    <Box className="flex-1">
      <VStack space="lg">
        {/* Header */}
        <VStack space="sm">
          <Heading size="xl" className="text-gray-900">
            Marketing do Perfil
          </Heading>
          <Text className="text-gray-600">
            Esta informação ajuda alunos e pais a entenderem seu estilo de ensino e escolherem você
            como professor.
          </Text>
        </VStack>

        {/* Teaching Philosophy */}
        <FormControl className={validationErrors.teaching_philosophy ? 'error' : ''}>
          <VStack space="sm">
            <HStack className="items-center" space="sm">
              <Icon as={Lightbulb} size="sm" className="text-yellow-600" />
              <Text className="font-medium">Filosofia de Ensino *</Text>
            </HStack>
            <Text className="text-sm text-gray-600">
              Descreva sua filosofia e crenças sobre educação. O que você acredita sobre o processo
              de aprendizagem?
            </Text>
            <Textarea className="min-h-[120px]">
              <TextareaInput
                placeholder="Exemplo: Acredito que cada aluno é único e aprende de forma diferente. Meu papel é identificar o estilo de aprendizagem de cada um e adaptar minha metodologia..."
                value={profileData.teaching_philosophy || ''}
                onChangeText={value => updateProfileData({ teaching_philosophy: value })}
                multiline
                textAlignVertical="top"
              />
            </Textarea>
            {validationErrors.teaching_philosophy && (
              <Text className="text-red-600 text-sm">{validationErrors.teaching_philosophy}</Text>
            )}

            {/* Example Philosophy Buttons */}
            <VStack space="xs">
              <Text className="text-xs text-gray-500">Exemplos para inspiração:</Text>
              <VStack space="xs">
                {philosophyExamples.map((example, index) => (
                  <Button
                    key={index}
                    variant="outline"
                    size="sm"
                    onPress={() => useExampleText('teaching_philosophy', example)}
                    className="items-start"
                  >
                    <ButtonText className="text-xs text-left flex-1">{example}</ButtonText>
                  </Button>
                ))}
              </VStack>
            </VStack>
          </VStack>
        </FormControl>

        {/* Teaching Approach */}
        <FormControl className={validationErrors.teaching_approach ? 'error' : ''}>
          <VStack space="sm">
            <HStack className="items-center" space="sm">
              <Icon as={Target} size="sm" className="text-blue-600" />
              <Text className="font-medium">Abordagem de Ensino *</Text>
            </HStack>
            <Text className="text-sm text-gray-600">
              Descreva suas metodologias e técnicas de ensino. Como você estrutura suas aulas?
            </Text>
            <Textarea className="min-h-[120px]">
              <TextareaInput
                placeholder="Exemplo: Utilizo uma abordagem prática e interativa, combinando explicações teóricas com exercícios práticos. Gosto de usar analogias do dia a dia para facilitar a compreensão..."
                value={profileData.teaching_approach || ''}
                onChangeText={value => updateProfileData({ teaching_approach: value })}
                multiline
                textAlignVertical="top"
              />
            </Textarea>
            {validationErrors.teaching_approach && (
              <Text className="text-red-600 text-sm">{validationErrors.teaching_approach}</Text>
            )}

            {/* Example Approach Buttons */}
            <VStack space="xs">
              <Text className="text-xs text-gray-500">Exemplos para inspiração:</Text>
              <VStack space="xs">
                {approachExamples.map((example, index) => (
                  <Button
                    key={index}
                    variant="outline"
                    size="sm"
                    onPress={() => useExampleText('teaching_approach', example)}
                    className="items-start"
                  >
                    <ButtonText className="text-xs text-left flex-1">{example}</ButtonText>
                  </Button>
                ))}
              </VStack>
            </VStack>
          </VStack>
        </FormControl>

        {/* Specializations */}
        <FormControl className={validationErrors.specializations ? 'error' : ''}>
          <VStack space="sm">
            <HStack className="items-center" space="sm">
              <Icon as={Star} size="sm" className="text-purple-600" />
              <Text className="font-medium">Especializações *</Text>
            </HStack>
            <Text className="text-sm text-gray-600">
              Áreas específicas em que você tem expertise especial ou métodos diferenciados.
            </Text>

            {/* Quick Add Specializations */}
            <VStack space="sm">
              <Text className="text-sm font-medium">Especializações Comuns:</Text>
              <Box className="flex-row flex-wrap">
                {commonSpecializations
                  .filter(spec => !(profileData.specializations || []).includes(spec))
                  .map(specialization => (
                    <Button
                      key={specialization}
                      variant="outline"
                      size="sm"
                      className="m-1"
                      onPress={() => addQuickSpecialization(specialization)}
                    >
                      <ButtonText className="text-sm">{specialization}</ButtonText>
                    </Button>
                  ))}
              </Box>
            </VStack>

            {/* Custom Specialization Input */}
            <HStack space="sm">
              <Input className="flex-1">
                <InputField
                  placeholder="Adicionar especialização personalizada"
                  value={newSpecialization}
                  onChangeText={setNewSpecialization}
                />
              </Input>
              <Button onPress={handleAddSpecialization}>
                <Icon as={Plus} size="sm" />
                <ButtonText className="ml-1">Adicionar</ButtonText>
              </Button>
            </HStack>

            {/* Current Specializations */}
            {profileData.specializations && profileData.specializations.length > 0 && (
              <VStack space="sm">
                <Text className="text-sm font-medium">
                  Suas Especializações ({profileData.specializations.length}):
                </Text>
                <Box className="flex-row flex-wrap">
                  {profileData.specializations.map((specialization, index) => (
                    <HStack key={index} className="items-center m-1">
                      <Badge className="bg-purple-100 text-purple-800">
                        <Text className="text-sm font-medium pr-2">{specialization}</Text>
                      </Badge>
                      <Button
                        variant="outline"
                        size="xs"
                        onPress={() => removeSpecialization(index)}
                        className="ml-1"
                      >
                        <Icon as={X} size="xs" className="text-red-600" />
                      </Button>
                    </HStack>
                  ))}
                </Box>
              </VStack>
            )}

            {validationErrors.specializations && (
              <Text className="text-red-600 text-sm">{validationErrors.specializations}</Text>
            )}
          </VStack>
        </FormControl>

        {/* Achievements */}
        <FormControl>
          <VStack space="sm">
            <HStack className="items-center" space="sm">
              <Icon as={Trophy} size="sm" className="text-orange-600" />
              <Text className="font-medium">Conquistas e Reconhecimentos (opcional)</Text>
            </HStack>
            <Text className="text-sm text-gray-600">
              Prêmios, reconhecimentos, resultados especiais de alunos, ou outras conquistas
              relevantes.
            </Text>

            <HStack space="sm">
              <Input className="flex-1">
                <InputField
                  placeholder="Ex: 95% dos meus alunos passaram no exame nacional"
                  value={newAchievement}
                  onChangeText={setNewAchievement}
                />
              </Input>
              <Button onPress={handleAddAchievement}>
                <Icon as={Plus} size="sm" />
                <ButtonText className="ml-1">Adicionar</ButtonText>
              </Button>
            </HStack>

            {/* Current Achievements */}
            {profileData.achievements && profileData.achievements.length > 0 && (
              <VStack space="sm">
                <Text className="text-sm font-medium">Suas Conquistas:</Text>
                <VStack space="xs">
                  {profileData.achievements.map((achievement, index) => (
                    <HStack
                      key={index}
                      className="justify-between items-start p-3 bg-orange-50 rounded-lg border border-orange-200"
                    >
                      <Text className="text-sm text-orange-800 flex-1">{achievement}</Text>
                      <Button variant="outline" size="xs" onPress={() => removeAchievement(index)}>
                        <Icon as={X} size="xs" className="text-red-600" />
                      </Button>
                    </HStack>
                  ))}
                </VStack>
              </VStack>
            )}
          </VStack>
        </FormControl>

        {/* Profile Summary Preview */}
        {(profileData.teaching_philosophy ||
          profileData.teaching_approach ||
          (profileData.specializations && profileData.specializations.length > 0)) && (
          <Box className="bg-green-50 p-4 rounded-lg border border-green-200">
            <VStack space="sm">
              <Text className="font-medium text-green-800">Prévia do seu perfil:</Text>
              <VStack space="xs">
                <Text className="text-sm text-green-700">
                  <Text className="font-medium">Filosofia:</Text>{' '}
                  {profileData.teaching_philosophy?.substring(0, 100)}...
                </Text>
                <Text className="text-sm text-green-700">
                  <Text className="font-medium">Abordagem:</Text>{' '}
                  {profileData.teaching_approach?.substring(0, 100)}...
                </Text>
                {profileData.specializations && profileData.specializations.length > 0 && (
                  <Text className="text-sm text-green-700">
                    <Text className="font-medium">Especializações:</Text>{' '}
                    {profileData.specializations.join(', ')}
                  </Text>
                )}
              </VStack>
            </VStack>
          </Box>
        )}

        {/* Help Text */}
        <Box className="bg-blue-50 p-4 rounded-lg border border-blue-200">
          <VStack space="sm">
            <Text className="font-medium text-blue-800">Dicas para um perfil atrativo:</Text>
            <VStack space="xs" className="ml-2">
              <Text className="text-sm text-blue-700">
                • Seja autêntico e pessoal - os pais querem conhecer quem você realmente é
              </Text>
              <Text className="text-sm text-blue-700">
                • Use linguagem clara e acessível, evite termos muito técnicos
              </Text>
              <Text className="text-sm text-blue-700">
                • Mencione como você lida com diferentes tipos de alunos
              </Text>
              <Text className="text-sm text-blue-700">
                • Inclua resultados concretos quando possível (aprovações, melhorias de notas)
              </Text>
              <Text className="text-sm text-blue-700">
                • Mostre paixão pelo ensino - isso é contagiante e atrai alunos
              </Text>
            </VStack>
          </VStack>
        </Box>
      </VStack>
    </Box>
  );
};

export default ProfileMarketingStep;
