import { Search, X, Users, Hash, Check } from 'lucide-react-native';
import React, { useState } from 'react';

import { useAuth } from '@/api/authContext';
import { User, createChannel, searchUsers } from '@/api/channelApi';
import { Avatar, AvatarFallbackText } from '@/components/ui/avatar';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Input, InputField, InputIcon } from '@/components/ui/input';
import {
  Modal,
  ModalBackdrop,
  ModalContent,
  ModalHeader,
  ModalCloseButton,
  ModalBody,
  ModalFooter,
} from '@/components/ui/modal';
import { Pressable } from '@/components/ui/pressable';
import { ScrollView } from '@/components/ui/scroll-view';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

interface CreateChannelModalProps {
  isOpen: boolean;
  onClose: () => void;
  onChannelCreated: () => void;
}

export const CreateChannelModal = ({
  isOpen,
  onClose,
  onChannelCreated,
}: CreateChannelModalProps) => {
  const [step, setStep] = useState<'type' | 'details' | 'participants'>('type');
  const [channelType, setChannelType] = useState<'group' | 'dm'>('group');
  const [channelName, setChannelName] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<User[]>([]);
  const [selectedUsers, setSelectedUsers] = useState<User[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const { userProfile } = useAuth();

  const handleSearch = async (query: string) => {
    setSearchQuery(query);
    if (query.trim().length > 0) {
      setIsSearching(true);
      try {
        const results = await searchUsers(query);
        setSearchResults(results);
      } catch (error) {
        console.error('Error searching users:', error);
      } finally {
        setIsSearching(false);
      }
    } else {
      setSearchResults([]);
    }
  };

  const toggleUserSelection = (user: User) => {
    setSelectedUsers(prev => {
      const isSelected = prev.some(u => u.id === user.id);
      if (isSelected) {
        return prev.filter(u => u.id !== user.id);
      } else {
        return [...prev, user];
      }
    });
  };

  const handleCreateChannel = async () => {
    if (!channelName.trim() && channelType === 'group') return;
    if (selectedUsers.length === 0) return;

    setIsCreating(true);
    try {
      const participantIds = selectedUsers.map(u => u.id);
      const name = channelType === 'dm' ? 'Direct Message' : channelName;

      await createChannel(name, channelType === 'dm', participantIds);

      // Reset form
      setStep('type');
      setChannelType('group');
      setChannelName('');
      setSearchQuery('');
      setSearchResults([]);
      setSelectedUsers([]);

      onChannelCreated();
      onClose();
    } catch (error) {
      console.error('Error creating channel:', error);
    } finally {
      setIsCreating(false);
    }
  };

  const canProceed = () => {
    if (step === 'type') return true;
    if (step === 'details') {
      return channelType === 'dm' || channelName.trim().length > 0;
    }
    if (step === 'participants') {
      return selectedUsers.length > 0 && (channelType === 'group' || selectedUsers.length === 1);
    }
    return false;
  };

  const getNextStep = () => {
    if (step === 'type') return 'details';
    if (step === 'details') return 'participants';
    return 'participants';
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose}>
      <ModalBackdrop />
      <ModalContent className="max-w-md">
        <ModalHeader>
          <Heading size="lg">
            {step === 'type' && 'Criar Conversa'}
            {step === 'details' && 'Detalhes da Conversa'}
            {step === 'participants' && 'Adicionar Participantes'}
          </Heading>
          <ModalCloseButton>
            <Icon as={X} size="md" />
          </ModalCloseButton>
        </ModalHeader>

        <ModalBody>
          {step === 'type' && (
            <VStack space="md">
              <Text className="text-gray-600">Escolha o tipo de conversa que deseja criar:</Text>

              <Pressable
                onPress={() => setChannelType('group')}
                className={`p-4 border rounded-lg ${
                  channelType === 'group' ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
                }`}
              >
                <HStack space="md" className="items-center">
                  <Icon as={Hash} size="md" className="text-blue-600" />
                  <VStack className="flex-1">
                    <Text className="font-semibold">Canal do Grupo</Text>
                    <Text className="text-sm text-gray-600">
                      Conversa em grupo com vários participantes
                    </Text>
                  </VStack>
                </HStack>
              </Pressable>

              <Pressable
                onPress={() => setChannelType('dm')}
                className={`p-4 border rounded-lg ${
                  channelType === 'dm' ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
                }`}
              >
                <HStack space="md" className="items-center">
                  <Icon as={Users} size="md" className="text-green-600" />
                  <VStack className="flex-1">
                    <Text className="font-semibold">Mensagem Direta</Text>
                    <Text className="text-sm text-gray-600">Conversa privada com uma pessoa</Text>
                  </VStack>
                </HStack>
              </Pressable>
            </VStack>
          )}

          {step === 'details' && (
            <VStack space="md">
              {channelType === 'group' && (
                <VStack space="sm">
                  <Text className="font-semibold">Nome do Canal</Text>
                  <Input>
                    <InputField
                      placeholder="ex: matematica-turma-a"
                      value={channelName}
                      onChangeText={setChannelName}
                    />
                  </Input>
                  <Text className="text-xs text-gray-500">
                    Use apenas letras minúsculas, números e hífens
                  </Text>
                </VStack>
              )}

              {channelType === 'dm' && (
                <Text className="text-gray-600">
                  Você criará uma conversa direta. Escolha a pessoa com quem deseja conversar na
                  próxima etapa.
                </Text>
              )}
            </VStack>
          )}

          {step === 'participants' && (
            <VStack space="md">
              <VStack space="sm">
                <Text className="font-semibold">
                  {channelType === 'dm' ? 'Escolha uma pessoa' : 'Adicionar participantes'}
                </Text>
                <Input>
                  <InputIcon as={Search} className="text-gray-400" />
                  <InputField
                    placeholder="Buscar por nome ou email..."
                    value={searchQuery}
                    onChangeText={handleSearch}
                  />
                </Input>
              </VStack>

              {selectedUsers.length > 0 && (
                <VStack space="sm">
                  <Text className="font-semibold text-sm">Selecionados:</Text>
                  <ScrollView horizontal className="max-h-20">
                    <HStack space="sm" className="px-1">
                      {selectedUsers.map(user => (
                        <Pressable
                          key={user.id}
                          onPress={() => toggleUserSelection(user)}
                          className="items-center"
                        >
                          <Box className="relative">
                            <Avatar className="bg-blue-100 h-12 w-12">
                              <AvatarFallbackText>
                                {user.first_name[0]}
                                {user.last_name[0]}
                              </AvatarFallbackText>
                            </Avatar>
                            <Box className="absolute -top-1 -right-1 bg-red-500 rounded-full h-5 w-5 items-center justify-center">
                              <Icon as={X} size="xs" className="text-white" />
                            </Box>
                          </Box>
                          <Text className="text-xs mt-1 text-center max-w-16">
                            {user.first_name}
                          </Text>
                        </Pressable>
                      ))}
                    </HStack>
                  </ScrollView>
                </VStack>
              )}

              <ScrollView className="max-h-60">
                <VStack space="sm">
                  {isSearching && <Text className="text-gray-500 text-center">Buscando...</Text>}

                  {searchResults.map(user => {
                    const isSelected = selectedUsers.some(u => u.id === user.id);
                    return (
                      <Pressable
                        key={user.id}
                        onPress={() => toggleUserSelection(user)}
                        className={`p-3 rounded-lg border ${
                          isSelected ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
                        }`}
                      >
                        <HStack space="sm" className="items-center">
                          <Avatar className="bg-purple-100 h-8 w-8">
                            <AvatarFallbackText>
                              {user.first_name[0]}
                              {user.last_name[0]}
                            </AvatarFallbackText>
                          </Avatar>
                          <VStack className="flex-1">
                            <Text className="font-medium">
                              {user.first_name} {user.last_name}
                            </Text>
                            <Text className="text-sm text-gray-600">{user.email}</Text>
                          </VStack>
                          {isSelected && <Icon as={Check} size="sm" className="text-blue-500" />}
                        </HStack>
                      </Pressable>
                    );
                  })}

                  {searchQuery && searchResults.length === 0 && !isSearching && (
                    <Text className="text-gray-500 text-center py-4">
                      Nenhum usuário encontrado
                    </Text>
                  )}
                </VStack>
              </ScrollView>
            </VStack>
          )}
        </ModalBody>

        <ModalFooter>
          <HStack space="sm" className="w-full">
            {step !== 'type' && (
              <Button
                variant="outline"
                onPress={() => {
                  if (step === 'details') setStep('type');
                  if (step === 'participants') setStep('details');
                }}
                className="flex-1"
              >
                <ButtonText>Voltar</ButtonText>
              </Button>
            )}

            {step !== 'participants' ? (
              <Button
                onPress={() => setStep(getNextStep())}
                isDisabled={!canProceed()}
                className="flex-1"
              >
                <ButtonText>Continuar</ButtonText>
              </Button>
            ) : (
              <Button
                onPress={handleCreateChannel}
                isDisabled={!canProceed() || isCreating}
                className="flex-1"
              >
                <ButtonText>{isCreating ? 'Criando...' : 'Criar Conversa'}</ButtonText>
              </Button>
            )}
          </HStack>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};

export default CreateChannelModal;
