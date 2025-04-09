import React, { useEffect, useState } from 'react';
import { StyleSheet, View, ScrollView, RefreshControl } from 'react-native';
import { Card, Text, ActivityIndicator, Button } from 'react-native-paper';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuth } from '../../hooks/useAuth';
import { DashboardInfo } from '../../api/userApi';
import { getDashboardInfo } from '../../api/userApi';

const HomeScreen: React.FC = () => {
  const { user } = useAuth();
  const [dashboardData, setDashboardData] = useState<DashboardInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboard = async () => {
    try {
      const data = await getDashboardInfo();
      setDashboardData(data);
      setError(null);
    } catch (err) {
      console.error(err);
      setError('Failed to load dashboard information');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    fetchDashboard();
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" />
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        <Text style={styles.welcomeText}>Welcome, {user?.name || 'User'}</Text>

        {error ? (
          <Card style={styles.errorCard}>
            <Card.Content>
              <Text>{error}</Text>
              <Button onPress={fetchDashboard} style={styles.retryButton}>
                Retry
              </Button>
            </Card.Content>
          </Card>
        ) : (
          <>
            <Card style={styles.card}>
              <Card.Title title="User Information" />
              <Card.Content>
                <Text>Email: {dashboardData?.user_info.email}</Text>
                <Text>Role: {dashboardData?.user_info.user_type}</Text>
                <Text>
                  Joined: {new Date(dashboardData?.user_info.date_joined || '').toLocaleDateString()}
                </Text>
              </Card.Content>
            </Card>

            <Card style={styles.card}>
              <Card.Title title="Stats" />
              <Card.Content>
                {user?.user_type === 'teacher' && (
                  <>
                    <Text>Today's Classes: {dashboardData?.stats.today_classes || 0}</Text>
                    <Text>Weekly Classes: {dashboardData?.stats.week_classes || 0}</Text>
                    <Text>Students: {dashboardData?.stats.student_count || 0}</Text>
                    <Text>Monthly Earnings: {dashboardData?.stats.monthly_earnings || 0}</Text>
                  </>
                )}

                {user?.user_type === 'student' && (
                  <>
                    <Text>Upcoming Classes: {dashboardData?.stats.upcoming_classes || 0}</Text>
                    <Text>Completed Classes: {dashboardData?.stats.completed_classes || 0}</Text>
                    <Text>Balance: {dashboardData?.stats.balance || '$0'}</Text>
                  </>
                )}

                {(user?.is_admin || user?.user_type === 'admin') && (
                  <>
                    <Text>Total Students: {dashboardData?.stats.student_count || 0}</Text>
                    <Text>Total Teachers: {dashboardData?.stats.teacher_count || 0}</Text>
                  </>
                )}
              </Card.Content>
            </Card>

            {user?.user_type === 'student' && dashboardData?.user_info.needs_onboarding && (
              <Card style={[styles.card, styles.warningCard]}>
                <Card.Title title="Complete Your Profile" />
                <Card.Content>
                  <Text>Please complete your profile to access all features.</Text>
                  <Button mode="contained" style={styles.actionButton}>
                    Complete Profile
                  </Button>
                </Card.Content>
              </Card>
            )}
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
  welcomeText: {
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
  warningCard: {
    backgroundColor: '#fff8e1',
  },
  retryButton: {
    marginTop: 8,
  },
  actionButton: {
    marginTop: 16,
  },
});

export default HomeScreen; 