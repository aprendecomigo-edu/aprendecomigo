import React, { useState } from 'react';
import { useAuth } from '@/api/authContext';
import { Avatar, AvatarFallbackText } from '@/components/ui/avatar';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Center } from '@/components/ui/center';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import {
  Modal,
  ModalBackdrop,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
} from '@/components/ui/modal';
import { Pressable } from '@/components/ui/pressable';
import { SafeAreaView } from '@/components/ui/safe-area-view';
import { ScrollView } from '@/components/ui/scroll-view';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { isWeb } from '@gluestack-ui/nativewind-utils/IsWeb';
import { BellIcon, ChevronLeftIcon, ChevronRightIcon, CheckIcon, AlertTriangleIcon, UserIcon, BookOpenIcon, ClipboardListIcon, UsersIcon, SchoolIcon, CalendarIcon, BriefcaseIcon } from 'lucide-react-native';
import { useRouter } from 'expo-router';

// Import the DashboardLayout from the dashboard-layout directory
import { bottomTabsList, DashboardLayout, MobileFooter, School, schools } from '../dashboard-layout';

// Define interfaces for admin dashboard
interface ScheduleClass {
  subject: string;
  timeStart: string;
  timeEnd: string;
  teacher: string;
  room: string;
  className: string;
  colorAccent: string;
}

interface Notification {
  id: string;
  title: string;
  message: string;
  time: string;
  isRead: boolean;
}

interface StatCard {
  title: string;
  value: string;
  icon: any;
  colorClass: string;
  change?: string;
  isPositive?: boolean;
}

// Sample data for admin dashboard
const todaySchedule: ScheduleClass[] = [
  {
    subject: 'Matemática',
    timeStart: '08:00',
    timeEnd: '09:30',
    teacher: 'Prof. Ana Santos',
    room: 'Sala 203',
    className: '9° Ano A',
    colorAccent: 'bg-green-500',
  },
  {
    subject: 'Física',
    timeStart: '09:45',
    timeEnd: '11:15',
    teacher: 'Prof. Carlos Lima',
    room: 'Sala 105',
    className: '10° Ano B',
    colorAccent: 'bg-orange-500',
  },
  {
    subject: 'História',
    timeStart: '13:00',
    timeEnd: '14:30',
    teacher: 'Prof. Maria Silva',
    room: 'Sala 302',
    className: '8° Ano C',
    colorAccent: 'bg-purple-500',
  },
  {
    subject: 'Inglês',
    timeStart: '14:45',
    timeEnd: '16:15',
    teacher: 'Prof. João Martins',
    room: 'Sala 401',
    className: '11° Ano A',
    colorAccent: 'bg-blue-500',
  },
];

const recentNotifications: Notification[] = [
  {
    id: '1',
    title: 'Professor ausente',
    message: 'O Prof. João Martins estará ausente amanhã',
    time: 'Há 30 minutos',
    isRead: false,
  },
  {
    id: '2',
    title: 'Reunião de pais',
    message: 'A reunião de pais do 9° Ano será no dia 15/06',
    time: 'Há 2 horas',
    isRead: false,
  },
  {
    id: '3',
    title: 'Relatório mensal',
    message: 'O relatório mensal está disponível para revisão',
    time: 'Ontem',
    isRead: true,
  },
];

const statsCards: StatCard[] = [
  {
    title: 'Alunos Totais',
    value: '856',
    icon: UserIcon,
    colorClass: 'bg-blue-100 text-blue-700',
    change: '+3.2%',
    isPositive: true,
  },
  {
    title: 'Professores',
    value: '42',
    icon: BriefcaseIcon,
    colorClass: 'bg-purple-100 text-purple-700',
  },
  {
    title: 'Turmas',
    value: '28',
    icon: UsersIcon,
    colorClass: 'bg-amber-100 text-amber-700',
  },
  {
    title: 'Disciplinas',
    value: '16',
    icon: BookOpenIcon,
    colorClass: 'bg-emerald-100 text-emerald-700',
  },
];

