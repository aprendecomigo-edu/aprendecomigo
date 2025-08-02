/**
 * Constants for the teacher invitation system.
 *
 * This file contains all hardcoded values used throughout the invitation
 * system to improve maintainability and prevent magic numbers.
 */

export const INVITATION_CONSTANTS = {
  // Limits
  MAX_BULK_INVITATIONS: 50,
  MAX_CUSTOM_MESSAGE_LENGTH: 500,

  // Polling intervals (in milliseconds)
  STATUS_POLLING_INTERVAL: 30000, // 30 seconds

  // Invitation link settings
  DEFAULT_EXPIRY_DAYS: 7,

  // UI timeouts
  COPY_FEEDBACK_TIMEOUT: 2000, // 2 seconds

  // Validation
  MIN_EMAIL_LENGTH: 5,

  // Error retry settings
  DEFAULT_RETRY_ATTEMPTS: 3,
  RETRY_DELAY_MS: 1000,
  RETRY_BACKOFF_MULTIPLIER: 2,
} as const;

export const INVITATION_MESSAGES = {
  SUCCESS: {
    INVITE_SENT: 'Convite enviado por email com sucesso!',
    BULK_INVITES_COMPLETED: 'Convites enviados com sucesso',
    INVITATION_ACCEPTED: 'Convite aceito com sucesso! Você já faz parte da escola.',
    INVITATION_DECLINED: 'O convite foi declinado com sucesso.',
    INVITATION_CANCELLED: 'Invitation cancelled successfully',
    INVITATION_RESENT: 'Invitation resent successfully',
    LINK_COPIED: 'Link copiado!',
  },
  ERROR: {
    INVALID_EMAIL: 'Por favor, insira um email válido.',
    NO_EMAILS: 'Por favor, insira pelo menos um email válido.',
    TOO_MANY_EMAILS: `Máximo de ${INVITATION_CONSTANTS.MAX_BULK_INVITATIONS} convites por vez.`,
    FAILED_TO_SEND: 'Failed to send invitation',
    FAILED_TO_ACCEPT: 'Erro ao aceitar convite',
    FAILED_TO_DECLINE: 'Erro ao declinar convite',
    FAILED_TO_COPY: 'Não foi possível copiar o link.',
    WHATSAPP_NOT_FOUND: 'Por favor, instale o WhatsApp para usar esta funcionalidade.',
    FAILED_TO_OPEN_WHATSAPP: 'Não foi possível abrir o WhatsApp.',
    INVITATION_NOT_FOUND: 'O convite não pôde ser encontrado ou é inválido.',
    WRONG_USER:
      'Este convite não é para o usuário atualmente autenticado. Por favor, faça login com o email correto.',
    AUTHENTICATION_REQUIRED: 'Você precisa estar logado para aceitar este convite.',
    CANNOT_ACCEPT: 'Não é possível aceitar este convite',
    LOAD_INVITATION_LINK_FAILED: 'Não foi possível carregar o link de convite.',
  },
  INFO: {
    AUTHENTICATION_NEEDED: 'Para aceitar este convite, você precisa fazer login com o email',
    QR_CODE_COMING_SOON: 'Funcionalidade de QR Code será implementada em breve.',
    PROCESSING: 'Processando...',
    LOADING_INVITATION: 'Carregando convite...',
    SENDING: 'Enviando...',
    DECLINING: 'Declinando...',
  },
} as const;

export const INVITATION_PLACEHOLDERS = {
  EMAIL: 'email@exemplo.com',
  BULK_EMAILS: `email1@exemplo.com, email2@exemplo.com
ou um por linha`,
  CUSTOM_MESSAGE: 'Adicione uma mensagem personalizada ao convite...',
} as const;

export const ROLE_LABELS = {
  teacher: 'Professor',
  school_admin: 'Administrador',
} as const;

export const ROLE_DESCRIPTIONS = {
  teacher: 'Pode dar aulas e gerenciar estudantes',
  school_admin: 'Pode gerenciar escola e professores',
} as const;
