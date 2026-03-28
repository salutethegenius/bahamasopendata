'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { BookText, Database, KeyRound, LogOut, Sparkles, Telescope } from 'lucide-react';
import { useAdminAuth } from '@/contexts/AdminAuthContext';

const navItems = [
  { href: '/admin/collections', label: 'Collections', icon: Database },
  { href: '/admin/api-keys', label: 'Access', icon: KeyRound },
  { href: '/admin/logs', label: 'Logs', icon: BookText },
  { href: '/admin/future-updates', label: 'Future updates', icon: Telescope },
];

export default function AdminSidebar() {
  const pathname = usePathname();
  const { user, logout } = useAdminAuth();

  return (
    <aside className="flex w-full flex-col overflow-hidden rounded-[28px] border border-[#0A2342]/8 bg-white/95 p-4 text-[#0A2342] shadow-[0_24px_80px_rgba(10,35,66,0.08)] lg:h-full lg:rounded-[32px] lg:p-5">
      <div className="mb-6 flex min-w-0 items-center gap-3 lg:mb-8">
        <div className="rounded-2xl bg-[#00CED1]/14 p-3 text-[#0A2342]">
          <Sparkles className="h-5 w-5" />
        </div>
        <div className="min-w-0">
          <p className="text-sm uppercase tracking-[0.24em] text-[#0A2342]/45">Admin</p>
          <p className="break-words text-xl font-semibold">Bahamas Open Data</p>
        </div>
      </div>

      <nav className="flex flex-wrap gap-2 lg:block lg:space-y-2">
        {navItems
          .filter((item) => {
            if (item.href === '/admin/collections') {
              return true;
            }
            if (item.href === '/admin/future-updates') {
              return user?.role === 'superuser';
            }
            return ['admin', 'superuser'].includes(user?.role ?? '');
          })
          .map((item) => {
          const isActive =
            pathname === item.href ||
            (item.href === '/admin/collections' && pathname.startsWith('/admin/collections/'));
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`inline-flex min-w-0 items-center gap-3 rounded-2xl px-4 py-3 text-sm font-medium ${
                isActive
                  ? 'bg-[#00CED1] text-white shadow-[0_12px_30px_rgba(0,206,209,0.25)]'
                  : 'text-[#0A2342]/72 hover:bg-[#f0fafb] hover:text-[#0A2342]'
              }`}
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="mt-6 min-w-0 rounded-[24px] border border-[#0A2342]/8 bg-[#f8fcfc] p-4 lg:mt-auto">
        <p className="text-xs uppercase tracking-[0.22em] text-[#0A2342]/42">Signed in</p>
        <p className="mt-2 break-words font-semibold">{user?.full_name || 'Admin operator'}</p>
        <p className="break-all text-sm text-[#0A2342]/60">{user?.email}</p>
        <button
          type="button"
          onClick={() => void logout()}
          className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-xl border border-[#0A2342]/10 px-3 py-2 text-sm text-[#0A2342]/72 hover:bg-white hover:text-[#0A2342] sm:w-auto"
        >
          <LogOut className="h-4 w-4" />
          Log out
        </button>
      </div>
    </aside>
  );
}
