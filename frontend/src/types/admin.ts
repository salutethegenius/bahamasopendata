export type AdminUser = {
  id: number;
  email: string;
  full_name: string | null;
  role: string;
  is_active: boolean;
};

export type LoginResponse = {
  token_type: string;
  expires_in: number;
  user: AdminUser;
};

export type DocumentRecord = {
  filename: string;
  original_filename: string | null;
  original_url: string | null;
  document_type: string | null;
  fiscal_year: string | null;
  upload_source: string | null;
  extraction_status: string | null;
  file_size: number | null;
  downloaded_at: string | null;
  chunk_count: number | null;
  normalization_status: string | null;
  normalized_count: number | null;
  embedding_status: string | null;
  embedding_count: number | null;
  review_status: string | null;
  reviewed_at: string | null;
  submitted_at: string | null;
  publish_status?: string | null;
  published_at?: string | null;
  review_notes: string | null;
  exists_on_disk: boolean;
};

export type DocumentsResponse = {
  documents: DocumentRecord[];
};

export type UploadDocumentResponse = {
  document: DocumentRecord;
  duplicate: boolean;
  processing?: ProcessDocumentResponse | null;
};

export type DeleteDocumentResponse = {
  filename: string;
  deleted: boolean;
  storage: Record<string, number>;
  published_rows: Record<string, number>;
};

export type StructuredDataPayload = {
  source_document?: string | null;
  title?: string | null;
  document_type: string;
  fiscal_year?: string | null;
  executive_summary?: string;
  ministries?: string[];
  extracted_items?: Array<Record<string, unknown>>;
  notable_topics?: string[];
  warnings?: string[];
  confidence?: number;
  needs_review?: boolean;
};

export type ProcessDocumentOptions = {
  run_parser?: boolean;
  run_normalizer?: boolean;
  enable_ai_scan?: boolean;
  run_embeddings?: boolean;
  enable_search_indexing?: boolean;
  force?: boolean;
};

export type ProcessDocumentResponse = {
  filename: string;
  status: string;
  stages: Record<string, Record<string, unknown>>;
};

export type DocumentReviewPagePreview = {
  page_number: number;
  text: string;
  char_count: number | null;
};

export type DocumentReviewTablePreview = {
  page_number: number | null;
  columns: string[];
  rows: Array<Array<string | number | null>>;
};

export type DocumentReviewResponse = {
  document: DocumentRecord;
  extraction: {
    available: boolean;
    status: string;
    page_count: number;
    table_count: number;
    chunk_count: number;
    sample_pages: DocumentReviewPagePreview[];
    sample_tables: DocumentReviewTablePreview[];
  };
  ai_processing: {
    available: boolean;
    status: string;
    model: string | null;
    confidence: number | null;
    needs_review: boolean | null;
    executive_summary: string | null;
    ministries: string[];
    notable_topics: string[];
    warnings: string[];
    extracted_item_count: number;
    preview_json: Record<string, unknown> | null;
  };
  submission: {
    can_submit: boolean;
    can_publish: boolean;
    can_unapprove: boolean;
    review_status: string;
    reviewed_at: string | null;
    submitted_at: string | null;
    publish_status: string | null;
    published_at: string | null;
    review_notes: string | null;
  };
};

export type PublishDocumentResponse = {
  filename: string;
  publish_status: string;
  published_at: string | null;
  published_records: Record<string, number>;
  warnings: string[];
};

export type IngestionRunOptions = {
  run_scraper?: boolean;
  run_parser?: boolean;
  run_normalizer?: boolean;
  run_embeddings?: boolean;
  force?: boolean;
};

export type IngestionStatus = {
  status: string;
  updated_at: string | null;
  latest_run: Record<string, unknown> | null;
  documents: {
    document_count: number;
    extraction_pending: number;
    extraction_success: number;
    embedding_success: number;
    normalization_success: number;
  };
};

export type ApiKeyRecord = {
  id: number;
  name: string;
  description: string | null;
  key_prefix: string;
  is_active: boolean;
  created_at: string | null;
  last_used_at: string | null;
  revoked_at: string | null;
};

export type ApiKeyCreateResponse = {
  api_key: string;
  record: ApiKeyRecord;
};

export type ManagedUserRecord = {
  id: number;
  email: string;
  full_name: string | null;
  role: string;
  is_active: boolean;
  created_at: string | null;
  last_login_at: string | null;
};

export type AuditLogRecord = {
  id: number;
  action: string;
  resource_type: string;
  resource_id: string | null;
  actor_label: string;
  actor_role: string | null;
  actor_type: string;
  ip_address: string | null;
  created_at: string | null;
  details: Record<string, unknown> | null;
};

export type PaginationState = {
  currentPage: number;
  totalPages: number;
  totalItems: number;
  pageSize: number;
};

export type FutureUpdateCard = {
  id: string;
  title: string;
  phase: string;
  description: string;
  items: string[];
};
