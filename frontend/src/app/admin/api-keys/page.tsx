'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Copy, KeyRound, Plus, ShieldCheck, Trash2, UserPlus, Users } from 'lucide-react';
import PaginationControls from '@/components/admin/PaginationControls';
import { useAdminAuth } from '@/contexts/AdminAuthContext';
import {
  createApiKey,
  createManagedUser,
  fetchApiKeys,
  fetchManagedUsers,
  revokeApiKey,
  revokeManagedUser,
} from '@/lib/admin-api';
import type { ApiKeyRecord, ManagedUserRecord } from '@/types/admin';

function formatDateTime(value?: string | null) {
  if (!value) {
    return 'Not yet';
  }
  return new Date(value).toLocaleString();
}

function formatRole(value: string) {
  if (value === 'superuser') {
    return 'Superuser';
  }
  if (value === 'admin') {
    return 'Admin';
  }
  if (value === 'uploader') {
    return 'Uploader';
  }
  return value;
}

export default function AdminApiKeysPage() {
  const router = useRouter();
  const { user, isLoading: authLoading } = useAdminAuth();
  const [apiKeys, setApiKeys] = useState<ApiKeyRecord[]>([]);
  const [users, setUsers] = useState<ManagedUserRecord[]>([]);

  const [keyName, setKeyName] = useState('');
  const [keyDescription, setKeyDescription] = useState('');
  const [generatedKey, setGeneratedKey] = useState<string | null>(null);

  const [userEmail, setUserEmail] = useState('');
  const [userPassword, setUserPassword] = useState('');
  const [userFullName, setUserFullName] = useState('');

  const [loading, setLoading] = useState(true);
  const [submittingKey, setSubmittingKey] = useState(false);
  const [submittingUser, setSubmittingUser] = useState(false);
  const [revokingId, setRevokingId] = useState<number | null>(null);
  const [revokingUserId, setRevokingUserId] = useState<number | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [userPage, setUserPage] = useState(1);
  const [keyPage, setKeyPage] = useState(1);
  const userPageSize = 5;
  const keyPageSize = 5;

  const canManageAccess = ['admin', 'superuser'].includes(user?.role ?? '');

  const loadAccessData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [userRecords, keyRecords] = await Promise.all([
        fetchManagedUsers(),
        fetchApiKeys(),
      ]);
      setUsers(userRecords);
      setApiKeys(keyRecords);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'Failed to load access settings');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (authLoading) {
      return;
    }
    if (!canManageAccess) {
      router.replace('/admin/collections');
      return;
    }
    void loadAccessData();
  }, [authLoading, canManageAccess, router]);

  useEffect(() => {
    const totalPages = Math.max(1, Math.ceil(users.length / userPageSize));
    if (userPage > totalPages) {
      setUserPage(totalPages);
    }
  }, [userPage, users.length]);

  useEffect(() => {
    const totalPages = Math.max(1, Math.ceil(apiKeys.length / keyPageSize));
    if (keyPage > totalPages) {
      setKeyPage(totalPages);
    }
  }, [apiKeys.length, keyPage]);

  if (authLoading) {
    return null;
  }

  if (!canManageAccess) {
    return (
      <div className="rounded-[28px] border border-[#0A2342]/8 bg-white p-6 shadow-[0_18px_55px_rgba(10,35,66,0.05)]">
        <p className="text-xs uppercase tracking-[0.28em] text-[#0A2342]/45">Redirecting</p>
        <h1 className="mt-3 text-2xl font-semibold text-[#0A2342]">This page is for admins only</h1>
        <p className="mt-3 max-w-2xl text-sm leading-6 text-[#0A2342]/65">
          Uploaders cannot manage access, accounts, or API keys. You are being returned to Collections now.
        </p>
        <Link
          href="/admin/collections"
          className="mt-5 inline-flex items-center rounded-2xl bg-[#00CED1] px-4 py-3 text-sm font-medium text-white shadow-[0_12px_30px_rgba(0,206,209,0.22)] hover:bg-[#00b8bb]"
        >
          Go to Collections
        </Link>
      </div>
    );
  }

  const handleCreateKey = async () => {
    if (!keyName.trim()) {
      setError('Give the key a simple label first.');
      return;
    }

    setSubmittingKey(true);
    setError(null);
    setMessage(null);

    try {
      const response = await createApiKey({
        name: keyName.trim(),
        description: keyDescription.trim() || undefined,
      });
      setGeneratedKey(response.api_key);
      setMessage(`Created API key "${response.record.name}". Copy it now because it will not be shown again.`);
      setKeyName('');
      setKeyDescription('');
      await loadAccessData();
    } catch (createError) {
      setError(createError instanceof Error ? createError.message : 'Failed to create API key');
    } finally {
      setSubmittingKey(false);
    }
  };

  const handleCreateUser = async () => {
    if (!userEmail.trim() || !userPassword.trim()) {
      setError('Email and password are required to create a user.');
      return;
    }

    setSubmittingUser(true);
    setError(null);
    setMessage(null);

    try {
      const record = await createManagedUser({
        email: userEmail.trim(),
        password: userPassword,
        fullName: userFullName.trim() || undefined,
      });
      setMessage(`Created ${formatRole(record.role).toLowerCase()} account for ${record.email}.`);
      setUserEmail('');
      setUserPassword('');
      setUserFullName('');
      await loadAccessData();
    } catch (createError) {
      setError(createError instanceof Error ? createError.message : 'Failed to create user');
    } finally {
      setSubmittingUser(false);
    }
  };

  const handleRevoke = async (keyId: number) => {
    setRevokingId(keyId);
    setError(null);
    setMessage(null);
    try {
      const revoked = await revokeApiKey(keyId);
      setMessage(`Revoked API key "${revoked.name}".`);
      await loadAccessData();
    } catch (revokeError) {
      setError(revokeError instanceof Error ? revokeError.message : 'Failed to revoke API key');
    } finally {
      setRevokingId(null);
    }
  };

  const handleRevokeUser = async (userId: number) => {
    setRevokingUserId(userId);
    setError(null);
    setMessage(null);
    try {
      const revoked = await revokeManagedUser(userId);
      setMessage(`Revoked access for "${revoked.email}".`);
      await loadAccessData();
    } catch (revokeError) {
      setError(
        revokeError instanceof Error ? revokeError.message : 'Failed to revoke user access',
      );
    } finally {
      setRevokingUserId(null);
    }
  };

  const handleCopy = async () => {
    if (!generatedKey) {
      return;
    }
    try {
      await navigator.clipboard.writeText(generatedKey);
      setMessage('API key copied to clipboard.');
    } catch {
      setError('Could not copy the key automatically. Select and copy it manually.');
    }
  };

  const paginatedUsers = users.slice((userPage - 1) * userPageSize, userPage * userPageSize);
  const paginatedKeys = apiKeys.slice((keyPage - 1) * keyPageSize, keyPage * keyPageSize);
  const userTotalPages = Math.max(1, Math.ceil(users.length / userPageSize));
  const keyTotalPages = Math.max(1, Math.ceil(apiKeys.length / keyPageSize));

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 rounded-[30px] border border-[#0A2342]/8 bg-[linear-gradient(135deg,#ecfbfc_0%,#fffaf3_100%)] p-6 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.28em] text-[#0A2342]/45">Access</p>
          <h1 className="mt-3 text-3xl font-semibold text-[#0A2342]">Provision people and keys</h1>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-[#0A2342]/60">
            Admins can create uploader accounts and provision API keys for scripts and connectors.
          </p>
        </div>
        <div className="rounded-[22px] border border-[#0A2342]/10 bg-white px-4 py-3 text-sm text-[#0A2342]/65">
          Uploaders can work with collections. Only admins can manage access.
        </div>
      </div>

      {message ? (
        <div className="rounded-[24px] border border-emerald-200 bg-emerald-50 px-5 py-4 text-sm text-emerald-800">
          {message}
        </div>
      ) : null}

      {error ? (
        <div className="rounded-[24px] border border-rose-200 bg-rose-50 px-5 py-4 text-sm text-rose-700">
          {error}
        </div>
      ) : null}

      <div className="grid gap-6 xl:grid-cols-2">
        <section className="rounded-[30px] border border-[#0A2342]/8 bg-white p-6 shadow-[0_18px_55px_rgba(10,35,66,0.05)]">
          <div className="flex items-center gap-3">
            <div className="rounded-2xl bg-[#00CED1]/12 p-3">
              <UserPlus className="h-5 w-5 text-[#0A2342]" />
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.24em] text-[#0A2342]/45">People</p>
              <h2 className="mt-1 text-xl font-semibold text-[#0A2342]">Create an account</h2>
            </div>
          </div>

          <div className="mt-6 space-y-4">
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-[#0A2342]/70">Full name</span>
              <input
                value={userFullName}
                onChange={(event) => setUserFullName(event.target.value)}
                placeholder="Local uploader"
                className="w-full rounded-2xl border border-[#0A2342]/10 bg-[#f8fcfc] px-4 py-3 text-sm text-[#0A2342] outline-none placeholder:text-[#0A2342]/25"
              />
            </label>

            <label className="block">
              <span className="mb-2 block text-sm font-medium text-[#0A2342]/70">Email</span>
              <input
                type="email"
                value={userEmail}
                onChange={(event) => setUserEmail(event.target.value)}
                placeholder="uploader@bahamasopendata.com"
                className="w-full rounded-2xl border border-[#0A2342]/10 bg-[#f8fcfc] px-4 py-3 text-sm text-[#0A2342] outline-none placeholder:text-[#0A2342]/25"
              />
            </label>

            <label className="block">
              <span className="mb-2 block text-sm font-medium text-[#0A2342]/70">Password</span>
              <input
                type="password"
                value={userPassword}
                onChange={(event) => setUserPassword(event.target.value)}
                placeholder="At least 12 characters, uppercase, lowercase, and a number"
                className="w-full rounded-2xl border border-[#0A2342]/10 bg-[#f8fcfc] px-4 py-3 text-sm text-[#0A2342] outline-none placeholder:text-[#0A2342]/25"
              />
            </label>

            <div className="rounded-[22px] border border-[#00CED1]/16 bg-[#f3fcfc] px-4 py-3 text-sm leading-6 text-[#0A2342]/60">
              New accounts created here are always uploader accounts.
            </div>

            <button
              type="button"
              onClick={() => void handleCreateUser()}
              disabled={submittingUser}
              className="inline-flex w-full items-center justify-center gap-2 rounded-2xl bg-[#00CED1] px-5 py-3 text-sm font-semibold text-white shadow-[0_12px_30px_rgba(0,206,209,0.22)] hover:bg-[#00b8bb] disabled:cursor-not-allowed disabled:opacity-60"
            >
              <Users className="h-4 w-4" />
              {submittingUser ? 'Creating account…' : 'Create account'}
            </button>
          </div>

          <div className="mt-6 space-y-3">
            {loading ? <p className="text-sm text-[#0A2342]/55">Loading people…</p> : null}
            {paginatedUsers.map((record) => (
              <article
                key={record.id}
                className="grid gap-4 rounded-[22px] border border-[#0A2342]/8 bg-[linear-gradient(180deg,#ffffff_0%,#fbfdfe_100%)] p-4 lg:grid-cols-[minmax(0,1fr)_auto]"
              >
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="text-sm font-semibold text-[#0A2342]">{record.full_name || record.email}</p>
                    <span className="rounded-full bg-[#0A2342]/6 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.16em] text-[#0A2342]/60">
                      {formatRole(record.role)}
                    </span>
                    <span
                      className={`rounded-full px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.16em] ${
                        record.is_active ? 'bg-emerald-100 text-emerald-700' : 'bg-[#0A2342]/8 text-[#0A2342]/55'
                      }`}
                    >
                      {record.is_active ? 'active' : 'revoked'}
                    </span>
                  </div>
                  <p className="mt-1 text-sm text-[#0A2342]/60">{record.email}</p>
                  <div className="mt-3 flex flex-wrap gap-4 text-xs text-[#0A2342]/50">
                    <span>Created {formatDateTime(record.created_at)}</span>
                    <span>Last login {formatDateTime(record.last_login_at)}</span>
                  </div>
                </div>

                <div className="flex w-full items-center justify-start gap-3 lg:w-auto lg:justify-end">
                  {record.role === 'uploader' && record.is_active ? (
                    <button
                      type="button"
                      onClick={() => void handleRevokeUser(record.id)}
                      disabled={revokingUserId === record.id}
                      className="inline-flex w-full items-center justify-center gap-2 rounded-2xl border border-rose-200 bg-white px-4 py-3 text-sm font-medium text-rose-700 hover:bg-rose-50 disabled:cursor-not-allowed disabled:opacity-60 sm:w-auto"
                    >
                      <Trash2 className="h-4 w-4" />
                      {revokingUserId === record.id ? 'Revoking…' : 'Revoke access'}
                    </button>
                  ) : (
                    <div className="inline-flex items-center gap-2 rounded-2xl border border-[#0A2342]/10 bg-white px-4 py-3 text-sm text-[#0A2342]/55">
                      <ShieldCheck className="h-4 w-4" />
                      {record.is_active ? 'Protected' : 'Inactive'}
                    </div>
                  )}
                </div>
              </article>
            ))}
          </div>

          <PaginationControls
            currentPage={userPage}
            totalPages={userTotalPages}
            totalItems={users.length}
            pageSize={userPageSize}
            itemLabel="users"
            onPageChange={setUserPage}
          />
        </section>

        <section className="rounded-[30px] border border-[#0A2342]/8 bg-white p-6 shadow-[0_18px_55px_rgba(10,35,66,0.05)]">
          <div className="flex items-center gap-3">
            <div className="rounded-2xl bg-[#00CED1]/12 p-3">
              <KeyRound className="h-5 w-5 text-[#0A2342]" />
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.24em] text-[#0A2342]/45">Keys</p>
              <h2 className="mt-1 text-xl font-semibold text-[#0A2342]">Provision API keys</h2>
            </div>
          </div>

          <div className="mt-6 space-y-4">
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-[#0A2342]/70">Key name</span>
              <input
                value={keyName}
                onChange={(event) => setKeyName(event.target.value)}
                placeholder="Budget importer"
                className="w-full rounded-2xl border border-[#0A2342]/10 bg-[#f8fcfc] px-4 py-3 text-sm text-[#0A2342] outline-none placeholder:text-[#0A2342]/25"
              />
            </label>

            <label className="block">
              <span className="mb-2 block text-sm font-medium text-[#0A2342]/70">Description</span>
              <textarea
                value={keyDescription}
                onChange={(event) => setKeyDescription(event.target.value)}
                placeholder="Used by our budget document importer."
                className="min-h-24 w-full rounded-2xl border border-[#0A2342]/10 bg-[#f8fcfc] px-4 py-3 text-sm text-[#0A2342] outline-none placeholder:text-[#0A2342]/25"
              />
            </label>

            <button
              type="button"
              onClick={() => void handleCreateKey()}
              disabled={submittingKey}
              className="inline-flex w-full items-center justify-center gap-2 rounded-2xl bg-[#00CED1] px-5 py-3 text-sm font-semibold text-white shadow-[0_12px_30px_rgba(0,206,209,0.22)] hover:bg-[#00b8bb] disabled:cursor-not-allowed disabled:opacity-60"
            >
              <Plus className="h-4 w-4" />
              {submittingKey ? 'Creating key…' : 'Create key'}
            </button>
          </div>

          {generatedKey ? (
            <div className="mt-6 rounded-[24px] border border-[#FCD116]/45 bg-[#fffbea] p-4">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div className="min-w-0">
                  <p className="text-sm font-semibold text-[#0A2342]">Copy this key now</p>
                  <p className="mt-1 text-sm leading-6 text-[#0A2342]/60">
                    The full secret is only shown once.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => void handleCopy()}
                  className="inline-flex items-center gap-2 rounded-2xl border border-[#0A2342]/10 bg-white px-4 py-3 text-sm font-medium text-[#0A2342] hover:border-[#0A2342]/20"
                >
                  <Copy className="h-4 w-4" />
                  Copy
                </button>
              </div>
              <pre className="mt-4 overflow-x-auto rounded-[18px] bg-[#1d1a17] px-4 py-4 text-xs leading-6 text-[#f8f2e9]">
                <code>{generatedKey}</code>
              </pre>
            </div>
          ) : null}

          <div className="mt-6 space-y-3">
            {loading ? <p className="text-sm text-[#0A2342]/55">Loading keys…</p> : null}
            {paginatedKeys.map((record) => (
              <article
                key={record.id}
                className="grid gap-4 rounded-[22px] border border-[#0A2342]/8 bg-[linear-gradient(180deg,#ffffff_0%,#fbfdfe_100%)] p-4 lg:grid-cols-[minmax(0,1fr)_auto]"
              >
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="text-sm font-semibold text-[#0A2342]">{record.name}</p>
                    <span
                      className={`rounded-full px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.16em] ${
                        record.is_active ? 'bg-emerald-100 text-emerald-700' : 'bg-[#0A2342]/8 text-[#0A2342]/55'
                      }`}
                    >
                      {record.is_active ? 'active' : 'revoked'}
                    </span>
                  </div>
                  <p className="mt-1 font-mono text-xs text-[#0A2342]/45">{record.key_prefix}…</p>
                  <p className="mt-3 text-sm leading-6 text-[#0A2342]/60">
                    {record.description || 'No description provided.'}
                  </p>
                  <div className="mt-3 flex flex-wrap gap-4 text-xs text-[#0A2342]/50">
                    <span>Created {formatDateTime(record.created_at)}</span>
                    <span>Last used {formatDateTime(record.last_used_at)}</span>
                  </div>
                </div>

                <div className="flex w-full items-center justify-start gap-3 lg:w-auto lg:justify-end">
                  {record.is_active ? (
                    <button
                      type="button"
                      onClick={() => void handleRevoke(record.id)}
                      disabled={revokingId === record.id}
                      className="inline-flex w-full items-center justify-center gap-2 rounded-2xl border border-rose-200 bg-white px-4 py-3 text-sm font-medium text-rose-700 hover:bg-rose-50 disabled:cursor-not-allowed disabled:opacity-60 sm:w-auto"
                    >
                      <Trash2 className="h-4 w-4" />
                      {revokingId === record.id ? 'Revoking…' : 'Revoke'}
                    </button>
                  ) : (
                    <div className="inline-flex items-center gap-2 rounded-2xl border border-[#0A2342]/10 bg-white px-4 py-3 text-sm text-[#0A2342]/55">
                      <ShieldCheck className="h-4 w-4" />
                      Inactive
                    </div>
                  )}
                </div>
              </article>
            ))}
          </div>

          <PaginationControls
            currentPage={keyPage}
            totalPages={keyTotalPages}
            totalItems={apiKeys.length}
            pageSize={keyPageSize}
            itemLabel="keys"
            onPageChange={setKeyPage}
          />
        </section>
      </div>

    </div>
  );
}
