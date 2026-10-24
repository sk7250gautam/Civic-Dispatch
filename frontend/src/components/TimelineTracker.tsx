import React from 'react';
import { StatusHistory } from '../types';
import { StatusBadge } from './StatusBadge';
import { CheckCircle2, Clock, UserCheck, AlertCircle } from 'lucide-react';

interface TimelineTrackerProps {
  history: StatusHistory[];
}

export const TimelineTracker: React.FC<TimelineTrackerProps> = ({ history }) => {
  if (!history || history.length === 0) {
    return <div className="text-xs text-slate-500 italic p-3">No history events logged yet.</div>;
  }

  // Chronological order
  const sorted = [...history].sort(
    (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
  );

  return (
    <div className="flow-root">
      <ul className="-mb-8">
        {sorted.map((item, idx) => {
          const isLast = idx === sorted.length - 1;
          return (
            <li key={item.id || idx}>
              <div className="relative pb-8">
                {!isLast && (
                  <span
                    className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-slate-200"
                    aria-hidden="true"
                  />
                )}
                <div className="relative flex space-x-3 items-start">
                  <div>
                    <span className="h-8 w-8 rounded-full bg-slate-100 flex items-center justify-center ring-4 ring-white text-navy-800">
                      {item.new_status === 'RESOLVED' || item.new_status === 'CLOSED' ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                      ) : item.new_status === 'REOPENED' ? (
                        <AlertCircle className="w-4 h-4 text-rose-600" />
                      ) : (
                        <Clock className="w-4 h-4 text-slate-500" />
                      )}
                    </span>
                  </div>
                  <div className="min-w-0 flex-1 pt-1 flex justify-between space-x-4">
                    <div>
                      <div className="flex items-center gap-2">
                        <StatusBadge status={item.new_status} size="sm" />
                        <span className="text-xs text-slate-500">
                          by <strong className="text-slate-700">{item.acting_user_name}</strong> ({item.acting_user_role})
                        </span>
                      </div>
                      {item.reason && (
                        <p className="mt-1 text-xs text-slate-600 bg-slate-50 p-2 rounded border border-slate-100">
                          {item.reason}
                        </p>
                      )}
                    </div>
                    <div className="text-right text-[11px] whitespace-nowrap text-slate-400 font-mono">
                      {new Date(item.created_at).toLocaleString([], {
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </div>
                  </div>
                </div>
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
};
