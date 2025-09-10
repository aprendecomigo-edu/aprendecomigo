# Onboarding/Workflow: Convite e Onboarding de Professor via Admin

## 1. Admin Gera e Envia Convite

O utilizador Admin autenticado acede à plataforma Aprende Comigo e navega até à secção de gestão de professores.

- O Admin seleciona "Adicionar Professor" no menu de gestão da escola
- O sistema apresenta um formulário para criar convite
- Campos obrigatórios: E-mail do professor e escola
- Campos opcionais: Mensagem personalizada
- O sistema gera automaticamente um link único com token criptográfico de 64 caracteres
- O Admin envia o link por e-mail (ou pode copiar para envio manual por SMS)
- O sistema regista o convite com status "PENDING" e data de expiração (7 dias)

## 2. Professor Recebe e Abre Link de Convite

O professor recebe o e-mail de convite e clica no link único.

- O sistema valida o token e verifica se o convite ainda é válido (não expirado, não aceite)
- Se válido, o convite é marcado como "VIEWED" com timestamp
- O sistema apresenta página de aceitação de convite com informações da escola
- Opções disponíveis: "Aceitar Convite" ou "Recusar Convite"

## 3. Preenchimento de Formulário Inicial

Quando o professor aceita o convite, acede ao formulário de registo inicial.

### Campos Obrigatórios:
- Nome completo
- E-mail (pré-preenchido do convite)
- Número de telemóvel (com validação de formato)

### Campos Opcionais:
- Disciplinas que leciona
- Ciclos/Anos de ensino preferidos
- Disponibilidade horária inicial

### Validações:
- E-mail: validação via regex e verificação de unicidade
- Telemóvel: formato nacional/internacional com prefixo país
- Verificação se e-mail já existe noutra escola (política a definir)

Após submissão:
- Conta criada em estado "PENDENTE"
- Professor automaticamente associado à escola do Admin
- Convite marcado como "ACCEPTED"

## 4. Verificação OTP e Primeiro Login

Após registo bem-sucedido, o sistema inicia processo de verificação.

- Sistema envia código OTP por SMS para o telemóvel fornecido
- Professor introduz código OTP (6 dígitos, válido por 10 minutos)
- Códigos com rate limiting (máximo 3 tentativas por hora)
- Após verificação bem-sucedida: login automático sem password
- Sistema utiliza django-sesame para autenticação por magic links + OTP

## 5. Dashboard Inicial com TO DOs

Após primeiro login, professor acede a dashboard "limpo" focado em TO DOs obrigatórias.

### Lista de TO DOs Obrigatórias:
1. **Confirmar E-mail** - Via link enviado por e-mail
2. **Completar Perfil**:
   - Disciplinas definitivas
   - Ciclos/anos de ensino
   - Dados pessoais (data de nascimento)
   - Dados fiscais (NIF com validação)
   - Dados bancários (IBAN com validação)
   - Fotografia de perfil
3. **Definir Disponibilidade Horária** - Horários semanais disponíveis para aulas

### Funcionalidades:
- Progresso em tempo real (barra de progresso percentual)
- Estados: Pendente/Concluído por cada TO DO
- Links diretos para completar cada tarefa
- Notificações de lembrança automáticas

## 6. Ativação de Conta

Quando todas as TO DOs obrigatórias são concluídas:

- Estado da conta muda automaticamente de "PENDENTE" para "ATIVO"
- Sistema regista timestamp de ativação
- Professor ganha acesso completo à plataforma
- Remoção de restrições de funcionalidades

## 7. E-mail de Boas-Vindas

Automaticamente após ativação da conta:

- Envio de e-mail de boas-vindas personalizado
- Inclui regulamento interno da plataforma
- Condições financeiras e sistema de pagamentos
- Documentos úteis (guias, manuais de utilização)
- Contactos de suporte técnico

## Caminhos Alternativos

### Convite Expirado/Inválido
- Mensagem clara: "Convite expirado. Peça reenvio ao Admin."
- Opção de "Solicitar Novo Convite" (envia e-mail ao Admin)
- Admin pode reenviar convite através do painel de gestão

### OTP Expirado/Incorreto
- Mensagem: "Código inválido ou expirado"
- Opção "Reenviar Código" com cooldown de 60 segundos
- Após 3 tentativas falhadas: bloqueio temporário de 1 hora

### Campos Obrigatórios em Falta
- Validação inline em tempo real
- Mensagens específicas: "Campo obrigatório", "E-mail inválido"
- Destaque visual nos campos com erro

### E-mail Já Usado Noutra Escola
- Verificação durante registo
- Opção 1: Bloquear registo com mensagem explicativa
- Opção 2: Sugerir processo de transferência (a definir política)

### Dados Inválidos (NIF/IBAN)
- Validação em tempo real conforme regras nacionais portuguesas
- Feedback imediato impede guardar formulário
- Links para informação sobre formatos corretos

### Design Mobile-First
- Todos os formulários responsivos para ecrãs pequenos
- Navegação táctil optimizada
- Campos de entrada adaptados a mobile
- Dashboard acessível em smartphone

### Criação Manual Alternativa
- Admin pode criar professor manualmente
- Formulário completo com todos os dados de uma vez
- Bypass do processo de convite para casos especiais

## Notas Importantes

### Segurança:
- Tokens de convite com encriptação forte (secrets.token_hex(32))
- Expiração automática após 7 dias
- Rate limiting para OTP e tentativas de login
- Logs de auditoria para todas as acções

### Performance:
- Convite enviado em ≤ 1 min após ação do Admin
- Registo do professor concluído em ≤ 5 min
- Dashboard carrega em ≤ 2 s com TO DOs
- Confirmação de e-mail em ≤ 7 dias (lembrete automático)

### Automatismos:
- E-mails de lembrete para TO DOs pendentes (3, 7, 14 dias)
- Notificações push para App móvel
- Relatórios automáticos para Admin sobre convites pendentes
- Limpeza automática de convites expirados

### Integração com Sistemas:
- SMS via serviço externo (Twilio/similar)
- E-mail via django-anymail + Amazon SES
- Validação NIF via API da AT (quando disponível)
- Validação IBAN via algoritmo de checksum

### Métricas e Monitorização:
- Taxa de convites aceites vs. enviados
- Tempo médio de convite até ativação completa
- % de professores que concluem TO DOs dentro de prazos
- Taxa de confirmação de e-mail
- Erros de submissão e taxa de abandono nos formulários
- Satisfação pós-ativação (questionário NPS)

### Ambiente de Teste:
- Compatible com browsers modernos (Chrome, Firefox, Safari, Edge)
- Responsive design testado em dispositivos móveis
- Testes automatizados para fluxo completo
- Ambiente de staging para validação antes de produção