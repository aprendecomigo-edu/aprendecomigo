import {
  Users,
  GraduationCap,
  BookOpen,
  TrendingUp,
  Clock,
  Award,
  Target,
  Activity,
} from 'lucide-react-native';
import React from 'react';

import { Box } from '@/components/ui/box';
import { Card, CardBody, CardHeader } from '@/components/ui/card';
import { Grid } from '@/components/ui/grid';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Progress } from '@/components/ui/progress';
import { Skeleton } from '@/components/ui/skeleton';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

interface SchoolStatsData {
  total_students: number;
  total_teachers: number;
  active_sessions_count: number;
  average_rating?: number;
  total_hours_taught?: number;
  courses_offered?: number;
  success_rate?: number;
  completion_rate?: number;
  student_satisfaction?: number;
  teacher_retention_rate?: number;
  monthly_growth?: number;
  active_courses?: number;
}

interface SchoolStatsProps {
  stats: SchoolStatsData;
  loading?: boolean;
  compact?: boolean;
  showGrowthMetrics?: boolean;
  showRatings?: boolean;
  className?: string;
}

export const SchoolStats: React.FC<SchoolStatsProps> = ({
  stats,
  loading = false,
  compact = false,
  showGrowthMetrics = true,
  showRatings = true,
  className = '',
}) => {
  const formatNumber = (num: number) => {
    if (num >= 1000000) {
      return `${(num / 1000000).toFixed(1)}M`;
    } else if (num >= 1000) {
      return `${(num / 1000).toFixed(1)}K`;
    }
    return num.toString();
  };

  const formatHours = (hours: number) => {
    if (hours >= 1000) {
      return `${(hours / 1000).toFixed(1)}K`;
    }
    return hours.toString();
  };

  const formatPercentage = (rate: number) => {
    return `${Math.round(rate * 100)}%`;
  };

  const getStatColor = (value: number, type: 'rating' | 'percentage' | 'growth') => {
    switch (type) {
      case 'rating':
        if (value >= 4.5) return 'text-green-600 bg-green-50';
        if (value >= 4.0) return 'text-blue-600 bg-blue-50';
        if (value >= 3.5) return 'text-yellow-600 bg-yellow-50';
        return 'text-red-600 bg-red-50';
      case 'percentage':
        if (value >= 0.9) return 'text-green-600 bg-green-50';
        if (value >= 0.8) return 'text-blue-600 bg-blue-50';
        if (value >= 0.7) return 'text-yellow-600 bg-yellow-50';
        return 'text-red-600 bg-red-50';
      case 'growth':
        if (value > 0) return 'text-green-600 bg-green-50';
        if (value === 0) return 'text-gray-600 bg-gray-50';
        return 'text-red-600 bg-red-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  if (loading) {
    return (
      <Card className={`${className} w-full`}>
        <CardHeader>
          <Skeleton className="w-32 h-6 rounded" />
        </CardHeader>
        <CardBody>
          <Grid className={compact ? 'grid-cols-2 gap-3' : 'grid-cols-2 lg:grid-cols-4 gap-4'}>
            {[1, 2, 3, 4].map(i => (
              <Box key={i} className="text-center p-3 bg-gray-50 rounded-lg">
                <Skeleton className="w-8 h-8 rounded mx-auto mb-2" />
                <Skeleton className="w-12 h-6 rounded mx-auto mb-1" />
                <Skeleton className="w-16 h-3 rounded mx-auto" />
              </Box>
            ))}
          </Grid>
        </CardBody>
      </Card>
    );
  }

  // Compact version for mobile or small spaces
  if (compact) {
    return (
      <Card className={`${className} w-full`}>
        <CardBody>
          <Grid className="grid-cols-2 gap-3">
            {/* Essential Stats */}
            <Box className="text-center p-3 bg-blue-50 rounded-lg">
              <Icon as={Users} size="md" className="text-blue-600 mx-auto mb-1" />
              <Text className="text-lg font-bold text-blue-600">
                {formatNumber(stats.total_students)}
              </Text>
              <Text className="text-xs text-gray-600">Estudantes</Text>
            </Box>

            <Box className="text-center p-3 bg-green-50 rounded-lg">
              <Icon as={GraduationCap} size="md" className="text-green-600 mx-auto mb-1" />
              <Text className="text-lg font-bold text-green-600">
                {formatNumber(stats.total_teachers)}
              </Text>
              <Text className="text-xs text-gray-600">Professores</Text>
            </Box>

            {stats.success_rate && (
              <Box className="text-center p-3 bg-yellow-50 rounded-lg">
                <Icon as={Target} size="md" className="text-yellow-600 mx-auto mb-1" />
                <Text className="text-lg font-bold text-yellow-600">
                  {formatPercentage(stats.success_rate)}
                </Text>
                <Text className="text-xs text-gray-600">Sucesso</Text>
              </Box>
            )}

            {stats.average_rating && (
              <Box
                className={`text-center p-3 rounded-lg ${getStatColor(
                  stats.average_rating,
                  'rating',
                )}`}
              >
                <Icon
                  as={Award}
                  size="md"
                  className={`mx-auto mb-1 ${
                    getStatColor(stats.average_rating, 'rating').split(' ')[0]
                  }`}
                />
                <Text
                  className={`text-lg font-bold ${
                    getStatColor(stats.average_rating, 'rating').split(' ')[0]
                  }`}
                >
                  {stats.average_rating.toFixed(1)}
                </Text>
                <Text className="text-xs text-gray-600">Avaliação</Text>
              </Box>
            )}
          </Grid>
        </CardBody>
      </Card>
    );
  }

  // Full detailed stats view
  return (
    <Card className={`${className} w-full`}>
      <CardHeader>
        <Heading size="lg">Estatísticas da Escola</Heading>
      </CardHeader>

      <CardBody>
        <VStack space="lg">
          {/* Core Metrics */}
          <VStack space="sm">
            <Heading size="md" className="text-gray-700">
              Métricas Principais
            </Heading>
            <Grid className="grid-cols-2 lg:grid-cols-4 gap-4">
              <Box className="text-center p-4 bg-blue-50 rounded-lg">
                <Icon as={Users} size="lg" className="text-blue-600 mx-auto mb-2" />
                <Text className="text-2xl font-bold text-blue-600">
                  {formatNumber(stats.total_students)}
                </Text>
                <Text className="text-sm text-gray-600">Estudantes Ativos</Text>
              </Box>

              <Box className="text-center p-4 bg-green-50 rounded-lg">
                <Icon as={GraduationCap} size="lg" className="text-green-600 mx-auto mb-2" />
                <Text className="text-2xl font-bold text-green-600">
                  {formatNumber(stats.total_teachers)}
                </Text>
                <Text className="text-sm text-gray-600">Professores</Text>
              </Box>

              <Box className="text-center p-4 bg-purple-50 rounded-lg">
                <Icon as={Activity} size="lg" className="text-purple-600 mx-auto mb-2" />
                <Text className="text-2xl font-bold text-purple-600">
                  {formatNumber(stats.active_sessions_count)}
                </Text>
                <Text className="text-sm text-gray-600">Sessões Ativas</Text>
              </Box>

              {stats.courses_offered && (
                <Box className="text-center p-4 bg-orange-50 rounded-lg">
                  <Icon as={BookOpen} size="lg" className="text-orange-600 mx-auto mb-2" />
                  <Text className="text-2xl font-bold text-orange-600">
                    {formatNumber(stats.courses_offered)}
                  </Text>
                  <Text className="text-sm text-gray-600">Cursos Oferecidos</Text>
                </Box>
              )}
            </Grid>
          </VStack>

          {/* Performance Metrics */}
          {(stats.success_rate || stats.completion_rate || stats.average_rating) && (
            <VStack space="sm">
              <Heading size="md" className="text-gray-700">
                Desempenho
              </Heading>
              <Grid className="grid-cols-1 lg:grid-cols-3 gap-4">
                {stats.success_rate && (
                  <Box className="p-4 bg-white border border-gray-200 rounded-lg">
                    <HStack className="justify-between items-center mb-2">
                      <HStack space="xs" className="items-center">
                        <Icon as={Target} size="sm" className="text-yellow-600" />
                        <Text className="font-medium">Taxa de Sucesso</Text>
                      </HStack>
                      <Text className="text-lg font-bold text-yellow-600">
                        {formatPercentage(stats.success_rate)}
                      </Text>
                    </HStack>
                    <Progress value={stats.success_rate * 100} className="h-2" />
                  </Box>
                )}

                {stats.completion_rate && (
                  <Box className="p-4 bg-white border border-gray-200 rounded-lg">
                    <HStack className="justify-between items-center mb-2">
                      <HStack space="xs" className="items-center">
                        <Icon as={Award} size="sm" className="text-green-600" />
                        <Text className="font-medium">Taxa de Conclusão</Text>
                      </HStack>
                      <Text className="text-lg font-bold text-green-600">
                        {formatPercentage(stats.completion_rate)}
                      </Text>
                    </HStack>
                    <Progress value={stats.completion_rate * 100} className="h-2" />
                  </Box>
                )}

                {showRatings && stats.average_rating && (
                  <Box className={`p-4 rounded-lg ${getStatColor(stats.average_rating, 'rating')}`}>
                    <HStack className="justify-between items-center mb-2">
                      <HStack space="xs" className="items-center">
                        <Icon
                          as={Award}
                          size="sm"
                          className={getStatColor(stats.average_rating, 'rating').split(' ')[0]}
                        />
                        <Text className="font-medium">Avaliação Média</Text>
                      </HStack>
                      <Text
                        className={`text-lg font-bold ${
                          getStatColor(stats.average_rating, 'rating').split(' ')[0]
                        }`}
                      >
                        {stats.average_rating.toFixed(1)}/5.0
                      </Text>
                    </HStack>
                    <HStack space="xs" className="mt-1">
                      {[1, 2, 3, 4, 5].map(star => (
                        <Box
                          key={star}
                          className={`w-3 h-3 rounded-full ${
                            star <= stats.average_rating! ? 'bg-yellow-400' : 'bg-gray-300'
                          }`}
                        />
                      ))}
                    </HStack>
                  </Box>
                )}
              </Grid>
            </VStack>
          )}

          {/* Additional Metrics */}
          {(stats.total_hours_taught ||
            stats.student_satisfaction ||
            stats.teacher_retention_rate) && (
            <VStack space="sm">
              <Heading size="md" className="text-gray-700">
                Métricas Adicionais
              </Heading>
              <Grid className="grid-cols-1 lg:grid-cols-3 gap-4">
                {stats.total_hours_taught && (
                  <Box className="text-center p-4 bg-indigo-50 rounded-lg">
                    <Icon as={Clock} size="lg" className="text-indigo-600 mx-auto mb-2" />
                    <Text className="text-2xl font-bold text-indigo-600">
                      {formatHours(stats.total_hours_taught)}h
                    </Text>
                    <Text className="text-sm text-gray-600">Horas Ensinadas</Text>
                  </Box>
                )}

                {showRatings && stats.student_satisfaction && (
                  <Box
                    className={`text-center p-4 rounded-lg ${getStatColor(
                      stats.student_satisfaction,
                      'percentage',
                    )}`}
                  >
                    <Icon
                      as={Users}
                      size="lg"
                      className={`mx-auto mb-2 ${
                        getStatColor(stats.student_satisfaction, 'percentage').split(' ')[0]
                      }`}
                    />
                    <Text
                      className={`text-2xl font-bold ${
                        getStatColor(stats.student_satisfaction, 'percentage').split(' ')[0]
                      }`}
                    >
                      {formatPercentage(stats.student_satisfaction)}
                    </Text>
                    <Text className="text-sm text-gray-600">Satisfação dos Estudantes</Text>
                  </Box>
                )}

                {stats.teacher_retention_rate && (
                  <Box
                    className={`text-center p-4 rounded-lg ${getStatColor(
                      stats.teacher_retention_rate,
                      'percentage',
                    )}`}
                  >
                    <Icon
                      as={GraduationCap}
                      size="lg"
                      className={`mx-auto mb-2 ${
                        getStatColor(stats.teacher_retention_rate, 'percentage').split(' ')[0]
                      }`}
                    />
                    <Text
                      className={`text-2xl font-bold ${
                        getStatColor(stats.teacher_retention_rate, 'percentage').split(' ')[0]
                      }`}
                    >
                      {formatPercentage(stats.teacher_retention_rate)}
                    </Text>
                    <Text className="text-sm text-gray-600">Retenção de Professores</Text>
                  </Box>
                )}
              </Grid>
            </VStack>
          )}

          {/* Growth Metrics */}
          {showGrowthMetrics && stats.monthly_growth && (
            <VStack space="sm">
              <Heading size="md" className="text-gray-700">
                Crescimento
              </Heading>
              <Box className={`p-4 rounded-lg ${getStatColor(stats.monthly_growth, 'growth')}`}>
                <HStack className="justify-between items-center">
                  <HStack space="xs" className="items-center">
                    <Icon
                      as={TrendingUp}
                      size="sm"
                      className={getStatColor(stats.monthly_growth, 'growth').split(' ')[0]}
                    />
                    <Text className="font-medium">Crescimento Mensal</Text>
                  </HStack>
                  <Text
                    className={`text-lg font-bold ${
                      getStatColor(stats.monthly_growth, 'growth').split(' ')[0]
                    }`}
                  >
                    {stats.monthly_growth > 0 ? '+' : ''}
                    {formatPercentage(stats.monthly_growth)}
                  </Text>
                </HStack>
              </Box>
            </VStack>
          )}
        </VStack>
      </CardBody>
    </Card>
  );
};

export default SchoolStats;
