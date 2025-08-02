import { router } from 'expo-router';
import {
  GraduationCapIcon,
  CalendarIcon,
  UsersIcon,
  TrendingUpIcon,
  DollarSignIcon,
} from 'lucide-react-native';
import React, { useCallback } from 'react';

import { useAuth } from '@/api/authContext';
import MainLayout from '@/components/layouts/main-layout';
import StudentAcquisitionHub from '@/components/tutor-dashboard/StudentAcquisitionHub';
import { Button, ButtonText } from '@/components/ui/button';
import { Card, CardBody, CardHeader } from '@/components/ui/card';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { ScrollView } from '@/components/ui/scroll-view';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

const TutorDashboard = () => {
  const { userProfile } = useAuth();

  // Mock school data for testing
  const mockSchool = {
    id: 1,
    name: `${userProfile?.name || 'Tutor'} - Negócio de Tutoria`,
  };

  const selectedSchoolId = mockSchool.id;

  // Quick action handlers
  const handleScheduleSession = useCallback(() => {
    router.push('/calendar/book');
  }, []);

  const handleViewStudents = useCallback(() => {
    router.push('/(tutor)/students');
  }, []);

  const handleViewAnalytics = useCallback(() => {
    router.push('/(tutor)/analytics');
  }, []);

  const handleManageSessions = useCallback(() => {
    router.push('/(tutor)/sessions');
  }, []);

  // Welcome message
  const name = userProfile?.name?.split(' ')[0] || 'Tutor';
  const currentHour = new Date().getHours();
  let welcomeMessage = `Bom dia, ${name}!`;
  if (currentHour >= 12 && currentHour < 18) {
    welcomeMessage = `Boa tarde, ${name}!`;
  } else if (currentHour >= 18) {
    welcomeMessage = `Boa noite, ${name}!`;
  }

  return (
    <ScrollView showsVerticalScrollIndicator={false} className="flex-1 bg-gray-50">
      <VStack className="p-6" space="lg">
        {/* Header Section */}
        <VStack space="sm">
          <Heading size="xl" className="text-gray-900">
            {welcomeMessage}
          </Heading>
          <Text className="text-gray-600">{mockSchool.name}</Text>
          <Text className="text-sm text-gray-500">
            {new Date().toLocaleDateString('pt-PT', {
              weekday: 'long',
              day: '2-digit',
              month: 'long',
              year: 'numeric',
            })}
          </Text>
        </VStack>

        {/* Quick Actions Panel */}
        <Card variant="elevated" className="bg-white shadow-sm">
          <CardHeader>
            <Heading size="md" className="text-gray-900">
              Ações Rápidas
            </Heading>
          </CardHeader>
          <CardBody>
            <VStack space="sm">
              <HStack space="sm">
                <Button className="flex-1 bg-blue-600" onPress={handleScheduleSession}>
                  <Icon as={CalendarIcon} size="sm" className="text-white mr-2" />
                  <ButtonText>Agendar Aula</ButtonText>
                </Button>
                <Button className="flex-1 bg-green-600" onPress={handleViewStudents}>
                  <Icon as={UsersIcon} size="sm" className="text-white mr-2" />
                  <ButtonText>Ver Estudantes</ButtonText>
                </Button>
              </HStack>
              <HStack space="sm">
                <Button variant="outline" className="flex-1" onPress={handleViewAnalytics}>
                  <Icon as={TrendingUpIcon} size="sm" className="text-blue-600 mr-2" />
                  <ButtonText className="text-blue-600">Analytics</ButtonText>
                </Button>
                <Button variant="outline" className="flex-1" onPress={handleManageSessions}>
                  <Icon as={DollarSignIcon} size="sm" className="text-green-600 mr-2" />
                  <ButtonText className="text-green-600">Sessões</ButtonText>
                </Button>
              </HStack>
            </VStack>
          </CardBody>
        </Card>

        {/* Student Acquisition Hub - THE KEY COMPONENT FOR TESTING */}
        <StudentAcquisitionHub
          schoolId={selectedSchoolId}
          tutorName={userProfile?.name || 'Tutor'}
        />

        {/* Getting Started Guide */}
        <Card
          variant="elevated"
          className="bg-gradient-to-r from-green-50 to-blue-50 border-2 border-dashed border-green-200 shadow-sm"
        >
          <CardBody>
            <VStack space="md" className="items-center text-center">
              <VStack space="sm">
                <Text className="text-lg font-bold text-gray-900">
                  Bem-vindo ao teu negócio de tutoria! 🎓
                </Text>
                <Text className="text-sm text-gray-600">
                  Use a secção "Aquisição de Estudantes" acima para começar a convidar novos
                  estudantes.
                </Text>
              </VStack>
              <HStack space="sm">
                <Button variant="solid" onPress={() => router.push('/(tutor)/acquisition')}>
                  <ButtonText>Convidar Mais Estudantes</ButtonText>
                </Button>
              </HStack>
            </VStack>
          </CardBody>
        </Card>
      </VStack>
    </ScrollView>
  );
};

// Export wrapped with MainLayout
export const TutorDashboardPageMinimal = () => {
  return (
    <MainLayout _title="Dashboard do Tutor">
      <TutorDashboard />
    </MainLayout>
  );
};

export default TutorDashboardPageMinimal;
