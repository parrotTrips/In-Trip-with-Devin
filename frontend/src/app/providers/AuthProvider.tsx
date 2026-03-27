import { useEffect, useState, type ReactNode } from 'react';

import { AuthContext, type AuthUser } from './auth-context';

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(() => {
    const stored = localStorage.getItem('parrot_user');
    return stored ? JSON.parse(stored) : null;
  });

  useEffect(() => {
    if (user) {
      localStorage.setItem('parrot_user', JSON.stringify(user));
      return;
    }

    localStorage.removeItem('parrot_user');
  }, [user]);

  const login = (userId: number, phone: string, name: string | null) => {
    setUser({ userId, phone, name });
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
