import React from 'react';

import { Box } from '@/components/ui/box';
import { Card, CardBody, CardHeader } from '@/components/ui/card';
import { HStack } from '@/components/ui/hstack';
import { Skeleton } from '@/components/ui/skeleton';
import { VStack } from '@/components/ui/vstack';

interface DashboardSkeletonProps {
  view?: 'overview' | 'students' | 'analytics' | 'quick-actions';
}

const SkeletonCard: React.FC<{ children: React.ReactNode; className?: string }> = ({ 
  children, 
  className = "" 
}) => (
  <Card variant="elevated" className={`bg-white shadow-sm ${className}`}>
    {children}
  </Card>
);

const OverviewSkeleton: React.FC = () => (
  <VStack space="md">
    {/* Stats Overview */}
    <SkeletonCard>
      <CardHeader>
        <Skeleton className="h-6 w-32" />
      </CardHeader>
      <CardBody>
        <VStack space="md">
          <HStack space="lg" className="justify-around">
            {[1, 2, 3, 4].map(i => (
              <VStack key={i} className="items-center">
                <Skeleton className="h-8 w-12 rounded" />
                <Skeleton className="h-4 w-16 mt-1" />
              </VStack>
            ))}
          </HStack>
          <Skeleton className="h-12 w-full rounded-lg" />
        </VStack>
      </CardBody>
    </SkeletonCard>

    {/* Sessions */}
    <SkeletonCard>
      <CardHeader>
        <HStack className="justify-between items-center">
          <Skeleton className="h-6 w-32" />
          <Skeleton className="h-6 w-8 rounded-full" />
        </HStack>
      </CardHeader>
      <CardBody>
        <VStack space="sm">
          {[1, 2, 3].map(i => (
            <HStack key={i} space="sm" className="items-center py-2">
              <Skeleton className="w-12 h-12 rounded-lg" />
              <VStack className="flex-1" space="xs">
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-3 w-1/2" />
              </VStack>
              <Skeleton className="h-6 w-16 rounded-full" />
            </HStack>
          ))}
        </VStack>
      </CardBody>
    </SkeletonCard>

    {/* Quick Stats */}
    <SkeletonCard className="bg-gradient-to-r from-blue-500 to-purple-600">
      <CardBody>
        <VStack space="md">
          <Skeleton className="h-6 w-32 bg-blue-400" />
          <HStack space="lg" className="justify-around">
            {[1, 2, 3, 4].map(i => (
              <VStack key={i} className="items-center">
                <Skeleton className="h-8 w-12 bg-blue-400 rounded" />
                <Skeleton className="h-4 w-16 bg-blue-300 mt-1" />
              </VStack>
            ))}
          </HStack>
        </VStack>
      </CardBody>
    </SkeletonCard>
  </VStack>
);

const StudentsSkeleton: React.FC = () => (
  <VStack space="md">
    {/* Header */}
    <SkeletonCard>
      <CardHeader>
        <HStack className="justify-between items-center">
          <Skeleton className="h-6 w-40" />
          <Skeleton className="h-6 w-8 rounded-full" />
        </HStack>
      </CardHeader>
      <CardBody>
        <VStack space="md">
          {/* Stats */}
          <HStack space="lg" className="justify-around">
            {[1, 2, 3, 4].map(i => (
              <VStack key={i} className="items-center">
                <Skeleton className="h-6 w-8 rounded" />
                <Skeleton className="h-3 w-12 mt-1" />
              </VStack>
            ))}
          </HStack>

          {/* Search */}
          <HStack space="sm">
            <Skeleton className="flex-1 h-12 rounded-lg" />
            <Skeleton className="h-12 w-24 rounded-lg" />
          </HStack>
        </VStack>
      </CardBody>
    </SkeletonCard>

    {/* Student List */}
    <VStack space="sm">
      {[1, 2, 3, 4, 5].map(i => (
        <SkeletonCard key={i}>
          <CardBody>
            <VStack space="sm">
              <HStack space="md" className="items-start">
                <Skeleton className="w-12 h-12 rounded-full" />
                <VStack className="flex-1" space="xs">
                  <HStack className="justify-between items-start">
                    <VStack className="flex-1" space="xs">
                      <Skeleton className="h-4 w-3/4" />
                      <Skeleton className="h-3 w-1/2" />
                    </VStack>
                    <Skeleton className="h-6 w-16 rounded-full" />
                  </HStack>
                </VStack>
              </HStack>

              <VStack space="xs">
                <HStack className="justify-between">
                  <Skeleton className="h-3 w-20" />
                  <Skeleton className="h-3 w-12" />
                </HStack>
                <Skeleton className="h-2 w-full rounded-full" />
              </VStack>

              <HStack space="sm" className="pt-2">
                <Skeleton className="flex-1 h-8 rounded-lg" />
                <Skeleton className="flex-1 h-8 rounded-lg" />
                <Skeleton className="w-8 h-8 rounded" />
              </HStack>
            </VStack>
          </CardBody>
        </SkeletonCard>
      ))}
    </VStack>
  </VStack>
);

