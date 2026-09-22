import { googleLogout } from '@react-oauth/google';
import { useEffect, useState, type ReactNode } from 'react';

import type { ConsoleConfig } from '../config';
import {
  acceptCredential,
  clearCredential,
  restoreCredential,
  subscribeSession,
  type GooglePrincipal,
} from './google-session';
import { AuthContext } from './auth-context';

const localPrincipal: GooglePrincipal = {
  sub: 'local-console',
  email: 'local@parrottrips.com',
  credential: '',
  expiresAt: Number.MAX_SAFE_INTEGER,
};

export function AuthProvider({
  children,
  config,
}: {
  children: ReactNode;
  config: ConsoleConfig;
}) {
  const readPrincipal = () => config.localBypass
    ? localPrincipal
    : restoreCredential(config.allowedEmailDomain);
  const [principal, setPrincipal] = useState<GooglePrincipal | null>(readPrincipal);

  useEffect(() => subscribeSession(() => setPrincipal(readPrincipal())), [config]);

  const login = (credential: string) => {
    const accepted = acceptCredential(credential, config.allowedEmailDomain);
    setPrincipal(accepted);
    return accepted !== null;
  };

  const logout = () => {
    clearCredential();
    googleLogout();
    setPrincipal(config.localBypass ? localPrincipal : null);
  };

  return (
    <AuthContext.Provider value={{
      principal, config, login, logout, isLoggedIn: principal !== null,
    }}>
      {children}
    </AuthContext.Provider>
  );
}
