import {
  TrendingUpIcon,
  UsersIcon,
  DollarSignIcon,
  CalendarIcon,
  BarChart3Icon,
  RefreshCwIcon,
  AlertTriangleIcon,
} from 'lucide-react-native';
import React, { useState } from 'react';
import { Pressable, RefreshControl } from 'react-native';

import MainLayout from '@/components/layouts/MainLayout';
import { Badge, BadgeText } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Card, CardBody, CardHeader } from '@/components/ui/card';
import { Center } from '@/components/ui/center';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { ScrollView } from '@/components/ui/scroll-view';
import {
  Select,
  SelectTrigger,
  SelectInput,
  SelectIcon,
  SelectPortal,
  SelectBackdrop,
  SelectContent,
  SelectDragIndicatorWrapper,
  SelectDragIndicator,
  SelectItem,
} from '@/components/ui/select';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { useTeacherDashboard } from '@/hooks/useTeacherDashboard';
import { isWeb } from '@/utils/platform';

const TeacherAnalyticsPage = () => {
  const { data, isLoading, error, refresh } = useTeacherDashboard();
  const [timeframe, setTimeframe] = useState<'week' | 'month' | 'year'>('month');

  // Calculate analytics based on available data
  const analytics = data
    ? {
        totalStudents: data.quick_stats.total_students,
        activeStudents: data.students.filter(
          s =>
            s.last_session_date &&
            new Date(s.last_session_date) >= new Date(Date.now() - 7 * 24 * 60 * 60 * 1000),
        ).length,
        averageProgress: data.progress_metrics.average_student_progress,
        totalSessions: data.quick_stats.sessions_this_week,
        completionRate: data.quick_stats.completion_rate,
        monthlyEarnings: data.earnings.current_month_total,
        totalEarnings: data.earnings.current_month_total + data.earnings.last_month_total,
        pendingEarnings: data.earnings.pending_amount,
        totalHours: data.earnings.total_hours_taught,
        improvementRate: data.progress_metrics.students_improved_this_month,
        totalAssessments: data.progress_metrics.total_assessments_given,
      }
    : null;

  // Loading state
  if (isLoading && !data) {
    return (
      <MainLayout _title="Analytics">
        <Center className="flex-1 p-6">
          <VStack space="md" className="items-center">
            <Icon as={BarChart3Icon} size="xl" className="text-blue-500" />
            <Text className="text-gray-600">Carregando analytics...</Text>
          </VStack>
        </Center>
      </MainLayout>
    );
  }

  // Error state
  if (error && !data) {
    return (
      <MainLayout _title="Analytics">
        <Center className="flex-1 p-6">
          <VStack space="lg" className="items-center max-w-md">
            <Icon as={AlertTriangleIcon} size="xl" className="text-red-500" />
            <VStack space="sm" className="items-center">
              <Heading size="lg" className="text-center text-gray-900">
                Erro ao Carregar Analytics
              </Heading>
              <Text className="text-center text-gray-600">{error}</Text>
            </VStack>
            <Button onPress={refresh} variant="solid">
              <Icon as={RefreshCwIcon} size="sm" className="text-white mr-2" />
              <ButtonText>Tentar Novamente</ButtonText>
            </Button>
          </VStack>
        </Center>
      </MainLayout>
    );
  }

  return (
    <MainLayout _title="Analytics">
      <ScrollView
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={isLoading} onRefresh={refresh} />}
        contentContainerStyle={{
          paddingBottom: isWeb ? 0 : 100,
          flexGrow: 1,
        }}
        className="flex-1 bg-gray-50"
      >
        <VStack className="p-6" space="lg">
          {/* Header */}
          <HStack className="justify-between items-center">
            <VStack>
              <Heading size="xl" className="text-gray-900">
                Analytics
              </Heading>
              <Text className="text-gray-600">Acompanhe o seu desempenho como professor</Text>
            </VStack>

            <HStack space="xs" className="items-center">
              <Select
                selectedValue={timeframe}
                onValueChange={value => setTimeframe(value as 'week' | 'month' | 'year')}
              >
                <SelectTrigger variant="outline" size="sm">
                  <SelectInput placeholder="Período" />
                  <SelectIcon as={CalendarIcon} />
                </SelectTrigger>
                <SelectPortal>
                  <SelectBackdrop />
                  <SelectContent>
                    <SelectDragIndicatorWrapper>
                      <SelectDragIndicator />
                    </SelectDragIndicatorWrapper>
                    <SelectItem label="Esta Semana" value="week" />
                    <SelectItem label="Este Mês" value="month" />
                    <SelectItem label="Este Ano" value="year" />
                  </SelectContent>
                </SelectPortal>
              </Select>

              <Pressable
                onPress={refresh}
                disabled={isLoading}
                className="p-2 rounded-md bg-gray-100 hover:bg-gray-200"
                accessibilityLabel="Atualizar analytics"
                accessibilityRole="button"
              >
                <Icon
                  as={RefreshCwIcon}
                  size="sm"
                  className={`text-gray-600 ${isLoading ? 'animate-spin' : ''}`}
                />
              </Pressable>
            </HStack>
          </HStack>

          {/* Error Alert */}
          {error && data && (
            <Box className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <HStack space="sm" className="items-start">
                <Icon as={AlertTriangleIcon} size="sm" className="text-yellow-600 mt-0.5" />
                <VStack className="flex-1">
                  <Text className="font-medium text-yellow-900">
                    Dados parcialmente desatualizados
                  </Text>
                  <Text className="text-sm text-yellow-700">{error}</Text>
                </VStack>
                <Pressable onPress={refresh}>
                  <Text className="text-sm font-medium text-yellow-600">Atualizar</Text>
                </Pressable>
              </HStack>
            </Box>
          )}

          {/* Key Metrics Grid */}
          {analytics && (
            <>
              <VStack space="md">
                <Heading size="md" className="text-gray-900">
                  Métricas Principais
                </Heading>

                <VStack space="sm" className={isWeb ? 'lg:grid lg:grid-cols-2 lg:gap-4' : ''}>
                  {/* Students Metrics */}
                  <Card variant="elevated" className="bg-white shadow-sm">
                    <CardHeader>
                      <HStack className="justify-between items-center">
                        <Text className="text-sm font-medium text-gray-600">Estudantes</Text>
                        <Icon as={UsersIcon} size="sm" className="text-blue-600" />
                      </HStack>
                    </CardHeader>
                    <CardBody>
                      <VStack space="md">
                        <HStack space="lg" className="justify-around">
                          <VStack className="items-center">
                            <Text className="text-2xl font-bold text-gray-900">
                              {analytics.totalStudents}
                            </Text>
                            <Text className="text-xs text-gray-500">Total</Text>
                          </VStack>
                          <VStack className="items-center">
                            <Text className="text-2xl font-bold text-green-600">
                              {analytics.activeStudents}
                            </Text>
                            <Text className="text-xs text-gray-500">Ativos</Text>
                          </VStack>
                          <VStack className="items-center">
                            <Text className="text-2xl font-bold text-blue-600">
                              {Math.round(analytics.averageProgress)}%
                            </Text>
                            <Text className="text-xs text-gray-500">Progresso Médio</Text>
                          </VStack>
                        </HStack>

                        <Box className="bg-gray-50 rounded-lg p-3">
                          <HStack className="justify-between items-center">
                            <Text className="text-sm text-gray-600">Taxa de Conclusão</Text>
                            <Text className="text-sm font-semibold text-gray-900">
                              {Math.round(analytics.completionRate)}%
                            </Text>
                          </HStack>
                          <Box className="w-full h-2 bg-gray-200 rounded-full overflow-hidden mt-2">
                            <Box
                              className="h-full bg-blue-500 rounded-full"
                              style={{ width: `${Math.min(analytics.completionRate, 100)}%` }}
                            />
                          </Box>
                        </Box>
                      </VStack>
                    </CardBody>
                  </Card>

                  {/* Sessions Metrics */}
                  <Card variant="elevated" className="bg-white shadow-sm">
                    <CardHeader>
                      <HStack className="justify-between items-center">
                        <Text className="text-sm font-medium text-gray-600">Sessões</Text>
                        <Icon as={CalendarIcon} size="sm" className="text-green-600" />
                      </HStack>
                    </CardHeader>
                    <CardBody>
                      <VStack space="md">
                        <HStack space="lg" className="justify-around">
                          <VStack className="items-center">
                            <Text className="text-2xl font-bold text-gray-900">
                              {analytics.totalSessions}
                            </Text>
                            <Text className="text-xs text-gray-500">Esta Semana</Text>
                          </VStack>
                          <VStack className="items-center">
                            <Text className="text-2xl font-bold text-green-600">
                              {Math.round(analytics.totalHours)}
                            </Text>
                            <Text className="text-xs text-gray-500">Horas Totais</Text>
                          </VStack>
                          <VStack className="items-center">
                            <Text className="text-2xl font-bold text-blue-600">
                              {analytics.totalAssessments}
                            </Text>
                            <Text className="text-xs text-gray-500">Avaliações</Text>
                          </VStack>
                        </HStack>

                        <Box className="bg-gray-50 rounded-lg p-3">
                          <HStack className="justify-between items-center">
                            <Text className="text-sm text-gray-600">Estudantes Melhoraram</Text>
                            <Badge className="bg-green-100">
                              <BadgeText className="text-green-800">
                                {analytics.improvementRate} este mês
                              </BadgeText>
                            </Badge>
                          </HStack>
                        </Box>
                      </VStack>
                    </CardBody>
                  </Card>

                  {/* Earnings Metrics */}
                  <Card variant="elevated" className="bg-white shadow-sm">
                    <CardHeader>
                      <HStack className="justify-between items-center">
                        <Text className="text-sm font-medium text-gray-600">Ganhos</Text>
                        <Icon as={DollarSignIcon} size="sm" className="text-purple-600" />
                      </HStack>
                    </CardHeader>
                    <CardBody>
                      <VStack space="md">
                        <HStack space="lg" className="justify-around">
                          <VStack className="items-center">
                            <Text className="text-2xl font-bold text-gray-900">
                              €{analytics.monthlyEarnings.toFixed(0)}
                            </Text>
                            <Text className="text-xs text-gray-500">Este Mês</Text>
                          </VStack>
                          <VStack className="items-center">
                            <Text className="text-2xl font-bold text-green-600">
                              €{analytics.totalEarnings.toFixed(0)}
                            </Text>
                            <Text className="text-xs text-gray-500">Total</Text>
                          </VStack>
                          <VStack className="items-center">
                            <Text className="text-2xl font-bold text-orange-600">
                              €{analytics.pendingEarnings.toFixed(0)}
                            </Text>
                            <Text className="text-xs text-gray-500">Pendente</Text>
                          </VStack>
                        </HStack>

                        <Box className="bg-gray-50 rounded-lg p-3">
                          <HStack className="justify-between items-center">
                            <Text className="text-sm text-gray-600">Taxa Horária Média</Text>
                            <Text className="text-sm font-semibold text-gray-900">
                              €
                              {analytics.totalHours > 0
                                ? (analytics.totalEarnings / analytics.totalHours).toFixed(2)
                                : '0.00'}
                              /h
                            </Text>
                          </HStack>
                        </Box>
                      </VStack>
                    </CardBody>
                  </Card>

                  {/* Performance Overview */}
                  <Card variant="elevated" className="bg-white shadow-sm">
                    <CardHeader>
                      <HStack className="justify-between items-center">
                        <Text className="text-sm font-medium text-gray-600">Desempenho Geral</Text>
                        <Icon as={TrendingUpIcon} size="sm" className="text-indigo-600" />
                      </HStack>
                    </CardHeader>
                    <CardBody>
                      <VStack space="md">
                        <VStack space="sm">
                          <HStack className="justify-between items-center">
                            <Text className="text-sm text-gray-600">Progresso dos Estudantes</Text>
                            <Badge
                              className={`${
                                analytics.averageProgress >= 80
                                  ? 'bg-green-100'
                                  : analytics.averageProgress >= 60
                                    ? 'bg-yellow-100'
                                    : 'bg-red-100'
                              }`}
                            >
                              <BadgeText
                                className={`${
                                  analytics.averageProgress >= 80
                                    ? 'text-green-800'
                                    : analytics.averageProgress >= 60
                                      ? 'text-yellow-800'
                                      : 'text-red-800'
                                }`}
                              >
                                {analytics.averageProgress >= 80
                                  ? 'Excelente'
                                  : analytics.averageProgress >= 60
                                    ? 'Bom'
                                    : 'Precisa Melhorar'}
                              </BadgeText>
                            </Badge>
                          </HStack>

                          <HStack className="justify-between items-center">
                            <Text className="text-sm text-gray-600">Retenção de Estudantes</Text>
                            <Badge
                              className={`${
                                analytics.activeStudents / analytics.totalStudents >= 0.8
                                  ? 'bg-green-100'
                                  : analytics.activeStudents / analytics.totalStudents >= 0.6
                                    ? 'bg-yellow-100'
                                    : 'bg-red-100'
                              }`}
                            >
                              <BadgeText
                                className={`${
                                  analytics.activeStudents / analytics.totalStudents >= 0.8
                                    ? 'text-green-800'
                                    : analytics.activeStudents / analytics.totalStudents >= 0.6
                                      ? 'text-yellow-800'
                                      : 'text-red-800'
                                }`}
                              >
                                {Math.round(
                                  (analytics.activeStudents / analytics.totalStudents) * 100,
                                )}
                                %
                              </BadgeText>
                            </Badge>
                          </HStack>

                          <HStack className="justify-between items-center">
                            <Text className="text-sm text-gray-600">Taxa de Avaliação</Text>
                            <Text className="text-sm font-semibold text-gray-900">
                              {analytics.totalStudents > 0
                                ? (analytics.totalAssessments / analytics.totalStudents).toFixed(1)
                                : '0'}{' '}
                              por estudante
                            </Text>
                          </HStack>
                        </VStack>
                      </VStack>
                    </CardBody>
                  </Card>
                </VStack>
              </VStack>

              {/* Recent Payments */}
              {data?.earnings?.recent_payments && data.earnings.recent_payments.length > 0 && (
                <Card variant="elevated" className="bg-white shadow-sm">
                  <CardHeader>
                    <Heading size="md" className="text-gray-900">
                      Pagamentos Recentes
                    </Heading>
                  </CardHeader>
                  <CardBody>
                    <VStack space="sm">
                      {data.earnings.recent_payments.map(payment => (
                        <HStack
                          key={payment.id}
                          space="sm"
                          className="items-center py-2 border-b border-gray-100 last:border-b-0"
                        >
                          <VStack className="w-10 h-10 bg-green-100 rounded-full items-center justify-center">
                            <Text className="text-xs font-bold text-green-600">€</Text>
                          </VStack>
                          <VStack className="flex-1">
                            <Text className="text-sm font-medium text-gray-900">
                              {payment.session_info}
                            </Text>
                            <Text className="text-xs text-gray-500">
                              {new Date(payment.date).toLocaleDateString('pt-PT')} • {payment.hours}
                              h
                            </Text>
                          </VStack>
                          <VStack className="items-end">
                            <Text className="text-sm font-semibold text-green-600">
                              €{payment.amount.toFixed(2)}
                            </Text>
                          </VStack>
                        </HStack>
                      ))}
                    </VStack>
                  </CardBody>
                </Card>
              )}
            </>
          )}

          {/* Empty State */}
          {!analytics && !isLoading && (
            <Center className="flex-1 py-16">
              <VStack space="md" className="items-center max-w-md">
                <Icon as={BarChart3Icon} size="xl" className="text-gray-400" />
                <VStack space="sm" className="items-center">
                  <Heading size="lg" className="text-center text-gray-900">
                    Dados Insuficientes
                  </Heading>
                  <Text className="text-center text-gray-600">
                    Comece a dar aulas e acompanhar estudantes para ver analytics detalhados aqui.
                  </Text>
                </VStack>
              </VStack>
            </Center>
          )}
        </VStack>
      </ScrollView>
    </MainLayout>
  );
};

export default TeacherAnalyticsPage;
