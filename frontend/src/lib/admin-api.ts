import {
  fetchCurrentAdmin,
  getAccessToken,
  refreshAdminSession,
  setAccessToken,
} from '@/lib/auth';
import type {
  AuditLogRecord,
  ApiKeyCreateResponse,
  ApiKeyRecord,
  DeleteDocumentResponse,
  DocumentReviewResponse,
  DocumentsResponse,
  FutureUpdateCard,
  IngestionRunOptions,
  ManagedUserRecord,
  IngestionStatus,
  ProcessDocumentOptions,
  ProcessDocumentResponse,
  PublishDocumentResponse,
  StructuredDataPayload,
  UploadDocumentResponse,
} from '@/types/admin';

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1';

type ApiRequestOptions = RequestInit & {
  skipAuthRetry?: boolean;
};

async function request<T>(path: string, options: ApiRequestOptions = {}): Promise<T> {
  const token = getAccessToken();
  const headers = new Headers(options.headers);

  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (response.status === 401 && !options.skipAuthRetry) {
    const refreshed = await refreshAdminSession();
    if (refreshed) {
      return request<T>(path, {
        ...options,
        skipAuthRetry: true,
      });
    }

    // Refresh failed — clear token and redirect to login
    setAccessToken(null);
    if (typeof window !== 'undefined' && !window.location.pathname.startsWith('/admin/login')) {
      window.location.href = '/admin/login';
    }
    throw new Error('Session expired');
  }

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail ?? `Request failed (${response.status})`);
  }

  return response.json() as Promise<T>;
}

export async function bootstrapAdminSession() {
  const token = getAccessToken();
  if (token) {
    try {
      return await fetchCurrentAdmin(token);
    } catch {
      // Fall through to refresh
    }
  }

  const refreshed = await refreshAdminSession();
  if (!refreshed) {
    return null;
  }

  return fetchCurrentAdmin(refreshed);
}

export function fetchAdminDocuments(): Promise<DocumentsResponse> {
  return request<DocumentsResponse>('/documents');
}

export function fetchIngestionStatus(): Promise<IngestionStatus> {
  return request<IngestionStatus>('/ingestion/status');
}

export function runIngestion(options: IngestionRunOptions): Promise<Record<string, unknown>> {
  return request<Record<string, unknown>>('/ingestion/run', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(options),
  });
}

export function processDocument(
  filename: string,
  options: ProcessDocumentOptions,
): Promise<ProcessDocumentResponse> {
  return request<ProcessDocumentResponse>(`/documents/${encodeURIComponent(filename)}/process`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(options),
  });
}

export function fetchDocumentReview(filename: string): Promise<DocumentReviewResponse> {
  return request<DocumentReviewResponse>(`/documents/${encodeURIComponent(filename)}/review`);
}

export function deleteDocument(filename: string): Promise<DeleteDocumentResponse> {
  return request<DeleteDocumentResponse>(`/documents/${encodeURIComponent(filename)}`, {
    method: 'DELETE',
  });
}

export function submitDocumentReview(
  filename: string,
  payload?: { review_notes?: string },
): Promise<DocumentReviewResponse> {
  return request<DocumentReviewResponse>(`/documents/${encodeURIComponent(filename)}/submit`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload ?? {}),
  });
}

export function unapproveDocumentReview(filename: string): Promise<DocumentReviewResponse> {
  return request<DocumentReviewResponse>(`/documents/${encodeURIComponent(filename)}/unapprove`, {
    method: 'POST',
  });
}

export function publishDocument(filename: string): Promise<PublishDocumentResponse> {
  return request<PublishDocumentResponse>(`/documents/${encodeURIComponent(filename)}/publish`, {
    method: 'POST',
  });
}

