import AdminShell from '@/components/admin/AdminShell';
import { AdminAuthProvider } from '@/contexts/AdminAuthContext';

export default function AdminLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <AdminAuthProvider>
      <AdminShell>{children}</AdminShell>
    </AdminAuthProvider>
  );
}
