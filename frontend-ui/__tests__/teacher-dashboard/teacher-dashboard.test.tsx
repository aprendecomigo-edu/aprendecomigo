import { jest } from '@jest/globals';
import { render, screen, fireEvent, waitFor } from '@testing-library/react-native';
import { router } from 'expo-router';
import React from 'react';

import { useAuth, useUserProfile } from '@/api/auth';
import TeacherDashboard from '@/app/(teacher)/dashboard/index';
import { useTeacherDashboard } from '@/hooks/useTeacherDashboard';

// Mock dependencies
jest.mock('expo-router', () => ({
  router: {
    push: jest.fn(),
    back: jest.fn(),
  },
}));

jest.mock('@/api/auth', () => ({
  useAuth: jest.fn(),
  useUserProfile: jest.fn(),
}));

jest.mock('@/hooks/useTeacherDashboard', () => ({
  useTeacherDashboard: jest.fn(),
}));

jest.mock('@gluestack-ui/nativewind-utils/IsWeb', () => ({
  isWeb: false,
}));

jest.mock('@/components/layouts/MainLayout', () => {
  return function MockMainLayout({ children, _title }: any) {
    return (
      <div data-testid="main-layout" data-title={_title}>
        {children}
      </div>
    );
  };
});

// Mock Gluestack UI components that might not be properly mocked
jest.mock('@/components/ui/badge', () => {
  const React = require('react');
  return {
    Badge: ({ children, ...props }: any) => React.createElement('div', { ...props, className: 'mock-badge' }, children),
    BadgeText: ({ children, ...props }: any) => React.createElement('span', { ...props, className: 'mock-badge-text' }, children),
  };
});

jest.mock('@/components/ui/card', () => {
  const React = require('react');
  return {
    Card: ({ children, ...props }: any) => React.createElement('div', { ...props, className: 'mock-card' }, children),
    CardBody: ({ children, ...props }: any) => React.createElement('div', { ...props, className: 'mock-card-body' }, children),
    CardHeader: ({ children, ...props }: any) => React.createElement('div', { ...props, className: 'mock-card-header' }, children),
  };
});

jest.mock('@/components/ui/input', () => {
  const React = require('react');
  return {
    Input: ({ children, ...props }: any) => React.createElement('div', { ...props, className: 'mock-input' }, children),
    InputField: React.forwardRef((props: any, ref) => React.createElement('input', { ...props, ref, className: 'mock-input-field' })),
  };
});

jest.mock('@/components/ui/icon', () => {
  const React = require('react');
  return {
    Icon: ({ children, ...props }: any) => React.createElement('div', { ...props, className: 'mock-icon' }, children || '📄'),
  };
});

const mockUserProfile = {
  id: 1,
  name: 'Professor João Silva',
  email: 'joao@escola.com',
};

