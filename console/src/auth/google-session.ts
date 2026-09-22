export const GOOGLE_CREDENTIAL_KEY = 'parrot_console_google_credential';

export type GooglePrincipal = {
  sub: string;
  email: string;
  credential: string;
  expiresAt: number;
};

const listeners = new Set<() => void>();

function notify() {
  listeners.forEach(listener => listener());
}

function decodeCredential(credential: string, domain: string): GooglePrincipal | null {
  try {
    const segments = credential.split('.');
    if (segments.length !== 3) return null;
    const base64 = segments[1].replace(/-/g, '+').replace(/_/g, '/');
    const payload = JSON.parse(atob(base64)) as {
      sub?: unknown; email?: unknown; exp?: unknown;
    };
    if (typeof payload.sub !== 'string' || !payload.sub) return null;
    if (typeof payload.email !== 'string') return null;
    const email = payload.email.toLowerCase();
    if (!email.endsWith(`@${domain}`)) return null;
    if (typeof payload.exp !== 'number' || payload.exp <= Date.now() / 1000) return null;
    return { sub: payload.sub, email, credential, expiresAt: payload.exp };
  } catch {
    return null;
  }
}

export function acceptCredential(credential: string, domain: string): GooglePrincipal | null {
  const principal = decodeCredential(credential, domain);
  if (!principal) return null;
  sessionStorage.setItem(GOOGLE_CREDENTIAL_KEY, credential);
  notify();
  return principal;
}

export function restoreCredential(domain: string): GooglePrincipal | null {
  const credential = sessionStorage.getItem(GOOGLE_CREDENTIAL_KEY);
  if (!credential) return null;
  const principal = decodeCredential(credential, domain);
  if (!principal) {
    sessionStorage.removeItem(GOOGLE_CREDENTIAL_KEY);
    notify();
  }
  return principal;
}

export function currentCredential(): string | null {
  return sessionStorage.getItem(GOOGLE_CREDENTIAL_KEY);
}

export function clearCredentialIfCurrent(expected: string): boolean {
  if (currentCredential() !== expected) return false;
  sessionStorage.removeItem(GOOGLE_CREDENTIAL_KEY);
  notify();
  return true;
}

export function clearCredential(): void {
  if (currentCredential() === null) return;
  sessionStorage.removeItem(GOOGLE_CREDENTIAL_KEY);
  notify();
}

export function subscribeSession(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}
