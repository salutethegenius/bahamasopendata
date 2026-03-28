'use client';

type SourceLink = {
  label: string;
  url: string;
};

type CoverageRow = {
  page: string;
  status: 'Dynamic' | 'Mixed' | 'Static';
  source: string;
  sourceLinks?: SourceLink[];
  recordTypes: string[];
  notes: string;
};

const rows: CoverageRow[] = [
  {
    page: 'Home',
    status: 'Mixed',
    source: 'Published finance data plus editorial/static modules',
    sourceLinks: [
      { label: 'Budget portal', url: 'https://bahamasbudget.gov.bs/budget/' },
      { label: 'Fiscal reports', url: 'https://bahamasbudget.gov.bs/fiscal/' },
    ],
    recordTypes: ['Budget book', 'Budget communication', 'News updates'],
    notes: 'Core finance cards are live. Some homepage modules still use older editorial or fallback content.',
  },
  {
    page: 'Ministries',
    status: 'Dynamic',
    source: 'Published finance data',
    sourceLinks: [{ label: 'Budget portal', url: 'https://bahamasbudget.gov.bs/budget/' }],
    recordTypes: ['Budget book', 'Budget communication'],
    notes: 'Uses published ministry allocations and inferred sectors from approved finance records.',
  },
  {
    page: 'Revenue',
    status: 'Dynamic',
    source: 'Published finance data',
    sourceLinks: [
      { label: 'Budget portal', url: 'https://bahamasbudget.gov.bs/budget/' },
      { label: 'Fiscal Strategy Reports', url: 'https://www.bahamasbudget.gov.bs/2020/publications/fiscal-strategy-reports/' },
    ],
    recordTypes: ['Revenue estimates'],
    notes: 'Revenue totals and source breakdowns come from published revenue records.',
  },
  {
    page: 'Debt',
    status: 'Mixed',
    source: 'Published debt overview plus fallback schedule data',
    sourceLinks: [{ label: 'Fiscal reports', url: 'https://bahamasbudget.gov.bs/fiscal/' }],
    recordTypes: ['Debt report'],
    notes: 'Debt overview is live. Repayment schedule still falls back to older static content.',
  },
  {
    page: 'Health',
    status: 'Mixed',
    source: 'Published finance and island project data plus static copy',
    recordTypes: ['Health strategy', 'Island projects', 'Budget book'],
    notes: 'Budget share and project allocations are live. Some supporting copy and presentation remain static.',
  },
  {
    page: 'Income',
    status: 'Dynamic',
    source: 'Published indicator datasets',
    sourceLinks: [
      {
        label: 'BNSI household income and expenditure',
        url: 'https://stats.gov.bs/subjects/household-income-and-expenditure/',
      },
      {
        label: 'BNSI publications',
        url: 'https://stats.gov.bs/publications/',
      },
    ],
    recordTypes: ['Economic indicators'],
    notes: 'Income and household comparison views read from published structured indicator rows.',
  },
  {
    page: 'Map',
    status: 'Dynamic',
    source: 'Published island project data',
    recordTypes: ['Island projects'],
    notes: 'Island totals and project lists come from published regional project records.',
  },
  {
    page: 'News',
    status: 'Dynamic',
    source: 'Published updates',
    recordTypes: ['News updates'],
    notes: 'News cards and article links use published update records.',
  },
  {
    page: 'Hot topics',
    status: 'Static',
    source: 'Separate report/static pipeline',
    recordTypes: ['Legal ruling', 'Procurement report'],
    notes: 'This page still uses the older report flow and is not yet on the same publish lifecycle.',
  },
  {
    page: 'Polls',
    status: 'Static',
    source: 'Dedicated polls system',
    recordTypes: [],
    notes: 'Polls are managed through their own database flow, not document publishing.',
  },
  {
    page: 'Export',
    status: 'Mixed',
    source: 'Published dataset availability plus static descriptors',
    sourceLinks: [
      { label: 'Budget portal', url: 'https://bahamasbudget.gov.bs/budget/' },
      { label: 'Fiscal reports', url: 'https://bahamasbudget.gov.bs/fiscal/' },
      {
        label: 'BNSI household income and expenditure',
        url: 'https://stats.gov.bs/subjects/household-income-and-expenditure/',
      },
    ],
    recordTypes: ['Budget book', 'Revenue estimates', 'Debt report', 'Economic indicators', 'Island projects', 'News updates'],
    notes: 'Dataset availability reflects published records, but some descriptive export copy is still static.',
  },
];

