import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';

interface AuthUser {
  userId: number;
  phone: string;
  name: string | null;
}

interface AuthContextType {
  user: AuthUser | null;
  login: (userId: number, phone: string, name: string | null) => void;
  logout: () => void;
  isLoggedIn: boolean;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  login: () => {},
  logout: () => {},
  isLoggedIn: false,
});

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

export function useAuth() {
  return useContext(AuthContext);
}
