'use client';

import { usePathname } from 'next/navigation';
import Navigation from './Navigation';

export default function ConditionalNavigation() {
  const pathname = usePathname();

  // Let the v2 marketing page render its own shell
  if (pathname.startsWith('/v2')) {
    return null;
  }

  return <Navigation />;
}

