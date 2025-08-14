import {
  User,
  BookOpen,
  GraduationCap,
  Clock,
  Euro,
  Award,
  Star,
  Lightbulb,
  Target,
  Check,
  Edit,
  Send,
  Globe,
} from 'lucide-react-native';
import React from 'react';
import { Alert } from 'react-native';

import { TeacherProfileData, GradeLevel } from '@/api/invitationApi';
import { Badge } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Divider } from '@/components/ui/divider';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { ScrollView } from '@/components/ui/scroll-view';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

interface PreviewSubmitStepProps {
  profileData: TeacherProfileData;
  updateProfileData: (updates: Partial<TeacherProfileData>) => void;
  validationErrors: { [key: string]: string };
  invitationData: any;
  onEditStep: (stepNumber: number) => void;
  onSubmit: () => void;
  isSubmitting: boolean;
}

const PreviewSubmitStep: React.FC<PreviewSubmitStepProps> = ({
  profileData,
  updateProfileData,
  validationErrors,
  invitationData,
  onEditStep,
  onSubmit,
  isSubmitting,
}) => {
  const formatGradeLevel = (level: GradeLevel): string => {
    switch (level) {
      case GradeLevel.ELEMENTARY:
        return 'Fundamental I';
      case GradeLevel.MIDDLE_SCHOOL:
        return 'Fundamental II';
      case GradeLevel.HIGH_SCHOOL:
        return 'Ensino Médio';
      case GradeLevel.UNIVERSITY:
        return 'Superior';
      default:
        return level;
    }
  };

  const formatDate = (dateString: string): string => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-PT', { year: 'numeric', month: 'long' });
  };

  const getAvailabilityHours = (): number => {
    if (!profileData.availability_schedule) return 0;
    let totalHours = 0;
    Object.values(profileData.availability_schedule).forEach(daySlots => {
      daySlots.forEach(slot => {
        const start = parseInt(slot.start_time.split(':')[0]);
        const end = parseInt(slot.end_time.split(':')[0]);
        totalHours += end - start;
      });
    });
    return totalHours;
  };

  const getCompletionStatus = () => {
    const requiredFields = [
      profileData.introduction,
      profileData.teaching_subjects.length > 0,
      profileData.grade_levels.length > 0,
      profileData.timezone,
      profileData.hourly_rate > 0,
      profileData.education_background.length > 0,
      profileData.teaching_philosophy,
      profileData.teaching_approach,
      profileData.specializations && profileData.specializations.length > 0,
    ];

    const completed = requiredFields.filter(Boolean).length;
    const total = requiredFields.length;

    return { completed, total, percentage: Math.round((completed / total) * 100) };
  };

  const completionStatus = getCompletionStatus();

  return (
    <Box className="flex-1">
      <ScrollView>
        <VStack space="lg" className="pb-6">
          {/* Header */}
          <VStack space="sm">
            <Heading size="xl" className="text-gray-900">
              Revisão e Submissão
            </Heading>
            <Text className="text-gray-600">
              Revise todas as informações do seu perfil antes de finalizar. Você poderá editar
              qualquer seção.
            </Text>
          </VStack>

          {/* Completion Status */}
          <Box
            className={`p-4 rounded-lg border ${
              completionStatus.percentage === 100
                ? 'bg-green-50 border-green-200'
                : 'bg-yellow-50 border-yellow-200'
            }`}
          >
            <HStack className="justify-between items-center">
              <VStack>
                <Text
                  className={`font-medium ${
                    completionStatus.percentage === 100 ? 'text-green-800' : 'text-yellow-800'
                  }`}
                >
                  Perfil {completionStatus.percentage}% Completo
                </Text>
                <Text
                  className={`text-sm ${
                    completionStatus.percentage === 100 ? 'text-green-700' : 'text-yellow-700'
                  }`}
                >
                  {completionStatus.completed} de {completionStatus.total} seções preenchidas
                </Text>
              </VStack>
              <Icon
                as={completionStatus.percentage === 100 ? Check : Edit}
                size="lg"
                className={
                  completionStatus.percentage === 100 ? 'text-green-600' : 'text-yellow-600'
                }
              />
            </HStack>
          </Box>

          {/* School Information */}
          <Box className="bg-blue-50 p-4 rounded-lg border border-blue-200">
            <VStack space="sm">
              <Text className="font-medium text-blue-800">Escola de Destino</Text>
              <Text className="text-blue-700">{invitationData?.invitation?.school?.name}</Text>
              <Text className="text-sm text-blue-600">
                Convidado por: {invitationData?.invitation?.invited_by?.name}
              </Text>
            </VStack>
          </Box>

          {/* Profile Sections */}

          {/* 1. Basic Information */}
          <Box className="bg-white p-4 rounded-lg border border-gray-200">
            <HStack className="justify-between items-start mb-3">
              <HStack className="items-center" space="sm">
                <Icon as={User} size="md" className="text-blue-600" />
                <Heading size="md" className="text-gray-800">
                  Informações Básicas
                </Heading>
              </HStack>
              <Button variant="outline" size="sm" onPress={() => onEditStep(1)}>
                <Icon as={Edit} size="sm" />
                <ButtonText className="ml-1">Editar</ButtonText>
              </Button>
            </HStack>
            <VStack space="sm">
              <Text className="text-gray-600">
                <Text className="font-medium">Apresentação:</Text>{' '}
                {profileData.introduction || 'Não preenchido'}
              </Text>
              <Text className="text-gray-600">
                <Text className="font-medium">Contato preferido:</Text>{' '}
                {profileData.contact_preferences?.preferred_contact_method || 'Email'}
              </Text>
            </VStack>
          </Box>

          {/* 2. Teaching Subjects */}
          <Box className="bg-white p-4 rounded-lg border border-gray-200">
            <HStack className="justify-between items-start mb-3">
              <HStack className="items-center" space="sm">
                <Icon as={BookOpen} size="md" className="text-green-600" />
                <Heading size="md" className="text-gray-800">
                  Matérias de Ensino
                </Heading>
              </HStack>
              <Button variant="outline" size="sm" onPress={() => onEditStep(2)}>
                <Icon as={Edit} size="sm" />
                <ButtonText className="ml-1">Editar</ButtonText>
              </Button>
            </HStack>
            <VStack space="sm">
              <Text className="text-gray-600">
                <Text className="font-medium">Total:</Text> {profileData.teaching_subjects.length}{' '}
                matérias
              </Text>
              <Box className="flex-row flex-wrap">
                {profileData.teaching_subjects.slice(0, 6).map((subject, index) => (
                  <Badge key={index} className="bg-green-100 text-green-800 m-1">
                    <Text className="text-sm">{subject.subject}</Text>
                  </Badge>
                ))}
                {profileData.teaching_subjects.length > 6 && (
                  <Badge className="bg-gray-100 text-gray-800 m-1">
                    <Text className="text-sm">
                      +{profileData.teaching_subjects.length - 6} mais
                    </Text>
                  </Badge>
                )}
              </Box>
            </VStack>
          </Box>

          {/* 3. Grade Levels */}
          <Box className="bg-white p-4 rounded-lg border border-gray-200">
            <HStack className="justify-between items-start mb-3">
              <HStack className="items-center" space="sm">
                <Icon as={GraduationCap} size="md" className="text-purple-600" />
                <Heading size="md" className="text-gray-800">
                  Níveis de Ensino
                </Heading>
              </HStack>
              <Button variant="outline" size="sm" onPress={() => onEditStep(3)}>
                <Icon as={Edit} size="sm" />
                <ButtonText className="ml-1">Editar</ButtonText>
              </Button>
            </HStack>
            <VStack space="sm">
              <Text className="text-gray-600">
                <Text className="font-medium">Níveis:</Text> {profileData.grade_levels.length}{' '}
                selecionados
              </Text>
              <Box className="flex-row flex-wrap">
                {profileData.grade_levels.map((level, index) => (
                  <Badge key={index} className="bg-purple-100 text-purple-800 m-1">
                    <Text className="text-sm">{formatGradeLevel(level)}</Text>
                  </Badge>
                ))}
              </Box>
            </VStack>
          </Box>

          {/* 4. Availability */}
          <Box className="bg-white p-4 rounded-lg border border-gray-200">
            <HStack className="justify-between items-start mb-3">
              <HStack className="items-center" space="sm">
                <Icon as={Clock} size="md" className="text-orange-600" />
                <Heading size="md" className="text-gray-800">
                  Disponibilidade
                </Heading>
              </HStack>
              <Button variant="outline" size="sm" onPress={() => onEditStep(4)}>
                <Icon as={Edit} size="sm" />
                <ButtonText className="ml-1">Editar</ButtonText>
              </Button>
            </HStack>
            <VStack space="sm">
              <HStack className="items-center" space="sm">
                <Icon as={Globe} size="sm" className="text-gray-600" />
                <Text className="text-gray-600">
                  <Text className="font-medium">Fuso horário:</Text> {profileData.timezone}
                </Text>
              </HStack>
              <Text className="text-gray-600">
                <Text className="font-medium">Disponibilidade:</Text> ~{getAvailabilityHours()}{' '}
                horas/semana
              </Text>
              {profileData.availability_notes && (
                <Text className="text-gray-600 text-sm italic">
                  "{profileData.availability_notes.substring(0, 100)}..."
                </Text>
              )}
            </VStack>
          </Box>

          {/* 5. Rates */}
          <Box className="bg-white p-4 rounded-lg border border-gray-200">
            <HStack className="justify-between items-start mb-3">
              <HStack className="items-center" space="sm">
                <Icon as={Euro} size="md" className="text-green-600" />
                <Heading size="md" className="text-gray-800">
                  Taxas
                </Heading>
              </HStack>
              <Button variant="outline" size="sm" onPress={() => onEditStep(5)}>
                <Icon as={Edit} size="sm" />
                <ButtonText className="ml-1">Editar</ButtonText>
              </Button>
            </HStack>
            <VStack space="sm">
              <Text className="text-gray-600">
                <Text className="font-medium">Taxa por hora:</Text> €{profileData.hourly_rate}/hora
              </Text>
              <Text className="text-gray-600">
                <Text className="font-medium">Negociável:</Text>{' '}
                {profileData.rate_negotiable ? 'Sim' : 'Não'}
              </Text>
              <Text className="text-gray-600">
                <Text className="font-medium">Método de pagamento:</Text>{' '}
                {profileData.payment_preferences?.preferred_payment_method ||
                  'Transferência bancária'}
              </Text>
            </VStack>
          </Box>

          {/* 6. Credentials */}
          <Box className="bg-white p-4 rounded-lg border border-gray-200">
            <HStack className="justify-between items-start mb-3">
              <HStack className="items-center" space="sm">
                <Icon as={Award} size="md" className="text-blue-600" />
                <Heading size="md" className="text-gray-800">
                  Credenciais
                </Heading>
              </HStack>
              <Button variant="outline" size="sm" onPress={() => onEditStep(6)}>
                <Icon as={Edit} size="sm" />
                <ButtonText className="ml-1">Editar</ButtonText>
              </Button>
            </HStack>
            <VStack space="sm">
              <Text className="text-gray-600">
                <Text className="font-medium">Formação:</Text>{' '}
                {profileData.education_background.length} entrada(s)
              </Text>
              <Text className="text-gray-600">
                <Text className="font-medium">Experiência:</Text>{' '}
                {profileData.teaching_experience.length} entrada(s)
              </Text>
              <Text className="text-gray-600">
                <Text className="font-medium">Certificações:</Text>{' '}
                {profileData.certifications.length} certificação(ões)
              </Text>
              {profileData.education_background.length > 0 && (
                <Text className="text-sm text-gray-600 italic">
                  Última formação: {profileData.education_background[0]?.degree} em{' '}
                  {profileData.education_background[0]?.field_of_study}
                </Text>
              )}
            </VStack>
          </Box>

          {/* 7. Marketing */}
          <Box className="bg-white p-4 rounded-lg border border-gray-200">
            <HStack className="justify-between items-start mb-3">
              <HStack className="items-center" space="sm">
                <Icon as={Target} size="md" className="text-purple-600" />
                <Heading size="md" className="text-gray-800">
                  Marketing
                </Heading>
              </HStack>
              <Button variant="outline" size="sm" onPress={() => onEditStep(7)}>
                <Icon as={Edit} size="sm" />
                <ButtonText className="ml-1">Editar</ButtonText>
              </Button>
            </HStack>
            <VStack space="sm">
              <Text className="text-gray-600">
                <Text className="font-medium">Filosofia:</Text>{' '}
                {profileData.teaching_philosophy
                  ? `${profileData.teaching_philosophy.substring(0, 80)}...`
                  : 'Não preenchido'}
              </Text>
              <Text className="text-gray-600">
                <Text className="font-medium">Abordagem:</Text>{' '}
                {profileData.teaching_approach
                  ? `${profileData.teaching_approach.substring(0, 80)}...`
                  : 'Não preenchido'}
              </Text>
              <Text className="text-gray-600">
                <Text className="font-medium">Especializações:</Text>{' '}
                {(profileData.specializations || []).length} especialização(ões)
              </Text>
              {profileData.achievements && profileData.achievements.length > 0 && (
                <Text className="text-gray-600">
                  <Text className="font-medium">Conquistas:</Text> {profileData.achievements.length}{' '}
                  conquista(s)
                </Text>
              )}
            </VStack>
          </Box>

          <Divider />

          {/* Final Actions */}
          <VStack space="md">
            {completionStatus.percentage < 100 && (
              <Box className="bg-yellow-50 p-4 rounded-lg border border-yellow-200">
                <VStack space="sm">
                  <Text className="font-medium text-yellow-800">Atenção</Text>
                  <Text className="text-sm text-yellow-700">
                    Seu perfil ainda não está 100% completo. Recomendamos preencher todas as seções
                    para aumentar suas chances de ser escolhido pelos alunos.
                  </Text>
                </VStack>
              </Box>
            )}

            <Box className="bg-green-50 p-4 rounded-lg border border-green-200">
              <VStack space="sm">
                <Text className="font-medium text-green-800">Próximos Passos</Text>
                <VStack space="xs">
                  <Text className="text-sm text-green-700">
                    • Seu perfil será revisado pela escola
                  </Text>
                  <Text className="text-sm text-green-700">
                    • Você receberá acesso ao dashboard do professor
                  </Text>
                  <Text className="text-sm text-green-700">
                    • Poderá começar a receber convites para aulas
                  </Text>
                  <Text className="text-sm text-green-700">
                    • Sempre poderá editar seu perfil posteriormente
                  </Text>
                </VStack>
              </VStack>
            </Box>

            <Button onPress={onSubmit} disabled={isSubmitting} className="bg-green-600" size="lg">
              {isSubmitting ? (
                <HStack space="sm" className="items-center">
                  <Spinner size="small" />
                  <ButtonText className="text-white">Finalizando...</ButtonText>
                </HStack>
              ) : (
                <HStack space="sm" className="items-center">
                  <Icon as={Send} size="sm" className="text-white" />
                  <ButtonText className="text-white">Finalizar e Aceitar Convite</ButtonText>
                </HStack>
              )}
            </Button>
          </VStack>
        </VStack>
      </ScrollView>
    </Box>
  );
};

export default PreviewSubmitStep;
