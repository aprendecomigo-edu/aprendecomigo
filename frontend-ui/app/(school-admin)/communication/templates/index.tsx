import { isWeb } from '@gluestack-ui/nativewind-utils/IsWeb';
import { router } from 'expo-router';
import { 
  PlusIcon, 
  EditIcon, 
  CopyIcon, 
  TrashIcon, 
  MailIcon,
  EyeIcon,
  SendIcon,
  FilterIcon,
  SearchIcon
} from 'lucide-react-native';
import React, { useCallback, useState, useMemo } from 'react';
import { Alert } from 'react-native';

import MainLayout from '@/components/layouts/main-layout';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Center } from '@/components/ui/center';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Input, InputField } from '@/components/ui/input';
import { Pressable } from '@/components/ui/pressable';
import { ScrollView } from '@/components/ui/scroll-view';
import { Select, SelectContent, SelectItem, SelectTrigger } from '@/components/ui/select';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { Badge } from '@/components/ui/badge';
import { useCommunicationTemplates, useTemplateActions } from '@/hooks/useCommunicationTemplates';
import { SchoolEmailTemplate, EmailTemplateType } from '@/api/communicationApi';

const TemplateManagement = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState<keyof EmailTemplateType | 'all'>('all');
  const [filterStatus, setFilterStatus] = useState<'all' | 'active' | 'inactive'>('all');

  const { 
    templates, 
    loading, 
    error, 
    pagination, 
    fetchTemplates, 
    refreshTemplates 
  } = useCommunicationTemplates();

  const { 
    loading: actionLoading, 
    confirmDelete, 
    toggleTemplateStatus 
  } = useTemplateActions();

  // Filter templates based on search and filters
  const filteredTemplates = useMemo(() => {
    return templates.filter(template => {
      const matchesSearch = template.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                           template.subject_template.toLowerCase().includes(searchQuery.toLowerCase());
      
      const matchesType = filterType === 'all' || template.template_type === filterType;
      
      const matchesStatus = filterStatus === 'all' || 
                           (filterStatus === 'active' && template.is_active) ||
                           (filterStatus === 'inactive' && !template.is_active);
      
      return matchesSearch && matchesType && matchesStatus;
    });
  }, [templates, searchQuery, filterType, filterStatus]);

  // Template type options
  const templateTypeOptions = [
    { label: 'All Types', value: 'all' },
    { label: 'Invitation', value: 'invitation' },
    { label: 'Reminder', value: 'reminder' },
    { label: 'Welcome', value: 'welcome' },
    { label: 'Profile Reminder', value: 'profile_reminder' },
    { label: 'Completion Celebration', value: 'completion_celebration' },
    { label: 'Ongoing Support', value: 'ongoing_support' },
  ];

  // Action handlers
  const handleCreateTemplate = useCallback(() => {
    router.push('/(school-admin)/communication/templates/new');
  }, []);

  const handleEditTemplate = useCallback((template: SchoolEmailTemplate) => {
    router.push(`/(school-admin)/communication/templates/${template.id}/edit`);
  }, []);

  const handlePreviewTemplate = useCallback((template: SchoolEmailTemplate) => {
    router.push(`/(school-admin)/communication/templates/${template.id}/preview`);
  }, []);

  const handleDuplicateTemplate = useCallback((template: SchoolEmailTemplate) => {
    Alert.alert(
      'Duplicate Template',
      `Create a copy of "${template.name}"?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Duplicate',
          onPress: () => router.push(`/(school-admin)/communication/templates/${template.id}/duplicate`),
        },
      ]
    );
  }, []);

  const handleDeleteTemplate = useCallback((template: SchoolEmailTemplate) => {
    confirmDelete(template.name, async () => {
      try {
        // This would be handled by the useTemplateActions hook
        await refreshTemplates();
      } catch (error) {
        console.error('Error deleting template:', error);
      }
    });
  }, [confirmDelete, refreshTemplates]);

  const handleToggleStatus = useCallback((template: SchoolEmailTemplate) => {
    toggleTemplateStatus(template, () => {
      refreshTemplates();
    });
  }, [toggleTemplateStatus, refreshTemplates]);

  const handleSendTest = useCallback((template: SchoolEmailTemplate) => {
    router.push(`/(school-admin)/communication/templates/${template.id}/test`);
  }, []);

  const clearFilters = useCallback(() => {
    setSearchQuery('');
    setFilterType('all');
    setFilterStatus('all');
  }, []);

  const getTemplateTypeLabel = (type: keyof EmailTemplateType) => {
    return type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  const getTemplateTypeColor = (type: keyof EmailTemplateType) => {
    const colors = {
      invitation: 'bg-blue-100 text-blue-800',
      reminder: 'bg-yellow-100 text-yellow-800',
      welcome: 'bg-green-100 text-green-800',
      profile_reminder: 'bg-orange-100 text-orange-800',
      completion_celebration: 'bg-purple-100 text-purple-800',
      ongoing_support: 'bg-gray-100 text-gray-800',
    };
    return colors[type] || 'bg-gray-100 text-gray-800';
  };

  return (
    <ScrollView
      showsVerticalScrollIndicator={false}
      contentContainerStyle={{
        paddingBottom: isWeb ? 0 : 100,
        flexGrow: 1,
      }}
      className="flex-1 bg-gray-50"
    >
      <VStack className="p-6" space="lg">
        {/* Header */}
        <HStack className="justify-between items-center">
          <VStack space="xs">
            <Heading size="xl" className="text-gray-900">
              Email Templates
            </Heading>
            <Text className="text-gray-600">
              Create and manage your school's email templates
            </Text>
          </VStack>
          
          <Button onPress={handleCreateTemplate} className="bg-blue-600">
            <HStack space="xs" className="items-center">
              <Icon as={PlusIcon} size="sm" className="text-white" />
              <ButtonText className="text-white">New Template</ButtonText>
            </HStack>
          </Button>
        </HStack>

        {/* Search and Filters */}
        <Card className="p-4">
          <VStack space="md">
            <HStack space="md" className="items-center">
              <Box className="flex-1">
                <Input className="w-full">
                  <InputField
                    placeholder="Search templates..."
                    value={searchQuery}
                    onChangeText={setSearchQuery}
                  />
                </Input>
              </Box>
              
              <Button variant="outline" size="sm" onPress={() => {}}>
                <Icon as={SearchIcon} size="sm" className="text-gray-600" />
              </Button>
            </HStack>

            <HStack space="md" className="flex-wrap">
              <Box className="flex-1 min-w-32">
                <Select value={filterType} onValueChange={setFilterType}>
                  <SelectTrigger>
                    <Text className="text-sm">
                      {templateTypeOptions.find(opt => opt.value === filterType)?.label || 'All Types'}
                    </Text>
                  </SelectTrigger>
                  <SelectContent>
                    {templateTypeOptions.map(option => (
                      <SelectItem key={option.value} value={option.value} label={option.label} />
                    ))}
                  </SelectContent>
                </Select>
              </Box>

              <Box className="flex-1 min-w-32">
                <Select value={filterStatus} onValueChange={setFilterStatus}>
                  <SelectTrigger>
                    <Text className="text-sm">
                      {filterStatus === 'all' ? 'All Status' : 
                       filterStatus === 'active' ? 'Active Only' : 'Inactive Only'}
                    </Text>
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all" label="All Status" />
                    <SelectItem value="active" label="Active Only" />
                    <SelectItem value="inactive" label="Inactive Only" />
                  </SelectContent>
                </Select>
              </Box>

              {(searchQuery || filterType !== 'all' || filterStatus !== 'all') && (
                <Button variant="outline" size="sm" onPress={clearFilters}>
                  <ButtonText>Clear</ButtonText>
                </Button>
              )}
            </HStack>

            <HStack className="justify-between items-center">
              <Text className="text-sm text-gray-600">
                {filteredTemplates.length} of {templates.length} templates
              </Text>
              
              <Button variant="link" size="sm" onPress={refreshTemplates}>
                <ButtonText>Refresh</ButtonText>
              </Button>
            </HStack>
          </VStack>
        </Card>

        {/* Templates List */}
        {loading ? (
          <Center className="py-12">
            <VStack space="md" className="items-center">
              <Text className="text-gray-600">Loading templates...</Text>
            </VStack>
          </Center>
        ) : error ? (
          <Card className="p-6">
            <Center>
              <VStack space="md" className="items-center">
                <Text className="text-red-600 font-semibold">Error Loading Templates</Text>
                <Text className="text-gray-600 text-center">{error}</Text>
                <Button onPress={refreshTemplates} variant="outline">
                  <ButtonText>Try Again</ButtonText>
                </Button>
              </VStack>
            </Center>
          </Card>
        ) : filteredTemplates.length === 0 ? (
          <Card className="p-8">
            <Center>
              <VStack space="md" className="items-center">
                <Icon as={MailIcon} size="xl" className="text-gray-400" />
                <Heading size="md" className="text-gray-900 text-center">
                  {templates.length === 0 ? 'No templates created yet' : 'No templates match your filters'}
                </Heading>
                <Text className="text-gray-600 text-center max-w-md">
                  {templates.length === 0 
                    ? 'Create your first email template to start communicating with teachers professionally.'
                    : 'Try adjusting your search or filter criteria to find the templates you\'re looking for.'
                  }
                </Text>
                {templates.length === 0 ? (
                  <Button onPress={handleCreateTemplate}>
                    <ButtonText>Create First Template</ButtonText>
                  </Button>
                ) : (
                  <Button onPress={clearFilters} variant="outline">
                    <ButtonText>Clear Filters</ButtonText>
                  </Button>
                )}
              </VStack>
            </Center>
          </Card>
        ) : (
          <VStack space="md">
            {filteredTemplates.map((template) => (
              <Card key={template.id} className="p-4">
                <VStack space="md">
                  {/* Template Header */}
                  <HStack className="justify-between items-start">
                    <VStack space="xs" className="flex-1">
                      <HStack space="sm" className="items-center flex-wrap">
                        <Heading size="md" className="text-gray-900">
                          {template.name}
                        </Heading>
                        <Badge className={getTemplateTypeColor(template.template_type)}>
                          <Text className="text-xs font-medium">
                            {getTemplateTypeLabel(template.template_type)}
                          </Text>
                        </Badge>
                        <Badge className={template.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}>
                          <Text className="text-xs font-medium">
                            {template.is_active ? 'Active' : 'Inactive'}
                          </Text>
                        </Badge>
                      </HStack>
                      
                      <Text className="text-gray-600 text-sm">
                        Subject: {template.subject_template}
                      </Text>
                      
                      <Text className="text-xs text-gray-500">
                        Updated {new Date(template.updated_at).toLocaleDateString()}
                      </Text>
                    </VStack>
                  </HStack>

                  {/* Template Actions */}
                  <HStack space="sm" className="flex-wrap">
                    <Button
                      size="sm"
                      variant="outline"
                      onPress={() => handlePreviewTemplate(template)}
                    >
                      <HStack space="xs" className="items-center">
                        <Icon as={EyeIcon} size="xs" className="text-gray-600" />
                        <ButtonText>Preview</ButtonText>
                      </HStack>
                    </Button>

                    <Button
                      size="sm"
                      variant="outline"
                      onPress={() => handleEditTemplate(template)}
                    >
                      <HStack space="xs" className="items-center">
                        <Icon as={EditIcon} size="xs" className="text-gray-600" />
                        <ButtonText>Edit</ButtonText>
                      </HStack>
                    </Button>

                    <Button
                      size="sm"
                      variant="outline"
                      onPress={() => handleDuplicateTemplate(template)}
                    >
                      <HStack space="xs" className="items-center">
                        <Icon as={CopyIcon} size="xs" className="text-gray-600" />
                        <ButtonText>Duplicate</ButtonText>
                      </HStack>
                    </Button>

                    <Button
                      size="sm"
                      variant="outline"
                      onPress={() => handleSendTest(template)}
                    >
                      <HStack space="xs" className="items-center">
                        <Icon as={SendIcon} size="xs" className="text-gray-600" />
                        <ButtonText>Send Test</ButtonText>
                      </HStack>
                    </Button>

                    <Button
                      size="sm"
                      variant="outline"
                      onPress={() => handleToggleStatus(template)}
                      disabled={actionLoading}
                    >
                      <ButtonText>
                        {template.is_active ? 'Deactivate' : 'Activate'}
                      </ButtonText>
                    </Button>

                    <Button
                      size="sm"
                      variant="outline"
                      onPress={() => handleDeleteTemplate(template)}
                      disabled={actionLoading}
                      className="border-red-200 hover:bg-red-50"
                    >
                      <HStack space="xs" className="items-center">
                        <Icon as={TrashIcon} size="xs" className="text-red-600" />
                        <ButtonText className="text-red-600">Delete</ButtonText>
                      </HStack>
                    </Button>
                  </HStack>
                </VStack>
              </Card>
            ))}

            {/* Pagination */}
            {pagination.count > templates.length && (
              <Card className="p-4">
                <HStack className="justify-center">
                  <Button
                    variant="outline"
                    onPress={() => fetchTemplates({ page: pagination.currentPage + 1 })}
                    disabled={!pagination.next}
                  >
                    <ButtonText>Load More Templates</ButtonText>
                  </Button>
                </HStack>
              </Card>
            )}
          </VStack>
        )}
      </VStack>
    </ScrollView>
  );
};

const TemplateManagementPage = () => {
  return (
    <MainLayout _title="Email Templates">
      <TemplateManagement />
    </MainLayout>
  );
};

export default TemplateManagementPage;