import type { AdminUser, LoginResponse } from '@/types/admin';

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1';

/**
 * Access JWT is httpOnly-only (R01). Do not read tokens from JS storage.
 */
export async function loginAdmin(email: string, password: string): Promise<LoginResponse> {
  const response = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail ?? `Login failed (${response.status})`);
  }

  return (await response.json()) as LoginResponse;
}

export async function refreshAdminSession(): Promise<boolean> {
  const response = await fetch(`${API_BASE}/auth/refresh`, {
    method: 'POST',
    credentials: 'include',
  });

  return response.ok;
}

export async function fetchCurrentAdmin(): Promise<AdminUser> {
  const response = await fetch(`${API_BASE}/auth/me`, {
    credentials: 'include',
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail ?? `Failed to load session (${response.status})`);
  }

  return response.json() as Promise<AdminUser>;
}

export async function logoutAdmin(): Promise<void> {
  try {
    await fetch(`${API_BASE}/auth/logout`, {
      method: 'POST',
      credentials: 'include',
    });
  } finally {
    /* cookies cleared by API */
  }
}
