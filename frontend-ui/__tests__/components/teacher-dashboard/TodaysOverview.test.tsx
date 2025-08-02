import { render, screen, fireEvent } from '@testing-library/react-native';
import React from 'react';

import TodaysOverview from '@/components/teacher-dashboard/TodaysOverview';

const mockSessionsData = {
  today: [
    {
      id: 1,
      date: '2025-08-02',
      start_time: '09:00',
      end_time: '10:00',
      session_type: 'Matemática',
      grade_level: '9º Ano',
      student_count: 3,
      student_names: ['Ana Silva', 'João Santos', 'Maria Costa'],
      status: 'scheduled',
      notes: 'Revisão de álgebra',
      duration_hours: 1,
    },
    {
      id: 2,
      date: '2025-08-02',
      start_time: '14:00',
      end_time: '15:00',
      session_type: 'Física',
      grade_level: '10º Ano',
      student_count: 2,
      student_names: ['Pedro Oliveira', 'Sofia Fernandes'],
      status: 'completed',
      notes: 'Mecânica clássica',
      duration_hours: 1,
    },
  ],
  upcoming: [
    {
      id: 3,
      date: '2025-08-03',
      start_time: '10:00',
      end_time: '11:00',
      session_type: 'Química',
      grade_level: '11º Ano',
      student_count: 1,
      student_names: ['Carlos Rodrigues'],
      status: 'scheduled',
      notes: 'Reações orgânicas',
      duration_hours: 1,
    },
  ],
  recent_completed: [],
};

const mockProps = {
  sessions: mockSessionsData,
  onScheduleSession: jest.fn(),
  onViewSession: jest.fn(),
  onStartSession: jest.fn(),
  isLoading: false,
};

describe('TodaysOverview', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders today\'s sessions correctly', () => {
    render(<TodaysOverview {...mockProps} />);

    // Check if today's sessions are displayed
    expect(screen.getByText('Matemática - 9º Ano')).toBeTruthy();
    expect(screen.getByText('Física - 10º Ano')).toBeTruthy();
    expect(screen.getByText('09:00 - 10:00 (1h)')).toBeTruthy();
    expect(screen.getByText('14:00 - 15:00 (1h)')).toBeTruthy();
  });

  it('displays session statistics correctly', () => {
    render(<TodaysOverview {...mockProps} />);

    // Check stats
    expect(screen.getByText('2')).toBeTruthy(); // Total sessions
    expect(screen.getByText('1')).toBeTruthy(); // Completed sessions
    expect(screen.getByText('0')).toBeTruthy(); // In progress sessions
    expect(screen.getByText('1')).toBeTruthy(); // Upcoming sessions
  });

  it('shows upcoming sessions', () => {
    render(<TodaysOverview {...mockProps} />);

    expect(screen.getByText('Química - 11º Ano')).toBeTruthy();
    expect(screen.getByText('10:00 - 11:00 (1h)')).toBeTruthy();
  });

  it('calls onScheduleSession when schedule button is pressed', () => {
    render(<TodaysOverview {...mockProps} />);

    const scheduleButtons = screen.getAllByText('Agendar Nova Sessão');
    fireEvent.press(scheduleButtons[0]);

    expect(mockProps.onScheduleSession).toHaveBeenCalledTimes(1);
  });

  it('calls onViewSession when session is pressed', () => {
    render(<TodaysOverview {...mockProps} />);

    // Find session cards by their accessibility label
    const sessionCard = screen.getByLabelText('Sessão Matemática às 09:00');
    fireEvent.press(sessionCard);

    expect(mockProps.onViewSession).toHaveBeenCalledWith(1);
  });

  it('calls onStartSession when start button is pressed for current session', () => {
    // Mock current time to be during the session
    const mockDate = new Date('2025-08-02T09:30:00');
    jest.spyOn(global, 'Date').mockImplementation(() => mockDate as any);

    render(<TodaysOverview {...mockProps} />);

    const startButton = screen.getByText('Iniciar');
    fireEvent.press(startButton);

    expect(mockProps.onStartSession).toHaveBeenCalledWith(1);

    // Restore original Date
    (global.Date as any).mockRestore();
  });

  it('displays empty state when no sessions', () => {
    const emptyProps = {
      ...mockProps,
      sessions: { today: [], upcoming: [], recent_completed: [] },
    };

    render(<TodaysOverview {...emptyProps} />);

    expect(screen.getByText('Sem Sessões Hoje')).toBeTruthy();
    expect(screen.getByText('Que tal agendar uma sessão para hoje ou para os próximos dias?')).toBeTruthy();
  });

  it('displays session status badges correctly', () => {
    render(<TodaysOverview {...mockProps} />);

    expect(screen.getByText('Agendada')).toBeTruthy();
    expect(screen.getByText('Concluída')).toBeTruthy();
  });

  it('shows student names for sessions', () => {
    render(<TodaysOverview {...mockProps} />);

    expect(screen.getByText('Ana Silva, João Santos, Maria Costa')).toBeTruthy();
    expect(screen.getByText('Pedro Oliveira, Sofia Fernandes')).toBeTruthy();
  });

  it('displays session notes when available', () => {
    render(<TodaysOverview {...mockProps} />);

    expect(screen.getByText('Revisão de álgebra')).toBeTruthy();
    expect(screen.getByText('Mecânica clássica')).toBeTruthy();
  });

  it('handles loading state', () => {
    const loadingProps = { ...mockProps, isLoading: true };
    render(<TodaysOverview {...loadingProps} />);

    // Component should still render but may show loading indicators
    expect(screen.getByText('Hoje')).toBeTruthy();
  });

  it('is accessible with proper labels', () => {
    render(<TodaysOverview {...mockProps} />);

    // Check accessibility labels
    expect(screen.getByLabelText('Agendar nova sessão')).toBeTruthy();
    expect(screen.getByLabelText('Sessão Matemática às 09:00')).toBeTruthy();
    expect(screen.getByLabelText('Sessão Física às 14:00')).toBeTruthy();
  });
});