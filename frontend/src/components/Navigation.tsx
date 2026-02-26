'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { motion } from 'framer-motion';
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
  DollarSign,
  HeartPulse,
  BarChart3,
  ChevronDown,
  Flame,
} from 'lucide-react';
import { useState } from 'react';

type NavItem = {
  id: string;
  href: string;
  label: string;
  icon: typeof LayoutDashboard;
  domain?: string;
};

const primaryNavItems: NavItem[] = [
  { id: 'dashboard', href: '/', label: 'Dashboard', icon: LayoutDashboard, domain: 'overview' },
  { id: 'health', href: '/health', label: 'Health', icon: HeartPulse, domain: 'health' },
  { id: 'income', href: '/income', label: 'Income', icon: DollarSign, domain: 'income' },
];

const budgetNavItems: NavItem[] = [
  { id: 'revenue', href: '/revenue', label: 'Revenue', icon: Wallet, domain: 'revenue' },
  { id: 'debt', href: '/debt', label: 'Debt', icon: CreditCard, domain: 'debt' },
  { id: 'map', href: '/map', label: 'Map', icon: Map, domain: 'geography' },
  { id: 'ministries', href: '/ministries', label: 'Ministries', icon: Building2, domain: 'ministries' },
];

const tailNavItems: NavItem[] = [
  { id: 'polls', href: '/polls', label: 'Polls', icon: BarChart3, domain: 'polls' },
  { id: 'news', href: '/news', label: 'News', icon: Newspaper, domain: 'news' },
  { id: 'hot', href: '/hot', label: 'Hot topics', icon: Flame, domain: 'hot' },
];

export default function Navigation() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [budgetOpen, setBudgetOpen] = useState(false);

  const isBudgetActive = budgetNavItems.some(
    (item) => pathname === item.href || pathname.startsWith(`${item.href}/`),
  );

  return (
    <>
      {/* Desktop Navigation */}
      <nav className="hidden md:flex fixed top-0 left-0 right-0 bg-white/95 backdrop-blur-sm border-b border-gray-200 z-50">
        <div className="max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-20 lg:h-24">
            {/* Logo */}
            <Link href="/" className="flex items-center gap-3">
              <span className="font-bold text-lg sm:text-xl md:text-2xl text-gray-900">
                Bahamas<span className="text-turquoise">OpenData</span>
              </span>
            </Link>

            {/* Nav Links */}
            <div className="flex items-center gap-1">
              {primaryNavItems.map((item) => {
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

              {/* National Budget dropdown */}
              <div
                className="relative"
                onMouseEnter={() => setBudgetOpen(true)}
                onMouseLeave={() => setBudgetOpen(false)}
              >
                <button
                  type="button"
                  className={`
                    relative px-3 py-2 rounded-lg text-sm font-medium transition-colors
                    flex items-center gap-2
                    ${isBudgetActive || budgetOpen
                      ? 'text-turquoise'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                    }
                  `}
                >
                  <LayoutDashboard className="w-4 h-4" />
                  National Budget
                  <ChevronDown className="w-3 h-3" />
                  {isBudgetActive && (
                    <motion.div
                      layoutId="nav-indicator"
                      className="absolute bottom-0 left-0 right-0 h-0.5 bg-turquoise"
                    />
                  )}
                </button>
                {budgetOpen && (
                  <div className="absolute right-0 mt-2 w-52 bg-white border border-gray-200 rounded-lg shadow-lg py-1 z-50">
                    {budgetNavItems.map((item) => {
                      const isActive = pathname === item.href;
                      const Icon = item.icon;
                      return (
                        <Link
                          key={item.href}
                          href={item.href}
                          className={`
                            flex items-center gap-2 px-3 py-2 text-sm
                            ${isActive ? 'text-turquoise bg-turquoise/5' : 'text-gray-700 hover:bg-gray-100'}
                          `}
                        >
                          <Icon className="w-4 h-4" />
                          {item.label}
                        </Link>
                      );
                    })}
                  </div>
                )}
              </div>

              {tailNavItems.map((item) => {
                const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
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
                {primaryNavItems.map((item) => {
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

                <div className="px-4 pt-2 pb-1 text-xs font-semibold text-gray-400 uppercase">
                  National Budget
                </div>
                {budgetNavItems.map((item) => {
                  const isActive = pathname === item.href;
                  const Icon = item.icon;
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      onClick={() => setMobileOpen(false)}
                      className={`
                        flex items-center gap-3 px-6 py-2 text-sm
                        ${isActive 
                          ? 'text-turquoise bg-turquoise/5' 
                          : 'text-gray-600'
                        }
                      `}
                    >
                      <Icon className="w-4 h-4" />
                      {item.label}
                    </Link>
                  );
                })}

                {tailNavItems.map((item) => {
                  const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
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

