export type ConsoleConfig = {
  apiUrl: string;
  googleClientId: string;
  allowedEmailDomain: string;
  localBypass: boolean;
};

type EnvSource = Record<string, string | undefined>;
export type ConfigResult =
  | { ok: true; value: ConsoleConfig }
  | { ok: false; error: string };

export function validateConfig(env: EnvSource, isDev: boolean): ConfigResult {
  const localBypass = isDev && env.VITE_ENABLE_CONSOLE_LOCAL === 'true';
  const apiUrl = env.VITE_API_URL?.trim() || (isDev ? 'http://localhost:8000' : '');
  const googleClientId = env.VITE_GOOGLE_CLIENT_ID?.trim() || '';
  const allowedEmailDomain = env.VITE_ALLOWED_EMAIL_DOMAIN?.trim().toLowerCase() || '';

  try {
    const parsed = new URL(apiUrl);
    if (!['http:', 'https:'].includes(parsed.protocol)) throw new Error('protocol');
  } catch {
    return { ok: false, error: 'VITE_API_URL precisa ser uma URL HTTP(S) válida.' };
  }
  if (!allowedEmailDomain || allowedEmailDomain.includes('@')) {
    return { ok: false, error: 'VITE_ALLOWED_EMAIL_DOMAIN não está configurado corretamente.' };
  }
  if (!localBypass && !googleClientId.endsWith('.apps.googleusercontent.com')) {
    return { ok: false, error: 'VITE_GOOGLE_CLIENT_ID não está configurado corretamente.' };
  }
  return {
    ok: true,
    value: { apiUrl: apiUrl.replace(/\/$/, ''), googleClientId, allowedEmailDomain, localBypass },
  };
}

export function readConfig(): ConfigResult {
  return validateConfig(import.meta.env, import.meta.env.DEV);
}
