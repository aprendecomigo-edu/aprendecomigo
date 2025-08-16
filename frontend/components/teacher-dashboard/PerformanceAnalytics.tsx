import {
  TrendingUpIcon,
  TrendingDownIcon,
  DollarSignIcon,
  ClockIcon,
  UsersIcon,
  AwardIcon,
  BarChart3Icon,
  PieChartIcon,
  CalendarIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  MinusIcon,
} from 'lucide-react-native';
import React, { useMemo } from 'react';

import type { ProgressMetrics, EarningsData, QuickStats } from '@/api/teacherApi';
import { Badge, BadgeText } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Card, CardBody, CardHeader } from '@/components/ui/card';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

interface PerformanceAnalyticsProps {
  progressMetrics: ProgressMetrics;
  earnings: EarningsData;
  quickStats: QuickStats;
  onViewDetailedAnalytics: () => void;
  isLoading?: boolean;
}

interface MetricCardProps {
  title: string;
  value: string | number;
  change?: number;
  changeLabel?: string;
  icon: any;
  color: string;
  bgColor: string;
  formatValue?: (value: number) => string;
}

const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  change,
  changeLabel,
  icon,
  color,
  bgColor,
  formatValue,
}) => {
  const displayValue = typeof value === 'number' && formatValue ? formatValue(value) : value;

  const getTrendIcon = (change?: number) => {
    if (!change) return MinusIcon;
    return change > 0 ? ArrowUpIcon : change < 0 ? ArrowDownIcon : MinusIcon;
  };

  const getTrendColor = (change?: number) => {
    if (!change) return 'text-gray-500';
    return change > 0 ? 'text-green-600' : change < 0 ? 'text-red-600' : 'text-gray-500';
  };

  return (
    <Card variant="elevated" className="bg-white shadow-sm">
      <CardBody>
        <VStack space="sm">
          <HStack className="justify-between items-start">
            <VStack className={`${bgColor} rounded-full p-2 items-center justify-center`}>
              <Icon as={icon} size="sm" className={color} />
            </VStack>
            {change !== undefined && (
              <HStack space="xs" className="items-center">
                <Icon as={getTrendIcon(change)} size="xs" className={getTrendColor(change)} />
                <Text className={`text-xs font-medium ${getTrendColor(change)}`}>
                  {Math.abs(change)}%
                </Text>
              </HStack>
            )}
          </HStack>

          <VStack space="xs">
            <Text className="text-2xl font-bold text-gray-900">{displayValue}</Text>
            <Text className="text-sm text-gray-600">{title}</Text>
            {changeLabel && <Text className="text-xs text-gray-500">{changeLabel}</Text>}
          </VStack>
        </VStack>
      </CardBody>
    </Card>
  );
};

const ProgressBar: React.FC<{
  label: string;
  value: number;
  maxValue: number;
  color: string;
  showPercentage?: boolean;
}> = ({ label, value, maxValue, color, showPercentage = true }) => {
  const percentage = Math.min((value / maxValue) * 100, 100);

  return (
    <VStack space="xs">
      <HStack className="justify-between items-center">
        <Text className="text-sm text-gray-700">{label}</Text>
        {showPercentage && (
          <Text className="text-sm font-semibold text-gray-900">{Math.round(percentage)}%</Text>
        )}
      </HStack>
      <Box className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
        <Box className={`h-full rounded-full ${color}`} style={{ width: `${percentage}%` }} />
      </Box>
      <HStack className="justify-between">
        <Text className="text-xs text-gray-500">{value}</Text>
        <Text className="text-xs text-gray-500">{maxValue}</Text>
      </HStack>
    </VStack>
  );
};

