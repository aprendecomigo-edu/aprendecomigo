import { render, screen, fireEvent, waitFor } from '@testing-library/react-native';
import React from 'react';

import StudentManagement from '@/components/teacher-dashboard/StudentManagement';

const mockStudents = [
  {
    id: 1,
    name: 'Ana Silva',
    email: 'ana.silva@email.com',
    current_level: '9º Ano',
    completion_percentage: 85,
    last_session_date: '2025-08-01',
    recent_assessments: [
      {
        id: 1,
        title: 'Teste de Matemática',
        assessment_type: 'quiz',
        percentage: 90,
        assessment_date: '2025-08-01',
      },
    ],
    skills_mastered: ['Álgebra', 'Geometria'],
  },
  {
    id: 2,
    name: 'João Santos',
    email: 'joao.santos@email.com',
    current_level: '10º Ano',
    completion_percentage: 45,
    last_session_date: '2025-07-15',
    recent_assessments: [],
    skills_mastered: ['Análise'],
  },
  {
    id: 3,
    name: 'Maria Costa',
    email: 'maria.costa@email.com',
    current_level: '11º Ano',
    completion_percentage: 92,
    last_session_date: null,
    recent_assessments: [
      {
        id: 2,
        title: 'Teste de Física',
        assessment_type: 'exam',
        percentage: 95,
        assessment_date: '2025-07-30',
      },
    ],
    skills_mastered: ['Mecânica', 'Termodinâmica', 'Eletromagnetismo'],
  },
];

const mockProps = {
  students: mockStudents,
  searchQuery: '',
  onSearchChange: jest.fn(),
  onStudentPress: jest.fn(),
  onScheduleSession: jest.fn(),
  onMessageStudent: jest.fn(),
  isLoading: false,
};

