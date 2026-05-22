import { useState } from 'react';
import { useAuth } from '../../app/providers/auth-context';

type DevUser = {
  userId: string;
  phone: string;
  name: string;
  token: string;
  role: 'traveler' | 'staff';
  label: string;
  hasData: boolean;
};

// devUsers.ts é gerado por gen_dev_users.py e está no .gitignore
// import.meta.glob retorna {} se o arquivo não existir — graceful fallback
const devModules = import.meta.glob<{ devUsers: readonly DevUser[] }>(
  '../../config/devUsers.ts',
  { eager: true }
);
const devUsers: DevUser[] = [...(Object.values(devModules)[0]?.devUsers ?? [])];

export default function DevUserSwitcher() {
  const [open, setOpen] = useState(false);
  const { user, login } = useAuth();

  // Só aparece em dev, com usuários carregados, e quando staff está logado
  if (!import.meta.env.DEV || devUsers.length === 0 || user?.role !== 'staff') return null;

  const handleSelect = (u: DevUser) => {
    login(u.userId, u.phone, u.name, u.token, u.role);
    setOpen(false);
    window.location.reload();
  };

  return (
    <div className="fixed bottom-24 right-4 z-50">
      {open && (
        <div className="mb-2 bg-white rounded-2xl shadow-xl border border-gray-200 overflow-hidden w-64">
          <div className="px-4 py-3 border-b border-gray-100">
            <p className="text-xs font-bold text-gray-500 uppercase tracking-wide">Ver como viajante</p>
          </div>
          {devUsers.map(u => (
            <button
              key={u.userId}
              onClick={() => handleSelect(u)}
              className="w-full px-4 py-3 text-left hover:bg-gray-50 transition-colors border-b border-gray-50 last:border-0"
            >
              <p className="text-sm font-semibold text-gray-800">{u.label}</p>
              {!u.hasData && (
                <p className="text-xs text-amber-500 mt-0.5">sem dados — testa estado vazio</p>
              )}
            </button>
          ))}
        </div>
      )}
      <button
        onClick={() => setOpen(!open)}
        className="w-12 h-12 bg-gray-800 text-white rounded-full shadow-lg flex items-center justify-center text-lg hover:bg-gray-700 transition-colors"
        title="Ver como viajante"
      >
        👁️
      </button>
    </div>
  );
}
