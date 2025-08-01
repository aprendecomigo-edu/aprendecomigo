import React, { useState } from 'react';
import { Alert } from 'react-native';
import { Box } from '@/components/ui/box';
import { VStack } from '@/components/ui/vstack';
import { HStack } from '@/components/ui/hstack';
import { Text } from '@/components/ui/text';
import { Heading } from '@/components/ui/heading';
import { Input, InputField } from '@/components/ui/input';
import { Textarea, TextareaInput } from '@/components/ui/textarea';
import { Button, ButtonText } from '@/components/ui/button';
import { FormControl } from '@/components/ui/form-control';
import { Select, SelectTrigger, SelectInput, SelectIcon, SelectPortal, SelectBackdrop, SelectContent, SelectDragIndicatorWrapper, SelectDragIndicator, SelectItem } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Icon } from '@/components/ui/icon';
import { Clock, Calendar, Globe, ChevronDownIcon } from 'lucide-react-native';

import { TeacherProfileData, WeeklySchedule, TimeSlot } from '@/api/invitationApi';
import { TIMEZONE_OPTIONS } from '@/hooks/useInvitationProfileWizard';

interface AvailabilityStepProps {
  profileData: TeacherProfileData;
  updateProfileData: (updates: Partial<TeacherProfileData>) => void;
  validationErrors: { [key: string]: string };
  invitationData: any;
}

