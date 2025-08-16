/**
 * Comprehensive tests for the new API Gateway pattern
 * Tests the centralized API service management with dependency injection
 *
 * These tests will initially FAIL since the implementation doesn't exist yet.
 * They serve as the specification for the API Gateway pattern described in issue #176.
 */

import { ApiClient } from '../client/ApiClient';

import { ApiGateway, ApiGatewayImpl } from './index';

// Mock the ApiClient
jest.mock('../client/ApiClient');

// Mock individual service classes (these will be created as part of the refactor)
jest.mock('../services/AuthApiService');
jest.mock('../services/PaymentApiService');
jest.mock('../services/BalanceApiService');
jest.mock('../services/UserApiService');
jest.mock('../services/TasksApiService');
jest.mock('../services/NotificationApiService');

// Import mocked classes
import { AuthApiService } from '../services/AuthApiService';
import { BalanceApiService } from '../services/BalanceApiService';
import { NotificationApiService } from '../services/NotificationApiService';
import { PaymentApiService } from '../services/PaymentApiService';
import { TasksApiService } from '../services/TasksApiService';
import { UserApiService } from '../services/UserApiService';

const MockedApiClient = ApiClient as jest.MockedClass<typeof ApiClient>;
const MockedAuthApiService = AuthApiService as jest.MockedClass<typeof AuthApiService>;
const MockedPaymentApiService = PaymentApiService as jest.MockedClass<typeof PaymentApiService>;
const MockedBalanceApiService = BalanceApiService as jest.MockedClass<typeof BalanceApiService>;
const MockedUserApiService = UserApiService as jest.MockedClass<typeof UserApiService>;
const MockedTasksApiService = TasksApiService as jest.MockedClass<typeof TasksApiService>;
const MockedNotificationApiService = NotificationApiService as jest.MockedClass<
  typeof NotificationApiService
>;

