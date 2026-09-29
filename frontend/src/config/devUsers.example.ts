// Exemplo de estrutura do devUsers.ts gerado por: python backend/scripts/gen_dev_users.py
// O arquivo real (devUsers.ts) está no .gitignore — nunca commitar (contém tokens JWT).

export const devUsers = [
  {
    userId: 'uuid-do-usuario',
    phone: '+1555TEST0001',
    name: 'Test Traveler — Nome da Viagem',
    // token_type: "session" com trip_id/role — a mesma viagem de `tripId`
    // abaixo. O middleware rejeita qualquer token sem esses claims.
    token: 'jwt-token-gerado-pelo-script',
    role: 'traveler' as const,
    label: 'Nome da Viagem · 8 Dec 2026',   // exibido no switcher
    hasData: true,                             // false se trip_phases vazio
    tripId: 'trip-uuid-da-viagem',             // deve bater com o claim trip_id do token
  },
] as const;