const mockDashboardData = {
  teacher_info: {
    id: 1,
    name: 'Professor João Silva',
    email: 'joao@escola.com',
    specialty: 'Matemática',
    hourly_rate: 25.0,
    profile_completion_score: 85.0,
    schools: [
      {
        id: 1,
        name: 'Escola Primária Lisboa',
        joined_at: '2024-01-15T10:00:00Z',
      },
    ],
    courses_taught: [
      {
        id: 1,
        name: 'Matemática 6º Ano',
        code: 'MAT6',
        hourly_rate: 25.0,
      },
    ],
  },
  students: [
    {
      id: 1,
      name: 'Ana Costa',
      email: 'ana@estudante.com',
      current_level: '6º Ano',
      completion_percentage: 75.5,
      last_session_date: '2024-01-25T14:00:00Z',
      recent_assessments: [
        {
          id: 1,
          title: 'Quiz Frações',
          assessment_type: 'quiz',
          percentage: 85.0,
          assessment_date: '2024-01-24',
        },
      ],
      skills_mastered: ['Frações básicas', 'Decimais'],
    },
    {
      id: 2,
      name: 'Pedro Santos',
      email: 'pedro@estudante.com',
      current_level: '6º Ano',
      completion_percentage: 60.0,
      last_session_date: null,
      recent_assessments: [],
      skills_mastered: [],
    },
  ],
  sessions: {
    today: [
      {
        id: 1,
        date: new Date().toISOString().split('T')[0],
        start_time: '14:00:00',
        end_time: '15:00:00',
        session_type: 'individual',
        grade_level: '6º Ano',
        student_count: 1,
        student_names: ['Ana Costa'],
        status: 'scheduled',
        notes: '',
        duration_hours: 1.0,
      },
    ],
    upcoming: [],
    recent_completed: [],
  },
  progress_metrics: {
    average_student_progress: 67.75,
    total_assessments_given: 1,
    students_improved_this_month: 1,
    completion_rate_trend: 70.0,
  },
  recent_activities: [
    {
      id: '1',
      activity_type: 'session_completed',
      description: 'Sessão de matemática concluída com Ana Costa',
      timestamp: '2024-01-25T15:00:00Z',
      actor_name: 'Professor João Silva',
      school_name: 'Escola Primária Lisboa',
    },
  ],
  earnings: {
    current_month_total: 125.0,
    last_month_total: 200.0,
    pending_amount: 50.0,
    total_hours_taught: 13.0,
    recent_payments: [
      {
        id: 1,
        amount: 25.0,
        date: '2024-01-25',
        session_info: 'Individual - 6º Ano',
        hours: 1.0,
      },
    ],
  },
  quick_stats: {
    total_students: 2,
    sessions_today: 1,
    sessions_this_week: 3,
    completion_rate: 67.75,
    average_rating: null,
  },
};