const EarningsBreakdown: React.FC<{ earnings: EarningsData }> = ({ earnings }) => {
  const monthlyChange = useMemo(() => {
    if (earnings.last_month_total === 0) return 0;
    return (
      ((earnings.current_month_total - earnings.last_month_total) / earnings.last_month_total) * 100
    );
  }, [earnings]);

  return (
    <Card variant="elevated" className="bg-white shadow-sm">
      <CardHeader>
        <HStack className="justify-between items-center">
          <Heading size="md" className="text-gray-900">
            Rendimentos
          </Heading>
          <Icon as={DollarSignIcon} size="sm" className="text-green-600" />
        </HStack>
      </CardHeader>
      <CardBody>
        <VStack space="md">
          {/* Current Month */}
          <VStack space="sm">
            <HStack className="justify-between items-center">
              <Text className="text-sm text-gray-600">Este Mês</Text>
              <HStack space="xs" className="items-center">
                <Icon
                  as={
                    monthlyChange > 0
                      ? TrendingUpIcon
                      : monthlyChange < 0
                        ? TrendingDownIcon
                        : MinusIcon
                  }
                  size="xs"
                  className={
                    monthlyChange > 0
                      ? 'text-green-600'
                      : monthlyChange < 0
                        ? 'text-red-600'
                        : 'text-gray-500'
                  }
                />
                <Text
                  className={`text-xs font-medium ${
                    monthlyChange > 0
                      ? 'text-green-600'
                      : monthlyChange < 0
                        ? 'text-red-600'
                        : 'text-gray-500'
                  }`}
                >
                  {Math.abs(Math.round(monthlyChange))}%
                </Text>
              </HStack>
            </HStack>
            <Text className="text-2xl font-bold text-gray-900">
              €{earnings.current_month_total.toFixed(2)}
            </Text>
          </VStack>

          {/* Comparison */}
          <VStack space="xs">
            <HStack className="justify-between">
              <Text className="text-sm text-gray-500">Mês Anterior</Text>
              <Text className="text-sm text-gray-700">€{earnings.last_month_total.toFixed(2)}</Text>
            </HStack>
            <HStack className="justify-between">
              <Text className="text-sm text-gray-500">Pendente</Text>
              <Text className="text-sm font-medium text-orange-600">
                €{earnings.pending_amount.toFixed(2)}
              </Text>
            </HStack>
            <HStack className="justify-between">
              <Text className="text-sm text-gray-500">Horas Totais</Text>
              <Text className="text-sm text-gray-700">{earnings.total_hours_taught}h</Text>
            </HStack>
          </VStack>

          {/* Recent Payments */}
          {earnings.recent_payments && earnings.recent_payments.length > 0 && (
            <VStack space="sm">
              <Text className="text-sm font-medium text-gray-900">Pagamentos Recentes</Text>
              {earnings.recent_payments.slice(0, 3).map((payment, index) => (
                <HStack key={payment.id || index} className="justify-between items-center py-1">
                  <VStack>
                    <Text className="text-sm text-gray-700">€{payment.amount.toFixed(2)}</Text>
                    <Text className="text-xs text-gray-500">
                      {new Date(payment.date).toLocaleDateString('pt-PT')}
                    </Text>
                  </VStack>
                  <VStack className="items-end">
                    <Text className="text-xs text-gray-600">{payment.hours}h</Text>
                    <Text className="text-xs text-gray-500" numberOfLines={1}>
                      {payment.session_info}
                    </Text>
                  </VStack>
                </HStack>
              ))}
            </VStack>
          )}
        </VStack>
      </CardBody>
    </Card>
  );
};

