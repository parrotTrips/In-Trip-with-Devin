import { createContext, useContext } from 'react';

export interface AuthUser {
  userId: number;
  phone: string;
  name: string | null;
}

export interface AuthContextType {
  user: AuthUser | null;
  login: (userId: number, phone: string, name: string | null) => void;
  logout: () => void;
  isLoggedIn: boolean;
}

export const AuthContext = createContext<AuthContextType>({
  user: null,
  login: () => {},
  logout: () => {},
  isLoggedIn: false,
});

export function useAuth() {
  return useContext(AuthContext);
}