// Admin Dashboard Component
const AdminDashboard = () => {
  const { userProfile } = useAuth();
  const userName = userProfile?.name || 'Administrador';
  const userInitials = userName
    .split(' ')
    .map(n => n[0])
    .join('');

  const [showNotifications, setShowNotifications] = useState(false);
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedDay, setSelectedDay] = useState('HOJE');

  const handlePrevDay = () => {
    const newDate = new Date(currentDate);
    newDate.setDate(currentDate.getDate() - 1);
    setCurrentDate(newDate);
    setSelectedDay('ONTEM');
  };

  const handleNextDay = () => {
    const newDate = new Date(currentDate);
    newDate.setDate(currentDate.getDate() + 1);
    setCurrentDate(newDate);
    setSelectedDay('AMANHÃ');
  };

  const handleToday = () => {
    setCurrentDate(new Date());
    setSelectedDay('HOJE');
  };

  const toggleNotifications = () => {
    setShowNotifications(!showNotifications);
  };

  const unreadNotifications = recentNotifications.filter(n => !n.isRead).length;

  const formattedDate = currentDate.toLocaleDateString('pt-BR', {
    weekday: 'long',
    day: '2-digit',
    month: 'long',
    year: 'numeric'
  }).replace(',', '');

  const router = useRouter();

  return (
    <Box className="flex-1">
      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={{
          paddingBottom: isWeb ? 0 : 100,
          flexGrow: 1,
        }}
        className="flex-1 mb-20 md:mb-2"
      >
        <VStack className="p-4 pb-0 md:px-6 md:pt-6 w-full" space="xl">
          {/* Admin Profile */}
          <HStack className="bg-blue-600 rounded-lg p-4 items-center justify-between">
            <HStack space="md" className="items-center">
              <Avatar className="bg-blue-700 h-14 w-14">
                <AvatarFallbackText>{userInitials}</AvatarFallbackText>
              </Avatar>
              <VStack>
                <Text className="text-white font-bold text-xl">Olá, {userName}</Text>
                <Text className="text-white">Administrador</Text>
              </VStack>
            </HStack>
            <Pressable onPress={toggleNotifications}>
              {unreadNotifications > 0 ? (
                <Box className="relative">
                  <Box className="bg-blue-500 h-9 w-9 rounded-full items-center justify-center">
                    <Icon as={BellIcon} size="sm" color="white" />
                  </Box>
                  <Box className="absolute -top-0.5 -right-0.5 bg-red-500 rounded-full h-3 w-3" />
                </Box>
              ) : (
                <Box className="bg-blue-500 h-9 w-9 rounded-full items-center justify-center">
                  <Icon as={BellIcon} size="sm" color="white" />
                </Box>
              )}
            </Pressable>
          </HStack>

          {/* Dashboard Stats */}
          <VStack space="md">
            <Heading className="text-xl font-bold">Visão Geral</Heading>
            <HStack className="flex-wrap -mx-2">
              {statsCards.map((stat, index) => (
                <Box key={index} className="w-1/2 md:w-1/4 p-2">
                  <VStack className="border border-gray-200 rounded-lg p-4 bg-white">
                    <Text className="text-gray-600 text-sm">{stat.title}</Text>
                    <HStack space="xs" className="items-baseline">
                      <Text className="font-bold text-xl">{stat.value}</Text>
                      {stat.change && (
                        <Text className={stat.isPositive ? "text-green-600 text-xs" : "text-red-600 text-xs"}>
                          {stat.change}
                        </Text>
                      )}
                    </HStack>
                  </VStack>
                </Box>
              ))}
            </HStack>
          </VStack>

          {/* Notifications Modal */}
          <Modal isOpen={showNotifications} onClose={toggleNotifications}>
            <ModalBackdrop />
            <ModalContent>
              <ModalHeader>
                <Heading size="lg">Notificações</Heading>
                <ModalCloseButton>
                  <Icon as={ChevronLeftIcon} />
                </ModalCloseButton>
              </ModalHeader>
              <ModalBody>
                <VStack space="md">
                  {recentNotifications.length > 0 ? (
                    recentNotifications.map((notification) => (
                      <HStack
                        key={notification.id}
                        className={`p-3 border-b border-gray-200 ${notification.isRead ? 'opacity-70' : 'bg-blue-50'}`}
                      >
                        <VStack className="flex-1">
                          <HStack className="justify-between">
                            <Text className="font-bold">{notification.title}</Text>
                            <Text className="text-xs text-gray-500">{notification.time}</Text>
                          </HStack>
                          <Text>{notification.message}</Text>
                        </VStack>
                        {!notification.isRead && (
                          <Box className="w-2 h-2 rounded-full bg-blue-500 self-center ml-2" />
                        )}
                      </HStack>
                    ))
                  ) : (
                    <Center className="p-4">
                      <Text>Não há notificações</Text>
                    </Center>
                  )}
                </VStack>
              </ModalBody>
              <ModalFooter>
                <Button onPress={toggleNotifications} variant="outline">
                  <ButtonText>Fechar</ButtonText>
                </Button>
              </ModalFooter>
            </ModalContent>
          </Modal>

          {/* Daily Schedule Section */}
          <VStack space="md">
            <HStack className="items-center justify-between">
              <Heading className="text-xl font-bold uppercase">{selectedDay}</Heading>
              <HStack className="space-x-2">
                <Pressable onPress={handlePrevDay}>
                  <Icon as={ChevronLeftIcon} />
                </Pressable>
                {selectedDay !== 'HOJE' && (
                  <Pressable onPress={handleToday}>
                    <Text className="text-blue-600 font-medium">Hoje</Text>
                  </Pressable>
                )}
                <Pressable onPress={handleNextDay}>
                  <Icon as={ChevronRightIcon} />
                </Pressable>
              </HStack>
            </HStack>
            <Text className="text-gray-600">{formattedDate}</Text>

            {/* Class Schedule */}
            <VStack space="md" className="mt-2">
              <HStack className="justify-between">
                <Text className="font-medium">Todas as aulas</Text>
                <Pressable>
                  <Text className="text-blue-600">Ver calendário completo</Text>
                </Pressable>
              </HStack>
              {todaySchedule.map((classInfo, index) => (
                <HStack key={index} className="border border-gray-200 rounded-lg p-4 items-start">
                  <Box
                    className={`${classInfo.colorAccent} w-2 h-full rounded-full mr-4 self-stretch`}
                  />
                  <VStack className="flex-1">
                    <Text className="font-bold text-lg">{classInfo.subject}</Text>
                    <Text>
                      {classInfo.timeStart} - {classInfo.timeEnd}
                    </Text>
                    <Text>
                      {classInfo.teacher} • {classInfo.room}
                    </Text>
                  </VStack>
                  <Text className="text-gray-600 font-medium self-start">{classInfo.className}</Text>
                </HStack>
              ))}
            </VStack>
          </VStack>

          {/* Quick Actions */}
          <VStack space="md">
            <Heading className="text-xl font-bold">Ações Rápidas</Heading>
            <HStack className="flex-wrap -mx-2">
              <Box className="w-1/2 p-2">
                <Pressable className="border border-gray-200 rounded-lg p-4 items-center bg-white">
                  <Box className="w-12 h-12 rounded-full bg-blue-100 items-center justify-center mb-2">
                    <Icon as={CalendarIcon} size="md" color="#3B82F6" />
                  </Box>
                  <Text className="font-medium text-center">Gerenciar Horários</Text>
                </Pressable>
              </Box>
              <Box className="w-1/2 p-2">
                <Pressable className="border border-gray-200 rounded-lg p-4 items-center bg-white">
                  <Box className="w-12 h-12 rounded-full bg-purple-100 items-center justify-center mb-2">
                    <Icon as={ClipboardListIcon} size="md" color="#8B5CF6" />
                  </Box>
                  <Text className="font-medium text-center">Relatórios</Text>
                </Pressable>
              </Box>
              <Box className="w-1/2 p-2">
                <Pressable className="border border-gray-200 rounded-lg p-4 items-center bg-white">
                  <Box className="w-12 h-12 rounded-full bg-amber-100 items-center justify-center mb-2">
                    <Icon as={UsersIcon} size="md" color="#F59E0B" />
                  </Box>
                  <Text className="font-medium text-center">Gerenciar Alunos</Text>
                </Pressable>
              </Box>
              <Box className="w-1/2 p-2">
                <Pressable className="border border-gray-200 rounded-lg p-4 items-center bg-white">
                  <Box className="w-12 h-12 rounded-full bg-emerald-100 items-center justify-center mb-2">
                    <Icon as={SchoolIcon} size="md" color="#10B981" />
                  </Box>
                  <Text className="font-medium text-center">Configurações</Text>
                </Pressable>
              </Box>
            </HStack>
          </VStack>

          {/* Student Dashboard Link - For development/demo purposes */}
          <VStack space="md" className="mt-4">
            <Pressable
              className="bg-gray-200 rounded-lg p-4 items-center"
              onPress={() => router.push('/student')}
            >
              <Text className="text-gray-700 font-bold">Ver Dashboard do Aluno</Text>
            </Pressable>
          </VStack>
        </VStack>
      </ScrollView>
    </Box>
  );
};

// Export the AdminDashboard wrapped with the Dashboard layout
export const AdminDashboardPage = () => {
  const [selectedSchool, setSelectedSchool] = useState<School>(schools[0]);

  const handleSchoolChange = (school: School) => {
    setSelectedSchool(school);
    // Here you would typically fetch data for the selected school
  };

  return (
    <SafeAreaView className="h-full w-full">
      <DashboardLayout title={selectedSchool.name} isSidebarVisible={true}>
        <AdminDashboard />
      </DashboardLayout>
      <MobileFooter footerIcons={bottomTabsList} />
    </SafeAreaView>
  );
};

export default AdminDashboardPage;
