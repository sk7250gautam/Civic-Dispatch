import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { ManagerDashboardData, Complaint } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { PriorityBadge } from '../components/PriorityBadge';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import {
  Building2,
  TrendingUp,
  AlertTriangle,
  Clock,
  CheckCircle2,
  Download,
  Users,
  Search,
  UserCheck,
  Ban,
  X,
  FileSpreadsheet,
} from 'lucide-react';

const PIE_COLORS = ['#08bfa6', '#3970a9', '#f59e0b', '#f43f5e', '#8b5cf6', '#64748b'];

export const ManagerCommandCenter: React.FC = () => {
  const [dashboardData, setDashboardData] = useState<ManagerDashboardData | null>(null);
  const [complaints, setComplaints] = useState<Complaint[]>([]);
  const [officers, setOfficers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [statusFilter, setStatusFilter] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');
  const [searchTerm, setSearchTerm] = useState('');

  // Reassign Modal
  const [reassignTicket, setReassignTicket] = useState<Complaint | null>(null);
  const [selectedOfficerId, setSelectedOfficerId] = useState<number | ''>('');
  const [assignNotes, setAssignNotes] = useState('');

  // Reject Modal
  const [rejectTicket, setRejectTicket] = useState<Complaint | null>(null);
  const [rejectReason, setRejectReason] = useState('');

  const loadData = async () => {
    setLoading(true);
    try {
      const [dash, compRes, offRes] = await Promise.all([
        api.getManagerDashboard(),
        api.getDepartmentComplaints({
          status: statusFilter || undefined,
          priority: priorityFilter || undefined,
          search: searchTerm || undefined,
        }),
        api.getDepartmentOfficers(),
      ]);
      setDashboardData(dash);
      setComplaints(compRes.complaints || []);
      setOfficers(offRes.officers || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [statusFilter, priorityFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadData();
  };

  const handleAssignSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reassignTicket || !selectedOfficerId) return;

    try {
      await api.assignOfficer(reassignTicket.id, Number(selectedOfficerId), assignNotes);
      setReassignTicket(null);
      setSelectedOfficerId('');
      setAssignNotes('');
      loadData();
    } catch (err: any) {
      alert(err.message || 'Assignment failed.');
    }
  };

  const handleRejectSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!rejectTicket || !rejectReason.trim()) return;

    try {
      await api.rejectComplaint(rejectTicket.id, rejectReason.trim());
      setRejectTicket(null);
      setRejectReason('');
      loadData();
    } catch (err: any) {
      alert(err.message || 'Rejection failed.');
    }
  };

  const handleExportCsv = () => {
    window.open('/api/v1/managers/export', '_blank');
  };

  const categoryChartData = Object.entries(dashboardData?.breakdown.by_category || {}).map(([key, val]) => ({
    name: key.replace('_', ' ').toLowerCase(),
    value: val,
  }));

  const priorityChartData = Object.entries(dashboardData?.breakdown.by_priority || {}).map(([key, val]) => ({
    name: key,
    count: val,
  }));

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-2 rounded-lg bg-emerald-500/10 text-emerald-600">
              <Building2 className="w-5 h-5" />
            </span>
            <h1 className="text-2xl font-extrabold text-navy-950">Department Operations Command Center</h1>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Real-time municipal SLA compliance, workload balancing, and ticket reassignment queue.
          </p>
        </div>

        <button
          onClick={handleExportCsv}
          className="inline-flex items-center gap-1.5 px-4 py-2 bg-navy-900 hover:bg-navy-800 text-white text-xs font-semibold rounded-xl shadow transition"
        >
          <FileSpreadsheet className="w-4 h-4 text-emerald-400" />
          Export CSV Report
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-6 gap-3 sm:gap-4">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">Total Filed</span>
          <div className="text-2xl font-extrabold text-navy-950 mt-1">
            {dashboardData?.metrics.total_complaints ?? 0}
          </div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <span className="text-[11px] font-semibold text-amber-600 uppercase tracking-wider block">In Progress</span>
          <div className="text-2xl font-extrabold text-amber-600 mt-1">
            {dashboardData?.metrics.in_progress ?? 0}
          </div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <span className="text-[11px] font-semibold text-emerald-600 uppercase tracking-wider block">Resolved</span>
          <div className="text-2xl font-extrabold text-emerald-600 mt-1">
            {dashboardData?.metrics.resolved ?? 0}
          </div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <span className="text-[11px] font-semibold text-rose-600 uppercase tracking-wider block">Overdue Tickets</span>
          <div className="text-2xl font-extrabold text-rose-600 mt-1">
            {dashboardData?.metrics.overdue ?? 0}
          </div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <span className="text-[11px] font-semibold text-civic-teal-700 uppercase tracking-wider block">SLA Compliance</span>
          <div className="text-2xl font-extrabold text-civic-teal-700 mt-1">
            {dashboardData?.metrics.sla_compliance_rate ?? 100}%
          </div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">Avg Resolution</span>
          <div className="text-2xl font-extrabold text-slate-800 mt-1">
            {dashboardData?.metrics.avg_resolution_hours ?? 0}h
          </div>
        </div>
      </div>

      {/* Analytics Charts & Officer Load Balancing */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Category Breakdown Chart */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-3">
          <h3 className="font-bold text-xs uppercase tracking-wider text-slate-700">Category Distribution</h3>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={categoryChartData}
                  cx="50%"
                  cy="50%"
                  innerRadius={45}
                  outerRadius={70}
                  paddingAngle={3}
                  dataKey="value"
                >
                  {categoryChartData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex flex-wrap gap-2 justify-center text-[10px] text-slate-500">
            {categoryChartData.map((c, i) => (
              <span key={c.name} className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full" style={{ backgroundColor: PIE_COLORS[i % PIE_COLORS.length] }}></span>
                {c.name}: {c.value}
              </span>
            ))}
          </div>
        </div>

        {/* Priority Breakdown Chart */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-3">
          <h3 className="font-bold text-xs uppercase tracking-wider text-slate-700">Priority Breakdown</h3>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={priorityChartData}>
                <XAxis dataKey="name" fontSize={10} />
                <YAxis fontSize={10} />
                <Tooltip />
                <Bar dataKey="count" fill="#204571" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Officer Workload Load Balancing */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-3">
          <h3 className="font-bold text-xs uppercase tracking-wider text-slate-700 flex items-center justify-between">
            <span>Officer Workload Distribution</span>
            <Users className="w-4 h-4 text-slate-400" />
          </h3>
          <p className="text-[11px] text-slate-500">Active assigned tickets per field officer for workload balancing:</p>
          <div className="space-y-2 max-h-48 overflow-y-auto divide-y divide-slate-100">
            {officers.length === 0 ? (
              <div className="text-xs text-slate-400 text-center py-4">No officers registered.</div>
            ) : (
              officers.map(off => (
                <div key={off.id} className="pt-2 flex items-center justify-between text-xs">
                  <div>
                    <span className="font-semibold text-slate-800 block">{off.full_name}</span>
                    <span className="text-[10px] text-slate-400">{off.email}</span>
                  </div>
                  <span
                    className={`font-mono font-bold px-2.5 py-0.5 rounded-full text-xs ${
                      off.active_ticket_count >= 5
                        ? 'bg-rose-50 text-rose-700 border border-rose-200'
                        : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                    }`}
                  >
                    {off.active_ticket_count} Active
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Complaints Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden space-y-4 p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h3 className="font-bold text-sm text-navy-950">Grievance Operations Queue</h3>

          {/* Search & Filter Form */}
          <form onSubmit={handleSearchSubmit} className="flex flex-wrap items-center gap-2">
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
              <input
                type="text"
                value={searchTerm}
                onChange={e => setSearchTerm(e.target.value)}
                placeholder="Search ref, title, street..."
                className="text-xs pl-8 pr-3 py-1.5 rounded-lg border border-slate-200 outline-none focus:ring-1 focus:ring-civic-teal-500"
              />
            </div>

            <select
              value={statusFilter}
              onChange={e => setStatusFilter(e.target.value)}
              className="text-xs border border-slate-200 rounded-lg p-1.5 bg-white text-slate-800"
            >
              <option value="">All Statuses</option>
              <option value="SUBMITTED">Submitted</option>
              <option value="ACKNOWLEDGED">Acknowledged</option>
              <option value="ASSIGNED">Assigned</option>
              <option value="IN_PROGRESS">In Progress</option>
              <option value="RESOLVED">Resolved</option>
              <option value="CLOSED">Closed</option>
              <option value="REOPENED">Reopened</option>
              <option value="REJECTED">Rejected</option>
            </select>

            <select
              value={priorityFilter}
              onChange={e => setPriorityFilter(e.target.value)}
              className="text-xs border border-slate-200 rounded-lg p-1.5 bg-white text-slate-800"
            >
              <option value="">All Priorities</option>
              <option value="CRITICAL">Critical</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
            </select>
          </form>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50 text-slate-600 font-semibold">
                <th className="py-2.5 px-3">Reference</th>
                <th className="py-2.5 px-3">Title & Category</th>
                <th className="py-2.5 px-3">Priority</th>
                <th className="py-2.5 px-3">Status</th>
                <th className="py-2.5 px-3">Assigned Officer</th>
                <th className="py-2.5 px-3">SLA Deadline</th>
                <th className="py-2.5 px-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {complaints.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-400 italic">
                    No department grievances matching current filter.
                  </td>
                </tr>
              ) : (
                complaints.map(c => (
                  <tr key={c.id} className="hover:bg-slate-50/80 transition">
                    <td className="py-3 px-3 font-mono font-bold text-navy-900">{c.reference_id}</td>
                    <td className="py-3 px-3">
                      <div className="font-semibold text-slate-900 line-clamp-1">{c.title}</div>
                      <div className="text-[11px] text-slate-400 capitalize">{c.category.replace('_', ' ').toLowerCase()}</div>
                    </td>
                    <td className="py-3 px-3">
                      <PriorityBadge priority={c.priority} showIcon={false} />
                    </td>
                    <td className="py-3 px-3">
                      <StatusBadge status={c.status} size="sm" />
                    </td>
                    <td className="py-3 px-3">
                      {c.assigned_officer_name ? (
                        <span className="font-medium text-slate-800">{c.assigned_officer_name}</span>
                      ) : (
                        <span className="text-amber-600 font-medium italic">Unassigned</span>
                      )}
                    </td>
                    <td className="py-3 px-3">
                      <span className={`font-mono ${c.is_overdue ? 'text-rose-600 font-bold' : 'text-slate-600'}`}>
                        {c.sla_deadline ? new Date(c.sla_deadline).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', month: 'short', day: 'numeric' }) : 'Standard'}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-right space-x-1">
                      {c.status !== 'CLOSED' && c.status !== 'REJECTED' && (
                        <button
                          onClick={() => {
                            setReassignTicket(c);
                            setSelectedOfficerId(c.assigned_officer_id || '');
                          }}
                          className="px-2.5 py-1 bg-navy-50 hover:bg-navy-100 text-navy-800 font-semibold rounded text-[11px] border border-navy-200 transition"
                        >
                          Assign
                        </button>
                      )}
                      {c.status !== 'REJECTED' && c.status !== 'CLOSED' && (
                        <button
                          onClick={() => setRejectTicket(c)}
                          className="px-2 py-1 text-slate-500 hover:text-rose-600 hover:bg-rose-50 rounded text-[11px] transition"
                          title="Reject Grievance"
                        >
                          <Ban className="w-3.5 h-3.5 inline" />
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Assign Modal */}
      {reassignTicket && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
          <form
            onSubmit={handleAssignSubmit}
            className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6 border border-slate-200 space-y-4 text-xs"
          >
            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
              <h3 className="font-bold text-sm text-slate-900">
                Assign Officer — Ticket #{reassignTicket.reference_id}
              </h3>
              <button type="button" onClick={() => setReassignTicket(null)} className="text-slate-400">
                <X className="w-4 h-4" />
              </button>
            </div>

            <div>
              <label className="block font-semibold text-slate-700 mb-1">Select Field Officer</label>
              <select
                required
                value={selectedOfficerId}
                onChange={e => setSelectedOfficerId(Number(e.target.value))}
                className="w-full border border-slate-200 rounded-lg p-2 bg-white"
              >
                <option value="">Choose an officer...</option>
                {officers.map(off => (
                  <option key={off.id} value={off.id}>
                    {off.full_name} ({off.active_ticket_count} active tickets)
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block font-semibold text-slate-700 mb-1">Supervisor Dispatch Notes (Optional)</label>
              <textarea
                rows={2}
                value={assignNotes}
                onChange={e => setAssignNotes(e.target.value)}
                placeholder="Specific instructions for on-site crew..."
                className="w-full border border-slate-200 rounded-lg p-2 outline-none"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setReassignTicket(null)}
                className="px-4 py-2 font-semibold text-slate-600 hover:bg-slate-100 rounded-lg"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 font-bold text-white bg-navy-900 hover:bg-navy-800 rounded-lg shadow"
              >
                Confirm Assignment
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Reject Modal */}
      {rejectTicket && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
          <form
            onSubmit={handleRejectSubmit}
            className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6 border border-slate-200 space-y-4 text-xs"
          >
            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
              <h3 className="font-bold text-sm text-slate-900">
                Reject Grievance #{rejectTicket.reference_id}
              </h3>
              <button type="button" onClick={() => setRejectTicket(null)} className="text-slate-400">
                <X className="w-4 h-4" />
              </button>
            </div>

            <p className="text-slate-500">
              A formal justification reason is legally required to reject a registered civic grievance.
            </p>

            <div>
              <label className="block font-semibold text-slate-700 mb-1">Formal Rejection Reason</label>
              <textarea
                required
                rows={3}
                value={rejectReason}
                onChange={e => setRejectReason(e.target.value)}
                placeholder="e.g. Private property boundary dispute; not under municipal jurisdiction..."
                className="w-full border border-slate-200 rounded-lg p-2 outline-none focus:ring-1 focus:ring-rose-500"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setRejectTicket(null)}
                className="px-4 py-2 font-semibold text-slate-600 hover:bg-slate-100 rounded-lg"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 font-bold text-white bg-rose-600 hover:bg-rose-700 rounded-lg shadow"
              >
                Confirm Rejection
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};
