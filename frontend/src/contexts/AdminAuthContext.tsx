'use client';

import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import { bootstrapAdminSession } from '@/lib/admin-api';
import { loginAdmin, logoutAdmin } from '@/lib/auth';
import type { AdminUser } from '@/types/admin';

type AdminAuthContextValue = {
  user: AdminUser | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<AdminUser>;
  logout: () => Promise<void>;
  refresh: () => Promise<AdminUser | null>;
};

const AdminAuthContext = createContext<AdminAuthContextValue | undefined>(undefined);

export function AdminAuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AdminUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refresh = async () => {
    try {
      const sessionUser = await bootstrapAdminSession();
      setUser(sessionUser);
      return sessionUser;
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void refresh();
  }, []);

  const value = useMemo<AdminAuthContextValue>(
    () => ({
      user,
      isLoading,
      login: async (email, password) => {
        const response = await loginAdmin(email, password);
        setUser(response.user);
        return response.user;
      },
      logout: async () => {
        await logoutAdmin();
        setUser(null);
      },
      refresh,
    }),
    [isLoading, user],
  );

  return (
    <AdminAuthContext.Provider value={value}>
      {children}
    </AdminAuthContext.Provider>
  );
}

export function useAdminAuth() {
  const context = useContext(AdminAuthContext);
  if (!context) {
    throw new Error('useAdminAuth must be used inside AdminAuthProvider');
  }
  return context;
}
