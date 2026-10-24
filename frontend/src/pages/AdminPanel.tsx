import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { SLAPolicy, User } from '../types';
import {
  ShieldCheck,
  Play,
  PlusCircle,
  FileText,
  Users,
  Settings,
  Clock,
  History,
  AlertCircle,
  CheckCircle2,
  X,
  Search,
} from 'lucide-react';

export const AdminPanel: React.FC = () => {
  const [overview, setOverview] = useState<any>(null);
  const [policies, setPolicies] = useState<SLAPolicy[]>([]);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);

  // SLA Trigger State
  const [triggeringSla, setTriggeringSla] = useState(false);
  const [slaResult, setSlaResult] = useState<any>(null);

  // New Policy Modal
  const [showPolicyModal, setShowPolicyModal] = useState(false);
  const [newPolicyName, setNewPolicyName] = useState('');
  const [newPolicyCategory, setNewPolicyCategory] = useState('');
  const [newPolicyPriority, setNewPolicyPriority] = useState('');
  const [newPolicyDuration, setNewPolicyDuration] = useState('48');
  const [newPolicyGrace, setNewPolicyGrace] = useState('4');

  // Active Tab
  const [activeTab, setActiveTab] = useState<'policies' | 'audit' | 'users'>('policies');

  const loadData = async () => {
    setLoading(true);
    try {
      const [ov, polRes, audRes, usrRes] = await Promise.all([
        api.getAdminOverview(),
        api.getSLAPolicies(),
        api.getAuditLogs(1),
        api.getAdminUsers(),
      ]);
      setOverview(ov);
      setPolicies(polRes.policies || []);
      setAuditLogs(audRes.audit_logs || []);
      setUsers(usrRes.users || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleTriggerSla = async () => {
    setTriggeringSla(true);
    setSlaResult(null);
    try {
      const res = await api.triggerSLASweep();
      setSlaResult(res.results);
      loadData();
    } catch (err: any) {
      alert(err.message || 'SLA sweep failed.');
    } finally {
      setTriggeringSla(false);
    }
  };

  const handleCreatePolicy = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newPolicyName.trim()) return;

    try {
      await api.createSLAPolicy({
        name: newPolicyName.trim(),
        category: newPolicyCategory || null,
        priority: newPolicyPriority || null,
        duration_hours: Number(newPolicyDuration),
        grace_period_hours: Number(newPolicyGrace),
      });
      setShowPolicyModal(false);
      setNewPolicyName('');
      loadData();
    } catch (err: any) {
      alert(err.message || 'Policy creation failed.');
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-2 rounded-lg bg-purple-500/10 text-purple-600">
              <ShieldCheck className="w-5 h-5" />
            </span>
            <h1 className="text-2xl font-extrabold text-navy-950">System Governance & Administration</h1>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Global SLA policies, immutable municipal audit logs, and on-demand background escalation triggers.
          </p>
        </div>

        <button
          onClick={handleTriggerSla}
          disabled={triggeringSla}
          className="inline-flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold rounded-xl shadow transition disabled:opacity-50"
        >
          <Play className="w-4 h-4 fill-current" />
          {triggeringSla ? 'Evaluating SLAs...' : 'Trigger SLA Background Sweep Now'}
        </button>
      </div>

      {/* SLA Trigger Feedback Banner */}
      {slaResult && (
        <div className="p-4 bg-purple-50 border border-purple-200 text-purple-900 rounded-2xl text-xs space-y-1 shadow-sm">
          <div className="flex items-center gap-2 font-bold">
            <CheckCircle2 className="w-4 h-4 text-purple-600" />
            SLA Evaluation Completed Successfully
          </div>
          <p className="text-[11px] text-purple-700 font-mono">
            Evaluated: {slaResult.evaluated_count} active tickets | Level 1 Warnings: {slaResult.level_1_warnings} | Level 2 Breaches: {slaResult.level_2_breaches} | Level 3 Critical Escalations: {slaResult.level_3_critical_escalations}
          </p>
        </div>
      )}

      {/* Overview Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">Total Users</span>
          <div className="text-2xl font-extrabold text-navy-950 mt-1">{overview?.users?.total ?? 0}</div>
          <div className="text-[10px] text-slate-400 mt-0.5">
            {overview?.users?.citizens} Citizens • {overview?.users?.officers} Officers • {overview?.users?.managers} Managers
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">Departments</span>
          <div className="text-2xl font-extrabold text-navy-950 mt-1">{overview?.operations?.departments ?? 0}</div>
          <div className="text-[10px] text-slate-400 mt-0.5">{overview?.operations?.service_zones} Service Zones</div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">Active SLA Policies</span>
          <div className="text-2xl font-extrabold text-civic-teal-700 mt-1">{overview?.operations?.active_sla_policies ?? 0}</div>
          <div className="text-[10px] text-slate-400 mt-0.5">Configured tier rules</div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <span className="text-[11px] font-semibold text-rose-600 uppercase tracking-wider block">Total Escalations Logged</span>
          <div className="text-2xl font-extrabold text-rose-600 mt-1">{overview?.operations?.total_escalations_logged ?? 0}</div>
          <div className="text-[10px] text-slate-400 mt-0.5">SLA breaches escalated</div>
        </div>
      </div>

      {/* Tab Controls */}
      <div className="flex items-center gap-2 border-b border-slate-200 pb-2">
        <button
          onClick={() => setActiveTab('policies')}
          className={`flex items-center gap-1.5 px-4 py-2 text-xs font-bold rounded-lg transition ${
            activeTab === 'policies' ? 'bg-navy-900 text-white shadow' : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          <Clock className="w-4 h-4" />
          SLA Resolution Policies ({policies.length})
        </button>

        <button
          onClick={() => setActiveTab('audit')}
          className={`flex items-center gap-1.5 px-4 py-2 text-xs font-bold rounded-lg transition ${
            activeTab === 'audit' ? 'bg-navy-900 text-white shadow' : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          <History className="w-4 h-4" />
          Audit Trail Log ({auditLogs.length})
        </button>

        <button
          onClick={() => setActiveTab('users')}
          className={`flex items-center gap-1.5 px-4 py-2 text-xs font-bold rounded-lg transition ${
            activeTab === 'users' ? 'bg-navy-900 text-white shadow' : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          <Users className="w-4 h-4" />
          User Management ({users.length})
        </button>
      </div>

      {/* Tab 1: SLA Policies */}
      {activeTab === 'policies' && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-bold text-sm text-navy-950">Municipal SLA Policies</h3>
              <p className="text-xs text-slate-500">
                Resolution duration targets and escalation thresholds evaluated by the background engine.
              </p>
            </div>
            <button
              onClick={() => setShowPolicyModal(true)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-navy-900 hover:bg-navy-800 text-white text-xs font-semibold rounded-lg shadow transition"
            >
              <PlusCircle className="w-4 h-4" />
              Add Policy
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50 text-slate-600 font-semibold">
                  <th className="py-2.5 px-3">Policy Name</th>
                  <th className="py-2.5 px-3">Target Category</th>
                  <th className="py-2.5 px-3">Priority</th>
                  <th className="py-2.5 px-3">Duration (Hours)</th>
                  <th className="py-2.5 px-3">Grace (Hours)</th>
                  <th className="py-2.5 px-3">Escalation Role</th>
                  <th className="py-2.5 px-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {policies.map(p => (
                  <tr key={p.id} className="hover:bg-slate-50/80">
                    <td className="py-3 px-3 font-semibold text-slate-800">{p.name}</td>
                    <td className="py-3 px-3 text-slate-600">{p.category || 'All Categories'}</td>
                    <td className="py-3 px-3 text-slate-600">{p.priority || 'All Priorities'}</td>
                    <td className="py-3 px-3 font-mono font-bold text-navy-900">{p.duration_hours}h</td>
                    <td className="py-3 px-3 font-mono text-slate-500">{p.grace_period_hours}h</td>
                    <td className="py-3 px-3 text-slate-600 font-medium">{p.escalation_target_role}</td>
                    <td className="py-3 px-3">
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-700">
                        Active
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 2: Audit Logs */}
      {activeTab === 'audit' && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4">
          <div>
            <h3 className="font-bold text-sm text-navy-950">Immutable Audit Trail</h3>
            <p className="text-xs text-slate-500">
              System events, status changes, assignments, and logins captured with timestamp and actor attribution.
            </p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50 text-slate-600 font-semibold">
                  <th className="py-2.5 px-3">Timestamp (UTC)</th>
                  <th className="py-2.5 px-3">Action</th>
                  <th className="py-2.5 px-3">Entity</th>
                  <th className="py-2.5 px-3">Actor</th>
                  <th className="py-2.5 px-3">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {auditLogs.map(log => (
                  <tr key={log.id} className="hover:bg-slate-50/80">
                    <td className="py-2.5 px-3 font-mono text-slate-500 whitespace-nowrap">
                      {new Date(log.created_at).toLocaleString()}
                    </td>
                    <td className="py-2.5 px-3 font-mono font-semibold text-navy-900">{log.action}</td>
                    <td className="py-2.5 px-3 text-slate-600">
                      {log.entity_type} {log.entity_id ? `#${log.entity_id}` : ''}
                    </td>
                    <td className="py-2.5 px-3">
                      <span className="font-semibold text-slate-800">{log.actor_name}</span>{' '}
                      <span className="text-[10px] text-slate-400 font-mono">({log.actor_role})</span>
                    </td>
                    <td className="py-2.5 px-3 font-mono text-[11px] text-slate-500 max-w-xs truncate">
                      {log.details ? JSON.stringify(log.details) : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 3: Users */}
      {activeTab === 'users' && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4">
          <div>
            <h3 className="font-bold text-sm text-navy-950">Registered Users & Staff</h3>
            <p className="text-xs text-slate-500">Citizen accounts and municipal staff credentials.</p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50 text-slate-600 font-semibold">
                  <th className="py-2.5 px-3">Full Name</th>
                  <th className="py-2.5 px-3">Email Address</th>
                  <th className="py-2.5 px-3">Role</th>
                  <th className="py-2.5 px-3">Department</th>
                  <th className="py-2.5 px-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {users.map(u => (
                  <tr key={u.id} className="hover:bg-slate-50/80">
                    <td className="py-2.5 px-3 font-semibold text-slate-800">{u.full_name}</td>
                    <td className="py-2.5 px-3 font-mono text-slate-600">{u.email}</td>
                    <td className="py-2.5 px-3">
                      <span className="font-semibold text-navy-800 bg-navy-50 px-2 py-0.5 rounded text-[11px]">
                        {u.role}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-slate-600">{u.department_name || 'City-Wide'}</td>
                    <td className="py-2.5 px-3">
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-50 text-emerald-700">
                        Active
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* New Policy Modal */}
      {showPolicyModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
          <form
            onSubmit={handleCreatePolicy}
            className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6 border border-slate-200 space-y-4 text-xs"
          >
            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
              <h3 className="font-bold text-sm text-slate-900">Add Municipal SLA Policy</h3>
              <button type="button" onClick={() => setShowPolicyModal(false)} className="text-slate-400">
                <X className="w-4 h-4" />
              </button>
            </div>

            <div>
              <label className="block font-semibold text-slate-700 mb-1">Policy Name</label>
              <input
                type="text"
                required
                value={newPolicyName}
                onChange={e => setNewPolicyName(e.target.value)}
                placeholder="e.g. Critical Hazard Escalation"
                className="w-full border border-slate-200 rounded-lg p-2 outline-none"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Resolution Duration (Hours)</label>
                <input
                  type="number"
                  required
                  min={1}
                  value={newPolicyDuration}
                  onChange={e => setNewPolicyDuration(e.target.value)}
                  className="w-full border border-slate-200 rounded-lg p-2 outline-none"
                />
              </div>
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Grace Period (Hours)</label>
                <input
                  type="number"
                  required
                  min={0}
                  value={newPolicyGrace}
                  onChange={e => setNewPolicyGrace(e.target.value)}
                  className="w-full border border-slate-200 rounded-lg p-2 outline-none"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setShowPolicyModal(false)}
                className="px-4 py-2 font-semibold text-slate-600 hover:bg-slate-100 rounded-lg"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 font-bold text-white bg-navy-900 hover:bg-navy-800 rounded-lg shadow"
              >
                Create Policy
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};
