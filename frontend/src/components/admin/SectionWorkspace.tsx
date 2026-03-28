'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { ArrowRight, FolderTree } from 'lucide-react';
import PaginationControls from '@/components/admin/PaginationControls';
import { fetchAdminDocuments } from '@/lib/admin-api';
import {
  formatDocumentType,
  getSectionById,
  getSectionDocuments,
  type AdminSectionId,
} from '@/lib/admin-collections';
import type { DocumentRecord } from '@/types/admin';

type SectionWorkspaceProps = {
  sectionId: AdminSectionId;
};

function formatDate(value?: string | null) {
  if (!value) {
    return 'No files yet';
  }

  return new Date(value).toLocaleDateString();
}

function groupDocumentsByType(documents: DocumentRecord[], documentTypes: string[]) {
  return documentTypes.map((type) => ({
    type,
    label: formatDocumentType(type),
    documents: documents.filter((document) => (document.document_type ?? 'other') === type),
    lastUpdated:
      documents
        .filter((document) => (document.document_type ?? 'other') === type)
        .map((document) => document.downloaded_at)
        .filter(Boolean)
        .sort()
        .at(-1) ?? null,
  }));
}

export default function SectionWorkspace({ sectionId }: SectionWorkspaceProps) {
  const section = getSectionById(sectionId);
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 6;

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetchAdminDocuments();
        setDocuments(response.documents);
      } catch (loadError) {
        setError(loadError instanceof Error ? loadError.message : 'Failed to load collection');
      } finally {
        setLoading(false);
      }
    };

    void load();
  }, [sectionId]);

  const sectionDocuments = useMemo(
    () => getSectionDocuments(documents, sectionId),
    [documents, sectionId],
  );

  const groupedDocuments = useMemo(
    () => groupDocumentsByType(sectionDocuments, section.documentTypes),
    [section.documentTypes, sectionDocuments],
  );
  const totalPages = Math.max(1, Math.ceil(groupedDocuments.length / pageSize));
  const paginatedGroups = groupedDocuments.slice(
    (currentPage - 1) * pageSize,
    currentPage * pageSize,
  );

  useEffect(() => {
    if (currentPage > totalPages) {
      setCurrentPage(totalPages);
    }
  }, [currentPage, totalPages]);

  const documentCount = sectionDocuments.length;
  const documentTypeCount = groupedDocuments.filter((group) => group.documents.length > 0).length;

  return (
    <div className="space-y-6">
      <section className="rounded-[30px] border border-[#0A2342]/8 bg-[linear-gradient(135deg,#ecfbfc_0%,#fffaf3_100%)] p-6">
        <p className="text-xs uppercase tracking-[0.28em] text-[#0A2342]/45">Collection</p>
        <h1 className="mt-3 text-3xl font-semibold text-[#0A2342]">{section.label}</h1>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-[#0A2342]/62">{section.description}</p>

        <div className="mt-6 grid gap-4 md:grid-cols-3">
          <div className="rounded-[24px] border border-[#0A2342]/8 bg-white px-5 py-4">
            <p className="text-xs uppercase tracking-[0.2em] text-[#0A2342]/45">Product areas</p>
            <p className="mt-3 text-sm leading-6 text-[#0A2342]/70">{section.publicAreas.join(', ')}</p>
          </div>
          <div className="rounded-[24px] border border-[#0A2342]/8 bg-white px-5 py-4">
            <p className="text-xs uppercase tracking-[0.2em] text-[#0A2342]/45">Record types</p>
            <p className="mt-3 text-3xl font-semibold text-[#0A2342]">{section.documentTypes.length}</p>
          </div>
          <div className="rounded-[24px] border border-[#0A2342]/8 bg-white px-5 py-4">
            <p className="text-xs uppercase tracking-[0.2em] text-[#0A2342]/45">Saved documents</p>
            <p className="mt-3 text-3xl font-semibold text-[#0A2342]">{documentCount}</p>
          </div>
        </div>
      </section>

      {error ? (
        <div className="rounded-[24px] border border-rose-200 bg-rose-50 px-5 py-4 text-sm text-rose-700">
          {error}
        </div>
      ) : null}

      <section className="rounded-[30px] border border-[#0A2342]/8 bg-white p-6 shadow-[0_18px_55px_rgba(10,35,66,0.05)]">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.24em] text-[#0A2342]/45">Structure</p>
            <h2 className="mt-2 text-xl font-semibold text-[#0A2342]">Record types in this collection</h2>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-[#0A2342]/62">
              Each collection contains record types. Each record type contains the actual source
              documents we have today.
            </p>
          </div>

          <div className="rounded-[22px] border border-[#00CED1]/16 bg-[#f3fcfc] px-4 py-3 text-sm text-[#0A2342]/68">
            {documentTypeCount} of {section.documentTypes.length} record types currently have files
          </div>
        </div>

        {loading ? <p className="mt-6 text-sm text-[#0A2342]/55">Loading collection…</p> : null}

        <div className="mt-6 space-y-5">
          {paginatedGroups.map((group) => (
            <article
              key={group.type}
              className="rounded-[28px] border border-[#0A2342]/8 bg-[linear-gradient(180deg,#ffffff_0%,#fbfdfe_100%)] p-5"
            >
              <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                <div>
                  <div className="flex items-center gap-3">
                    <div className="rounded-2xl bg-[#00CED1]/12 p-3">
                      <FolderTree className="h-4 w-4 text-[#0A2342]" />
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-[#0A2342]">{group.label}</p>
                      <p className="mt-1 font-mono text-xs text-[#0A2342]/45">{group.type}</p>
                    </div>
                  </div>
                </div>

                <div className="flex flex-wrap gap-2">
                  <span className="rounded-full border border-[#0A2342]/10 bg-[#f8fcfc] px-3 py-2 text-xs font-medium text-[#0A2342]/70">
                    {group.documents.length} {group.documents.length === 1 ? 'document' : 'documents'}
                  </span>
                  <span className="rounded-full border border-[#0A2342]/10 bg-[#f8fcfc] px-3 py-2 text-xs font-medium text-[#0A2342]/70">
                    Last updated {formatDate(group.lastUpdated)}
                  </span>
                </div>
              </div>

              <div className="mt-5 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
                <div className="flex flex-wrap gap-2">
                  {group.documents.length ? (
                    group.documents.map((document) => (
                      <span
                        key={document.filename}
                        className="rounded-full border border-[#0A2342]/10 bg-[#f8fcfc] px-3 py-2 text-xs font-medium text-[#0A2342]/70"
                      >
                        {document.original_filename || document.filename}
                      </span>
                    ))
                  ) : (
                    <span className="rounded-full border border-[#0A2342]/10 bg-[#f8fcfc] px-3 py-2 text-xs font-medium text-[#0A2342]/45">
                      No files yet
                    </span>
                  )}
                </div>

                <Link
                  href={`/admin/collections/${sectionId}/groups/${group.type}`}
                  className="inline-flex items-center gap-2 rounded-2xl bg-[#00CED1] px-4 py-3 text-sm font-medium text-white shadow-[0_12px_30px_rgba(0,206,209,0.22)] hover:bg-[#00b8bb]"
                >
                  Open record type
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </div>
            </article>
          ))}
        </div>

        <PaginationControls
          currentPage={currentPage}
          totalPages={totalPages}
          totalItems={groupedDocuments.length}
          pageSize={pageSize}
          itemLabel="record types"
          onPageChange={setCurrentPage}
        />
      </section>

      <section className="rounded-[30px] border border-[#0A2342]/8 bg-white p-6 shadow-[0_18px_55px_rgba(10,35,66,0.05)]">
        <p className="text-xs uppercase tracking-[0.24em] text-[#0A2342]/45">Navigation</p>
        <h2 className="mt-2 text-xl font-semibold text-[#0A2342]">Move through collections</h2>
        <div className="mt-6 flex flex-wrap gap-3">
          <Link
            href="/admin/collections"
            className="inline-flex items-center rounded-2xl border border-[#0A2342]/10 bg-[#f8fcfc] px-4 py-3 text-sm font-medium text-[#0A2342] hover:border-[#0A2342]/20"
          >
            Back to collections
          </Link>
        </div>
      </section>
    </div>
  );
}
