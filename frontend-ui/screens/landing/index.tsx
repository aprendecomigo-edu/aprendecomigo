import useRouter from '@unitools/router';
import { CheckCircle, Star } from 'lucide-react-native';
import React, { useState } from 'react';
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

// Header Component with Sticky Navigation
const StickyHeader = () => {
  const router = useRouter();

  return (
    <Box className="bg-white/90 backdrop-blur-md sticky top-0 z-50 shadow-sm">
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
                Sign In
              </ButtonText>
            </Button>
            <Button 
              onPress={() => router.push('/auth/signup')}
              className="bg-indigo-600 hover:bg-indigo-700 rounded-full px-5 py-2.5 shadow-lg transition-all duration-300"
            >
              <ButtonText className="text-sm font-semibold text-white">
                Sign Up
              </ButtonText>
            </Button>
          </HStack>
        </HStack>
      </Box>
    </Box>
  );
};

// Hero Section
const HeroSection = () => {
  const router = useRouter();

  return (
    <Box className="relative bg-white py-20">
      <Box className="container mx-auto px-4">
        <HStack className="lg:grid-cols-2 gap-12 items-center flex-col lg:flex-row">
          <VStack space="lg" className="flex-1 lg:pr-8">
            <Heading 
              className="text-4xl md:text-5xl lg:text-6xl font-extrabold tracking-tight text-gray-900 leading-tight"
              accessibilityRole="header"
              accessibilityLevel={1}
            >
              Unlock Your Potential with Expert Tutoring
            </Heading>
            <Text className="mt-6 text-lg text-gray-600 leading-relaxed">
              Connect with top-rated tutors for personalized learning experiences. 
              Achieve your academic goals with our flexible and effective tutoring platform.
            </Text>
            <Button 
              onPress={() => router.push('/auth/signup')}
              className="mt-8 bg-indigo-600 hover:bg-indigo-700 rounded-full px-8 py-4 w-fit shadow-lg transition-all duration-300 transform hover:scale-105"
            >
              <ButtonText className="text-base font-semibold text-white">
                Get Started
              </ButtonText>
            </Button>
          </VStack>
          
          <Box className="flex-1 relative mt-12 lg:mt-0">
            <Box className="w-full h-auto rounded-3xl shadow-2xl overflow-hidden transform hover:rotate-1 transition-transform duration-500">
              <Box className="w-full h-80 bg-gradient-to-br from-indigo-100 to-purple-100 items-center justify-center">
                <VStack space="sm" className="items-center text-center px-6">
                  <Text className="text-gray-600 text-lg font-medium">
                    Hero Image
                  </Text>
                  <Text className="text-gray-500 text-sm">
                    Study scene illustration would go here
                  </Text>
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

  const PricingCard = ({ 
    title, 
    price, 
    period, 
    description, 
    features, 
    buttonText, 
    isPopular = false 
  }: {
    title: string;
    price: string;
    period: string;
    description: string;
    features: string[];
    buttonText: string;
    isPopular?: boolean;
  }) => (
    <Card className={`flex-1 rounded-3xl bg-white shadow-xl transform hover:-translate-y-2 transition-transform duration-300 ${isPopular ? 'ring-2 ring-indigo-600' : ''}`}>
      <VStack className="flex-1 p-8" space="lg">
        {isPopular && (
          <Box className="absolute top-0 left-1/2 transform -translate-x-1/2 -translate-y-1/2 bg-indigo-600 px-4 py-1.5 rounded-full">
            <Text className="text-sm font-semibold text-white">Most Popular</Text>
          </Box>
        )}
        
        <VStack space="md" className="flex-1">
          <Heading className="text-xl font-semibold text-gray-900">
            {title}
          </Heading>
          <HStack className="items-baseline text-gray-900">
            <Text className="text-5xl font-extrabold tracking-tight">
              {price}
            </Text>
            <Text className="ml-1 text-xl font-semibold">
              {period}
            </Text>
          </HStack>
          <Text className="text-gray-500 mt-6">{description}</Text>
        </VStack>

        <VStack space="sm" className="mt-8 flex-1">
          {features.map((feature, index) => (
            <HStack key={index} space="sm" className="items-start">
              <Icon as={CheckCircle} className="h-6 w-6 text-green-500 flex-shrink-0" />
              <Text className="text-base text-gray-700 ml-3 flex-1">{feature}</Text>
            </HStack>
          ))}
        </VStack>

        <Button 
          onPress={() => router.push('/parents')}
          className={`w-full rounded-full px-6 py-3 shadow-md transition-colors ${
            isPopular 
              ? 'bg-indigo-600 hover:bg-indigo-700' 
              : 'bg-indigo-100 hover:bg-indigo-200'
          }`}
        >
          <ButtonText className={`font-semibold text-base text-center ${
            isPopular ? 'text-white' : 'text-indigo-600'
          }`}>
            {buttonText}
          </ButtonText>
        </Button>
      </VStack>
    </Card>
  );

  return (
    <Box className="py-16 sm:py-24 bg-gray-50">
      <Box className="container mx-auto px-4">
        <VStack space="lg" className="text-center">
          <Heading className="text-center text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
            Our Pricing Plans
          </Heading>
          <Text className="mt-4 text-center text-lg text-gray-600">
            Choose the plan that's right for you.
          </Text>
        </VStack>

        <HStack className="mt-16 grid-cols-1 gap-8 md:grid-cols-2 flex-col md:flex-row">
          <PricingCard
            title="Monthly Subscription"
            price="€49"
            period="/month"
            description="5 tutoring hours per month. Perfect for consistent progress."
            features={[
              "5 tutoring hours per month",
              "Access to all subjects",
              "Cancel anytime"
            ]}
            buttonText="Choose Plan"
          />

          <PricingCard
            title="One-Time Purchase"
            price="€79"
            period="/ 10 hours"
            description="10 tutoring hours. Flexible and valid for 3 months."
            features={[
              "10 tutoring hours",
              "Access to all subjects",
              "Valid for 3 months"
            ]}
            buttonText="Buy Now"
            isPopular={true}
          />
        </HStack>
      </Box>
    </Box>
  );
};

// Testimonials Section
const TestimonialsSection = () => {
  const testimonials = [
    {
      name: "Sarah J.",
      role: "University Student",
      content: "Aprende Comigo has been a game-changer for my studies. The tutors are incredibly knowledgeable and supportive. I've seen a significant improvement in my grades!",
      avatar: "SJ"
    },
    {
      name: "Michael B.", 
      role: "High School Student",
      content: "I was struggling with calculus, but my tutor broke down complex concepts into easy-to-understand lessons. Highly recommended!",
      avatar: "MB"
    }
  ];

  return (
    <Box className="bg-white py-16 sm:py-24">
      <Box className="container mx-auto px-4">
        <VStack space="lg" className="text-center">
          <Heading className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
            What Our Students Say
          </Heading>
          <Text className="mt-4 text-lg text-gray-600">
            Real stories from students who achieved their goals with us.
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
          Ready to Start Learning?
        </Heading>
        <Text className="mt-4 text-lg text-gray-600">
          Join thousands of students and unlock your full academic potential.
        </Text>
        <Button 
          onPress={() => router.push('/auth/signup')}
          className="mt-8 bg-indigo-600 hover:bg-indigo-700 rounded-full px-8 py-4 shadow-lg transition-all duration-300 transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
        >
          <ButtonText className="text-base font-semibold text-white">
            Find Your Tutor Now
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
            Contact Us
          </Heading>
          <Text className="mt-4 text-center text-lg text-gray-600">
            Have questions? We'd love to hear from you.
          </Text>
        </VStack>

        <Box className="mt-12 max-w-lg mx-auto">
          <VStack space="lg">
            <VStack space="xs">
              <Text className="block text-sm font-medium text-gray-700">Full Name</Text>
              <Input className="mt-1">
                <InputField
                  placeholder="Your full name"
                  value={formData.name}
                  onChangeText={(value) => setFormData(prev => ({ ...prev, name: value }))}
                  className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm py-3 px-4"
                />
              </Input>
            </VStack>

            <VStack space="xs">
              <Text className="block text-sm font-medium text-gray-700">Email Address</Text>
              <Input className="mt-1">
                <InputField
                  placeholder="your.email@example.com"
                  value={formData.email}
                  onChangeText={(value) => setFormData(prev => ({ ...prev, email: value }))}
                  keyboardType="email-address"
                  className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm py-3 px-4"
                />
              </Input>
            </VStack>

            <VStack space="xs">
              <Text className="block text-sm font-medium text-gray-700">Message</Text>
              <Textarea className="mt-1">
                <TextareaInput
                  placeholder="Tell us how we can help you..."
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
                Send Message
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
            <Text className="mt-2 text-gray-400">Unlock your potential.</Text>
          </VStack>

          <HStack className="flex-wrap justify-center gap-x-6 gap-y-2 md:justify-start">
            <Button variant="link" onPress={() => {}}>
              <ButtonText className="text-sm text-gray-400 hover:text-white">About</ButtonText>
            </Button>
            <Button variant="link" onPress={() => router.push('/parents')}>
              <ButtonText className="text-sm text-gray-400 hover:text-white">Pricing</ButtonText>
            </Button>
            <Button variant="link" onPress={() => {}}>
              <ButtonText className="text-sm text-gray-400 hover:text-white">Contact</ButtonText>
            </Button>
            <Button variant="link" onPress={() => {}}>
              <ButtonText className="text-sm text-gray-400 hover:text-white">Terms</ButtonText>
            </Button>
          </HStack>
        </HStack>

        <Box className="mt-8 border-t border-gray-800 pt-8">
          <HStack className="flex-col items-center justify-between gap-4 md:flex-row">
            <Text className="text-sm text-gray-500">
              © 2024 Aprende Comigo. All rights reserved.
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
  return (
    <ScrollView className="flex-1 bg-gray-50">
      <VStack className="relative size-full min-h-screen flex-col justify-between overflow-x-hidden">
        <VStack>
          <StickyHeader />
          <HeroSection />
          <PricingSection />
          <TestimonialsSection />
          <CTASection />
          <ContactSection />
        </VStack>
        <Footer />
      </VStack>
    </ScrollView>
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