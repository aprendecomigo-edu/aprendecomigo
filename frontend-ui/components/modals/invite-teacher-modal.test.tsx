import { render, fireEvent, waitFor, screen } from '@testing-library/react-native';
import React from 'react';

import { InviteTeacherModal } from './invite-teacher-modal';

// Mock the API client
jest.mock('@/api/apiClient', () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
    post: jest.fn(),
  },
}));

// Mock react-native modules
jest.mock('react-native', () => {
  const RN = jest.requireActual('react-native');
  return {
    ...RN,
    Alert: {
      alert: jest.fn(),
    },
    Linking: {
      canOpenURL: jest.fn().mockResolvedValue(true),
      openURL: jest.fn().mockResolvedValue(undefined),
    },
    Platform: {
      OS: 'web',
    },
  };
});

// Mock navigator.clipboard for web
Object.defineProperty(navigator, 'clipboard', {
  value: {
    writeText: jest.fn().mockResolvedValue(undefined),
  },
  writable: true,
});

describe('InviteTeacherModal', () => {
  const defaultProps = {
    isOpen: true,
    onClose: jest.fn(),
    onSuccess: jest.fn(),
    schoolId: 1,
  };

  const mockInvitationLink = {
    url: 'https://aprendecomigo.com/join-school/xyz789abc123',
    expires_at: '2025-12-31T23:59:59Z',
    usage_count: 5,
  };

  beforeEach(() => {
    jest.clearAllMocks();
    const apiClient = require('@/api/apiClient').default;
    apiClient.get.mockResolvedValue({
      data: { invitation_link: mockInvitationLink },
    });
  });

  it('should render the modal when isOpen is true', async () => {
    render(<InviteTeacherModal {...defaultProps} />);

    expect(screen.getByText('Convidar Professor')).toBeTruthy();
  });

  it('should display loading state initially', () => {
    render(<InviteTeacherModal {...defaultProps} />);

    expect(screen.getByText('Carregando link de convite...')).toBeTruthy();
  });

  it('should call the school invitation link API on mount', async () => {
    const apiClient = require('@/api/apiClient').default;

    render(<InviteTeacherModal {...defaultProps} />);

    await waitFor(() => {
      expect(apiClient.get).toHaveBeenCalledWith('/accounts/schools/1/invitation-link/');
    });
  });

  it('should display invitation link after loading', async () => {
    render(<InviteTeacherModal {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText(mockInvitationLink.url)).toBeTruthy();
    });
  });

  it('should display sharing options', async () => {
    render(<InviteTeacherModal {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText('Copiar Link')).toBeTruthy();
      expect(screen.getByText('Compartilhar no WhatsApp')).toBeTruthy();
      expect(screen.getByText('Mostrar QR Code')).toBeTruthy();
      expect(screen.getByText('Enviar por Email')).toBeTruthy();
    });
  });

  it('should copy link to clipboard when copy button is pressed', async () => {
    render(<InviteTeacherModal {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText(mockInvitationLink.url)).toBeTruthy();
    });

    const copyButton = screen.getByText('Copiar Link');
    fireEvent.press(copyButton);

    await waitFor(() => {
      expect(navigator.clipboard.writeText).toHaveBeenCalledWith(mockInvitationLink.url);
    });
  });

  it('should show "Link Copiado!" after successful copy', async () => {
    render(<InviteTeacherModal {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText(mockInvitationLink.url)).toBeTruthy();
    });

    const copyButton = screen.getByText('Copiar Link');
    fireEvent.press(copyButton);

    await waitFor(() => {
      expect(screen.getByText('Link Copiado!')).toBeTruthy();
    });
  });

  it('should handle email input and submission', async () => {
    const apiClient = require('@/api/apiClient').default;
    apiClient.post.mockResolvedValue({ data: { success: true } });

    render(<InviteTeacherModal {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText(mockInvitationLink.url)).toBeTruthy();
    });

    const emailInput = screen.getByPlaceholderText('email@exemplo.com');
    fireEvent.changeText(emailInput, 'test@example.com');

    const sendButton = screen.getByText('Enviar por Email');
    fireEvent.press(sendButton);

    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalledWith('/accounts/teachers/invite-email/', {
        email: 'test@example.com',
        school_id: 1,
        role: 'teacher',
      });
    });
  });

  it('should call onClose when close button is pressed', async () => {
    render(<InviteTeacherModal {...defaultProps} />);

    const closeButton = screen.getByText('Fechar');
    fireEvent.press(closeButton);

    expect(defaultProps.onClose).toHaveBeenCalled();
  });

  it('should show error message when API call fails', async () => {
    const apiClient = require('@/api/apiClient').default;
    apiClient.get.mockRejectedValue(new Error('API Error'));

    render(<InviteTeacherModal {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText('Erro ao carregar o link de convite')).toBeTruthy();
    });
  });
});
