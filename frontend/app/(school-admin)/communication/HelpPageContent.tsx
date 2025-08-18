import { isWeb } from '@/utils/platform';
import { router } from 'expo-router';
import {
  HelpCircleIcon,
  BookOpenIcon,
  VideoIcon,
  MessageSquareIcon,
  ExternalLinkIcon,
  SearchIcon,
  PlayCircleIcon,
  FileTextIcon,
  LightbulbIcon,
  ChevronRightIcon,
  MailIcon,
  PaletteIcon,
  SettingsIcon,
  BarChart3Icon,
} from 'lucide-react-native';
import React, { useState, useCallback, useMemo } from 'react';
import { Linking } from 'react-native';

import MainLayout from '@/components/layouts/MainLayout';
import { Badge } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Input, InputField } from '@/components/ui/input';
import { Pressable } from '@/components/ui/pressable';
import { SafeAreaView } from '@/components/ui/safe-area-view';
import { ScrollView } from '@/components/ui/scroll-view';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

// Types for help articles and resources
interface HelpArticle {
  id: string;
  title: string;
  category: string;
  description: string;
  icon: any;
  badges?: string[];
  lastUpdated?: string;
  estimatedReadTime?: string;
  type: 'article' | 'video' | 'guide' | 'faq';
  difficulty?: 'beginner' | 'intermediate' | 'advanced';
  link?: string;
  isExternal?: boolean;
}

interface HelpCategory {
  id: string;
  title: string;
  description: string;
  icon: any;
  color: string;
  count: number;
}

interface QuickAction {
  id: string;
  title: string;
  description: string;
  icon: any;
  action: () => void;
  color: string;
}

// Mock data - in a real app, this would come from an API
const helpCategories: HelpCategory[] = [
  {
    id: 'getting-started',
    title: 'Primeiros Passos',
    description: 'Guias básicos para começar a usar a plataforma',
    icon: LightbulbIcon,
    color: 'bg-blue-100 text-blue-700',
    count: 12,
  },
  {
    id: 'communication',
    title: 'Comunicação',
    description: 'Templates, emails e mensagens para sua escola',
    icon: MessageSquareIcon,
    color: 'bg-green-100 text-green-700',
    count: 8,
  },
  {
    id: 'analytics',
    title: 'Relatórios e Analytics',
    description: 'Como interpretar dados e métricas',
    icon: BarChart3Icon,
    color: 'bg-purple-100 text-purple-700',
    count: 6,
  },
  {
    id: 'customization',
    title: 'Personalização',
    description: 'Branding e configurações visuais',
    icon: PaletteIcon,
    color: 'bg-orange-100 text-orange-700',
    count: 4,
  },
  {
    id: 'settings',
    title: 'Configurações',
    description: 'Configurações da escola e conta',
    icon: SettingsIcon,
    color: 'bg-gray-100 text-gray-700',
    count: 10,
  },
];

const helpArticles: HelpArticle[] = [
  {
    id: '1',
    title: 'Como configurar sua primeira escola',
    category: 'getting-started',
    description: 'Passo a passo para configurar sua escola na plataforma',
    icon: BookOpenIcon,
    badges: ['Novo', 'Essencial'],
    lastUpdated: '2 dias atrás',
    estimatedReadTime: '5 min',
    type: 'guide',
    difficulty: 'beginner',
  },
  {
    id: '2',
    title: 'Criando templates de email eficazes',
    category: 'communication',
    description: 'Como criar templates de email que convertem e engajam',
    icon: MailIcon,
    badges: ['Popular'],
    lastUpdated: '1 semana atrás',
    estimatedReadTime: '8 min',
    type: 'article',
    difficulty: 'intermediate',
  },
  {
    id: '3',
    title: 'Interpretando métricas de engajamento',
    category: 'analytics',
    description: 'Entenda as principais métricas e como usá-las',
    icon: BarChart3Icon,
    badges: ['Avançado'],
    lastUpdated: '3 dias atrás',
    estimatedReadTime: '12 min',
    type: 'article',
    difficulty: 'advanced',
  },
  {
    id: '4',
    title: 'Vídeo: Personalizando cores da sua escola',
    category: 'customization',
    description: 'Tutorial em vídeo sobre personalização visual',
    icon: VideoIcon,
    badges: ['Vídeo', 'Atualizado'],
    lastUpdated: '5 dias atrás',
    estimatedReadTime: '6 min',
    type: 'video',
    difficulty: 'beginner',
  },
  {
    id: '5',
    title: 'FAQ: Configurações de notificação',
    category: 'settings',
    description: 'Perguntas frequentes sobre notificações',
    icon: HelpCircleIcon,
    badges: ['FAQ'],
    lastUpdated: '1 semana atrás',
    estimatedReadTime: '3 min',
    type: 'faq',
    difficulty: 'beginner',
  },
];

