import React, { useState } from 'react';
import { StyleSheet, View, KeyboardAvoidingView, Platform, ScrollView } from 'react-native';
import { Button, TextInput, Text, Card } from 'react-native-paper';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { AuthStackParamList } from '../../navigation/types';
import { getUserProfile, verifyEmailCode } from '../../api/authApi';
import { useAuth } from '../../hooks/useAuth';
import { SafeAreaView } from 'react-native-safe-area-context';

type Props = NativeStackScreenProps<AuthStackParamList, 'VerifyCode'>;

const VerifyCodeScreen: React.FC<Props> = ({ route }) => {
  const { email } = route.params;
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { login } = useAuth();

  const handleVerifyCode = async () => {
    if (!code.trim()) {
      setError('Code is required');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Verify the code and get tokens
      await verifyEmailCode({ email, code });
      
      // Get user profile
      const userProfile = await getUserProfile();
      
      // Set the user in context
      login(userProfile);
    } catch (err) {
      setError('Invalid verification code. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardView}
      >
        <ScrollView contentContainerStyle={styles.scrollView}>
          <Card style={styles.card}>
            <Card.Title title="Enter Verification Code" />
            <Card.Content>
              <Text style={styles.subtitle}>
                Enter the 6-digit code sent to {email}
              </Text>
              
              <TextInput
                label="Code"
                value={code}
                onChangeText={setCode}
                keyboardType="number-pad"
                maxLength={6}
                style={styles.input}
              />
              
              {error && <Text style={styles.errorText}>{error}</Text>}
              
              <Button
                mode="contained"
                onPress={handleVerifyCode}
                loading={loading}
                disabled={loading}
                style={styles.button}
              >
                Verify Code
              </Button>
            </Card.Content>
          </Card>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  keyboardView: {
    flex: 1,
  },
  scrollView: {
    flexGrow: 1,
    justifyContent: 'center',
    padding: 20,
  },
  card: {
    padding: 16,
  },
  subtitle: {
    marginVertical: 16,
    fontSize: 16,
    color: '#555',
  },
  input: {
    marginBottom: 16,
  },
  button: {
    marginTop: 16,
  },
  errorText: {
    color: 'red',
    marginBottom: 16,
  },
});

export default VerifyCodeScreen; 