import {
  TrendingDown,
  TrendingUp,
  Users,
  GraduationCap,
  BookOpen,
  Activity,
} from 'lucide-react-native';
import React from 'react';

import { SchoolMetrics } from '@/api/userApi';
import { Card, CardBody, CardHeader } from '@/components/ui/card';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Skeleton } from '@/components/ui/skeleton';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

interface MetricsCardProps {
  metrics: SchoolMetrics | null;
  isLoading: boolean;
}

interface MetricItemProps {
  title: string;
  value: number;
  subtitle?: string;
  trend?: {
    value: number;
    isPositive: boolean;
  } | null;
  icon: React.ComponentType<any>;
  color: string;
}

const MetricItem: React.FC<MetricItemProps> = ({
  title,
  value,
  subtitle,
  trend,
  icon: IconComponent,
  color,
}) => (
  <VStack space="xs" className="flex-1 min-w-0">
    <HStack space="sm" className="items-center">
      <Icon as={IconComponent} size="sm" className={`text-${color}-600`} />
      <Text className="text-sm font-medium text-gray-600 flex-1">{title}</Text>
    </HStack>

    <VStack space="xs">
      <Text className="text-2xl font-bold text-gray-900">{value.toLocaleString()}</Text>

      {subtitle && <Text className="text-xs text-gray-500">{subtitle}</Text>}

      {trend && (
        <HStack space="xs" className="items-center">
          <Icon
            as={trend.isPositive ? TrendingUp : TrendingDown}
            size="xs"
            className={trend.isPositive ? 'text-green-600' : 'text-red-600'}
          />
          <Text
            className={`text-xs font-medium ${
              trend.isPositive ? 'text-green-600' : 'text-red-600'
            }`}
          >
            {trend.isPositive ? '+' : ''}
            {trend.value}%
          </Text>
        </HStack>
      )}
    </VStack>
  </VStack>
);

const MetricItemSkeleton: React.FC = () => (
  <VStack space="xs" className="flex-1 min-w-0">
    <HStack space="sm" className="items-center">
      <Skeleton className="h-4 w-4 rounded" />
      <Skeleton className="h-4 w-20 rounded" />
    </HStack>
    <Skeleton className="h-8 w-16 rounded" />
    <Skeleton className="h-3 w-12 rounded" />
  </VStack>
);

const MetricsCard: React.FC<MetricsCardProps> = ({ metrics, isLoading }) => {
  if (isLoading) {
    return (
      <Card variant="elevated" className="bg-white shadow-sm">
        <CardHeader>
          <Skeleton className="h-6 w-32 rounded" />
        </CardHeader>
        <CardBody>
          <VStack space="lg">
            <HStack space="lg" className="flex-wrap">
              <MetricItemSkeleton />
              <MetricItemSkeleton />
            </HStack>
            <HStack space="lg" className="flex-wrap">
              <MetricItemSkeleton />
              <MetricItemSkeleton />
            </HStack>
          </VStack>
        </CardBody>
      </Card>
    );
  }

  if (!metrics) {
    return (
      <Card variant="elevated" className="bg-white shadow-sm">
        <CardBody>
          <VStack space="md" className="items-center py-8">
            <Icon as={Activity} size="xl" className="text-gray-300" />
            <Text className="text-lg font-medium text-gray-600">Métricas indisponíveis</Text>
            <Text className="text-sm text-gray-500 text-center">
              Não foi possível carregar as métricas da escola
            </Text>
          </VStack>
        </CardBody>
      </Card>
    );
  }

  // Calculate trends (using latest data point if available)
  const getLatestTrend = (trendData: Array<{ date: string; count: number; change: number }>) => {
    if (!trendData || trendData.length === 0) return null;
    const latest = trendData[trendData.length - 1];
    return {
      value: Math.abs(latest.change),
      isPositive: latest.change >= 0,
    };
  };

  const studentTrend = getLatestTrend(metrics.student_count.trend.daily);
  const teacherTrend = getLatestTrend(metrics.teacher_count.trend.daily);
  const classTrend = getLatestTrend(metrics.class_metrics.trend.daily);

  return (
    <Card variant="elevated" className="bg-white shadow-sm">
      <CardHeader>
        <Heading size="md" className="text-gray-900">
          Métricas da Escola
        </Heading>
      </CardHeader>
      <CardBody>
        <VStack space="lg">
          {/* Students and Teachers Row */}
          <HStack space="lg" className="flex-wrap">
            <MetricItem
              title="Estudantes"
              value={metrics.student_count.total}
              subtitle={`${metrics.student_count.active} ativos`}
              trend={studentTrend}
              icon={Users}
              color="blue"
            />

            <MetricItem
              title="Professores"
              value={metrics.teacher_count.total}
              subtitle={`${metrics.teacher_count.active} ativos`}
              trend={teacherTrend}
              icon={GraduationCap}
              color="green"
            />
          </HStack>

          {/* Classes and Engagement Row */}
          <HStack space="lg" className="flex-wrap">
            <MetricItem
              title="Aulas Ativas"
              value={metrics.class_metrics.active_classes}
              subtitle={`${metrics.class_metrics.completed_today} hoje`}
              trend={classTrend}
              icon={BookOpen}
              color="purple"
            />

            <MetricItem
              title="Taxa de Aceitação"
              value={Math.round(metrics.engagement_metrics.acceptance_rate * 100)}
              subtitle={`${metrics.engagement_metrics.invitations_sent} convites`}
              trend={
                metrics.engagement_metrics.acceptance_rate >= 0.7
                  ? {
                      value: Math.round(metrics.engagement_metrics.acceptance_rate * 100),
                      isPositive: true,
                    }
                  : {
                      value: Math.round((1 - metrics.engagement_metrics.acceptance_rate) * 100),
                      isPositive: false,
                    }
              }
              icon={Activity}
              color="orange"
            />
          </HStack>

          {/* Completion Rate Bar */}
          {metrics.class_metrics.completion_rate > 0 && (
            <VStack space="xs">
              <HStack className="justify-between items-center">
                <Text className="text-sm font-medium text-gray-600">Taxa de Conclusão</Text>
                <Text className="text-sm font-bold text-gray-900">
                  {Math.round(metrics.class_metrics.completion_rate * 100)}%
                </Text>
              </HStack>
              <VStack className="w-full bg-gray-200 rounded-full h-2">
                <VStack
                  className="bg-blue-600 h-2 rounded-full"
                  style={{ width: `${Math.round(metrics.class_metrics.completion_rate * 100)}%` }}
                />
              </VStack>
            </VStack>
          )}
        </VStack>
      </CardBody>
    </Card>
  );
};

export { MetricsCard };
export default MetricsCard;
