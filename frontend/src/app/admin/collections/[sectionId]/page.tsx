'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import SectionWorkspace from '@/components/admin/SectionWorkspace';
import { isAdminSectionId } from '@/lib/admin-collections';

export default function AdminCollectionPage() {
  const params = useParams<{ sectionId: string }>();
  const sectionId = Array.isArray(params.sectionId) ? params.sectionId[0] : params.sectionId;

  if (!sectionId || !isAdminSectionId(sectionId)) {
    return (
      <div className="space-y-6">
        <section className="rounded-[30px] border border-[#0A2342]/8 bg-[linear-gradient(135deg,#ecfbfc_0%,#fffaf3_100%)] p-6">
          <p className="text-xs uppercase tracking-[0.28em] text-[#0A2342]/45">Collection not found</p>
          <h1 className="mt-3 text-3xl font-semibold text-[#0A2342]">This collection does not exist</h1>
          <p className="mt-3 text-sm leading-6 text-[#0A2342]/60">
            Go back to the collections page and open one of the available collections.
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

  return <SectionWorkspace sectionId={sectionId} />;
}
