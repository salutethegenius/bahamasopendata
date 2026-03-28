'use client';

type PaginationControlsProps = {
  currentPage: number;
  totalPages: number;
  totalItems: number;
  pageSize: number;
  itemLabel: string;
  onPageChange: (page: number) => void;
};

export default function PaginationControls({
  currentPage,
  totalPages,
  totalItems,
  pageSize,
  itemLabel,
  onPageChange,
}: PaginationControlsProps) {
  if (totalPages <= 1) {
    return null;
  }

  const start = (currentPage - 1) * pageSize + 1;
  const end = Math.min(currentPage * pageSize, totalItems);

  return (
    <div className="mt-5 flex flex-col gap-3 rounded-[22px] border border-[#0A2342]/8 bg-[linear-gradient(135deg,#f7fcfc_0%,#fffaf3_100%)] px-4 py-4 sm:flex-row sm:items-center sm:justify-between">
      <p className="text-sm text-[#0A2342]/60">
        Showing {start}-{end} of {totalItems} {itemLabel}
      </p>
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage <= 1}
          className="rounded-xl border border-[#0A2342]/10 bg-white px-3 py-2 text-sm font-medium text-[#0A2342] disabled:cursor-not-allowed disabled:opacity-40"
        >
          Previous
        </button>
        <span className="px-3 text-sm text-[#0A2342]/60">
          Page {currentPage} of {totalPages}
        </span>
        <button
          type="button"
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage >= totalPages}
          className="rounded-xl border border-[#0A2342]/10 bg-white px-3 py-2 text-sm font-medium text-[#0A2342] disabled:cursor-not-allowed disabled:opacity-40"
        >
          Next
        </button>
      </div>
    </div>
  );
}
