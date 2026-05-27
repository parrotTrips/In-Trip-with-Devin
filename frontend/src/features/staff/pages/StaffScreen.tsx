import { useAuth } from '../../../app/providers/auth-context';

const MOCK_DAYS = [
  {
    id: '1',
    label: 'Dia 1',
    date: '10 Jul',
    tasks: [
      { id: 't1', time: '08:00', title: 'Recepção dos viajantes no aeroporto', done: false },
      { id: 't2', time: '12:00', title: 'Check-in no hotel e briefing de boas-vindas', done: false },
      { id: 't3', time: '19:00', title: 'Jantar de abertura — confirmar reserva', done: false },
    ],
  },
  {
    id: '2',
    label: 'Dia 2',
    date: '11 Jul',
    tasks: [
      { id: 't4', time: '07:30', title: 'Café da manhã e distribuição de kits', done: false },
      { id: 't5', time: '09:00', title: 'Passeio de barco — coordenar embarque', done: false },
      { id: 't6', time: '16:00', title: 'Atividade opcional — lista de presença', done: false },
    ],
  },
  {
    id: '3',
    label: 'Dia 3',
    date: '12 Jul',
    tasks: [
      { id: 't7', time: '08:00', title: 'Trilha matinal — verificar equipamentos', done: false },
      { id: 't8', time: '14:00', title: 'Tempo livre — disponível para dúvidas', done: false },
      { id: 't9', time: '20:00', title: 'Festa de encerramento — setup do espaço', done: false },
    ],
  },
];

export default function StaffScreen() {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-emerald-700 text-white px-4 pt-10 pb-6">
        <div className="flex items-center justify-between mb-1">
          <span className="text-emerald-200 text-sm font-medium uppercase tracking-wide">Staff</span>
          <button onClick={logout} className="text-emerald-300 text-sm hover:text-white">
            Sair
          </button>
        </div>
        <h1 className="text-2xl font-bold">Olá, {user?.name?.split(' ')[0] ?? 'Staff'} 👋</h1>
        <p className="text-emerald-200 text-sm mt-1">Galápagos Jul 2026 · Suas tarefas</p>
      </div>

      {/* Days */}
      <div className="px-4 py-6 space-y-6">
        {MOCK_DAYS.map((day) => (
          <div key={day.id} className="bg-white rounded-2xl shadow-sm overflow-hidden">
            {/* Day header */}
            <div className="bg-emerald-50 px-4 py-3 flex items-center justify-between border-b border-emerald-100">
              <span className="font-semibold text-emerald-800">{day.label}</span>
              <span className="text-sm text-emerald-600">{day.date}</span>
            </div>

            {/* Tasks */}
            <div className="divide-y divide-gray-50">
              {day.tasks.map((task) => (
                <div key={task.id} className="px-4 py-3 flex items-start gap-3">
                  <div className="mt-0.5 w-5 h-5 rounded-full border-2 border-gray-300 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-800">{task.title}</p>
                    {task.time && (
                      <p className="text-xs text-gray-400 mt-0.5">{task.time}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}

        <p className="text-center text-xs text-gray-400 pb-4">
          Dados de exemplo — integração com backend em breve
        </p>
      </div>
    </div>
  );
}
