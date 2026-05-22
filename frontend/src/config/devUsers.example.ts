// Exemplo de estrutura do devUsers.ts gerado por: python backend/scripts/gen_dev_users.py
// O arquivo real (devUsers.ts) está no .gitignore — nunca commitar (contém tokens JWT).

export const devUsers = [
  {
    userId: 'uuid-do-usuario',
    phone: '+1555TEST0001',
    name: 'Test Traveler — Nome da Viagem',
    token: 'jwt-token-gerado-pelo-script',
    role: 'traveler' as const,
    label: 'Nome da Viagem · 8 Dec 2026',   // exibido no switcher
    hasData: true,                             // false se trip_phases vazio
  },
] as const;