describe('ApiGateway', () => {
  let mockApiClient: jest.Mocked<ApiClient>;
  let mockAuthService: jest.Mocked<AuthApiService>;
  let mockPaymentService: jest.Mocked<PaymentApiService>;
  let mockBalanceService: jest.Mocked<BalanceApiService>;
  let mockUserService: jest.Mocked<UserApiService>;
  let mockTasksService: jest.Mocked<TasksApiService>;
  let mockNotificationService: jest.Mocked<NotificationApiService>;

  beforeEach(() => {
    jest.clearAllMocks();

    // Mock ApiClient instance
    mockApiClient = {
      get: jest.fn(),
      post: jest.fn(),
      put: jest.fn(),
      patch: jest.fn(),
      delete: jest.fn(),
    } as any;

    MockedApiClient.mockImplementation(() => mockApiClient);

    // Mock service instances
    mockAuthService = {
      requestEmailCode: jest.fn(),
      verifyEmailCode: jest.fn(),
      createUser: jest.fn(),
    } as any;
    MockedAuthApiService.mockImplementation(() => mockAuthService);

    mockPaymentService = {
      createPaymentMethod: jest.fn(),
      getPaymentMethods: jest.fn(),
      processPayment: jest.fn(),
    } as any;
    MockedPaymentApiService.mockImplementation(() => mockPaymentService);

    mockBalanceService = {
      getBalance: jest.fn(),
      getTransactions: jest.fn(),
    } as any;
    MockedBalanceApiService.mockImplementation(() => mockBalanceService);

    mockUserService = {
      getUserProfile: jest.fn(),
      updateUserProfile: jest.fn(),
    } as any;
    MockedUserApiService.mockImplementation(() => mockUserService);

    mockTasksService = {
      getTasks: jest.fn(),
      createTask: jest.fn(),
      updateTask: jest.fn(),
      deleteTask: jest.fn(),
    } as any;
    MockedTasksApiService.mockImplementation(() => mockTasksService);

    mockNotificationService = {
      getNotifications: jest.fn(),
      markAsRead: jest.fn(),
    } as any;
    MockedNotificationApiService.mockImplementation(() => mockNotificationService);
  });

  describe('ApiGatewayImpl Construction', () => {
    it('should create gateway with all service instances', () => {
      // This test will FAIL initially - no ApiGatewayImpl class exists yet
      const gateway = new ApiGatewayImpl(mockApiClient);

      expect(gateway).toBeInstanceOf(ApiGatewayImpl);
      expect(gateway.auth).toBeDefined();
      expect(gateway.payment).toBeDefined();
      expect(gateway.balance).toBeDefined();
      expect(gateway.user).toBeDefined();
      expect(gateway.tasks).toBeDefined();
      expect(gateway.notification).toBeDefined();
    });

    it('should pass ApiClient instance to all service constructors', () => {
      new ApiGatewayImpl(mockApiClient);

      expect(MockedAuthApiService).toHaveBeenCalledWith(mockApiClient);
      expect(MockedPaymentApiService).toHaveBeenCalledWith(mockApiClient);
      expect(MockedBalanceApiService).toHaveBeenCalledWith(mockApiClient);
      expect(MockedUserApiService).toHaveBeenCalledWith(mockApiClient);
      expect(MockedTasksApiService).toHaveBeenCalledWith(mockApiClient);
      expect(MockedNotificationApiService).toHaveBeenCalledWith(mockApiClient);
    });

    it('should implement the ApiGateway interface', () => {
      const gateway: ApiGateway = new ApiGatewayImpl(mockApiClient);

      expect(gateway.auth).toBeDefined();
      expect(gateway.payment).toBeDefined();
      expect(gateway.balance).toBeDefined();
      expect(gateway.user).toBeDefined();
      expect(gateway.tasks).toBeDefined();
      expect(gateway.notification).toBeDefined();
    });
  });

  describe('Service Integration', () => {
    let gateway: ApiGatewayImpl;

    beforeEach(() => {
      gateway = new ApiGatewayImpl(mockApiClient);
    });

    describe('Auth Service Integration', () => {
      it('should delegate auth operations to AuthApiService', async () => {
        const emailParams = { email: 'test@example.com' };
        const expectedResponse = { success: true };

        mockAuthService.requestEmailCode.mockResolvedValue(expectedResponse);

        const result = await gateway.auth.requestEmailCode(emailParams);

        expect(mockAuthService.requestEmailCode).toHaveBeenCalledWith(emailParams);
        expect(result).toBe(expectedResponse);
      });

      it('should handle verification through auth service', async () => {
        const verifyParams = { email: 'test@example.com', code: '123456' };
        const expectedResponse = { token: 'jwt-token', user: { id: 1 } };

        mockAuthService.verifyEmailCode.mockResolvedValue(expectedResponse);

        const result = await gateway.auth.verifyEmailCode(verifyParams);

        expect(mockAuthService.verifyEmailCode).toHaveBeenCalledWith(verifyParams);
        expect(result).toBe(expectedResponse);
      });

      it('should handle user creation through auth service', async () => {
        const createUserParams = { name: 'John Doe', email: 'john@example.com' };
        const expectedResponse = { user: { id: 1, name: 'John Doe' } };

        mockAuthService.createUser.mockResolvedValue(expectedResponse);

        const result = await gateway.auth.createUser(createUserParams);

        expect(mockAuthService.createUser).toHaveBeenCalledWith(createUserParams);
        expect(result).toBe(expectedResponse);
      });
    });

    describe('Payment Service Integration', () => {
      it('should delegate payment operations to PaymentApiService', async () => {
        const paymentData = { amount: 100, currency: 'USD' };
        const expectedResponse = { paymentId: 'pay_123' };

        mockPaymentService.processPayment.mockResolvedValue(expectedResponse);

        const result = await gateway.payment.processPayment(paymentData);

        expect(mockPaymentService.processPayment).toHaveBeenCalledWith(paymentData);
        expect(result).toBe(expectedResponse);
      });

      it('should handle payment method management', async () => {
        const expectedMethods = [{ id: '1', type: 'card' }];

        mockPaymentService.getPaymentMethods.mockResolvedValue(expectedMethods);

        const result = await gateway.payment.getPaymentMethods();

        expect(mockPaymentService.getPaymentMethods).toHaveBeenCalled();
        expect(result).toBe(expectedMethods);
      });
    });

    describe('User Service Integration', () => {
      it('should delegate user profile operations to UserApiService', async () => {
        const expectedProfile = { id: 1, name: 'John Doe', email: 'john@example.com' };

        mockUserService.getUserProfile.mockResolvedValue(expectedProfile);

        const result = await gateway.user.getUserProfile();

        expect(mockUserService.getUserProfile).toHaveBeenCalled();
        expect(result).toBe(expectedProfile);
      });

      it('should handle profile updates', async () => {
        const updateData = { name: 'Jane Doe' };
        const expectedResponse = { success: true };

        mockUserService.updateUserProfile.mockResolvedValue(expectedResponse);

        const result = await gateway.user.updateUserProfile(updateData);

        expect(mockUserService.updateUserProfile).toHaveBeenCalledWith(updateData);
        expect(result).toBe(expectedResponse);
      });
    });

    describe('Tasks Service Integration', () => {
      it('should delegate task operations to TasksApiService', async () => {
        const expectedTasks = [{ id: 1, title: 'Test Task' }];

        mockTasksService.getTasks.mockResolvedValue(expectedTasks);

        const result = await gateway.tasks.getTasks();

        expect(mockTasksService.getTasks).toHaveBeenCalled();
        expect(result).toBe(expectedTasks);
      });

      it('should handle task creation', async () => {
        const taskData = { title: 'New Task', description: 'Task description' };
        const expectedResponse = { id: 1, ...taskData };

        mockTasksService.createTask.mockResolvedValue(expectedResponse);

        const result = await gateway.tasks.createTask(taskData);

        expect(mockTasksService.createTask).toHaveBeenCalledWith(taskData);
        expect(result).toBe(expectedResponse);
      });
    });
  });

  describe('No Global State Guarantees', () => {
    it('should allow multiple gateway instances with different clients', () => {
      const mockApiClient2 = {
        get: jest.fn(),
        post: jest.fn(),
        put: jest.fn(),
        patch: jest.fn(),
        delete: jest.fn(),
      } as any;

      const gateway1 = new ApiGatewayImpl(mockApiClient);
      const gateway2 = new ApiGatewayImpl(mockApiClient2);

      expect(gateway1).not.toBe(gateway2);

      // Verify different clients were passed to service constructors
      expect(MockedAuthApiService).toHaveBeenCalledTimes(2);
      expect(MockedAuthApiService).toHaveBeenNthCalledWith(1, mockApiClient);
      expect(MockedAuthApiService).toHaveBeenNthCalledWith(2, mockApiClient2);
    });

    it('should isolate service calls between gateway instances', async () => {
      const mockApiClient2 = {
        get: jest.fn(),
        post: jest.fn(),
        put: jest.fn(),
        patch: jest.fn(),
        delete: jest.fn(),
      } as any;

      // Create separate service mocks for the second gateway
      const mockAuthService2 = {
        requestEmailCode: jest.fn(),
        verifyEmailCode: jest.fn(),
        createUser: jest.fn(),
      } as any;

      // Mock the constructor to return different instances based on call count
      let callCount = 0;
      MockedAuthApiService.mockImplementation(() => {
        callCount++;
        return callCount === 1 ? mockAuthService : mockAuthService2;
      });

      const gateway1 = new ApiGatewayImpl(mockApiClient);
      const gateway2 = new ApiGatewayImpl(mockApiClient2);

      const params1 = { email: 'user1@example.com' };
      const params2 = { email: 'user2@example.com' };

      mockAuthService.requestEmailCode.mockResolvedValue({ success: true });
      mockAuthService2.requestEmailCode.mockResolvedValue({ success: true });

      await Promise.all([
        gateway1.auth.requestEmailCode(params1),
        gateway2.auth.requestEmailCode(params2),
      ]);

      expect(mockAuthService.requestEmailCode).toHaveBeenCalledWith(params1);
      expect(mockAuthService2.requestEmailCode).toHaveBeenCalledWith(params2);
    });
  });

  describe('Error Propagation', () => {
    let gateway: ApiGatewayImpl;

    beforeEach(() => {
      gateway = new ApiGatewayImpl(mockApiClient);
    });

    it('should propagate errors from auth service', async () => {
      const error = new Error('Auth service error');
      mockAuthService.requestEmailCode.mockRejectedValue(error);

      await expect(gateway.auth.requestEmailCode({ email: 'test@example.com' })).rejects.toThrow(
        'Auth service error',
      );
    });

    it('should propagate errors from payment service', async () => {
      const error = new Error('Payment service error');
      mockPaymentService.processPayment.mockRejectedValue(error);

      await expect(gateway.payment.processPayment({ amount: 100 })).rejects.toThrow(
        'Payment service error',
      );
    });

    it('should not affect other services when one service fails', async () => {
      mockAuthService.requestEmailCode.mockRejectedValue(new Error('Auth error'));
      mockUserService.getUserProfile.mockResolvedValue({ id: 1, name: 'John' });

      const authPromise = gateway.auth
        .requestEmailCode({ email: 'test@example.com' })
        .catch(error => error.message);
      const userPromise = gateway.user.getUserProfile();

      const [authResult, userResult] = await Promise.all([authPromise, userPromise]);

      expect(authResult).toBe('Auth error');
      expect(userResult).toEqual({ id: 1, name: 'John' });
    });
  });

  describe('Type Safety', () => {
    it('should satisfy ApiGateway interface contract', () => {
      const gateway: ApiGateway = new ApiGatewayImpl(mockApiClient);

      // TypeScript compilation should verify these properties exist
      expect(typeof gateway.auth.requestEmailCode).toBe('function');
      expect(typeof gateway.auth.verifyEmailCode).toBe('function');
      expect(typeof gateway.auth.createUser).toBe('function');

      expect(typeof gateway.payment.processPayment).toBe('function');
      expect(typeof gateway.payment.getPaymentMethods).toBe('function');

      expect(typeof gateway.user.getUserProfile).toBe('function');
      expect(typeof gateway.user.updateUserProfile).toBe('function');

      expect(typeof gateway.tasks.getTasks).toBe('function');
      expect(typeof gateway.tasks.createTask).toBe('function');
    });
  });

  describe('Parallel Test Execution Compatibility', () => {
    it('should handle parallel operations across different gateway instances', async () => {
      const mockApiClient2 = {
        get: jest.fn(),
        post: jest.fn(),
        put: jest.fn(),
        patch: jest.fn(),
        delete: jest.fn(),
      } as any;

      const gateway1 = new ApiGatewayImpl(mockApiClient);
      const gateway2 = new ApiGatewayImpl(mockApiClient2);

      // Setup different responses for each gateway's services
      mockAuthService.requestEmailCode.mockResolvedValue({ gateway: 1 });

      const mockAuthService2 = {
        requestEmailCode: jest.fn().mockResolvedValue({ gateway: 2 }),
        verifyEmailCode: jest.fn(),
        createUser: jest.fn(),
      } as any;

      // Mock to return different instances
      let instanceCount = 0;
      MockedAuthApiService.mockImplementation(() => {
        instanceCount++;
        return instanceCount <= 1 ? mockAuthService : mockAuthService2;
      });

      // Reset and recreate gateways to apply the new mock
      const freshGateway1 = new ApiGatewayImpl(mockApiClient);
      const freshGateway2 = new ApiGatewayImpl(mockApiClient2);

      const operations = [
        freshGateway1.auth.requestEmailCode({ email: 'user1@test.com' }),
        freshGateway2.auth.requestEmailCode({ email: 'user2@test.com' }),
        freshGateway1.auth.requestEmailCode({ email: 'user3@test.com' }),
        freshGateway2.auth.requestEmailCode({ email: 'user4@test.com' }),
      ];

      const results = await Promise.all(operations);

      expect(results).toHaveLength(4);
      // Each gateway should maintain its own state and service instances
      expect(MockedAuthApiService).toHaveBeenCalledWith(mockApiClient);
      expect(MockedAuthApiService).toHaveBeenCalledWith(mockApiClient2);
    });

    it('should prevent cross-contamination between test instances', () => {
      // This test ensures that gateway instances don't share state
      const gateway1 = new ApiGatewayImpl(mockApiClient);

      const mockApiClient2 = {
        get: jest.fn(),
        post: jest.fn(),
        put: jest.fn(),
        patch: jest.fn(),
        delete: jest.fn(),
      } as any;

      const gateway2 = new ApiGatewayImpl(mockApiClient2);

      // Verify instances are separate
      expect(gateway1).not.toBe(gateway2);

      // Verify service constructors were called with different clients
      expect(MockedAuthApiService).toHaveBeenCalledWith(mockApiClient);
      expect(MockedAuthApiService).toHaveBeenCalledWith(mockApiClient2);
    });
  });
});
