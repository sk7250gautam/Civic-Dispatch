import React from 'react';
import { ComplaintPriority } from '../types';
import { AlertTriangle, AlertCircle, Clock, ShieldAlert } from 'lucide-react';

interface PriorityBadgeProps {
  priority: ComplaintPriority | string;
  showIcon?: boolean;
}

const PRIORITY_CONFIG: Record<string, { label: string; bg: string; text: string; border: string; icon: any }> = {
  CRITICAL: {
    label: 'Critical Hazard',
    bg: 'bg-rose-50',
    text: 'text-rose-700',
    border: 'border-rose-300',
    icon: ShieldAlert,
  },
  HIGH: {
    label: 'High Priority',
    bg: 'bg-amber-50',
    text: 'text-amber-700',
    border: 'border-amber-300',
    icon: AlertTriangle,
  },
  MEDIUM: {
    label: 'Medium Priority',
    bg: 'bg-sky-50',
    text: 'text-sky-700',
    border: 'border-sky-300',
    icon: AlertCircle,
  },
  LOW: {
    label: 'Low Priority',
    bg: 'bg-slate-50',
    text: 'text-slate-600',
    border: 'border-slate-300',
    icon: Clock,
  },
};

export const PriorityBadge: React.FC<PriorityBadgeProps> = ({ priority, showIcon = true }) => {
  const config = PRIORITY_CONFIG[priority] || PRIORITY_CONFIG.MEDIUM;
  const Icon = config.icon;

  return (
    <span
      className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold border ${config.bg} ${config.text} ${config.border}`}
    >
      {showIcon && <Icon className="w-3.5 h-3.5" />}
      {config.label}
    </span>
  );
};
