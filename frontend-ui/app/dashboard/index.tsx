import React, { useEffect, useState } from "react";
import { VStack } from "@/components/ui/vstack";
import { HStack } from "@/components/ui/hstack";
import { Heading } from "@/components/ui/heading";
import { Text } from "@/components/ui/text";
import { Button, ButtonText } from "@/components/ui/button";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { getDashboardInfo } from "@/api/userApi";
import { useAuth } from "@/api/authContext";
import { Spinner } from "@/components/ui/spinner";
import { Box } from "@/components/ui/box";
import { Alert, AlertIcon, AlertText } from "@/components/ui/alert";
import { InfoIcon } from "@/components/ui/icon";

export default function Dashboard() {
  const { isLoggedIn, userProfile, logout } = useAuth();
  const [dashboardData, setDashboardData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        const data = await getDashboardInfo();
        setDashboardData(data);
        setError(null);
      } catch (err) {
        console.error('Error fetching dashboard data:', err);
        setError("Failed to load dashboard data. Please try again later.");
      } finally {
        setLoading(false);
      }
    };

    if (isLoggedIn) {
      fetchDashboardData();
    }
  }, [isLoggedIn]);

  if (loading) {
    return (
      <VStack className="flex-1 justify-center items-center p-4 bg-background-50">
        <Spinner size="large" />
        <Text className="mt-4">Loading dashboard...</Text>
      </VStack>
    );
  }

  if (error) {
    return (
      <VStack className="flex-1 justify-center items-center p-4 bg-background-50">
        <Alert action="error" className="mb-4">
          <AlertIcon as={InfoIcon} />
          <AlertText>{error}</AlertText>
        </Alert>
        <Button onPress={logout}>
          <ButtonText>Logout</ButtonText>
        </Button>
      </VStack>
    );
  }

  return (
    <VStack className="flex-1 p-4 bg-background-50">
      <HStack className="justify-between items-center mb-8">
        <Heading size="2xl">Dashboard</Heading>
        <Button action="secondary" onPress={logout}>
          <ButtonText>Logout</ButtonText>
        </Button>
      </HStack>

      {userProfile && (
        <Card className="mb-4">
          <CardHeader>
            <Heading size="lg">Your Profile</Heading>
          </CardHeader>
          <CardBody>
            <VStack space="sm">
              <HStack space="md">
                <Text className="font-medium">Name:</Text>
                <Text>{userProfile.name}</Text>
              </HStack>
              <HStack space="md">
                <Text className="font-medium">Email:</Text>
                <Text>{userProfile.email}</Text>
              </HStack>
              <HStack space="md">
                <Text className="font-medium">Role:</Text>
                <Text>{userProfile.user_type}</Text>
              </HStack>
            </VStack>
          </CardBody>
        </Card>
      )}

      {dashboardData && (
        <Card>
          <CardHeader>
            <Heading size="lg">Dashboard Info</Heading>
          </CardHeader>
          <CardBody>
            <VStack space="md">
              {dashboardData.stats && Object.entries(dashboardData.stats).map(([key, value]: [string, any]) => (
                <HStack key={key} space="md">
                  <Text className="font-medium capitalize">{key.replace('_', ' ')}:</Text>
                  <Text>{value}</Text>
                </HStack>
              ))}
            </VStack>
          </CardBody>
        </Card>
      )}
    </VStack>
  );
} 