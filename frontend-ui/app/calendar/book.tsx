import { router } from 'expo-router';
import { Calendar, Clock, User, ChevronDown } from 'lucide-react-native';
import React, { useState, useEffect, useCallback } from 'react';
import { Alert } from 'react-native';

import { useAuth } from '@/api/authContext';
import schedulerApi, { CreateClassScheduleData, AvailableTimeSlot } from '@/api/schedulerApi';
import { getTeachers, TeacherProfile } from '@/api/userApi';
import MainLayout from '@/components/layouts/main-layout';
import { Badge, BadgeText } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import {
  FormControl,
  FormControlLabel,
  FormControlLabelText,
  FormControlError,
  FormControlErrorText,
} from '@/components/ui/form-control';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Input, InputField } from '@/components/ui/input';
import { Pressable } from '@/components/ui/pressable';
import { ScrollView } from '@/components/ui/scroll-view';
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
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { Textarea, TextareaInput } from '@/components/ui/textarea';
import { VStack } from '@/components/ui/vstack';

// Form data interface
interface BookingFormData {
  teacher_id: string;
  student_id: string;
  school_id: string;
  title: string;
  description: string;
  class_type: 'individual' | 'group' | 'trial';
  scheduled_date: string;
  start_time: string;
  end_time: string;
  duration_minutes: string;
}

// Initial form state
const initialFormData: BookingFormData = {
  teacher_id: '',
  student_id: '',
  school_id: '',
  title: '',
  description: '',
  class_type: 'individual',
  scheduled_date: '',
  start_time: '',
  end_time: '',
  duration_minutes: '60',
};

// Helper function to format date for input
const formatDateForInput = (date: Date): string => {
  return date.toISOString().split('T')[0];
};

// Helper function to get next 30 days
const getNext30Days = (): Array<{ value: string; label: string }> => {
  const days = [];
  const today = new Date();

  for (let i = 0; i < 30; i++) {
    const date = new Date(today);
    date.setDate(today.getDate() + i);

    days.push({
      value: formatDateForInput(date),
      label: date.toLocaleDateString('pt-PT', {
        weekday: 'long',
        day: 'numeric',
        month: 'long',
      }),
    });
  }

  return days;
};

