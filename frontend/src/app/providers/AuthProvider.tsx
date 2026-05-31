import { useEffect, useState, type ReactNode } from 'react';

import { AuthContext, type AuthUser, type UserRole } from './auth-context';

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

  const userId = import.meta.env.VITE_DEV_USER_ID ?? '';
  const role = (import.meta.env.VITE_DEV_USER_ROLE ?? 'traveler') as UserRole;

  return {
    userId,
    phone: import.meta.env.VITE_DEV_USER_PHONE ?? '+15550000001',
    name: import.meta.env.VITE_DEV_USER_NAME ?? 'Dev Traveler',
    token: import.meta.env.VITE_DEV_TOKEN ?? '',
    role,
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

  const login = (userId: string, phone: string, name: string | null, token: string, role: UserRole) => {
    const newUser = { userId, phone, name, token, role };
    localStorage.setItem('parrot_user', JSON.stringify(newUser));
    setUser(newUser);
  };

  const logout = () => {
    localStorage.removeItem('parrot_user');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, isLoggedIn: !!user }}>
      {children}
    </AuthContext.Provider>
  );
}
