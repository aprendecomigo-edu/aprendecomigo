/**
 * Dependency Injection Context and Provider
 * 
 * This file implements the React context and provider for dependency injection.
 * It provides a way to inject dependencies into React components through context.
 */

import React, { createContext, useContext, ReactNode } from 'react';
import { Dependencies } from './types';

// ==================== Context Creation ====================

export const DependencyContext = createContext<Dependencies | undefined>(undefined);

// ==================== Provider Props ====================

interface DependencyProviderProps {
  children: ReactNode;
  dependencies: Dependencies;
}

// ==================== Dependency Provider Component ====================

export const DependencyProvider: React.FC<DependencyProviderProps> = ({
  children,
  dependencies,
}) => {
  // Validate that all required dependencies are provided
  const validateDependencies = (deps: Dependencies) => {
    const requiredServices: (keyof Dependencies)[] = [
      'authApi',
      'storageService',
      'analyticsService',
      'routerService',
      'toastService',
      'authContextService',
      'onboardingApiService',
      'paymentService',
      'balanceService',
    ];

    const missingServices = requiredServices.filter(service => !deps[service]);
    
    if (missingServices.length > 0) {
      throw new Error(`Missing required dependencies: ${missingServices.join(', ')}`);
    }
  };

  validateDependencies(dependencies);

  return (
    <DependencyContext.Provider value={dependencies}>
      {children}
    </DependencyContext.Provider>
  );
};

// ==================== useDependencies Hook ====================

export const useDependencies = (): Dependencies => {
  const context = useContext(DependencyContext);
  
  if (context === undefined) {
    throw new Error('useDependencies must be used within a DependencyProvider');
  }
  
  return context;
};

// ==================== createDefaultDependencies Function ====================

// This is declared here but implemented in defaults.ts to avoid circular dependencies
export { createDefaultDependencies } from './defaults';