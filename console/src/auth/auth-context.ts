import { createContext, useContext } from 'react';

import type { ConsoleConfig } from '../config';
import type { GooglePrincipal } from './google-session';

export interface AuthContextType {
  principal: GooglePrincipal | null;
  config: ConsoleConfig;
  login: (credential: string) => boolean;
  logout: () => void;
  isLoggedIn: boolean;
}

export const AuthContext = createContext<AuthContextType>({
  principal: null,
  config: { apiUrl: '', googleClientId: '', allowedEmailDomain: '', localBypass: false },
  login: () => false,
  logout: () => {},
  isLoggedIn: false,
});

export function useAuth() {
  return useContext(AuthContext);
}
