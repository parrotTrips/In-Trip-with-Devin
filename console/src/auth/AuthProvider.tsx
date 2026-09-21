import { useState, type ReactNode } from 'react';

import { STORAGE_KEY } from '../api/client';
import { AuthContext, type AuthUser } from './auth-context';

function getStoredUser(): AuthUser | null {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored ? (JSON.parse(stored) as AuthUser) : null;
  } catch {
    return null;
  }
}

/** Skips the OTP screen while developing locally.
 *
 * Guarded by import.meta.env.DEV, so a production build can never take this
 * path however the variables are set. Mirrors the traveler app's dev login.
 */
function getDevAutoLoginUser(): AuthUser | null {
  if (!import.meta.env.DEV || import.meta.env.VITE_DEV_AUTO_LOGIN !== 'true') {
    return null;
  }
  return {
    userId: import.meta.env.VITE_DEV_USER_ID ?? 'dev-admin',
    phone: import.meta.env.VITE_DEV_USER_PHONE ?? '+5511999000001',
    name: import.meta.env.VITE_DEV_USER_NAME ?? 'Admin Demo',
    token: import.meta.env.VITE_DEV_TOKEN ?? '',
    role: 'admin',
  };
}

export function AuthProvider({ children }: { children: ReactNode }) {
  // The HTTP client reads the token from localStorage, so the dev auto-login
  // must land there during initialisation — not in an effect. Child effects
  // run before the parent's, so a child fetching on mount would otherwise go
  // out without an Authorization header.
  const [user, setUser] = useState<AuthUser | null>(() => {
    const stored = getStoredUser();
    if (stored) return stored;

    const devUser = getDevAutoLoginUser();
    if (devUser) localStorage.setItem(STORAGE_KEY, JSON.stringify(devUser));
    return devUser;
  });

  const login = (newUser: AuthUser) => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(newUser));
    setUser(newUser);
  };

  const logout = () => {
    localStorage.removeItem(STORAGE_KEY);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, isLoggedIn: !!user }}>
      {children}
    </AuthContext.Provider>
  );
}
