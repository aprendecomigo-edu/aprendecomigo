import * as DocumentPicker from 'expo-document-picker';
import {
  Plus,
  X,
  GraduationCap,
  Briefcase,
  Award,
  Upload,
  Calendar,
  FileText,
} from 'lucide-react-native';
import React, { useState } from 'react';
import { Alert } from 'react-native';

import {
  TeacherProfileData,
  EducationEntry,
  ExperienceEntry,
  CertificationFile,
} from '@/api/invitationApi';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { DocumentUploadComponent } from '@/components/ui/file-upload';
import { FormControl } from '@/components/ui/form-control';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Input, InputField } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { Text } from '@/components/ui/text';
import { Textarea, TextareaInput } from '@/components/ui/textarea';
import { VStack } from '@/components/ui/vstack';
import FileUploadService from '@/services/FileUploadService';

interface CredentialsStepProps {
  profileData: TeacherProfileData;
  updateProfileData: (updates: Partial<TeacherProfileData>) => void;
  validationErrors: { [key: string]: string };
  invitationData: any;
  onAddEducation: (education: EducationEntry) => void;
  onRemoveEducation: (index: number) => void;
  onAddExperience: (experience: ExperienceEntry) => void;
  onRemoveExperience: (index: number) => void;
  onAddCertification: (certification: CertificationFile) => void;
  onRemoveCertification: (index: number) => void;
}

