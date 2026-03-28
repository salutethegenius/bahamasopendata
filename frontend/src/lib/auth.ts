import type { AdminUser, LoginResponse } from '@/types/admin';

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1';

const ACCESS_TOKEN_KEY = 'bahamas_admin_access_token';

export function getAccessToken(): string | null {
  if (typeof window === 'undefined') {
    return null;
  }
  return window.localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function setAccessToken(token: string | null): void {
  if (typeof window === 'undefined') {
    return;
  }

  if (token) {
    window.localStorage.setItem(ACCESS_TOKEN_KEY, token);
    return;
  }

  window.localStorage.removeItem(ACCESS_TOKEN_KEY);
}

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

  const payload = (await response.json()) as LoginResponse;
  setAccessToken(payload.access_token);
  return payload;
}

export async function refreshAdminSession(): Promise<string | null> {
  const response = await fetch(`${API_BASE}/auth/refresh`, {
    method: 'POST',
    credentials: 'include',
  });

  if (!response.ok) {
    setAccessToken(null);
    return null;
  }

  const payload = (await response.json()) as LoginResponse;
  setAccessToken(payload.access_token);
  return payload.access_token;
}

export async function fetchCurrentAdmin(token?: string | null): Promise<AdminUser> {
  const accessToken = token ?? getAccessToken();
  if (!accessToken) {
    throw new Error('No access token available');
  }

  const response = await fetch(`${API_BASE}/auth/me`, {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
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
    setAccessToken(null);
  }
}
