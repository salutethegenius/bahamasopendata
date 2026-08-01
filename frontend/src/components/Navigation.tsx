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
  History,
  Landmark,
} from 'lucide-react';
import { useState, useRef } from 'react';

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
  { id: 'grand-bahama', href: '/grand-bahama', label: 'Grand Bahama', icon: Landmark, domain: 'grand-bahama' },
];

const budgetNavItems: NavItem[] = [
  { id: 'revenue', href: '/revenue', label: 'Revenue', icon: Wallet, domain: 'revenue' },
  { id: 'debt', href: '/debt', label: 'Debt', icon: CreditCard, domain: 'debt' },
  { id: 'map', href: '/map', label: 'Map', icon: Map, domain: 'geography' },
  { id: 'ministries', href: '/ministries', label: 'Ministries', icon: Building2, domain: 'ministries' },
  { id: 'past-budgets', href: '/budget/history', label: 'Past Budgets', icon: History, domain: 'budget' },
];

const tailNavItems: NavItem[] = [
  { id: 'polls', href: '/polls', label: 'Polls', icon: BarChart3, domain: 'polls' },
  { id: 'news', href: '/news', label: 'News', icon: Newspaper, domain: 'news' },
  { id: 'hot', href: '/hot', label: 'Hot topics', icon: Flame, domain: 'hot' },
  {
    id: 'intelligence',
    href: '/intelligence',
    label: 'Intelligence',
    icon: BarChart3,
    domain: 'intelligence',
  },
];

export default function Navigation() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [budgetOpen, setBudgetOpen] = useState(false);
  const budgetCloseTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const openBudgetMenu = () => {
    if (budgetCloseTimer.current) {
      clearTimeout(budgetCloseTimer.current);
      budgetCloseTimer.current = null;
    }
    setBudgetOpen(true);
  };

  const closeBudgetMenu = () => {
    budgetCloseTimer.current = setTimeout(() => setBudgetOpen(false), 120);
  };

  const isBudgetActive = budgetNavItems.some(
    (item) => pathname === item.href || pathname.startsWith(`${item.href}/`),
  ) || pathname.startsWith('/budget/');

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
                        layoutId={`nav-indicator-${item.id}`}
                        className="absolute bottom-0 left-0 right-0 h-0.5 bg-turquoise"
                      />
                    )}
                  </Link>
                );
              })}

              {/* National Budget dropdown */}
              <div
                className="relative"
                onMouseEnter={openBudgetMenu}
                onMouseLeave={closeBudgetMenu}
              >
                <button
                  type="button"
                  aria-expanded={budgetOpen}
                  aria-haspopup="true"
                  className={`
                    relative px-3 py-2 rounded-lg text-sm font-medium transition-colors
                    flex items-center gap-2
                    ${isBudgetActive || budgetOpen
                      ? 'text-turquoise bg-turquoise/5'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                    }
                  `}
                >
                  <LayoutDashboard className="w-4 h-4" />
                  National Budget
                  <ChevronDown
                    className={`w-3 h-3 transition-transform duration-150 ${budgetOpen ? 'rotate-180' : ''}`}
                  />
                  {isBudgetActive && (
                    <motion.div
                      layoutId="nav-indicator-budget"
                      className="absolute bottom-0 left-0 right-0 h-0.5 bg-turquoise"
                    />
                  )}
                </button>
                {budgetOpen && (
                  <div className="absolute right-0 top-full z-50 w-52 pt-2">
                    <div className="rounded-lg border border-gray-200 bg-white py-1 shadow-lg">
                      {budgetNavItems.map((item) => {
                        const isActive = pathname === item.href;
                        const Icon = item.icon;
                        return (
                          <Link
                            key={item.href}
                            href={item.href}
                            className={`
                              flex items-center gap-2 px-3 py-2 text-sm transition-colors
                              ${isActive
                                ? 'bg-turquoise/5 text-turquoise'
                                : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'}
                            `}
                          >
                            <Icon className="w-4 h-4" />
                            {item.label}
                          </Link>
                        );
                      })}
                    </div>
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
                        layoutId={`nav-indicator-${item.id}`}
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