const quickActions: QuickAction[] = [
  {
    id: 'contact-support',
    title: 'Falar com Suporte',
    description: 'Entre em contato conosco diretamente',
    icon: MessageSquareIcon,
    action: () => {
      if (isWeb()) {
        window.open('mailto:suporte@aprendecomigo.com', '_blank');
      } else {
        Linking.openURL('mailto:suporte@aprendecomigo.com');
      }
    },
    color: 'bg-blue-500',
  },
  {
    id: 'schedule-demo',
    title: 'Agendar Demo',
    description: 'Agende uma demonstração personalizada',
    icon: VideoIcon,
    action: () => {
      if (isWeb()) {
        window.open('https://calendly.com/aprendecomigo/demo', '_blank');
      } else {
        Linking.openURL('https://calendly.com/aprendecomigo/demo');
      }
    },
    color: 'bg-green-500',
  },
  {
    id: 'feature-request',
    title: 'Sugerir Funcionalidade',
    description: 'Nos ajude a melhorar a plataforma',
    icon: LightbulbIcon,
    action: () => {
      router.push('/feedback');
    },
    color: 'bg-purple-500',
  },
  {
    id: 'documentation',
    title: 'Documentação Completa',
    description: 'Acesse nossa documentação técnica',
    icon: FileTextIcon,
    action: () => {
      if (isWeb()) {
        window.open('https://docs.aprendecomigo.com', '_blank');
      } else {
        Linking.openURL('https://docs.aprendecomigo.com');
      }
    },
    color: 'bg-orange-500',
  },
];

