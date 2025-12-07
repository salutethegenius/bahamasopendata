'use client';

import { motion } from 'framer-motion';
import { Ministry } from '@/types';
import { formatCurrency, formatPercent, getChangeColor } from '@/lib/format';
import SparklineChart from './SparklineChart';
import { TrendingUp, TrendingDown, ChevronRight } from 'lucide-react';

interface MinistryCardProps {
  ministry: Ministry;
  onClick: () => void;
  index: number;
}

export default function MinistryCard({ ministry, onClick, index }: MinistryCardProps) {
  const TrendIcon = ministry.change_percent > 0 ? TrendingUp : TrendingDown;
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      whileHover={{ scale: 1.02, y: -2 }}
      onClick={onClick}
      className="bg-white rounded-xl border border-gray-200 p-5 cursor-pointer card-hover"
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <p className="text-xs font-medium text-turquoise uppercase tracking-wide mb-1">
            {ministry.sector}
          </p>
          <h3 className="font-semibold text-gray-900 truncate pr-2">
            {ministry.name.replace('Ministry of ', '')}
          </h3>
        </div>
        <ChevronRight className="w-5 h-5 text-gray-400 flex-shrink-0" />
      </div>
      
      <div className="flex items-end justify-between">
        <div>
          <p className="text-2xl font-bold text-gray-900 tabular-nums">
            {formatCurrency(ministry.allocation, true)}
          </p>
          <div className={`flex items-center gap-1 mt-1 text-sm ${getChangeColor(ministry.change_percent)}`}>
            <TrendIcon className="w-3.5 h-3.5" />
            <span className="font-medium">{formatPercent(ministry.change_percent)}</span>
            <span className="text-gray-400">YoY</span>
          </div>
        </div>
        
        <div className="w-20">
          <SparklineChart 
            data={ministry.sparkline} 
            color={ministry.change_percent >= 0 ? '#10b981' : '#ef4444'}
          />
        </div>
      </div>
    </motion.div>
  );
}

