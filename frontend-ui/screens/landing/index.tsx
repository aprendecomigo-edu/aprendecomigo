import useRouter from '@unitools/router';
import { CheckCircle, Star, Users, GraduationCap, Heart, Building, BookOpen, TrendingUp, Shield, Award, Clock, BarChart3 } from 'lucide-react-native';
import React, { useState, createContext, useContext } from 'react';
import { ScrollView, Platform } from 'react-native';

import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Input, InputField } from '@/components/ui/input';
import { Text } from '@/components/ui/text';
import { Textarea, TextareaInput } from '@/components/ui/textarea';
import { VStack } from '@/components/ui/vstack';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { PricingPlanSelector } from '@/components/purchase';

// User Type Context
type UserType = 'schools' | 'teachers' | 'families';

interface UserTypeContextType {
  selectedUserType: UserType;
  setSelectedUserType: (type: UserType) => void;
}

const UserTypeContext = createContext<UserTypeContextType>({
  selectedUserType: 'schools',
  setSelectedUserType: () => {}
});

const useUserType = () => useContext(UserTypeContext);

// Header Component with Sticky Navigation
const StickyHeader = () => {
  const router = useRouter();

  return (
    <Box className="bg-white/95 backdrop-blur-md sticky top-0 z-50 shadow-sm border-b border-gray-100">
      <Box className="container mx-auto px-4">
        <HStack className="items-center justify-between py-4">
          <Heading size="3xl" className="text-gray-900 font-bold">
            Aprende Comigo
          </Heading>
          <HStack space="md" className="items-center">
            <Button 
              variant="link" 
              onPress={() => router.push('/auth/signin')}
              className="hidden sm:flex"
            >
              <ButtonText className="text-sm font-medium text-gray-600 hover:text-indigo-600">
                Entrar
              </ButtonText>
            </Button>
            <Button 
              onPress={() => router.push('/auth/signup')}
              className="bg-indigo-600 hover:bg-indigo-700 rounded-lg px-6 py-2.5 shadow-lg transition-all duration-300"
            >
              <ButtonText className="text-sm font-semibold text-white">
                Começar Agora
              </ButtonText>
            </Button>
          </HStack>
        </HStack>
      </Box>
    </Box>
  );
};

// User Type Selector Component
const UserTypeSelector = () => {
  const { selectedUserType, setSelectedUserType } = useUserType();

  const userTypes = [
    { id: 'schools' as UserType, label: 'Escolas', icon: Building },
    { id: 'teachers' as UserType, label: 'Professores', icon: GraduationCap },
    { id: 'families' as UserType, label: 'Famílias', icon: Heart }
  ];

  return (
    <HStack space="xs" className="justify-center mb-8">
      {userTypes.map((type) => {
        const IconComponent = type.icon;
        const isSelected = selectedUserType === type.id;
        return (
          <Button
            key={type.id}
            onPress={() => setSelectedUserType(type.id)}
            className={`px-6 py-3 rounded-lg border-2 transition-all duration-300 ${
              isSelected 
                ? 'bg-indigo-600 border-indigo-600' 
                : 'bg-white border-gray-200 hover:border-indigo-300'
            }`}
          >
            <HStack space="xs" className="items-center">
              <Icon 
                as={IconComponent} 
                className={`w-4 h-4 ${
                  isSelected ? 'text-white' : 'text-gray-600'
                }`} 
              />
              <ButtonText className={`text-sm font-medium ${
                isSelected ? 'text-white' : 'text-gray-700'
              }`}>
                {type.label}
              </ButtonText>
            </HStack>
          </Button>
        );
      })}
    </HStack>
  );
};