export default function HelpPageContent() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  const filteredArticles = useMemo(() => {
    return helpArticles.filter(article => {
      const matchesSearch =
        article.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        article.description.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesCategory = !selectedCategory || article.category === selectedCategory;
      return matchesSearch && matchesCategory;
    });
  }, [searchQuery, selectedCategory]);

  const handleArticlePress = useCallback((article: HelpArticle) => {
    if (article.isExternal && article.link) {
      if (isWeb()) {
        window.open(article.link, '_blank');
      } else {
        Linking.openURL(article.link);
      }
    } else {
      // Navigate to internal help article
      router.push(`/help/articles/${article.id}`);
    }
  }, []);

  const handleCategoryPress = useCallback(
    (categoryId: string) => {
      setSelectedCategory(selectedCategory === categoryId ? null : categoryId);
    },
    [selectedCategory],
  );

  const getBadgeColor = (badge: string) => {
    switch (badge.toLowerCase()) {
      case 'novo':
        return 'bg-green-100 text-green-700';
      case 'popular':
        return 'bg-blue-100 text-blue-700';
      case 'essencial':
        return 'bg-red-100 text-red-700';
      case 'avançado':
        return 'bg-purple-100 text-purple-700';
      case 'vídeo':
        return 'bg-orange-100 text-orange-700';
      case 'atualizado':
        return 'bg-yellow-100 text-yellow-700';
      case 'faq':
        return 'bg-gray-100 text-gray-700';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'video':
        return PlayCircleIcon;
      case 'guide':
        return BookOpenIcon;
      case 'faq':
        return HelpCircleIcon;
      default:
        return FileTextIcon;
    }
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'beginner':
        return 'text-green-600';
      case 'intermediate':
        return 'text-yellow-600';
      case 'advanced':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  return (
    <MainLayout>
      <SafeAreaView className="flex-1 bg-background-50">
        <ScrollView className="flex-1" showsVerticalScrollIndicator={false}>
          <VStack className="p-6" space="xl">
            {/* Header */}
            <VStack space="md">
              <HStack className="items-center" space="sm">
                <Icon as={HelpCircleIcon} size="xl" className="text-primary-600" />
                <Heading size="2xl" className="text-typography-900">
                  Central de Ajuda
                </Heading>
              </HStack>
              <Text className="text-typography-600 text-lg">
                Encontre respostas, guias e recursos para aproveitar ao máximo sua experiência.
              </Text>
            </VStack>

            {/* Search */}
            <Box className="relative">
              <Input variant="outline" size="lg">
                <InputField
                  placeholder="Pesquisar artigos, guias e tutoriais..."
                  value={searchQuery}
                  onChangeText={setSearchQuery}
                />
              </Input>
              <Box className="absolute right-3 top-3">
                <Icon as={SearchIcon} size="md" className="text-typography-400" />
              </Box>
            </Box>

            {/* Quick Actions */}
            <VStack space="md">
              <Heading size="lg" className="text-typography-900">
                Ações Rápidas
              </Heading>
              <ScrollView
                horizontal
                showsHorizontalScrollIndicator={false}
                contentContainerStyle={{ gap: 12 }}
              >
                {quickActions.map(action => (
                  <Pressable
                    key={action.id}
                    onPress={action.action}
                    className="w-48 p-4 bg-white rounded-lg border border-border-200 shadow-sm"
                  >
                    <VStack space="sm">
                      <Box
                        className={`w-10 h-10 ${action.color} rounded-lg items-center justify-center`}
                      >
                        <Icon as={action.icon} size="md" className="text-white" />
                      </Box>
                      <Text className="font-semibold text-typography-900">{action.title}</Text>
                      <Text className="text-sm text-typography-600">{action.description}</Text>
                    </VStack>
                  </Pressable>
                ))}
              </ScrollView>
            </VStack>

            {/* Categories */}
            <VStack space="md">
              <Heading size="lg" className="text-typography-900">
                Categorias
              </Heading>
              <VStack space="sm">
                {helpCategories.map(category => (
                  <Pressable
                    key={category.id}
                    onPress={() => handleCategoryPress(category.id)}
                    className={`p-4 rounded-lg border ${
                      selectedCategory === category.id
                        ? 'border-primary-300 bg-primary-50'
                        : 'border-border-200 bg-white'
                    }`}
                  >
                    <HStack className="items-center justify-between">
                      <HStack className="items-center flex-1" space="md">
                        <Box
                          className={`w-12 h-12 ${category.color} rounded-lg items-center justify-center`}
                        >
                          <Icon as={category.icon} size="md" />
                        </Box>
                        <VStack className="flex-1" space="xs">
                          <Text className="font-semibold text-typography-900">
                            {category.title}
                          </Text>
                          <Text className="text-sm text-typography-600">
                            {category.description}
                          </Text>
                        </VStack>
                        <Badge variant="outline">
                          <Text className="text-xs">{category.count}</Text>
                        </Badge>
                      </HStack>
                      <Icon
                        as={ChevronRightIcon}
                        size="sm"
                        className={`text-typography-400 ${
                          selectedCategory === category.id ? 'rotate-90' : ''
                        }`}
                      />
                    </HStack>
                  </Pressable>
                ))}
              </VStack>
            </VStack>

            {/* Articles */}
            <VStack space="md">
              <HStack className="items-center justify-between">
                <Heading size="lg" className="text-typography-900">
                  {selectedCategory
                    ? `Artigos - ${helpCategories.find(c => c.id === selectedCategory)?.title}`
                    : 'Artigos em Destaque'}
                </Heading>
                {selectedCategory && (
                  <Button size="sm" variant="outline" onPress={() => setSelectedCategory(null)}>
                    <ButtonText>Ver Todos</ButtonText>
                  </Button>
                )}
              </HStack>

              {filteredArticles.length === 0 ? (
                <Card className="p-8">
                  <VStack className="items-center" space="md">
                    <Icon as={SearchIcon} size="xl" className="text-typography-400" />
                    <Text className="text-lg font-semibold text-typography-700">
                      Nenhum artigo encontrado
                    </Text>
                    <Text className="text-center text-typography-600">
                      Tente pesquisar com outros termos ou navegue pelas categorias.
                    </Text>
                  </VStack>
                </Card>
              ) : (
                <VStack space="sm">
                  {filteredArticles.map(article => (
                    <Pressable
                      key={article.id}
                      onPress={() => handleArticlePress(article)}
                      className="p-4 bg-white rounded-lg border border-border-200"
                    >
                      <HStack className="items-start" space="md">
                        <Box className="w-12 h-12 bg-primary-100 rounded-lg items-center justify-center">
                          <Icon
                            as={getTypeIcon(article.type)}
                            size="md"
                            className="text-primary-600"
                          />
                        </Box>
                        <VStack className="flex-1" space="sm">
                          <HStack className="items-start justify-between">
                            <VStack className="flex-1" space="xs">
                              <Text className="font-semibold text-typography-900">
                                {article.title}
                              </Text>
                              <Text className="text-sm text-typography-600">
                                {article.description}
                              </Text>
                            </VStack>
                            <Icon
                              as={article.isExternal ? ExternalLinkIcon : ChevronRightIcon}
                              size="sm"
                              className="text-typography-400 mt-1"
                            />
                          </HStack>

                          {/* Badges */}
                          {article.badges && (
                            <ScrollView
                              horizontal
                              showsHorizontalScrollIndicator={false}
                              contentContainerStyle={{ gap: 6 }}
                            >
                              {article.badges.map(badge => (
                                <Badge key={badge} size="sm" className={getBadgeColor(badge)}>
                                  <Text className="text-xs">{badge}</Text>
                                </Badge>
                              ))}
                            </ScrollView>
                          )}

                          {/* Meta info */}
                          <HStack className="items-center" space="md">
                            {article.estimatedReadTime && (
                              <Text className="text-xs text-typography-500">
                                📖 {article.estimatedReadTime}
                              </Text>
                            )}
                            {article.difficulty && (
                              <Text className={`text-xs ${getDifficultyColor(article.difficulty)}`}>
                                ●{' '}
                                {article.difficulty === 'beginner'
                                  ? 'Iniciante'
                                  : article.difficulty === 'intermediate'
                                    ? 'Intermediário'
                                    : 'Avançado'}
                              </Text>
                            )}
                            {article.lastUpdated && (
                              <Text className="text-xs text-typography-500">
                                Atualizado {article.lastUpdated}
                              </Text>
                            )}
                          </HStack>
                        </VStack>
                      </HStack>
                    </Pressable>
                  ))}
                </VStack>
              )}
            </VStack>

            {/* Contact Support Section */}
            <Card className="p-6 bg-gradient-to-r from-primary-50 to-secondary-50">
              <VStack space="md">
                <HStack className="items-center" space="sm">
                  <Icon as={MessageSquareIcon} size="lg" className="text-primary-600" />
                  <Heading size="lg" className="text-typography-900">
                    Ainda precisa de ajuda?
                  </Heading>
                </HStack>
                <Text className="text-typography-600">
                  Nossa equipe de suporte está sempre pronta para ajudar você a resolver qualquer
                  questão.
                </Text>
                <HStack space="sm">
                  <Button
                    size="md"
                    onPress={() => {
                      if (isWeb()) {
                        window.open('mailto:suporte@aprendecomigo.com', '_blank');
                      } else {
                        Linking.openURL('mailto:suporte@aprendecomigo.com');
                      }
                    }}
                  >
                    <ButtonText>Enviar Email</ButtonText>
                  </Button>
                  <Button
                    size="md"
                    variant="outline"
                    onPress={() => {
                      if (isWeb()) {
                        window.open('https://wa.me/5511999999999', '_blank');
                      } else {
                        Linking.openURL('https://wa.me/5511999999999');
                      }
                    }}
                  >
                    <ButtonText>WhatsApp</ButtonText>
                  </Button>
                </HStack>
              </VStack>
            </Card>
          </VStack>
        </ScrollView>
      </SafeAreaView>
    </MainLayout>
  );
}
