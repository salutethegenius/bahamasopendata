'use client';

import { motion } from 'framer-motion';
import { formatCurrency, formatPercent, getChangeColor } from '@/lib/format';
import { FileText, TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: number;
  change?: number;
  subtitle?: string;
  format?: 'currency' | 'percent' | 'number';
  sourceDocument?: string;
  sourcePage?: number;
  compact?: boolean;
  onClick?: () => void;
}

export default function StatCard({
  title,
  value,
  change,
  subtitle,
  format = 'currency',
  sourceDocument,
  sourcePage,
  compact = false,
  onClick,
}: StatCardProps) {
  const formattedValue = format === 'currency' 
    ? formatCurrency(value, true)
    : format === 'percent'
    ? `${value.toFixed(1)}%`
    : value.toLocaleString();

  const TrendIcon = change && change > 0 ? TrendingUp : change && change < 0 ? TrendingDown : Minus;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: onClick ? 1.02 : 1 }}
      onClick={onClick}
      className={`
        bg-white rounded-xl border border-gray-200 p-6
        ${onClick ? 'cursor-pointer card-hover' : ''}
        ${compact ? 'p-4' : 'p-6'}
      `}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-gray-500 mb-1">{title}</p>
          <p className={`font-bold text-turquoise tabular-nums ${compact ? 'text-2xl' : 'text-3xl'}`}>
            {formattedValue}
          </p>
          {subtitle && (
            <p className="text-sm text-gray-500 mt-1">{subtitle}</p>
          )}
        </div>
        
        {change !== undefined && (
          <div className={`flex items-center gap-1 px-2 py-1 rounded-full text-sm font-medium ${
            change > 0 ? 'bg-green-100 text-green-700' : 
            change < 0 ? 'bg-red-100 text-red-700' : 
            'bg-gray-100 text-gray-600'
          }`}>
            <TrendIcon className="w-3 h-3" />
            <span>{formatPercent(change)}</span>
          </div>
        )}
      </div>

      {sourceDocument && (
        <div className="mt-4 pt-3 border-t border-gray-100">
          <button className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-turquoise transition-colors">
            <FileText className="w-3 h-3" />
            <span>{sourceDocument}{sourcePage ? `, p.${sourcePage}` : ''}</span>
          </button>
        </div>
      )}
    </motion.div>
  );
}

