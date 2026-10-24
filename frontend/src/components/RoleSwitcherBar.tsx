import React from 'react';
import { useAuth } from '../context/AuthContext';
import { Role } from '../types';
import { User, HardHat, Building2, ShieldCheck, Sparkles } from 'lucide-react';

interface RoleOption {
  role: Role;
  label: string;
  sublabel: string;
  icon: any;
  color: string;
}

const ROLES: RoleOption[] = [
  { role: 'CITIZEN', label: 'Citizen', sublabel: 'Priya Sharma', icon: User, color: 'text-sky-400' },
  { role: 'FIELD_OFFICER', label: 'Field Officer', sublabel: 'Rajesh Kumar', icon: HardHat, color: 'text-amber-400' },
  { role: 'DEPARTMENT_MANAGER', label: 'Dept Manager', sublabel: 'Anita Desai', icon: Building2, color: 'text-emerald-400' },
  { role: 'SYSTEM_ADMIN', label: 'Admin', sublabel: 'Vikram Mehta', icon: ShieldCheck, color: 'text-purple-400' },
];

export const RoleSwitcherBar: React.FC = () => {
  const { user, switchRole, loading } = useAuth();

  return (
    <div className="bg-navy-950 text-slate-200 border-b border-navy-800 text-xs py-2 px-4 shadow-sm sticky top-0 z-50">
      <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="flex items-center gap-1.5 font-semibold text-civic-teal-300">
            <Sparkles className="w-3.5 h-3.5" />
            Recruiter Demo Sandbox
          </span>
          <span className="hidden md:inline text-slate-400">| Switch role to test live RBAC & views:</span>
        </div>

        <div className="flex items-center gap-1.5 flex-wrap">
          {ROLES.map(({ role, label, sublabel, icon: Icon, color }) => {
            const isActive = user?.role === role;
            return (
              <button
                key={role}
                onClick={() => switchRole(role)}
                disabled={loading || isActive}
                className={`flex items-center gap-1.5 px-3 py-1 rounded-md transition-all font-medium border ${
                  isActive
                    ? 'bg-civic-teal-600 text-white border-civic-teal-500 shadow'
                    : 'bg-navy-900/80 hover:bg-navy-800 text-slate-300 border-navy-700/60'
                }`}
                title={`Switch to ${label} (${sublabel})`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-white' : color}`} />
                <span>{label}</span>
                {isActive && <span className="ml-1 text-[10px] bg-civic-teal-800 px-1.5 py-0.2 rounded">Active</span>}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};
