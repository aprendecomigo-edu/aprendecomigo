/**
 * Dependency Injection Public API
 *
 * This file exports all the public interfaces and utilities for the DI system.
 */

// ==================== Type Exports ====================
export type {
  Dependencies,
  MockDependencies,
  PartialDependencies,
  ServiceGateway,
  AuthApiService,
  StorageService,
  AnalyticsService,
  RouterService,
  ToastService,
  AuthContextService,
  OnboardingApiService,
  DependencyKey,
  DependencyService,
  DependencyOverrides,
} from './types';

// ==================== Context and Provider Exports ====================
export {
  DependencyContext,
  DependencyProvider,
  useDependencies,
  createDefaultDependencies,
} from './context';

// ==================== Default Implementation Exports ====================
export { createDefaultDependencies as createDefaults } from './defaults';

// ==================== Testing Utility Exports ====================
export {
  createMockDependencies,
  createPartialMockDependencies,
  withMockDependencies,
  MockDependencyBuilder,
  TestDependencyProvider,
  createTestDependencyProvider,
  createMockDependencyProvider,
  setupTestDependencies,
  createAuthScenarioMocks,
  createNetworkErrorScenario,
  mockDependenciesBeforeEach,
  isMockFunction,
  assertMockCalled,
  assertMockCalledWith,
  createAsyncTestScenario,
  createCombinedServiceScenario,
} from './testing';

// Note: createDefaultDependencies is already exported from context.tsx
