'use client';

import { usePathname } from 'next/navigation';
import Navigation from './Navigation';

export default function ConditionalNavigation() {
  const pathname = usePathname();

  // Let imprint / admin shells render without the civic nav chrome
  if (
    pathname.startsWith('/v2') ||
    pathname.startsWith('/admin') ||
    pathname.startsWith('/intelligence')
  ) {
    return null;
  }

  return <Navigation />;
}
