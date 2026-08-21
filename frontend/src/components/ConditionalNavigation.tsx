'use client';

import { usePathname } from 'next/navigation';
import Navigation from './Navigation';

export default function ConditionalNavigation() {
  const pathname = usePathname();

  // Marketing home, admin, and intelligence use their own chrome
  if (
    pathname === '/' ||
    pathname.startsWith('/admin') ||
    pathname.startsWith('/intelligence')
  ) {
    return null;
  }

  return <Navigation />;
}
