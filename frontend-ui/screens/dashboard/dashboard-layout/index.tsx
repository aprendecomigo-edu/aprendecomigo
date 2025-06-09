import { cn } from '@gluestack-ui/nativewind-utils/cn';
import { isWeb } from '@gluestack-ui/nativewind-utils/IsWeb';
import { router } from 'expo-router';
import type { Href } from 'expo-router';
import type { LucideIcon } from 'lucide-react-native';
import {
  LogOutIcon,
  PlusIcon,
  CheckIcon,
  MinusIcon,
  AlertTriangleIcon,
  MessagesSquare,
  HomeIcon,
  Home,
} from 'lucide-react-native';
import React, { useEffect, useState } from 'react';
import { Platform, Alert } from 'react-native';

import { CalendarIcon } from './assets/icons/calendar';
import { ProfileIcon } from './assets/icons/profile';

import { useAuth } from '@/api/authContext';
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

type MobileHeaderProps = {
  title: string;
  onSchoolChange?: (school: School) => void;
};

type HeaderProps = {
  title: string;
  toggleSidebar: () => void;
  onSchoolChange?: (school: School) => void;
};

type Icons = {
  iconName: LucideIcon | typeof Icon;
  route?: string;
};
const list: Icons[] = [
  {
    iconName: HomeIcon,
    route: '/home',
  },
  {
    iconName: MessagesSquare,
    route: '/chat',
  },
];
type BottomTabs = {
  iconName: LucideIcon | typeof Icon;
  iconText: string;
  route?: string;
};
const bottomTabsList: BottomTabs[] = [
  {
    iconName: HomeIcon,
    iconText: 'Home',
    route: '/home',
  },
  {
    iconName: MessagesSquare,
    iconText: 'Chats',
    route: '/chat',
  },
  {
    iconName: ProfileIcon,
    iconText: 'Profile',
    route: '/profile',
  },
];

// Create a reusable logout button component to follow DRY principles
function LogoutButton({
  displayStyle = 'icon-only',
}: {
  displayStyle?: 'icon-only' | 'icon-with-text' | 'button';
}) {
  const { logout } = useAuth();
  const [showModal, setShowModal] = useState(false);

  const handlePressLogout = () => {
    setShowModal(true);
  };

  const handleConfirmLogout = async () => {
    setShowModal(false); // Close modal first

    // Short timeout to allow the modal to close smoothly
    setTimeout(async () => {
      try {
        await logout();
      } catch (error) {
        console.error('Error during logout:', error);
      }
    }, 150);
  };

  const handleCancelLogout = () => {
    setShowModal(false);
  };

  // Render the confirmation modal
  const renderModal = () => {
    return (
      <Modal isOpen={showModal} onClose={handleCancelLogout}>
        <ModalBackdrop />
        <ModalContent className="p-6">
          <ModalHeader>
            <Heading size="lg">Confirm Logout</Heading>
            <ModalCloseButton>
              <Icon as={ChevronLeftIcon} />
            </ModalCloseButton>
          </ModalHeader>
          <ModalBody>
            <Center>
              <Icon as={AlertTriangleIcon} className="w-14 h-14 mb-4 text-amber-500" />
              <Text className="text-center mb-2">Are you sure you want to log out?</Text>
              <Text className="text-center text-sm text-typography-500">
                You will need to sign in again to access your account.
              </Text>
            </Center>
          </ModalBody>
          <ModalFooter>
            <Button
              variant="outline"
              action="secondary"
              className="flex-1 mr-2"
              onPress={handleCancelLogout}
            >
              <ButtonText>Cancel</ButtonText>
            </Button>
            <Button action="negative" className="flex-1 ml-2" onPress={handleConfirmLogout}>
              <ButtonText>Logout</ButtonText>
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    );
  };

  if (displayStyle === 'button') {
    return (
      <>
        <Button
          size="sm"
          variant="outline"
          action="negative"
          onPress={handlePressLogout}
          className="border-error-600"
        >
          <HStack space="xs" className="items-center">
            <Icon as={LogOutIcon} className="w-4 h-4 stroke-error-700" />
            <ButtonText className="text-error-700">Logout</ButtonText>
          </HStack>
        </Button>
        {renderModal()}
      </>
    );
  }

  if (displayStyle === 'icon-with-text') {
    return (
      <>
        <Pressable
          className="bg-error-50 rounded-md p-2 mb-4 w-11 hover:bg-error-100"
          onPress={handlePressLogout}
        >
          <VStack className="items-center" space="xs">
            <Icon as={LogOutIcon} className="w-6 h-6 stroke-error-700" />
            <Text className="text-[10px] text-error-700 font-medium">Logout</Text>
          </VStack>
        </Pressable>
        {renderModal()}
      </>
    );
  }

  // Default icon-only
  return (
    <>
      <Pressable className="bg-error-50 rounded-full p-2" onPress={handlePressLogout}>
        <Icon as={LogOutIcon} className="w-5 h-5 stroke-error-700" />
      </Pressable>
      {renderModal()}
    </>
  );
}

