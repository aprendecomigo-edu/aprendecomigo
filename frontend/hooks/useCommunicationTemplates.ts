import { useState, useEffect, useCallback } from 'react';
import { Alert } from 'react-native';

import CommunicationApi, {
  SchoolEmailTemplate,
  EmailTemplateType,
  CreateTemplateRequest,
  UpdateTemplateRequest,
  PreviewTemplateResponse,
  TemplateListResponse,
} from '@/api/communicationApi';

interface UseCommunicationTemplatesOptions {
  autoFetch?: boolean;
  templateType?: keyof EmailTemplateType;
  activeOnly?: boolean;
}

export const useCommunicationTemplates = (options: UseCommunicationTemplatesOptions = {}) => {
  const { autoFetch = true, templateType, activeOnly = true } = options;

  const [templates, setTemplates] = useState<SchoolEmailTemplate[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pagination, setPagination] = useState({
    count: 0,
    next: null as string | null,
    previous: null as string | null,
    currentPage: 1,
  });

  const fetchTemplates = useCallback(
    async (params?: {
      template_type?: keyof EmailTemplateType;
      is_active?: boolean;
      page?: number;
    }) => {
      try {
        setLoading(true);
        setError(null);

        const fetchParams = {
          template_type: templateType,
          is_active: activeOnly,
          ...params,
        };

        const response = await CommunicationApi.getSchoolTemplates(fetchParams);

        setTemplates(response.results);
        setPagination({
          count: response.count,
          next: response.next || null,
          previous: response.previous || null,
          currentPage: params?.page || 1,
        });
      } catch (err: any) {
        const errorMessage =
          err.response?.data?.detail || err.message || 'Failed to fetch templates';
        setError(errorMessage);
        console.error('Error fetching templates:', err);
      } finally {
        setLoading(false);
      }
    },
    [templateType, activeOnly],
  );

  const refreshTemplates = useCallback(() => {
    fetchTemplates({ page: pagination.currentPage });
  }, [fetchTemplates, pagination.currentPage]);

  useEffect(() => {
    if (autoFetch) {
      fetchTemplates();
    }
  }, [autoFetch, fetchTemplates]);

  return {
    templates,
    loading,
    error,
    pagination,
    fetchTemplates,
    refreshTemplates,
  };
};

