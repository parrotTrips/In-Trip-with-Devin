import { createContext, useContext } from 'react';

export interface AuthUser {
  userId: number;
  phone: string;
  name: string | null;
  token: string;
}

export interface AuthContextType {
  user: AuthUser | null;
  login: (userId: number, phone: string, name: string | null, token: string) => void;
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
