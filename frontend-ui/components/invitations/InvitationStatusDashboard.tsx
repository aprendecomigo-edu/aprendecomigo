import { RefreshCw, Search, Filter, Plus } from 'lucide-react-native';
import React, { useState, useEffect } from 'react';
import { RefreshControl, FlatList } from 'react-native';

import { useInvitations, useInvitationPolling } from '@/hooks/useInvitations';
import { InvitationStatus, SchoolRole } from '@/api/invitationApi';

import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Center } from '@/components/ui/center';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Input, InputField } from '@/components/ui/input';
import { Spinner } from '@/components/ui/spinner';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

import { InvitationListItem } from './InvitationListItem';
import { InvitationFilters } from './InvitationFilters';

interface InvitationStatusDashboardProps {
  onInvitePress?: () => void;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

export const InvitationStatusDashboard: React.FC<InvitationStatusDashboardProps> = ({
  onInvitePress,
  autoRefresh = false,
  refreshInterval = 30000, // 30 seconds
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<{
    status?: InvitationStatus;
    role?: SchoolRole;
    ordering?: string;
  }>({});

  const {
    invitations,
    loading,
    error,
    pagination,
    fetchInvitations,
    refreshInvitations,
  } = useInvitations();

  const { isPolling, startPolling, stopPolling } = useInvitationPolling(
    refreshInvitations,
    refreshInterval
  );

  // Start/stop polling based on autoRefresh prop
  useEffect(() => {
    if (autoRefresh) {
      const cleanup = startPolling();
      return cleanup;
    } else {
      stopPolling();
    }
  }, [autoRefresh, startPolling, stopPolling]);

  const handleSearch = () => {
    fetchInvitations({
      ...filters,
      email: searchQuery.trim() || undefined,
    });
  };

  const handleFilterChange = (newFilters: typeof filters) => {
    setFilters(newFilters);
    fetchInvitations({
      ...newFilters,
      email: searchQuery.trim() || undefined,
    });
  };

  const handleClearFilters = () => {
    setFilters({});
    setSearchQuery('');
    fetchInvitations();
  };

  const handleLoadMore = () => {
    if (pagination.next && !loading) {
      fetchInvitations({
        ...filters,
        email: searchQuery.trim() || undefined,
        page: pagination.currentPage + 1,
      });
    }
  };

  const getStatsData = () => {
    const statusCounts = invitations.reduce((acc, invitation) => {
      acc[invitation.status] = (acc[invitation.status] || 0) + 1;
      return acc;
    }, {} as Record<InvitationStatus, number>);

    return [
      {
        label: 'Total',
        value: pagination.count,
        color: '#6B7280',
      },
      {
        label: 'Pendentes',
        value: statusCounts[InvitationStatus.PENDING] || 0,
        color: '#F59E0B',
      },
      {
        label: 'Enviados',
        value: (statusCounts[InvitationStatus.SENT] || 0) + 
               (statusCounts[InvitationStatus.DELIVERED] || 0) + 
               (statusCounts[InvitationStatus.VIEWED] || 0),
        color: '#3B82F6',
      },
      {
        label: 'Aceitos',
        value: statusCounts[InvitationStatus.ACCEPTED] || 0,
        color: '#10B981',
      },
      {
        label: 'Expirados',
        value: (statusCounts[InvitationStatus.EXPIRED] || 0) + 
               (statusCounts[InvitationStatus.CANCELLED] || 0) + 
               (statusCounts[InvitationStatus.DECLINED] || 0),
        color: '#EF4444',
      },
    ];
  };

  const renderHeader = () => (
    <VStack space="lg" className="mb-6">
      {/* Title and Actions */}
      <HStack className="justify-between items-center">
        <VStack>
          <Heading size="xl">Convites de Professores</Heading>
          <Text className="text-gray-600">
            Gerencie convites e acompanhe o status
          </Text>
        </VStack>
        
        <HStack space="sm">
          <Button
            variant="outline"
            size="sm"
            onPress={refreshInvitations}
            disabled={loading}
          >
            <Icon as={RefreshCw} size="sm" className={loading ? 'animate-spin' : ''} />
          </Button>
          
          {onInvitePress && (
            <Button size="sm" onPress={onInvitePress}>
              <HStack space="xs" className="items-center">
                <Icon as={Plus} size="sm" />
                <ButtonText>Convidar</ButtonText>
              </HStack>
            </Button>
          )}
        </HStack>
      </HStack>

      {/* Stats Cards */}
      <HStack space="md" className="flex-wrap">
        {getStatsData().map((stat, index) => (
          <Box
            key={index}
            className="flex-1 min-w-[80px] p-3 bg-white rounded-lg border"
            style={{ borderLeftWidth: 3, borderLeftColor: stat.color }}
          >
            <VStack space="xs">
              <Text className="text-2xl font-bold" style={{ color: stat.color }}>
                {stat.value}
              </Text>
              <Text className="text-xs text-gray-600">{stat.label}</Text>
            </VStack>
          </Box>
        ))}
      </HStack>

      {/* Search and Filters */}
      <VStack space="sm">
        <HStack space="sm">
          <Box className="flex-1">
            <Input>
              <InputField
                placeholder="Buscar por email..."
                value={searchQuery}
                onChangeText={setSearchQuery}
                onSubmitEditing={handleSearch}
                returnKeyType="search"
              />
            </Input>
          </Box>
          <Button variant="outline" onPress={handleSearch} disabled={loading}>
            <Icon as={Search} size="sm" />
          </Button>
          <Button
            variant="outline"
            onPress={() => setShowFilters(!showFilters)}
          >
            <Icon as={Filter} size="sm" />
          </Button>
        </HStack>

        {/* Polling indicator */}
        {autoRefresh && isPolling && (
          <Box className="p-2 bg-blue-50 rounded border border-blue-200">
            <HStack space="xs" className="items-center">
              <Spinner size="small" />
              <Text className="text-xs text-blue-600">
                Atualizando automaticamente a cada {refreshInterval / 1000}s
              </Text>
            </HStack>
          </Box>
        )}
      </VStack>

      {/* Filters Component */}
      {showFilters && (
        <InvitationFilters
          filters={filters}
          onFiltersChange={handleFilterChange}
          onClearFilters={handleClearFilters}
        />
      )}
    </VStack>
  );

  const renderInvitation = ({ item, index }: { item: any; index: number }) => (
    <InvitationListItem
      invitation={item}
      onAction={refreshInvitations}
      isLast={index === invitations.length - 1}
    />
  );

  const renderFooter = () => {
    if (!loading) return null;
    
    return (
      <Box className="py-4">
        <Center>
          <Spinner size="small" />
        </Center>
      </Box>
    );
  };

  const renderEmpty = () => (
    <Center className="py-12">
      <VStack space="md" className="items-center">
        <Icon as={Search} size="xl" className="text-gray-400" />
        <VStack space="xs" className="items-center">
          <Text className="text-lg font-medium text-gray-900">
            Nenhum convite encontrado
          </Text>
          <Text className="text-gray-600 text-center">
            {searchQuery || Object.keys(filters).length > 0
              ? 'Tente ajustar os filtros de busca'
              : 'Comece convidando professores para sua escola'
            }
          </Text>
        </VStack>
        {(searchQuery || Object.keys(filters).length > 0) && (
          <Button variant="outline" onPress={handleClearFilters}>
            <ButtonText>Limpar filtros</ButtonText>
          </Button>
        )}
      </VStack>
    </Center>
  );

  if (error) {
    return (
      <Box className="p-4">
        <Center>
          <VStack space="md" className="items-center">
            <Text className="text-red-600 text-center">{error}</Text>
            <Button variant="outline" onPress={refreshInvitations}>
              <ButtonText>Tentar novamente</ButtonText>
            </Button>
          </VStack>
        </Center>
      </Box>
    );
  }

  return (
    <Box className="flex-1 bg-gray-50">
      <FlatList
        data={invitations}
        keyExtractor={(item) => item.id}
        renderItem={renderInvitation}
        ListHeaderComponent={renderHeader}
        ListEmptyComponent={!loading ? renderEmpty : null}
        ListFooterComponent={renderFooter}
        refreshControl={
          <RefreshControl
            refreshing={loading}
            onRefresh={refreshInvitations}
          />
        }
        onEndReached={handleLoadMore}
        onEndReachedThreshold={0.5}
        showsVerticalScrollIndicator={false}
        className="p-4"
      />
    </Box>
  );
};