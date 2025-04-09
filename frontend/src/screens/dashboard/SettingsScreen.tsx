import React from 'react';
import { StyleSheet, View, ScrollView } from 'react-native';
import { Card, List, Switch, Divider, Text } from 'react-native-paper';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuth } from '../../hooks/useAuth';

const SettingsScreen: React.FC = () => {
  const { user } = useAuth();
  const [notificationsEnabled, setNotificationsEnabled] = React.useState(true);
  const [darkMode, setDarkMode] = React.useState(false);

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <Text style={styles.headerText}>Settings</Text>

        <Card style={styles.card}>
          <Card.Title title="Preferences" />
          <Card.Content>
            <List.Item
              title="Notifications"
              description="Enable push notifications"
              left={(props) => <List.Icon {...props} icon="bell" />}
              right={() => (
                <Switch
                  value={notificationsEnabled}
                  onValueChange={setNotificationsEnabled}
                />
              )}
            />
            <Divider />
            <List.Item
              title="Dark Mode"
              description="Enable dark theme"
              left={(props) => <List.Icon {...props} icon="moon-waning-crescent" />}
              right={() => (
                <Switch
                  value={darkMode}
                  onValueChange={setDarkMode}
                />
              )}
            />
          </Card.Content>
        </Card>

        <Card style={styles.card}>
          <Card.Title title="Account" />
          <Card.Content>
            <List.Item
              title="Change Email"
              description={user?.email}
              left={(props) => <List.Icon {...props} icon="email" />}
              onPress={() => {}}
            />
            <Divider />
            <List.Item
              title="Privacy Settings"
              left={(props) => <List.Icon {...props} icon="shield-account" />}
              onPress={() => {}}
            />
          </Card.Content>
        </Card>

        <Card style={styles.card}>
          <Card.Title title="Support" />
          <Card.Content>
            <List.Item
              title="Help Center"
              left={(props) => <List.Icon {...props} icon="help-circle" />}
              onPress={() => {}}
            />
            <Divider />
            <List.Item
              title="About"
              description="Version 1.0.0"
              left={(props) => <List.Icon {...props} icon="information" />}
              onPress={() => {}}
            />
          </Card.Content>
        </Card>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
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
});

export default SettingsScreen; 