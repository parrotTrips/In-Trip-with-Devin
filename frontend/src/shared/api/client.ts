const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

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
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || 'Request failed');
  }

  return response.json();
}
