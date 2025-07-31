import { router } from 'expo-router';
import { 
  TrendingUpIcon,
  DollarSignIcon,
  UsersIcon,
  CalendarIcon,
  StarIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  BarChart3Icon,
  PieChartIcon,
  MoreVerticalIcon
} from 'lucide-react-native';
import React, { useState, useMemo } from 'react';

import MainLayout from '@/components/layouts/main-layout';
import { Badge, BadgeText } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Card, CardBody, CardHeader } from '@/components/ui/card';
import { Center } from '@/components/ui/center';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Menu, MenuItem, MenuItemLabel } from '@/components/ui/menu';
import { Pressable } from '@/components/ui/pressable';
import { ScrollView } from '@/components/ui/scroll-view';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import useTutorAnalytics from '@/hooks/useTutorAnalytics';

const TutorAnalyticsPage = () => {
  const [timeRange, setTimeRange] = useState<'week' | 'month' | 'quarter' | 'year'>('month');
  
  // For now, using a mock school ID - in real app, get from tutor context
  const mockSchoolId = 1;
  
  const { analytics, isLoading, error, refresh } = useTutorAnalytics(mockSchoolId);

  // Mock additional analytics data that would come from enhanced APIs
  const mockMonthlyData = useMemo(() => [
    { month: 'Jan', revenue: 850, students: 8, hours: 32 },
    { month: 'Fev', revenue: 920, students: 9, hours: 36 },
    { month: 'Mar', revenue: 1180, students: 12, hours: 44 },
    { month: 'Abr', revenue: 1350, students: 14, hours: 52 },
    { month: 'Mai', revenue: 1420, students: 15, hours: 58 },
    { month: 'Jun', revenue: 1680, students: 17, hours: 64 },
  ], []);

  const mockSubjectBreakdown = useMemo(() => [
    { subject: 'Matemática', revenue: 980, students: 12, percentage: 45 },
    { subject: 'Física', revenue: 650, students: 8, percentage: 30 },
    { subject: 'Química', revenue: 420, students: 5, percentage: 20 },
    { subject: 'Biologia', revenue: 110, students: 2, percentage: 5 },
  ], []);

  const mockAcquisitionData = useMemo(() => [
    { source: 'Convites por Email', conversions: 12, rate: 85 },
    { source: 'Link de Partilha', conversions: 8, rate: 45 },
    { source: 'Referências', conversions: 6, rate: 95 },
    { source: 'Redes Sociais', conversions: 3, rate: 25 },
  ], []);

  if (isLoading) {
    return (
      <MainLayout _title="Business Analytics">
        <Center className="flex-1 p-6">
          <VStack space="md" className="items-center">
            <Icon as={BarChart3Icon} size="xl" className="text-blue-500" />
            <Text className="text-gray-600">Carregando analytics...</Text>
          </VStack>
        </Center>
      </MainLayout>
    );
  }

  if (error) {
    return (
      <MainLayout _title="Business Analytics">
        <Center className="flex-1 p-6">
          <VStack space="lg" className="items-center max-w-md">
            <Icon as={BarChart3Icon} size="xl" className="text-gray-400" />
            <VStack space="sm" className="items-center">
              <Heading size="lg" className="text-center text-gray-900">
                Erro ao Carregar Analytics
              </Heading>
              <Text className="text-center text-gray-600">
                {error}
              </Text>
            </VStack>
            <Button onPress={refresh} variant="solid">
              <ButtonText>Tentar Novamente</ButtonText>
            </Button>
          </VStack>
        </Center>
      </MainLayout>
    );
  }

  const currentMonthData = mockMonthlyData[mockMonthlyData.length - 1];
  const previousMonthData = mockMonthlyData[mockMonthlyData.length - 2];
  
  const revenueGrowth = previousMonthData 
    ? ((currentMonthData.revenue - previousMonthData.revenue) / previousMonthData.revenue) * 100 
    : 0;
  const studentGrowth = previousMonthData 
    ? ((currentMonthData.students - previousMonthData.students) / previousMonthData.students) * 100 
    : 0;

  return (
    <MainLayout _title="Business Analytics">
      <ScrollView 
        className="flex-1 bg-gray-50"
        contentContainerStyle={{ paddingBottom: 100 }}
      >
        <VStack className="p-6" space="lg">
          {/* Header */}
          <VStack space="sm">
            <HStack className="justify-between items-center">
              <VStack>
                <Heading size="xl" className="text-gray-900">
                  Business Analytics
                </Heading>
                <Text className="text-gray-600">
                  Insights sobre o crescimento do seu negócio
                </Text>
              </VStack>
              <Menu
                trigger={({ ...triggerProps }) => (
                  <Pressable {...triggerProps} className="p-2 bg-white border border-gray-300 rounded-lg">
                    <Icon as={MoreVerticalIcon} size="sm" className="text-gray-600" />
                  </Pressable>
                )}
              >
                <MenuItem onPress={() => setTimeRange('week')}>
                  <MenuItemLabel>Última Semana</MenuItemLabel>
                </MenuItem>
                <MenuItem onPress={() => setTimeRange('month')}>
                  <MenuItemLabel>Último Mês</MenuItemLabel>
                </MenuItem>
                <MenuItem onPress={() => setTimeRange('quarter')}>
                  <MenuItemLabel>Último Trimestre</MenuItemLabel>
                </MenuItem>
                <MenuItem onPress={() => setTimeRange('year')}>
                  <MenuItemLabel>Último Ano</MenuItemLabel>
                </MenuItem>
              </Menu>
            </HStack>
            
            <Badge variant="outline">
              <BadgeText>
                Período: {timeRange === 'week' ? 'Semana' : 
                         timeRange === 'month' ? 'Mês' :
                         timeRange === 'quarter' ? 'Trimestre' : 'Ano'}
              </BadgeText>
            </Badge>
          </VStack>

          {/* Key Metrics Overview */}
          <VStack space="sm">
            <Text className="text-lg font-semibold text-gray-900">
              Métricas Principais
            </Text>
            <VStack space="sm">
              {/* Revenue and Growth */}
              <HStack space="sm">
                <Card variant="elevated" className="bg-white shadow-sm flex-1">
                  <CardBody>
                    <VStack space="xs">
                      <HStack className="justify-between items-center">
                        <Icon as={DollarSignIcon} size="sm" className="text-green-600" />
                        <HStack space="xs" className="items-center">
                          <Icon 
                            as={revenueGrowth >= 0 ? ArrowUpIcon : ArrowDownIcon} 
                            size="xs" 
                            className={revenueGrowth >= 0 ? "text-green-600" : "text-red-600"} 
                          />
                          <Text className={`text-xs font-medium ${revenueGrowth >= 0 ? "text-green-600" : "text-red-600"}`}>
                            {Math.abs(revenueGrowth).toFixed(1)}%
                          </Text>
                        </HStack>
                      </HStack>
                      <Text className="text-2xl font-bold text-gray-900">
                        €{analytics?.total_earnings.toFixed(0) || currentMonthData.revenue}
                      </Text>
                      <Text className="text-sm text-gray-600">
                        Receita Total
                      </Text>
                    </VStack>
                  </CardBody>
                </Card>

                <Card variant="elevated" className="bg-white shadow-sm flex-1">
                  <CardBody>
                    <VStack space="xs">
                      <HStack className="justify-between items-center">
                        <Icon as={UsersIcon} size="sm" className="text-blue-600" />
                        <HStack space="xs" className="items-center">
                          <Icon 
                            as={studentGrowth >= 0 ? ArrowUpIcon : ArrowDownIcon} 
                            size="xs" 
                            className={studentGrowth >= 0 ? "text-green-600" : "text-red-600"} 
                          />
                          <Text className={`text-xs font-medium ${studentGrowth >= 0 ? "text-green-600" : "text-red-600"}`}>
                            {Math.abs(studentGrowth).toFixed(1)}%
                          </Text>
                        </HStack>
                      </HStack>
                      <Text className="text-2xl font-bold text-gray-900">
                        {analytics?.total_students || currentMonthData.students}
                      </Text>
                      <Text className="text-sm text-gray-600">
                        Estudantes Ativos
                      </Text>
                    </VStack>
                  </CardBody>
                </Card>
              </HStack>

              <HStack space="sm">
                <Card variant="elevated" className="bg-white shadow-sm flex-1">
                  <CardBody>
                    <VStack space="xs">
                      <Icon as={CalendarIcon} size="sm" className="text-purple-600" />
                      <Text className="text-2xl font-bold text-gray-900">
                        {analytics?.total_hours_taught || currentMonthData.hours}h
                      </Text>
                      <Text className="text-sm text-gray-600">
                        Horas Lecionadas
                      </Text>
                    </VStack>
                  </CardBody>
                </Card>

                <Card variant="elevated" className="bg-white shadow-sm flex-1">
                  <CardBody>
                    <VStack space="xs">
                      <Icon as={StarIcon} size="sm" className="text-yellow-600" />
                      <Text className="text-2xl font-bold text-gray-900">
                        {analytics?.average_rating.toFixed(1) || '4.8'}
                      </Text>
                      <Text className="text-sm text-gray-600">
                        Avaliação Média
                      </Text>
                    </VStack>
                  </CardBody>
                </Card>
              </HStack>
            </VStack>
          </VStack>

          {/* Revenue Trend Chart */}
          <Card variant="elevated" className="bg-white shadow-sm">
            <CardHeader>
              <HStack className="justify-between items-center">
                <Heading size="md" className="text-gray-900">
                  Crescimento da Receita
                </Heading>
                <Icon as={TrendingUpIcon} size="sm" className="text-blue-600" />
              </HStack>
            </CardHeader>
            <CardBody>
              <VStack space="md">
                {/* Simple bar chart representation */}
                <VStack space="sm">
                  {mockMonthlyData.slice(-6).map((data, index) => (
                    <HStack key={data.month} space="sm" className="items-center">
                      <Text className="text-sm font-medium text-gray-600 w-10">
                        {data.month}
                      </Text>
                      <VStack className="flex-1 bg-gray-200 rounded-full h-4 justify-center">
                        <VStack
                          className="bg-blue-500 h-4 rounded-full"
                          style={{ 
                            width: `${(data.revenue / Math.max(...mockMonthlyData.map(d => d.revenue))) * 100}%` 
                          }}
                        />
                      </VStack>
                      <Text className="text-sm font-semibold text-gray-900 w-16 text-right">
                        €{data.revenue}
                      </Text>
                    </HStack>
                  ))}
                </VStack>
                
                <VStack className="bg-blue-50 rounded-lg p-3">
                  <Text className="text-sm font-medium text-blue-900">
                    📈 Crescimento Mensal: +{revenueGrowth.toFixed(1)}%
                  </Text>
                  <Text className="text-xs text-blue-700">
                    Sua receita tem crescido consistentemente nos últimos meses
                  </Text>
                </VStack>
              </VStack>
            </CardBody>
          </Card>

          {/* Subject Performance Breakdown */}
          <Card variant="elevated" className="bg-white shadow-sm">
            <CardHeader>
              <HStack className="justify-between items-center">
                <Heading size="md" className="text-gray-900">
                  Performance por Disciplina
                </Heading>
                <Icon as={PieChartIcon} size="sm" className="text-purple-600" />
              </HStack>
            </CardHeader>
            <CardBody>
              <VStack space="sm">
                {mockSubjectBreakdown.map((subject, index) => (
                  <VStack key={subject.subject} space="xs">
                    <HStack className="justify-between items-center">
                      <VStack>
                        <Text className="text-sm font-medium text-gray-900">
                          {subject.subject}
                        </Text>
                        <Text className="text-xs text-gray-600">
                          {subject.students} estudantes
                        </Text>
                      </VStack>
                      <VStack className="items-end">
                        <Text className="text-sm font-semibold text-gray-900">
                          €{subject.revenue}
                        </Text>
                        <Text className="text-xs text-gray-600">
                          {subject.percentage}%
                        </Text>
                      </VStack>
                    </HStack>
                    <VStack className="w-full bg-gray-200 rounded-full h-2">
                      <VStack
                        className={`h-2 rounded-full ${
                          index === 0 ? 'bg-blue-500' :
                          index === 1 ? 'bg-green-500' :
                          index === 2 ? 'bg-purple-500' : 'bg-orange-500'
                        }`}
                        style={{ width: `${subject.percentage}%` }}
                      />
                    </VStack>
                  </VStack>
                ))}
              </VStack>
            </CardBody>
          </Card>

          {/* Student Acquisition Analytics */}
          <Card variant="elevated" className="bg-white shadow-sm">
            <CardHeader>
              <Heading size="md" className="text-gray-900">
                Análise de Aquisição de Estudantes
              </Heading>
            </CardHeader>
            <CardBody>
              <VStack space="sm">
                {mockAcquisitionData.map((source, index) => (
                  <HStack key={source.source} space="sm" className="items-center py-2">
                    <VStack className="flex-1">
                      <Text className="text-sm font-medium text-gray-900">
                        {source.source}
                      </Text>
                      <Text className="text-xs text-gray-600">
                        {source.conversions} conversões
                      </Text>
                    </VStack>
                    <VStack className="items-end">
                      <Badge 
                        variant="outline"
                        className={source.rate >= 70 ? "bg-green-50" : source.rate >= 40 ? "bg-yellow-50" : "bg-red-50"}
                      >
                        <BadgeText className={
                          source.rate >= 70 ? "text-green-700" : 
                          source.rate >= 40 ? "text-yellow-700" : "text-red-700"
                        }>
                          {source.rate}% taxa
                        </BadgeText>
                      </Badge>
                    </VStack>
                  </HStack>
                ))}
              </VStack>
              
              <VStack className="bg-green-50 border border-green-200 rounded-lg p-3 mt-4">
                <Text className="text-sm font-medium text-green-900">
                  💡 Insight: Convites por Email têm a melhor taxa de conversão
                </Text>
                <Text className="text-xs text-green-700">
                  Concentre seus esforços de marketing em convites personalizados por email
                </Text>
              </VStack>
            </CardBody>
          </Card>

          {/* Performance Metrics */}
          {analytics && (
            <Card variant="elevated" className="bg-white shadow-sm">
              <CardHeader>
                <Heading size="md" className="text-gray-900">
                  Métricas de Performance
                </Heading>
              </CardHeader>
              <CardBody>
                <VStack space="md">
                  <VStack space="xs">
                    <HStack className="justify-between items-center">
                      <Text className="text-sm text-gray-600">
                        Taxa de Conclusão de Aulas
                      </Text>
                      <Text className="text-sm font-semibold text-gray-900">
                        {Math.round(analytics.performance_metrics.completion_rate * 100)}%
                      </Text>
                    </HStack>
                    <VStack className="w-full bg-gray-200 rounded-full h-2">
                      <VStack
                        className={`h-2 rounded-full ${
                          analytics.performance_metrics.completion_rate >= 0.9 ? 'bg-green-500' :
                          analytics.performance_metrics.completion_rate >= 0.7 ? 'bg-yellow-500' : 'bg-red-500'
                        }`}
                        style={{ width: `${Math.round(analytics.performance_metrics.completion_rate * 100)}%` }}
                      />
                    </VStack>
                  </VStack>

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
                        className={`h-2 rounded-full ${
                          analytics.performance_metrics.on_time_rate >= 0.95 ? 'bg-green-500' :
                          analytics.performance_metrics.on_time_rate >= 0.8 ? 'bg-yellow-500' : 'bg-red-500'
                        }`}
                        style={{ width: `${Math.round(analytics.performance_metrics.on_time_rate * 100)}%` }}
                      />
                    </VStack>
                  </VStack>

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
                        className={`h-2 rounded-full ${
                          analytics.performance_metrics.student_retention >= 0.85 ? 'bg-green-500' :
                          analytics.performance_metrics.student_retention >= 0.7 ? 'bg-yellow-500' : 'bg-red-500'
                        }`}
                        style={{ width: `${Math.round(analytics.performance_metrics.student_retention * 100)}%` }}
                      />
                    </VStack>
                  </VStack>
                </VStack>
              </CardBody>
            </Card>
          )}

          {/* Action Items */}
          <Card variant="elevated" className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 shadow-sm">
            <CardHeader>
              <Heading size="md" className="text-gray-900">
                Ações Recomendadas
              </Heading>
            </CardHeader>
            <CardBody>
              <VStack space="sm">
                <HStack space="sm" className="items-start">
                  <Text className="text-blue-600 font-bold">1.</Text>
                  <VStack className="flex-1">
                    <Text className="text-sm font-medium text-gray-900">
                      Aumentar convites por email
                    </Text>
                    <Text className="text-xs text-gray-600">
                      85% de taxa de conversão - foque neste canal
                    </Text>
                  </VStack>
                </HStack>
                <HStack space="sm" className="items-start">
                  <Text className="text-blue-600 font-bold">2.</Text>
                  <VStack className="flex-1">
                    <Text className="text-sm font-medium text-gray-900">
                      Expandir ofertas em Matemática
                    </Text>
                    <Text className="text-xs text-gray-600">
                      Sua disciplina mais rentável - 45% da receita
                    </Text>
                  </VStack>
                </HStack>
                <HStack space="sm" className="items-start">
                  <Text className="text-blue-600 font-bold">3.</Text>
                  <VStack className="flex-1">
                    <Text className="text-sm font-medium text-gray-900">
                      Melhorar estratégia de redes sociais
                    </Text>
                    <Text className="text-xs text-gray-600">
                      25% de conversão - há espaço para melhoria
                    </Text>
                  </VStack>
                </HStack>
              </VStack>
            </CardBody>
          </Card>

          {/* Export and More Actions */}
          <VStack space="sm">
            <Button 
              variant="outline" 
              onPress={() => router.push('/(tutor)/dashboard')}
            >
              <ButtonText className="text-blue-600">Voltar ao Dashboard</ButtonText>
            </Button>
          </VStack>
        </VStack>
      </ScrollView>
    </MainLayout>
  );
};

export default TutorAnalyticsPage;