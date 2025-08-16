import {
  TrendingUp,
  TrendingDown,
  Users,
  CheckCircle,
  AlertTriangle,
  BarChart3,
  PieChart,
  RefreshCw,
  Info,
  Award,
  Target,
  AlertCircle,
} from 'lucide-react-native';
import React, { useState, useMemo } from 'react';

import { CircularProgress } from './ProfileCompletionIndicator';

import { TeacherAnalytics } from '@/api/userApi';
import { Badge } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Pressable } from '@/components/ui/pressable';
import { Progress } from '@/components/ui/progress';
import { ScrollView } from '@/components/ui/scroll-view';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { useTeacherAnalytics } from '@/hooks/useTeacherAnalytics';

interface TeacherAnalyticsDashboardProps {
  schoolId?: number;
  onRefresh?: () => void;
  onViewTeacher?: (teacherId: number) => void;
}

// Color constants
const COLORS = {
  primary: '#156082',
  success: '#16A34A',
  warning: '#D97706',
  danger: '#DC2626',
  info: '#2563EB',
  gray: {
    50: '#F9FAFB',
    100: '#F3F4F6',
    200: '#E5E7EB',
    300: '#D1D5DB',
    500: '#6B7280',
    600: '#4B5563',
    700: '#374151',
    900: '#111827',
  },
};

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: any;
  trend?: 'up' | 'down' | 'stable';
  trendValue?: string;
  color?: string;
  onPress?: () => void;
}

const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  icon,
  trend,
  trendValue,
  color = COLORS.primary,
  onPress,
}) => {
  const getTrendIcon = () => {
    if (trend === 'up') return TrendingUp;
    if (trend === 'down') return TrendingDown;
    return null;
  };

  const getTrendColor = () => {
    if (trend === 'up') return COLORS.success;
    if (trend === 'down') return COLORS.danger;
    return COLORS.gray[500];
  };

  const TrendIcon = getTrendIcon();

  return (
    <Card className="p-4 bg-white">
      <Pressable onPress={onPress} disabled={!onPress}>
        <VStack space="sm">
          <HStack className="items-center justify-between">
            <Icon as={icon} size="md" style={{ color }} />
            {TrendIcon && trendValue && (
              <HStack className="items-center" space="xs">
                <Icon as={TrendIcon} size="xs" style={{ color: getTrendColor() }} />
                <Text className="text-xs font-medium" style={{ color: getTrendColor() }}>
                  {trendValue}
                </Text>
              </HStack>
            )}
          </HStack>

          <VStack space="xs">
            <Text className="text-2xl font-bold text-gray-900">{value}</Text>
            <Text className="text-sm font-medium text-gray-700">{title}</Text>
            {subtitle && <Text className="text-xs text-gray-500">{subtitle}</Text>}
          </VStack>
        </VStack>
      </Pressable>
    </Card>
  );
};

interface CompletionDistributionChartProps {
  distribution: Record<string, number>;
  total: number;
}

const CompletionDistributionChart: React.FC<CompletionDistributionChartProps> = ({
  distribution,
  total,
}) => {
  if (total === 0) {
    return (
      <Box className="h-40 justify-center items-center">
        <Text className="text-gray-500">Nenhum dado disponível</Text>
      </Box>
    );
  }

  const segments = [
    { range: '0-25%', count: distribution['0-25%'] || 0, color: COLORS.danger },
    { range: '26-50%', count: distribution['26-50%'] || 0, color: COLORS.warning },
    { range: '51-75%', count: distribution['51-75%'] || 0, color: COLORS.info },
    { range: '76-100%', count: distribution['76-100%'] || 0, color: COLORS.success },
  ];

  return (
    <VStack space="md">
      {segments.map(segment => {
        const percentage = total > 0 ? (segment.count / total) * 100 : 0;

        return (
          <VStack key={segment.range} space="xs">
            <HStack className="items-center justify-between">
              <HStack className="items-center" space="xs">
                <Box className="w-3 h-3 rounded-full" style={{ backgroundColor: segment.color }} />
                <Text className="text-sm font-medium text-gray-700">{segment.range}</Text>
              </HStack>
              <Text className="text-sm text-gray-600">
                {segment.count} ({Math.round(percentage)}%)
              </Text>
            </HStack>
            <Progress
              value={percentage}
              className="h-2"
              style={{ backgroundColor: `${segment.color}20` }}
            />
          </VStack>
        );
      })}
    </VStack>
  );
};

interface TopMissingFieldsProps {
  fields: Array<{ field: string; count: number; percentage: number }>;
  onFieldClick?: (field: string) => void;
}

