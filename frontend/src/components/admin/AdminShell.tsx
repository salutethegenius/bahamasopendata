'use client';

import { useEffect } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import AdminSidebar from '@/components/admin/AdminSidebar';
import { useAdminAuth } from '@/contexts/AdminAuthContext';

export default function AdminShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, isLoading } = useAdminAuth();

  const isLoginPage = pathname === '/admin/login';

  useEffect(() => {
    if (isLoading || isLoginPage) {
      return;
    }
    if (!user) {
      router.replace('/admin/login');
    }
  }, [isLoading, isLoginPage, router, user]);

  if (isLoginPage) {
    return <>{children}</>;
  }

  if (isLoading || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[linear-gradient(180deg,#f7fbfc_0%,#eef6f7_55%,#f8f4ec_100%)]">
        <div className="rounded-[28px] border border-[#00CED1]/12 bg-white px-8 py-6 shadow-[0_24px_80px_rgba(10,35,66,0.08)]">
          <p className="text-sm uppercase tracking-[0.24em] text-[#0A2342]/45">Loading admin</p>
          <p className="mt-2 text-lg font-semibold text-[#0A2342]">Checking your session…</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen overflow-x-hidden bg-[radial-gradient(circle_at_top_left,_rgba(0,206,209,0.16),_transparent_28%),radial-gradient(circle_at_bottom_right,_rgba(252,209,22,0.12),_transparent_24%),linear-gradient(180deg,#f7fbfc_0%,#eef6f7_55%,#f8f4ec_100%)] px-3 py-3 sm:px-5 sm:py-5 lg:px-8">
      <div className="mx-auto grid min-h-[calc(100vh-1.5rem)] max-w-[1380px] gap-4 lg:min-h-[calc(100vh-2.5rem)] lg:grid-cols-[260px_minmax(0,1fr)]">
        <AdminSidebar />
        <div className="min-w-0 overflow-hidden rounded-[28px] border border-[#0A2342]/8 bg-white/90 p-4 shadow-[0_24px_80px_rgba(10,35,66,0.08)] backdrop-blur sm:p-5 lg:rounded-[32px]">
          {children}
        </div>
      </div>
    </div>
  );
}
