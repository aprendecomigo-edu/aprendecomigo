import { TutorialConfig } from '../types';

export const dashboardTutorial: TutorialConfig = {
  id: 'dashboard-onboarding',
  title: 'Bem-vindo ao Aprende Comigo!',
  description: 'Vamos mostrar como usar o seu novo dashboard.',
  canSkip: true,
  showProgress: true,
  steps: [
    {
      id: 'welcome',
      title: 'Bem-vindo ao seu Dashboard! 👋',
      content:
        'Parabéns por se juntar ao Aprende Comigo! Este é o seu centro de controle onde você pode gerir toda a sua plataforma educacional.',
      position: 'center',
      highlight: false,
      skippable: true,
    },
    {
      id: 'profile-section',
      title: 'Seu Perfil',
      content:
        'Aqui você pode ver o seu perfil e informações básicas. Este é o seu espaço pessoal no dashboard.',
      targetElement: 'profile-section',
      position: 'bottom',
      highlight: true,
    },
    {
      id: 'warning-banner',
      title: 'Avisos Importantes',
      content:
        'Esta seção mostra avisos importantes sobre o estado da sua conta. Certifique-se de completar as tarefas pendentes para manter sua conta ativa.',
      targetElement: 'warning-banner',
      position: 'bottom',
      highlight: true,
    },
    {
      id: 'activities-section',
      title: 'Próximas Atividades',
      content:
        'Aqui você pode ver todas as atividades agendadas. Quando tiver professores e alunos cadastrados, as aulas aparecerão aqui.',
      targetElement: 'activities-section',
      position: 'top',
      highlight: true,
    },
    {
      id: 'view-filters',
      title: 'Filtros de Visualização',
      content:
        'Use estes filtros para organizar suas atividades por pessoa, evento ou lista. Você também pode alternar entre vista de lista e calendário.',
      targetElement: 'view-filters',
      position: 'bottom',
      highlight: true,
    },
    {
      id: 'tasks-section',
      title: 'Tarefas Pendentes',
      content:
        'Esta seção mostra suas tarefas pendentes. Complete-as para configurar totalmente sua plataforma e começar a conectar professores e alunos.',
      targetElement: 'tasks-section',
      position: 'top',
      highlight: true,
    },
    {
      id: 'navigation',
      title: 'Navegação',
      content:
        'Use o menu lateral (desktop) ou inferior (mobile) para navegar entre as diferentes seções da plataforma.',
      targetElement: 'navigation',
      position: 'center',
      highlight: true,
    },
    {
      id: 'next-steps',
      title: 'Próximos Passos',
      content:
        'Agora você está pronto para começar! Recomendamos que complete as tarefas pendentes primeiro, depois adicione professores e alunos à sua plataforma.',
      position: 'center',
      highlight: false,
      action: {
        label: 'Começar',
        onPress: () => {
          console.log('Tutorial completed - redirecting to tasks');
        },
      },
    },
  ],
};