const AnalyticsSkeleton: React.FC = () => (
  <VStack space="md">
    {/* Performance Metrics */}
    <SkeletonCard>
      <CardHeader>
        <HStack className="justify-between items-center">
          <Skeleton className="h-6 w-40" />
          <Skeleton className="h-8 w-24 rounded-lg" />
        </HStack>
      </CardHeader>
      <CardBody>
        <VStack space="md">
          {/* Metrics Grid */}
          <VStack space="sm">
            <HStack space="sm">
              {[1, 2].map(i => (
                <Box key={i} className="flex-1">
                  <SkeletonCard>
                    <CardBody>
                      <VStack space="sm">
                        <HStack className="justify-between">
                          <Skeleton className="w-8 h-8 rounded-full" />
                          <Skeleton className="h-4 w-12" />
                        </HStack>
                        <VStack space="xs">
                          <Skeleton className="h-8 w-16" />
                          <Skeleton className="h-4 w-20" />
                        </VStack>
                      </VStack>
                    </CardBody>
                  </SkeletonCard>
                </Box>
              ))}
            </HStack>
            <HStack space="sm">
              {[1, 2].map(i => (
                <Box key={i} className="flex-1">
                  <SkeletonCard>
                    <CardBody>
                      <VStack space="sm">
                        <HStack className="justify-between">
                          <Skeleton className="w-8 h-8 rounded-full" />
                          <Skeleton className="h-4 w-12" />
                        </HStack>
                        <VStack space="xs">
                          <Skeleton className="h-8 w-16" />
                          <Skeleton className="h-4 w-20" />
                        </VStack>
                      </VStack>
                    </CardBody>
                  </SkeletonCard>
                </Box>
              ))}
            </HStack>
          </VStack>

          {/* Progress Bars */}
          <VStack space="sm">
            {[1, 2, 3].map(i => (
              <VStack key={i} space="xs">
                <HStack className="justify-between">
                  <Skeleton className="h-4 w-32" />
                  <Skeleton className="h-4 w-12" />
                </HStack>
                <Skeleton className="h-2 w-full rounded-full" />
                <HStack className="justify-between">
                  <Skeleton className="h-3 w-8" />
                  <Skeleton className="h-3 w-8" />
                </HStack>
              </VStack>
            ))}
          </VStack>
        </VStack>
      </CardBody>
    </SkeletonCard>

    {/* Earnings */}
    <SkeletonCard>
      <CardHeader>
        <HStack className="justify-between items-center">
          <Skeleton className="h-6 w-24" />
          <Skeleton className="w-6 h-6 rounded" />
        </HStack>
      </CardHeader>
      <CardBody>
        <VStack space="md">
          <VStack space="sm">
            <HStack className="justify-between">
              <Skeleton className="h-4 w-20" />
              <Skeleton className="h-4 w-16" />
            </HStack>
            <Skeleton className="h-8 w-24" />
          </VStack>

          <VStack space="xs">
            {[1, 2, 3].map(i => (
              <HStack key={i} className="justify-between">
                <Skeleton className="h-4 w-24" />
                <Skeleton className="h-4 w-16" />
              </HStack>
            ))}
          </VStack>

          <VStack space="sm">
            <Skeleton className="h-4 w-32" />
            {[1, 2, 3].map(i => (
              <HStack key={i} className="justify-between items-center py-1">
                <VStack space="xs">
                  <Skeleton className="h-4 w-16" />
                  <Skeleton className="h-3 w-20" />
                </VStack>
                <VStack className="items-end" space="xs">
                  <Skeleton className="h-3 w-8" />
                  <Skeleton className="h-3 w-24" />
                </VStack>
              </HStack>
            ))}
          </VStack>
        </VStack>
      </CardBody>
    </SkeletonCard>

    {/* Performance Insights */}
    <SkeletonCard className="bg-gradient-to-r from-blue-50 to-purple-50 border-l-4 border-blue-500">
      <CardBody>
        <VStack space="sm">
          <HStack space="sm" className="items-center">
            <Skeleton className="w-6 h-6 rounded" />
            <Skeleton className="h-6 w-40" />
          </HStack>
          <VStack space="xs">
            {[1, 2, 3].map(i => (
              <HStack key={i} space="sm" className="items-center">
                <Skeleton className="w-4 h-4 rounded" />
                <Skeleton className="h-4 flex-1" />
              </HStack>
            ))}
          </VStack>
        </VStack>
      </CardBody>
    </SkeletonCard>
  </VStack>
);

