import React, { lazy, Suspense } from 'react';

import LoadingScreen from '@/components/ui/loading-screen';

// Lazy load heavy profile wizard steps
export const LazyAvailabilityStep = lazy(() => import('./AvailabilityStep'));
export const LazyBasicInfoStep = lazy(() => import('./BasicInfoStep'));
export const LazyEducationStep = lazy(() => import('./EducationStep'));
export const LazyRatesStep = lazy(() => import('./RatesStep'));
export const LazySubjectsStep = lazy(() => import('./SubjectsStep'));
export const LazyBiographyStep = lazy(() => import('./BiographyStep'));
export const LazyProfilePreviewStep = lazy(() => import('./ProfilePreviewStep'));

// Wrapper components with Suspense
export function AvailabilityStepWithSuspense(props: any) {
  return (
    <Suspense fallback={<LoadingScreen message="Loading availability settings..." />}>
      <LazyAvailabilityStep {...props} />
    </Suspense>
  );
}

export function BasicInfoStepWithSuspense(props: any) {
  return (
    <Suspense fallback={<LoadingScreen message="Loading basic information form..." />}>
      <LazyBasicInfoStep {...props} />
    </Suspense>
  );
}

export function EducationStepWithSuspense(props: any) {
  return (
    <Suspense fallback={<LoadingScreen message="Loading education form..." />}>
      <LazyEducationStep {...props} />
    </Suspense>
  );
}

export function RatesStepWithSuspense(props: any) {
  return (
    <Suspense fallback={<LoadingScreen message="Loading rates form..." />}>
      <LazyRatesStep {...props} />
    </Suspense>
  );
}

export function SubjectsStepWithSuspense(props: any) {
  return (
    <Suspense fallback={<LoadingScreen message="Loading subjects form..." />}>
      <LazySubjectsStep {...props} />
    </Suspense>
  );
}

export function BiographyStepWithSuspense(props: any) {
  return (
    <Suspense fallback={<LoadingScreen message="Loading biography form..." />}>
      <LazyBiographyStep {...props} />
    </Suspense>
  );
}

export function ProfilePreviewStepWithSuspense(props: any) {
  return (
    <Suspense fallback={<LoadingScreen message="Loading profile preview..." />}>
      <LazyProfilePreviewStep {...props} />
    </Suspense>
  );
}
