import {
  GraduationCap,
  Award,
  Certificate,
  Plus,
  X,
  Calendar,
  MapPin,
  ExternalLink,
  CheckCircle2,
  Upload,
} from 'lucide-react-native';
import React, { useState } from 'react';

import { Badge, BadgeText } from '@/components/ui/badge';
import { Box } from '@/components/ui/box';
import { Button, ButtonText, ButtonIcon } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Divider } from '@/components/ui/divider';
import {
  FormControl,
  FormControlLabel,
  FormControlHelper,
  FormControlError,
} from '@/components/ui/form-control';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Input, InputField } from '@/components/ui/input';
import { ScrollView } from '@/components/ui/scroll-view';
import {
  Select,
  SelectTrigger,
  SelectInput,
  SelectContent,
  SelectItem,
} from '@/components/ui/select';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

interface Degree {
  id: string;
  degree_type: string;
  field_of_study: string;
  institution: string;
  location: string;
  graduation_year: number;
  gpa?: string;
  honors?: string;
  description?: string;
}

interface Certification {
  id: string;
  name: string;
  issuing_organization: string;
  issue_date: string;
  expiration_date?: string;
  credential_id?: string;
  verification_url?: string;
}

interface EducationFormData {
  degrees: Degree[];
  certifications: Certification[];
  additional_training: string[];
  languages_taught: string[];
  research_publications?: string[];
}

interface EducationStepProps {
  formData: EducationFormData;
  onFormDataChange: (data: Partial<EducationFormData>) => void;
  validationErrors?: Record<string, string[]>;
  isLoading?: boolean;
}

const DEGREE_TYPES = [
  'High School Diploma',
  'Associate Degree',
  "Bachelor's Degree",
  "Master's Degree",
  'Doctoral Degree (PhD)',
  'Professional Degree (JD, MD, etc.)',
  'Certificate Program',
  'Diploma',
  'Other',
];

const COMMON_FIELDS = [
  'Education',
  'Mathematics',
  'Science',
  'English Literature',
  'History',
  'Physics',
  'Chemistry',
  'Biology',
  'Computer Science',
  'Psychology',
  'Business Administration',
  'Art',
  'Music',
  'Physical Education',
  'Foreign Languages',
  'Economics',
  'Political Science',
  'Philosophy',
];

const HONOR_TYPES = [
  'Summa Cum Laude',
  'Magna Cum Laude',
  'Cum Laude',
  "Dean's List",
  'Phi Beta Kappa',
  'Honor Society',
  'Scholarship Recipient',
  'Other',
];

