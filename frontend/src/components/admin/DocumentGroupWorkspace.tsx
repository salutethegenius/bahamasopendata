'use client';

import Link from 'next/link';
import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  ChevronRight,
  ExternalLink,
  FileJson,
  FolderTree,
  Sparkles,
  Upload,
} from 'lucide-react';
import PaginationControls from '@/components/admin/PaginationControls';
import { useAdminAuth } from '@/contexts/AdminAuthContext';
import {
  deleteDocument,
  fetchAdminDocuments,
  fetchDocumentReview,
  getAdminDocumentUrl,
  publishDocument,
  processDocument,
  submitDocumentReview,
  unapproveDocumentReview,
  uploadDocument,
  uploadStructuredData,
} from '@/lib/admin-api';
import {
  formatDocumentType,
  getDocumentTypeDetails,
  getSectionById,
  getSectionDocuments,
  type AdminSectionId,
  type DocumentType,
} from '@/lib/admin-collections';
import type { DocumentRecord, DocumentReviewResponse, StructuredDataPayload } from '@/types/admin';

type DocumentGroupWorkspaceProps = {
  sectionId: AdminSectionId;
  documentType: DocumentType;
  mode?: 'overview' | 'manual' | 'files' | 'api';
};

function formatDate(value?: string | null) {
  if (!value) {
    return 'Unknown date';
  }
  return new Date(value).toLocaleDateString();
}

function formatDateTime(value?: string | null) {
  if (!value) {
    return 'Not yet';
  }
  return new Date(value).toLocaleString();
}

function formatStatus(value?: string | null) {
  if (!value) {
    return 'Waiting';
  }
  return value.replaceAll('_', ' ');
}

function getReviewStatusTone(value?: string | null) {
  if (value === 'approved' || value === 'submitted') {
    return 'border-emerald-200 bg-emerald-50 text-emerald-700';
  }

  if (value === 'pending_review' || value === 'rejected') {
    return 'border-rose-200 bg-rose-50 text-rose-700';
  }

  return 'border-amber-200 bg-amber-50 text-amber-700';
}

function getPublishStatusTone(value?: string | null) {
  if (value === 'success') {
    return 'border-emerald-200 bg-emerald-50 text-emerald-700';
  }
  if (value === 'failed' || value === 'error') {
    return 'border-rose-200 bg-rose-50 text-rose-700';
  }
  return 'border-amber-200 bg-amber-50 text-amber-700';
}

function buildExtractionExample(review: DocumentReviewResponse | null) {
  if (!review) {
    return null;
  }

  if (review.extraction.sample_tables.length > 0) {
    const table = review.extraction.sample_tables[0];
    return {
      page_number: table.page_number,
      columns: table.columns,
      rows: table.rows,
    };
  }

  if (review.extraction.sample_pages.length > 0) {
    const page = review.extraction.sample_pages[0];
    return {
      page_number: page.page_number,
      text: page.text,
      char_count: page.char_count,
    };
  }

  return null;
}

function getExpectedString(
  example: Record<string, unknown>,
  key: string,
  fallback: string,
) {
  const value = example[key];
  return typeof value === 'string' && value.trim().length > 0 ? value : fallback;
}

function getExpectedOptionalString(example: Record<string, unknown>, key: string) {
  const value = example[key];
  return typeof value === 'string' && value.trim().length > 0 ? value : null;
}

function buildStructuredUploadExample(
  documentType: DocumentType,
  details: ReturnType<typeof getDocumentTypeDetails>,
  document?: DocumentRecord,
) {
  const title = getExpectedOptionalString(details.expectedExample, 'title');
  const fiscalYear =
    document?.fiscal_year || getExpectedOptionalString(details.expectedExample, 'fiscal_year');
  const sourceUrl = document?.original_url || 'https://source.example.gov.bs/document.pdf';

  return `POST /api/v1/documents/upload-structured
${JSON.stringify(
    {
      title,
      document_type: documentType,
      fiscal_year: fiscalYear,
      source_url: sourceUrl,
      structured_data: details.expectedExample,
      review_notes: 'Imported as structured data for review.',
      submit_after_upload: false,
    },
    null,
    2,
  )}`;
}

function buildReviewExample(
  document?: DocumentRecord,
  details?: ReturnType<typeof getDocumentTypeDetails>,
) {
  const filename =
    document?.filename ||
    getExpectedString(details?.expectedExample ?? {}, 'source_document', 'document.pdf');

  return {
    process: `POST /api/v1/documents/${filename}/process
{
  "run_parser": true,
  "enable_ai_scan": true,
  "enable_search_indexing": false,
  "force": false
}`,
    review: `GET /api/v1/documents/${filename}/review`,
  };
}

