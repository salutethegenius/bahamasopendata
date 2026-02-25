'use client';

import { usePathname } from 'next/navigation';

export default function ConditionalFooter() {
  const pathname = usePathname();
  
  // Hide footer on home page (maintenance mode)
  if (pathname === '/') {
    return null;
  }
  
  return (
    <footer className="bg-white border-t border-gray-200 py-8 mt-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row justify-between items-center gap-4">
          <div className="text-center md:text-left">
            <p className="font-bold text-gray-900">
              Bahamas<span className="text-turquoise">OpenData</span>
            </p>
            <p className="text-sm text-gray-500">
              Making Bahamas public finance clear and accessible
            </p>
          </div>
          <div className="text-sm text-gray-500 text-center md:text-right">
            <p>Data sourced from official government documents</p>
            <p>© 2025 Registered. Development by Kemis Group of Companies Inc.</p>
          </div>
        </div>
      </div>
    </footer>
  );
}

