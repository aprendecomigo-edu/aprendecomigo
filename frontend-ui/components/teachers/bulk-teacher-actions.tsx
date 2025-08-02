import {
  Users,
  Mail,
  Activity,
  Download,
  Edit3,
  CheckCircle,
  AlertCircle,
  X,
  Send,
  FileDown,
  Settings,
  MessageSquare,
} from 'lucide-react-native';
import React, { useState, useEffect } from 'react';

import { TeacherProfile, TeacherMessageTemplate } from '@/api/userApi';
import { Badge } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Divider } from '@/components/ui/divider';
import { FormControl } from '@/components/ui/form-control';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Input } from '@/components/ui/input';
import { Modal } from '@/components/ui/modal';
import { Pressable } from '@/components/ui/pressable';
import { Progress } from '@/components/ui/progress';
import { ScrollView } from '@/components/ui/scroll-view';
import { Select } from '@/components/ui/select';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { Textarea } from '@/components/ui/textarea';
import { VStack } from '@/components/ui/vstack';
import { useBulkTeacherActions } from '@/hooks/useBulkTeacherActions';

interface BulkTeacherActionsProps {
  selectedTeachers: number[];
  teachers: TeacherProfile[];
  onClearSelection: () => void;
  onActionComplete?: () => void;
}

type ActionType = 'message' | 'status' | 'export' | 'profile';

interface MessageFormData {
  template: string;
  customMessage: string;
  subject: string;
}

interface StatusFormData {
  status: 'active' | 'inactive' | 'pending';
  reason: string;
}

interface ExportFormData {
  fields: string[];
  format: 'csv' | 'xlsx';
}

interface ProfileFormData {
  updateType: 'status' | 'availability' | 'calendar';
  value: string;
}

const MESSAGE_TEMPLATES = [
  {
    id: 'profile_completion_reminder',
    name: 'Lembrete de Perfil',
    subject: 'Complete seu perfil na plataforma',
    content:
      'Olá {{name}}, notamos que seu perfil ainda não está completo. Complete as informações para melhorar sua visibilidade para os estudantes.',
    variables: ['name', 'completion_percentage', 'missing_fields'],
  },
  {
    id: 'welcome_onboarding',
    name: 'Boas-vindas',
    subject: 'Bem-vindo à nossa plataforma!',
    content:
      'Olá {{name}}, seja bem-vindo à nossa plataforma! Estamos animados para tê-lo conosco.',
    variables: ['name', 'school_name'],
  },
  {
    id: 'custom',
    name: 'Mensagem Personalizada',
    subject: '',
    content: '',
    variables: ['name', 'email'],
  },
];

const EXPORT_FIELDS = [
  { id: 'name', label: 'Nome', default: true },
  { id: 'email', label: 'Email', default: true },
  { id: 'specialty', label: 'Especialidade', default: true },
  { id: 'hourly_rate', label: 'Taxa Horária', default: true },
  { id: 'profile_completion_score', label: 'Completude do Perfil', default: true },
  { id: 'bio', label: 'Biografia', default: false },
  { id: 'education', label: 'Formação', default: false },
  { id: 'availability', label: 'Disponibilidade', default: false },
  { id: 'phone_number', label: 'Telefone', default: false },
  { id: 'address', label: 'Endereço', default: false },
  { id: 'last_activity', label: 'Última Atividade', default: false },
];

