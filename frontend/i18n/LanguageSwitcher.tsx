import {
  Box,
  Button,
  ButtonText,
  HStack,
  VStack,
  Text,
  Spinner,
  Alert,
  AlertIcon,
  AlertText,
  Icon,
  CheckIcon,
  InfoIcon,
} from '@gluestack-ui/themed';
import React from 'react';
import { useTranslation } from 'react-i18next';

import { useLanguage } from './useLanguage';

/**
 * Language switcher component with loading states and error handling
 * Demonstrates the optimized i18n implementation
 */
export const LanguageSwitcher: React.FC = () => {
  const { t } = useTranslation();
  const { availableLanguages, isChangingLanguage, error, changeLanguage, clearError } =
    useLanguage();

  return (
    <VStack space="md" p="$4">
      <Text size="lg" fontWeight="bold">
        {t('settings.language')}
      </Text>

      {error && (
        <Alert action="error" variant="solid">
          <AlertIcon as={InfoIcon} />
          <AlertText>{error}</AlertText>
          <Button size="sm" variant="outline" onPress={clearError} ml="auto">
            <ButtonText>{'Dismiss'}</ButtonText>
          </Button>
        </Alert>
      )}

      <VStack space="sm">
        <Text size="sm" color="$textLight600">
          {t('common.current')}: {availableLanguages.find(lang => lang.isCurrent)?.name}
        </Text>

        <HStack space="md" flexWrap="wrap">
          {availableLanguages.map(language => (
            <Button
              key={language.code}
              variant={language.isCurrent ? 'solid' : 'outline'}
              size="md"
              isDisabled={isChangingLanguage}
              onPress={() => changeLanguage(language.code)}
              opacity={isChangingLanguage && !language.isCurrent ? 0.5 : 1}
              minWidth="$24"
            >
              <HStack space="xs" alignItems="center">
                {isChangingLanguage && !language.isCurrent && <Spinner size="small" />}
                {language.isCurrent && <Icon as={CheckIcon} size="sm" />}
                <ButtonText>{language.name}</ButtonText>
              </HStack>
            </Button>
          ))}
        </HStack>
      </VStack>

      {isChangingLanguage && (
        <Box
          bg="$backgroundLight100"
          p="$3"
          borderRadius="$md"
          borderWidth="$1"
          borderColor="$borderLight200"
        >
          <HStack space="sm" alignItems="center">
            <Spinner size="small" />
            <Text size="sm" color="$textLight600">
              {t('common.loading')}
            </Text>
          </HStack>
        </Box>
      )}

      {/* Debug info for development */}
      {process.env.NODE_ENV === 'development' && (
        <VStack space="xs" p="$3" bg="$backgroundLight50" borderRadius="$md">
          <Text size="xs" fontWeight="bold" color="$textLight500">
            Debug Info:
          </Text>
          {availableLanguages.map(lang => (
            <Text key={lang.code} size="xs" color="$textLight500">
              {lang.code}: {lang.isLoaded ? '✅ Loaded' : '❌ Not loaded'}
            </Text>
          ))}
        </VStack>
      )}
    </VStack>
  );
};

export default LanguageSwitcher;
