import { jest } from '@jest/globals';
import { render, screen, fireEvent, waitFor } from '@testing-library/react-native';
import { router } from 'expo-router';
import React from 'react';

import TeacherStudentsPage from '@/app/(teacher)/students/index';
import { useTeacherStudents } from '@/hooks/useTeacherDashboard';

// Mock dependencies
jest.mock('expo-router', () => ({
  router: {
    push: jest.fn(),
    back: jest.fn(),
  },
}));

jest.mock('@/hooks/useTeacherDashboard', () => ({
  useTeacherStudents: jest.fn(),
}));

jest.mock('@/hooks/useDebounce', () => ({
  useDebounce: jest.fn(value => value),
}));

jest.mock('@/components/layouts/main-layout', () => {
  return function MockMainLayout({ children, _title }: any) {
    return (
      <div data-testid="main-layout" data-title={_title}>
        {children}
      </div>
    );
  };
});

const mockStudents = [
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
    completion_percentage: 45.0,
    last_session_date: '2024-01-10T14:00:00Z', // More than 14 days ago
    recent_assessments: [],
    skills_mastered: [],
  },
  {
    id: 3,
    name: 'Maria Silva',
    email: 'maria@estudante.com',
    current_level: '6º Ano',
    completion_percentage: 90.0,
    last_session_date: '2024-01-24T14:00:00Z', // Within 7 days
    recent_assessments: [
      {
        id: 2,
        title: 'Teste Geometria',
        assessment_type: 'test',
        percentage: 92.0,
        assessment_date: '2024-01-23',
      },
    ],
    skills_mastered: ['Geometria básica', 'Perímetros', 'Áreas'],
  },
];

