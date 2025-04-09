import React, { useEffect, useState } from 'react';
import { StyleSheet, View, ScrollView } from 'react-native';
import { Card, Text, Button, ActivityIndicator } from 'react-native-paper';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuth } from '../../hooks/useAuth';
import { getTeacherProfile, getStudentProfile, TeacherProfile, StudentProfile } from '../../api/userApi';

const ProfileScreen: React.FC = () => {
  const { user, logout } = useAuth();
  const [loading, setLoading] = useState(true);
  const [profile, setProfile] = useState<TeacherProfile | StudentProfile | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchProfile = async () => {
      if (!user) return;

      setLoading(true);
      try {
        if (user.user_type === 'teacher') {
          const teacherProfile = await getTeacherProfile();
          setProfile(teacherProfile);
        } else if (user.user_type === 'student') {
          const studentProfile = await getStudentProfile();
          setProfile(studentProfile);
        }
        setError(null);
      } catch (err) {
        console.error(err);
        setError('Failed to load profile information');
      } finally {
        setLoading(false);
      }
    };

    fetchProfile();
  }, [user]);

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" />
      </View>
    );
  }

  const handleLogout = async () => {
    await logout();
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <Text style={styles.headerText}>My Profile</Text>

        {error ? (
          <Card style={styles.errorCard}>
            <Card.Content>
              <Text>{error}</Text>
            </Card.Content>
          </Card>
        ) : (
          <>
            <Card style={styles.card}>
              <Card.Title title="Account Information" />
              <Card.Content>
                <Text style={styles.fieldLabel}>Name</Text>
                <Text style={styles.fieldValue}>{user?.name}</Text>

                <Text style={styles.fieldLabel}>Email</Text>
                <Text style={styles.fieldValue}>{user?.email}</Text>

                <Text style={styles.fieldLabel}>Phone</Text>
                <Text style={styles.fieldValue}>{user?.phone_number || 'Not set'}</Text>

                <Text style={styles.fieldLabel}>Role</Text>
                <Text style={styles.fieldValue}>{user?.user_type}</Text>
              </Card.Content>
            </Card>

            {user?.user_type === 'teacher' && profile && (
              <Card style={styles.card}>
                <Card.Title title="Teacher Information" />
                <Card.Content>
                  <Text style={styles.fieldLabel}>Specialty</Text>
                  <Text style={styles.fieldValue}>
                    {(profile as TeacherProfile).specialty || 'Not set'}
                  </Text>

                  <Text style={styles.fieldLabel}>Hourly Rate</Text>
                  <Text style={styles.fieldValue}>
                    €{(profile as TeacherProfile).hourly_rate || 'Not set'}
                  </Text>

                  <Text style={styles.fieldLabel}>Education</Text>
                  <Text style={styles.fieldValue}>
                    {(profile as TeacherProfile).education || 'Not set'}
                  </Text>

                  <Text style={styles.fieldLabel}>Bio</Text>
                  <Text style={styles.fieldValue}>
                    {(profile as TeacherProfile).bio || 'Not set'}
                  </Text>
                </Card.Content>
                <Card.Actions>
                  <Button mode="outlined">Edit Profile</Button>
                </Card.Actions>
              </Card>
            )}

            {user?.user_type === 'student' && profile && (
              <Card style={styles.card}>
                <Card.Title title="Student Information" />
                <Card.Content>
                  <Text style={styles.fieldLabel}>School Year</Text>
                  <Text style={styles.fieldValue}>
                    {(profile as StudentProfile).school_year || 'Not set'}
                  </Text>

                  <Text style={styles.fieldLabel}>Birth Date</Text>
                  <Text style={styles.fieldValue}>
                    {(profile as StudentProfile).birth_date
                      ? new Date((profile as StudentProfile).birth_date).toLocaleDateString()
                      : 'Not set'}
                  </Text>

                  <Text style={styles.fieldLabel}>Address</Text>
                  <Text style={styles.fieldValue}>
                    {(profile as StudentProfile).address || 'Not set'}
                  </Text>
                </Card.Content>
                <Card.Actions>
                  <Button mode="outlined">Edit Profile</Button>
                </Card.Actions>
              </Card>
            )}

            <Button
              mode="contained"
              onPress={handleLogout}
              style={styles.logoutButton}
              color="#f44336"
            >
              Logout
            </Button>
          </>
        )}
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  scrollContent: {
    padding: 16,
  },
  headerText: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 16,
  },
  card: {
    marginBottom: 16,
  },
  errorCard: {
    marginBottom: 16,
    backgroundColor: '#ffebee',
  },
  fieldLabel: {
    fontSize: 14,
    color: '#666',
    marginTop: 12,
  },
  fieldValue: {
    fontSize: 16,
    marginBottom: 8,
  },
  logoutButton: {
    marginTop: 16,
  },
});

export default ProfileScreen; 