const BookClassScreen: React.FC = () => {
  const { userProfile } = useAuth();
  const [formData, setFormData] = useState<BookingFormData>(initialFormData);
  const [teachers, setTeachers] = useState<TeacherProfile[]>([]);
  const [availableSlots, setAvailableSlots] = useState<AvailableTimeSlot[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [errors, setErrors] = useState<Partial<BookingFormData>>({});

  const isAdmin = userProfile?.is_admin;

  const loadTeachers = useCallback(async () => {
    try {
      const data = await getTeachers();
      setTeachers(data);
    } catch (error) {
      console.error('Error loading teachers:', error);
      Alert.alert('Error', 'Failed to load teachers');
    }
  }, []);

  const loadAvailableSlots = useCallback(async () => {
    if (!formData.teacher_id || !formData.scheduled_date) return;

    try {
      setLoadingSlots(true);
      const response = await schedulerApi.getAvailableTimeSlots(
        parseInt(formData.teacher_id),
        formData.scheduled_date
      );
      setAvailableSlots(response.available_slots);
    } catch (error) {
      console.error('Error loading available slots:', error);
      setAvailableSlots([]);
    } finally {
      setLoadingSlots(false);
    }
  }, [formData.teacher_id, formData.scheduled_date]);

  // Load teachers on component mount
  useEffect(() => {
    loadTeachers();

    // Set student_id to current user if not admin
    if (!isAdmin && userProfile?.id) {
      setFormData(prev => ({
        ...prev,
        student_id: userProfile.id.toString(),
      }));
    }
  }, [loadTeachers, isAdmin, userProfile]);

  // Load available slots when teacher and date change
  useEffect(() => {
    loadAvailableSlots();
  }, [loadAvailableSlots]);

  // Update form data
  const updateFormData = (field: keyof BookingFormData, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }));

    // Clear error for this field
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: undefined,
      }));
    }
  };

  // Handle time slot selection
  const selectTimeSlot = (slot: AvailableTimeSlot) => {
    setFormData(prev => ({
      ...prev,
      start_time: slot.start_time,
      end_time: slot.end_time,
      school_id: slot.school_id.toString(),
    }));
  };

  // Validate form
  const validateForm = (): boolean => {
    const newErrors: Partial<BookingFormData> = {};

    if (!formData.teacher_id) newErrors.teacher_id = 'Teacher is required';
    if (!formData.student_id) newErrors.student_id = 'Student is required';
    if (!formData.title) newErrors.title = 'Title is required';
    if (!formData.scheduled_date) newErrors.scheduled_date = 'Date is required';
    if (!formData.start_time) newErrors.start_time = 'Start time is required';
    if (!formData.end_time) newErrors.end_time = 'End time is required';
    if (!formData.duration_minutes) newErrors.duration_minutes = 'Duration is required';

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Submit form
  const handleSubmit = async () => {
    if (!validateForm()) {
      Alert.alert('Validation Error', 'Please fill in all required fields');
      return;
    }

    try {
      setLoading(true);

      const bookingData: CreateClassScheduleData = {
        teacher: parseInt(formData.teacher_id),
        student: parseInt(formData.student_id),
        school: parseInt(formData.school_id),
        title: formData.title,
        description: formData.description,
        class_type: formData.class_type,
        scheduled_date: formData.scheduled_date,
        start_time: formData.start_time,
        end_time: formData.end_time,
        duration_minutes: parseInt(formData.duration_minutes),
      };

      await schedulerApi.createClassSchedule(bookingData);

      Alert.alert('Success', 'Class scheduled successfully!', [
        {
          text: 'OK',
          onPress: () => router.back(),
        },
      ]);
    } catch (error: unknown) {
      console.error('Error booking class:', error);
      const errorMessage = error instanceof Error ? error.message : 'Failed to schedule class';
      Alert.alert('Error', errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const selectedTeacher = teachers.find(t => t.id.toString() === formData.teacher_id);
  const next30Days = getNext30Days();

  return (
    <MainLayout _title="Book Class">
      <ScrollView>
        <VStack className="flex-1 p-4" space="lg">
          <VStack space="md">
            <Heading className="text-2xl font-bold">
              <Text>Book a Class</Text>
            </Heading>
            <Text className="text-gray-600">Schedule a new class with your preferred teacher</Text>
          </VStack>

          <VStack space="md">
            {/* Teacher Selection */}
            <FormControl isInvalid={!!errors.teacher_id}>
              <FormControlLabel>
                <FormControlLabelText>
                  <Text>Teacher *</Text>
                </FormControlLabelText>
              </FormControlLabel>
              <Select
                selectedValue={formData.teacher_id}
                onValueChange={value => updateFormData('teacher_id', value)}
              >
                <SelectTrigger variant="outline" size="md">
                  <SelectInput placeholder="Select a teacher" />
                  <SelectIcon className="mr-3" as={ChevronDown} />
                </SelectTrigger>
                <SelectPortal>
                  <SelectBackdrop />
                  <SelectContent>
                    <SelectDragIndicatorWrapper>
                      <SelectDragIndicator />
                    </SelectDragIndicatorWrapper>
                    {teachers.map(teacher => (
                      <SelectItem
                        key={teacher.id}
                        label={`${teacher.user.name} - ${teacher.specialty}`}
                        value={teacher.id.toString()}
                      />
                    ))}
                  </SelectContent>
                </SelectPortal>
              </Select>
              {errors.teacher_id && (
                <FormControlError>
                  <FormControlErrorText>{errors.teacher_id}</FormControlErrorText>
                </FormControlError>
              )}
            </FormControl>

            {/* Student Selection (for admins only) */}
            {isAdmin && (
              <FormControl isInvalid={!!errors.student_id}>
                <FormControlLabel>
                  <FormControlLabelText>
                    <Text>Student *</Text>
                  </FormControlLabelText>
                </FormControlLabel>
                <Input>
                  <InputField
                    placeholder="Student ID"
                    value={formData.student_id}
                    onChangeText={value => updateFormData('student_id', value)}
                    keyboardType="numeric"
                  />
                </Input>
                {errors.student_id && (
                  <FormControlError>
                    <FormControlErrorText>{errors.student_id}</FormControlErrorText>
                  </FormControlError>
                )}
              </FormControl>
            )}

            {/* Class Title */}
            <FormControl isInvalid={!!errors.title}>
              <FormControlLabel>
                <FormControlLabelText>
                  <Text>Class Title *</Text>
                </FormControlLabelText>
              </FormControlLabel>
              <Input>
                <InputField
                  placeholder="e.g., Math Tutoring"
                  value={formData.title}
                  onChangeText={value => updateFormData('title', value)}
                />
              </Input>
              {errors.title && (
                <FormControlError>
                  <FormControlErrorText>{errors.title}</FormControlErrorText>
                </FormControlError>
              )}
            </FormControl>

            {/* Class Type */}
            <FormControl>
              <FormControlLabel>
                <FormControlLabelText>
                  <Text>Class Type</Text>
                </FormControlLabelText>
              </FormControlLabel>
              <Select
                selectedValue={formData.class_type}
                onValueChange={value =>
                  updateFormData('class_type', value as 'individual' | 'group' | 'trial')
                }
              >
                <SelectTrigger variant="outline" size="md">
                  <SelectInput placeholder="Select class type" />
                  <SelectIcon className="mr-3" as={ChevronDown} />
                </SelectTrigger>
                <SelectPortal>
                  <SelectBackdrop />
                  <SelectContent>
                    <SelectDragIndicatorWrapper>
                      <SelectDragIndicator />
                    </SelectDragIndicatorWrapper>
                    <SelectItem label="Individual" value="individual" />
                    <SelectItem label="Group" value="group" />
                    <SelectItem label="Trial" value="trial" />
                  </SelectContent>
                </SelectPortal>
              </Select>
            </FormControl>

            {/* Date Selection */}
            <FormControl isInvalid={!!errors.scheduled_date}>
              <FormControlLabel>
                <FormControlLabelText>
                  <Text>Date *</Text>
                </FormControlLabelText>
              </FormControlLabel>
              <Select
                selectedValue={formData.scheduled_date}
                onValueChange={value => updateFormData('scheduled_date', value)}
              >
                <SelectTrigger variant="outline" size="md">
                  <SelectInput placeholder="Select a date" />
                  <SelectIcon className="mr-3" as={Calendar} />
                </SelectTrigger>
                <SelectPortal>
                  <SelectBackdrop />
                  <SelectContent>
                    <SelectDragIndicatorWrapper>
                      <SelectDragIndicator />
                    </SelectDragIndicatorWrapper>
                    {next30Days.map(day => (
                      <SelectItem key={day.value} label={day.label} value={day.value} />
                    ))}
                  </SelectContent>
                </SelectPortal>
              </Select>
              {errors.scheduled_date && (
                <FormControlError>
                  <FormControlErrorText>{errors.scheduled_date}</FormControlErrorText>
                </FormControlError>
              )}
            </FormControl>

            {/* Available Time Slots */}
            {formData.teacher_id && formData.scheduled_date && (
              <VStack space="sm">
                <Text className="font-medium">Available Time Slots</Text>
                {loadingSlots ? (
                  <Box className="p-4">
                    <Spinner size="small" />
                    <Text className="text-center text-gray-600 mt-2">
                      Loading available times...
                    </Text>
                  </Box>
                ) : availableSlots.length > 0 ? (
                  <VStack space="xs">
                    {availableSlots.map((slot, index) => (
                      <Pressable key={index} onPress={() => selectTimeSlot(slot)}>
                        <Box
                          className={`p-3 rounded-lg border ${
                            formData.start_time === slot.start_time
                              ? 'bg-blue-50 border-blue-300'
                              : 'bg-white border-gray-200'
                          }`}
                        >
                          <HStack className="justify-between items-center">
                            <HStack space="sm" className="items-center">
                              <Icon as={Clock} size="sm" className="text-gray-500" />
                              <Text className="font-medium">
                                {slot.start_time} - {slot.end_time}
                              </Text>
                            </HStack>
                            <Badge>
                              <BadgeText>{slot.school_name}</BadgeText>
                            </Badge>
                          </HStack>
                        </Box>
                      </Pressable>
                    ))}
                  </VStack>
                ) : (
                  <Box className="bg-gray-50 rounded-lg p-4">
                    <Text className="text-center text-gray-600">
                      No available time slots for this date
                    </Text>
                  </Box>
                )}
              </VStack>
            )}

            {/* Duration */}
            <FormControl isInvalid={!!errors.duration_minutes}>
              <FormControlLabel>
                <FormControlLabelText>
                  <Text>Duration (minutes) *</Text>
                </FormControlLabelText>
              </FormControlLabel>
              <Select
                selectedValue={formData.duration_minutes}
                onValueChange={value => updateFormData('duration_minutes', value)}
              >
                <SelectTrigger variant="outline" size="md">
                  <SelectInput placeholder="Select duration" />
                  <SelectIcon className="mr-3" as={ChevronDown} />
                </SelectTrigger>
                <SelectPortal>
                  <SelectBackdrop />
                  <SelectContent>
                    <SelectDragIndicatorWrapper>
                      <SelectDragIndicator />
                    </SelectDragIndicatorWrapper>
                    <SelectItem label="30 minutes" value="30" />
                    <SelectItem label="45 minutes" value="45" />
                    <SelectItem label="60 minutes" value="60" />
                    <SelectItem label="90 minutes" value="90" />
                    <SelectItem label="120 minutes" value="120" />
                  </SelectContent>
                </SelectPortal>
              </Select>
              {errors.duration_minutes && (
                <FormControlError>
                  <FormControlErrorText>{errors.duration_minutes}</FormControlErrorText>
                </FormControlError>
              )}
            </FormControl>

            {/* Description */}
            <FormControl>
              <FormControlLabel>
                <FormControlLabelText>
                  <Text>Description</Text>
                </FormControlLabelText>
              </FormControlLabel>
              <Textarea>
                <TextareaInput
                  placeholder="Additional notes or special requirements..."
                  value={formData.description}
                  onChangeText={value => updateFormData('description', value)}
                />
              </Textarea>
            </FormControl>

            {/* Selected teacher info */}
            {selectedTeacher && (
              <Box className="bg-blue-50 rounded-lg p-4">
                <VStack space="sm">
                  <Text className="font-medium">Selected Teacher</Text>
                  <HStack space="sm" className="items-center">
                    <Icon as={User} size="sm" className="text-blue-600" />
                    <VStack className="flex-1">
                      <Text className="font-medium">{selectedTeacher.user.name}</Text>
                      <Text className="text-sm text-gray-600">{selectedTeacher.specialty}</Text>
                      <Text className="text-sm text-gray-600">
                        €{selectedTeacher.hourly_rate}/hour
                      </Text>
                    </VStack>
                  </HStack>
                </VStack>
              </Box>
            )}
          </VStack>

          {/* Submit Button */}
          <VStack space="md">
            <Button size="lg" onPress={handleSubmit} disabled={loading} className="w-full">
              {loading && <Spinner size="small" color="white" className="mr-2" />}
              <ButtonText>{loading ? 'Booking...' : 'Book Class'}</ButtonText>
            </Button>

            <Button variant="outline" size="lg" onPress={() => router.back()}>
              <ButtonText>Cancel</ButtonText>
            </Button>
          </VStack>
        </VStack>
      </ScrollView>
    </MainLayout>
  );
};

export default BookClassScreen;
