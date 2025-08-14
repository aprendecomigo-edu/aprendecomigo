/**
 * API Gateway
 * Central point for accessing all API services with dependency injection
 * This replaces the scattered import pattern with a centralized gateway
 */

import { ApiClient } from '../client/ApiClient';
import { AuthApiService } from '../services/AuthApiService';
import { BalanceApiService } from '../services/BalanceApiService';
import { NotificationApiService } from '../services/NotificationApiService';
import { PaymentApiService } from '../services/PaymentApiService';
import { TasksApiService } from '../services/TasksApiService';
import { UserApiService } from '../services/UserApiService';

/**
 * Interface defining all available API services
 */
export interface ApiGateway {
  auth: AuthApiService;
  payment: PaymentApiService;
  balance: BalanceApiService;
  user: UserApiService;
  tasks: TasksApiService;
  notification: NotificationApiService;
}

/**
 * Implementation of the API Gateway
 * Creates and manages service instances with injected ApiClient
 */
export class ApiGatewayImpl implements ApiGateway {
  public readonly auth: AuthApiService;
  public readonly payment: PaymentApiService;
  public readonly balance: BalanceApiService;
  public readonly user: UserApiService;
  public readonly tasks: TasksApiService;
  public readonly notification: NotificationApiService;

  constructor(apiClient: ApiClient) {
    // Initialize all services with the injected ApiClient
    this.auth = new AuthApiService(apiClient);
    this.payment = new PaymentApiService(apiClient);
    this.balance = new BalanceApiService(apiClient);
    this.user = new UserApiService(apiClient);
    this.tasks = new TasksApiService(apiClient);
    this.notification = new NotificationApiService(apiClient);
  }
}
