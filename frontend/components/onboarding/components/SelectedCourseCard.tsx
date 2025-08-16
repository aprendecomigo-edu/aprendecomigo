import { ChevronDown, ChevronUp, Star, Trash2, GripVertical, Info } from 'lucide-react-native';
import React, { useState } from 'react';
import { Platform } from 'react-native';

import { SelectedCourse, CustomSubject } from '../hooks/useCourseManager';

import { ExpertiseLevelBadge } from './ExpertiseLevelBadge';
import { RateInputField } from './RateInputField';

import {
  AlertDialog,
  AlertDialogBackdrop,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogBody,
  AlertDialogFooter,
} from '@/components/ui/alert-dialog';
import { Badge, BadgeText } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { FormControl, FormControlLabel, FormControlLabelText } from '@/components/ui/form-control';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Pressable } from '@/components/ui/pressable';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

interface SelectedCourseCardProps {
  item: SelectedCourse | CustomSubject;
  index: number;
  onUpdate: (updates: Partial<SelectedCourse | CustomSubject>) => void;
  onRemove: () => void;
  currency: string;
  isDragDisabled?: boolean;
}

export const SelectedCourseCard: React.FC<SelectedCourseCardProps> = ({
  item,
  index,
  onUpdate,
  onRemove,
  currency,
  isDragDisabled,
}) => {
  const [expanded, setExpanded] = useState(false);
  const [showRemoveDialog, setShowRemoveDialog] = useState(false);

  const isCustomSubject = 'subject_area' in item && !('course' in item);
  const course = isCustomSubject ? null : (item as SelectedCourse).course;
  const name = isCustomSubject ? item.name : course?.name || '';
  const description = isCustomSubject ? item.description : course?.description || '';

  return (
    <>
      <Card
        className={`
          border transition-all duration-200 mb-3
          ${
            item.is_featured
              ? 'ring-2 ring-blue-200 border-blue-300'
              : 'border-gray-200 hover:border-gray-300'
          }
        `}
      >
        <CardHeader className="pb-3">
          <HStack className="items-start justify-between">
            <HStack space="sm" className="items-start flex-1">
              {/* Drag Handle */}
              {!isDragDisabled && Platform.OS === 'web' && (
                <Box className="mt-1 p-1 hover:bg-gray-100 rounded cursor-grab active:cursor-grabbing">
                  <Icon as={GripVertical} className="text-gray-400" size="sm" />
                </Box>
              )}

              <VStack className="flex-1" space="xs">
                <HStack className="items-start justify-between">
                  <VStack space="xs" className="flex-1">
                    <HStack space="sm" className="items-center">
                      <Heading size="sm" className="text-gray-900 flex-1">
                        {name}
                      </Heading>

                      {item.is_featured && (
                        <Badge className="bg-yellow-100">
                          <HStack space="xs" className="items-center">
                            <Icon as={Star} className="text-yellow-600" size="xs" />
                            <BadgeText className="text-yellow-700 text-xs">Featured</BadgeText>
                          </HStack>
                        </Badge>
                      )}
                    </HStack>

                    {!isCustomSubject && course && (
                      <HStack space="xs" className="flex-wrap">
                        <Badge className="bg-blue-100">
                          <BadgeText className="text-blue-700 text-xs">
                            {course.education_level}
                          </BadgeText>
                        </Badge>

                        {course.subject_area && (
                          <Badge className="bg-green-100">
                            <BadgeText className="text-green-700 text-xs">
                              {course.subject_area}
                            </BadgeText>
                          </Badge>
                        )}
                      </HStack>
                    )}

                    {isCustomSubject && (
                      <HStack space="xs" className="flex-wrap">
                        <Badge className="bg-purple-100">
                          <BadgeText className="text-purple-700 text-xs">Custom</BadgeText>
                        </Badge>

                        <Badge className="bg-green-100">
                          <BadgeText className="text-green-700 text-xs">
                            {(item as CustomSubject).subject_area}
                          </BadgeText>
                        </Badge>
                      </HStack>
                    )}
                  </VStack>
                </HStack>

                <HStack className="items-center justify-between">
                  <HStack space="sm" className="items-center">
                    <Text className="text-gray-600 text-sm font-medium">
                      {item.hourly_rate}
                      {currency}/hour
                    </Text>

                    {!isCustomSubject && (
                      <ExpertiseLevelBadge level={(item as SelectedCourse).expertise_level} />
                    )}
                  </HStack>

                  <HStack space="xs">
                    <Pressable
                      onPress={() => setExpanded(!expanded)}
                      className="p-1 hover:bg-gray-100 rounded"
                      accessibilityLabel={expanded ? 'Collapse' : 'Expand'}
                    >
                      <Icon
                        as={expanded ? ChevronUp : ChevronDown}
                        className="text-gray-500"
                        size="sm"
                      />
                    </Pressable>

                    <Pressable
                      onPress={() => setShowRemoveDialog(true)}
                      className="p-1 hover:bg-red-100 rounded"
                      accessibilityLabel="Remove course"
                    >
                      <Icon as={Trash2} className="text-red-500" size="sm" />
                    </Pressable>
                  </HStack>
                </HStack>
              </VStack>
            </HStack>
          </HStack>
        </CardHeader>

        {expanded && (
          <CardContent className="pt-0">
            <VStack space="md">
              {description && (
                <Text className="text-gray-600 text-sm leading-relaxed">{description}</Text>
              )}

              <VStack space="sm">
                <Heading size="xs" className="text-gray-700">
                  Configuration
                </Heading>

                <HStack space="md" className="items-start">
                  <VStack space="xs" className="flex-1">
                    <FormControl>
                      <FormControlLabel>
                        <FormControlLabelText className="text-xs">Hourly Rate</FormControlLabelText>
                      </FormControlLabel>
                      <RateInputField
                        value={item.hourly_rate}
                        onChange={rate => onUpdate({ hourly_rate: rate })}
                        currency={currency}
                        suggestedRate={course?.rate_suggestions}
                      />
                    </FormControl>
                  </VStack>

                  {!isCustomSubject && (
                    <VStack space="xs" className="flex-1">
                      <FormControl>
                        <FormControlLabel>
                          <FormControlLabelText className="text-xs">
                            Expertise Level
                          </FormControlLabelText>
                        </FormControlLabel>
                        <HStack space="xs" className="flex-wrap">
                          {['beginner', 'intermediate', 'advanced', 'expert'].map(level => (
                            <Pressable
                              key={level}
                              onPress={() => onUpdate({ expertise_level: level as any })}
                              className={`px-2 py-1 rounded-md border ${
                                (item as SelectedCourse).expertise_level === level
                                  ? 'border-blue-500 bg-blue-50'
                                  : 'border-gray-200 bg-white'
                              }`}
                            >
                              <Text
                                className={`text-xs capitalize ${
                                  (item as SelectedCourse).expertise_level === level
                                    ? 'text-blue-700'
                                    : 'text-gray-600'
                                }`}
                              >
                                {level}
                              </Text>
                            </Pressable>
                          ))}
                        </HStack>
                      </FormControl>
                    </VStack>
                  )}
                </HStack>

                <HStack space="xs" className="items-center">
                  <Pressable
                    onPress={() => onUpdate({ is_featured: !item.is_featured })}
                    className={`w-4 h-4 rounded border-2 items-center justify-center ${
                      item.is_featured ? 'bg-blue-600 border-blue-600' : 'border-gray-300 bg-white'
                    }`}
                  >
                    {item.is_featured && <Icon as={Star} className="text-white" size="xs" />}
                  </Pressable>
                  <Text className="text-gray-700 text-sm">Feature this subject in my profile</Text>
                  <Pressable className="p-1">
                    <Icon as={Info} className="text-gray-400" size="xs" />
                  </Pressable>
                </HStack>
              </VStack>
            </VStack>
          </CardContent>
        )}
      </Card>

      {/* Remove Confirmation Dialog */}
      <AlertDialog isOpen={showRemoveDialog} onClose={() => setShowRemoveDialog(false)}>
        <AlertDialogBackdrop />
        <AlertDialogContent className="max-w-md">
          <AlertDialogHeader>
            <Heading size="lg" className="text-gray-900">
              Remove Subject
            </Heading>
          </AlertDialogHeader>
          <AlertDialogBody>
            <Text className="text-gray-600">
              Are you sure you want to remove "{name}" from your teaching subjects?
            </Text>
          </AlertDialogBody>
          <AlertDialogFooter>
            <HStack space="sm" className="w-full justify-end">
              <Button variant="outline" onPress={() => setShowRemoveDialog(false)}>
                <ButtonText>Cancel</ButtonText>
              </Button>
              <Button
                onPress={() => {
                  onRemove();
                  setShowRemoveDialog(false);
                }}
                className="bg-red-600"
              >
                <ButtonText className="text-white">Remove</ButtonText>
              </Button>
            </HStack>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
};
