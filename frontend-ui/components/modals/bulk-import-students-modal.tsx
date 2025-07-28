import React, { useState, useCallback } from 'react';
import { X, Upload, Download, FileText, AlertCircle, CheckCircle, AlertTriangle } from 'lucide-react-native';

import { useStudents } from '@/hooks/useStudents';
import { BulkImportResult } from '@/api/userApi';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import {
  Modal,
  ModalBackdrop,
  ModalContent,
  ModalHeader,
  ModalCloseButton,
  ModalBody,
  ModalFooter,
} from '@/components/ui/modal';
import { ScrollView } from '@/components/ui/scroll-view';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { useToast } from '@/components/ui/toast';
import { VStack } from '@/components/ui/vstack';
import { Pressable } from '@/components/ui/pressable';

// Color constants
const COLORS = {
  primary: '#156082',
  secondary: '#FFC000',
  white: '#FFFFFF',
  gray: {
    50: '#F9FAFB',
    100: '#F3F4F6',
    200: '#E5E7EB',
    300: '#D1D5DB',
    500: '#6B7280',
    600: '#4B5563',
    700: '#374151',
    900: '#111827',
  },
  success: '#10B981',
  warning: '#F59E0B',
  error: '#EF4444',
} as const;

interface BulkImportStudentsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

interface DropZoneProps {
  onFileSelect: (file: File) => void;
  isDragOver: boolean;
  onDragOver: (event: React.DragEvent) => void;
  onDragLeave: (event: React.DragEvent) => void;
  onDrop: (event: React.DragEvent) => void;
}

const DropZone: React.FC<DropZoneProps> = ({
  onFileSelect,
  isDragOver,
  onDragOver,
  onDragLeave,
  onDrop,
}) => {
  const handleFileInput = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      onFileSelect(file);
    }
  };

  return (
    <Box
      className={`
        border-2 border-dashed rounded-lg p-8 text-center transition-colors
        ${isDragOver ? 'border-primary-400 bg-primary-50' : 'border-gray-300 bg-gray-50'}
      `}
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      onDrop={onDrop}
    >
      <VStack className="items-center" space="md">
        <Icon 
          as={Upload} 
          size="xl" 
          className={isDragOver ? 'text-primary-500' : 'text-gray-400'} 
        />
        <VStack className="items-center" space="sm">
          <Text className="text-lg font-medium text-gray-900">
            Arraste o arquivo CSV aqui
          </Text>
          <Text className="text-gray-500">
            ou clique para selecionar um arquivo
          </Text>
        </VStack>
        
        <input
          type="file"
          accept=".csv"
          onChange={handleFileInput}
          style={{ display: 'none' }}
          id="csv-file-input"
        />
        
        <Button
          variant="outline"
          onPress={() => document.getElementById('csv-file-input')?.click()}
        >
          <HStack space="xs" className="items-center">
            <Icon as={FileText} size="sm" />
            <ButtonText>Selecionar Arquivo CSV</ButtonText>
          </HStack>
        </Button>
        
        <Text className="text-xs text-gray-400">
          Apenas arquivos .csv são aceitos
        </Text>
      </VStack>
    </Box>
  );
};

interface ImportResultProps {
  result: BulkImportResult;
  onReset: () => void;
}

