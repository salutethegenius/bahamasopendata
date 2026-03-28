'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import DocumentGroupWorkspace from '@/components/admin/DocumentGroupWorkspace';
import {
  getSectionById,
  isAdminSectionId,
  isDocumentType,
} from '@/lib/admin-collections';

export default function AdminDocumentTypePage() {
  const params = useParams<{ sectionId: string; documentType: string }>();
  const sectionId = Array.isArray(params.sectionId) ? params.sectionId[0] : params.sectionId;
  const documentType = Array.isArray(params.documentType)
    ? params.documentType[0]
    : params.documentType;

  if (!sectionId || !isAdminSectionId(sectionId) || !documentType || !isDocumentType(documentType)) {
    return (
      <div className="space-y-6">
        <section className="rounded-[30px] border border-[#0A2342]/8 bg-[linear-gradient(135deg,#ecfbfc_0%,#fffaf3_100%)] p-6">
          <p className="text-xs uppercase tracking-[0.28em] text-[#0A2342]/45">Record type not found</p>
          <h1 className="mt-3 text-3xl font-semibold text-[#0A2342]">This record type does not exist</h1>
          <p className="mt-3 text-sm leading-6 text-[#0A2342]/60">
            Go back to the collection and open one of the available record types.
          </p>
          <Link
            href="/admin/collections"
            className="mt-5 inline-flex items-center rounded-2xl bg-[#00CED1] px-5 py-3 text-sm font-semibold text-white shadow-[0_12px_30px_rgba(0,206,209,0.22)] hover:bg-[#00b8bb]"
          >
            Back to collections
          </Link>
        </section>
      </div>
    );
  }

  const section = getSectionById(sectionId);
  if (!section.documentTypes.includes(documentType)) {
    return (
      <div className="space-y-6">
        <section className="rounded-[30px] border border-[#0A2342]/8 bg-[linear-gradient(135deg,#ecfbfc_0%,#fffaf3_100%)] p-6">
          <p className="text-xs uppercase tracking-[0.28em] text-[#0A2342]/45">Record type not found</p>
          <h1 className="mt-3 text-3xl font-semibold text-[#0A2342]">This record type is not in the selected collection</h1>
          <p className="mt-3 text-sm leading-6 text-[#0A2342]/60">
            Go back to the collection and choose one of its available record types.
          </p>
          <Link
            href={`/admin/collections/${sectionId}`}
            className="mt-5 inline-flex items-center rounded-2xl bg-[#00CED1] px-5 py-3 text-sm font-semibold text-white shadow-[0_12px_30px_rgba(0,206,209,0.22)] hover:bg-[#00b8bb]"
          >
            Back to collection
          </Link>
        </section>
      </div>
    );
  }

  return <DocumentGroupWorkspace sectionId={sectionId} documentType={documentType} mode="overview" />;
}
