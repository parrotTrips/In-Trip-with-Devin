import { clearCredentialIfCurrent, currentCredential } from '../auth/google-session';
import { readConfig } from '../config';

export class ApiError extends Error {
  constructor(message: string, readonly status: number) {
    super(message);
    this.name = 'ApiError';
  }
}

function errorMessage(status: number, detail?: string): string {
  if (status === 401) return 'Sua sessão expirou. Entre novamente.';
  if (status === 403) return 'Conta Google sem acesso ao console.';
  if (status === 503) return 'Autenticação do console não configurada.';
  return detail || 'A API não conseguiu concluir a operação.';
}

export async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const config = readConfig();
  if (!config.ok) throw new ApiError(config.error, 0);

  const credential = currentCredential();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options?.headers as Record<string, string>),
  };
  if (credential) headers.Authorization = `Bearer ${credential}`;

  let response: Response;
  try {
    response = await fetch(`${config.value.apiUrl}${path}`, { ...options, headers });
  } catch {
    throw new ApiError('Não foi possível conectar à API.', 0);
  }

  if (!response.ok) {
    if (response.status === 401 && credential) clearCredentialIfCurrent(credential);
    const body = await response.json().catch(() => ({})) as { detail?: string };
    throw new ApiError(errorMessage(response.status, body.detail), response.status);
  }
  return response.json() as Promise<T>;
}