const ImportResult: React.FC<ImportResultProps> = ({ result, onReset }) => {
  const getStatusIcon = () => {
    if (result.success) {
      return result.failed_count > 0 ? AlertTriangle : CheckCircle;
    }
    return AlertCircle;
  };

  const getStatusColor = () => {
    if (result.success) {
      return result.failed_count > 0 ? COLORS.warning : COLORS.success;
    }
    return COLORS.error;
  };

  const StatusIcon = getStatusIcon();
  const statusColor = getStatusColor();

  return (
    <VStack space="lg">
      {/* Status Summary */}
      <Box className="p-4 rounded-lg" style={{ backgroundColor: `${statusColor}20` }}>
        <HStack className="items-center" space="sm">
          <Icon as={StatusIcon} style={{ color: statusColor }} />
          <VStack className="flex-1">
            <Text className="font-medium" style={{ color: statusColor }}>
              {result.success ? 'Importação Concluída' : 'Erro na Importação'}
            </Text>
            <Text className="text-sm text-gray-600">
              {result.created_count} alunos criados com sucesso
              {result.failed_count > 0 && `, ${result.failed_count} falhas`}
            </Text>
          </VStack>
        </HStack>
      </Box>

      {/* Detailed Results */}
      <VStack space="md">
        <HStack className="justify-between p-3 bg-green-50 rounded-lg">
          <Text className="text-green-700">Alunos criados:</Text>
          <Text className="font-bold text-green-700">{result.created_count}</Text>
        </HStack>

        {result.failed_count > 0 && (
          <HStack className="justify-between p-3 bg-red-50 rounded-lg">
            <Text className="text-red-700">Falhas:</Text>
            <Text className="font-bold text-red-700">{result.failed_count}</Text>
          </HStack>
        )}
      </VStack>

      {/* Error Details */}
      {result.errors && result.errors.length > 0 && (
        <VStack space="sm">
          <Text className="font-medium text-gray-900">Detalhes dos Erros:</Text>
          <ScrollView className="max-h-40 border border-gray-200 rounded-lg p-3">
            <VStack space="xs">
              {result.errors.map((error, index) => (
                <Text key={index} className="text-sm text-red-600">
                  Linha {error.row}: {error.field} - {error.message}
                </Text>
              ))}
            </VStack>
          </ScrollView>
        </VStack>
      )}

      {/* Actions */}
      <HStack space="sm" className="justify-center">
        <Button variant="outline" onPress={onReset}>
          <ButtonText>Importar Outro Arquivo</ButtonText>
        </Button>
      </HStack>
    </VStack>
  );
};

