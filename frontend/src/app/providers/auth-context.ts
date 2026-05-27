import { createContext, useContext } from 'react';

export type UserRole = 'traveler' | 'staff';

export interface AuthUser {
  userId: string;
  phone: string;
  name: string | null;
  token: string;
  role: UserRole;
}

export interface AuthContextType {
  user: AuthUser | null;
  login: (userId: string, phone: string, name: string | null, token: string, role: UserRole) => void;
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