const PerformanceAnalytics: React.FC<PerformanceAnalyticsProps> = ({
  progressMetrics,
  earnings,
  quickStats,
  onViewDetailedAnalytics,
  isLoading = false,
}) => {
  // Calculate derived metrics
  const metrics = useMemo(() => {
    const avgSessionsPerWeek = quickStats.sessions_this_week;
    const efficiencyScore = Math.round(
      (quickStats.completion_rate + progressMetrics.average_student_progress) / 2,
    );

    return {
      avgSessionsPerWeek,
      efficiencyScore,
      improvementRate: progressMetrics.completion_rate_trend,
    };
  }, [progressMetrics, quickStats]);

  const formatCurrency = (value: number) => `€${value.toFixed(0)}`;
  const formatPercentage = (value: number) => `${Math.round(value)}%`;
  const formatHours = (value: number) => `${value}h`;

  return (
    <VStack space="md">
      {/* Key Performance Metrics */}
      <Card variant="elevated" className="bg-white shadow-sm">
        <CardHeader>
          <HStack className="justify-between items-center">
            <Heading size="md" className="text-gray-900">
              Métricas de Desempenho
            </Heading>
            <Button size="sm" variant="outline" onPress={onViewDetailedAnalytics}>
              <Icon as={BarChart3Icon} size="xs" className="text-blue-600 mr-1" />
              <ButtonText className="text-blue-600">Ver Detalhes</ButtonText>
            </Button>
          </HStack>
        </CardHeader>
        <CardBody>
          <VStack space="md">
            {/* Metrics Grid */}
            <VStack space="sm">
              <HStack space="sm">
                <Box className="flex-1">
                  <MetricCard
                    title="Estudantes Totais"
                    value={quickStats.total_students}
                    icon={UsersIcon}
                    color="text-blue-600"
                    bgColor="bg-blue-100"
                  />
                </Box>
                <Box className="flex-1">
                  <MetricCard
                    title="Taxa de Conclusão"
                    value={quickStats.completion_rate}
                    change={progressMetrics.completion_rate_trend}
                    changeLabel="vs mês anterior"
                    icon={AwardIcon}
                    color="text-green-600"
                    bgColor="bg-green-100"
                    formatValue={formatPercentage}
                  />
                </Box>
              </HStack>

              <HStack space="sm">
                <Box className="flex-1">
                  <MetricCard
                    title="Sessões Esta Semana"
                    value={quickStats.sessions_this_week}
                    icon={CalendarIcon}
                    color="text-purple-600"
                    bgColor="bg-purple-100"
                  />
                </Box>
                <Box className="flex-1">
                  <MetricCard
                    title="Avaliação Média"
                    value={quickStats.average_rating || 0}
                    icon={TrendingUpIcon}
                    color="text-yellow-600"
                    bgColor="bg-yellow-100"
                    formatValue={value => (value > 0 ? `${value.toFixed(1)}★` : 'N/A')}
                  />
                </Box>
              </HStack>
            </VStack>

            {/* Progress Bars */}
            <VStack space="sm">
              <ProgressBar
                label="Progresso Médio dos Estudantes"
                value={progressMetrics.average_student_progress}
                maxValue={100}
                color="bg-green-500"
              />

              <ProgressBar
                label="Estudantes que Melhoraram Este Mês"
                value={progressMetrics.students_improved_this_month}
                maxValue={quickStats.total_students}
                color="bg-blue-500"
                showPercentage={false}
              />

              <ProgressBar
                label="Avaliações Realizadas"
                value={progressMetrics.total_assessments_given}
                maxValue={Math.max(progressMetrics.total_assessments_given * 1.2, 50)}
                color="bg-purple-500"
                showPercentage={false}
              />
            </VStack>
          </VStack>
        </CardBody>
      </Card>

      {/* Earnings Section */}
      <EarningsBreakdown earnings={earnings} />

      {/* Performance Insights */}
      <Card
        variant="elevated"
        className="bg-gradient-to-r from-blue-50 to-purple-50 border-l-4 border-blue-500"
      >
        <CardBody>
          <VStack space="sm">
            <HStack space="sm" className="items-center">
              <Icon as={TrendingUpIcon} size="md" className="text-blue-600" />
              <Text className="text-lg font-semibold text-gray-900">Insights de Performance</Text>
            </HStack>

            <VStack space="xs">
              {quickStats.completion_rate >= 80 && (
                <HStack space="sm" className="items-center">
                  <Icon as={AwardIcon} size="xs" className="text-green-600" />
                  <Text className="text-sm text-gray-700">
                    Excelente taxa de conclusão! Seus estudantes estão muito engajados.
                  </Text>
                </HStack>
              )}

              {progressMetrics.students_improved_this_month >= quickStats.total_students * 0.7 && (
                <HStack space="sm" className="items-center">
                  <Icon as={TrendingUpIcon} size="xs" className="text-blue-600" />
                  <Text className="text-sm text-gray-700">
                    Ótimo impacto:{' '}
                    {Math.round(
                      (progressMetrics.students_improved_this_month / quickStats.total_students) *
                        100,
                    )}
                    % dos estudantes melhoraram este mês.
                  </Text>
                </HStack>
              )}

              {earnings.current_month_total > earnings.last_month_total && (
                <HStack space="sm" className="items-center">
                  <Icon as={DollarSignIcon} size="xs" className="text-green-600" />
                  <Text className="text-sm text-gray-700">
                    Rendimentos em crescimento: +
                    {Math.round(
                      ((earnings.current_month_total - earnings.last_month_total) /
                        earnings.last_month_total) *
                        100,
                    )}
                    % este mês.
                  </Text>
                </HStack>
              )}

              {quickStats.sessions_this_week < 5 && quickStats.total_students > 10 && (
                <HStack space="sm" className="items-center">
                  <Icon as={ClockIcon} size="xs" className="text-orange-600" />
                  <Text className="text-sm text-gray-700">
                    Considere agendar mais sessões para maximizar o impacto nos estudantes.
                  </Text>
                </HStack>
              )}
            </VStack>
          </VStack>
        </CardBody>
      </Card>
    </VStack>
  );
};

export default PerformanceAnalytics;