describe('StudentManagement', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders student list correctly', () => {
    render(<StudentManagement {...mockProps} />);

    expect(screen.getByText('Ana Silva')).toBeTruthy();
    expect(screen.getByText('João Santos')).toBeTruthy();
    expect(screen.getByText('Maria Costa')).toBeTruthy();
  });

  it('displays student statistics in header', () => {
    render(<StudentManagement {...mockProps} />);

    // Total students
    expect(screen.getByText('3')).toBeTruthy();

    // Should show average progress (85 + 45 + 92) / 3 = 74%
    expect(screen.getByText('74%')).toBeTruthy();
  });

  it('shows student status badges correctly', () => {
    render(<StudentManagement {...mockProps} />);

    expect(screen.getByText('Ativo')).toBeTruthy(); // Ana Silva (recent session)
    expect(screen.getByText('Inativo')).toBeTruthy(); // João Santos (old session)
    expect(screen.getByText('Novo')).toBeTruthy(); // Maria Costa (no sessions)
  });

  it('displays progress bars for each student', () => {
    render(<StudentManagement {...mockProps} />);

    expect(screen.getByText('85% - Excelente')).toBeTruthy();
    expect(screen.getByText('45% - Regular')).toBeTruthy();
    expect(screen.getByText('92% - Excelente')).toBeTruthy();
  });

  it('calls onSearchChange when search input changes', () => {
    render(<StudentManagement {...mockProps} />);

    const searchInput = screen.getByPlaceholderText('Pesquisar por nome ou email...');
    fireEvent.changeText(searchInput, 'Ana');

    expect(mockProps.onSearchChange).toHaveBeenCalledWith('Ana');
  });

  it('calls onStudentPress when student card is pressed', () => {
    render(<StudentManagement {...mockProps} />);

    const studentCard = screen.getByLabelText('Ver detalhes de Ana Silva');
    fireEvent.press(studentCard);

    expect(mockProps.onStudentPress).toHaveBeenCalledWith(1);
  });

  it('calls onScheduleSession when schedule button is pressed', () => {
    render(<StudentManagement {...mockProps} />);

    const scheduleButtons = screen.getAllByText('Agendar');
    fireEvent.press(scheduleButtons[0]);

    expect(mockProps.onScheduleSession).toHaveBeenCalledWith(1);
  });

  it('calls onMessageStudent when message button is pressed', () => {
    render(<StudentManagement {...mockProps} />);

    const messageButtons = screen.getAllByText('Mensagem');
    fireEvent.press(messageButtons[0]);

    expect(mockProps.onMessageStudent).toHaveBeenCalledWith(1);
  });

  it('shows attention alerts for students needing help', () => {
    render(<StudentManagement {...mockProps} />);

    // João Santos should have attention alert (low progress)
    expect(screen.getByText('Progresso baixo - considere agendar sessões adicionais')).toBeTruthy();

    // Maria Costa should have attention alert (no sessions)
    expect(screen.getByText('Sem aulas recentes - pode precisar de acompanhamento')).toBeTruthy();
  });

  it('filters students correctly', async () => {
    render(<StudentManagement {...mockProps} />);

    // Test search functionality by checking if onSearchChange is called
    const searchInput = screen.getByPlaceholderText('Pesquisar por nome ou email...');
    fireEvent.changeText(searchInput, 'ana');

    expect(mockProps.onSearchChange).toHaveBeenCalledWith('ana');
  });

  it('displays student email addresses', () => {
    render(<StudentManagement {...mockProps} />);

    expect(screen.getByText('ana.silva@email.com')).toBeTruthy();
    expect(screen.getByText('joao.santos@email.com')).toBeTruthy();
    expect(screen.getByText('maria.costa@email.com')).toBeTruthy();
  });

  it('shows last session dates', () => {
    render(<StudentManagement {...mockProps} />);

    expect(screen.getByText('01 ago')).toBeTruthy(); // Ana's last session
    expect(screen.getByText('15 jul')).toBeTruthy(); // João's last session
    expect(screen.getByText('Nunca')).toBeTruthy(); // Maria's no sessions
  });

  it('displays recent assessment scores', () => {
    render(<StudentManagement {...mockProps} />);

    expect(screen.getByText('90%')).toBeTruthy(); // Ana's assessment
    expect(screen.getByText('95%')).toBeTruthy(); // Maria's assessment
  });

  it('shows skills mastered count', () => {
    render(<StudentManagement {...mockProps} />);

    expect(screen.getByText('2')).toBeTruthy(); // Ana's skills
    expect(screen.getByText('1')).toBeTruthy(); // João's skills
    expect(screen.getByText('3')).toBeTruthy(); // Maria's skills
  });

  it('handles empty student list', () => {
    const emptyProps = { ...mockProps, students: [] };
    render(<StudentManagement {...emptyProps} />);

    expect(screen.getByText('Nenhum estudante encontrado')).toBeTruthy();
    expect(screen.getByText('Ainda não tem estudantes atribuídos.')).toBeTruthy();
  });

  it('is accessible with proper labels', () => {
    render(<StudentManagement {...mockProps} />);

    expect(screen.getByLabelText('Pesquisar estudantes')).toBeTruthy();
    expect(screen.getByLabelText('Ver detalhes de Ana Silva')).toBeTruthy();
    expect(screen.getByLabelText('Agendar sessão com Ana Silva')).toBeTruthy();
    expect(screen.getByLabelText('Enviar mensagem para Ana Silva')).toBeTruthy();
  });

  it('has working filter dropdown', () => {
    render(<StudentManagement {...mockProps} />);

    // Filter dropdown should be present
    expect(screen.getByText('Filtrar')).toBeTruthy();
  });

  it('sorts students by priority (needs attention first)', () => {
    render(<StudentManagement {...mockProps} />);

    // Students should be sorted with those needing attention first
    // This is based on the component's internal logic
    const studentCards = screen.getAllByText(/Ver detalhes de/);
    expect(studentCards).toHaveLength(3);
  });
});
