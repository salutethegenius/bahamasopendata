'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { motion } from 'framer-motion';
import Image from 'next/image';
import { 
  LayoutDashboard, 
  Building2, 
  Wallet, 
  CreditCard,
  Map,
  Newspaper,
  Download,
  Menu,
  X,
  DollarSign
} from 'lucide-react';
import { useState } from 'react';
import logo from '@/images/logo.jpeg';

const navItems = [
  { href: '/', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/ministries', label: 'Ministries', icon: Building2 },
  { href: '/revenue', label: 'Revenue', icon: Wallet },
  { href: '/debt', label: 'Debt', icon: CreditCard },
  { href: '/income', label: 'Income', icon: DollarSign },
  { href: '/map', label: 'Map', icon: Map },
  { href: '/news', label: 'News', icon: Newspaper },
];

export default function Navigation() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <>
      {/* Desktop Navigation */}
      <nav className="hidden md:flex fixed top-0 left-0 right-0 bg-white/95 backdrop-blur-sm border-b border-gray-200 z-50">
        <div className="max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-20 lg:h-24">
            {/* Logo */}
            <Link href="/" className="flex items-center gap-3">
              <Image
                src={logo}
                alt="Bahamas Open Data Logo"
                width={120}
                height={72}
                className="h-12 sm:h-14 md:h-16 w-auto object-contain"
                priority
              />
              <span className="font-bold text-lg sm:text-xl md:text-2xl text-gray-900">
                Bahamas<span className="text-turquoise">OpenData</span>
              </span>
            </Link>

            {/* Nav Links */}
            <div className="flex items-center gap-1">
              {navItems.map((item) => {
                const isActive = pathname === item.href;
                const Icon = item.icon;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`
                      relative px-3 py-2 rounded-lg text-sm font-medium transition-colors
                      flex items-center gap-2
                      ${isActive 
                        ? 'text-turquoise' 
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                      }
                    `}
                  >
                    <Icon className="w-4 h-4" />
                    {item.label}
                    {isActive && (
                      <motion.div
                        layoutId="nav-indicator"
                        className="absolute bottom-0 left-0 right-0 h-0.5 bg-turquoise"
                      />
                    )}
                  </Link>
                );
              })}
            </div>

            {/* Download Button */}
            <Link
              href="/export"
              className="flex items-center gap-2 px-4 py-2 bg-turquoise text-white rounded-lg text-sm font-medium hover:bg-turquoise-dark transition-colors"
            >
              <Download className="w-4 h-4" />
              Export Data
            </Link>
          </div>
        </div>
      </nav>

      {/* Mobile Navigation */}
      <nav className="md:hidden fixed top-0 left-0 right-0 bg-white border-b border-gray-200 z-50">
        <div className="flex items-center justify-between h-16 sm:h-18 px-3 sm:px-4 py-2">
          <Link href="/" className="flex items-center gap-2">
            <Image
              src={logo}
              alt="Bahamas Open Data Logo"
              width={100}
              height={60}
              className="h-10 w-auto object-contain"
              priority
            />
            <span className="font-bold text-base sm:text-lg text-gray-900">
              Bahamas<span className="text-turquoise">OpenData</span>
            </span>
          </Link>
          
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="p-2 text-gray-600"
          >
            {mobileOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>

        {/* Mobile Menu */}
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white border-b border-gray-200 py-2"
          >
            {navItems.map((item) => {
              const isActive = pathname === item.href;
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setMobileOpen(false)}
                  className={`
                    flex items-center gap-3 px-4 py-3 text-sm font-medium
                    ${isActive 
                      ? 'text-turquoise bg-turquoise/5' 
                      : 'text-gray-600'
                    }
                  `}
                >
                  <Icon className="w-5 h-5" />
                  {item.label}
                </Link>
              );
            })}
            <Link
              href="/export"
              onClick={() => setMobileOpen(false)}
              className="flex items-center gap-3 px-4 py-3 text-sm font-medium text-turquoise"
            >
              <Download className="w-5 h-5" />
              Export Data
            </Link>
          </motion.div>
        )}
      </nav>

      {/* Spacer */}
      <div className="h-16 sm:h-18 md:h-20 lg:h-24" />
    </>
  );
}