// Dynamic Content Component
const DynamicHeroContent = () => {
  const { selectedUserType } = useUserType();
  const router = useRouter();

  const content = {
    schools: {
      headline: "Transforme a Gestão Educacional da Sua Escola",
      subtitle: "Plataforma completa para administrar 50-500 alunos com visibilidade total",
      benefits: [
        "Compensação automática de professores",
        "Monitorização em tempo real",
        "Relatórios detalhados de progresso",
        "Gestão multi-institucional"
      ],
      cta: "Agendar Demo Administrativa",
      metrics: "€15.000-90.000/ano de receita potencial"
    },
    teachers: {
      headline: "Ganhe €500-2.000/Mês Ensinando em Múltiplas Escolas",
      subtitle: "Junte-se à rede de educadores qualificados e maximize o seu rendimento",
      benefits: [
        "Oportunidades em múltiplas escolas",
        "Pagamentos transparentes e automáticos",
        "Horários flexíveis e personalizados",
        "Ferramentas de ensino avançadas"
      ],
      cta: "Candidatar-se a Educador",
      metrics: "Rendimento suplementar garantido"
    },
    families: {
      headline: "Acompanhe o Progresso do Seu Filho com Tutores Certificados",
      subtitle: "Investimento €50-300/mês com resultados visíveis e acompanhamento completo",
      benefits: [
        "Tutores verificados e qualificados",
        "Relatórios detalhados de progresso",
        "Apoio personalizado 1º-12º ano",
        "Plataforma segura e confiável"
      ],
      cta: "Começar Teste Grátis",
      metrics: "Melhoria média de 2 pontos nas notas"
    }
  };

  const currentContent = content[selectedUserType];

  return (
    <VStack space="lg" className="flex-1 lg:pr-8 text-center lg:text-left">
      <VStack space="sm">
        <Text className="text-sm font-semibold text-indigo-600 uppercase tracking-wide">
          {currentContent.metrics}
        </Text>
        <Heading 
          className="text-4xl md:text-5xl lg:text-6xl font-extrabold tracking-tight text-gray-900 leading-tight"
          accessibilityRole="header"
          accessibilityLevel={1}
        >
          {currentContent.headline}
        </Heading>
        <Text className="mt-4 text-xl text-gray-600 leading-relaxed">
          {currentContent.subtitle}
        </Text>
      </VStack>

      <VStack space="xs" className="mt-6">
        {currentContent.benefits.map((benefit, index) => (
          <HStack key={index} space="sm" className="items-center justify-center lg:justify-start">
            <Icon as={CheckCircle} className="w-5 h-5 text-green-500" />
            <Text className="text-gray-700 font-medium">{benefit}</Text>
          </HStack>
        ))}
      </VStack>

      <Button 
        onPress={() => router.push('/auth/signup')}
        className="mt-8 bg-indigo-600 hover:bg-indigo-700 rounded-lg px-10 py-4 w-fit mx-auto lg:mx-0 shadow-xl transition-all duration-300 transform hover:scale-105"
      >
        <ButtonText className="text-base font-semibold text-white">
          {currentContent.cta}
        </ButtonText>
      </Button>
    </VStack>
  );
};

// Hero Section with Multi-Segment Support
const HeroSection = () => {
  return (
    <Box className="relative bg-gradient-to-br from-gray-50 to-white py-20 lg:py-28">
      <Box className="container mx-auto px-4">
        <UserTypeSelector />
        
        <HStack className="lg:grid-cols-2 gap-12 items-center flex-col lg:flex-row">
          <DynamicHeroContent />
          
          <Box className="flex-1 relative mt-12 lg:mt-0">
            <Box className="w-full h-auto rounded-2xl shadow-2xl overflow-hidden bg-white border border-gray-200">
              <Box className="w-full h-96 bg-gradient-to-br from-indigo-50 via-white to-purple-50 items-center justify-center p-8">
                <VStack space="md" className="items-center text-center">
                  <Box className="w-16 h-16 bg-indigo-100 rounded-2xl items-center justify-center mb-4">
                    <Icon as={BarChart3} className="w-8 h-8 text-indigo-600" />
                  </Box>
                  <Text className="text-gray-700 text-lg font-semibold">
                    Dashboard Administrativo
                  </Text>
                  <Text className="text-gray-500 text-sm leading-relaxed">
                    Visualização completa de métricas de desempenho,
                    gestão de utilizadores e relatórios em tempo real
                  </Text>
                  <Box className="mt-6 w-full h-32 bg-white rounded-lg shadow-sm border border-gray-100 items-center justify-center">
                    <Text className="text-gray-400 text-xs">
                      [Screenshot da plataforma]
                    </Text>
                  </Box>
                </VStack>
              </Box>
            </Box>
          </Box>
        </HStack>
      </Box>
    </Box>
  );
};

