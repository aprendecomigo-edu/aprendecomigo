import { isWeb } from '@gluestack-ui/nativewind-utils/IsWeb';
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

import MainLayout from '@/components/layouts/main-layout';
import { Badge } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Input, InputField } from '@/components/ui/input';
import { Pressable } from '@/components/ui/pressable';
import { ScrollView } from '@/components/ui/scroll-view';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

interface HelpArticle {
  id: string;
  title: string;
  category: string;
  description: string;
  content: string;
  tags: string[];
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  readTime: number;
  videoUrl?: string;
}

interface HelpCategory {
  id: string;
  name: string;
  description: string;
  icon: any;
  color: string;
  articles: HelpArticle[];
}

const CommunicationHelpPage = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [selectedArticle, setSelectedArticle] = useState<HelpArticle | null>(null);

  // Mock help content (in real app, this would come from API)
  const helpCategories: HelpCategory[] = useMemo(() => [
    {
      id: 'getting-started',
      name: 'Getting Started',
      description: 'Learn the basics of teacher communication',
      icon: PlayCircleIcon,
      color: 'bg-blue-100 text-blue-800',
      articles: [
        {
          id: 'first-template',
          title: 'Creating Your First Email Template',
          category: 'getting-started',
          description: 'Step-by-step guide to creating your first teacher invitation template',
          content: `# Creating Your First Email Template

Welcome to the Teacher Communication System! This guide will walk you through creating your first email template.

## Step 1: Choose Template Type
1. Go to Communication > Templates > New Template
2. Select the template type (Invitation, Reminder, Welcome, etc.)
3. Give your template a descriptive name

## Step 2: Configure Settings
- Enable school branding to use your colors and logo
- Set the template as active when ready to use

## Step 3: Write Your Content
### Subject Line
- Keep it clear and actionable
- Use variables like {{teacher_name}} for personalization
- Example: "Join {{school_name}} - Complete Your Teacher Profile"

### Email Content
- Start with a warm greeting
- Clearly explain what the teacher needs to do
- Include a clear call-to-action button
- End with contact information

## Step 4: Use Template Variables
Available variables:
- {{teacher_name}} - Teacher's full name
- {{school_name}} - Your school's name
- {{invitation_link}} - Direct link to complete setup
- {{deadline}} - Deadline for completion
- {{contact_email}} - School contact email

## Step 5: Preview and Test
1. Use the Preview tab to see how it looks
2. Send a test email to yourself
3. Check both desktop and mobile views

## Best Practices
- Keep emails concise and action-oriented
- Use your school's voice and tone
- Always test before activating
- Include clear next steps`,
          tags: ['template', 'email', 'basic', 'setup'],
          difficulty: 'beginner',
          readTime: 5,
          videoUrl: 'https://example.com/video1',
        },
        {
          id: 'school-branding',
          title: 'Setting Up School Branding',
          category: 'getting-started',
          description: 'Configure your school\'s visual identity for emails',
          content: `# Setting Up School Branding

Make your emails reflect your school's identity with custom branding.

## Upload Your Logo
1. Go to Communication > Branding
2. Click "Upload Logo"
3. Select a high-quality PNG or JPG file
4. Recommended size: 400x200 pixels

## Choose Your Colors
### Primary Color
- Used for headers, buttons, and main accents
- Should match your school's main brand color
- Example: #3B82F6 (blue)

### Secondary Color
- Used for text and subtle elements
- Usually a neutral color like dark gray
- Example: #1F2937 (dark gray)

## Custom Messaging
Add a special message that appears in highlighted sections:
- School motto or mission statement
- Welcome message for new teachers
- Key values or culture points

## Email Footer
Customize the footer that appears in all emails:
- Contact information
- School address
- Professional closing

## Preview Your Branding
Always preview how your branding looks:
1. Click "Generate Preview"
2. Review the sample email
3. Make adjustments as needed
4. Save your changes

Your branding will automatically apply to all new emails!`,
          tags: ['branding', 'logo', 'colors', 'setup'],
          difficulty: 'beginner',
          readTime: 4,
        },
      ],
    },
    {
      id: 'templates',
      name: 'Email Templates',
      description: 'Master template creation and management',
      icon: MailIcon,
      color: 'bg-green-100 text-green-800',
      articles: [
        {
          id: 'template-variables',
          title: 'Using Template Variables',
          category: 'templates',
          description: 'Learn how to personalize emails with dynamic variables',
          content: `# Using Template Variables

Template variables make your emails personal and dynamic. Here's how to use them effectively.

## Available Variable Categories

### Teacher Variables
- {{teacher_name}} - Full name
- {{teacher_first_name}} - First name only
- {{teacher_email}} - Email address
- {{teacher_phone}} - Phone number

### School Variables
- {{school_name}} - Your school's name
- {{school_address}} - Physical address
- {{school_phone}} - Main phone number
- {{school_website}} - Website URL

### Invitation Variables
- {{invitation_link}} - Secure signup link
- {{invitation_token}} - Unique invitation code
- {{expiry_date}} - When invitation expires
- {{deadline}} - Completion deadline

### System Variables
- {{current_date}} - Today's date
- {{current_year}} - Current year
- {{support_email}} - Help desk email
- {{unsubscribe_link}} - Opt-out link

## How to Insert Variables
1. Place cursor where you want the variable
2. Click the "Variables" button in the editor
3. Select from the available options
4. Variable appears as {{variable_name}}

## Variable Formatting
Variables can include formatting:
- {{teacher_name|title}} - Title case
- {{current_date|date:"F j, Y"}} - Formatted date
- {{school_name|upper}} - Uppercase

## Best Practices
- Always test with real data
- Have fallbacks for missing data
- Don't overuse variables
- Keep variable names readable

## Common Mistakes to Avoid
- Typos in variable names
- Missing opening or closing braces
- Using undefined variables
- Not testing with different data`,
          tags: ['variables', 'personalization', 'advanced'],
          difficulty: 'intermediate',
          readTime: 7,
        },
        {
          id: 'email-sequences',
          title: 'Creating Email Sequences',
          category: 'templates',
          description: 'Set up automated follow-up sequences for better engagement',
          content: `# Creating Email Sequences

Automated email sequences ensure no teacher falls through the cracks.

## Types of Sequences

### Invitation Sequence
1. **Initial Invitation** - Welcome and setup instructions
2. **First Reminder** - Gentle nudge after 3 days
3. **Second Reminder** - More urgent after 7 days
4. **Final Reminder** - Last chance after 14 days

### Welcome Sequence
1. **Welcome Email** - Immediate after signup
2. **Getting Started** - 1 day later with resources
3. **First Week Check-in** - 7 days later
4. **30-Day Follow-up** - Monthly check-in

## Setting Up Sequences
1. Go to Communication > Settings
2. Enable the sequence type you want
3. Set the timing (days between emails)
4. Choose which templates to use
5. Test the sequence with yourself

## Sequence Best Practices
- Start with a warm welcome
- Provide value in each email
- Include clear next steps
- Monitor engagement rates
- Adjust timing based on results

## Timing Recommendations
- **Day 1**: Send immediately
- **Day 3**: First gentle reminder
- **Day 7**: More detailed follow-up
- **Day 14**: Final urgent reminder

## Monitoring Sequences
Track performance metrics:
- Open rates by email in sequence
- Click rates on action buttons
- Completion rates
- Unsubscribe rates

Optimize based on data!`,
          tags: ['sequences', 'automation', 'follow-up'],
          difficulty: 'intermediate',
          readTime: 8,
        },
      ],
    },
    {
      id: 'analytics',
      name: 'Analytics & Reporting',
      description: 'Understand your email performance',
      icon: BarChart3Icon,
      color: 'bg-purple-100 text-purple-800',
      articles: [
        {
          id: 'understanding-metrics',
          title: 'Understanding Email Metrics',
          category: 'analytics',
          description: 'Learn what each metric means and how to improve them',
          content: `# Understanding Email Metrics

Email analytics help you improve your communication effectiveness.

## Key Metrics Explained

### Delivery Rate
- **What it is**: Percentage of emails that reached inboxes
- **Good rate**: 95% or higher
- **How to improve**: Clean email lists, avoid spam triggers

### Open Rate
- **What it is**: Percentage of delivered emails that were opened
- **Good rate**: 20-25% for educational emails
- **How to improve**: Better subject lines, sender reputation

### Click Rate
- **What it is**: Percentage of opened emails where links were clicked
- **Good rate**: 3-5% for call-to-action emails
- **How to improve**: Clear CTAs, relevant content

### Bounce Rate
- **What it is**: Percentage of emails that couldn't be delivered
- **Good rate**: Less than 5%
- **How to improve**: Verify email addresses, remove invalid emails

## Reading Your Dashboard

### Overview Cards
Show high-level metrics for quick assessment

### Template Performance
Compare how different templates perform:
- Which get opened most
- Which drive the most action
- Which need improvement

### Recent Activity
Track individual email status:
- Sent, delivered, opened, clicked
- Failed emails and reasons
- Timeline of engagement

## Improving Your Metrics

### Better Subject Lines
- Keep under 50 characters
- Create urgency when appropriate
- Personalize with teacher names
- Ask questions to spark curiosity

### Optimize Send Times
- Tuesday-Thursday work best
- 9-11 AM in school timezone
- Avoid Mondays and Fridays
- Test different times

### Improve Content
- Mobile-first design
- Clear call-to-action buttons
- Relevant, valuable content
- Professional but friendly tone

### Clean Your Lists
- Remove bounced emails
- Segment by engagement
- Re-engage inactive contacts
- Respect unsubscribe requests`,
          tags: ['metrics', 'analytics', 'optimization'],
          difficulty: 'intermediate',
          readTime: 10,
        },
      ],
    },
    {
      id: 'troubleshooting',
      name: 'Troubleshooting',
      description: 'Solve common issues and problems',
      icon: HelpCircleIcon,
      color: 'bg-red-100 text-red-800',
      articles: [
        {
          id: 'common-issues',
          title: 'Common Issues and Solutions',
          category: 'troubleshooting',
          description: 'Quick fixes for the most common problems',
          content: `# Common Issues and Solutions

Quick solutions to frequent problems.

## Email Delivery Issues

### Emails Going to Spam
**Symptoms**: Teachers report not receiving emails
**Solutions**:
- Check sender reputation
- Avoid spam trigger words
- Include unsubscribe link
- Authenticate your domain

### High Bounce Rate
**Symptoms**: Many emails fail to deliver
**Solutions**:
- Verify email addresses before sending
- Clean your email list regularly
- Check for typos in email addresses
- Remove hard bounces immediately

### Low Open Rates
**Symptoms**: Few teachers open your emails
**Solutions**:
- Improve subject lines
- Send at optimal times
- Use school email domain
- Personalize sender name

## Template Issues

### Variables Not Working
**Symptoms**: {{variable_name}} appears in sent emails
**Solutions**:
- Check variable spelling
- Ensure proper braces: {{variable}}
- Verify variable exists in system
- Test with preview feature

### Formatting Problems
**Symptoms**: Email looks broken or ugly
**Solutions**:
- Test in multiple email clients
- Use simple, clean designs
- Avoid complex layouts
- Check mobile compatibility

### Missing School Branding
**Symptoms**: Emails don't show school colors/logo
**Solutions**:
- Enable "Use School Branding" option
- Upload logo in correct format
- Set primary/secondary colors
- Save branding settings

## System Issues

### Slow Loading
**Symptoms**: Pages take long to load
**Solutions**:
- Check internet connection
- Clear browser cache
- Try different browser
- Contact support if persistent

### Permission Errors
**Symptoms**: Cannot access certain features
**Solutions**:
- Verify your role permissions
- Log out and back in
- Contact school admin
- Check if feature is enabled

### Save Failures
**Symptoms**: Changes don't save
**Solutions**:
- Check all required fields
- Ensure stable internet
- Try saving smaller changes
- Refresh and try again

## Getting Help

### When to Contact Support
- System-wide outages
- Data loss or corruption  
- Permission issues
- Payment/billing problems

### What Information to Provide
- Your school name
- What you were trying to do
- Error messages (screenshot)
- Steps to reproduce
- Browser and device info

### Self-Help Resources
- Check this help center first
- Try the troubleshooting steps
- Test with different browsers
- Ask colleagues if they see same issue`,
          tags: ['troubleshooting', 'issues', 'fixes', 'support'],
          difficulty: 'beginner',
          readTime: 8,
        },
      ],
    },
  ], []);

  // Filter articles based on search and category
  const filteredArticles = useMemo(() => {
    let articles: HelpArticle[] = [];
    
    if (selectedCategory) {
      const category = helpCategories.find(cat => cat.id === selectedCategory);
      articles = category?.articles || [];
    } else {
      articles = helpCategories.flatMap(cat => cat.articles);
    }

    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      articles = articles.filter(article =>
        article.title.toLowerCase().includes(query) ||
        article.description.toLowerCase().includes(query) ||
        article.tags.some(tag => tag.toLowerCase().includes(query)) ||
        article.content.toLowerCase().includes(query)
      );
    }

    return articles;
  }, [searchQuery, selectedCategory, helpCategories]);

  // Handle article selection
  const selectArticle = useCallback((article: HelpArticle) => {
    setSelectedArticle(article);
  }, []);

  // Handle category selection
  const selectCategory = useCallback((categoryId: string) => {
    setSelectedCategory(categoryId === selectedCategory ? null : categoryId);
    setSelectedArticle(null);
  }, [selectedCategory]);

  // Get difficulty badge color
  const getDifficultyColor = useCallback((difficulty: HelpArticle['difficulty']) => {
    switch (difficulty) {
      case 'beginner': return 'bg-green-100 text-green-800';
      case 'intermediate': return 'bg-yellow-100 text-yellow-800';
      case 'advanced': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  }, []);

  // Open video link
  const openVideo = useCallback((url: string) => {
    if (isWeb) {
      window.open(url, '_blank');
    } else {
      Linking.openURL(url);
    }
  }, []);

  // If an article is selected, show article view
  if (selectedArticle) {
    return (
      <MainLayout _title={selectedArticle.title}>
        <ScrollView
          showsVerticalScrollIndicator={false}
          contentContainerStyle={{
            paddingBottom: isWeb ? 0 : 100,
            flexGrow: 1,
          }}
          className="flex-1 bg-gray-50"
        >
          <VStack className="p-6" space="lg">
            {/* Article Header */}
            <HStack className="justify-between items-start">
              <VStack space="xs" className="flex-1">
                <Button
                  onPress={() => setSelectedArticle(null)}
                  variant="link"
                  size="sm"
                  className="self-start -ml-2"
                >
                  <ButtonText>← Back to Help Center</ButtonText>
                </Button>
                
                <HStack space="sm" className="items-center flex-wrap">
                  <Heading size="xl" className="text-gray-900">
                    {selectedArticle.title}
                  </Heading>
                  <Badge className={getDifficultyColor(selectedArticle.difficulty)}>
                    <Text className="text-xs font-medium capitalize">
                      {selectedArticle.difficulty}
                    </Text>
                  </Badge>
                </HStack>

                <Text className="text-gray-600">{selectedArticle.description}</Text>
                
                <HStack space="md" className="items-center">
                  <Text className="text-sm text-gray-500">
                    {selectedArticle.readTime} min read
                  </Text>
                  {selectedArticle.videoUrl && (
                    <Button
                      onPress={() => openVideo(selectedArticle.videoUrl!)}
                      variant="link"
                      size="sm"
                    >
                      <HStack space="xs" className="items-center">
                        <Icon as={PlayCircleIcon} size="sm" className="text-blue-600" />
                        <ButtonText className="text-blue-600">Watch Video</ButtonText>
                      </HStack>
                    </Button>
                  )}
                </HStack>
              </VStack>
            </HStack>

            {/* Article Content */}
            <Card className="p-8">
              <VStack space="md">
                <Text className="text-gray-800 leading-relaxed" style={{ whiteSpace: 'pre-line' }}>
                  {selectedArticle.content}
                </Text>
              </VStack>
            </Card>

            {/* Article Tags */}
            <Card className="p-4">
              <VStack space="sm">
                <Text className="font-medium text-gray-900">Related Topics</Text>
                <HStack space="xs" className="flex-wrap">
                  {selectedArticle.tags.map((tag) => (
                    <Badge key={tag} className="bg-gray-100 text-gray-700">
                      <Text className="text-xs">{tag}</Text>
                    </Badge>
                  ))}
                </HStack>
              </VStack>
            </Card>

            {/* Quick Actions */}
            <Card className="p-6">
              <VStack space="md">
                <Text className="font-medium text-gray-900">Quick Actions</Text>
                
                <HStack space="sm" className="flex-wrap">
                  <Button
                    onPress={() => router.push('/(school-admin)/communication/templates/new')}
                    size="sm"
                    className="flex-1"
                  >
                    <ButtonText>Create Template</ButtonText>
                  </Button>

                  <Button
                    onPress={() => router.push('/(school-admin)/communication/branding')}
                    variant="outline"
                    size="sm"
                    className="flex-1"
                  >
                    <ButtonText>Setup Branding</ButtonText>
                  </Button>

                  <Button
                    onPress={() => router.push('/(school-admin)/communication/analytics')}
                    variant="outline"
                    size="sm"
                    className="flex-1"
                  >
                    <ButtonText>View Analytics</ButtonText>
                  </Button>
                </HStack>
              </VStack>
            </Card>
          </VStack>
        </ScrollView>
      </MainLayout>
    );
  }

  // Main help center view
  return (
    <ScrollView
      showsVerticalScrollIndicator={false}
      contentContainerStyle={{
        paddingBottom: isWeb ? 0 : 100,
        flexGrow: 1,
      }}
      className="flex-1 bg-gray-50"
    >
      <VStack className="p-6" space="lg">
        {/* Header */}
        <VStack space="xs">
          <Heading size="xl" className="text-gray-900">
            Communication Help Center
          </Heading>
          <Text className="text-gray-600">
            Learn how to effectively communicate with teachers using our email system
          </Text>
        </VStack>

        {/* Search */}
        <Card className="p-4">
          <VStack space="md">
            <Text className="font-medium text-gray-900">Search Help Articles</Text>
            <Input>
              <InputField
                placeholder="Search for help topics, tutorials, or guides..."
                value={searchQuery}
                onChangeText={setSearchQuery}
              />
            </Input>
            {searchQuery && (
              <Text className="text-sm text-gray-600">
                Found {filteredArticles.length} articles matching "{searchQuery}"
              </Text>
            )}
          </VStack>
        </Card>

        {/* Categories */}
        {!searchQuery && (
          <Card className="p-6">
            <VStack space="lg">
              <Text className="font-medium text-gray-900">Browse by Category</Text>
              
              <VStack space="md" className={isWeb ? 'lg:grid lg:grid-cols-2 lg:gap-4' : ''}>
                {helpCategories.map((category) => (
                  <Pressable
                    key={category.id}
                    onPress={() => selectCategory(category.id)}
                    className={`flex-row items-center p-4 rounded-lg border-2 ${
                      selectedCategory === category.id
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:bg-gray-50 active:bg-gray-50'
                    }`}
                  >
                    <Box className={`mr-4 p-3 rounded-full ${category.color}`}>
                      <Icon as={category.icon} size="sm" />
                    </Box>
                    <VStack space="xs" className="flex-1">
                      <Text className="font-medium text-gray-900">{category.name}</Text>
                      <Text className="text-sm text-gray-600">{category.description}</Text>
                      <Text className="text-xs text-gray-500">
                        {category.articles.length} articles
                      </Text>
                    </VStack>
                    <Icon as={ChevronRightIcon} size="sm" className="text-gray-400" />
                  </Pressable>
                ))}
              </VStack>
            </VStack>
          </Card>
        )}

        {/* Articles List */}
        {(searchQuery || selectedCategory) && (
          <Card className="p-6">
            <VStack space="lg">
              <HStack className="justify-between items-center">
                <Text className="font-medium text-gray-900">
                  {selectedCategory 
                    ? helpCategories.find(cat => cat.id === selectedCategory)?.name + ' Articles'
                    : 'Search Results'
                  }
                </Text>
                {selectedCategory && (
                  <Button
                    onPress={() => setSelectedCategory(null)}
                    variant="link"
                    size="sm"
                  >
                    <ButtonText>View All Categories</ButtonText>
                  </Button>
                )}
              </HStack>

              <VStack space="md">
                {filteredArticles.map((article) => (
                  <Pressable
                    key={article.id}
                    onPress={() => selectArticle(article)}
                    className="flex-row items-start p-4 bg-gray-50 rounded-lg hover:bg-gray-100 active:bg-gray-100"
                  >
                    <Box className="mr-4 p-2 bg-blue-100 rounded-full">
                      <Icon as={FileTextIcon} size="sm" className="text-blue-600" />
                    </Box>
                    <VStack space="xs" className="flex-1">
                      <HStack space="sm" className="items-center flex-wrap">
                        <Text className="font-medium text-gray-900">{article.title}</Text>
                        <Badge className={getDifficultyColor(article.difficulty)}>
                          <Text className="text-xs font-medium capitalize">
                            {article.difficulty}
                          </Text>
                        </Badge>
                        {article.videoUrl && (
                          <Badge className="bg-purple-100 text-purple-800">
                            <HStack space="xs" className="items-center">
                              <Icon as={VideoIcon} size="xs" />
                              <Text className="text-xs font-medium">Video</Text>
                            </HStack>
                          </Badge>
                        )}
                      </HStack>
                      <Text className="text-sm text-gray-600">{article.description}</Text>
                      <HStack space="md" className="items-center">
                        <Text className="text-xs text-gray-500">
                          {article.readTime} min read
                        </Text>
                        <HStack space="xs" className="items-center">
                          {article.tags.slice(0, 3).map((tag) => (
                            <Text key={tag} className="text-xs text-blue-600">
                              #{tag}
                            </Text>
                          ))}
                        </HStack>
                      </HStack>
                    </VStack>
                    <Icon as={ChevronRightIcon} size="sm" className="text-gray-400" />
                  </Pressable>
                ))}

                {filteredArticles.length === 0 && (
                  <VStack space="md" className="items-center py-8">
                    <Icon as={SearchIcon} size="xl" className="text-gray-400" />
                    <Text className="text-gray-600 text-center">
                      {searchQuery 
                        ? `No articles found for "${searchQuery}"`
                        : 'No articles in this category'
                      }
                    </Text>
                    <Button
                      onPress={() => {
                        setSearchQuery('');
                        setSelectedCategory(null);
                      }}
                      variant="outline"
                      size="sm"
                    >
                      <ButtonText>Clear Search</ButtonText>
                    </Button>
                  </VStack>
                )}
              </VStack>
            </VStack>
          </Card>
        )}

        {/* Quick Start Guide */}
        {!searchQuery && !selectedCategory && (
          <Card className="p-6 bg-gradient-to-r from-blue-50 to-purple-50 border-blue-200">
            <VStack space="lg">
              <VStack space="xs">
                <HStack space="sm" className="items-center">
                  <Icon as={LightbulbIcon} size="md" className="text-blue-600" />
                  <Heading size="md" className="text-blue-900">
                    Quick Start Guide
                  </Heading>
                </HStack>
                <Text className="text-blue-700">
                  New to the communication system? Start here for a quick setup.
                </Text>
              </VStack>

              <VStack space="sm">
                <HStack space="sm" className="items-center">
                  <Text className="text-blue-800 font-bold">1.</Text>
                  <Button
                    onPress={() => router.push('/(school-admin)/communication/branding')}
                    variant="link"
                    size="sm"
                    className="flex-1 justify-start"
                  >
                    <ButtonText className="text-blue-700">Set up your school branding</ButtonText>
                  </Button>
                </HStack>

                <HStack space="sm" className="items-center">
                  <Text className="text-blue-800 font-bold">2.</Text>
                  <Button
                    onPress={() => router.push('/(school-admin)/communication/templates/new')}
                    variant="link"
                    size="sm"
                    className="flex-1 justify-start"
                  >
                    <ButtonText className="text-blue-700">Create your first email template</ButtonText>
                  </Button>
                </HStack>

                <HStack space="sm" className="items-center">
                  <Text className="text-blue-800 font-bold">3.</Text>
                  <Button
                    onPress={() => router.push('/(school-admin)/communication/settings')}
                    variant="link"
                    size="sm"
                    className="flex-1 justify-start"
                  >
                    <ButtonText className="text-blue-700">Configure communication settings</ButtonText>
                  </Button>
                </HStack>

                <HStack space="sm" className="items-center">
                  <Text className="text-blue-800 font-bold">4.</Text>
                  <Button
                    onPress={() => selectArticle(helpCategories[0].articles[0])}
                    variant="link"
                    size="sm"
                    className="flex-1 justify-start"
                  >
                    <ButtonText className="text-blue-700">Read the getting started guide</ButtonText>
                  </Button>
                </HStack>
              </VStack>
            </VStack>
          </Card>
        )}

        {/* Contact Support */}
        <Card className="p-6">
          <VStack space="lg">
            <Text className="font-medium text-gray-900">Need More Help?</Text>
            
            <VStack space="md">
              <Text className="text-sm text-gray-600">
                Can't find what you're looking for? Our support team is here to help.
              </Text>

              <HStack space="sm" className="flex-wrap">
                <Button
                  onPress={() => {
                    if (isWeb) {
                      window.open('mailto:support@aprendecomigo.com?subject=Communication System Help');
                    } else {
                      Linking.openURL('mailto:support@aprendecomigo.com?subject=Communication System Help');
                    }
                  }}
                  variant="outline"
                  className="flex-1"
                >
                  <HStack space="xs" className="items-center">
                    <Icon as={MailIcon} size="sm" className="text-gray-600" />
                    <ButtonText>Email Support</ButtonText>
                  </HStack>
                </Button>

                <Button
                  onPress={() => {
                    if (isWeb) {
                      window.open('https://help.aprendecomigo.com', '_blank');
                    } else {
                      Linking.openURL('https://help.aprendecomigo.com');
                    }
                  }}
                  variant="outline"
                  className="flex-1"
                >
                  <HStack space="xs" className="items-center">
                    <Icon as={ExternalLinkIcon} size="sm" className="text-gray-600" />
                    <ButtonText>Knowledge Base</ButtonText>
                  </HStack>
                </Button>
              </HStack>
            </VStack>
          </VStack>
        </Card>
      </VStack>
    </ScrollView>
  );
};

const CommunicationHelpPageWrapper = () => {
  return (
    <MainLayout _title="Communication Help">
      <CommunicationHelpPage />
    </MainLayout>
  );
};

export default CommunicationHelpPageWrapper;