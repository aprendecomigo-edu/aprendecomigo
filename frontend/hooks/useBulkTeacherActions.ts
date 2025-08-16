import { useState, useCallback } from 'react';

import {
  BulkTeacherAction,
  BulkActionResult,
  TeacherMessageTemplate,
  performBulkTeacherActions,
  getTeacherMessageTemplates,
} from '@/api/userApi';

interface UseBulkTeacherActionsReturn {
  loading: boolean;
  error: string | null;
  lastResult: BulkActionResult | null;
  templates: TeacherMessageTemplate[];
  templatesLoading: boolean;

  // Actions
  performAction: (action: BulkTeacherAction) => Promise<BulkActionResult>;
  updateStatus: (
    teacherIds: number[],
    status: 'active' | 'inactive' | 'pending',
  ) => Promise<BulkActionResult>;
  sendMessage: (
    teacherIds: number[],
    template: string,
    customMessage?: string,
  ) => Promise<BulkActionResult>;
  exportData: (teacherIds: number[], fields?: string[]) => Promise<BulkActionResult>;
  updateProfiles: (teacherIds: number[], updates: Record<string, any>) => Promise<BulkActionResult>;

  // Template management
  loadTemplates: () => Promise<void>;
  getTemplate: (templateId: string) => TeacherMessageTemplate | undefined;

  // Result helpers
  getSuccessRate: () => number;
  hasErrors: () => boolean;
  getErrorMessages: () => string[];
  clearResult: () => void;
}

export const useBulkTeacherActions = (): UseBulkTeacherActionsReturn => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastResult, setLastResult] = useState<BulkActionResult | null>(null);
  const [templates, setTemplates] = useState<TeacherMessageTemplate[]>([]);
  const [templatesLoading, setTemplatesLoading] = useState(false);

  const performAction = useCallback(
    async (action: BulkTeacherAction): Promise<BulkActionResult> => {
      try {
        setLoading(true);
        setError(null);

        // Validate input
        if (!action.teacher_ids || action.teacher_ids.length === 0) {
          throw new Error('No teachers selected');
        }

        if (action.teacher_ids.length > 50) {
          throw new Error('Cannot perform bulk actions on more than 50 teachers at once');
        }

        const result = await performBulkTeacherActions(action);
        setLastResult(result);

        if (!result.success) {
          setError('Some actions failed. Check the results for details.');
        }

        return result;
      } catch (err: any) {
        console.error('Error performing bulk action:', err);
        const errorMessage = err.message || 'Failed to perform bulk action';
        setError(errorMessage);
        throw new Error(errorMessage);
      } finally {
        setLoading(false);
      }
    },
    [],
  );

  const updateStatus = useCallback(
    async (
      teacherIds: number[],
      status: 'active' | 'inactive' | 'pending',
    ): Promise<BulkActionResult> => {
      return performAction({
        action: 'update_status',
        teacher_ids: teacherIds,
        parameters: { status },
      });
    },
    [performAction],
  );

  const sendMessage = useCallback(
    async (
      teacherIds: number[],
      template: string,
      customMessage?: string,
    ): Promise<BulkActionResult> => {
      return performAction({
        action: 'send_message',
        teacher_ids: teacherIds,
        parameters: {
          template,
          custom_message: customMessage,
        },
      });
    },
    [performAction],
  );

  const exportData = useCallback(
    async (teacherIds: number[], fields?: string[]): Promise<BulkActionResult> => {
      return performAction({
        action: 'export_data',
        teacher_ids: teacherIds,
        parameters: {
          fields: fields || ['name', 'email', 'bio', 'hourly_rate', 'profile_completion_score'],
        },
      });
    },
    [performAction],
  );

  const updateProfiles = useCallback(
    async (teacherIds: number[], updates: Record<string, any>): Promise<BulkActionResult> => {
      return performAction({
        action: 'update_profile',
        teacher_ids: teacherIds,
        parameters: updates,
      });
    },
    [performAction],
  );

  const loadTemplates = useCallback(async () => {
    try {
      setTemplatesLoading(true);
      const templateData = await getTeacherMessageTemplates();
      setTemplates(templateData);
    } catch (err: any) {
      console.error('Error loading message templates:', err);
      // Don't set main error state for template loading failures
    } finally {
      setTemplatesLoading(false);
    }
  }, []);

  const getTemplate = useCallback(
    (templateId: string): TeacherMessageTemplate | undefined => {
      return templates.find(template => template.id === templateId);
    },
    [templates],
  );

  const getSuccessRate = useCallback((): number => {
    if (!lastResult || lastResult.total_processed === 0) return 0;
    return (lastResult.successful_count / lastResult.total_processed) * 100;
  }, [lastResult]);

  const hasErrors = useCallback((): boolean => {
    return Boolean(lastResult && lastResult.errors && lastResult.errors.length > 0);
  }, [lastResult]);

  const getErrorMessages = useCallback((): string[] => {
    if (!lastResult || !lastResult.errors) return [];
    return lastResult.errors.map(error => `Teacher ${error.teacher_id}: ${error.error}`);
  }, [lastResult]);

  const clearResult = useCallback(() => {
    setLastResult(null);
    setError(null);
  }, []);

  return {
    loading,
    error,
    lastResult,
    templates,
    templatesLoading,

    // Actions
    performAction,
    updateStatus,
    sendMessage,
    exportData,
    updateProfiles,

    // Template management
    loadTemplates,
    getTemplate,

    // Result helpers
    getSuccessRate,
    hasErrors,
    getErrorMessages,
    clearResult,
  };
};

export default useBulkTeacherActions;