describe('TeacherStudentsPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Loading State', () => {
    it('should show loading state when students are being fetched', () => {
      (useTeacherStudents as jest.Mock).mockReturnValue({
        students: [],
        filteredStudents: [],
        isLoading: true,
        error: null,
        searchQuery: '',
        filterBy: 'all',
        setSearchQuery: jest.fn(),
        setFilterBy: jest.fn(),
        refresh: jest.fn(),
        getStudentById: jest.fn(),
      });

      render(<TeacherStudentsPage />);

      expect(screen.getByText('Carregando estudantes...')).toBeTruthy();
      expect(screen.getByTestId('main-layout')).toHaveAttribute('data-title', 'Estudantes');
    });
  });

  describe('Error State', () => {
    it('should show error state when API fails', () => {
      (useTeacherStudents as jest.Mock).mockReturnValue({
        students: [],
        filteredStudents: [],
        isLoading: false,
        error: 'Erro de conexão',
        searchQuery: '',
        filterBy: 'all',
        setSearchQuery: jest.fn(),
        setFilterBy: jest.fn(),
        refresh: jest.fn(),
        getStudentById: jest.fn(),
      });

      render(<TeacherStudentsPage />);

      expect(screen.getByText('Erro ao Carregar Estudantes')).toBeTruthy();
      expect(screen.getByText('Erro de conexão')).toBeTruthy();
      expect(screen.getByText('Tentar Novamente')).toBeTruthy();
    });

    it('should call refresh when "Tentar Novamente" is pressed', () => {
      const mockRefresh = jest.fn();
      (useTeacherStudents as jest.Mock).mockReturnValue({
        students: [],
        filteredStudents: [],
        isLoading: false,
        error: 'Erro de conexão',
        searchQuery: '',
        filterBy: 'all',
        setSearchQuery: jest.fn(),
        setFilterBy: jest.fn(),
        refresh: mockRefresh,
        getStudentById: jest.fn(),
      });

      render(<TeacherStudentsPage />);

      fireEvent.press(screen.getByText('Tentar Novamente'));
      expect(mockRefresh).toHaveBeenCalledTimes(1);
    });
  });

  describe('Empty State', () => {
    it('should show empty state when no students exist', () => {
      (useTeacherStudents as jest.Mock).mockReturnValue({
        students: [],
        filteredStudents: [],
        isLoading: false,
        error: null,
        searchQuery: '',
        filterBy: 'all',
        setSearchQuery: jest.fn(),
        setFilterBy: jest.fn(),
        refresh: jest.fn(),
        getStudentById: jest.fn(),
      });

      render(<TeacherStudentsPage />);

      expect(screen.getByText('Nenhum Estudante Encontrado')).toBeTruthy();
      expect(
        screen.getByText(
          'Ainda não tem estudantes atribuídos. Entre em contacto com a administração da escola.'
        )
      ).toBeTruthy();
      expect(screen.getByText('Agendar Primeira Aula')).toBeTruthy();
    });
  });

  describe('Students List', () => {
    beforeEach(() => {
      (useTeacherStudents as jest.Mock).mockReturnValue({
        students: mockStudents,
        filteredStudents: mockStudents,
        isLoading: false,
        error: null,
        searchQuery: '',
        filterBy: 'all',
        setSearchQuery: jest.fn(),
        setFilterBy: jest.fn(),
        refresh: jest.fn(),
        getStudentById: jest.fn(id => mockStudents.find(s => s.id === id)),
      });
    });

    it('should display students list', () => {
      render(<TeacherStudentsPage />);

      expect(screen.getByText('Meus Estudantes')).toBeTruthy();
      expect(screen.getByText('3 de 3 estudante(s)')).toBeTruthy();

      // Should display all students
      expect(screen.getByText('Ana Costa')).toBeTruthy();
      expect(screen.getByText('Pedro Santos')).toBeTruthy();
      expect(screen.getByText('Maria Silva')).toBeTruthy();

      // Should display email addresses
      expect(screen.getByText('ana@estudante.com')).toBeTruthy();
      expect(screen.getByText('pedro@estudante.com')).toBeTruthy();
      expect(screen.getByText('maria@estudante.com')).toBeTruthy();
    });

    it('should display correct progress percentages', () => {
      render(<TeacherStudentsPage />);

      expect(screen.getByText('76%')).toBeTruthy(); // Ana Costa (rounded)
      expect(screen.getByText('45%')).toBeTruthy(); // Pedro Santos
      expect(screen.getByText('90%')).toBeTruthy(); // Maria Silva
    });

    it('should display correct status badges', () => {
      render(<TeacherStudentsPage />);

      expect(screen.getByText('Ativo')).toBeTruthy(); // Maria (recent session)
      expect(screen.getByText('Inativo')).toBeTruthy(); // Pedro (old session)
    });

    it('should display last session dates correctly', () => {
      render(<TeacherStudentsPage />);

      expect(screen.getByText('25 jan')).toBeTruthy(); // Ana's last session
      expect(screen.getByText('10 jan')).toBeTruthy(); // Pedro's last session
      expect(screen.getByText('24 jan')).toBeTruthy(); // Maria's last session
    });

    it('should display skills and assessments count', () => {
      render(<TeacherStudentsPage />);

      expect(screen.getByText('2 competência(s) dominada(s)')).toBeTruthy(); // Ana
      expect(screen.getByText('1 avaliação(ões) recente(s)')).toBeTruthy(); // Ana
      expect(screen.getByText('3 competência(s) dominada(s)')).toBeTruthy(); // Maria
    });

    it('should navigate to student detail when student is pressed', () => {
      render(<TeacherStudentsPage />);

      fireEvent.press(screen.getByText('Ana Costa'));
      expect(router.push).toHaveBeenCalledWith('/(teacher)/students/1');
    });
  });

  describe('Search Functionality', () => {
    const mockSetSearchQuery = jest.fn();

    beforeEach(() => {
      (useTeacherStudents as jest.Mock).mockReturnValue({
        students: mockStudents,
        filteredStudents: mockStudents,
        isLoading: false,
        error: null,
        searchQuery: '',
        filterBy: 'all',
        setSearchQuery: mockSetSearchQuery,
        setFilterBy: jest.fn(),
        refresh: jest.fn(),
        getStudentById: jest.fn(),
      });
    });

    it('should have search input field', () => {
      render(<TeacherStudentsPage />);

      const searchInput = screen.getByPlaceholderText('Pesquisar por nome ou email...');
      expect(searchInput).toBeTruthy();
      expect(searchInput).toHaveAccessibilityLabel('Pesquisar estudantes');
    });

    it('should call setSearchQuery when search input changes', () => {
      render(<TeacherStudentsPage />);

      const searchInput = screen.getByPlaceholderText('Pesquisar por nome ou email...');
      fireEvent.changeText(searchInput, 'Ana');

      expect(mockSetSearchQuery).toHaveBeenCalledWith('Ana');
    });

    it('should show filtered results when search query is active', () => {
      (useTeacherStudents as jest.Mock).mockReturnValue({
        students: mockStudents,
        filteredStudents: [mockStudents[0]], // Only Ana
        isLoading: false,
        error: null,
        searchQuery: 'Ana',
        filterBy: 'all',
        setSearchQuery: jest.fn(),
        setFilterBy: jest.fn(),
        refresh: jest.fn(),
        getStudentById: jest.fn(),
      });

      render(<TeacherStudentsPage />);

      expect(screen.getByText('1 de 3 estudante(s)')).toBeTruthy();
      expect(screen.getByText('Pesquisa: "Ana"')).toBeTruthy();
    });

    it('should show no results message when search yields no matches', () => {
      (useTeacherStudents as jest.Mock).mockReturnValue({
        students: mockStudents,
        filteredStudents: [],
        isLoading: false,
        error: null,
        searchQuery: 'xyz',
        filterBy: 'all',
        setSearchQuery: jest.fn(),
        setFilterBy: jest.fn(),
        refresh: jest.fn(),
        getStudentById: jest.fn(),
      });

      render(<TeacherStudentsPage />);

      expect(screen.getByText('Nenhum estudante encontrado')).toBeTruthy();
      expect(
        screen.getByText('Nenhum resultado para "xyz". Tente ajustar os filtros de pesquisa.')
      ).toBeTruthy();
    });
  });

  describe('Filter Functionality', () => {
    const mockSetFilterBy = jest.fn();

    beforeEach(() => {
      (useTeacherStudents as jest.Mock).mockReturnValue({
        students: mockStudents,
        filteredStudents: mockStudents,
        isLoading: false,
        error: null,
        searchQuery: '',
        filterBy: 'all',
        setSearchQuery: jest.fn(),
        setFilterBy: mockSetFilterBy,
        refresh: jest.fn(),
        getStudentById: jest.fn(),
      });
    });

    it('should have filter dropdown', () => {
      render(<TeacherStudentsPage />);

      expect(screen.getByText('Filtrar')).toBeTruthy();
    });

    it('should show active filter badge', () => {
      (useTeacherStudents as jest.Mock).mockReturnValue({
        students: mockStudents,
        filteredStudents: [mockStudents[2]], // Only Maria (active)
        isLoading: false,
        error: null,
        searchQuery: '',
        filterBy: 'active',
        setSearchQuery: jest.fn(),
        setFilterBy: jest.fn(),
        refresh: jest.fn(),
        getStudentById: jest.fn(),
      });

      render(<TeacherStudentsPage />);

      expect(screen.getByText('Ativos')).toBeTruthy();
      expect(screen.getByText('1 de 3 estudante(s)')).toBeTruthy();
    });

    it('should show needs attention filter results', () => {
      (useTeacherStudents as jest.Mock).mockReturnValue({
        students: mockStudents,
        filteredStudents: [mockStudents[1]], // Only Pedro (needs attention)
        isLoading: false,
        error: null,
        searchQuery: '',
        filterBy: 'needs_attention',
        setSearchQuery: jest.fn(),
        setFilterBy: jest.fn(),
        refresh: jest.fn(),
        getStudentById: jest.fn(),
      });

      render(<TeacherStudentsPage />);

      expect(screen.getByText('Precisam Atenção')).toBeTruthy();
      expect(screen.getByText('1 de 3 estudante(s)')).toBeTruthy();
    });

    it('should clear filters when "Limpar filtros" is pressed', () => {
      const mockSetSearchQuery = jest.fn();
      const mockSetFilterBy = jest.fn();

      (useTeacherStudents as jest.Mock).mockReturnValue({
        students: mockStudents,
        filteredStudents: [mockStudents[0]],
        isLoading: false,
        error: null,
        searchQuery: 'Ana',
        filterBy: 'active',
        setSearchQuery: mockSetSearchQuery,
        setFilterBy: mockSetFilterBy,
        refresh: jest.fn(),
        getStudentById: jest.fn(),
      });

      render(<TeacherStudentsPage />);

      fireEvent.press(screen.getByText('Limpar filtros'));

      expect(mockSetSearchQuery).toHaveBeenCalledWith('');
      expect(mockSetFilterBy).toHaveBeenCalledWith('all');
    });
  });

  describe('Accessibility', () => {
    beforeEach(() => {
      (useTeacherStudents as jest.Mock).mockReturnValue({
        students: mockStudents,
        filteredStudents: mockStudents,
        isLoading: false,
        error: null,
        searchQuery: '',
        filterBy: 'all',
        setSearchQuery: jest.fn(),
        setFilterBy: jest.fn(),
        refresh: jest.fn(),
        getStudentById: jest.fn(),
      });
    });

    it('should have proper accessibility labels and roles', () => {
      render(<TeacherStudentsPage />);

      expect(screen.getByLabelText('Atualizar lista de estudantes')).toBeTruthy();
      expect(screen.getByLabelText('Pesquisar estudantes')).toBeTruthy();
      expect(screen.getByLabelText('Ver detalhes de Ana Costa')).toBeTruthy();

      const refreshButton = screen.getByLabelText('Atualizar lista de estudantes');
      expect(refreshButton).toHaveAccessibilityRole('button');

      const studentButton = screen.getByLabelText('Ver detalhes de Ana Costa');
      expect(studentButton).toHaveAccessibilityRole('button');
    });
  });

  describe('Performance Optimizations', () => {
    it('should handle large student lists efficiently', () => {
      const largeStudentList = Array.from({ length: 100 }, (_, i) => ({
        ...mockStudents[0],
        id: i + 1,
        name: `Estudante ${i + 1}`,
        email: `estudante${i + 1}@escola.com`,
      }));

      (useTeacherStudents as jest.Mock).mockReturnValue({
        students: largeStudentList,
        filteredStudents: largeStudentList,
        isLoading: false,
        error: null,
        searchQuery: '',
        filterBy: 'all',
        setSearchQuery: jest.fn(),
        setFilterBy: jest.fn(),
        refresh: jest.fn(),
        getStudentById: jest.fn(),
      });

      render(<TeacherStudentsPage />);

      expect(screen.getByText('100 de 100 estudante(s)')).toBeTruthy();
      // FlatList should handle virtualization automatically
    });
  });

  describe('Error Handling with Partial Data', () => {
    it('should show warning when data is partially outdated', () => {
      (useTeacherStudents as jest.Mock).mockReturnValue({
        students: mockStudents,
        filteredStudents: mockStudents,
        isLoading: false,
        error: 'Alguns dados podem estar desatualizados',
        searchQuery: '',
        filterBy: 'all',
        setSearchQuery: jest.fn(),
        setFilterBy: jest.fn(),
        refresh: jest.fn(),
        getStudentById: jest.fn(),
      });

      render(<TeacherStudentsPage />);

      expect(screen.getByText('Dados parcialmente desatualizados')).toBeTruthy();
      expect(screen.getByText('Alguns dados podem estar desatualizados')).toBeTruthy();
    });
  });
});