const Sidebar = () => {
  const [selectedIndex, setSelectedIndex] = useState<number>(0);

  const handlePress = (index: number) => {
    setSelectedIndex(index);
    // Navigate based on route if available
    const selectedItem = list[index];
    if (selectedItem && selectedItem.route) {
      router.push(selectedItem.route as Href<string>);
    }
  };

  return (
    <VStack
      className="w-14 pt-5 h-full items-center border-r border-border-300 pb-5 bg-background-primary"
      space="xl"
    >
      <VStack className="items-center" space="xl">
        {list.map((item, index) => {
          return (
            <Pressable
              key={index}
              className="hover:bg-primary-600"
              onPress={() => handlePress(index)}
            >
              <Icon
                as={item.iconName}
                className={`w-[55px] h-9 stroke-background-0
                ${index === selectedIndex ? 'fill-background-0' : 'fill-none'}
                `}
              />
            </Pressable>
          );
        })}
      </VStack>

      <Box className="flex-1" />
    </VStack>
  );
};

type DashboardLayoutProps = {
  title: string;
  isSidebarVisible: boolean;
  onSchoolChange?: (school: School) => void;
  children: React.ReactNode;
};

const DashboardLayout = (props: DashboardLayoutProps) => {
  const [isSidebarVisible, setIsSidebarVisible] = useState(props.isSidebarVisible);
  function toggleSidebar() {
    setIsSidebarVisible(!isSidebarVisible);
  }
  return (
    <VStack className="h-full w-full bg-background-0">
      <Box className="md:hidden">
        <MobileHeader title={props.title} onSchoolChange={props.onSchoolChange} />
      </Box>
      <Box className="hidden md:flex">
        <WebHeader
          toggleSidebar={toggleSidebar}
          title={props.title}
          onSchoolChange={props.onSchoolChange}
        />
      </Box>
      <VStack className="h-full w-full">
        <HStack className="h-full w-full">
          <Box className="hidden md:flex h-full">{isSidebarVisible && <Sidebar />}</Box>
          <VStack className="w-full">{props.children}</VStack>
        </HStack>
      </VStack>
    </VStack>
  );
};

function MobileFooter({ footerIcons }: { footerIcons: any }) {
  return (
    <HStack
      className={cn(
        'bg-background-primary justify-between w-full absolute left-0 bottom-0 right-0 p-3 overflow-hidden items-center border-t-border-300 md:hidden border-t',
        { 'pb-5': Platform.OS === 'ios' },
        { 'pb-5': Platform.OS === 'android' }
      )}
    >
      {footerIcons.map(
        (
          item: { iconText: string; iconName: any; route?: string },
          index: React.Key | null | undefined
        ) => {
          return (
            <Pressable
              className="px-0.5 flex-1 flex-col items-center"
              key={index}
              onPress={() => {
                if (item.route) {
                  router.push(item.route as Href<string>);
                } else {
                  router.push('/home' as Href<string>);
                }
              }}
            >
              <Icon as={item.iconName} size="md" className="h-[32px] w-[65px] text-background-0" />
              <Text className="text-xs text-center text-background-50">{item.iconText}</Text>
            </Pressable>
          );
        }
      )}
    </HStack>
  );
}

// Define interface for school data
interface School {
  id: string;
  name: string;
}

// Mock school data
const schools: School[] = [
  {
    id: '1',
    name: 'Escola São Paulo',
  },
  {
    id: '2',
    name: 'Colégio Rio de Janeiro',
  },
];

