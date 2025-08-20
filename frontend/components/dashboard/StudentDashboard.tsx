import { router } from 'expo-router';
import {
  CheckIcon,
  MinusIcon,
  AlertTriangleIcon,
  MessagesSquare,
  HomeIcon,
  Home,
  BarChart3,
} from 'lucide-react-native';
import React, { useEffect, useState } from 'react';
import { Platform, Alert } from 'react-native';

import { useUserProfile } from '@/api/auth';
import { Avatar, AvatarFallbackText, AvatarImage } from '@/components/ui/avatar';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Center } from '@/components/ui/center';
import { Divider } from '@/components/ui/divider';
import { Grid, GridItem } from '@/components/ui/grid';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { ChevronLeftIcon, ChevronDownIcon, Icon, MenuIcon } from '@/components/ui/icon';
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
import { isWeb } from '@/utils/platform';

// Define new interfaces for student dashboard
interface ClassInfo {
  subject: string;
  date: string;
  timeStart: string;
  timeEnd: string;
  teacher: string;
  room: string;
  completed?: boolean;
  colorAccent: string;
}

interface TaskInfo {
  title: string;
  dueDate: string;
  isUrgent?: boolean;
}

// Sample data for student dashboard
const upcomingClasses: ClassInfo[] = [
  {
    subject: 'Matemática',
    date: 'Hoje',
    timeStart: '14:30',
    timeEnd: '16:00',
    teacher: 'Prof. Ana Santos',
    room: 'Sala 203',
    completed: true,
    colorAccent: 'bg-green-500',
  },
  {
    subject: 'Física',
    date: 'Amanhã',
    timeStart: '09:00',
    timeEnd: '10:30',
    teacher: 'Prof. Carlos Lima',
    room: 'Sala 105',
    colorAccent: 'bg-orange-500',
  },
];

const pendingTasks: TaskInfo[] = [
  {
    title: 'Relatório de Laboratório',
    dueDate: 'Hoje às 18:00',
    isUrgent: true,
  },
  {
    title: 'Lista de Exercícios',
    dueDate: 'Em 3 dias',
  },
];

const MainContent = () => {
  const { userProfile } = useUserProfile();
  const userName = userProfile?.name || 'Aluno';
  const userGrade = '9° Ano';
  const userInitials = userName
    .split(' ')
    .map(n => n[0])
    .join('');

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
          {/* Student Profile */}
          <HStack className="bg-blue-600 rounded-lg p-4 items-center justify-between">
            <HStack space="md" className="items-center">
              <Avatar className="bg-blue-700 h-14 w-14">
                <AvatarFallbackText>{userInitials}</AvatarFallbackText>
              </Avatar>
              <VStack>
                <Text className="text-white font-bold text-xl">{userName}</Text>
                <Text className="text-white">Aluno • {userGrade}</Text>
              </VStack>
            </HStack>
            <Avatar className="bg-blue-500 h-9 w-9">
              <AvatarFallbackText>3</AvatarFallbackText>
            </Avatar>
          </HStack>

          <Heading className="text-2xl font-bold">Dashboard</Heading>

          {/* Upcoming Classes */}
          <VStack space="md">
            <Heading className="text-lg font-semibold">Próximas Aulas</Heading>
            {upcomingClasses.map((classInfo, index) => (
              <HStack key={index} className="border border-gray-200 rounded-lg p-4 items-start">
                <Box
                  className={`${classInfo.colorAccent} w-2 h-full rounded-full mr-4 self-stretch`}
                />
                <VStack className="flex-1">
                  <HStack className="justify-between w-full">
                    <Text className="font-bold text-lg">{classInfo.subject}</Text>
                    {classInfo.completed && (
                      <Box className="bg-blue-50 rounded-full p-1">
                        <Icon as={CheckIcon} size="sm" color="#3B82F6" />
                      </Box>
                    )}
                  </HStack>
                  <Text>
                    {classInfo.date} • {classInfo.timeStart} - {classInfo.timeEnd}
                  </Text>
                  <Text>
                    {classInfo.teacher} • {classInfo.room}
                  </Text>
                </VStack>
              </HStack>
            ))}
          </VStack>

          {/* Pending Tasks */}
          <VStack space="md">
            <Heading className="text-lg font-semibold">Tarefas Pendentes</Heading>
            {pendingTasks.map((task, index) => (
              <HStack
                key={index}
                className="border border-gray-200 rounded-lg p-4 items-center justify-between"
              >
                <HStack space="md">
                  <Avatar className="bg-red-50 h-12 w-12">
                    <Icon as={MinusIcon} color="#EF4444" />
                  </Avatar>
                  <VStack>
                    <Text className="font-semibold">{task.title}</Text>
                    <Text>Entrega: {task.dueDate}</Text>
                  </VStack>
                </HStack>
                {task.isUrgent && <Text className="text-red-500 font-semibold">URGENTE</Text>}
              </HStack>
            ))}
          </VStack>

          {/* Recent Messages */}
          <VStack space="md">
            <Heading className="text-lg font-semibold">Mensagens Recentes</Heading>
            {/* Empty state for messages */}
            <Box className="border border-gray-200 rounded-lg p-8 items-center">
              <Text className="text-center text-gray-500">Nenhuma mensagem recente</Text>
            </Box>
          </VStack>

          {/* Admin Dashboard Link - For demo purposes */}
          <VStack space="md" className="mt-4">
            <Pressable
              className="bg-indigo-600 rounded-lg p-4 items-center"
              onPress={() => router.push('/admin')}
            >
              <Text className="text-white font-bold">Acessar Dashboard Admin</Text>
            </Pressable>
          </VStack>
        </VStack>
      </ScrollView>
    </Box>
  );
};

export const StudentDashboard = () => {
  return (
    <SafeAreaView className="h-full w-full">
      <MainContent />
    </SafeAreaView>
  );
};