export const BulkImportStudentsModal: React.FC<BulkImportStudentsModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const { showToast } = useToast();
  const { bulkImportStudentsFromCSV, isBulkImporting } = useStudents({ autoLoad: false });

  // State
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [importResult, setImportResult] = useState<BulkImportResult | null>(null);
  const [step, setStep] = useState<'upload' | 'importing' | 'result'>('upload');

  // Reset modal state
  const resetModal = () => {
    setSelectedFile(null);
    setIsDragOver(false);
    setImportResult(null);
    setStep('upload');
  };

  // Handle file selection
  const handleFileSelect = useCallback((file: File) => {
    if (file.type !== 'text/csv' && !file.name.endsWith('.csv')) {
      showToast('error', 'Por favor, selecione um arquivo CSV válido');
      return;
    }

    if (file.size > 5 * 1024 * 1024) { // 5MB limit
      showToast('error', 'O arquivo é muito grande. Máximo 5MB permitido');
      return;
    }

    setSelectedFile(file);
  }, [showToast]);

  // Drag and drop handlers
  const handleDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    setIsDragOver(false);
    
    const files = event.dataTransfer.files;
    if (files.length > 0) {
      handleFileSelect(files[0]);
    }
  }, [handleFileSelect]);

  // Handle import
  const handleImport = async () => {
    if (!selectedFile) return;

    try {
      setStep('importing');
      const result = await bulkImportStudentsFromCSV(selectedFile);
      setImportResult(result);
      setStep('result');
      
      if (result.success) {
        onSuccess();
        if (result.failed_count === 0) {
          showToast('success', `${result.created_count} alunos importados com sucesso!`);
        } else {
          showToast('warning', `${result.created_count} alunos importados, ${result.failed_count} com falhas`);
        }
      } else {
        showToast('error', 'Falha na importação. Verifique os detalhes.');
      }
    } catch (error: any) {
      console.error('Import failed:', error);
      showToast('error', error.message || 'Erro ao importar arquivo');
      setStep('upload');
    }
  };

  // Handle close
  const handleClose = () => {
    resetModal();
    onClose();
  };

  // Download template
  const downloadTemplate = () => {
    const csvContent = [
      'name,email,phone_number,school_year,birth_date,address,educational_system_id',
      'João Silva,joao.silva@example.com,+351912345678,10º ano,2005-06-15,Rua da Escola 123,1',
      'Maria Santos,maria.santos@example.com,+351987654321,11º ano,2004-03-22,Avenida Central 456,1',
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', 'template_alunos.csv');
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const renderContent = () => {
    switch (step) {
      case 'upload':
        return (
          <VStack space="lg">
            {/* Instructions */}
            <VStack space="md">
              <Text className="text-gray-600">
                Importe múltiplos alunos de uma só vez usando um arquivo CSV. 
                Certifique-se de que o arquivo contém as colunas obrigatórias.
              </Text>
              
              <Button variant="outline" onPress={downloadTemplate}>
                <HStack space="xs" className="items-center">
                  <Icon as={Download} size="sm" />
                  <ButtonText>Baixar Modelo CSV</ButtonText>
                </HStack>
              </Button>
            </VStack>

            {/* File Upload */}
            {!selectedFile ? (
              <DropZone
                onFileSelect={handleFileSelect}
                isDragOver={isDragOver}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
              />
            ) : (
              <Box className="p-4 border border-gray-200 rounded-lg bg-gray-50">
                <HStack className="items-center justify-between">
                  <HStack className="items-center" space="sm">
                    <Icon as={FileText} className="text-gray-500" />
                    <VStack>
                      <Text className="font-medium text-gray-900">{selectedFile.name}</Text>
                      <Text className="text-sm text-gray-500">
                        {(selectedFile.size / 1024).toFixed(1)} KB
                      </Text>
                    </VStack>
                  </HStack>
                  <Button
                    variant="outline"
                    size="sm"
                    onPress={() => setSelectedFile(null)}
                  >
                    <Icon as={X} size="sm" />
                  </Button>
                </HStack>
              </Box>
            )}

            {/* Requirements */}
            <Box className="p-4 bg-blue-50 rounded-lg">
              <VStack space="sm">
                <Text className="font-medium text-blue-900">Requisitos do arquivo CSV:</Text>
                <VStack space="xs">
                  <Text className="text-sm text-blue-700">• Colunas obrigatórias: name, email, school_year, birth_date</Text>
                  <Text className="text-sm text-blue-700">• Formato da data: AAAA-MM-DD (ex: 2005-06-15)</Text>
                  <Text className="text-sm text-blue-700">• educational_system_id: 1 para Portugal (padrão)</Text>
                  <Text className="text-sm text-blue-700">• Máximo 5MB por arquivo</Text>
                </VStack>
              </VStack>
            </Box>
          </VStack>
        );

      case 'importing':
        return (
          <Box className="p-8">
            <Center>
              <VStack className="items-center" space="lg">
                <Spinner size="large" />
                <VStack className="items-center" space="sm">
                  <Text className="text-lg font-medium text-gray-900">
                    Importando alunos...
                  </Text>
                  <Text className="text-gray-600 text-center">
                    Processando arquivo {selectedFile?.name}
                  </Text>
                </VStack>
              </VStack>
            </Center>
          </Box>
        );

      case 'result':
        return importResult ? (
          <ImportResult
            result={importResult}
            onReset={() => {
              setStep('upload');
              setSelectedFile(null);
              setImportResult(null);
            }}
          />
        ) : null;

      default:
        return null;
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose} size="lg">
      <ModalBackdrop />
      <ModalContent>
        <ModalHeader>
          <Heading size="lg">Importação em Massa de Alunos</Heading>
          <ModalCloseButton>
            <Icon as={X} />
          </ModalCloseButton>
        </ModalHeader>

        <ModalBody>
          <ScrollView showsVerticalScrollIndicator={false}>
            {renderContent()}
          </ScrollView>
        </ModalBody>

        {step === 'upload' && (
          <ModalFooter>
            <HStack space="sm" className="justify-end">
              <Button variant="outline" onPress={handleClose}>
                <ButtonText>Cancelar</ButtonText>
              </Button>
              <Button
                onPress={handleImport}
                disabled={!selectedFile || isBulkImporting}
                style={{ backgroundColor: COLORS.primary }}
              >
                {isBulkImporting ? (
                  <HStack space="xs" className="items-center">
                    <Spinner size="small" />
                    <ButtonText className="text-white">Importando...</ButtonText>
                  </HStack>
                ) : (
                  <ButtonText className="text-white">Importar Alunos</ButtonText>
                )}
              </Button>
            </HStack>
          </ModalFooter>
        )}

        {step === 'result' && (
          <ModalFooter>
            <HStack space="sm" className="justify-end">
              <Button onPress={handleClose}>
                <ButtonText>Fechar</ButtonText>
              </Button>
            </HStack>
          </ModalFooter>
        )}
      </ModalContent>
    </Modal>
  );
};