function StatusBadge({ status }: { status: CoverageRow['status'] }) {
  const classes =
    status === 'Dynamic'
      ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
      : status === 'Mixed'
        ? 'border-amber-200 bg-amber-50 text-amber-700'
        : 'border-slate-200 bg-slate-100 text-slate-600';

  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-semibold ${classes}`}>
      {status}
    </span>
  );
}

export default function DataCoverageMatrix() {
  const renderSourceLinks = (links?: SourceLink[]) => {
    if (!links?.length) {
      return null;
    }

    return (
      <div className="mt-2 flex flex-wrap gap-2">
        {links.map((link) => (
          <a
            key={link.url}
            href={link.url}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center rounded-full border border-[#0A2342]/10 bg-[#f8fcfc] px-2.5 py-1 text-xs font-medium text-[#0A2342] transition hover:border-[#00CED1]/40 hover:text-[#008b8d]"
          >
            {link.label}
          </a>
        ))}
      </div>
    );
  };

  return (
    <section className="rounded-[28px] border border-[#0A2342]/8 bg-white p-5 shadow-[0_18px_55px_rgba(10,35,66,0.05)] sm:rounded-[30px] sm:p-6">
      <div className="max-w-3xl">
        <p className="text-xs uppercase tracking-[0.28em] text-[#0A2342]/45">Website data matrix</p>
        <h2 className="mt-3 text-2xl font-semibold text-[#0A2342]">Where uploaded data shows up</h2>
        <p className="mt-3 text-sm leading-6 text-[#0A2342]/68 sm:text-[15px]">
          Uploaded files do not appear on the public site immediately. They are stored, reviewed,
          approved, and then published into the live datasets. This matrix shows which public pages
          already use published records and which ones still mix in fallback or static content.
        </p>
      </div>

      <div className="mt-6 space-y-4 lg:hidden">
        {rows.map((row) => (
          <article
            key={row.page}
            className="rounded-[24px] border border-[#0A2342]/8 bg-[linear-gradient(180deg,#ffffff_0%,#fbfdfe_100%)] p-4"
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <h3 className="text-base font-semibold text-[#0A2342]">{row.page}</h3>
                <p className="mt-1 text-xs uppercase tracking-[0.18em] text-[#0A2342]/45">Public page</p>
              </div>
              <StatusBadge status={row.status} />
            </div>
            <div className="mt-4 space-y-3 text-sm text-[#0A2342]/72">
              <div>
                <p className="text-xs uppercase tracking-[0.16em] text-[#0A2342]/42">Source</p>
                <p className="mt-1 leading-6">{row.source}</p>
                {renderSourceLinks(row.sourceLinks)}
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.16em] text-[#0A2342]/42">Record types</p>
                <p className="mt-1 leading-6">{row.recordTypes.length ? row.recordTypes.join(', ') : 'Not record-driven'}</p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.16em] text-[#0A2342]/42">Notes</p>
                <p className="mt-1 leading-6">{row.notes}</p>
              </div>
            </div>
          </article>
        ))}
      </div>

      <div className="mt-6 hidden overflow-hidden rounded-[24px] border border-[#0A2342]/8 lg:block">
        <div className="overflow-x-auto">
          <table className="min-w-full border-collapse text-left">
            <thead className="bg-[#f8fcfc]">
              <tr className="text-xs uppercase tracking-[0.16em] text-[#0A2342]/42">
                <th className="px-4 py-4 font-medium">Page</th>
                <th className="px-4 py-4 font-medium">Status</th>
                <th className="px-4 py-4 font-medium">Source</th>
                <th className="px-4 py-4 font-medium">Record types</th>
                <th className="px-4 py-4 font-medium">Notes</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row, index) => (
                <tr
                  key={row.page}
                  className={index % 2 === 0 ? 'bg-white' : 'bg-[#fcfdfd]'}
                >
                  <td className="px-4 py-4 align-top text-sm font-semibold text-[#0A2342]">{row.page}</td>
                  <td className="px-4 py-4 align-top">
                    <StatusBadge status={row.status} />
                  </td>
                  <td className="px-4 py-4 align-top text-sm leading-6 text-[#0A2342]/72">
                    <p>{row.source}</p>
                    {renderSourceLinks(row.sourceLinks)}
                  </td>
                  <td className="px-4 py-4 align-top text-sm leading-6 text-[#0A2342]/72">
                    {row.recordTypes.length ? row.recordTypes.join(', ') : 'Not record-driven'}
                  </td>
                  <td className="px-4 py-4 align-top text-sm leading-6 text-[#0A2342]/72">{row.notes}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
