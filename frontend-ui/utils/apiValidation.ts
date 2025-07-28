// API Request Validation Utilities
// Provides client-side validation for API requests to prevent sending invalid data

export interface ValidationResult {
  isValid: boolean;
  errors: string[];
}

export class ApiValidator {
  static validateStudentData(data: any): ValidationResult {
    const errors: string[] = [];

    // Required fields validation
    if (!data.name || typeof data.name !== 'string' || data.name.trim().length === 0) {
      errors.push('Nome é obrigatório');
    } else if (data.name.trim().length < 2 || data.name.trim().length > 100) {
      errors.push('Nome deve ter entre 2 e 100 caracteres');
    }

    if (!data.email || typeof data.email !== 'string' || data.email.trim().length === 0) {
      errors.push('Email é obrigatório');
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.email.trim())) {
      errors.push('Formato de email inválido');
    } else if (data.email.trim().length > 254) {
      errors.push('Email muito longo');
    }

    if (!data.phone_number || typeof data.phone_number !== 'string' || data.phone_number.trim().length === 0) {
      errors.push('Telefone é obrigatório');
    } else if (!/^[\+]?[0-9\s\-\(\)]{8,20}$/.test(data.phone_number.trim())) {
      errors.push('Formato de telefone inválido');
    }

    if (!data.school_year || typeof data.school_year !== 'string') {
      errors.push('Ano escolar é obrigatório');
    }

    if (!data.birth_date || typeof data.birth_date !== 'string') {
      errors.push('Data de nascimento é obrigatória');
    } else if (!/^\d{4}-\d{2}-\d{2}$/.test(data.birth_date)) {
      errors.push('Formato de data inválido (AAAA-MM-DD)');
    } else {
      const birthDate = new Date(data.birth_date);
      const today = new Date();
      const age = today.getFullYear() - birthDate.getFullYear();
      
      if (birthDate > today) {
        errors.push('Data de nascimento não pode ser no futuro');
      } else if (age < 5 || age > 25) {
        errors.push('Idade deve estar entre 5 e 25 anos');
      }
    }

    if (!data.school_id || typeof data.school_id !== 'number' || data.school_id <= 0) {
      errors.push('ID da escola é obrigatório');
    }

    if (!data.educational_system_id || typeof data.educational_system_id !== 'number' || data.educational_system_id <= 0) {
      errors.push('Sistema educacional é obrigatório');
    }

    // Optional fields validation
    if (data.address && (typeof data.address !== 'string' || data.address.length > 500)) {
      errors.push('Endereço deve ter no máximo 500 caracteres');
    }

    if (data.primary_contact && !['email', 'phone'].includes(data.primary_contact)) {
      errors.push('Tipo de contato primário inválido');
    }

    return {
      isValid: errors.length === 0,
      errors
    };
  }

  static validateStudentFilters(filters: any): ValidationResult {
    const errors: string[] = [];

    if (filters.page && (typeof filters.page !== 'number' || filters.page < 1)) {
      errors.push('Número da página deve ser maior que 0');
    }

    if (filters.page_size && (typeof filters.page_size !== 'number' || filters.page_size < 1 || filters.page_size > 100)) {
      errors.push('Tamanho da página deve estar entre 1 e 100');
    }

    if (filters.search && (typeof filters.search !== 'string' || filters.search.length > 255)) {
      errors.push('Termo de busca deve ter no máximo 255 caracteres');
    }

    if (filters.status && !['active', 'inactive', 'graduated'].includes(filters.status)) {
      errors.push('Status inválido');
    }

    if (filters.educational_system && (typeof filters.educational_system !== 'number' || filters.educational_system <= 0)) {
      errors.push('ID do sistema educacional inválido');
    }

    if (filters.school_year && typeof filters.school_year !== 'string') {
      errors.push('Ano escolar deve ser uma string');
    }

    return {
      isValid: errors.length === 0,
      errors
    };
  }

  static validateStudentStatusUpdate(id: number, status: string): ValidationResult {
    const errors: string[] = [];

    if (!id || typeof id !== 'number' || id <= 0) {
      errors.push('ID do aluno é obrigatório');
    }

    if (!status || !['active', 'inactive', 'graduated'].includes(status)) {
      errors.push('Status deve ser: active, inactive ou graduated');
    }

    return {
      isValid: errors.length === 0,
      errors
    };
  }

  static sanitizeInput(input: string): string {
    if (typeof input !== 'string') return '';
    return input.trim().replace(/<[^>]*>/g, ''); // Remove HTML tags and trim
  }

  static sanitizeStudentData(data: any): any {
    return {
      ...data,
      name: this.sanitizeInput(data.name || ''),
      email: this.sanitizeInput((data.email || '').toLowerCase()),
      phone_number: this.sanitizeInput(data.phone_number || ''),
      address: this.sanitizeInput(data.address || ''),
      birth_date: (data.birth_date || '').trim(),
      school_year: (data.school_year || '').trim(),
    };
  }
}

// Higher-order function to wrap API calls with validation
export function withValidation<T extends any[], R>(
  apiFunction: (...args: T) => Promise<R>,
  validator: (...args: T) => ValidationResult
) {
  return async (...args: T): Promise<R> => {
    const validation = validator(...args);
    
    if (!validation.isValid) {
      throw new Error(`Dados inválidos: ${validation.errors.join(', ')}`);
    }

    return apiFunction(...args);
  };
}

export default ApiValidator;