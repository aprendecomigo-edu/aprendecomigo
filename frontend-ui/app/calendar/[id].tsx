import { useLocalSearchParams, router } from 'expo-router';
import { Calendar, Clock, User, MapPin, BookOpen } from 'lucide-react-native';
import React, { useState, useEffect, useCallback } from 'react';
import { Alert } from 'react-native';

import { useAuth } from '@/api/authContext';
import schedulerApi, { ClassSchedule } from '@/api/schedulerApi';
import MainLayout from '@/components/layouts/MainLayout';
import { Badge, BadgeText } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Center } from '@/components/ui/center';
import { Divider } from '@/components/ui/divider';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { ScrollView } from '@/components/ui/scroll-view';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

// Helper function to get status color
const getStatusColor = (status: string): string => {
  switch (status) {
    case 'scheduled':
      return 'bg-blue-100 text-blue-800';
    case 'confirmed':
      return 'bg-green-100 text-green-800';
    case 'completed':
      return 'bg-gray-100 text-gray-800';
    case 'cancelled':
      return 'bg-red-100 text-red-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
};

const ClassDetailScreen: React.FC = () => {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { userProfile } = useAuth();
  const [classSchedule, setClassSchedule] = useState<ClassSchedule | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);

  const isTeacher = userProfile?.user_type === 'teacher';
  const isAdmin = userProfile?.is_admin;

  const loadClassDetails = useCallback(async () => {
    try {
      setLoading(true);
      const data = await schedulerApi.getClassSchedule(parseInt(id!));
      setClassSchedule(data);
    } catch (error) {
      console.error('Error loading class details:', error);
      Alert.alert('Error', 'Failed to load class details');
      router.back();
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    if (id) {
      loadClassDetails();
    }
  }, [id, loadClassDetails]);

  const handleCancel = async () => {
    if (!classSchedule) return;

    Alert.alert(
      'Cancel Class',
      'Are you sure you want to cancel this class? This action cannot be undone.',
      [
        { text: 'No', style: 'cancel' },
        {
          text: 'Yes, Cancel',
          style: 'destructive',
          onPress: async () => {
            try {
              setActionLoading(true);
              await schedulerApi.cancelClassSchedule(classSchedule.id);
              Alert.alert('Success', 'Class cancelled successfully');
              router.back();
            } catch (error) {
              console.error('Error cancelling class:', error);
              Alert.alert('Error', 'Failed to cancel class');
            } finally {
              setActionLoading(false);
            }
          },
        },
      ]
    );
  };

  const handleConfirm = async () => {
    if (!classSchedule) return;

    try {
      setActionLoading(true);
      await schedulerApi.confirmClassSchedule(classSchedule.id);
      Alert.alert('Success', 'Class confirmed successfully');
      loadClassDetails(); // Refresh the data
    } catch (error) {
      console.error('Error confirming class:', error);
      Alert.alert('Error', 'Failed to confirm class');
    } finally {
      setActionLoading(false);
    }
  };

  const handleComplete = async () => {
    if (!classSchedule) return;

    try {
      setActionLoading(true);
      await schedulerApi.completeClassSchedule(classSchedule.id);
      Alert.alert('Success', 'Class marked as completed');
      loadClassDetails(); // Refresh the data
    } catch (error) {
      console.error('Error completing class:', error);
      Alert.alert('Error', 'Failed to complete class');
    } finally {
      setActionLoading(false);
    }
  };

  const canCancel =
    classSchedule &&
    ['scheduled', 'confirmed'].includes(classSchedule.status) &&
    (isAdmin || (isTeacher && classSchedule.teacher_id === userProfile?.id));

  const canConfirm =
    classSchedule &&
    classSchedule.status === 'scheduled' &&
    (isAdmin || (isTeacher && classSchedule.teacher_id === userProfile?.id));

  const canComplete =
    classSchedule &&
    classSchedule.status === 'confirmed' &&
    (isAdmin || (isTeacher && classSchedule.teacher_id === userProfile?.id));

  if (loading) {
    return (
      <MainLayout _title="Class Details">
        <Center className="flex-1">
          <Spinner size="large" />
          <Text className="mt-4 text-gray-600">Loading class details...</Text>
        </Center>
      </MainLayout>
    );
  }

  if (!classSchedule) {
    return (
      <MainLayout _title="Class Details">
        <Center className="flex-1">
          <Text className="text-gray-600">Class not found</Text>
          <Button className="mt-4" onPress={() => router.back()}>
            <ButtonText>Go Back</ButtonText>
          </Button>
        </Center>
      </MainLayout>
    );
  }

  return (
    <MainLayout _title="Class Details">
      <ScrollView>
        <VStack className="flex-1 p-4" space="lg">
          {/* Header */}
          <VStack space="md">
            <HStack className="justify-between items-start">
              <VStack className="flex-1">
                <Heading className="text-2xl font-bold">{classSchedule.title}</Heading>
                <Text className="text-gray-600 mt-1">{classSchedule.class_type_display}</Text>
              </VStack>
              <Badge className={getStatusColor(classSchedule.status)}>
                <BadgeText>{classSchedule.status_display}</BadgeText>
              </Badge>
            </HStack>
          </VStack>

          {/* Class Information */}
          <Box className="bg-white rounded-lg border border-gray-200 p-4">
            <VStack space="md">
              <Text className="font-bold text-lg">Class Information</Text>

              <VStack space="sm">
                <HStack space="sm" className="items-center">
                  <Icon as={Calendar} size="sm" className="text-gray-500" />
                  <Text className="font-medium">Date:</Text>
                  <Text>{classSchedule.scheduled_date}</Text>
                </HStack>

                <HStack space="sm" className="items-center">
                  <Icon as={Clock} size="sm" className="text-gray-500" />
                  <Text className="font-medium">Time:</Text>
                  <Text>
                    {classSchedule.start_time} - {classSchedule.end_time}
                  </Text>
                </HStack>

                <HStack space="sm" className="items-center">
                  <Icon as={MapPin} size="sm" className="text-gray-500" />
                  <Text className="font-medium">School:</Text>
                  <Text>{classSchedule.school_name}</Text>
                </HStack>

                <HStack space="sm" className="items-center">
                  <Icon as={BookOpen} size="sm" className="text-gray-500" />
                  <Text className="font-medium">Duration:</Text>
                  <Text>{classSchedule.duration_minutes} minutes</Text>
                </HStack>
              </VStack>
            </VStack>
          </Box>

          {/* Participants */}
          <Box className="bg-white rounded-lg border border-gray-200 p-4">
            <VStack space="md">
              <Text className="font-bold text-lg">Participants</Text>

              <VStack space="sm">
                <HStack space="sm" className="items-center">
                  <Icon as={User} size="sm" className="text-blue-500" />
                  <Text className="font-medium">Teacher:</Text>
                  <Text>{classSchedule.teacher_name}</Text>
                </HStack>

                <HStack space="sm" className="items-center">
                  <Icon as={User} size="sm" className="text-green-500" />
                  <Text className="font-medium">Student:</Text>
                  <Text>{classSchedule.student_name}</Text>
                </HStack>

                {classSchedule.additional_students_names.length > 0 && (
                  <HStack space="sm" className="items-center">
                    <Icon as={User} size="sm" className="text-purple-500" />
                    <Text className="font-medium">Additional Students:</Text>
                    <Text>{classSchedule.additional_students_names.join(', ')}</Text>
                  </HStack>
                )}
              </VStack>
            </VStack>
          </Box>

          {/* Description */}
          {classSchedule.description && (
            <Box className="bg-white rounded-lg border border-gray-200 p-4">
              <VStack space="md">
                <Text className="font-bold text-lg">Description</Text>
                <Text className="text-gray-700">{classSchedule.description}</Text>
              </VStack>
            </Box>
          )}

          {/* Actions */}
          <VStack space="md">
            <Divider />
            <Text className="font-bold text-lg">Actions</Text>

            <VStack space="sm">
              {canConfirm && (
                <Button className="bg-green-600" onPress={handleConfirm} disabled={actionLoading}>
                  {actionLoading && <Spinner size="small" color="white" className="mr-2" />}
                  <ButtonText>Confirm Class</ButtonText>
                </Button>
              )}

              {canComplete && (
                <Button className="bg-blue-600" onPress={handleComplete} disabled={actionLoading}>
                  {actionLoading && <Spinner size="small" color="white" className="mr-2" />}
                  <ButtonText>Mark as Completed</ButtonText>
                </Button>
              )}

              {canCancel && (
                <Button className="bg-red-600" onPress={handleCancel} disabled={actionLoading}>
                  {actionLoading && <Spinner size="small" color="white" className="mr-2" />}
                  <ButtonText>Cancel Class</ButtonText>
                </Button>
              )}

              <Button variant="outline" onPress={() => router.back()}>
                <ButtonText>Go Back</ButtonText>
              </Button>
            </VStack>
          </VStack>
        </VStack>
      </ScrollView>
    </MainLayout>
  );
};

export default ClassDetailScreen;