describe('TeacherDashboard', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (useUserProfile as jest.Mock).mockReturnValue({
      userProfile: mockUserProfile,
    });
  });

  describe('Loading State', () => {
    it('should show loading state when data is being fetched', () => {
      (useTeacherDashboard as jest.Mock).mockReturnValue({
        data: null,
        isLoading: true,
        error: null,
        refresh: jest.fn(),
        lastUpdated: null,
      });

      render(<TeacherDashboard />);

      expect(screen.getByText('Carregando dashboard...')).toBeTruthy();
      expect(screen.getByTestId('main-layout')).toHaveAttribute(
        'data-title',
        'Dashboard do Professor'
      );
    });
  });

  describe('Error State', () => {
    it('should show error state when API fails', () => {
      (useTeacherDashboard as jest.Mock).mockReturnValue({
        data: null,
        isLoading: false,
        error: 'Erro de conexão',
        refresh: jest.fn(),
        lastUpdated: null,
      });

      render(<TeacherDashboard />);

      expect(screen.getByText('Erro ao Carregar Dashboard')).toBeTruthy();
      expect(screen.getByText('Erro de conexão')).toBeTruthy();
      expect(screen.getByText('Tentar Novamente')).toBeTruthy();
    });

    it('should call refresh when "Tentar Novamente" is pressed', () => {
      const mockRefresh = jest.fn();
      (useTeacherDashboard as jest.Mock).mockReturnValue({
        data: null,
        isLoading: false,
        error: 'Erro de conexão',
        refresh: mockRefresh,
        lastUpdated: null,
      });

      render(<TeacherDashboard />);

      fireEvent.press(screen.getByText('Tentar Novamente'));
      expect(mockRefresh).toHaveBeenCalledTimes(1);
    });
  });

  describe('Dashboard Content', () => {
    beforeEach(() => {
      (useTeacherDashboard as jest.Mock).mockReturnValue({
        data: mockDashboardData,
        isLoading: false,
        error: null,
        refresh: jest.fn(),
        lastUpdated: new Date('2024-01-25T16:00:00Z'),
      });
    });

    it('should display welcome message with correct greeting', () => {
      // Mock morning time
      jest.spyOn(Date.prototype, 'getHours').mockReturnValue(10);

      render(<TeacherDashboard />);

      expect(screen.getByText('Bom dia, Professor!')).toBeTruthy();
    });

    it('should display school name', () => {
      render(<TeacherDashboard />);

      expect(screen.getByText('Escola Primária Lisboa')).toBeTruthy();
    });

    it('should display quick stats', () => {
      render(<TeacherDashboard />);

      expect(screen.getByText('2')).toBeTruthy(); // Total students
      expect(screen.getByText('1')).toBeTruthy(); // Sessions today
      expect(screen.getByText('3')).toBeTruthy(); // Sessions this week
      expect(screen.getByText('68%')).toBeTruthy(); // Progress (rounded)
    });

    it('should display quick action buttons', () => {
      render(<TeacherDashboard />);

      expect(screen.getByText('Agendar Sessão')).toBeTruthy();
      expect(screen.getByText('Estudantes')).toBeTruthy();
      expect(screen.getByText('Analytics')).toBeTruthy();
      expect(screen.getByText('Sessões')).toBeTruthy();
    });

    it('should navigate to correct routes when quick actions are pressed', () => {
      render(<TeacherDashboard />);

      fireEvent.press(screen.getByText('Agendar Sessão'));
      expect(router.push).toHaveBeenCalledWith('/calendar/book');

      fireEvent.press(screen.getByText('Estudantes'));
      expect(router.push).toHaveBeenCalledWith('/(teacher)/students');

      fireEvent.press(screen.getByText('Analytics'));
      expect(router.push).toHaveBeenCalledWith('/(teacher)/analytics');

      fireEvent.press(screen.getByText('Sessões'));
      expect(router.push).toHaveBeenCalledWith('/(teacher)/sessions');
    });

    it("should display today's sessions", () => {
      render(<TeacherDashboard />);

      expect(screen.getByText('Sessões de Hoje')).toBeTruthy();
      expect(screen.getByText('14:00')).toBeTruthy();
      expect(screen.getByText('individual - 6º Ano')).toBeTruthy();
      expect(screen.getByText('Ana Costa')).toBeTruthy();
    });

    it('should display student roster with search functionality', async () => {
      render(<TeacherDashboard />);

      expect(screen.getByText('Estudantes')).toBeTruthy();
      expect(screen.getByPlaceholderText('Pesquisar estudante...')).toBeTruthy();

      // Should display students
      expect(screen.getByText('Ana Costa')).toBeTruthy();
      expect(screen.getByText('Pedro Santos')).toBeTruthy();

      // Should display progress percentages
      expect(screen.getByText('76%')).toBeTruthy(); // Ana's progress
      expect(screen.getByText('60%')).toBeTruthy(); // Pedro's progress
    });

    it('should filter students based on search query', async () => {
      render(<TeacherDashboard />);

      const searchInput = screen.getByPlaceholderText('Pesquisar estudante...');
      fireEvent.changeText(searchInput, 'Ana');

      await waitFor(() => {
        expect(screen.getByText('Ana Costa')).toBeTruthy();
        expect(screen.queryByText('Pedro Santos')).toBeFalsy();
      });
    });

    it('should display progress metrics', () => {
      render(<TeacherDashboard />);

      expect(screen.getByText('Métricas de Progresso')).toBeTruthy();
      expect(screen.getByText('68%')).toBeTruthy(); // Average progress
      expect(screen.getByText('1')).toBeTruthy(); // Total assessments
      expect(screen.getByText('1')).toBeTruthy(); // Students improved
    });

    it('should display recent activities', () => {
      render(<TeacherDashboard />);

      expect(screen.getByText('Atividade Recente')).toBeTruthy();
      expect(screen.getByText('Sessão de matemática concluída com Ana Costa')).toBeTruthy();
    });

    it('should handle refresh functionality', () => {
      const mockRefresh = jest.fn();
      (useTeacherDashboard as jest.Mock).mockReturnValue({
        data: mockDashboardData,
        isLoading: false,
        error: null,
        refresh: mockRefresh,
        lastUpdated: new Date(),
      });

      render(<TeacherDashboard />);

      const refreshButton = screen.getByLabelText('Atualizar dashboard');
      fireEvent.press(refreshButton);

      expect(mockRefresh).toHaveBeenCalledTimes(1);
    });
  });

  describe('Empty State', () => {
    it('should show welcome message for new teachers', () => {
      const emptyData = {
        ...mockDashboardData,
        quick_stats: {
          ...mockDashboardData.quick_stats,
          total_students: 0,
        },
        sessions: {
          today: [],
          upcoming: [],
          recent_completed: [],
        },
      };

      (useTeacherDashboard as jest.Mock).mockReturnValue({
        data: emptyData,
        isLoading: false,
        error: null,
        refresh: jest.fn(),
        lastUpdated: new Date(),
      });

      render(<TeacherDashboard />);

      expect(screen.getByText('Bem-vindo como Professor! 👨‍🏫')).toBeTruthy();
      expect(screen.getByText('Configurar Perfil')).toBeTruthy();
      expect(screen.getByText('Agendar Primeira Aula')).toBeTruthy();
    });
  });

  describe('Accessibility', () => {
    beforeEach(() => {
      (useTeacherDashboard as jest.Mock).mockReturnValue({
        data: mockDashboardData,
        isLoading: false,
        error: null,
        refresh: jest.fn(),
        lastUpdated: new Date(),
      });
    });

    it('should have proper accessibility labels', () => {
      render(<TeacherDashboard />);

      expect(screen.getByLabelText('Atualizar dashboard')).toBeTruthy();
      expect(screen.getByLabelText('Agendar nova sessão')).toBeTruthy();
      expect(screen.getByLabelText('Ver todos os estudantes')).toBeTruthy();
      expect(screen.getByLabelText('Ver analytics detalhados')).toBeTruthy();
      expect(screen.getByLabelText('Gerenciar sessões')).toBeTruthy();
    });

    it('should have proper accessibility roles', () => {
      render(<TeacherDashboard />);

      const refreshButton = screen.getByLabelText('Atualizar dashboard');
      expect(refreshButton).toHaveAccessibilityRole('button');
    });

    it('should provide progress information for screen readers', () => {
      render(<TeacherDashboard />);

      expect(screen.getByLabelText('Progresso: 76%')).toBeTruthy();
    });
  });

  describe('Error Handling with Partial Data', () => {
    it('should show warning when data is partially outdated', () => {
      (useTeacherDashboard as jest.Mock).mockReturnValue({
        data: mockDashboardData,
        isLoading: false,
        error: 'Alguns dados podem estar desatualizados',
        refresh: jest.fn(),
        lastUpdated: new Date(),
      });

      render(<TeacherDashboard />);

      expect(screen.getByText('Dados parcialmente desatualizados')).toBeTruthy();
      expect(screen.getByText('Alguns dados podem estar desatualizados')).toBeTruthy();
    });
  });
});

describe('TeacherDashboard Integration', () => {
  it('should handle complete user interaction flow', async () => {
    const mockRefresh = jest.fn();
    (useUserProfile as jest.Mock).mockReturnValue({
      userProfile: mockUserProfile,
    });
    (useTeacherDashboard as jest.Mock).mockReturnValue({
      data: mockDashboardData,
      isLoading: false,
      error: null,
      refresh: mockRefresh,
      lastUpdated: new Date(),
    });

    render(<TeacherDashboard />);

    // Check initial render
    expect(screen.getByText('Bom dia, Professor!')).toBeTruthy();

    // Test search functionality
    const searchInput = screen.getByPlaceholderText('Pesquisar estudante...');
    fireEvent.changeText(searchInput, 'Ana');

    await waitFor(() => {
      expect(screen.getByText('Ana Costa')).toBeTruthy();
    });

    // Test navigation
    fireEvent.press(screen.getByText('Estudantes'));
    expect(router.push).toHaveBeenCalledWith('/(teacher)/students');

    // Test refresh
    fireEvent.press(screen.getByLabelText('Atualizar dashboard'));
    expect(mockRefresh).toHaveBeenCalled();
  });
});
