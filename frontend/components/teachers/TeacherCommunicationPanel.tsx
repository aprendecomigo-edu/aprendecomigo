import {
  MessageCircle,
  Send,
  Bell,
  Mail,
  Users,
  AlertTriangle,
  CheckCircle,
  Clock,
  Filter,
  RefreshCw,
  MessageSquare,
  FileText,
  User,
  X,
  Plus,
  Edit3,
} from 'lucide-react-native';
import React, { useState, useEffect } from 'react';

import { TeacherProfile, TeacherMessageTemplate } from '@/api/userApi';
import { Badge } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { Divider } from '@/components/ui/divider';
import { FormControl } from '@/components/ui/form-control';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Input } from '@/components/ui/input';
import { Modal } from '@/components/ui/modal';
import { Pressable } from '@/components/ui/pressable';
import { ScrollView } from '@/components/ui/scroll-view';
import { Select } from '@/components/ui/select';
import { Spinner } from '@/components/ui/spinner';
import { Switch } from '@/components/ui/switch';
import { Text } from '@/components/ui/text';
import { Textarea } from '@/components/ui/textarea';
import { VStack } from '@/components/ui/vstack';
import { useBulkTeacherActions } from '@/hooks/useBulkTeacherActions';

interface TeacherCommunicationPanelProps {
  teachers: TeacherProfile[];
  selectedTeachers?: number[];
  onTeacherSelect?: (teacherId: number, selected: boolean) => void;
  onSelectAll?: (selected: boolean) => void;
  onRefresh?: () => void;
}

interface MessageFormData {
  template: string;
  subject: string;
  message: string;
  includeProfileLink: boolean;
  urgentFlag: boolean;
  scheduleDate?: string;
}

interface FilterOptions {
  status: 'all' | 'active' | 'inactive' | 'pending';
  completionStatus: 'all' | 'complete' | 'incomplete' | 'critical';
  lastActivity: 'all' | 'today' | 'week' | 'month' | 'never';
}

const MESSAGE_TEMPLATES: TeacherMessageTemplate[] = [
  {
    id: 'profile_completion_reminder',
    name: 'Lembrete de Perfil Incompleto',
    subject: 'Complete seu perfil profissional',
    content:
      'Olá {{name}},\n\nNotamos que seu perfil ainda não está completo ({{completion_percentage}}% concluído). Para melhorar sua visibilidade para os estudantes e aumentar suas oportunidades de aulas, por favor complete as seguintes informações:\n\n{{missing_fields_list}}\n\nClique aqui para acessar seu perfil: {{profile_link}}\n\nObrigado!',
    variables: ['name', 'completion_percentage', 'missing_fields_list', 'profile_link'],
  },
  {
    id: 'critical_fields_missing',
    name: 'Campos Críticos Ausentes',
    subject: 'Ação necessária: Informações importantes em falta',
    content:
      'Olá {{name}},\n\nIdentificamos que alguns campos críticos do seu perfil estão em falta:\n\n{{critical_fields_list}}\n\nEstas informações são essenciais para garantir a qualidade do nosso serviço. Por favor, complete-as o quanto antes.\n\nPerfil: {{profile_link}}\n\nObrigado pela sua atenção!',
    variables: ['name', 'critical_fields_list', 'profile_link'],
  },
  {
    id: 'welcome_onboarding',
    name: 'Boas-vindas e Orientação',
    subject: 'Bem-vindo à nossa plataforma!',
    content:
      'Olá {{name}},\n\nSeja muito bem-vindo à nossa plataforma educacional!\n\nPara começar a receber estudantes, certifique-se de que seu perfil está completo. Aqui está um guia rápido:\n\n1. Complete sua biografia profissional\n2. Adicione suas qualificações e especialidades\n3. Configure sua disponibilidade\n4. Defina sua taxa horária\n\nSeu perfil: {{profile_link}}\n\nSe tiver dúvidas, não hesite em nos contactar!\n\nBem-vindo à equipe!',
    variables: ['name', 'profile_link'],
  },
  {
    id: 'activity_reminder',
    name: 'Lembrete de Atividade',
    subject: 'Sentimos sua falta na plataforma',
    content:
      'Olá {{name}},\n\nNotamos que não tem estado ativo na plataforma há algum tempo. Temos novos estudantes procurando aulas na sua área de especialidade!\n\nPara reativar seu perfil e começar a receber novos estudantes:\n\n1. Atualize sua disponibilidade\n2. Revise suas informações de contato\n3. Confirme seus horários\n\nAcesse aqui: {{profile_link}}\n\nEsperamos vê-lo em breve!',
    variables: ['name', 'profile_link'],
  },
  {
    id: 'custom',
    name: 'Mensagem Personalizada',
    subject: '',
    content: '',
    variables: ['name', 'email', 'profile_link'],
  },
];