export const useTemplateEditor = () => {
  const [currentTemplate, setCurrentTemplate] = useState<SchoolEmailTemplate | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [availableVariables, setAvailableVariables] = useState<
    Record<string, Record<string, string>>
  >({});

  const loadTemplate = useCallback(async (id: number) => {
    try {
      setLoading(true);
      setError(null);

      const template = await CommunicationApi.getTemplate(id);
      setCurrentTemplate(template);
      setHasUnsavedChanges(false);
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to load template';
      setError(errorMessage);
      console.error('Error loading template:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const createTemplate = useCallback(async (data: CreateTemplateRequest) => {
    try {
      setSaving(true);
      setError(null);

      const template = await CommunicationApi.createTemplate(data);
      setCurrentTemplate(template);
      setHasUnsavedChanges(false);

      Alert.alert('Success', 'Template created successfully');
      return template;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to create template';
      setError(errorMessage);
      Alert.alert('Error', errorMessage);
      throw err;
    } finally {
      setSaving(false);
    }
  }, []);

  const updateTemplate = useCallback(async (id: number, data: UpdateTemplateRequest) => {
    try {
      setSaving(true);
      setError(null);

      const template = await CommunicationApi.updateTemplate(id, data);
      setCurrentTemplate(template);
      setHasUnsavedChanges(false);

      Alert.alert('Success', 'Template updated successfully');
      return template;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to update template';
      setError(errorMessage);
      Alert.alert('Error', errorMessage);
      throw err;
    } finally {
      setSaving(false);
    }
  }, []);

  const deleteTemplate = useCallback(
    async (id: number) => {
      try {
        setSaving(true);
        setError(null);

        await CommunicationApi.deleteTemplate(id);

        if (currentTemplate?.id === id) {
          setCurrentTemplate(null);
        }

        Alert.alert('Success', 'Template deleted successfully');
      } catch (err: any) {
        const errorMessage =
          err.response?.data?.detail || err.message || 'Failed to delete template';
        setError(errorMessage);
        Alert.alert('Error', errorMessage);
        throw err;
      } finally {
        setSaving(false);
      }
    },
    [currentTemplate],
  );

  const duplicateTemplate = useCallback(async (id: number, newName?: string) => {
    try {
      setSaving(true);
      setError(null);

      const template = await CommunicationApi.duplicateTemplate(id, newName);
      setCurrentTemplate(template);
      setHasUnsavedChanges(false);

      Alert.alert('Success', 'Template duplicated successfully');
      return template;
    } catch (err: any) {
      const errorMessage =
        err.response?.data?.detail || err.message || 'Failed to duplicate template';
      setError(errorMessage);
      Alert.alert('Error', errorMessage);
      throw err;
    } finally {
      setSaving(false);
    }
  }, []);

  const updateTemplateField = useCallback(
    (field: keyof SchoolEmailTemplate, value: any) => {
      if (currentTemplate) {
        setCurrentTemplate({
          ...currentTemplate,
          [field]: value,
        });
        setHasUnsavedChanges(true);
      }
    },
    [currentTemplate],
  );

  const loadAvailableVariables = useCallback(async () => {
    try {
      const variables = await CommunicationApi.getAvailableVariables();
      setAvailableVariables(variables);
    } catch (err: any) {
      console.error('Error loading available variables:', err);
    }
  }, []);

  useEffect(() => {
    loadAvailableVariables();
  }, [loadAvailableVariables]);

  return {
    currentTemplate,
    loading,
    saving,
    error,
    hasUnsavedChanges,
    availableVariables,
    loadTemplate,
    createTemplate,
    updateTemplate,
    deleteTemplate,
    duplicateTemplate,
    updateTemplateField,
    setHasUnsavedChanges,
    clearError: () => setError(null),
  };
};

export const useTemplatePreview = () => {
  const [preview, setPreview] = useState<PreviewTemplateResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const generatePreview = useCallback(
    async (data: {
      template_id?: number;
      template_type?: keyof EmailTemplateType;
      subject_template?: string;
      html_content?: string;
      text_content?: string;
      context_variables?: Record<string, any>;
    }) => {
      try {
        setLoading(true);
        setError(null);

        const previewResponse = await CommunicationApi.previewTemplate(data);
        setPreview(previewResponse);

        return previewResponse;
      } catch (err: any) {
        const errorMessage =
          err.response?.data?.detail || err.message || 'Failed to generate preview';
        setError(errorMessage);
        console.error('Error generating preview:', err);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [],
  );

  const sendTestEmail = useCallback(async (templateId: number, testEmail: string) => {
    try {
      setLoading(true);
      setError(null);

      const response = await CommunicationApi.sendTestEmail(templateId, testEmail);

      if (response.success) {
        Alert.alert('Success', 'Test email sent successfully');
      } else {
        Alert.alert('Warning', response.message);
      }

      return response;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to send test email';
      setError(errorMessage);
      Alert.alert('Error', errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const validateTemplate = useCallback(
    async (templateContent: {
      subject_template: string;
      html_content: string;
      text_content: string;
    }) => {
      try {
        setLoading(true);
        setError(null);

        const validation = await CommunicationApi.validateTemplate(templateContent);
        return validation;
      } catch (err: any) {
        const errorMessage =
          err.response?.data?.detail || err.message || 'Failed to validate template';
        setError(errorMessage);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [],
  );

  return {
    preview,
    loading,
    error,
    generatePreview,
    sendTestEmail,
    validateTemplate,
    clearPreview: () => setPreview(null),
    clearError: () => setError(null),
  };
};

export const useTemplateActions = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const confirmDelete = useCallback((templateName: string, onConfirm: () => void) => {
    Alert.alert(
      'Delete Template',
      `Are you sure you want to delete "${templateName}"? This action cannot be undone.`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: onConfirm,
        },
      ],
    );
  }, []);

  const toggleTemplateStatus = useCallback(
    async (
      template: SchoolEmailTemplate,
      onUpdate: (updatedTemplate: SchoolEmailTemplate) => void,
    ) => {
      try {
        setLoading(true);
        setError(null);

        const updatedTemplate = await CommunicationApi.updateTemplate(template.id, {
          is_active: !template.is_active,
        });

        onUpdate(updatedTemplate);

        Alert.alert(
          'Success',
          `Template ${updatedTemplate.is_active ? 'activated' : 'deactivated'} successfully`,
        );
      } catch (err: any) {
        const errorMessage =
          err.response?.data?.detail || err.message || 'Failed to update template status';
        setError(errorMessage);
        Alert.alert('Error', errorMessage);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [],
  );

  return {
    loading,
    error,
    confirmDelete,
    toggleTemplateStatus,
    clearError: () => setError(null),
  };
};