const AvailabilityStep: React.FC<AvailabilityStepProps> = ({
  profileData,
  updateProfileData,
  validationErrors,
  invitationData,
}) => {
  const [showDetailedSchedule, setShowDetailedSchedule] = useState(false);

  const weekDays = [
    { key: 'monday', label: 'Segunda-feira' },
    { key: 'tuesday', label: 'Terça-feira' },
    { key: 'wednesday', label: 'Quarta-feira' },
    { key: 'thursday', label: 'Quinta-feira' },
    { key: 'friday', label: 'Sexta-feira' },
    { key: 'saturday', label: 'Sábado' },
    { key: 'sunday', label: 'Domingo' },
  ];

  const timeSlots = [
    { label: 'Manhã (6h-12h)', value: 'morning' },
    { label: 'Tarde (12h-18h)', value: 'afternoon' },
    { label: 'Noite (18h-22h)', value: 'evening' },
  ];

  const getDefaultSchedule = (): WeeklySchedule => ({
    monday: [],
    tuesday: [],
    wednesday: [],
    thursday: [],
    friday: [],
    saturday: [],
    sunday: [],
  });

  const currentSchedule = profileData.availability_schedule || getDefaultSchedule();

  const updateSchedule = (schedule: WeeklySchedule) => {
    updateProfileData({ availability_schedule: schedule });
  };

  const toggleTimeSlot = (day: keyof WeeklySchedule, period: string) => {
    const updatedSchedule = { ...currentSchedule };
    const daySchedule = [...(updatedSchedule[day] || [])];
    
    let timeSlot: TimeSlot;
    switch (period) {
      case 'morning':
        timeSlot = { start_time: '06:00', end_time: '12:00', available: true };
        break;
      case 'afternoon':
        timeSlot = { start_time: '12:00', end_time: '18:00', available: true };
        break;
      case 'evening':
        timeSlot = { start_time: '18:00', end_time: '22:00', available: true };
        break;
      default:
        return;
    }

    const existingIndex = daySchedule.findIndex(slot => 
      slot.start_time === timeSlot.start_time && slot.end_time === timeSlot.end_time
    );

    if (existingIndex > -1) {
      // Remove if already exists
      daySchedule.splice(existingIndex, 1);
    } else {
      // Add if doesn't exist
      daySchedule.push(timeSlot);
    }

    updatedSchedule[day] = daySchedule;
    updateSchedule(updatedSchedule);
  };

  const isTimeSlotSelected = (day: keyof WeeklySchedule, period: string): boolean => {
    const daySchedule = currentSchedule[day] || [];
    
    let targetSlot: { start_time: string; end_time: string };
    switch (period) {
      case 'morning':
        targetSlot = { start_time: '06:00', end_time: '12:00' };
        break;
      case 'afternoon':
        targetSlot = { start_time: '12:00', end_time: '18:00' };
        break;
      case 'evening':
        targetSlot = { start_time: '18:00', end_time: '22:00' };
        break;
      default:
        return false;
    }

    return daySchedule.some(slot => 
      slot.start_time === targetSlot.start_time && slot.end_time === targetSlot.end_time
    );
  };

  const quickSetAvailability = (type: 'weekdays' | 'weekend' | 'fulltime') => {
    const newSchedule = getDefaultSchedule();
    
    const allPeriods: TimeSlot[] = [
      { start_time: '06:00', end_time: '12:00', available: true },
      { start_time: '12:00', end_time: '18:00', available: true },
      { start_time: '18:00', end_time: '22:00', available: true },
    ];

    const weekdayPeriods: TimeSlot[] = [
      { start_time: '18:00', end_time: '22:00', available: true }, // Evening only
    ];

    switch (type) {
      case 'weekdays':
        ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'].forEach(day => {
          newSchedule[day as keyof WeeklySchedule] = [...weekdayPeriods];
        });
        break;
      case 'weekend':
        ['saturday', 'sunday'].forEach(day => {
          newSchedule[day as keyof WeeklySchedule] = [...allPeriods];
        });
        break;
      case 'fulltime':
        Object.keys(newSchedule).forEach(day => {
          newSchedule[day as keyof WeeklySchedule] = [...allPeriods];
        });
        break;
    }

    updateSchedule(newSchedule);
  };

  const getTotalAvailableHours = (): number => {
    let totalHours = 0;
    Object.values(currentSchedule).forEach(daySlots => {
      daySlots.forEach(slot => {
        const start = parseInt(slot.start_time.split(':')[0]);
        const end = parseInt(slot.end_time.split(':')[0]);
        totalHours += end - start;
      });
    });
    return totalHours;
  };

  return (
    <Box className="flex-1">
      <VStack space="lg">
        {/* Header */}
        <VStack space="sm">
          <Heading size="xl" className="text-gray-900">
            Disponibilidade
          </Heading>
          <Text className="text-gray-600">
            Configure quando você está disponível para dar aulas. Você poderá ajustar isso depois.
          </Text>
        </VStack>

        {/* Timezone Selection */}
        <FormControl className={validationErrors.timezone ? 'error' : ''}>
          <VStack space="sm">
            <HStack className="items-center" space="sm">
              <Icon as={Globe} size="sm" className="text-gray-600" />
              <Text className="font-medium">Fuso Horário *</Text>
            </HStack>
            <Select
              selectedValue={profileData.timezone}
              onValueChange={(value) => updateProfileData({ timezone: value })}
            >
              <SelectTrigger variant="outline" size="md">
                <SelectInput placeholder="Selecione seu fuso horário" />
                <SelectIcon className="mr-3" as={ChevronDownIcon} />
              </SelectTrigger>
              <SelectPortal>
                <SelectBackdrop />
                <SelectContent>
                  <SelectDragIndicatorWrapper>
                    <SelectDragIndicator />
                  </SelectDragIndicatorWrapper>
                  {TIMEZONE_OPTIONS.map((option) => (
                    <SelectItem
                      key={option.value}
                      label={option.label}
                      value={option.value}
                    />
                  ))}
                </SelectContent>
              </SelectPortal>
            </Select>
            {validationErrors.timezone && (
              <Text className="text-red-600 text-sm">
                {validationErrors.timezone}
              </Text>
            )}
          </VStack>
        </FormControl>

        {/* Quick Setup Options */}
        <VStack space="sm">
          <Text className="font-medium">Configuração Rápida</Text>
          <HStack space="sm" className="flex-wrap">
            <Button variant="outline" size="sm" onPress={() => quickSetAvailability('weekdays')}>
              <ButtonText>Noites da Semana</ButtonText>
            </Button>
            <Button variant="outline" size="sm" onPress={() => quickSetAvailability('weekend')}>
              <ButtonText>Fins de Semana</ButtonText>
            </Button>
            <Button variant="outline" size="sm" onPress={() => quickSetAvailability('fulltime')}>
              <ButtonText>Tempo Integral</ButtonText>
            </Button>
          </HStack>
        </VStack>

        {/* Detailed Schedule Toggle */}
        <HStack className="justify-between items-center">
          <VStack>
            <Text className="font-medium">Horário Detalhado</Text>
            <Text className="text-sm text-gray-600">
              Configure horários específicos por dia
            </Text>
          </VStack>
          <Switch
            value={showDetailedSchedule}
            onValueChange={setShowDetailedSchedule}
          />
        </HStack>

        {/* Schedule Grid */}
        {showDetailedSchedule && (
          <VStack space="md">
            <Text className="font-medium">Selecione seus horários disponíveis:</Text>
            
            <Box className="bg-white border border-gray-200 rounded-lg p-4">
              {/* Header */}
              <HStack className="mb-3">
                <Box className="w-32">
                  <Text className="font-medium text-sm">Dia da Semana</Text>
                </Box>
                {timeSlots.map((slot) => (
                  <Box key={slot.value} className="flex-1 items-center">
                    <Text className="font-medium text-xs text-center">
                      {slot.label}
                    </Text>
                  </Box>
                ))}
              </HStack>

              {/* Schedule Grid */}
              <VStack space="sm">
                {weekDays.map((day) => (
                  <HStack key={day.key} className="items-center">
                    <Box className="w-32">
                      <Text className="text-sm">{day.label}</Text>
                    </Box>
                    {timeSlots.map((slot) => (
                      <Box key={slot.value} className="flex-1 items-center">
                        <Button
                          variant={isTimeSlotSelected(day.key as keyof WeeklySchedule, slot.value) ? 'solid' : 'outline'}
                          size="sm"
                          onPress={() => toggleTimeSlot(day.key as keyof WeeklySchedule, slot.value)}
                          className={`w-16 ${
                            isTimeSlotSelected(day.key as keyof WeeklySchedule, slot.value)
                              ? 'bg-green-500'
                              : ''
                          }`}
                        >
                          <ButtonText className="text-xs">
                            {isTimeSlotSelected(day.key as keyof WeeklySchedule, slot.value) ? '✓' : '-'}
                          </ButtonText>
                        </Button>
                      </Box>
                    ))}
                  </HStack>
                ))}
              </VStack>
            </Box>
          </VStack>
        )}

        {/* Availability Summary */}
        {getTotalAvailableHours() > 0 && (
          <Box className="bg-green-50 p-4 rounded-lg border border-green-200">
            <VStack space="sm">
              <HStack className="items-center" space="sm">
                <Icon as={Clock} size="sm" className="text-green-600" />
                <Text className="font-medium text-green-800">
                  Total Disponível: {getTotalAvailableHours()} horas por semana
                </Text>
              </HStack>
              <Text className="text-sm text-green-700">
                Ótimo! Você tem uma boa disponibilidade para atender diferentes necessidades de alunos.
              </Text>
            </VStack>
          </Box>
        )}

        {/* Availability Notes */}
        <FormControl>
          <VStack space="sm">
            <Text className="font-medium">Observações sobre Disponibilidade (opcional)</Text>
            <Text className="text-sm text-gray-600">
              Adicione informações extras sobre sua disponibilidade, preferências de horário, ou flexibilidade.
            </Text>
            <Textarea className="min-h-[80px]">
              <TextareaInput
                placeholder="Ex: Posso ser flexível com horários em emergências, prefiro não dar aulas muito cedo de manhã nos finais de semana..."
                value={profileData.availability_notes || ''}
                onChangeText={(value) => updateProfileData({ availability_notes: value })}
                multiline
                textAlignVertical="top"
              />
            </Textarea>
          </VStack>
        </FormControl>

        {/* Help Text */}
        <Box className="bg-blue-50 p-4 rounded-lg border border-blue-200">
          <VStack space="sm">
            <Text className="font-medium text-blue-800">Dicas:</Text>
            <VStack space="xs" className="ml-2">
              <Text className="text-sm text-blue-700">
                • Você pode alterar sua disponibilidade a qualquer momento no dashboard
              </Text>
              <Text className="text-sm text-blue-700">
                • Considere os horários quando seus alunos-alvo estão livres
              </Text>
              <Text className="text-sm text-blue-700">
                • Mantenha alguma flexibilidade para acomodar diferentes fusos horários
              </Text>
              <Text className="text-sm text-blue-700">
                • Lembre-se de reservar tempo para preparação de aulas
              </Text>
            </VStack>
          </VStack>
        </Box>
      </VStack>
    </Box>
  );
};

export default AvailabilityStep;