const TopMissingFields: React.FC<TopMissingFieldsProps> = ({ fields, onFieldClick }) => {
  const getFieldDisplayName = (field: string): string => {
    const fieldNames: Record<string, string> = {
      bio: 'Biografia',
      specialty: 'Especialidade',
      education: 'Formação',
      hourly_rate: 'Taxa Horária',
      phone_number: 'Telefone',
      address: 'Endereço',
      availability: 'Disponibilidade',
      teaching_subjects: 'Disciplinas',
      calendar_iframe: 'Calendário',
    };
    return fieldNames[field] || field;
  };

  if (fields.length === 0) {
    return (
      <Box className="p-4 text-center">
        <Icon as={CheckCircle} size="lg" className="text-green-500 mb-2" />
        <Text className="text-sm text-gray-500">Todos os perfis estão completos!</Text>
      </Box>
    );
  }

  return (
    <VStack space="sm">
      {fields.map((field, index) => (
        <Pressable
          key={field.field}
          onPress={() => onFieldClick?.(field.field)}
          className="p-3 bg-gray-50 rounded-lg border border-gray-200"
        >
          <HStack className="items-center justify-between">
            <VStack className="flex-1">
              <Text className="font-medium text-gray-900">{getFieldDisplayName(field.field)}</Text>
              <Text className="text-xs text-gray-500">
                {field.count} professores ({field.percentage}%)
              </Text>
            </VStack>

            <HStack className="items-center" space="sm">
              <Box className="w-12">
                <Progress value={field.percentage} className="h-2" />
              </Box>
              <Badge variant={field.percentage > 50 ? 'destructive' : 'secondary'} size="sm">
                {field.percentage}%
              </Badge>
            </HStack>
          </HStack>
        </Pressable>
      ))}
    </VStack>
  );
};

interface TeachersNeedingAttentionProps {
  teachers: Array<{
    teacher_id: number;
    name: string;
    completion_percentage: number;
    missing_critical: string[];
  }>;
  onViewTeacher?: (teacherId: number) => void;
}

const TeachersNeedingAttention: React.FC<TeachersNeedingAttentionProps> = ({
  teachers,
  onViewTeacher,
}) => {
  if (teachers.length === 0) {
    return (
      <Box className="p-4 text-center">
        <Icon as={Award} size="lg" className="text-green-500 mb-2" />
        <Text className="text-sm text-gray-500">Todos os professores estão em boa situação!</Text>
      </Box>
    );
  }

  return (
    <VStack space="sm">
      {teachers.slice(0, 5).map(teacher => (
        <Pressable
          key={teacher.teacher_id}
          onPress={() => onViewTeacher?.(teacher.teacher_id)}
          className="p-3 bg-red-50 border border-red-200 rounded-lg"
        >
          <HStack className="items-center justify-between">
            <VStack className="flex-1">
              <Text className="font-medium text-gray-900">{teacher.name}</Text>
              <Text className="text-xs text-red-700">
                {teacher.missing_critical.length} campo
                {teacher.missing_critical.length > 1 ? 's' : ''} crítico
                {teacher.missing_critical.length > 1 ? 's' : ''} em falta
              </Text>
            </VStack>

            <HStack className="items-center" space="sm">
              <CircularProgress
                percentage={teacher.completion_percentage}
                size={30}
                strokeWidth={3}
                color={teacher.completion_percentage < 30 ? COLORS.danger : COLORS.warning}
                showPercentage={false}
              />
              <Icon as={AlertTriangle} size="sm" className="text-red-500" />
            </HStack>
          </HStack>
        </Pressable>
      ))}

      {teachers.length > 5 && (
        <Text className="text-xs text-gray-500 text-center">
          +{teachers.length - 5} mais professores precisam de atenção
        </Text>
      )}
    </VStack>
  );
};

