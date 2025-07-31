import { 
  TrendingDownIcon, 
  TrendingUpIcon, 
  UsersIcon, 
  CalendarIcon, 
  DollarSignIcon, 
  StarIcon,
  ActivityIcon 
} from 'lucide-react-native';
import React from 'react';

import { TutorAnalytics } from '@/api/tutorApi';
import { Card, CardBody, CardHeader } from '@/components/ui/card';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Skeleton } from '@/components/ui/skeleton';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

interface TutorMetricsCardProps {
  analytics: TutorAnalytics | null;
  isLoading: boolean;
}

interface MetricItemProps {
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: {
    value: number;
    isPositive: boolean;
  } | null;
  icon: React.ComponentType<any>;
  color: string;
  prefix?: string;
  suffix?: string;
}

const MetricItem: React.FC<MetricItemProps> = ({
  title,
  value,
  subtitle,
  trend,
  icon: IconComponent,
  color,
  prefix = '',
  suffix = '',
}) => (
  <VStack space="xs" className="flex-1 min-w-0">
    <HStack space="sm" className="items-center">
      <Icon as={IconComponent} size="sm" className={`text-${color}-600`} />
      <Text className="text-sm font-medium text-gray-600 flex-1">{title}</Text>
    </HStack>
    
    <VStack space="xs">
      <Text className="text-2xl font-bold text-gray-900">
        {prefix}{typeof value === 'number' ? value.toLocaleString() : value}{suffix}
      </Text>
      
      {subtitle && (
        <Text className="text-xs text-gray-500">{subtitle}</Text>
      )}
      
      {trend && (
        <HStack space="xs" className="items-center">
          <Icon
            as={trend.isPositive ? TrendingUpIcon : TrendingDownIcon}
            size="xs"
            className={trend.isPositive ? 'text-green-600' : 'text-red-600'}
          />
          <Text
            className={`text-xs font-medium ${
              trend.isPositive ? 'text-green-600' : 'text-red-600'
            }`}
          >
            {trend.isPositive ? '+' : ''}{trend.value}%
          </Text>
          <Text className="text-xs text-gray-500">vs mês anterior</Text>
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

export const TutorMetricsCard: React.FC<TutorMetricsCardProps> = ({ analytics, isLoading }) => {
  if (isLoading) {
    return (
      <Card variant="elevated" className="bg-white shadow-sm">
        <CardHeader>
          <Skeleton className="h-6 w-40 rounded" />
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

  if (!analytics) {
    return (
      <Card variant="elevated" className="bg-white shadow-sm">
        <CardBody>
          <VStack space="md" className="items-center py-8">
            <Icon as={ActivityIcon} size="xl" className="text-gray-300" />
            <Text className="text-lg font-medium text-gray-600">
              Métricas indisponíveis
            </Text>
            <Text className="text-sm text-gray-500 text-center">
              Não foi possível carregar suas métricas de negócio
            </Text>
          </VStack>
        </CardBody>
      </Card>
    );
  }

  // Calculate monthly trends
  const studentTrend = analytics.monthly_growth ? {
    value: Math.round(analytics.monthly_growth.students * 100) / 100,
    isPositive: analytics.monthly_growth.students >= 0,
  } : null;

  const earningsTrend = analytics.monthly_growth ? {
    value: Math.round(analytics.monthly_growth.earnings * 100) / 100,
    isPositive: analytics.monthly_growth.earnings >= 0,
  } : null;

  const hoursTrend = analytics.monthly_growth ? {
    value: Math.round(analytics.monthly_growth.hours * 100) / 100,
    isPositive: analytics.monthly_growth.hours >= 0,
  } : null;

  return (
    <Card variant="elevated" className="bg-white shadow-sm">
      <CardHeader>
        <Heading size="md" className="text-gray-900">
          Resumo do Negócio
        </Heading>
      </CardHeader>
      <CardBody>
        <VStack space="lg">
          {/* Students and Revenue Row */}
          <HStack space="lg" className="flex-wrap">
            <MetricItem
              title="Estudantes Ativos"
              value={analytics.total_students}
              subtitle="estudantes matriculados"
              trend={studentTrend}
              icon={UsersIcon}
              color="blue"
            />
            
            <MetricItem
              title="Receita Total"
              value={analytics.total_earnings}
              subtitle="valor acumulado"
              trend={earningsTrend}
              icon={DollarSignIcon}
              color="green"
              prefix="€"
            />
          </HStack>

          {/* Hours and Rating Row */}
          <HStack space="lg" className="flex-wrap">
            <MetricItem
              title="Horas Lecionadas"
              value={analytics.total_hours_taught}
              subtitle="total de horas"
              trend={hoursTrend}
              icon={CalendarIcon}
              color="purple"
              suffix="h"
            />
            
            <MetricItem
              title="Avaliação Média"
              value={analytics.average_rating.toFixed(1)}
              subtitle={`${Object.values(analytics.rating_distribution).reduce((a, b) => a + b, 0)} avaliações`}
              trend={
                analytics.average_rating >= 4.5
                  ? { value: Math.round((analytics.average_rating - 4.0) * 25), isPositive: true }
                  : { value: Math.round((4.5 - analytics.average_rating) * 20), isPositive: false }
              }
              icon={StarIcon}
              color="yellow"
              suffix="/5"
            />
          </HStack>

          {/* Performance Metrics Bar */}
          <VStack space="md">
            <Text className="text-sm font-medium text-gray-700">
              Métricas de Performance
            </Text>
            
            <VStack space="sm">
              {/* Completion Rate */}
              <VStack space="xs">
                <HStack className="justify-between items-center">
                  <Text className="text-sm text-gray-600">
                    Taxa de Conclusão
                  </Text>
                  <Text className="text-sm font-semibold text-gray-900">
                    {Math.round(analytics.performance_metrics.completion_rate * 100)}%
                  </Text>
                </HStack>
                <VStack className="w-full bg-gray-200 rounded-full h-2">
                  <VStack
                    className="bg-green-500 h-2 rounded-full"
                    style={{ width: `${Math.round(analytics.performance_metrics.completion_rate * 100)}%` }}
                  />
                </VStack>
              </VStack>

              {/* On Time Rate */}
              <VStack space="xs">
                <HStack className="justify-between items-center">
                  <Text className="text-sm text-gray-600">
                    Pontualidade
                  </Text>
                  <Text className="text-sm font-semibold text-gray-900">
                    {Math.round(analytics.performance_metrics.on_time_rate * 100)}%
                  </Text>
                </HStack>
                <VStack className="w-full bg-gray-200 rounded-full h-2">
                  <VStack
                    className="bg-blue-500 h-2 rounded-full"
                    style={{ width: `${Math.round(analytics.performance_metrics.on_time_rate * 100)}%` }}
                  />
                </VStack>
              </VStack>

              {/* Student Retention */}
              <VStack space="xs">
                <HStack className="justify-between items-center">
                  <Text className="text-sm text-gray-600">
                    Retenção de Estudantes
                  </Text>
                  <Text className="text-sm font-semibold text-gray-900">
                    {Math.round(analytics.performance_metrics.student_retention * 100)}%
                  </Text>
                </HStack>
                <VStack className="w-full bg-gray-200 rounded-full h-2">
                  <VStack
                    className="bg-purple-500 h-2 rounded-full"
                    style={{ width: `${Math.round(analytics.performance_metrics.student_retention * 100)}%` }}
                  />
                </VStack>
              </VStack>
            </VStack>
          </VStack>
        </VStack>
      </CardBody>
    </Card>
  );
};

export default TutorMetricsCard;