const QuickActionsSkeleton: React.FC = () => (
  <VStack space="md">
    {/* Primary Actions */}
    <SkeletonCard>
      <CardHeader>
        <HStack className="justify-between items-center">
          <Skeleton className="h-6 w-32" />
          <Skeleton className="w-5 h-5 rounded" />
        </HStack>
      </CardHeader>
      <CardBody>
        <VStack space="sm">
          <HStack space="sm">
            <Skeleton className="flex-1 h-32 rounded-lg" />
            <VStack space="sm" className="flex-1">
              <Skeleton className="h-16 w-full rounded-lg" />
              <Skeleton className="h-16 w-full rounded-lg" />
            </VStack>
          </HStack>
          <Skeleton className="h-20 w-full rounded-lg" />
        </VStack>
      </CardBody>
    </SkeletonCard>

    {/* Secondary Actions */}
    <SkeletonCard>
      <CardHeader>
        <Skeleton className="h-6 w-40" />
      </CardHeader>
      <CardBody>
        <VStack space="sm">
          <HStack space="sm">
            {[1, 2].map(i => (
              <Skeleton key={i} className="flex-1 h-24 rounded-lg" />
            ))}
          </HStack>
          <HStack space="sm">
            {[1, 2].map(i => (
              <Skeleton key={i} className="flex-1 h-24 rounded-lg" />
            ))}
          </HStack>
        </VStack>
      </CardBody>
    </SkeletonCard>

    {/* Utility Actions */}
    <SkeletonCard>
      <CardHeader>
        <Skeleton className="h-6 w-32" />
      </CardHeader>
      <CardBody>
        <HStack space="sm">
          {[1, 2].map(i => (
            <Skeleton key={i} className="flex-1 h-24 rounded-lg" />
          ))}
        </HStack>
      </CardBody>
    </SkeletonCard>

    {/* Quick Tips */}
    <SkeletonCard className="bg-gradient-to-r from-blue-50 to-purple-50 border-2 border-dashed border-blue-200">
      <CardBody>
        <VStack space="sm" className="items-center">
          <Skeleton className="w-8 h-8 rounded" />
          <VStack space="xs" className="items-center">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-3 w-48" />
            <Skeleton className="h-3 w-32" />
          </VStack>
        </VStack>
      </CardBody>
    </SkeletonCard>
  </VStack>
);

const DashboardSkeleton: React.FC<DashboardSkeletonProps> = ({ view = 'overview' }) => {
  switch (view) {
    case 'students':
      return <StudentsSkeleton />;
    case 'analytics':
      return <AnalyticsSkeleton />;
    case 'quick-actions':
      return <QuickActionsSkeleton />;
    case 'overview':
    default:
      return <OverviewSkeleton />;
  }
};

export default DashboardSkeleton;