export const EducationStep: React.FC<EducationStepProps> = ({
  formData,
  onFormDataChange,
  validationErrors = {},
  isLoading = false,
}) => {
  const [showDegreeForm, setShowDegreeForm] = useState(false);
  const [showCertificationForm, setShowCertificationForm] = useState(false);
  const [showTrainingInput, setShowTrainingInput] = useState(false);
  const [newTraining, setNewTraining] = useState('');

  const [editingDegree, setEditingDegree] = useState<Degree | null>(null);
  const [editingCertification, setEditingCertification] = useState<Certification | null>(null);

  // Generate years for graduation dropdown
  const currentYear = new Date().getFullYear();
  const years = Array.from({ length: 50 }, (_, i) => currentYear - i);

  const handleFieldChange = (field: string, value: any) => {
    onFormDataChange({ [field]: value });
  };

  const addDegree = (degree: Omit<Degree, 'id'>) => {
    const newDegree: Degree = {
      ...degree,
      id: Date.now().toString(),
    };
    handleFieldChange('degrees', [...formData.degrees, newDegree]);
    setShowDegreeForm(false);
    setEditingDegree(null);
  };

  const updateDegree = (id: string, updatedDegree: Omit<Degree, 'id'>) => {
    const degrees = formData.degrees.map(degree =>
      degree.id === id ? { ...updatedDegree, id } : degree
    );
    handleFieldChange('degrees', degrees);
    setShowDegreeForm(false);
    setEditingDegree(null);
  };

  const removeDegree = (id: string) => {
    handleFieldChange(
      'degrees',
      formData.degrees.filter(degree => degree.id !== id)
    );
  };

  const addCertification = (certification: Omit<Certification, 'id'>) => {
    const newCertification: Certification = {
      ...certification,
      id: Date.now().toString(),
    };
    handleFieldChange('certifications', [...formData.certifications, newCertification]);
    setShowCertificationForm(false);
    setEditingCertification(null);
  };

  const updateCertification = (id: string, updatedCertification: Omit<Certification, 'id'>) => {
    const certifications = formData.certifications.map(cert =>
      cert.id === id ? { ...updatedCertification, id } : cert
    );
    handleFieldChange('certifications', certifications);
    setShowCertificationForm(false);
    setEditingCertification(null);
  };

  const removeCertification = (id: string) => {
    handleFieldChange(
      'certifications',
      formData.certifications.filter(cert => cert.id !== id)
    );
  };

  const addTraining = (training: string) => {
    if (training.trim()) {
      handleFieldChange('additional_training', [...formData.additional_training, training.trim()]);
    }
    setNewTraining('');
    setShowTrainingInput(false);
  };

  const removeTraining = (index: number) => {
    const newTraining = [...formData.additional_training];
    newTraining.splice(index, 1);
    handleFieldChange('additional_training', newTraining);
  };

  const DegreeForm = ({
    degree,
    onSubmit,
    onCancel,
  }: {
    degree?: Degree;
    onSubmit: (degree: Omit<Degree, 'id'>) => void;
    onCancel: () => void;
  }) => {
    const [formData, setFormData] = useState<Omit<Degree, 'id'>>({
      degree_type: degree?.degree_type || '',
      field_of_study: degree?.field_of_study || '',
      institution: degree?.institution || '',
      location: degree?.location || '',
      graduation_year: degree?.graduation_year || new Date().getFullYear(),
      gpa: degree?.gpa || '',
      honors: degree?.honors || '',
      description: degree?.description || '',
    });

    const handleSubmit = () => {
      if (formData.degree_type && formData.field_of_study && formData.institution) {
        onSubmit(formData);
      }
    };

    return (
      <Card className="border-blue-200 bg-blue-50">
        <VStack space="md" className="p-4">
          <HStack className="items-center justify-between">
            <Heading size="sm" className="text-blue-900">
              {degree ? 'Edit Degree' : 'Add Degree'}
            </Heading>
            <Button variant="ghost" size="sm" onPress={onCancel}>
              <ButtonIcon as={X} className="text-gray-600" />
            </Button>
          </HStack>

          <HStack space="md">
            <VStack className="flex-1">
              <FormControl>
                <FormControlLabel>
                  <Text>Degree Type *</Text>
                </FormControlLabel>
                <Select
                  selectedValue={formData.degree_type}
                  onValueChange={value => setFormData(prev => ({ ...prev, degree_type: value }))}
                >
                  <SelectTrigger>
                    <SelectInput placeholder="Select degree type" />
                  </SelectTrigger>
                  <SelectContent>
                    {DEGREE_TYPES.map(type => (
                      <SelectItem key={type} label={type} value={type} />
                    ))}
                  </SelectContent>
                </Select>
              </FormControl>
            </VStack>

            <VStack className="flex-1">
              <FormControl>
                <FormControlLabel>
                  <Text>Field of Study *</Text>
                </FormControlLabel>
                <Input>
                  <InputField
                    value={formData.field_of_study}
                    onChangeText={value =>
                      setFormData(prev => ({ ...prev, field_of_study: value }))
                    }
                    placeholder="e.g., Mathematics Education"
                  />
                </Input>
              </FormControl>
            </VStack>
          </HStack>

          <HStack space="md">
            <VStack className="flex-1">
              <FormControl>
                <FormControlLabel>
                  <Text>Institution *</Text>
                </FormControlLabel>
                <Input>
                  <InputField
                    value={formData.institution}
                    onChangeText={value => setFormData(prev => ({ ...prev, institution: value }))}
                    placeholder="University name"
                  />
                </Input>
              </FormControl>
            </VStack>

            <VStack className="flex-1">
              <FormControl>
                <FormControlLabel>
                  <Text>Location</Text>
                </FormControlLabel>
                <Input>
                  <InputField
                    value={formData.location}
                    onChangeText={value => setFormData(prev => ({ ...prev, location: value }))}
                    placeholder="City, Country"
                  />
                </Input>
              </FormControl>
            </VStack>
          </HStack>

          <HStack space="md">
            <VStack className="flex-1">
              <FormControl>
                <FormControlLabel>
                  <Text>Graduation Year *</Text>
                </FormControlLabel>
                <Select
                  selectedValue={formData.graduation_year.toString()}
                  onValueChange={value =>
                    setFormData(prev => ({ ...prev, graduation_year: parseInt(value) }))
                  }
                >
                  <SelectTrigger>
                    <SelectInput placeholder="Select year" />
                  </SelectTrigger>
                  <SelectContent>
                    {years.map(year => (
                      <SelectItem key={year} label={year.toString()} value={year.toString()} />
                    ))}
                  </SelectContent>
                </Select>
              </FormControl>
            </VStack>

            <VStack className="flex-1">
              <FormControl>
                <FormControlLabel>
                  <Text>GPA (Optional)</Text>
                </FormControlLabel>
                <Input>
                  <InputField
                    value={formData.gpa}
                    onChangeText={value => setFormData(prev => ({ ...prev, gpa: value }))}
                    placeholder="e.g., 3.8/4.0"
                  />
                </Input>
              </FormControl>
            </VStack>
          </HStack>

          <FormControl>
            <FormControlLabel>
              <Text>Honors/Awards</Text>
            </FormControlLabel>
            <Select
              selectedValue={formData.honors}
              onValueChange={value => setFormData(prev => ({ ...prev, honors: value }))}
            >
              <SelectTrigger>
                <SelectInput placeholder="Select honors (if any)" />
              </SelectTrigger>
              <SelectContent>
                {HONOR_TYPES.map(honor => (
                  <SelectItem key={honor} label={honor} value={honor} />
                ))}
              </SelectContent>
            </Select>
          </FormControl>

          <FormControl>
            <FormControlLabel>
              <Text>Description (Optional)</Text>
            </FormControlLabel>
            <Input>
              <InputField
                value={formData.description}
                onChangeText={value => setFormData(prev => ({ ...prev, description: value }))}
                placeholder="Any additional details about your education"
                multiline
                numberOfLines={2}
              />
            </Input>
          </FormControl>

          <HStack space="sm" className="justify-end">
            <Button variant="outline" onPress={onCancel}>
              <ButtonText>Cancel</ButtonText>
            </Button>
            <Button onPress={handleSubmit}>
              <ButtonText>{degree ? 'Update' : 'Add'} Degree</ButtonText>
            </Button>
          </HStack>
        </VStack>
      </Card>
    );
  };

  const CertificationForm = ({
    certification,
    onSubmit,
    onCancel,
  }: {
    certification?: Certification;
    onSubmit: (certification: Omit<Certification, 'id'>) => void;
    onCancel: () => void;
  }) => {
    const [formData, setFormData] = useState<Omit<Certification, 'id'>>({
      name: certification?.name || '',
      issuing_organization: certification?.issuing_organization || '',
      issue_date: certification?.issue_date || '',
      expiration_date: certification?.expiration_date || '',
      credential_id: certification?.credential_id || '',
      verification_url: certification?.verification_url || '',
    });

    const handleSubmit = () => {
      if (formData.name && formData.issuing_organization && formData.issue_date) {
        onSubmit(formData);
      }
    };

    return (
      <Card className="border-green-200 bg-green-50">
        <VStack space="md" className="p-4">
          <HStack className="items-center justify-between">
            <Heading size="sm" className="text-green-900">
              {certification ? 'Edit Certification' : 'Add Certification'}
            </Heading>
            <Button variant="ghost" size="sm" onPress={onCancel}>
              <ButtonIcon as={X} className="text-gray-600" />
            </Button>
          </HStack>

          <HStack space="md">
            <VStack className="flex-1">
              <FormControl>
                <FormControlLabel>
                  <Text>Certification Name *</Text>
                </FormControlLabel>
                <Input>
                  <InputField
                    value={formData.name}
                    onChangeText={value => setFormData(prev => ({ ...prev, name: value }))}
                    placeholder="e.g., Teaching License, TESOL Certificate"
                  />
                </Input>
              </FormControl>
            </VStack>

            <VStack className="flex-1">
              <FormControl>
                <FormControlLabel>
                  <Text>Issuing Organization *</Text>
                </FormControlLabel>
                <Input>
                  <InputField
                    value={formData.issuing_organization}
                    onChangeText={value =>
                      setFormData(prev => ({ ...prev, issuing_organization: value }))
                    }
                    placeholder="e.g., State Board of Education"
                  />
                </Input>
              </FormControl>
            </VStack>
          </HStack>

          <HStack space="md">
            <VStack className="flex-1">
              <FormControl>
                <FormControlLabel>
                  <Text>Issue Date *</Text>
                </FormControlLabel>
                <Input>
                  <InputField
                    value={formData.issue_date}
                    onChangeText={value => setFormData(prev => ({ ...prev, issue_date: value }))}
                    placeholder="MM/YYYY"
                  />
                </Input>
              </FormControl>
            </VStack>

            <VStack className="flex-1">
              <FormControl>
                <FormControlLabel>
                  <Text>Expiration Date</Text>
                </FormControlLabel>
                <Input>
                  <InputField
                    value={formData.expiration_date}
                    onChangeText={value =>
                      setFormData(prev => ({ ...prev, expiration_date: value }))
                    }
                    placeholder="MM/YYYY (if applicable)"
                  />
                </Input>
              </FormControl>
            </VStack>
          </HStack>

          <HStack space="md">
            <VStack className="flex-1">
              <FormControl>
                <FormControlLabel>
                  <Text>Credential ID</Text>
                </FormControlLabel>
                <Input>
                  <InputField
                    value={formData.credential_id}
                    onChangeText={value => setFormData(prev => ({ ...prev, credential_id: value }))}
                    placeholder="Certificate number/ID"
                  />
                </Input>
              </FormControl>
            </VStack>

            <VStack className="flex-1">
              <FormControl>
                <FormControlLabel>
                  <Text>Verification URL</Text>
                </FormControlLabel>
                <Input>
                  <InputField
                    value={formData.verification_url}
                    onChangeText={value =>
                      setFormData(prev => ({ ...prev, verification_url: value }))
                    }
                    placeholder="Link to verify certificate"
                  />
                </Input>
              </FormControl>
            </VStack>
          </HStack>

          <HStack space="sm" className="justify-end">
            <Button variant="outline" onPress={onCancel}>
              <ButtonText>Cancel</ButtonText>
            </Button>
            <Button onPress={handleSubmit}>
              <ButtonText>{certification ? 'Update' : 'Add'} Certification</ButtonText>
            </Button>
          </HStack>
        </VStack>
      </Card>
    );
  };

  return (
    <ScrollView className="flex-1">
      <Box className="p-6 max-w-4xl mx-auto">
        <VStack space="lg">
          {/* Header */}
          <VStack space="sm">
            <Heading size="xl" className="text-gray-900">
              Education Background
            </Heading>
            <Text className="text-gray-600">
              Share your educational qualifications, certifications, and training to build
              credibility with students and parents.
            </Text>
          </VStack>

          {/* Degrees Section */}
          <Card>
            <VStack space="md" className="p-6">
              <HStack className="items-center justify-between">
                <HStack space="sm" className="items-center">
                  <Icon as={GraduationCap} size={20} className="text-blue-600" />
                  <Heading size="md" className="text-gray-900">
                    Degrees
                  </Heading>
                </HStack>
                <Button variant="outline" size="sm" onPress={() => setShowDegreeForm(true)}>
                  <ButtonIcon as={Plus} className="text-blue-600 mr-1" />
                  <ButtonText>Add Degree</ButtonText>
                </Button>
              </HStack>

              {showDegreeForm && (
                <DegreeForm
                  degree={editingDegree || undefined}
                  onSubmit={
                    editingDegree ? degree => updateDegree(editingDegree.id, degree) : addDegree
                  }
                  onCancel={() => {
                    setShowDegreeForm(false);
                    setEditingDegree(null);
                  }}
                />
              )}

              {formData.degrees.length > 0 ? (
                <VStack space="sm">
                  {formData.degrees.map(degree => (
                    <Card key={degree.id} className="border-gray-200">
                      <VStack space="sm" className="p-4">
                        <HStack className="items-start justify-between">
                          <VStack className="flex-1" space="xs">
                            <HStack space="sm" className="items-center">
                              <Icon as={GraduationCap} size={16} className="text-blue-600" />
                              <Text className="font-semibold text-gray-900">
                                {degree.degree_type} in {degree.field_of_study}
                              </Text>
                            </HStack>
                            <HStack space="sm" className="items-center">
                              <Icon as={MapPin} size={14} className="text-gray-500" />
                              <Text className="text-gray-700">
                                {degree.institution}
                                {degree.location && `, ${degree.location}`}
                              </Text>
                            </HStack>
                            <HStack space="sm" className="items-center">
                              <Icon as={Calendar} size={14} className="text-gray-500" />
                              <Text className="text-gray-600">
                                Graduated {degree.graduation_year}
                              </Text>
                            </HStack>
                            {degree.gpa && (
                              <Text className="text-sm text-gray-600">GPA: {degree.gpa}</Text>
                            )}
                            {degree.honors && (
                              <Badge className="bg-yellow-100 self-start">
                                <BadgeText className="text-yellow-800">{degree.honors}</BadgeText>
                              </Badge>
                            )}
                            {degree.description && (
                              <Text className="text-sm text-gray-600">{degree.description}</Text>
                            )}
                          </VStack>
                          <HStack space="xs">
                            <Button
                              variant="ghost"
                              size="sm"
                              onPress={() => {
                                setEditingDegree(degree);
                                setShowDegreeForm(true);
                              }}
                            >
                              <ButtonText>Edit</ButtonText>
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onPress={() => removeDegree(degree.id)}
                            >
                              <ButtonIcon as={X} className="text-red-500" />
                            </Button>
                          </HStack>
                        </HStack>
                      </VStack>
                    </Card>
                  ))}
                </VStack>
              ) : (
                <Box className="p-8 text-center border-2 border-dashed border-gray-300 rounded-lg">
                  <Icon as={GraduationCap} size={48} className="text-gray-400 mx-auto mb-4" />
                  <Text className="text-gray-600 mb-2">No degrees added yet</Text>
                  <Text className="text-sm text-gray-500">
                    Add your educational background to build credibility
                  </Text>
                </Box>
              )}
            </VStack>
          </Card>

          {/* Certifications Section */}
          <Card>
            <VStack space="md" className="p-6">
              <HStack className="items-center justify-between">
                <HStack space="sm" className="items-center">
                  <Icon as={Certificate} size={20} className="text-green-600" />
                  <Heading size="md" className="text-gray-900">
                    Certifications & Licenses
                  </Heading>
                </HStack>
                <Button variant="outline" size="sm" onPress={() => setShowCertificationForm(true)}>
                  <ButtonIcon as={Plus} className="text-green-600 mr-1" />
                  <ButtonText>Add Certification</ButtonText>
                </Button>
              </HStack>

              {showCertificationForm && (
                <CertificationForm
                  certification={editingCertification || undefined}
                  onSubmit={
                    editingCertification
                      ? cert => updateCertification(editingCertification.id, cert)
                      : addCertification
                  }
                  onCancel={() => {
                    setShowCertificationForm(false);
                    setEditingCertification(null);
                  }}
                />
              )}

              {formData.certifications.length > 0 ? (
                <VStack space="sm">
                  {formData.certifications.map(certification => (
                    <Card key={certification.id} className="border-gray-200">
                      <VStack space="sm" className="p-4">
                        <HStack className="items-start justify-between">
                          <VStack className="flex-1" space="xs">
                            <HStack space="sm" className="items-center">
                              <Icon as={Certificate} size={16} className="text-green-600" />
                              <Text className="font-semibold text-gray-900">
                                {certification.name}
                              </Text>
                            </HStack>
                            <Text className="text-gray-700">
                              {certification.issuing_organization}
                            </Text>
                            <HStack space="sm" className="items-center">
                              <Icon as={Calendar} size={14} className="text-gray-500" />
                              <Text className="text-gray-600">
                                Issued {certification.issue_date}
                                {certification.expiration_date &&
                                  ` • Expires ${certification.expiration_date}`}
                              </Text>
                            </HStack>
                            {certification.credential_id && (
                              <Text className="text-sm text-gray-600">
                                ID: {certification.credential_id}
                              </Text>
                            )}
                            {certification.verification_url && (
                              <Button
                                variant="ghost"
                                size="sm"
                                className="self-start"
                                onPress={() => {
                                  // Open verification URL
                                  console.log('Open URL:', certification.verification_url);
                                }}
                              >
                                <ButtonIcon as={ExternalLink} className="text-blue-600 mr-1" />
                                <ButtonText className="text-blue-600">
                                  Verify Certificate
                                </ButtonText>
                              </Button>
                            )}
                          </VStack>
                          <HStack space="xs">
                            <Button
                              variant="ghost"
                              size="sm"
                              onPress={() => {
                                setEditingCertification(certification);
                                setShowCertificationForm(true);
                              }}
                            >
                              <ButtonText>Edit</ButtonText>
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onPress={() => removeCertification(certification.id)}
                            >
                              <ButtonIcon as={X} className="text-red-500" />
                            </Button>
                          </HStack>
                        </HStack>
                      </VStack>
                    </Card>
                  ))}
                </VStack>
              ) : (
                <Box className="p-8 text-center border-2 border-dashed border-gray-300 rounded-lg">
                  <Icon as={Certificate} size={48} className="text-gray-400 mx-auto mb-4" />
                  <Text className="text-gray-600 mb-2">No certifications added yet</Text>
                  <Text className="text-sm text-gray-500">
                    Add teaching licenses, certificates, and professional credentials
                  </Text>
                </Box>
              )}
            </VStack>
          </Card>

          {/* Additional Training Section */}
          <Card>
            <VStack space="md" className="p-6">
              <HStack className="items-center justify-between">
                <HStack space="sm" className="items-center">
                  <Icon as={Award} size={20} className="text-purple-600" />
                  <Heading size="md" className="text-gray-900">
                    Additional Training & Workshops
                  </Heading>
                </HStack>
                <Button variant="outline" size="sm" onPress={() => setShowTrainingInput(true)}>
                  <ButtonIcon as={Plus} className="text-purple-600 mr-1" />
                  <ButtonText>Add Training</ButtonText>
                </Button>
              </HStack>

              <Text className="text-gray-600">
                Include professional development courses, workshops, seminars, or specialized
                training.
              </Text>

              {showTrainingInput && (
                <Card className="border-purple-200 bg-purple-50">
                  <VStack space="sm" className="p-4">
                    <FormControl>
                      <FormControlLabel>
                        <Text className="text-purple-900">Training/Workshop Details</Text>
                      </FormControlLabel>
                      <Input>
                        <InputField
                          value={newTraining}
                          onChangeText={setNewTraining}
                          placeholder="e.g., Advanced Classroom Management Workshop (2023) - National Education Association"
                          multiline
                          numberOfLines={2}
                        />
                      </Input>
                      <FormControlHelper>
                        <Text>Include name, year, and organization if applicable</Text>
                      </FormControlHelper>
                    </FormControl>
                    <HStack space="sm" className="justify-end">
                      <Button variant="outline" onPress={() => setShowTrainingInput(false)}>
                        <ButtonText>Cancel</ButtonText>
                      </Button>
                      <Button
                        onPress={() => addTraining(newTraining)}
                        isDisabled={!newTraining.trim()}
                      >
                        <ButtonText>Add Training</ButtonText>
                      </Button>
                    </HStack>
                  </VStack>
                </Card>
              )}

              {formData.additional_training.length > 0 ? (
                <VStack space="sm">
                  {formData.additional_training.map((training, index) => (
                    <HStack
                      key={index}
                      space="sm"
                      className="items-start p-3 bg-purple-50 rounded-lg"
                    >
                      <Icon as={CheckCircle2} size={16} className="text-purple-600 mt-0.5" />
                      <Text className="flex-1 text-purple-800">{training}</Text>
                      <Button
                        size="xs"
                        variant="ghost"
                        onPress={() => removeTraining(index)}
                        className="p-1"
                      >
                        <ButtonIcon as={X} size={12} className="text-purple-600" />
                      </Button>
                    </HStack>
                  ))}
                </VStack>
              ) : (
                <Box className="p-6 text-center border-2 border-dashed border-gray-300 rounded-lg">
                  <Icon as={Award} size={40} className="text-gray-400 mx-auto mb-3" />
                  <Text className="text-gray-600 mb-1">No additional training listed</Text>
                  <Text className="text-sm text-gray-500">
                    Add workshops, seminars, or professional development courses
                  </Text>
                </Box>
              )}
            </VStack>
          </Card>
        </VStack>
      </Box>
    </ScrollView>
  );
};