// Pricing Section
const PricingSection = () => {
  const router = useRouter();
  const { selectedUserType } = useUserType();
  
  const handlePlanSelect = (plan: any) => {
    // For the landing page, we'll navigate to the purchase page
    // where the full purchase flow is available
    router.push('/purchase');
  };

  // Only show pricing for families - schools and teachers have custom pricing
  if (selectedUserType !== 'families') {
    return null;
  }

  return (
    <Box className="py-16 sm:py-24 bg-gray-50">
      <Box className="container mx-auto px-4">
        <VStack space="lg" className="text-center mb-16">
          <Heading className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
            Planos Para Famílias
          </Heading>
          <Text className="mt-4 text-lg text-gray-600">
            Escolha o plano ideal para o sucesso académico do seu filho
          </Text>
        </VStack>
        <PricingPlanSelector
          onPlanSelect={handlePlanSelect}
          className="max-w-6xl mx-auto"
        />
      </Box>
    </Box>
  );
};

// Testimonials Section
const TestimonialsSection = () => {
  const testimonials = [
    {
      name: "Escola Secundária do Porto",
      role: "Administração Escolar",
      content: "Escola Secundária do Porto reduziu custos administrativos em 40%",
      avatar: "ESP"
    },
    {
      name: "Prof. Maria Santos", 
      role: "Professora de Matemática",
      content: "Prof. Maria Santos: €1,200/mês extra ensinando em 3 escolas",
      avatar: "MS"
    },
    {
      name: "Família Oliveira",
      role: "Pais de Estudante",
      content: "Família Oliveira: +2 pontos nas notas em 6 meses",
      avatar: "FO"
    }
  ];

  return (
    <Box className="bg-white py-16 sm:py-24">
      <Box className="container mx-auto px-4">
        <VStack space="lg" className="text-center">
          <Heading className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
            O Que Dizem os Nossos Clientes
          </Heading>
          <Text className="mt-4 text-lg text-gray-600">
            Histórias reais de sucesso na nossa plataforma educacional.
          </Text>
        </VStack>

        <VStack space="lg" className="mt-16 grid-cols-1 gap-8">
          {testimonials.map((testimonial, index) => (
            <Card key={index} className="bg-gray-100 p-8 rounded-3xl shadow-lg">
              <VStack space="lg">
                <HStack space="md" className="items-center gap-4">
                  <Box className="w-16 h-16 rounded-full items-center justify-center bg-indigo-600">
                    <Text className="text-white font-bold text-lg">
                      {testimonial.avatar}
                    </Text>
                  </Box>
                  <VStack space="xs">
                    <Heading className="text-xl font-semibold text-gray-900">
                      {testimonial.name}
                    </Heading>
                    <Text className="text-gray-600">{testimonial.role}</Text>
                  </VStack>
                </HStack>
                <Text className="mt-6 text-gray-700 text-lg leading-relaxed">
                  "{testimonial.content}"
                </Text>
              </VStack>
            </Card>
          ))}
        </VStack>
      </Box>
    </Box>
  );
};

// Call-to-Action Section
const CTASection = () => {
  const router = useRouter();

  return (
    <Box className="bg-gray-50 py-16 sm:py-24">
      <Box className="container mx-auto px-4 text-center">
        <Heading className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
          Pronto Para Começar?
        </Heading>
        <Text className="mt-4 text-lg text-gray-600">
          Junte-se a milhares de estudantes e descubra o seu potencial académico completo.
        </Text>
        <Button 
          onPress={() => router.push('/auth/signup')}
          className="mt-8 bg-indigo-600 hover:bg-indigo-700 rounded-full px-8 py-4 shadow-lg transition-all duration-300 transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
        >
          <ButtonText className="text-base font-semibold text-white">
            Encontrar o Seu Tutor Agora
          </ButtonText>
        </Button>
      </Box>
    </Box>
  );
};