export async function uploadDocument(payload: {
  file: File;
  documentType?: string;
  fiscalYear?: string;
  sourceUrl?: string;
  autoProcess?: boolean;
  enableAiScan?: boolean;
  enableSearchIndexing?: boolean;
  forceProcess?: boolean;
}): Promise<UploadDocumentResponse> {
  const formData = new FormData();
  formData.set('file', payload.file);
  if (payload.documentType) {
    formData.set('document_type', payload.documentType);
  }
  if (payload.fiscalYear) {
    formData.set('fiscal_year', payload.fiscalYear);
  }
  if (payload.sourceUrl) {
    formData.set('source_url', payload.sourceUrl);
  }
  if (payload.autoProcess) {
    formData.set('auto_process', 'true');
  }
  if (payload.enableAiScan) {
    formData.set('enable_ai_scan', 'true');
  }
  if (payload.enableSearchIndexing) {
    formData.set('enable_search_indexing', 'true');
  }
  if (payload.forceProcess) {
    formData.set('force_process', 'true');
  }

  return request<UploadDocumentResponse>('/documents/upload', {
    method: 'POST',
    body: formData,
  });
}

export function uploadStructuredData(payload: {
  title?: string;
  documentType: string;
  fiscalYear?: string;
  sourceUrl?: string;
  structuredData: StructuredDataPayload;
  reviewNotes?: string;
  submitAfterUpload?: boolean;
}): Promise<UploadDocumentResponse> {
  return request<UploadDocumentResponse>('/documents/upload-structured', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      title: payload.title,
      document_type: payload.documentType,
      fiscal_year: payload.fiscalYear,
      source_url: payload.sourceUrl,
      structured_data: payload.structuredData,
      review_notes: payload.reviewNotes,
      submit_after_upload: payload.submitAfterUpload ?? false,
    }),
  });
}

export function getAdminDocumentUrl(filename: string) {
  return `${API_BASE}/documents/${encodeURIComponent(filename)}`;
}

export function fetchApiKeys(): Promise<ApiKeyRecord[]> {
  return request<ApiKeyRecord[]>('/auth/api-keys');
}

export function createApiKey(payload: {
  name: string;
  description?: string;
}): Promise<ApiKeyCreateResponse> {
  return request<ApiKeyCreateResponse>('/auth/api-keys', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
}

export function revokeApiKey(keyId: number): Promise<ApiKeyRecord> {
  return request<ApiKeyRecord>(`/auth/api-keys/${keyId}/revoke`, {
    method: 'POST',
  });
}

export function fetchManagedUsers(): Promise<ManagedUserRecord[]> {
  return request<ManagedUserRecord[]>('/auth/users');
}

export function createManagedUser(payload: {
  email: string;
  password: string;
  fullName?: string;
}): Promise<ManagedUserRecord> {
  return request<ManagedUserRecord>('/auth/users', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      email: payload.email,
      password: payload.password,
      full_name: payload.fullName,
    }),
  });
}

export function revokeManagedUser(userId: number): Promise<ManagedUserRecord> {
  return request<ManagedUserRecord>(`/auth/users/${userId}/revoke`, {
    method: 'POST',
  });
}

export function fetchAuditLog(options?: {
  limit?: number;
  search?: string;
  action?: string;
  actorType?: string;
}): Promise<AuditLogRecord[]> {
  const params = new URLSearchParams({
    limit: String(options?.limit ?? 30),
  });
  if (options?.search) {
    params.set('search', options.search);
  }
  if (options?.action) {
    params.set('action', options.action);
  }
  if (options?.actorType) {
    params.set('actor_type', options.actorType);
  }
  return request<AuditLogRecord[]>(`/auth/audit-log?${params.toString()}`);
}

export function fetchFutureUpdates(): Promise<FutureUpdateCard[]> {
  return request<FutureUpdateCard[]>('/future-updates');
}

export function updateFutureUpdates(payload: FutureUpdateCard[]): Promise<FutureUpdateCard[]> {
  return request<FutureUpdateCard[]>('/future-updates', {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
}