// SchoolSelector component
function SchoolSelector({ onSchoolChange }: { onSchoolChange?: (school: School) => void }) {
  const [selectedSchool, setSelectedSchool] = useState<School>(schools[0]);
  const [showMenu, setShowMenu] = useState(false);

  const handleSelectSchool = (school: School) => {
    setSelectedSchool(school);
    setShowMenu(false);
    if (onSchoolChange) {
      onSchoolChange(school);
    }
  };

  const handleAddNewSchool = () => {
    // This would open a form to add a new school
    setShowMenu(false);
    // For now just show an alert
    Alert.alert('Add School', 'This would open a form to add a new school');
  };

  // Position differently based on platform
  const modalPosition = Platform.OS === 'web' ? { top: 60, left: 50 } : { top: 70, left: 10 };

  return (
    <Box className="relative">
      <Pressable onPress={() => setShowMenu(!showMenu)} className="flex-row items-center">
        <Text className="text-2xl text-background-0">{selectedSchool.name}</Text>
        <Icon as={ChevronDownIcon} size="sm" className="ml-2 mt-1 text-background-0" />
      </Pressable>

      <Modal isOpen={showMenu} onClose={() => setShowMenu(false)}>
        <ModalBackdrop />
        <ModalContent
          style={{
            position: 'absolute',
            top: modalPosition.top,
            left: modalPosition.left,
            margin: 0,
            width: 250,
            backgroundColor: 'transparent',
            borderWidth: 0,
            zIndex: 9999,
          }}
        >
          <Box className="bg-background-0 border border-border-200 rounded-md shadow-md w-full">
            <VStack>
              {schools.map(school => (
                <Pressable
                  key={school.id}
                  className={`p-3 hover:bg-background-50 ${
                    selectedSchool.id === school.id ? 'bg-background-50' : ''
                  }`}
                  onPress={() => handleSelectSchool(school)}
                >
                  <Text>{school.name}</Text>
                </Pressable>
              ))}
              <Pressable
                className="p-3 flex-row items-center border-t border-border-200 hover:bg-background-50"
                onPress={handleAddNewSchool}
              >
                <Icon as={PlusIcon} size="sm" className="mr-2" />
                <Text className="text-primary-600">Add new school</Text>
              </Pressable>
            </VStack>
          </Box>
        </ModalContent>
      </Modal>
    </Box>
  );
}

function WebHeader(props: HeaderProps) {
  return (
    <HStack className="pt-4 pr-10 pb-3 bg-background-primary items-center justify-between border-b border-border-300">
      <HStack className="items-center">
        <Pressable
          onPress={() => {
            props.toggleSidebar();
          }}
        >
          <Icon as={MenuIcon} size="lg" className="mx-5 text-background-0" />
        </Pressable>
        <SchoolSelector onSchoolChange={props.onSchoolChange} />
      </HStack>

      <HStack space="md" className="items-center">
        <LogoutButton displayStyle="button" />
        <Avatar className="h-9 w-9">
          <AvatarFallbackText className="font-light">A</AvatarFallbackText>
        </Avatar>
      </HStack>
    </HStack>
  );
}

function MobileHeader(props: MobileHeaderProps) {
  return (
    <HStack className="py-6 px-4 border-b border-border-50 bg-background-primary items-center justify-between">
      <HStack space="md" className="items-center">
        <Pressable
          onPress={() => {
            router.back();
          }}
        >
          <Icon as={ChevronLeftIcon} className="text-background-0" />
        </Pressable>
        <SchoolSelector onSchoolChange={props.onSchoolChange} />
      </HStack>

      <LogoutButton displayStyle="icon-only" />
    </HStack>
  );
}

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
  const { userProfile } = useAuth();
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

export const Dashboard = () => {
  const { userProfile } = useAuth();
  const [selectedSchool, setSelectedSchool] = useState<School>(schools[0]);

  const handleSchoolChange = (school: School) => {
    setSelectedSchool(school);
    // Here you would typically fetch data for the selected school
  };

  return (
    <SafeAreaView className="h-full w-full">
      <DashboardLayout
        title={selectedSchool.name}
        isSidebarVisible={true}
        onSchoolChange={handleSchoolChange}
      >
        <MainContent />
      </DashboardLayout>
      <MobileFooter footerIcons={bottomTabsList} />
    </SafeAreaView>
  );
};

// Export components for reuse in other dashboards
export { DashboardLayout, MobileFooter, bottomTabsList, School, schools };
