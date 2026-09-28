const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const API_AUTH_EVENT = 'parrot:api-auth-error';

export type ApiAuthEventDetail = {
  kind: 'unauthorized' | 'membership_revoked';
  path: string;
};

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly path: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

function getToken(): string | null {
  try {
    const stored = localStorage.getItem('parrot_user');
    if (!stored) return null;
    const user = JSON.parse(stored) as { token?: string };
    return user.token ?? null;
  } catch {
    return null;
  }
}

export async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options?.headers as Record<string, string>),
  };

  // Auth selection calls (listTrips/selectTrip) pass their own Authorization
  // header with the selection or session token they were handed explicitly.
  // Only fall back to the current scoped session token from localStorage
  // for ordinary app requests that didn't already supply one — otherwise a
  // stale localStorage token would silently override the caller's token.
  if (!headers['Authorization']) {
    const token = getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
  }

  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const error: unknown = await response.json().catch(() => ({ detail: response.statusText }));
    const detail = error && typeof error === 'object' && 'detail' in error && typeof error.detail === 'string'
      ? error.detail
      : 'Request failed';
    const hasSession = getToken() !== null;
    const isProtectedAppPath = path.startsWith('/me/')
      || path.startsWith('/profile/')
      || path.startsWith('/checklist/')
      || path.startsWith('/phases/')
      || path === '/auth/trips'
      || path === '/auth/select-trip';
    const kind = response.status === 401 && hasSession && isProtectedAppPath
      ? 'unauthorized'
      : response.status === 403
        && isProtectedAppPath
        && !path.startsWith('/auth/')
        && detail === 'Trip membership required'
          ? 'membership_revoked'
          : null;

    if (kind) {
      window.dispatchEvent(new CustomEvent<ApiAuthEventDetail>(API_AUTH_EVENT, {
        detail: { kind, path },
      }));
    }
    throw new ApiError(detail, response.status, path);
  }

  return response.json();
}
