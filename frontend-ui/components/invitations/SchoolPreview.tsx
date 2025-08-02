import {
  School,
  Users,
  GraduationCap,
  MapPin,
  Globe,
  Mail,
  Phone,
  Calendar,
  Award,
  TrendingUp,
  Eye,
  EyeOff,
  ExternalLink,
} from 'lucide-react-native';
import React, { useState, useEffect } from 'react';

import apiClient from '@/api/apiClient';
import { Avatar } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Card, CardBody, CardHeader } from '@/components/ui/card';
import { Divider } from '@/components/ui/divider';
import { Grid } from '@/components/ui/grid';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Image } from '@/components/ui/image';
import { Pressable } from '@/components/ui/pressable';
import { Skeleton } from '@/components/ui/skeleton';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

interface SchoolDetails {
  id: number;
  name: string;
  description?: string;
  logo_url?: string;
  banner_url?: string;
  website?: string;
  email?: string;
  phone?: string;
  address?: string;
  city?: string;
  state?: string;
  country?: string;
  founded_year?: number;
  school_type?: string;
  grades_offered?: string[];
  languages?: string[];
  specializations?: string[];
  facilities?: string[];
  certifications?: string[];
  social_media?: {
    facebook?: string;
    instagram?: string;
    twitter?: string;
    linkedin?: string;
  };
}

interface SchoolStats {
  total_students: number;
  total_teachers: number;
  active_sessions_count: number;
  average_rating?: number;
  total_hours_taught?: number;
  courses_offered?: number;
  success_rate?: number;
}

interface SchoolPreviewProps {
  schoolId: number;
  compact?: boolean;
  showStats?: boolean;
  showContactInfo?: boolean;
  showFullDetails?: boolean;
  onContactSchool?: () => void;
  className?: string;
}