const getCompletionStatusColor = (status: 'complete' | 'incomplete' | 'critical') => {
  switch (status) {
    case 'complete':
      return 'text-green-600';
    case 'critical':
      return 'text-red-600';
    default:
      return 'text-yellow-600';
  }
};

const getCompletionStatusBadge = (status: 'complete' | 'incomplete' | 'critical') => {
  switch (status) {
    case 'complete':
      return { variant: 'success' as const, text: 'Completo' };
    case 'critical':
      return { variant: 'destructive' as const, text: 'Crítico' };
    default:
      return { variant: 'secondary' as const, text: 'Incompleto' };
  }
};

const TeacherRow: React.FC<{
  teacher: TeacherProfile;
  selected: boolean;
  onSelect: (selected: boolean) => void;
}> = ({ teacher, selected, onSelect }) => {
  const completionPercentage = teacher.profile_completion_score || 0;
  const isComplete = teacher.is_profile_complete || false;
  const hasCritical = teacher.profile_completion?.missing_critical?.length > 0;

  const completionStatus: 'complete' | 'incomplete' | 'critical' =
    hasCritical || completionPercentage < 30
      ? 'critical'
      : isComplete && completionPercentage >= 80
        ? 'complete'
        : 'incomplete';

  const statusBadge = getCompletionStatusBadge(completionStatus);

  const getLastActivityText = (): string => {
    if (!teacher.last_activity) return 'Nunca';

    const date = new Date(teacher.last_activity);
    const now = new Date();
    const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return 'Hoje';
    if (diffDays === 1) return 'Ontem';
    if (diffDays < 7) return `${diffDays}d atrás`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)}sem atrás`;
    return `${Math.floor(diffDays / 30)}m atrás`;
  };

  return (
    <HStack className="p-3 border-b border-gray-100 items-center" space="sm">
      <Checkbox value={selected} onValueChange={onSelect} />

      <VStack className="flex-1" space="xs">
        <HStack className="items-center justify-between">
          <Text className="font-medium text-gray-900">{teacher.user.name}</Text>
          <Badge variant={statusBadge.variant} size="sm">
            {statusBadge.text}
          </Badge>
        </HStack>

        <Text className="text-sm text-gray-600">{teacher.user.email}</Text>

        <HStack className="items-center justify-between">
          <HStack className="items-center" space="xs">
            <Text className="text-xs text-gray-500">
              Perfil: {Math.round(completionPercentage)}%
            </Text>
            {hasCritical && (
              <Badge variant="destructive" size="sm">
                {teacher.profile_completion?.missing_critical?.length} crítico
              </Badge>
            )}
          </HStack>

          <Text className="text-xs text-gray-500">Atividade: {getLastActivityText()}</Text>
        </HStack>
      </VStack>
    </HStack>
  );
};

export const TeacherCommunicationPanel: React.FC<TeacherCommunicationPanelProps> = ({
  teachers,
  selectedTeachers = [],
  onTeacherSelect,
  onSelectAll,
  onRefresh,
}) => {
  const [showMessageModal, setShowMessageModal] = useState(false);
  const [showTemplateModal, setShowTemplateModal] = useState(false);
  const [messageForm, setMessageForm] = useState<MessageFormData>({
    template: '',
    subject: '',
    message: '',
    includeProfileLink: true,
    urgentFlag: false,
  });

  const [filters, setFilters] = useState<FilterOptions>({
    status: 'all',
    completionStatus: 'all',
    lastActivity: 'all',
  });

  const [searchQuery, setSearchQuery] = useState('');
  const [showFilters, setShowFilters] = useState(false);

  const {
    loading,
    error,
    lastResult,
    templates,
    templatesLoading,
    sendMessage,
    loadTemplates,
    getTemplate,
    getSuccessRate,
    hasErrors,
    clearResult,
  } = useBulkTeacherActions();

  // Load templates on mount
  useEffect(() => {
    loadTemplates();
  }, [loadTemplates]);

  // Filter teachers based on current filters
  const filteredTeachers = React.useMemo(() => {
    let filtered = [...teachers];

    // Apply search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        teacher =>
          teacher.user.name.toLowerCase().includes(query) ||
          teacher.user.email.toLowerCase().includes(query) ||
          teacher.specialty?.toLowerCase().includes(query),
      );
    }

    // Apply status filter
    if (filters.status !== 'all') {
      filtered = filtered.filter(teacher => teacher.status === filters.status);
    }

    // Apply completion status filter
    if (filters.completionStatus !== 'all') {
      filtered = filtered.filter(teacher => {
        const completionScore = teacher.profile_completion_score || 0;
        const hasCritical = teacher.profile_completion?.missing_critical?.length > 0;

        switch (filters.completionStatus) {
          case 'complete':
            return teacher.is_profile_complete && completionScore >= 80;
          case 'critical':
            return hasCritical || completionScore < 30;
          case 'incomplete':
            return !teacher.is_profile_complete && completionScore < 80 && !hasCritical;
          default:
            return true;
        }
      });
    }

    // Apply last activity filter
    if (filters.lastActivity !== 'all') {
      const now = new Date();
      filtered = filtered.filter(teacher => {
        if (!teacher.last_activity && filters.lastActivity === 'never') return true;
        if (!teacher.last_activity) return false;

        const activityDate = new Date(teacher.last_activity);
        const diffDays = Math.floor(
          (now.getTime() - activityDate.getTime()) / (1000 * 60 * 60 * 24),
        );

        switch (filters.lastActivity) {
          case 'today':
            return diffDays === 0;
          case 'week':
            return diffDays <= 7;
          case 'month':
            return diffDays <= 30;
          default:
            return true;
        }
      });
    }

    return filtered;
  }, [teachers, searchQuery, filters]);

  const selectedTeacherData = teachers.filter(t => selectedTeachers.includes(t.id));

  const handleTemplateSelect = (templateId: string) => {
    const template = MESSAGE_TEMPLATES.find(t => t.id === templateId);
    if (template) {
      setMessageForm(prev => ({
        ...prev,
        template: templateId,
        subject: template.subject,
        message: template.content,
      }));
    }
  };

  const handleSendMessage = async () => {
    if (selectedTeachers.length === 0) {
      alert('Selecione pelo menos um professor');
      return;
    }

    if (!messageForm.message.trim()) {
      alert('Digite uma mensagem');
      return;
    }

    try {
      await sendMessage(selectedTeachers, messageForm.template || 'custom', messageForm.message);

      if (getSuccessRate() > 80) {
        setShowMessageModal(false);
        setMessageForm({
          template: '',
          subject: '',
          message: '',
          includeProfileLink: true,
          urgentFlag: false,
        });
      }
    } catch (error) {
      console.error('Error sending message:', error);
    }
  };

  const renderQuickActions = () => (
    <HStack space="sm" className="flex-wrap">
      <Button
        variant="outline"
        size="sm"
        onPress={() => {
          // Set completion reminder template
          handleTemplateSelect('profile_completion_reminder');
          setShowMessageModal(true);
        }}
        disabled={selectedTeachers.length === 0}
      >
        <Icon as={Bell} size="sm" />
        <ButtonText className="ml-1">Lembrete Perfil</ButtonText>
      </Button>

      <Button
        variant="outline"
        size="sm"
        onPress={() => {
          // Set critical fields template
          handleTemplateSelect('critical_fields_missing');
          setShowMessageModal(true);
        }}
        disabled={selectedTeachers.length === 0}
      >
        <Icon as={AlertTriangle} size="sm" />
        <ButtonText className="ml-1">Campos Críticos</ButtonText>
      </Button>

      <Button
        variant="outline"
        size="sm"
        onPress={() => {
          // Set activity reminder template
          handleTemplateSelect('activity_reminder');
          setShowMessageModal(true);
        }}
        disabled={selectedTeachers.length === 0}
      >
        <Icon as={Clock} size="sm" />
        <ButtonText className="ml-1">Atividade</ButtonText>
      </Button>

      <Button
        size="sm"
        onPress={() => setShowMessageModal(true)}
        disabled={selectedTeachers.length === 0}
        className="bg-blue-600"
      >
        <Icon as={MessageSquare} size="sm" />
        <ButtonText className="ml-1">Mensagem Personalizada</ButtonText>
      </Button>
    </HStack>
  );

  return (
    <VStack space="lg" className="bg-white rounded-lg border border-gray-200">
      {/* Header */}
      <VStack space="md" className="p-6 pb-0">
        <HStack className="items-center justify-between">
          <VStack>
            <Heading size="md" className="text-gray-900">
              Comunicação com Professores
            </Heading>
            <Text className="text-sm text-gray-600">
              {filteredTeachers.length} professores • {selectedTeachers.length} selecionados
            </Text>
          </VStack>

          <HStack space="sm">
            <Button variant="outline" size="sm" onPress={() => setShowFilters(!showFilters)}>
              <Icon as={Filter} size="sm" />
              <ButtonText className="ml-1">Filtros</ButtonText>
            </Button>

            <Button variant="outline" size="sm" onPress={onRefresh}>
              <Icon as={RefreshCw} size="sm" />
              <ButtonText className="ml-1">Atualizar</ButtonText>
            </Button>
          </HStack>
        </HStack>

        {/* Search */}
        <Input
          placeholder="Buscar professores..."
          value={searchQuery}
          onChangeText={setSearchQuery}
          className="bg-gray-50"
        />

        {/* Filters */}
        {showFilters && (
          <Card className="p-4 bg-gray-50">
            <VStack space="md">
              <HStack space="md">
                <VStack className="flex-1">
                  <Text className="text-sm font-medium text-gray-700">Status</Text>
                  <Select
                    selectedValue={filters.status}
                    onValueChange={value => setFilters(prev => ({ ...prev, status: value as any }))}
                  >
                    <Select.Item value="all" label="Todos" />
                    <Select.Item value="active" label="Ativo" />
                    <Select.Item value="inactive" label="Inativo" />
                    <Select.Item value="pending" label="Pendente" />
                  </Select>
                </VStack>

                <VStack className="flex-1">
                  <Text className="text-sm font-medium text-gray-700">Completude</Text>
                  <Select
                    selectedValue={filters.completionStatus}
                    onValueChange={value =>
                      setFilters(prev => ({ ...prev, completionStatus: value as any }))
                    }
                  >
                    <Select.Item value="all" label="Todos" />
                    <Select.Item value="complete" label="Completos" />
                    <Select.Item value="incomplete" label="Incompletos" />
                    <Select.Item value="critical" label="Críticos" />
                  </Select>
                </VStack>
              </HStack>

              <VStack>
                <Text className="text-sm font-medium text-gray-700">Última Atividade</Text>
                <Select
                  selectedValue={filters.lastActivity}
                  onValueChange={value =>
                    setFilters(prev => ({ ...prev, lastActivity: value as any }))
                  }
                >
                  <Select.Item value="all" label="Qualquer período" />
                  <Select.Item value="today" label="Hoje" />
                  <Select.Item value="week" label="Esta semana" />
                  <Select.Item value="month" label="Este mês" />
                  <Select.Item value="never" label="Nunca ativo" />
                </Select>
              </VStack>
            </VStack>
          </Card>
        )}

        {/* Quick Actions */}
        <VStack space="sm">
          <Text className="text-sm font-medium text-gray-700">Ações Rápidas</Text>
          {renderQuickActions()}
        </VStack>
      </VStack>

      <Divider />

      {/* Selection Controls */}
      <HStack className="px-6 items-center justify-between">
        <HStack className="items-center" space="sm">
          <Checkbox
            value={
              selectedTeachers.length > 0 && selectedTeachers.length === filteredTeachers.length
            }
            onValueChange={selected => onSelectAll?.(selected)}
          />
          <Text className="text-sm font-medium text-gray-700">
            Selecionar todos ({filteredTeachers.length})
          </Text>
        </HStack>

        {selectedTeachers.length > 0 && (
          <Badge variant="secondary">
            {selectedTeachers.length} selecionado{selectedTeachers.length > 1 ? 's' : ''}
          </Badge>
        )}
      </HStack>

      {/* Teachers List */}
      <Box className="max-h-96">
        <ScrollView showsVerticalScrollIndicator={false}>
          {filteredTeachers.length === 0 ? (
            <Box className="p-8 text-center">
              <Icon as={Users} size="lg" className="text-gray-400 mb-4" />
              <Text className="text-gray-500">
                {searchQuery ||
                filters.status !== 'all' ||
                filters.completionStatus !== 'all' ||
                filters.lastActivity !== 'all'
                  ? 'Nenhum professor encontrado com os filtros aplicados'
                  : 'Nenhum professor disponível'}
              </Text>
            </Box>
          ) : (
            filteredTeachers.map(teacher => (
              <TeacherRow
                key={teacher.id}
                teacher={teacher}
                selected={selectedTeachers.includes(teacher.id)}
                onSelect={selected => onTeacherSelect?.(teacher.id, selected)}
              />
            ))
          )}
        </ScrollView>
      </Box>

      {/* Message Composition Modal */}
      <Modal isOpen={showMessageModal} onClose={() => setShowMessageModal(false)}>
        <Box className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-5/6">
          <VStack space="lg" className="p-6">
            {/* Header */}
            <HStack className="items-center justify-between">
              <VStack>
                <Heading size="lg" className="text-gray-900">
                  Enviar Mensagem
                </Heading>
                <Text className="text-sm text-gray-600">
                  Para {selectedTeachers.length} professor{selectedTeachers.length > 1 ? 'es' : ''}
                </Text>
              </VStack>

              <Pressable onPress={() => setShowMessageModal(false)} className="p-2 -mr-2">
                <Icon as={X} size="md" className="text-gray-500" />
              </Pressable>
            </HStack>

            {/* Template Selection */}
            <FormControl>
              <Text className="text-sm font-medium text-gray-700 mb-2">Modelo de Mensagem</Text>
              <Select selectedValue={messageForm.template} onValueChange={handleTemplateSelect}>
                <Select.Item value="" label="Selecione um modelo..." />
                {MESSAGE_TEMPLATES.map(template => (
                  <Select.Item key={template.id} value={template.id} label={template.name} />
                ))}
              </Select>
            </FormControl>

            {/* Subject */}
            <FormControl>
              <Text className="text-sm font-medium text-gray-700 mb-2">Assunto</Text>
              <Input
                value={messageForm.subject}
                onChangeText={value => setMessageForm(prev => ({ ...prev, subject: value }))}
                placeholder="Assunto da mensagem"
              />
            </FormControl>

            {/* Message */}
            <FormControl>
              <Text className="text-sm font-medium text-gray-700 mb-2">Mensagem</Text>
              <Textarea
                value={messageForm.message}
                onChangeText={value => setMessageForm(prev => ({ ...prev, message: value }))}
                placeholder="Digite sua mensagem aqui..."
                numberOfLines={8}
              />
              <Text className="text-xs text-gray-500 mt-1">
                Use {{ name }} para incluir o nome do professor, {{ profile_link }} para o link do
                perfil
              </Text>
            </FormControl>

            {/* Options */}
            <VStack space="sm">
              <HStack className="items-center justify-between">
                <Text className="text-sm font-medium text-gray-700">Incluir link do perfil</Text>
                <Switch
                  value={messageForm.includeProfileLink}
                  onValueChange={value =>
                    setMessageForm(prev => ({ ...prev, includeProfileLink: value }))
                  }
                />
              </HStack>

              <HStack className="items-center justify-between">
                <Text className="text-sm font-medium text-gray-700">Marcar como urgente</Text>
                <Switch
                  value={messageForm.urgentFlag}
                  onValueChange={value => setMessageForm(prev => ({ ...prev, urgentFlag: value }))}
                />
              </HStack>
            </VStack>

            {/* Error Display */}
            {error && (
              <Box className="p-4 bg-red-50 border border-red-200 rounded-lg">
                <Text className="text-sm text-red-800">{error}</Text>
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
                    as={lastResult.success ? CheckCircle : AlertTriangle}
                    size="sm"
                    className={lastResult.success ? 'text-green-600 mt-1' : 'text-red-600 mt-1'}
                  />
                  <VStack className="flex-1">
                    <Text
                      className={`text-sm font-medium ${
                        lastResult.success ? 'text-green-800' : 'text-red-800'
                      }`}
                    >
                      {lastResult.success ? 'Mensagens enviadas' : 'Envio parcialmente concluído'}
                    </Text>
                    <Text
                      className={`text-xs ${
                        lastResult.success ? 'text-green-700' : 'text-red-700'
                      }`}
                    >
                      {lastResult.successful_count} de {lastResult.total_processed} enviadas com
                      sucesso
                    </Text>
                  </VStack>
                </HStack>
              </Box>
            )}

            {/* Actions */}
            <HStack className="justify-end" space="sm">
              <Button
                variant="outline"
                onPress={() => setShowMessageModal(false)}
                disabled={loading}
              >
                <ButtonText>Cancelar</ButtonText>
              </Button>

              <Button
                onPress={handleSendMessage}
                disabled={loading || !messageForm.message.trim() || selectedTeachers.length === 0}
                className="bg-blue-600"
              >
                {loading ? (
                  <Spinner size="small" />
                ) : (
                  <Icon as={Send} size="sm" className="text-white" />
                )}
                <ButtonText className="text-white ml-2">
                  {loading ? 'Enviando...' : `Enviar para ${selectedTeachers.length}`}
                </ButtonText>
              </Button>
            </HStack>
          </VStack>
        </Box>
      </Modal>
    </VStack>
  );
};

export default TeacherCommunicationPanel;
