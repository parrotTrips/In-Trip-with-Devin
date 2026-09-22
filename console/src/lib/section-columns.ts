/** Rótulos das colunas por seção. Uma seção nova é uma entrada aqui. */
export const SECTION_COLUMNS: Record<string, Record<string, string>> = {
  roteiro: { dia: 'Dia', data: 'Data', title: 'Título', atividades: 'Atividades' },
  recomendacoes: {
    name: 'Nome', category: 'Categoria', neighborhood: 'Bairro', address: 'Endereço',
  },
  faq: { question: 'Pergunta', answer: 'Resposta' },
  politica_cancelamento: { title: 'Título', body: 'Texto' },
  contatos_emergencia: { name: 'Nome', role: 'Função', phone: 'Telefone' },
  viajantes: {
    full_name: 'Nome', phone: 'Telefone', email: 'E-mail',
    profile_completed: 'Perfil preenchido',
  },
  staff: { full_name: 'Nome', function: 'Função', phone: 'Telefone' },
  contatos_operacionais: {
    category: 'Categoria', name: 'Nome', role: 'Função', phone: 'Telefone',
  },
  avisos: { title: 'Título', body: 'Texto', created_at: 'Enviado em' },
  tarefas_staff: { title: 'Tarefa', fase: 'Fase', responsavel: 'Responsável' },
  feedbacks: { viajante: 'Viajante', feedback: 'Feedback', created_at: 'Enviado em' },
};

/** Traduz um valor do banco para algo legível numa célula. */
export function formatCell(value: unknown): string {
  if (value === null || value === undefined || value === '') return '—';
  if (typeof value === 'boolean') return value ? 'Sim' : 'Não';
  if (typeof value === 'string' && /^\d{4}-\d{2}-\d{2}T/.test(value)) {
    const date = new Date(value);
    if (!Number.isNaN(date.getTime())) return date.toLocaleString('pt-BR');
  }
  return String(value);
}