export const BulkTeacherActions: React.FC<BulkTeacherActionsProps> = ({
  selectedTeachers,
  teachers,
  onClearSelection,
  onActionComplete,
}) => {
  const [showModal, setShowModal] = useState(false);
  const [currentAction, setCurrentAction] = useState<ActionType | null>(null);

  // Form states
  const [messageForm, setMessageForm] = useState<MessageFormData>({
    template: '',
    customMessage: '',
    subject: '',
  });

  const [statusForm, setStatusForm] = useState<StatusFormData>({
    status: 'active',
    reason: '',
  });

  const [exportForm, setExportForm] = useState<ExportFormData>({
    fields: EXPORT_FIELDS.filter(f => f.default).map(f => f.id),
    format: 'csv',
  });

  const {
    loading,
    error,
    lastResult,
    performAction,
    updateStatus,
    sendMessage,
    exportData,
    getSuccessRate,
    hasErrors,
    getErrorMessages,
    clearResult,
  } = useBulkTeacherActions();

  const selectedTeacherData = teachers.filter(t => selectedTeachers.includes(t.id));

  useEffect(() => {
    if (lastResult && !loading) {
      // Auto-close modal after successful action
      if (lastResult.success && getSuccessRate() > 80) {
        setTimeout(() => {
          setShowModal(false);
          onActionComplete?.();
        }, 2000);
      }
    }
  }, [lastResult, loading, getSuccessRate, onActionComplete]);

  const handleActionStart = (action: ActionType) => {
    setCurrentAction(action);
    setShowModal(true);
    clearResult();
  };

  const handleSendMessage = async () => {
    try {
      const template = messageForm.template || 'custom';
      await sendMessage(selectedTeachers, template, messageForm.customMessage);
    } catch (error) {
      console.error('Error sending bulk message:', error);
    }
  };

  const handleUpdateStatus = async () => {
    try {
      await updateStatus(selectedTeachers, statusForm.status);
    } catch (error) {
      console.error('Error updating bulk status:', error);
    }
  };

  const handleExportData = async () => {
    try {
      await exportData(selectedTeachers, exportForm.fields);
    } catch (error) {
      console.error('Error exporting data:', error);
    }
  };

  const renderActionContent = () => {
    switch (currentAction) {
      case 'message':
        return (
          <VStack space="lg">
            <FormControl>
              <Text className="text-sm font-medium text-gray-700 mb-2">Modelo de Mensagem</Text>
              <Select
                selectedValue={messageForm.template}
                onValueChange={value => {
                  const template = MESSAGE_TEMPLATES.find(t => t.id === value);
                  setMessageForm(prev => ({
                    ...prev,
                    template: value,
                    subject: template?.subject || '',
                    customMessage: template?.content || '',
                  }));
                }}
              >
                {MESSAGE_TEMPLATES.map(template => (
                  <Select.Item key={template.id} value={template.id} label={template.name} />
                ))}
              </Select>
            </FormControl>

            <FormControl>
              <Text className="text-sm font-medium text-gray-700 mb-2">Assunto</Text>
              <Input
                value={messageForm.subject}
                onChangeText={value => setMessageForm(prev => ({ ...prev, subject: value }))}
                placeholder="Assunto da mensagem"
              />
            </FormControl>

            <FormControl>
              <Text className="text-sm font-medium text-gray-700 mb-2">Mensagem</Text>
              <Textarea
                value={messageForm.customMessage}
                onChangeText={value => setMessageForm(prev => ({ ...prev, customMessage: value }))}
                placeholder="Digite sua mensagem aqui..."
                numberOfLines={6}
              />
              <Text className="text-xs text-gray-500 mt-1">
                Use {{ name }} para incluir o nome do professor
              </Text>
            </FormControl>

            <Button onPress={handleSendMessage} disabled={loading || !messageForm.customMessage}>
              {loading ? <Spinner size="small" /> : <Icon as={Send} size="sm" />}
              <ButtonText className="ml-2">
                {loading ? 'Enviando...' : `Enviar para ${selectedTeachers.length} professores`}
              </ButtonText>
            </Button>
          </VStack>
        );

      case 'status':
        return (
          <VStack space="lg">
            <FormControl>
              <Text className="text-sm font-medium text-gray-700 mb-2">Novo Status</Text>
              <Select
                selectedValue={statusForm.status}
                onValueChange={value => setStatusForm(prev => ({ ...prev, status: value as any }))}
              >
                <Select.Item value="active" label="Ativo" />
                <Select.Item value="inactive" label="Inativo" />
                <Select.Item value="pending" label="Pendente" />
              </Select>
            </FormControl>

            <FormControl>
              <Text className="text-sm font-medium text-gray-700 mb-2">Motivo (opcional)</Text>
              <Textarea
                value={statusForm.reason}
                onChangeText={value => setStatusForm(prev => ({ ...prev, reason: value }))}
                placeholder="Motivo da alteração de status..."
                numberOfLines={3}
              />
            </FormControl>

            <Button onPress={handleUpdateStatus} disabled={loading}>
              {loading ? <Spinner size="small" /> : <Icon as={Activity} size="sm" />}
              <ButtonText className="ml-2">
                {loading ? 'Atualizando...' : `Atualizar ${selectedTeachers.length} professores`}
              </ButtonText>
            </Button>
          </VStack>
        );

      case 'export':
        return (
          <VStack space="lg">
            <FormControl>
              <Text className="text-sm font-medium text-gray-700 mb-2">Campos para Exportar</Text>
              <VStack space="sm">
                {EXPORT_FIELDS.map(field => (
                  <HStack key={field.id} className="items-center justify-between">
                    <Text className="text-sm text-gray-700">{field.label}</Text>
                    <Checkbox
                      value={exportForm.fields.includes(field.id)}
                      onValueChange={checked => {
                        setExportForm(prev => ({
                          ...prev,
                          fields: checked
                            ? [...prev.fields, field.id]
                            : prev.fields.filter(f => f !== field.id),
                        }));
                      }}
                    />
                  </HStack>
                ))}
              </VStack>
            </FormControl>

            <FormControl>
              <Text className="text-sm font-medium text-gray-700 mb-2">Formato</Text>
              <Select
                selectedValue={exportForm.format}
                onValueChange={value => setExportForm(prev => ({ ...prev, format: value as any }))}
              >
                <Select.Item value="csv" label="CSV" />
                <Select.Item value="xlsx" label="Excel (XLSX)" />
              </Select>
            </FormControl>

            <Button onPress={handleExportData} disabled={loading || exportForm.fields.length === 0}>
              {loading ? <Spinner size="small" /> : <Icon as={FileDown} size="sm" />}
              <ButtonText className="ml-2">
                {loading ? 'Exportando...' : `Exportar ${selectedTeachers.length} professores`}
              </ButtonText>
            </Button>
          </VStack>
        );

      default:
        return null;
    }
  };

  if (selectedTeachers.length === 0) {
    return null;
  }

  return (
    <>
      {/* Floating Action Bar */}
      <Box className="fixed bottom-4 left-4 right-4 bg-white border border-gray-200 rounded-lg shadow-lg p-4 z-50">
        <HStack className="items-center justify-between">
          <HStack className="items-center" space="sm">
            <Icon as={Users} size="sm" className="text-blue-600" />
            <Text className="font-medium text-gray-900">
              {selectedTeachers.length} professor{selectedTeachers.length > 1 ? 'es' : ''}{' '}
              selecionado{selectedTeachers.length > 1 ? 's' : ''}
            </Text>
          </HStack>

          <HStack space="sm">
            <Button variant="outline" size="sm" onPress={() => handleActionStart('message')}>
              <Icon as={Mail} size="sm" className="text-gray-600" />
              <ButtonText className="text-gray-600 ml-1">Mensagem</ButtonText>
            </Button>

            <Button variant="outline" size="sm" onPress={() => handleActionStart('status')}>
              <Icon as={Activity} size="sm" className="text-gray-600" />
              <ButtonText className="text-gray-600 ml-1">Status</ButtonText>
            </Button>

            <Button variant="outline" size="sm" onPress={() => handleActionStart('export')}>
              <Icon as={Download} size="sm" className="text-gray-600" />
              <ButtonText className="text-gray-600 ml-1">Exportar</ButtonText>
            </Button>

            <Pressable
              onPress={onClearSelection}
              className="p-2 border border-gray-300 rounded-md bg-white"
            >
              <Icon as={X} size="sm" className="text-gray-500" />
            </Pressable>
          </HStack>
        </HStack>
      </Box>

      {/* Action Modal */}
      <Modal isOpen={showModal} onClose={() => setShowModal(false)}>
        <Box className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-5/6">
          <VStack space="lg" className="p-6">
            {/* Header */}
            <HStack className="items-center justify-between">
              <VStack>
                <Heading size="lg" className="text-gray-900">
                  {currentAction === 'message' && 'Enviar Mensagem'}
                  {currentAction === 'status' && 'Alterar Status'}
                  {currentAction === 'export' && 'Exportar Dados'}
                  {currentAction === 'profile' && 'Atualizar Perfis'}
                </Heading>
                <Text className="text-sm text-gray-600">
                  Ação será aplicada a {selectedTeachers.length} professor
                  {selectedTeachers.length > 1 ? 'es' : ''}
                </Text>
              </VStack>

              <Pressable onPress={() => setShowModal(false)} className="p-2 -mr-2">
                <Icon as={X} size="md" className="text-gray-500" />
              </Pressable>
            </HStack>

            {/* Selected Teachers Preview */}
            <Box className="p-3 bg-gray-50 rounded-lg">
              <Text className="text-sm font-medium text-gray-700 mb-2">
                Professores Selecionados:
              </Text>
              <ScrollView horizontal showsHorizontalScrollIndicator={false}>
                <HStack space="sm">
                  {selectedTeacherData.slice(0, 5).map(teacher => (
                    <Badge key={teacher.id} variant="secondary" size="sm">
                      {teacher.user.name}
                    </Badge>
                  ))}
                  {selectedTeacherData.length > 5 && (
                    <Badge variant="outline" size="sm">
                      +{selectedTeacherData.length - 5} mais
                    </Badge>
                  )}
                </HStack>
              </ScrollView>
            </Box>

            {/* Error Display */}
            {error && (
              <Box className="p-4 bg-red-50 border border-red-200 rounded-lg">
                <HStack space="sm" className="items-start">
                  <Icon as={AlertCircle} size="sm" className="text-red-600 mt-1" />
                  <Text className="text-sm text-red-800 flex-1">{error}</Text>
                </HStack>
              </Box>
            )}

            {/* Result Display */}
            {lastResult && !loading && (
              <Box
                className={`p-4 border rounded-lg ${
                  lastResult.success ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'
                }`}
              >
                <HStack space="sm" className="items-start">
                  <Icon
                    as={lastResult.success ? CheckCircle : AlertCircle}
                    size="sm"
                    className={lastResult.success ? 'text-green-600 mt-1' : 'text-red-600 mt-1'}
                  />
                  <VStack className="flex-1">
                    <Text
                      className={`text-sm font-medium ${
                        lastResult.success ? 'text-green-800' : 'text-red-800'
                      }`}
                    >
                      {lastResult.success ? 'Ação concluída' : 'Ação parcialmente concluída'}
                    </Text>
                    <Text
                      className={`text-xs ${
                        lastResult.success ? 'text-green-700' : 'text-red-700'
                      }`}
                    >
                      {lastResult.successful_count} de {lastResult.total_processed} processados com
                      sucesso
                    </Text>

                    {hasErrors() && (
                      <VStack space="xs" className="mt-2">
                        <Text className="text-xs font-medium text-red-700">Erros:</Text>
                        {getErrorMessages()
                          .slice(0, 3)
                          .map((error, index) => (
                            <Text key={index} className="text-xs text-red-600">
                              • {error}
                            </Text>
                          ))}
                      </VStack>
                    )}

                    {lastResult.export_url && (
                      <Button
                        variant="outline"
                        size="sm"
                        className="mt-2 self-start"
                        onPress={() => {
                          // TODO: Handle download
                          console.log('Download:', lastResult.export_url);
                        }}
                      >
                        <Icon as={Download} size="sm" />
                        <ButtonText className="ml-2">Baixar Arquivo</ButtonText>
                      </Button>
                    )}
                  </VStack>
                </HStack>
              </Box>
            )}

            {/* Action Content */}
            <ScrollView showsVerticalScrollIndicator={false} className="max-h-96">
              {renderActionContent()}
            </ScrollView>
          </VStack>
        </Box>
      </Modal>
    </>
  );
};

export default BulkTeacherActions;