export default function DocumentGroupWorkspace({
  sectionId,
  documentType,
  mode = 'overview',
}: DocumentGroupWorkspaceProps) {
  const section = getSectionById(sectionId);
  const details = getDocumentTypeDetails(documentType);
  const typeBasePath = `/admin/collections/${sectionId}/groups/${documentType}`;
  const { user } = useAdminAuth();
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [selectedFilename, setSelectedFilename] = useState<string | null>(null);
  const [selectedReview, setSelectedReview] = useState<DocumentReviewResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [reviewLoading, setReviewLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [pdfInputKey, setPdfInputKey] = useState(0);
  const [pdfFiscalYear, setPdfFiscalYear] = useState(
    getExpectedOptionalString(details.expectedExample, 'fiscal_year') ?? '',
  );
  const [pdfSourceUrl, setPdfSourceUrl] = useState('');
  const [structuredTitle, setStructuredTitle] = useState(
    getExpectedOptionalString(details.expectedExample, 'title') ?? '',
  );
  const [structuredFiscalYear, setStructuredFiscalYear] = useState(
    getExpectedOptionalString(details.expectedExample, 'fiscal_year') ?? '',
  );
  const [structuredSourceUrl, setStructuredSourceUrl] = useState('');
  const [structuredJson, setStructuredJson] = useState(
    JSON.stringify(details.expectedExample, null, 2),
  );
  const [reviewNotes, setReviewNotes] = useState('');
  const [openManualPanel, setOpenManualPanel] = useState<'pdf' | 'json' | 'review'>(
    mode === 'manual' || mode === 'files' ? 'review' : 'pdf',
  );
  const pageSize = 6;

  const loadDocumentReview = useCallback(async (filename: string) => {
    setReviewLoading(true);
    try {
      const review = await fetchDocumentReview(filename);
      setSelectedReview(review);
      setReviewNotes(review.submission.review_notes ?? '');
    } finally {
      setReviewLoading(false);
    }
  }, []);

  const loadDocuments = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetchAdminDocuments();
      const typeDocuments = getSectionDocuments(response.documents, sectionId).filter(
        (document) => (document.document_type ?? 'other') === documentType,
      );
      setDocuments(typeDocuments);

      const nextSelected =
        typeDocuments.find((document) => document.filename === selectedFilename)?.filename ??
        typeDocuments[0]?.filename ??
        null;
      setSelectedFilename(nextSelected);

      if (nextSelected) {
        await loadDocumentReview(nextSelected);
      } else {
        setSelectedReview(null);
        setReviewNotes('');
      }
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'Failed to load record type');
    } finally {
      setLoading(false);
    }
  }, [documentType, loadDocumentReview, sectionId, selectedFilename]);

  useEffect(() => {
    void loadDocuments();
  }, [loadDocuments]);

  useEffect(() => {
    setPdfFiscalYear(getExpectedOptionalString(details.expectedExample, 'fiscal_year') ?? '');
    setStructuredTitle(getExpectedOptionalString(details.expectedExample, 'title') ?? '');
    setStructuredFiscalYear(getExpectedOptionalString(details.expectedExample, 'fiscal_year') ?? '');
    setStructuredJson(JSON.stringify(details.expectedExample, null, 2));
    setPdfSourceUrl('');
    setStructuredSourceUrl('');
    setPdfFile(null);
    setPdfInputKey((current) => current + 1);
    setActionMessage(null);
    setCurrentPage(1);
    setOpenManualPanel('pdf');
  }, [details, documentType]);

  useEffect(() => {
    const totalPages = Math.max(1, Math.ceil(documents.length / pageSize));
    if (currentPage > totalPages) {
      setCurrentPage(totalPages);
    }
  }, [currentPage, documents.length]);

  const totalPages = Math.max(1, Math.ceil(documents.length / pageSize));
  const paginatedDocuments = documents.slice(
    (currentPage - 1) * pageSize,
    currentPage * pageSize,
  );
  const extractionExample = useMemo(
    () => buildExtractionExample(selectedReview),
    [selectedReview],
  );
  const primaryDocument = documents[0];
  const apiExamples = useMemo(
    () => ({
      uploadStructured: buildStructuredUploadExample(documentType, details, primaryDocument),
      ...buildReviewExample(primaryDocument, details),
    }),
    [details, documentType, primaryDocument],
  );
  const selectedDocument =
    documents.find((document) => document.filename === selectedFilename) ?? null;
  const canDeleteDocuments = user?.role === 'admin' || user?.role === 'superuser';
  const selectedReviewStatus =
    selectedReview?.submission.review_status ?? selectedDocument?.review_status ?? null;

  function toggleManualPanel(panel: 'pdf' | 'json' | 'review') {
    setOpenManualPanel(panel);
  }

  async function handlePdfUpload(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!pdfFile) {
      setError('Choose a PDF file before uploading.');
      return;
    }

    setError(null);
    setActionMessage(null);

    try {
      const response = await uploadDocument({
        file: pdfFile,
        documentType,
        fiscalYear: pdfFiscalYear || undefined,
        sourceUrl: pdfSourceUrl || undefined,
        autoProcess: true,
        enableAiScan: true,
      });
      setActionMessage(
        response.duplicate
          ? 'This file was already in the library, so we linked to the existing record.'
          : 'Document uploaded successfully.',
      );
      setPdfFile(null);
      setPdfInputKey((current) => current + 1);
      setPdfSourceUrl('');
      setOpenManualPanel('review');
      await loadDocuments();
      setSelectedFilename(response.document.filename);
      await loadDocumentReview(response.document.filename);
    } catch (uploadError) {
      setError(uploadError instanceof Error ? uploadError.message : 'Failed to upload PDF');
    }
  }

  async function handleStructuredUpload(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setActionMessage(null);

    let parsedData: StructuredDataPayload;
    try {
      parsedData = JSON.parse(structuredJson) as StructuredDataPayload;
    } catch {
      setError('Structured JSON must be valid JSON before it can be uploaded.');
      return;
    }

    try {
      const response = await uploadStructuredData({
        title: structuredTitle || undefined,
        documentType,
        fiscalYear: structuredFiscalYear || undefined,
        sourceUrl: structuredSourceUrl || undefined,
        structuredData: parsedData,
      });
      setActionMessage(
        response.duplicate
          ? 'This structured record already exists, so we linked to the existing item.'
          : 'Structured data uploaded successfully.',
      );
      setOpenManualPanel('review');
      await loadDocuments();
      setSelectedFilename(response.document.filename);
      await loadDocumentReview(response.document.filename);
    } catch (uploadError) {
      setError(
        uploadError instanceof Error ? uploadError.message : 'Failed to upload structured data',
      );
    }
  }

  async function handleProcessSelected(enableAiScan: boolean, force = false) {
    if (!selectedDocument) {
      return;
    }

    setError(null);
    setActionMessage(null);

    try {
      await processDocument(selectedDocument.filename, {
        run_parser: true,
        enable_ai_scan: enableAiScan,
        enable_search_indexing: false,
        force,
      });
      setActionMessage(
        enableAiScan
          ? force
            ? 'AI cleanup re-ran from scratch for the selected document.'
            : 'AI cleanup finished for the selected document.'
          : force
            ? 'The selected document was re-read from scratch.'
            : 'The selected document was read again successfully.',
      );
      await loadDocuments();
      await loadDocumentReview(selectedDocument.filename);
    } catch (processError) {
      setError(processError instanceof Error ? processError.message : 'Failed to process document');
    }
  }

  async function handleSubmitReview() {
    if (!selectedDocument) {
      return;
    }

    setError(null);
    setActionMessage(null);

    try {
      const response = await submitDocumentReview(selectedDocument.filename, {
        review_notes: reviewNotes || undefined,
      });
      setSelectedReview(response);
      setActionMessage('Document review approved. Publish it when you are ready to make it live.');
      await loadDocuments();
    } catch (submitError) {
      setError(
        submitError instanceof Error ? submitError.message : 'Failed to approve document review',
      );
    }
  }

  async function handlePublishSelected() {
    if (!selectedDocument) {
      return;
    }

    setError(null);
    setActionMessage(null);

    try {
      const result = await publishDocument(selectedDocument.filename);
      setActionMessage(
        result.publish_status === 'success'
          ? 'Document published successfully.'
          : `Document published with status: ${formatStatus(result.publish_status)}.`,
      );
      await loadDocuments();
      await loadDocumentReview(selectedDocument.filename);
    } catch (publishError) {
      setError(publishError instanceof Error ? publishError.message : 'Failed to publish document');
    }
  }

  async function handleUnapproveSelected() {
    if (!selectedDocument) {
      return;
    }

    setError(null);
    setActionMessage(null);

    try {
      const response = await unapproveDocumentReview(selectedDocument.filename);
      setSelectedReview(response);
      setActionMessage('Document moved back to pending review.');
      await loadDocuments();
    } catch (unapproveError) {
      setError(
        unapproveError instanceof Error ? unapproveError.message : 'Failed to unapprove document',
      );
    }
  }

  async function handleSelectDocument(filename: string) {
    setSelectedFilename(filename);
    setActionMessage(null);
    setError(null);
    try {
      await loadDocumentReview(filename);
    } catch (reviewError) {
      setError(reviewError instanceof Error ? reviewError.message : 'Failed to load document');
    }
  }

  async function handleDeleteSelected() {
    if (!selectedDocument || !canDeleteDocuments) {
      return;
    }

    const confirmed = window.confirm(
      `Delete ${selectedDocument.original_filename || selectedDocument.filename}? This removes the stored file, processed artifacts, and any published finance rows.`,
    );
    if (!confirmed) {
      return;
    }

    setError(null);
    setActionMessage(null);

    try {
      await deleteDocument(selectedDocument.filename);
      setActionMessage('Document deleted successfully.');
      setSelectedFilename(null);
      setSelectedReview(null);
      setReviewNotes('');
      await loadDocuments();
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : 'Failed to delete document');
    }
  }

  return (
    <div className="space-y-6">
      <section className="rounded-[30px] border border-[#0A2342]/8 bg-[linear-gradient(135deg,#ecfbfc_0%,#fffaf3_100%)] p-6">
        <p className="text-xs uppercase tracking-[0.28em] text-[#0A2342]/45">Record type</p>
        <h1 className="mt-3 text-3xl font-semibold text-[#0A2342]">{formatDocumentType(documentType)}</h1>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-[#0A2342]/62">{details.description}</p>

        <div className="mt-6 flex flex-wrap gap-3">
          <span className="rounded-full border border-[#0A2342]/10 bg-[#f8fcfc] px-3 py-2 text-xs font-medium text-[#0A2342]/70">
            Collection: {section.label}
          </span>
          <span className="rounded-full border border-[#0A2342]/10 bg-[#f8fcfc] px-3 py-2 text-xs font-medium text-[#0A2342]/70">
            {documents.length} {documents.length === 1 ? 'document' : 'documents'}
          </span>
          <span className="rounded-full border border-[#0A2342]/10 bg-[#f8fcfc] px-3 py-2 text-xs font-medium text-[#0A2342]/70">
            Last updated{' '}
            {formatDate(
              documents
                .map((document) => document.downloaded_at)
                .filter(Boolean)
                .sort()
                .at(-1) ?? null,
            )}
          </span>
        </div>
      </section>

      {error ? (
        <div className="rounded-[24px] border border-rose-200 bg-rose-50 px-5 py-4 text-sm text-rose-700">
          {error}
        </div>
      ) : null}

      {actionMessage ? (
        <div className="rounded-[24px] border border-emerald-200 bg-emerald-50 px-5 py-4 text-sm text-emerald-700">
          {actionMessage}
        </div>
      ) : null}

      {mode === 'overview' ? (
        <section className="rounded-[30px] border border-[#0A2342]/8 bg-white p-6 shadow-[0_18px_55px_rgba(10,35,66,0.05)]">
          <p className="text-xs uppercase tracking-[0.24em] text-[#0A2342]/45">Choose a route</p>
          <h2 className="mt-2 text-xl font-semibold text-[#0A2342]">How do you want to work with this record type?</h2>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-[#0A2342]/62">
            Choose one route to keep the screen focused. The manual route is for uploads, review,
            and AI cleanup. The API route is for payloads and expected data structures.
          </p>

          <div className="mt-6 grid gap-6 md:grid-cols-2">
            <Link
              href={`${typeBasePath}/manual`}
              className="rounded-[28px] border border-[#0A2342]/8 bg-[linear-gradient(180deg,#ffffff_0%,#fbfdfe_100%)] p-6 transition hover:border-[#00CED1]/35 hover:shadow-[0_16px_40px_rgba(0,206,209,0.12)]"
            >
              <p className="text-xs uppercase tracking-[0.22em] text-[#0A2342]/45">Manual admin</p>
              <h3 className="mt-3 text-xl font-semibold text-[#0A2342]">Upload, review, and use AI</h3>
              <p className="mt-3 text-sm leading-6 text-[#0A2342]/62">
                Add source PDFs or structured JSON, inspect raw extraction, run AI cleanup, and
                approve documents.
              </p>
            </Link>

            <Link
              href={`${typeBasePath}/api`}
              className="rounded-[28px] border border-[#0A2342]/8 bg-[linear-gradient(180deg,#ffffff_0%,#fbfdfe_100%)] p-6 transition hover:border-[#00CED1]/35 hover:shadow-[0_16px_40px_rgba(0,206,209,0.12)]"
            >
              <p className="text-xs uppercase tracking-[0.22em] text-[#0A2342]/45">API docs</p>
              <h3 className="mt-3 text-xl font-semibold text-[#0A2342]">Payloads and expectations</h3>
              <p className="mt-3 text-sm leading-6 text-[#0A2342]/62">
                See the current example, the expected JSON shape, and the endpoint examples for this
                exact record type.
              </p>
            </Link>
          </div>

          {documents.some(
            (document) =>
              document.publish_status === 'pending' || document.review_status === 'pending_review',
          ) ? (
            <div className="mt-6 rounded-[24px] border border-amber-200 bg-amber-50 px-5 py-4 text-sm leading-6 text-amber-900">
              <p className="font-semibold">Documents waiting for approval or publish</p>
              <p className="mt-1">
                Open{' '}
                <Link href={`${typeBasePath}/manual`} className="font-semibold underline">
                  Manual admin
                </Link>
                , expand <strong>Review saved documents</strong>, select your file, then use{' '}
                <strong>Approve document</strong> and <strong>Publish document</strong>.
              </p>
            </div>
          ) : null}

          <div className="mt-6">
            <Link
              href={`/admin/collections/${sectionId}`}
              className="inline-flex items-center rounded-2xl border border-[#0A2342]/10 bg-[#f8fcfc] px-4 py-3 text-sm font-medium text-[#0A2342] hover:border-[#0A2342]/20"
            >
              Back to collection
            </Link>
          </div>
        </section>
      ) : null}

      {mode === 'api' ? (
        <div className="space-y-6">
          <section className="rounded-[30px] border border-[#0A2342]/8 bg-white p-6 shadow-[0_18px_55px_rgba(10,35,66,0.05)]">
            <div className="flex items-center gap-3">
              <div className="rounded-2xl bg-[#00CED1]/12 p-3">
                <FileJson className="h-4 w-4 text-[#0A2342]" />
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.24em] text-[#0A2342]/45">Requirements</p>
                <h2 className="mt-1 text-xl font-semibold text-[#0A2342]">Current and expected JSON</h2>
              </div>
            </div>

            <p className="mt-5 text-sm leading-6 text-[#0A2342]/60">
              The first example shows what we can read from a real file. The second shows the cleaned
              JSON structure we want for this record type.
            </p>

            <div className="mt-6 space-y-6">
              <div>
                <p className="text-xs uppercase tracking-[0.22em] text-[#0A2342]/45">Current example</p>
                <div className="mt-3">
                  {selectedReview?.ai_processing.preview_json ? (
                    <pre className="min-w-0 overflow-x-auto rounded-[20px] bg-[#1d1a17] px-4 py-4 text-xs leading-6 text-[#f8f2e9] whitespace-pre-wrap break-words">
                      <code>{JSON.stringify(selectedReview.ai_processing.preview_json, null, 2)}</code>
                    </pre>
                  ) : extractionExample ? (
                    <pre className="min-w-0 overflow-x-auto rounded-[20px] bg-[#1d1a17] px-4 py-4 text-xs leading-6 text-[#f8f2e9] whitespace-pre-wrap break-words">
                      <code>{JSON.stringify(extractionExample, null, 2)}</code>
                    </pre>
                  ) : (
                    <div className="rounded-[24px] border border-dashed border-[#0A2342]/12 bg-[linear-gradient(135deg,#f7fcfc_0%,#fffaf3_100%)] px-5 py-8 text-sm leading-6 text-[#0A2342]/60">
                      No processed example is available yet for this record type.
                    </div>
                  )}
                </div>
              </div>

              <div>
                <p className="text-xs uppercase tracking-[0.22em] text-[#0A2342]/45">Expected JSON</p>
                <pre className="mt-3 min-w-0 overflow-x-auto rounded-[20px] bg-[#1d1a17] px-4 py-4 text-xs leading-6 text-[#f8f2e9] whitespace-pre-wrap break-words">
                  <code>{JSON.stringify(details.expectedExample, null, 2)}</code>
                </pre>
              </div>
            </div>
          </section>

          <section className="rounded-[30px] border border-[#0A2342]/8 bg-white p-6 shadow-[0_18px_55px_rgba(10,35,66,0.05)]">
            <div className="max-w-3xl">
              <p className="text-xs uppercase tracking-[0.24em] text-[#0A2342]/45">API for this type</p>
              <h2 className="mt-2 text-xl font-semibold text-[#0A2342]">JSON API expectations and examples</h2>
              <p className="mt-3 text-sm leading-6 text-[#0A2342]/60">
                This route is for structured JSON only. Source PDFs should be uploaded through
                Manual admin, then reviewed and processed there.
              </p>
            </div>

            <div className="mt-6 grid gap-6">
              <article className="rounded-[24px] border border-[#0A2342]/8 bg-[linear-gradient(180deg,#ffffff_0%,#fbfdfe_100%)] p-5">
                <p className="text-xs uppercase tracking-[0.22em] text-[#0A2342]/45">Upload structured JSON</p>
                <pre className="mt-4 min-w-0 overflow-x-auto rounded-[20px] bg-[#1d1a17] px-4 py-4 text-xs leading-6 text-[#f8f2e9] whitespace-pre-wrap break-words">
                  <code>{apiExamples.uploadStructured}</code>
                </pre>
              </article>

              <article className="rounded-[24px] border border-[#0A2342]/8 bg-[linear-gradient(180deg,#ffffff_0%,#fbfdfe_100%)] p-5">
                <p className="text-xs uppercase tracking-[0.22em] text-[#0A2342]/45">Run AI cleanup</p>
                <pre className="mt-4 min-w-0 overflow-x-auto rounded-[20px] bg-[#1d1a17] px-4 py-4 text-xs leading-6 text-[#f8f2e9] whitespace-pre-wrap break-words">
                  <code>{apiExamples.process}</code>
                </pre>
              </article>

              <article className="rounded-[24px] border border-[#0A2342]/8 bg-[linear-gradient(180deg,#ffffff_0%,#fbfdfe_100%)] p-5">
                <p className="text-xs uppercase tracking-[0.22em] text-[#0A2342]/45">Review one document</p>
                <pre className="mt-4 min-w-0 overflow-x-auto rounded-[20px] bg-[#1d1a17] px-4 py-4 text-xs leading-6 text-[#f8f2e9] whitespace-pre-wrap break-words">
                  <code>{apiExamples.review}</code>
                </pre>
              </article>
            </div>

            <div className="mt-6">
              <Link
                href={typeBasePath}
                className="inline-flex items-center rounded-2xl border border-[#0A2342]/10 bg-[#f8fcfc] px-4 py-3 text-sm font-medium text-[#0A2342] hover:border-[#0A2342]/20"
              >
                Back to record type
              </Link>
            </div>
          </section>
        </div>
      ) : null}

      {mode === 'manual' ? (
        <div className="space-y-6">
          <section className="rounded-[30px] border border-[#0A2342]/8 bg-white p-6 shadow-[0_18px_55px_rgba(10,35,66,0.05)]">
            <div className="flex items-center gap-3">
              <div className="rounded-2xl bg-[#00CED1]/12 p-3">
                <Upload className="h-4 w-4 text-[#0A2342]" />
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.24em] text-[#0A2342]/45">Manual admin</p>
                <h2 className="mt-1 text-xl font-semibold text-[#0A2342]">Work with this record type</h2>
              </div>
            </div>

            <div className="mt-6 space-y-4">
              <article className="overflow-hidden rounded-[24px] border border-[#0A2342]/8 bg-[linear-gradient(180deg,#ffffff_0%,#fbfdfe_100%)]">
                <button
                  type="button"
                  onClick={() => toggleManualPanel('pdf')}
                  className="flex w-full items-center justify-between gap-4 px-5 py-4 text-left"
                >
                  <div>
                    <p className="text-sm font-semibold text-[#0A2342]">Upload a PDF</p>
                    <p className="mt-1 text-sm leading-6 text-[#0A2342]/60">
                      Save the original source file under this record type first.
                    </p>
                  </div>
                  {openManualPanel === 'pdf' ? (
                    <span className="rounded-full border border-[#0A2342]/10 bg-[#f8fcfc] px-3 py-1 text-xs font-medium text-[#0A2342]/60">
                      Active
                    </span>
                  ) : (
                    <ChevronRight className="h-5 w-5 text-[#0A2342]/55" />
                  )}
                </button>

                {openManualPanel === 'pdf' ? (
                  <form onSubmit={(event) => void handlePdfUpload(event)} className="border-t border-[#0A2342]/8 px-5 py-5">
                    <div className="grid gap-4">
                      <label className="block">
                        <span className="mb-2 block text-xs uppercase tracking-[0.18em] text-[#0A2342]/45">
                          PDF file
                        </span>
                        <input
                          key={pdfInputKey}
                          type="file"
                          accept="application/pdf"
                          onChange={(event) => setPdfFile(event.target.files?.[0] ?? null)}
                          className="block w-full rounded-2xl border border-[#0A2342]/10 bg-[#f8fcfc] px-4 py-3 text-sm text-[#0A2342]"
                        />
                        <p className="mt-2 text-xs text-[#0A2342]/55">
                          {pdfFile ? `Selected: ${pdfFile.name}` : 'No file selected yet.'}
                        </p>
                      </label>

                      <div className="grid gap-4 md:grid-cols-2">
                        <label className="block">
                          <span className="mb-2 block text-xs uppercase tracking-[0.18em] text-[#0A2342]/45">
                            Fiscal year
                          </span>
                          <input
                            value={pdfFiscalYear}
                            onChange={(event) => setPdfFiscalYear(event.target.value)}
                            placeholder="2025/26"
                            className="w-full rounded-2xl border border-[#0A2342]/10 bg-[#f8fcfc] px-4 py-3 text-sm text-[#0A2342] outline-none transition focus:border-[#00CED1]/35"
                          />
                        </label>

                        <label className="block">
                          <span className="mb-2 block text-xs uppercase tracking-[0.18em] text-[#0A2342]/45">
                            Source URL
                          </span>
                          <input
                            value={pdfSourceUrl}
                            onChange={(event) => setPdfSourceUrl(event.target.value)}
                            placeholder="https://source.example.gov.bs/file.pdf"
                            className="w-full rounded-2xl border border-[#0A2342]/10 bg-[#f8fcfc] px-4 py-3 text-sm text-[#0A2342] outline-none transition focus:border-[#00CED1]/35"
                          />
                        </label>
                      </div>
                    </div>

                    <button
                      type="submit"
                      className="mt-5 inline-flex items-center rounded-2xl bg-[#00CED1] px-5 py-3 text-sm font-semibold text-white shadow-[0_12px_30px_rgba(0,206,209,0.22)] hover:bg-[#00b8bb]"
                    >
                      Save PDF
                    </button>
                  </form>
                ) : null}
              </article>

              <article className="overflow-hidden rounded-[24px] border border-black/8 bg-[#fffaf4]">
                <button
                  type="button"
                  onClick={() => toggleManualPanel('json')}
                  className="flex w-full items-center justify-between gap-4 px-5 py-4 text-left"
                >
                  <div>
                    <p className="text-sm font-semibold text-black">Upload structured JSON</p>
                    <p className="mt-1 text-sm leading-6 text-black/60">
                      Use this when the data is already cleaned and you want to add it directly.
                    </p>
                  </div>
                  {openManualPanel === 'json' ? (
                    <span className="rounded-full border border-[#0A2342]/10 bg-[#f8fcfc] px-3 py-1 text-xs font-medium text-[#0A2342]/60">
                      Active
                    </span>
                  ) : (
                    <ChevronRight className="h-5 w-5 text-[#0A2342]/55" />
                  )}
                </button>

                {openManualPanel === 'json' ? (
                  <form onSubmit={(event) => void handleStructuredUpload(event)} className="border-t border-[#0A2342]/8 px-5 py-5">
                    <div className="grid gap-4">
                      <div className="grid gap-4 md:grid-cols-3">
                        <label className="block">
                          <span className="mb-2 block text-xs uppercase tracking-[0.18em] text-[#0A2342]/45">
                            Title
                          </span>
                          <input
                            value={structuredTitle}
                            onChange={(event) => setStructuredTitle(event.target.value)}
                            className="w-full rounded-2xl border border-[#0A2342]/10 bg-[#f8fcfc] px-4 py-3 text-sm text-[#0A2342] outline-none transition focus:border-[#00CED1]/35"
                          />
                        </label>

                        <label className="block">
                          <span className="mb-2 block text-xs uppercase tracking-[0.18em] text-[#0A2342]/45">
                            Fiscal year
                          </span>
                          <input
                            value={structuredFiscalYear}
                            onChange={(event) => setStructuredFiscalYear(event.target.value)}
                            placeholder="2025/26"
                            className="w-full rounded-2xl border border-[#0A2342]/10 bg-[#f8fcfc] px-4 py-3 text-sm text-[#0A2342] outline-none transition focus:border-[#00CED1]/35"
                          />
                        </label>

                        <label className="block">
                          <span className="mb-2 block text-xs uppercase tracking-[0.18em] text-[#0A2342]/45">
                            Source URL
                          </span>
                          <input
                            value={structuredSourceUrl}
                            onChange={(event) => setStructuredSourceUrl(event.target.value)}
                            placeholder="https://source.example.gov.bs/file.pdf"
                            className="w-full rounded-2xl border border-[#0A2342]/10 bg-[#f8fcfc] px-4 py-3 text-sm text-[#0A2342] outline-none transition focus:border-[#00CED1]/35"
                          />
                        </label>
                      </div>

                      <label className="block">
                        <span className="mb-2 block text-xs uppercase tracking-[0.18em] text-[#0A2342]/45">
                          Structured JSON
                        </span>
                        <textarea
                          value={structuredJson}
                          onChange={(event) => setStructuredJson(event.target.value)}
                          rows={16}
                          className="w-full rounded-[22px] border border-[#0A2342]/10 bg-[#1d1a17] px-4 py-4 font-mono text-xs leading-6 text-[#f8f2e9] outline-none transition focus:border-[#00CED1]/35"
                        />
                      </label>
                    </div>

                    <button
                      type="submit"
                      className="mt-5 inline-flex items-center rounded-2xl bg-[#00CED1] px-5 py-3 text-sm font-semibold text-white shadow-[0_12px_30px_rgba(0,206,209,0.22)] hover:bg-[#00b8bb]"
                    >
                      Save structured data
                    </button>
                  </form>
                ) : null}
              </article>

              <article className="overflow-hidden rounded-[24px] border border-[#0A2342]/8 bg-[linear-gradient(180deg,#ffffff_0%,#fbfdfe_100%)]">
                <button
                  type="button"
                  onClick={() => toggleManualPanel('review')}
                  className="flex w-full items-center justify-between gap-4 px-5 py-4 text-left"
                >
                  <div>
                    <p className="text-sm font-semibold text-[#0A2342]">Review saved documents</p>
                    <p className="mt-1 text-sm leading-6 text-[#0A2342]/60">
                      Open an existing record, read the file again, run AI cleanup, and approve the result.
                    </p>
                  </div>
                  {openManualPanel === 'review' ? (
                    <span className="rounded-full border border-[#0A2342]/10 bg-[#f8fcfc] px-3 py-1 text-xs font-medium text-[#0A2342]/60">
                      Active
                    </span>
                  ) : (
                    <ChevronRight className="h-5 w-5 text-[#0A2342]/55" />
                  )}
                </button>

                {openManualPanel === 'review' ? (
                  <div className="border-t border-[#0A2342]/8 px-5 py-5">
                    <div className="grid gap-6 xl:grid-cols-[340px_minmax(0,1fr)]">
                      <section className="rounded-[24px] border border-[#0A2342]/8 bg-white p-5">
                        <div className="flex items-center gap-3">
                          <div className="rounded-2xl bg-[#00CED1]/12 p-3">
                            <FolderTree className="h-4 w-4 text-[#0A2342]" />
                          </div>
                          <div>
                            <p className="text-xs uppercase tracking-[0.24em] text-[#0A2342]/45">Saved documents</p>
                            <h2 className="mt-1 text-xl font-semibold text-[#0A2342]">Choose a document</h2>
                          </div>
                        </div>

                        {loading ? <p className="mt-6 text-sm text-[#0A2342]/55">Loading documents…</p> : null}

                        <div className="mt-6 space-y-3">
                          {documents.length ? (
                            paginatedDocuments.map((document) => {
                              const isSelected = document.filename === selectedFilename;
                              return (
                                <button
                                  key={document.filename}
                                  type="button"
                                  onClick={() => void handleSelectDocument(document.filename)}
                                  className={`block w-full rounded-[24px] border p-4 text-left transition ${
                                    isSelected
                                      ? 'border-[#00CED1]/30 bg-[linear-gradient(135deg,#ecfbfc_0%,#fffaf3_100%)] shadow-[0_14px_34px_rgba(10,35,66,0.06)]'
                                      : 'border-[#0A2342]/8 bg-[linear-gradient(180deg,#ffffff_0%,#fbfdfe_100%)] hover:border-[#0A2342]/15'
                                  }`}
                                >
                                  <p className="break-words text-sm font-semibold text-[#0A2342]">
                                    {document.original_filename || document.filename}
                                  </p>
                                  <p className="mt-1 break-words font-mono text-xs text-[#0A2342]/45">
                                    {document.filename}
                                  </p>
                                  <div className="mt-3 flex flex-wrap gap-2 text-xs text-[#0A2342]/60">
                                    {document.fiscal_year ? (
                                      <span className="rounded-full border border-[#0A2342]/10 bg-white px-3 py-2">
                                        {document.fiscal_year}
                                      </span>
                                    ) : null}
                                    <span
                                      className={`rounded-full border px-3 py-2 ${getReviewStatusTone(
                                        document.review_status,
                                      )}`}
                                    >
                                      Review {formatStatus(document.review_status)}
                                    </span>
                                    <span
                                      className={`rounded-full border px-3 py-2 ${getPublishStatusTone(
                                        document.publish_status,
                                      )}`}
                                    >
                                      Publish {formatStatus(document.publish_status)}
                                    </span>
                                    <span className="rounded-full border border-[#0A2342]/10 bg-white px-3 py-2">
                                      Extraction {formatStatus(document.extraction_status)}
                                    </span>
                                    <span className="rounded-full border border-[#0A2342]/10 bg-white px-3 py-2">
                                      AI {formatStatus(document.normalization_status)}
                                    </span>
                                  </div>
                                </button>
                              );
                            })
                          ) : (
                            <div className="rounded-[24px] border border-dashed border-[#0A2342]/12 bg-[linear-gradient(135deg,#f7fcfc_0%,#fffaf3_100%)] px-5 py-8 text-sm leading-6 text-[#0A2342]/60">
                              No files in this record type yet.
                            </div>
                          )}
                        </div>

                        <PaginationControls
                          currentPage={currentPage}
                          totalPages={totalPages}
                          totalItems={documents.length}
                          pageSize={pageSize}
                          itemLabel="documents"
                          onPageChange={setCurrentPage}
                        />
                      </section>

                      <section className="min-w-0 rounded-[24px] border border-[#0A2342]/8 bg-white p-5">
                        {selectedDocument ? (
                          <div className="space-y-6">
                            <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                              <div className="min-w-0">
                                <p className="text-sm font-semibold text-[#0A2342]">
                                  {selectedDocument.original_filename || selectedDocument.filename}
                                </p>
                                <p className="mt-1 break-words font-mono text-xs text-[#0A2342]/45">
                                  {selectedDocument.filename}
                                </p>
                                <div className="mt-3 flex flex-wrap gap-2 text-xs text-[#0A2342]/60">
                                  <span className="rounded-full border border-[#0A2342]/10 bg-white px-3 py-2">
                                    Added {formatDate(selectedDocument.downloaded_at)}
                                  </span>
                                  <span
                                    className={`rounded-full border px-3 py-2 ${getReviewStatusTone(
                                      selectedReviewStatus,
                                    )}`}
                                  >
                                    Review {formatStatus(selectedReviewStatus)}
                                  </span>
                                  <span
                                    className={`rounded-full border px-3 py-2 ${getPublishStatusTone(
                                      selectedReview?.submission.publish_status ??
                                        selectedDocument.publish_status,
                                    )}`}
                                  >
                                    Publish{' '}
                                    {formatStatus(
                                      selectedReview?.submission.publish_status ??
                                        selectedDocument.publish_status,
                                    )}
                                  </span>
                                  <span className="rounded-full border border-[#0A2342]/10 bg-white px-3 py-2">
                                    Submitted {formatDateTime(selectedReview?.submission.submitted_at ?? selectedDocument.submitted_at)}
                                  </span>
                                  <span className="rounded-full border border-[#0A2342]/10 bg-white px-3 py-2">
                                    Live {formatDateTime(selectedReview?.submission.published_at ?? selectedDocument.published_at)}
                                  </span>
                                </div>
                              </div>

                              {selectedDocument.exists_on_disk ? (
                                <a
                                  href={getAdminDocumentUrl(selectedDocument.filename)}
                                  target="_blank"
                                  rel="noreferrer"
                                  className="inline-flex items-center gap-2 rounded-2xl border border-[#0A2342]/10 bg-white px-4 py-3 text-sm font-medium text-[#0A2342] hover:border-[#0A2342]/20"
                                >
                                  Open file
                                  <ExternalLink className="h-4 w-4" />
                                </a>
                              ) : (
                                <div className="inline-flex items-center rounded-2xl border border-[#0A2342]/10 bg-white px-4 py-3 text-sm text-[#0A2342]/55">
                                  File not available locally
                                </div>
                              )}
                            </div>

                            <div className="flex flex-wrap gap-3">
                              <button
                                type="button"
                                onClick={() => void handleProcessSelected(false)}
                                className="inline-flex items-center rounded-2xl border border-[#0A2342]/10 bg-white px-4 py-3 text-sm font-medium text-[#0A2342] hover:border-[#0A2342]/20"
                              >
                                Read file
                              </button>
                              <button
                                type="button"
                                onClick={() => void handleProcessSelected(false, true)}
                                className="inline-flex items-center rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-medium text-amber-800 hover:border-amber-300"
                              >
                                Re-read file (force)
                              </button>
                              <button
                                type="button"
                                onClick={() => void handleProcessSelected(true)}
                                className="inline-flex items-center gap-2 rounded-2xl bg-[#00CED1] px-4 py-3 text-sm font-semibold text-white shadow-[0_12px_30px_rgba(0,206,209,0.22)] hover:bg-[#00b8bb]"
                              >
                                <Sparkles className="h-4 w-4" />
                                Use AI cleanup
                              </button>
                              <button
                                type="button"
                                onClick={() => void handleProcessSelected(true, true)}
                                className="inline-flex items-center gap-2 rounded-2xl border border-[#00CED1]/30 bg-[#00CED1]/10 px-4 py-3 text-sm font-semibold text-[#0A2342] hover:border-[#00CED1]/50"
                              >
                                <Sparkles className="h-4 w-4 text-[#00CED1]" />
                                Re-run AI cleanup (force)
                              </button>
                              <button
                                type="button"
                                onClick={() => void handleSelectDocument(selectedDocument.filename)}
                                className="inline-flex items-center rounded-2xl border border-[#0A2342]/10 bg-white px-4 py-3 text-sm font-medium text-[#0A2342] hover:border-[#0A2342]/20"
                              >
                                Refresh review
                              </button>
                              {canDeleteDocuments ? (
                                <button
                                  type="button"
                                  onClick={() => void handleDeleteSelected()}
                                  className="inline-flex items-center rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700 hover:border-rose-300"
                                >
                                  Delete document
                                </button>
                              ) : null}
                            </div>

                            {reviewLoading ? <p className="text-sm text-[#0A2342]/55">Loading review data…</p> : null}

                            <div className="space-y-5">
                              <div>
                                <p className="text-xs uppercase tracking-[0.22em] text-[#0A2342]/45">Raw extraction</p>
                                <div className="mt-3 min-w-0 rounded-[20px] bg-[#1d1a17] px-4 py-4 text-xs leading-6 text-[#f8f2e9]">
                                  {selectedReview?.extraction.sample_pages.length ? (
                                    <pre className="overflow-x-auto whitespace-pre-wrap break-words">
                                      <code>{JSON.stringify(selectedReview.extraction.sample_pages[0], null, 2)}</code>
                                    </pre>
                                  ) : selectedReview?.extraction.sample_tables.length ? (
                                    <pre className="overflow-x-auto whitespace-pre-wrap break-words">
                                      <code>{JSON.stringify(selectedReview.extraction.sample_tables[0], null, 2)}</code>
                                    </pre>
                                  ) : (
                                    <p>No extraction output is available yet.</p>
                                  )}
                                </div>
                              </div>

                              <div>
                                <p className="text-xs uppercase tracking-[0.22em] text-[#0A2342]/45">AI output</p>
                                <div className="mt-3 min-w-0 rounded-[20px] bg-[#1d1a17] px-4 py-4 text-xs leading-6 text-[#f8f2e9]">
                                  {selectedReview?.ai_processing.preview_json ? (
                                    <pre className="overflow-x-auto whitespace-pre-wrap break-words">
                                      <code>{JSON.stringify(selectedReview.ai_processing.preview_json, null, 2)}</code>
                                    </pre>
                                  ) : (
                                    <p>No AI-cleaned output is available yet.</p>
                                  )}
                                </div>
                              </div>
                            </div>

                            <div>
                              <p className="text-xs uppercase tracking-[0.22em] text-[#0A2342]/45">Review notes</p>
                              <textarea
                                value={reviewNotes}
                                onChange={(event) => setReviewNotes(event.target.value)}
                                rows={4}
                                placeholder="Add any notes before approving this document."
                                className="mt-3 w-full rounded-[22px] border border-[#0A2342]/10 bg-[#f8fcfc] px-4 py-4 text-sm leading-6 text-[#0A2342] outline-none transition focus:border-[#00CED1]/35"
                              />
                              <button
                                type="button"
                                onClick={() => void handleSubmitReview()}
                                className="mt-4 inline-flex items-center rounded-2xl bg-[#00CED1] px-5 py-3 text-sm font-semibold text-white shadow-[0_12px_30px_rgba(0,206,209,0.22)] hover:bg-[#00b8bb]"
                              >
                                Approve document
                              </button>
                              <button
                                type="button"
                                onClick={() => void handleUnapproveSelected()}
                                disabled={!selectedReview?.submission.can_unapprove}
                                className="mt-4 ml-3 inline-flex items-center rounded-2xl border border-amber-200 bg-amber-50 px-5 py-3 text-sm font-semibold text-amber-700 hover:border-amber-300 disabled:cursor-not-allowed disabled:opacity-50"
                              >
                                Unapprove document
                              </button>
                              <button
                                type="button"
                                onClick={() => void handlePublishSelected()}
                                disabled={!selectedReview?.submission.can_publish}
                                className="mt-4 ml-3 inline-flex items-center rounded-2xl border border-[#0A2342]/10 bg-white px-5 py-3 text-sm font-semibold text-[#0A2342] hover:border-[#0A2342]/20 disabled:cursor-not-allowed disabled:opacity-50"
                              >
                                Publish document
                              </button>
                              {!selectedReview?.submission.can_publish ? (
                                <p className="mt-3 text-sm leading-6 text-[#0A2342]/60">
                                  {selectedReviewStatus === 'approved'
                                    ? 'This document is approved. If Publish is still disabled, click Refresh review or make sure the backend API is running.'
                                    : 'Click Approve document first. Then Publish will become available to push data to the live dashboard.'}
                                </p>
                              ) : selectedReview?.submission.publish_status === 'pending' ? (
                                <p className="mt-3 text-sm leading-6 text-[#0A2342]/60">
                                  Approved and ready — click Publish document to update the public budget data.
                                </p>
                              ) : null}
                            </div>
                          </div>
                        ) : (
                          <div className="rounded-[24px] border border-dashed border-[#0A2342]/12 bg-[linear-gradient(135deg,#f7fcfc_0%,#fffaf3_100%)] px-5 py-10 text-sm leading-6 text-[#0A2342]/60">
                            Select a document to review its extracted data, AI output, and approval status.
                          </div>
                        )}
                      </section>
                    </div>
                  </div>
                ) : null}
              </article>
            </div>
            <div className="mt-6">
              <Link
                href={typeBasePath}
                className="inline-flex items-center rounded-2xl border border-[#0A2342]/10 bg-[#f8fcfc] px-4 py-3 text-sm font-medium text-[#0A2342] hover:border-[#0A2342]/20"
              >
                Back to record type
              </Link>
            </div>
          </section>
        </div>
      ) : null}
    </div>
  );
}