export const TeacherAnalyticsDashboard: React.FC<TeacherAnalyticsDashboardProps> = ({
  schoolId,
  onRefresh,
  onViewTeacher,
}) => {
  const [selectedTimeframe, setSelectedTimeframe] = useState<'week' | 'month' | 'quarter'>('month');

  const {
    analytics,
    loading,
    error,
    lastUpdated,
    refresh,
    getCompletionTrend,
    getHighPriorityIssues,
    getTopMissingFields,
    getCompletionDistributionPercentages,
    isHealthy,
    needsAttention,
    getCriticalTeachersCount,
    getAverageCompletionGrade,
  } = useTeacherAnalytics({
    schoolId,
    autoFetch: true,
    refreshInterval: 5 * 60 * 1000, // Refresh every 5 minutes
  });

  const handleRefresh = async () => {
    await refresh();
    onRefresh?.();
  };

  // Calculate derived metrics
  const completionTrend = useMemo(() => getCompletionTrend(), [analytics]);
  const priorityIssues = useMemo(() => getHighPriorityIssues(), [analytics]);
  const topMissingFields = useMemo(() => getTopMissingFields(5), [analytics]);
  const distributionPercentages = useMemo(
    () => getCompletionDistributionPercentages(),
    [analytics],
  );
  const healthStatus = useMemo(() => isHealthy(), [analytics]);
  const attentionNeeded = useMemo(() => needsAttention(), [analytics]);
  const criticalCount = useMemo(() => getCriticalTeachersCount(), [analytics]);
  const completionGrade = useMemo(() => getAverageCompletionGrade(), [analytics]);

  if (loading && !analytics) {
    return (
      <Box className="p-6">
        <VStack className="items-center justify-center" space="md">
          <Spinner size="large" />
          <Text className="text-gray-500">Carregando análises...</Text>
        </VStack>
      </Box>
    );
  }

  if (error) {
    return (
      <Box className="p-6">
        <VStack className="items-center" space="md">
          <Icon as={AlertCircle} size="xl" className="text-red-500" />
          <VStack className="items-center" space="sm">
            <Text className="font-medium text-gray-900">Erro ao carregar análises</Text>
            <Text className="text-sm text-gray-600 text-center">{error}</Text>
          </VStack>
          <Button onPress={handleRefresh} variant="outline">
            <Icon as={RefreshCw} size="sm" />
            <ButtonText className="ml-2">Tentar novamente</ButtonText>
          </Button>
        </VStack>
      </Box>
    );
  }

  if (!analytics) {
    return (
      <Box className="p-6">
        <Text className="text-gray-500 text-center">Nenhum dado de análise disponível</Text>
      </Box>
    );
  }

  return (
    <ScrollView className="flex-1 bg-gray-50" showsVerticalScrollIndicator={false}>
      <VStack space="lg" className="p-6">
        {/* Header */}
        <HStack className="items-center justify-between">
          <VStack>
            <Heading size="lg" className="text-gray-900">
              Análise de Professores
            </Heading>
            <Text className="text-sm text-gray-600">
              Última atualização: {lastUpdated ? lastUpdated.toLocaleTimeString('pt-BR') : 'Nunca'}
            </Text>
          </VStack>

          <Button variant="outline" size="sm" onPress={handleRefresh} disabled={loading}>
            {loading ? <Spinner size="small" /> : <Icon as={RefreshCw} size="sm" />}
            <ButtonText className="ml-2">Atualizar</ButtonText>
          </Button>
        </HStack>

        {/* Health Status Alert */}
        {attentionNeeded && (
          <Box className="p-4 bg-red-50 border border-red-200 rounded-lg">
            <HStack space="sm" className="items-start">
              <Icon as={AlertTriangle} size="sm" className="text-red-600 mt-1" />
              <VStack className="flex-1">
                <Text className="text-sm font-medium text-red-800">Atenção necessária</Text>
                <Text className="text-xs text-red-700">
                  Os perfis dos professores precisam de melhorias urgentes
                </Text>
              </VStack>
            </HStack>
          </Box>
        )}

        {/* Overview Metrics */}
        <VStack space="md">
          <Text className="text-lg font-semibold text-gray-900">Visão Geral</Text>

          <HStack space="md" className="flex-wrap">
            <Box className="flex-1 min-w-40">
              <MetricCard
                title="Total de Professores"
                value={analytics.total_teachers}
                icon={Users}
                color={COLORS.primary}
                subtitle={`${analytics.complete_profiles} completos`}
              />
            </Box>

            <Box className="flex-1 min-w-40">
              <MetricCard
                title="Completude Média"
                value={`${Math.round(analytics.average_completion)}%`}
                icon={Target}
                color={
                  completionGrade === 'A' || completionGrade === 'B'
                    ? COLORS.success
                    : completionGrade === 'C'
                      ? COLORS.warning
                      : COLORS.danger
                }
                subtitle={`Nota: ${completionGrade}`}
                trend={
                  completionTrend === 'improving'
                    ? 'up'
                    : completionTrend === 'declining'
                      ? 'down'
                      : 'stable'
                }
                trendValue={
                  completionTrend === 'improving'
                    ? 'Melhorando'
                    : completionTrend === 'declining'
                      ? 'Piorando'
                      : 'Estável'
                }
              />
            </Box>
          </HStack>

          <HStack space="md">
            <Box className="flex-1">
              <MetricCard
                title="Perfis Completos"
                value={analytics.complete_profiles}
                icon={CheckCircle}
                color={COLORS.success}
                subtitle={`${Math.round(
                  (analytics.complete_profiles / analytics.total_teachers) * 100,
                )}% do total`}
              />
            </Box>

            <Box className="flex-1">
              <MetricCard
                title="Precisam Atenção"
                value={criticalCount}
                icon={AlertTriangle}
                color={criticalCount > 0 ? COLORS.danger : COLORS.success}
                subtitle={criticalCount > 0 ? 'Ação urgente' : 'Tudo bem'}
                onPress={() => {
                  // TODO: Navigate to filtered view of critical teachers
                  if (__DEV__) {
                    console.log('View critical teachers');
                  }
                }}
              />
            </Box>
          </HStack>
        </VStack>

        {/* Distribution Chart */}
        <Card className="p-6 bg-white">
          <VStack space="lg">
            <HStack className="items-center justify-between">
              <Heading size="md" className="text-gray-900">
                Distribuição de Completude
              </Heading>
              <Icon as={PieChart} size="md" className="text-gray-500" />
            </HStack>

            <CompletionDistributionChart
              distribution={analytics.completion_distribution}
              total={analytics.total_teachers}
            />
          </VStack>
        </Card>

        {/* Top Missing Fields */}
        <Card className="p-6 bg-white">
          <VStack space="lg">
            <HStack className="items-center justify-between">
              <Heading size="md" className="text-gray-900">
                Campos Mais Ausentes
              </Heading>
              <Icon as={BarChart3} size="md" className="text-gray-500" />
            </HStack>

            <TopMissingFields
              fields={topMissingFields}
              onFieldClick={field => {
                // TODO: Navigate to teachers filtered by missing field
                if (__DEV__) {
                  console.log('Filter by missing field:', field);
                }
              }}
            />
          </VStack>
        </Card>

        {/* Teachers Needing Attention */}
        {analytics.profile_completion_stats?.needs_attention && (
          <Card className="p-6 bg-white">
            <VStack space="lg">
              <HStack className="items-center justify-between">
                <Heading size="md" className="text-gray-900">
                  Professores que Precisam de Atenção
                </Heading>
                <Badge variant="destructive" size="sm">
                  {analytics.profile_completion_stats.needs_attention.length}
                </Badge>
              </HStack>

              <TeachersNeedingAttention
                teachers={analytics.profile_completion_stats.needs_attention}
                onViewTeacher={onViewTeacher}
              />
            </VStack>
          </Card>
        )}

        {/* Priority Issues */}
        {priorityIssues.length > 0 && (
          <Card className="p-6 bg-white">
            <VStack space="lg">
              <HStack className="items-center justify-between">
                <Heading size="md" className="text-gray-900">
                  Questões Prioritárias
                </Heading>
                <Icon as={Info} size="md" className="text-amber-500" />
              </HStack>

              <VStack space="sm">
                {priorityIssues.map((issue, index) => (
                  <Box key={index} className="p-3 bg-amber-50 border border-amber-200 rounded-lg">
                    <HStack space="sm" className="items-start">
                      <Icon as={AlertTriangle} size="sm" className="text-amber-600 mt-1" />
                      <Text className="text-sm text-amber-800 flex-1">{issue}</Text>
                    </HStack>
                  </Box>
                ))}
              </VStack>
            </VStack>
          </Card>
        )}

        {/* Recommendations */}
        <Card className="p-6 bg-white">
          <VStack space="lg">
            <Heading size="md" className="text-gray-900">
              Recomendações
            </Heading>

            <VStack space="sm">
              {healthStatus ? (
                <Box className="p-3 bg-green-50 border border-green-200 rounded-lg">
                  <HStack space="sm" className="items-center">
                    <Icon as={CheckCircle} size="sm" className="text-green-600" />
                    <Text className="text-sm text-green-800">
                      Excelente! Os perfis dos professores estão em ótima forma.
                    </Text>
                  </HStack>
                </Box>
              ) : (
                <>
                  {analytics.average_completion < 70 && (
                    <Box className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                      <HStack space="sm" className="items-start">
                        <Icon as={Info} size="sm" className="text-blue-600 mt-1" />
                        <Text className="text-sm text-blue-800">
                          Considere enviar lembretes para professores com perfis incompletos
                        </Text>
                      </HStack>
                    </Box>
                  )}

                  {criticalCount > 0 && (
                    <Box className="p-3 bg-red-50 border border-red-200 rounded-lg">
                      <HStack space="sm" className="items-start">
                        <Icon as={AlertTriangle} size="sm" className="text-red-600 mt-1" />
                        <Text className="text-sm text-red-800">
                          Entre em contato com professores que têm campos críticos em falta
                        </Text>
                      </HStack>
                    </Box>
                  )}

                  <Box className="p-3 bg-gray-50 border border-gray-200 rounded-lg">
                    <HStack space="sm" className="items-start">
                      <Icon as={Target} size="sm" className="text-gray-600 mt-1" />
                      <Text className="text-sm text-gray-700">
                        Use ferramentas de mensagem em massa para comunicar com múltiplos
                        professores
                      </Text>
                    </HStack>
                  </Box>
                </>
              )}
            </VStack>
          </VStack>
        </Card>
      </VStack>
    </ScrollView>
  );
};

export default TeacherAnalyticsDashboard;