export const SchoolPreview: React.FC<SchoolPreviewProps> = ({
  schoolId,
  compact = false,
  showStats = true,
  showContactInfo = true,
  showFullDetails = false,
  onContactSchool,
  className = '',
}) => {
  const [schoolDetails, setSchoolDetails] = useState<SchoolDetails | null>(null);
  const [schoolStats, setSchoolStats] = useState<SchoolStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(showFullDetails);
  const [loadingStats, setLoadingStats] = useState(false);

  useEffect(() => {
    fetchSchoolDetails();
    if (showStats) {
      fetchSchoolStats();
    }
  }, [schoolId, showStats]);

  const fetchSchoolDetails = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiClient.get(`/accounts/schools/${schoolId}/`);
      setSchoolDetails(response.data);
    } catch (err: any) {
      setError('Falha ao carregar detalhes da escola');
      console.error('Failed to fetch school details:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchSchoolStats = async () => {
    try {
      setLoadingStats(true);
      const response = await apiClient.get(`/accounts/schools/${schoolId}/stats/`);
      setSchoolStats(response.data);
    } catch (err: any) {
      console.error('Failed to fetch school stats:', err);
      // Don't show error for stats as it's not critical
    } finally {
      setLoadingStats(false);
    }
  };

  const handleWebsiteOpen = () => {
    if (schoolDetails?.website) {
      // In a real app, this would open the URL
      console.log('Opening website:', schoolDetails.website);
    }
  };

  const handleSocialMediaOpen = (platform: string, url: string) => {
    // In a real app, this would open the social media URL
    console.log(`Opening ${platform}:`, url);
  };

  if (loading) {
    return (
      <Card className={`${className} w-full`}>
        <CardHeader>
          <HStack space="md" className="items-start">
            <Skeleton className="w-16 h-16 rounded-full" />
            <VStack className="flex-1" space="xs">
              <Skeleton className="w-48 h-6 rounded" />
              <Skeleton className="w-32 h-4 rounded" />
              <Skeleton className="w-full h-12 rounded" />
            </VStack>
          </HStack>
        </CardHeader>
        {showStats && (
          <CardBody>
            <Grid className="grid-cols-2 gap-4">
              {[1, 2, 3, 4].map(i => (
                <Box key={i} className="text-center p-3 bg-gray-50 rounded">
                  <Skeleton className="w-8 h-8 rounded mx-auto mb-2" />
                  <Skeleton className="w-12 h-6 rounded mx-auto mb-1" />
                  <Skeleton className="w-16 h-3 rounded mx-auto" />
                </Box>
              ))}
            </Grid>
          </CardBody>
        )}
      </Card>
    );
  }

  if (error || !schoolDetails) {
    return (
      <Card className={`${className} w-full border-red-200 bg-red-50`}>
        <CardBody className="text-center py-8">
          <Icon as={School} size="xl" className="text-red-400 mx-auto mb-3" />
          <Text className="text-red-700 mb-2">Erro ao carregar escola</Text>
          <Text className="text-sm text-red-600 mb-4">
            {error || 'Não foi possível carregar as informações da escola'}
          </Text>
          <Button variant="outline" onPress={fetchSchoolDetails} className="border-red-300">
            <ButtonText className="text-red-600">Tentar Novamente</ButtonText>
          </Button>
        </CardBody>
      </Card>
    );
  }

  // Compact version for quick preview
  if (compact) {
    return (
      <Card className={`${className} w-full`}>
        <CardBody>
          <HStack space="md" className="items-center">
            <Avatar size="md">
              {schoolDetails.logo_url ? (
                <Avatar.Image source={{ uri: schoolDetails.logo_url }} />
              ) : (
                <Avatar.FallbackText>{schoolDetails.name}</Avatar.FallbackText>
              )}
            </Avatar>

            <VStack className="flex-1">
              <Text className="font-bold text-base">{schoolDetails.name}</Text>
              {schoolDetails.city && schoolDetails.state && (
                <HStack space="xs" className="items-center">
                  <Icon as={MapPin} size="xs" className="text-gray-500" />
                  <Text className="text-sm text-gray-600">
                    {schoolDetails.city}, {schoolDetails.state}
                  </Text>
                </HStack>
              )}
              {showStats && schoolStats && (
                <HStack space="md" className="mt-1">
                  <Text className="text-xs text-gray-500">
                    {schoolStats.total_students} estudantes
                  </Text>
                  <Text className="text-xs text-gray-500">
                    {schoolStats.total_teachers} professores
                  </Text>
                </HStack>
              )}
            </VStack>

            {schoolDetails.website && (
              <Pressable onPress={handleWebsiteOpen}>
                <Icon as={ExternalLink} size="sm" className="text-blue-600" />
              </Pressable>
            )}
          </HStack>
        </CardBody>
      </Card>
    );
  }

  // Full detailed preview
  return (
    <Card className={`${className} w-full`}>
      {/* Banner Image */}
      {schoolDetails.banner_url && (
        <Box className="w-full h-32 overflow-hidden rounded-t-lg">
          <Image
            source={{ uri: schoolDetails.banner_url }}
            className="w-full h-full"
            resizeMode="cover"
          />
        </Box>
      )}

      <CardHeader>
        <VStack space="md">
          {/* School Header */}
          <HStack space="md" className="items-start">
            <Avatar size="xl">
              {schoolDetails.logo_url ? (
                <Avatar.Image source={{ uri: schoolDetails.logo_url }} />
              ) : (
                <Avatar.FallbackText>{schoolDetails.name}</Avatar.FallbackText>
              )}
            </Avatar>

            <VStack className="flex-1">
              <Heading size="xl">{schoolDetails.name}</Heading>

              {/* Location */}
              {(schoolDetails.city || schoolDetails.address) && (
                <HStack space="xs" className="items-center mt-1">
                  <Icon as={MapPin} size="sm" className="text-gray-500" />
                  <Text className="text-sm text-gray-600">
                    {schoolDetails.address
                      ? `${schoolDetails.address}${
                          schoolDetails.city ? `, ${schoolDetails.city}` : ''
                        }`
                      : `${schoolDetails.city}${
                          schoolDetails.state ? `, ${schoolDetails.state}` : ''
                        }`}
                  </Text>
                </HStack>
              )}

              {/* School Type & Founded */}
              <HStack space="md" className="mt-2">
                {schoolDetails.school_type && (
                  <Badge className="bg-blue-100 text-blue-800">
                    <Text className="text-xs">{schoolDetails.school_type}</Text>
                  </Badge>
                )}
                {schoolDetails.founded_year && (
                  <HStack space="xs" className="items-center">
                    <Icon as={Calendar} size="xs" className="text-gray-500" />
                    <Text className="text-xs text-gray-600">
                      Fundada em {schoolDetails.founded_year}
                    </Text>
                  </HStack>
                )}
              </HStack>
            </VStack>
          </HStack>

          {/* Description */}
          {schoolDetails.description && (
            <Text className="text-gray-700 leading-relaxed">{schoolDetails.description}</Text>
          )}
        </VStack>
      </CardHeader>

      <CardBody>
        <VStack space="lg">
          {/* Statistics */}
          {showStats && (
            <VStack space="sm">
              <Heading size="md">Estatísticas</Heading>
              {loadingStats ? (
                <Grid className="grid-cols-2 gap-4">
                  {[1, 2, 3, 4].map(i => (
                    <Box key={i} className="text-center p-3 bg-gray-50 rounded">
                      <Skeleton className="w-8 h-8 rounded mx-auto mb-2" />
                      <Skeleton className="w-12 h-6 rounded mx-auto mb-1" />
                      <Skeleton className="w-16 h-3 rounded mx-auto" />
                    </Box>
                  ))}
                </Grid>
              ) : schoolStats ? (
                <Grid className="grid-cols-2 lg:grid-cols-4 gap-4">
                  <Box className="text-center p-4 bg-blue-50 rounded-lg">
                    <Icon as={Users} size="lg" className="text-blue-600 mx-auto mb-2" />
                    <Text className="text-2xl font-bold text-blue-600">
                      {schoolStats.total_students}
                    </Text>
                    <Text className="text-sm text-gray-600">Estudantes</Text>
                  </Box>

                  <Box className="text-center p-4 bg-green-50 rounded-lg">
                    <Icon as={GraduationCap} size="lg" className="text-green-600 mx-auto mb-2" />
                    <Text className="text-2xl font-bold text-green-600">
                      {schoolStats.total_teachers}
                    </Text>
                    <Text className="text-sm text-gray-600">Professores</Text>
                  </Box>

                  {schoolStats.courses_offered && (
                    <Box className="text-center p-4 bg-purple-50 rounded-lg">
                      <Icon as={Award} size="lg" className="text-purple-600 mx-auto mb-2" />
                      <Text className="text-2xl font-bold text-purple-600">
                        {schoolStats.courses_offered}
                      </Text>
                      <Text className="text-sm text-gray-600">Cursos</Text>
                    </Box>
                  )}

                  {schoolStats.success_rate && (
                    <Box className="text-center p-4 bg-yellow-50 rounded-lg">
                      <Icon as={TrendingUp} size="lg" className="text-yellow-600 mx-auto mb-2" />
                      <Text className="text-2xl font-bold text-yellow-600">
                        {Math.round(schoolStats.success_rate * 100)}%
                      </Text>
                      <Text className="text-sm text-gray-600">Taxa de Sucesso</Text>
                    </Box>
                  )}
                </Grid>
              ) : (
                <Text className="text-gray-500 text-center py-4">Estatísticas não disponíveis</Text>
              )}
            </VStack>
          )}

          {/* Expanded Details */}
          {(expanded || showFullDetails) && (
            <VStack space="md">
              <Divider />

              {/* Specializations */}
              {schoolDetails.specializations && schoolDetails.specializations.length > 0 && (
                <VStack space="sm">
                  <Heading size="sm">Especializações</Heading>
                  <HStack space="xs" className="flex-wrap">
                    {schoolDetails.specializations.map((spec, index) => (
                      <Badge key={index} className="bg-green-100 text-green-800 mb-1">
                        <Text className="text-xs">{spec}</Text>
                      </Badge>
                    ))}
                  </HStack>
                </VStack>
              )}

              {/* Grades Offered */}
              {schoolDetails.grades_offered && schoolDetails.grades_offered.length > 0 && (
                <VStack space="sm">
                  <Heading size="sm">Níveis de Ensino</Heading>
                  <HStack space="xs" className="flex-wrap">
                    {schoolDetails.grades_offered.map((grade, index) => (
                      <Badge key={index} className="bg-blue-100 text-blue-800 mb-1">
                        <Text className="text-xs">{grade}</Text>
                      </Badge>
                    ))}
                  </HStack>
                </VStack>
              )}

              {/* Languages */}
              {schoolDetails.languages && schoolDetails.languages.length > 0 && (
                <VStack space="sm">
                  <Heading size="sm">Idiomas</Heading>
                  <HStack space="xs" className="flex-wrap">
                    {schoolDetails.languages.map((lang, index) => (
                      <Badge key={index} className="bg-purple-100 text-purple-800 mb-1">
                        <Text className="text-xs">{lang}</Text>
                      </Badge>
                    ))}
                  </HStack>
                </VStack>
              )}

              {/* Facilities */}
              {schoolDetails.facilities && schoolDetails.facilities.length > 0 && (
                <VStack space="sm">
                  <Heading size="sm">Instalações</Heading>
                  <VStack space="xs">
                    {schoolDetails.facilities.map((facility, index) => (
                      <HStack key={index} space="xs" className="items-center">
                        <Box className="w-2 h-2 bg-green-500 rounded-full" />
                        <Text className="text-sm text-gray-700">{facility}</Text>
                      </HStack>
                    ))}
                  </VStack>
                </VStack>
              )}

              {/* Certifications */}
              {schoolDetails.certifications && schoolDetails.certifications.length > 0 && (
                <VStack space="sm">
                  <Heading size="sm">Certificações</Heading>
                  <VStack space="xs">
                    {schoolDetails.certifications.map((cert, index) => (
                      <HStack key={index} space="xs" className="items-center">
                        <Icon as={Award} size="xs" className="text-yellow-500" />
                        <Text className="text-sm text-gray-700">{cert}</Text>
                      </HStack>
                    ))}
                  </VStack>
                </VStack>
              )}
            </VStack>
          )}

          {/* Contact Information */}
          {showContactInfo &&
            (schoolDetails.email || schoolDetails.phone || schoolDetails.website) && (
              <VStack space="md">
                <Divider />
                <Heading size="sm">Informações de Contato</Heading>

                <VStack space="sm">
                  {schoolDetails.email && (
                    <HStack space="sm" className="items-center">
                      <Icon as={Mail} size="sm" className="text-gray-500" />
                      <Text className="text-sm text-gray-700">{schoolDetails.email}</Text>
                    </HStack>
                  )}

                  {schoolDetails.phone && (
                    <HStack space="sm" className="items-center">
                      <Icon as={Phone} size="sm" className="text-gray-500" />
                      <Text className="text-sm text-gray-700">{schoolDetails.phone}</Text>
                    </HStack>
                  )}

                  {schoolDetails.website && (
                    <Pressable onPress={handleWebsiteOpen}>
                      <HStack space="sm" className="items-center">
                        <Icon as={Globe} size="sm" className="text-blue-600" />
                        <Text className="text-sm text-blue-600 underline">
                          {schoolDetails.website}
                        </Text>
                        <Icon as={ExternalLink} size="xs" className="text-blue-600" />
                      </HStack>
                    </Pressable>
                  )}
                </VStack>

                {/* Social Media */}
                {schoolDetails.social_media && (
                  <HStack space="md" className="mt-2">
                    {Object.entries(schoolDetails.social_media).map(([platform, url]) => {
                      if (!url) return null;
                      return (
                        <Pressable
                          key={platform}
                          onPress={() => handleSocialMediaOpen(platform, url)}
                        >
                          <Badge className="bg-gray-100 text-gray-800">
                            <Text className="text-xs capitalize">{platform}</Text>
                          </Badge>
                        </Pressable>
                      );
                    })}
                  </HStack>
                )}
              </VStack>
            )}

          {/* Action Buttons */}
          <VStack space="sm">
            {!showFullDetails && (
              <Button variant="outline" onPress={() => setExpanded(!expanded)}>
                <Icon as={expanded ? EyeOff : Eye} size="sm" className="mr-2" />
                <ButtonText>{expanded ? 'Ver Menos' : 'Ver Mais Detalhes'}</ButtonText>
              </Button>
            )}

            {onContactSchool && (
              <Button onPress={onContactSchool}>
                <Icon as={Mail} size="sm" className="mr-2" />
                <ButtonText>Entrar em Contato</ButtonText>
              </Button>
            )}
          </VStack>
        </VStack>
      </CardBody>
    </Card>
  );
};

export default SchoolPreview;
