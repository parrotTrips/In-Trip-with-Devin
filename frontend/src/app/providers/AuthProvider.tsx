import { useEffect, useState, type ReactNode } from 'react';

import { AuthContext, type AuthUser } from './auth-context';

function getStoredUser(): AuthUser | null {
  try {
    const stored = localStorage.getItem('parrot_user');
    return stored ? JSON.parse(stored) : null;
  } catch {
    return null;
  }
}

function getDevAutoLoginUser(): AuthUser | null {
  if (!import.meta.env.DEV || import.meta.env.VITE_DEV_AUTO_LOGIN !== 'true') {
    return null;
  }

  const userId = Number.parseInt(import.meta.env.VITE_DEV_USER_ID ?? '1', 10);

  return {
    userId: Number.isNaN(userId) ? 1 : userId,
    phone: import.meta.env.VITE_DEV_USER_PHONE ?? '+15550000001',
    name: import.meta.env.VITE_DEV_USER_NAME ?? 'Dev Traveler',
    token: import.meta.env.VITE_DEV_TOKEN ?? '',
  };
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(() => getStoredUser() ?? getDevAutoLoginUser());

  useEffect(() => {
    if (user) {
      localStorage.setItem('parrot_user', JSON.stringify(user));
      return;
    }
    localStorage.removeItem('parrot_user');
  }, [user]);

  const login = (userId: number, phone: string, name: string | null, token: string) => {
    setUser({ userId, phone, name, token });
  };

  const logout = () => {
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, isLoggedIn: !!user }}>
      {children}
    </AuthContext.Provider>
  );
}
