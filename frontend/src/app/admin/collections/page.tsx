'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { ArrowRight, FolderTree } from 'lucide-react';
import DataCoverageMatrix from '@/components/admin/DataCoverageMatrix';
import PaginationControls from '@/components/admin/PaginationControls';
import { fetchAdminDocuments } from '@/lib/admin-api';
import { getSectionSummary } from '@/lib/admin-collections';
import type { DocumentRecord } from '@/types/admin';

export default function AdminCollectionsPage() {
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 4;

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetchAdminDocuments();
        setDocuments(response.documents);
      } catch (loadError) {
        setError(loadError instanceof Error ? loadError.message : 'Failed to load collections');
      } finally {
        setLoading(false);
      }
    };

    void load();
  }, []);

  const sectionSummary = useMemo(() => getSectionSummary(documents), [documents]);
  const totalPages = Math.max(1, Math.ceil(sectionSummary.length / pageSize));
  const paginatedSections = sectionSummary.slice(
    (currentPage - 1) * pageSize,
    currentPage * pageSize,
  );

  useEffect(() => {
    if (currentPage > totalPages) {
      setCurrentPage(totalPages);
    }
  }, [currentPage, totalPages]);

  return (
    <div className="space-y-6">
      <section className="rounded-[28px] border border-[#0A2342]/8 bg-[linear-gradient(135deg,#ecfbfc_0%,#fffaf3_100%)] p-5 sm:rounded-[30px] sm:p-6">
        <p className="text-xs uppercase tracking-[0.28em] text-[#0A2342]/45">Collections</p>
        <h1 className="mt-3 text-2xl font-semibold text-[#0A2342] sm:text-3xl">Browse the data library by collection</h1>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-[#0A2342]/68 sm:text-[15px]">
          Collections are the top level of organization. Inside each collection, record types hold
          the specific types of files, and each type contains the actual documents we have today.
        </p>
      </section>

      {error ? (
        <div className="rounded-[24px] border border-rose-200 bg-rose-50 px-5 py-4 text-sm text-rose-700">
          {error}
        </div>
      ) : null}

      <section className="rounded-[28px] border border-[#0A2342]/8 bg-white p-5 shadow-[0_18px_55px_rgba(10,35,66,0.05)] sm:rounded-[30px] sm:p-6">
        <div className="grid gap-4 md:grid-cols-2">
          {paginatedSections.map((section) => (
            <article key={section.id} className="min-w-0 rounded-[24px] border border-[#0A2342]/8 bg-[linear-gradient(180deg,#ffffff_0%,#fbfdfe_100%)] p-5">
              <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                <div className="min-w-0">
                  <div className="flex items-center gap-3">
                    <div className="rounded-2xl bg-[#00CED1]/12 p-3">
                      <FolderTree className="h-4 w-4 text-[#0A2342]" />
                    </div>
                    <div className="min-w-0">
                      <p className="break-words text-sm font-semibold text-[#0A2342]">{section.label}</p>
                      <p className="mt-1 text-xs uppercase tracking-[0.18em] text-[#0A2342]/45">
                        Collection
                      </p>
                    </div>
                  </div>
                  <p className="mt-2 break-words text-sm leading-6 text-[#0A2342]/62">{section.description}</p>
                  <p className="mt-3 break-words text-sm text-[#0A2342]/55">{section.publicAreas.join(', ')}</p>
                </div>
                <Link
                  href={`/admin/collections/${section.id}`}
                  className="inline-flex shrink-0 items-center gap-2 self-start rounded-2xl bg-[#00CED1] px-4 py-3 text-sm font-medium text-white shadow-[0_12px_30px_rgba(0,206,209,0.22)] hover:bg-[#00b8bb]"
                >
                  Open
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </div>

              <p className="mt-5 break-words text-sm leading-6 text-[#0A2342]/60">
                Open this collection to browse its record types and the files currently assigned to them.
              </p>
            </article>
          ))}
        </div>

        <PaginationControls
          currentPage={currentPage}
          totalPages={totalPages}
          totalItems={sectionSummary.length}
          pageSize={pageSize}
          itemLabel="collections"
          onPageChange={setCurrentPage}
        />
        {loading ? <p className="mt-6 text-sm text-[#0A2342]/55">Loading collections…</p> : null}
      </section>

      <DataCoverageMatrix />
    </div>
  );
}
