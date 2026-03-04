'use client';

import { ReactNode } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';

type IconType = React.ComponentType<React.SVGProps<SVGSVGElement>>;

interface DashboardSectionCardProps {
  href: string;
  title: string;
  subtitle?: string;
  icon: IconType;
  primaryStatLabel?: string;
  primaryStatValue?: ReactNode;
  secondaryStatLabel?: string;
  secondaryStatValue?: ReactNode;
  children?: ReactNode;
}

export default function DashboardSectionCard({
  href,
  title,
  subtitle,
  icon: Icon,
  primaryStatLabel,
  primaryStatValue,
  secondaryStatLabel,
  secondaryStatValue,
  children,
}: DashboardSectionCardProps) {
  return (
    <Link href={href} className="block group">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        whileHover={{ y: -2, scale: 1.01 }}
        transition={{ type: 'spring', stiffness: 260, damping: 20 }}
        className="bg-white rounded-xl border border-gray-200 p-5 h-full flex flex-col justify-between shadow-sm hover:shadow-md transition-shadow"
      >
        <div className="flex items-start gap-3 mb-4">
          <div className="w-9 h-9 rounded-full bg-turquoise/10 flex items-center justify-center flex-shrink-0">
            <Icon className="w-4 h-4 text-turquoise" />
          </div>
          <div className="min-w-0">
            <h3 className="text-sm font-semibold text-gray-900 truncate">
              {title}
            </h3>
            {subtitle && (
              <p className="mt-0.5 text-xs text-gray-500 line-clamp-2">
                {subtitle}
              </p>
            )}
          </div>
        </div>

        {(primaryStatLabel || secondaryStatLabel || children) && (
          <div className="space-y-3">
            {primaryStatLabel && (
              <div>
                <p className="text-[11px] uppercase tracking-wide text-gray-500 mb-0.5">
                  {primaryStatLabel}
                </p>
                <div className="text-lg font-semibold text-gray-900 tabular-nums">
                  {primaryStatValue}
                </div>
              </div>
            )}

            {secondaryStatLabel && (
              <div>
                <p className="text-[11px] uppercase tracking-wide text-gray-500 mb-0.5">
                  {secondaryStatLabel}
                </p>
                <div className="text-sm font-medium text-gray-700 tabular-nums">
                  {secondaryStatValue}
                </div>
              </div>
            )}

            {children && (
              <div className="mt-1">
                {children}
              </div>
            )}
          </div>
        )}

        <div className="mt-4 pt-3 border-t border-gray-100 flex items-center justify-between text-xs text-gray-500">
          <span className="group-hover:text-turquoise transition-colors">
            Explore details
          </span>
          <span className="text-gray-400 group-hover:text-turquoise transition-colors">
            →
          </span>
        </div>
      </motion.div>
    </Link>
  );
}