// Contact Form Section  
const ContactSection = () => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    message: ''
  });

  const handleSubmit = () => {
    // TODO: Implement contact form submission
    console.log('Contact form submitted:', formData);
  };

  return (
    <Box className="bg-white py-16 sm:py-24">
      <Box className="container mx-auto px-4">
        <VStack space="lg" className="text-center">
          <Heading className="text-center text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
            Contacte-nos
          </Heading>
          <Text className="mt-4 text-center text-lg text-gray-600">
            Tem questões? Adoraríamos ouvir de si.
          </Text>
        </VStack>

        <Box className="mt-12 max-w-lg mx-auto">
          <VStack space="lg">
            <VStack space="xs">
              <Text className="block text-sm font-medium text-gray-700">Nome Completo</Text>
              <Input className="mt-1">
                <InputField
                  placeholder="O seu nome completo"
                  value={formData.name}
                  onChangeText={(value) => setFormData(prev => ({ ...prev, name: value }))}
                  className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm py-3 px-4"
                />
              </Input>
            </VStack>

            <VStack space="xs">
              <Text className="block text-sm font-medium text-gray-700">Endereço de Email</Text>
              <Input className="mt-1">
                <InputField
                  placeholder="seu.email@exemplo.com"
                  value={formData.email}
                  onChangeText={(value) => setFormData(prev => ({ ...prev, email: value }))}
                  keyboardType="email-address"
                  className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm py-3 px-4"
                />
              </Input>
            </VStack>

            <VStack space="xs">
              <Text className="block text-sm font-medium text-gray-700">Mensagem</Text>
              <Textarea className="mt-1">
                <TextareaInput
                  placeholder="Diga-nos como podemos ajudá-lo..."
                  value={formData.message}
                  onChangeText={(value) => setFormData(prev => ({ ...prev, message: value }))}
                  className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm py-3 px-4"
                />
              </Textarea>
            </VStack>

            <Button 
              onPress={handleSubmit}
              className="w-full bg-indigo-600 hover:bg-indigo-700 rounded-full px-6 py-3 shadow-lg transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
            >
              <ButtonText className="text-base font-semibold text-white justify-center">
                Enviar Mensagem
              </ButtonText>
            </Button>
          </VStack>
        </Box>
      </Box>
    </Box>
  );
};

// Footer
const Footer = () => {
  const router = useRouter();

  return (
    <Box className="bg-gray-900 text-white">
      <Box className="container mx-auto px-4 py-12">
        <HStack className="flex-col items-center justify-between gap-8 md:flex-row">
          <VStack space="sm" className="text-center md:text-left">
            <Heading className="text-2xl font-bold text-white">
              Aprende Comigo
            </Heading>
            <Text className="mt-2 text-gray-400">Desbloqueie o seu potencial.</Text>
          </VStack>

          <HStack className="flex-wrap justify-center gap-x-6 gap-y-2 md:justify-start">
            <Button variant="link" onPress={() => {}}>
              <ButtonText className="text-sm text-gray-400 hover:text-white">Sobre</ButtonText>
            </Button>
            <Button variant="link" onPress={() => router.push('/parents')}>
              <ButtonText className="text-sm text-gray-400 hover:text-white">Preços</ButtonText>
            </Button>
            <Button variant="link" onPress={() => {}}>
              <ButtonText className="text-sm text-gray-400 hover:text-white">Contacto</ButtonText>
            </Button>
            <Button variant="link" onPress={() => {}}>
              <ButtonText className="text-sm text-gray-400 hover:text-white">Termos</ButtonText>
            </Button>
          </HStack>
        </HStack>

        <Box className="mt-8 border-t border-gray-800 pt-8">
          <HStack className="flex-col items-center justify-between gap-4 md:flex-row">
            <Text className="text-sm text-gray-500">
              © 2024 Aprende Comigo. Todos os direitos reservados.
            </Text>
            <HStack space="md" className="gap-4">
              <Text className="text-gray-500 text-sm hover:text-white">🐦</Text>
              <Text className="text-gray-500 text-sm hover:text-white">📘</Text>
              <Text className="text-gray-500 text-sm hover:text-white">💼</Text>
            </HStack>
          </HStack>
        </Box>
      </Box>
    </Box>
  );
};

// Main Landing Page Component
const LandingContent = () => {
  const [selectedUserType, setSelectedUserType] = useState<UserType>('schools');

  return (
    <UserTypeContext.Provider value={{ selectedUserType, setSelectedUserType }}>
      <ScrollView className="flex-1 bg-white">
        <VStack className="relative size-full min-h-screen flex-col justify-between overflow-x-hidden">
          <VStack>
            <StickyHeader />
            <HeroSection />
            <TestimonialsSection />
            <PricingSection />
            <CTASection />
            <ContactSection />
          </VStack>
          <Footer />
        </VStack>
      </ScrollView>
    </UserTypeContext.Provider>
  );
};

export const Landing = () => (
  <ErrorBoundary
    onError={(error, errorInfo) => {
      console.error('Landing page error:', error, errorInfo);
    }}
  >
    <LandingContent />
  </ErrorBoundary>
);