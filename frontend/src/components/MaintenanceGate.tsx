'use client';

import { usePathname } from 'next/navigation';
import { motion } from 'framer-motion';
import ConditionalNavigation from './ConditionalNavigation';
import ConditionalFooter from './ConditionalFooter';
import { MAINTENANCE_MODE } from '@/lib/maintenance';

export default function MaintenanceGate({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();

  // Keep the admin area reachable so the team can keep working.
  const showMaintenance = MAINTENANCE_MODE && !pathname.startsWith('/admin');

  if (showMaintenance) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center px-6 text-center">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          className="max-w-lg w-full"
        >
          <p className="text-2xl md:text-3xl font-bold text-[var(--ocean)] mb-8">
            Bahamas<span className="text-turquoise">OpenData</span>
          </p>

          <h1 className="text-3xl md:text-4xl font-bold text-[var(--ocean)] mb-4">
            We&apos;ll be right back
          </h1>
          <p className="text-lg text-gray-600">
            We&apos;re working on adding the new budget for you!
          </p>

          <div className="mt-10 flex items-center justify-center gap-2 text-xs uppercase tracking-[0.2em] text-turquoise font-semibold">
            <span className="h-1.5 w-1.5 rounded-full bg-turquoise animate-pulse" />
            Updating now
          </div>
        </motion.div>
      </div>
    );
  }

  return (
    <>
      <ConditionalNavigation />
      <main className="min-h-screen">{children}</main>
      <ConditionalFooter />
    </>
  );
}