const CredentialsStep: React.FC<CredentialsStepProps> = ({
  profileData,
  updateProfileData,
  validationErrors,
  invitationData,
  onAddEducation,
  onRemoveEducation,
  onAddExperience,
  onRemoveExperience,
  onAddCertification,
  onRemoveCertification,
}) => {
  const [showEducationForm, setShowEducationForm] = useState(false);
  const [showExperienceForm, setShowExperienceForm] = useState(false);
  const [showCertificationForm, setShowCertificationForm] = useState(false);

  // Education form state
  const [newEducation, setNewEducation] = useState<EducationEntry>({
    degree: '',
    field_of_study: '',
    institution: '',
    graduation_year: new Date().getFullYear(),
    is_highest_degree: false,
  });

  // Experience form state
  const [newExperience, setNewExperience] = useState<ExperienceEntry>({
    role: '',
    institution: '',
    start_date: '',
    end_date: '',
    description: '',
    is_current: false,
  });

  // Certification form state
  const [newCertification, setNewCertification] = useState<CertificationFile>({
    name: '',
    file: '',
    issuing_organization: '',
    expiry_date: '',
  });

  // Document upload state for certifications
  const [certificationUploadStates, setCertificationUploadStates] = useState<{
    [index: number]: {
      progress: number;
      status: 'idle' | 'uploading' | 'success' | 'error';
      error: string;
    };
  }>({});

  const handleAddEducation = () => {
    if (
      !newEducation.degree.trim() ||
      !newEducation.field_of_study.trim() ||
      !newEducation.institution.trim()
    ) {
      Alert.alert('Erro', 'Por favor, preencha todos os campos obrigatórios da formação');
      return;
    }

    onAddEducation(newEducation);
    setNewEducation({
      degree: '',
      field_of_study: '',
      institution: '',
      graduation_year: new Date().getFullYear(),
      is_highest_degree: false,
    });
    setShowEducationForm(false);
  };

  const handleAddExperience = () => {
    if (
      !newExperience.role.trim() ||
      !newExperience.institution.trim() ||
      !newExperience.start_date
    ) {
      Alert.alert('Erro', 'Por favor, preencha todos os campos obrigatórios da experiência');
      return;
    }

    onAddExperience(newExperience);
    setNewExperience({
      role: '',
      institution: '',
      start_date: '',
      end_date: '',
      description: '',
      is_current: false,
    });
    setShowExperienceForm(false);
  };

  const handleAddCertification = () => {
    if (!newCertification.name.trim() || !newCertification.issuing_organization.trim()) {
      Alert.alert('Erro', 'Por favor, preencha todos os campos obrigatórios da certificação');
      return;
    }

    onAddCertification(newCertification);
    setNewCertification({
      name: '',
      file: '',
      issuing_organization: '',
      expiry_date: '',
    });
    setShowCertificationForm(false);
  };

  const formatDate = (dateString: string): string => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-PT', { year: 'numeric', month: 'long' });
  };

  const years = Array.from({ length: 50 }, (_, i) => new Date().getFullYear() - i);

  return (
    <Box className="flex-1">
      <VStack space="lg">
        {/* Header */}
        <VStack space="sm">
          <Heading size="xl" className="text-gray-900">
            Credenciais e Experiência
          </Heading>
          <Text className="text-gray-600">
            Adicione sua formação acadêmica, experiência profissional e certificações para
            demonstrar suas qualificações.
          </Text>
        </VStack>

        {/* Education Section */}
        <VStack space="md">
          <HStack className="justify-between items-center">
            <HStack className="items-center" space="sm">
              <Icon as={GraduationCap} size="md" className="text-blue-600" />
              <Heading size="md" className="text-gray-800">
                Formação Acadêmica *
              </Heading>
            </HStack>
            <Button
              variant="outline"
              size="sm"
              onPress={() => setShowEducationForm(!showEducationForm)}
            >
              <Icon as={Plus} size="sm" />
              <ButtonText className="ml-1">Adicionar</ButtonText>
            </Button>
          </HStack>

          {validationErrors.education_background && (
            <Text className="text-red-600 text-sm">{validationErrors.education_background}</Text>
          )}

          {/* Education Form */}
          {showEducationForm && (
            <Box className="bg-gray-50 p-4 rounded-lg border border-gray-200">
              <VStack space="md">
                <FormControl>
                  <VStack space="sm">
                    <Text className="text-sm font-medium">Grau/Título *</Text>
                    <Input>
                      <InputField
                        placeholder="Ex: Licenciatura, Mestrado, Doutoramento"
                        value={newEducation.degree}
                        onChangeText={value => setNewEducation({ ...newEducation, degree: value })}
                      />
                    </Input>
                  </VStack>
                </FormControl>

                <FormControl>
                  <VStack space="sm">
                    <Text className="text-sm font-medium">Área de Estudo *</Text>
                    <Input>
                      <InputField
                        placeholder="Ex: Matemática, Engenharia, História"
                        value={newEducation.field_of_study}
                        onChangeText={value =>
                          setNewEducation({ ...newEducation, field_of_study: value })
                        }
                      />
                    </Input>
                  </VStack>
                </FormControl>

                <FormControl>
                  <VStack space="sm">
                    <Text className="text-sm font-medium">Instituição *</Text>
                    <Input>
                      <InputField
                        placeholder="Ex: Universidade de Lisboa"
                        value={newEducation.institution}
                        onChangeText={value =>
                          setNewEducation({ ...newEducation, institution: value })
                        }
                      />
                    </Input>
                  </VStack>
                </FormControl>

                <FormControl>
                  <VStack space="sm">
                    <Text className="text-sm font-medium">Ano de Formação</Text>
                    <Input>
                      <InputField
                        placeholder="2020"
                        value={newEducation.graduation_year.toString()}
                        onChangeText={value =>
                          setNewEducation({
                            ...newEducation,
                            graduation_year: parseInt(value) || new Date().getFullYear(),
                          })
                        }
                        keyboardType="numeric"
                      />
                    </Input>
                  </VStack>
                </FormControl>

                <HStack className="justify-between items-center">
                  <Text className="text-sm font-medium">É sua maior formação?</Text>
                  <Switch
                    value={newEducation.is_highest_degree}
                    onValueChange={value =>
                      setNewEducation({ ...newEducation, is_highest_degree: value })
                    }
                  />
                </HStack>

                <HStack space="sm">
                  <Button variant="outline" size="sm" onPress={() => setShowEducationForm(false)}>
                    <ButtonText>Cancelar</ButtonText>
                  </Button>
                  <Button size="sm" onPress={handleAddEducation}>
                    <ButtonText>Adicionar Formação</ButtonText>
                  </Button>
                </HStack>
              </VStack>
            </Box>
          )}

          {/* Education List */}
          <VStack space="sm">
            {profileData.education_background.length === 0 ? (
              <Box className="bg-gray-50 p-4 rounded-lg border border-dashed border-gray-300">
                <Text className="text-gray-600 text-center">
                  Nenhuma formação adicionada. Adicione pelo menos uma formação acadêmica.
                </Text>
              </Box>
            ) : (
              profileData.education_background.map((education, index) => (
                <Box key={index} className="bg-white p-4 rounded-lg border border-gray-200">
                  <HStack className="justify-between items-start">
                    <VStack space="xs" className="flex-1">
                      <Text className="font-semibold text-gray-900">{education.degree}</Text>
                      <Text className="text-gray-700">{education.field_of_study}</Text>
                      <Text className="text-sm text-gray-600">{education.institution}</Text>
                      <HStack className="items-center" space="sm">
                        <Text className="text-sm text-gray-500">{education.graduation_year}</Text>
                        {education.is_highest_degree && (
                          <Text className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                            Maior Formação
                          </Text>
                        )}
                      </HStack>
                    </VStack>
                    <Button variant="outline" size="sm" onPress={() => onRemoveEducation(index)}>
                      <Icon as={X} size="sm" className="text-red-600" />
                    </Button>
                  </HStack>
                </Box>
              ))
            )}
          </VStack>
        </VStack>

        {/* Experience Section */}
        <VStack space="md">
          <HStack className="justify-between items-center">
            <HStack className="items-center" space="sm">
              <Icon as={Briefcase} size="md" className="text-green-600" />
              <Heading size="md" className="text-gray-800">
                Experiência Profissional
              </Heading>
            </HStack>
            <Button
              variant="outline"
              size="sm"
              onPress={() => setShowExperienceForm(!showExperienceForm)}
            >
              <Icon as={Plus} size="sm" />
              <ButtonText className="ml-1">Adicionar</ButtonText>
            </Button>
          </HStack>

          {/* Experience Form */}
          {showExperienceForm && (
            <Box className="bg-gray-50 p-4 rounded-lg border border-gray-200">
              <VStack space="md">
                <FormControl>
                  <VStack space="sm">
                    <Text className="text-sm font-medium">Cargo/Função *</Text>
                    <Input>
                      <InputField
                        placeholder="Ex: Professor de Matemática"
                        value={newExperience.role}
                        onChangeText={value => setNewExperience({ ...newExperience, role: value })}
                      />
                    </Input>
                  </VStack>
                </FormControl>

                <FormControl>
                  <VStack space="sm">
                    <Text className="text-sm font-medium">Instituição/Empresa *</Text>
                    <Input>
                      <InputField
                        placeholder="Ex: Escola Secundária XYZ"
                        value={newExperience.institution}
                        onChangeText={value =>
                          setNewExperience({ ...newExperience, institution: value })
                        }
                      />
                    </Input>
                  </VStack>
                </FormControl>

                <HStack space="sm">
                  <FormControl className="flex-1">
                    <VStack space="sm">
                      <Text className="text-sm font-medium">Data de Início *</Text>
                      <Input>
                        <InputField
                          placeholder="YYYY-MM-DD"
                          value={newExperience.start_date}
                          onChangeText={value =>
                            setNewExperience({ ...newExperience, start_date: value })
                          }
                        />
                      </Input>
                    </VStack>
                  </FormControl>

                  {!newExperience.is_current && (
                    <FormControl className="flex-1">
                      <VStack space="sm">
                        <Text className="text-sm font-medium">Data de Fim</Text>
                        <Input>
                          <InputField
                            placeholder="YYYY-MM-DD"
                            value={newExperience.end_date || ''}
                            onChangeText={value =>
                              setNewExperience({ ...newExperience, end_date: value })
                            }
                          />
                        </Input>
                      </VStack>
                    </FormControl>
                  )}
                </HStack>

                <HStack className="justify-between items-center">
                  <Text className="text-sm font-medium">Cargo atual?</Text>
                  <Switch
                    value={newExperience.is_current}
                    onValueChange={value =>
                      setNewExperience({
                        ...newExperience,
                        is_current: value,
                        end_date: value ? undefined : newExperience.end_date,
                      })
                    }
                  />
                </HStack>

                <FormControl>
                  <VStack space="sm">
                    <Text className="text-sm font-medium">Descrição</Text>
                    <Textarea className="min-h-[80px]">
                      <TextareaInput
                        placeholder="Descreva suas responsabilidades e conquistas..."
                        value={newExperience.description}
                        onChangeText={value =>
                          setNewExperience({ ...newExperience, description: value })
                        }
                        multiline
                        textAlignVertical="top"
                      />
                    </Textarea>
                  </VStack>
                </FormControl>

                <HStack space="sm">
                  <Button variant="outline" size="sm" onPress={() => setShowExperienceForm(false)}>
                    <ButtonText>Cancelar</ButtonText>
                  </Button>
                  <Button size="sm" onPress={handleAddExperience}>
                    <ButtonText>Adicionar Experiência</ButtonText>
                  </Button>
                </HStack>
              </VStack>
            </Box>
          )}

          {/* Experience List */}
          <VStack space="sm">
            {profileData.teaching_experience.length === 0 ? (
              <Box className="bg-gray-50 p-4 rounded-lg border border-dashed border-gray-300">
                <Text className="text-gray-600 text-center">
                  Nenhuma experiência adicionada. Adicione sua experiência profissional relevante.
                </Text>
              </Box>
            ) : (
              profileData.teaching_experience.map((experience, index) => (
                <Box key={index} className="bg-white p-4 rounded-lg border border-gray-200">
                  <HStack className="justify-between items-start">
                    <VStack space="xs" className="flex-1">
                      <Text className="font-semibold text-gray-900">{experience.role}</Text>
                      <Text className="text-gray-700">{experience.institution}</Text>
                      <HStack className="items-center" space="sm">
                        <Icon as={Calendar} size="xs" className="text-gray-500" />
                        <Text className="text-sm text-gray-600">
                          {formatDate(experience.start_date)} -{' '}
                          {experience.is_current
                            ? 'Presente'
                            : formatDate(experience.end_date || '')}
                        </Text>
                        {experience.is_current && (
                          <Text className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
                            Atual
                          </Text>
                        )}
                      </HStack>
                      {experience.description && (
                        <Text className="text-sm text-gray-600 mt-2">{experience.description}</Text>
                      )}
                    </VStack>
                    <Button variant="outline" size="sm" onPress={() => onRemoveExperience(index)}>
                      <Icon as={X} size="sm" className="text-red-600" />
                    </Button>
                  </HStack>
                </Box>
              ))
            )}
          </VStack>
        </VStack>

        {/* Certifications Section */}
        <VStack space="md">
          <HStack className="justify-between items-center">
            <HStack className="items-center" space="sm">
              <Icon as={Award} size="md" className="text-purple-600" />
              <Heading size="md" className="text-gray-800">
                Certificações
              </Heading>
            </HStack>
            <Button
              variant="outline"
              size="sm"
              onPress={() => setShowCertificationForm(!showCertificationForm)}
            >
              <Icon as={Plus} size="sm" />
              <ButtonText className="ml-1">Adicionar</ButtonText>
            </Button>
          </HStack>

          {/* Certification Form */}
          {showCertificationForm && (
            <Box className="bg-gray-50 p-4 rounded-lg border border-gray-200">
              <VStack space="md">
                <FormControl>
                  <VStack space="sm">
                    <Text className="text-sm font-medium">Nome da Certificação *</Text>
                    <Input>
                      <InputField
                        placeholder="Ex: Certificação em Ensino Online"
                        value={newCertification.name}
                        onChangeText={value =>
                          setNewCertification({ ...newCertification, name: value })
                        }
                      />
                    </Input>
                  </VStack>
                </FormControl>

                <FormControl>
                  <VStack space="sm">
                    <Text className="text-sm font-medium">Organização Emissora *</Text>
                    <Input>
                      <InputField
                        placeholder="Ex: Microsoft, Google, Cambridge"
                        value={newCertification.issuing_organization}
                        onChangeText={value =>
                          setNewCertification({ ...newCertification, issuing_organization: value })
                        }
                      />
                    </Input>
                  </VStack>
                </FormControl>

                <FormControl>
                  <VStack space="sm">
                    <Text className="text-sm font-medium">Data de Expiração (opcional)</Text>
                    <Input>
                      <InputField
                        placeholder="YYYY-MM-DD"
                        value={newCertification.expiry_date || ''}
                        onChangeText={value =>
                          setNewCertification({ ...newCertification, expiry_date: value })
                        }
                      />
                    </Input>
                  </VStack>
                </FormControl>

                <DocumentUploadComponent
                  onDocumentSelected={document => {
                    setNewCertification({
                      ...newCertification,
                      file: document.uri,
                      name: newCertification.name || document.name || 'Certificado',
                    });
                  }}
                  onDocumentRemoved={() => {
                    setNewCertification({ ...newCertification, file: '' });
                  }}
                  currentDocument={
                    newCertification.file
                      ? {
                          name:
                            typeof newCertification.file === 'string' &&
                            newCertification.file.includes('/')
                              ? newCertification.file.split('/').pop() || 'Document'
                              : 'Document',
                          uri:
                            typeof newCertification.file === 'string' ? newCertification.file : '',
                        }
                      : undefined
                  }
                  acceptedTypes={FileUploadService.getAllowedDocumentTypes()}
                  maxSizeInMB={10}
                  label="Certificado"
                  description="Anexe seu certificado ou diploma (opcional)"
                  required={false}
                />

                <HStack space="sm">
                  <Button
                    variant="outline"
                    size="sm"
                    onPress={() => setShowCertificationForm(false)}
                  >
                    <ButtonText>Cancelar</ButtonText>
                  </Button>
                  <Button size="sm" onPress={handleAddCertification}>
                    <ButtonText>Adicionar Certificação</ButtonText>
                  </Button>
                </HStack>
              </VStack>
            </Box>
          )}

          {/* Certifications List */}
          <VStack space="sm">
            {profileData.certifications.length === 0 ? (
              <Box className="bg-gray-50 p-4 rounded-lg border border-dashed border-gray-300">
                <Text className="text-gray-600 text-center">
                  Nenhuma certificação adicionada. Adicione certificações relevantes (opcional).
                </Text>
              </Box>
            ) : (
              profileData.certifications.map((certification, index) => (
                <Box key={index} className="bg-white p-4 rounded-lg border border-gray-200">
                  <HStack className="justify-between items-start">
                    <VStack space="xs" className="flex-1">
                      <Text className="font-semibold text-gray-900">{certification.name}</Text>
                      <Text className="text-gray-700">{certification.issuing_organization}</Text>
                      {certification.expiry_date && (
                        <Text className="text-sm text-gray-600">
                          Expira em: {formatDate(certification.expiry_date)}
                        </Text>
                      )}
                      {certification.file && (
                        <HStack className="items-center mt-1" space="xs">
                          <Icon as={FileText} size="xs" className="text-blue-600" />
                          <Text className="text-xs text-blue-600">Documento anexado</Text>
                        </HStack>
                      )}
                    </VStack>
                    <Button
                      variant="outline"
                      size="sm"
                      onPress={() => onRemoveCertification(index)}
                    >
                      <Icon as={X} size="sm" className="text-red-600" />
                    </Button>
                  </HStack>
                </Box>
              ))
            )}
          </VStack>
        </VStack>

        {/* Help Text */}
        <Box className="bg-blue-50 p-4 rounded-lg border border-blue-200">
          <VStack space="sm">
            <Text className="font-medium text-blue-800">Dicas:</Text>
            <VStack space="xs" className="ml-2">
              <Text className="text-sm text-blue-700">
                • Adicione pelo menos uma formação acadêmica relevante à área que ensina
              </Text>
              <Text className="text-sm text-blue-700">
                • Inclua experiências de ensino mesmo que não formais (explicações, tutorias)
              </Text>
              <Text className="text-sm text-blue-700">
                • Certificações online são válidas e valorizadas
              </Text>
              <Text className="text-sm text-blue-700">
                • Estas informações ajudam a construir confiança com alunos e pais
              </Text>
            </VStack>
          </VStack>
        </Box>
      </VStack>
    </Box>
  );
};

export default CredentialsStep;
