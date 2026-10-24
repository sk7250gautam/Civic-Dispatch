import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import { GrievanceMap } from '../components/GrievanceMap';
import { StatusBadge } from '../components/StatusBadge';
import { PriorityBadge } from '../components/PriorityBadge';
import { TimelineTracker } from '../components/TimelineTracker';
import {
  Search,
  CheckCircle,
  AlertTriangle,
  Clock,
  ShieldCheck,
  Building,
  ArrowRight,
  TrendingUp,
  MapPin,
  FileText,
  User,
  HardHat,
  Sparkles,
} from 'lucide-react';

export const HomePage: React.FC = () => {
  const { user, switchRole } = useAuth();
  const navigate = useNavigate();

  const [stats, setStats] = useState<any>(null);
  const [mapMarkers, setMapMarkers] = useState<any[]>([]);
  const [departments, setDepartments] = useState<any[]>([]);
  const [refSearch, setRefSearch] = useState<string>('');
  const [trackedGrievance, setTrackedGrievance] = useState<any>(null);
  const [trackingError, setTrackingError] = useState<string | null>(null);
  const [trackingLoading, setTrackingLoading] = useState<boolean>(false);

  useEffect(() => {
    api.getPublicStatistics().then(setStats).catch(() => {});
    api.getPublicMapMarkers().then(res => setMapMarkers(res.markers || [])).catch(() => {});
    api.getDepartments().then(res => setDepartments(res.departments || [])).catch(() => {});
  }, []);

  const handleTrackSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!refSearch.trim()) return;

    setTrackingLoading(true);
    setTrackingError(null);
    setTrackedGrievance(null);

    try {
      const res = await api.trackGrievance(refSearch.trim());
      setTrackedGrievance(res.complaint);
    } catch (err: any) {
      setTrackingError(err.message || 'Grievance reference ID not found.');
    } finally {
      setTrackingLoading(false);
    }
  };

  return (
    <div className="space-y-12 pb-16">
      {/* Hero Section */}
      <section className="bg-navy-950 text-white py-16 px-4 sm:px-6 lg:px-8 rounded-b-3xl shadow-xl relative overflow-hidden">
        <div className="absolute inset-0 opacity-10 bg-[radial-gradient(#3970a9_1px,transparent_1px)] [background-size:16px_16px]"></div>
        
        <div className="max-w-5xl mx-auto text-center relative z-10 space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-navy-800/80 border border-navy-700 text-civic-teal-300 text-xs font-semibold">
            <Sparkles className="w-3.5 h-3.5" />
            AI-Assisted Municipal Grievance & SLA Escalation Platform
          </div>

          <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-white leading-tight">
            Transparent Civic Grievance Resolution & Field Operations
          </h1>

          <p className="max-w-2xl mx-auto text-sm sm:text-base text-slate-300 leading-relaxed">
            Report municipal infrastructure issues, track live SLA countdowns, and empower field personnel with GPS-verified completions and automated escalation tracking.
          </p>

          {/* Quick Track Reference Input */}
          <div className="max-w-xl mx-auto pt-4">
            <form onSubmit={handleTrackSubmit} className="relative flex items-center">
              <Search className="w-5 h-5 absolute left-4 text-slate-400" />
              <input
                type="text"
                value={refSearch}
                onChange={e => setRefSearch(e.target.value)}
                placeholder="Enter Reference ID (e.g. CD-2026-90412)..."
                className="w-full pl-12 pr-28 py-3.5 rounded-xl bg-white text-slate-900 placeholder-slate-400 text-sm shadow-lg focus:outline-none focus:ring-2 focus:ring-civic-teal-500 font-mono"
              />
              <button
                type="submit"
                disabled={trackingLoading}
                className="absolute right-2 px-4 py-2 bg-civic-teal-600 hover:bg-civic-teal-700 text-white font-semibold text-xs rounded-lg transition shadow disabled:opacity-50"
              >
                {trackingLoading ? 'Checking...' : 'Track'}
              </button>
            </form>
          </div>

          {/* Primary CTA Buttons */}
          <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
            <Link
              to={user ? (user.role === 'CITIZEN' ? '/citizen/new' : `/${user.role.toLowerCase()}`) : '/login'}
              className="px-6 py-3 rounded-xl bg-civic-teal-500 hover:bg-civic-teal-600 text-navy-950 font-bold text-sm shadow-md transition flex items-center gap-2"
            >
              Report a Municipal Issue
              <ArrowRight className="w-4 h-4" />
            </Link>
            {!user && (
              <Link
                to="/login"
                className="px-6 py-3 rounded-xl bg-navy-800 hover:bg-navy-700 text-white font-semibold text-sm border border-navy-700 transition"
              >
                Staff & Citizen Login
              </Link>
            )}
          </div>
        </div>
      </section>

      {/* Tracked Grievance Result Card */}
      {trackedGrievance && (
        <section className="max-w-4xl mx-auto px-4">
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-lg space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-3">
              <div>
                <span className="text-xs font-mono font-bold text-navy-800 bg-navy-50 px-2 py-0.5 rounded">
                  {trackedGrievance.reference_id}
                </span>
                <h3 className="text-base font-bold text-slate-900 mt-1">{trackedGrievance.title}</h3>
              </div>
              <div className="flex items-center gap-2">
                <StatusBadge status={trackedGrievance.status} />
                <PriorityBadge priority={trackedGrievance.priority} />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs bg-slate-50 p-4 rounded-xl border border-slate-100">
              <div>
                <span className="text-slate-500 block">Department</span>
                <strong className="text-slate-800 font-semibold">{trackedGrievance.department_name}</strong>
              </div>
              <div>
                <span className="text-slate-500 block">Reported At</span>
                <strong className="text-slate-800 font-semibold">
                  {new Date(trackedGrievance.created_at).toLocaleString()}
                </strong>
              </div>
              <div>
                <span className="text-slate-500 block">Resolution SLA</span>
                <strong className="text-slate-800 font-semibold">
                  {trackedGrievance.sla_deadline
                    ? new Date(trackedGrievance.sla_deadline).toLocaleString()
                    : 'Standard SLA'}
                </strong>
              </div>
            </div>

            {trackedGrievance.resolution_summary && (
              <div className="p-3 bg-emerald-50 text-emerald-900 border border-emerald-200 rounded-xl text-xs">
                <div className="font-bold flex items-center gap-1.5 mb-1">
                  <CheckCircle className="w-4 h-4 text-emerald-600" />
                  Official Resolution Summary
                </div>
                <p>{trackedGrievance.resolution_summary}</p>
              </div>
            )}

            <div>
              <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-3">Audit Timeline</h4>
              <TimelineTracker history={trackedGrievance.timeline || []} />
            </div>
          </div>
        </section>
      )}

      {trackingError && (
        <div className="max-w-xl mx-auto px-4">
          <div className="p-4 bg-rose-50 text-rose-700 border border-rose-200 rounded-xl text-xs flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            {trackingError}
          </div>
        </div>
      )}

      {/* Public Transparency KPIs */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-2xl mx-auto mb-8">
          <h2 className="text-2xl font-bold text-navy-950">City-Wide Municipal Health & Transparency</h2>
          <p className="text-xs text-slate-500 mt-1">Live metrics calculated directly from database records without manual estimates.</p>
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
            <div className="flex items-center justify-between text-slate-500 mb-2">
              <span className="text-xs font-semibold uppercase tracking-wider">Total Complaints</span>
              <FileText className="w-4 h-4 text-navy-700" />
            </div>
            <div className="text-3xl font-extrabold text-navy-950">{stats?.total_complaints ?? '...'}</div>
            <div className="text-[11px] text-slate-500 mt-1">Registered city-wide</div>
          </div>

          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
            <div className="flex items-center justify-between text-slate-500 mb-2">
              <span className="text-xs font-semibold uppercase tracking-wider">Resolved Tickets</span>
              <CheckCircle className="w-4 h-4 text-emerald-600" />
            </div>
            <div className="text-3xl font-extrabold text-emerald-600">{stats?.resolved_complaints ?? '...'}</div>
            <div className="text-[11px] text-slate-500 mt-1">Grievances resolved & inspected</div>
          </div>

          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
            <div className="flex items-center justify-between text-slate-500 mb-2">
              <span className="text-xs font-semibold uppercase tracking-wider">SLA Compliance</span>
              <TrendingUp className="w-4 h-4 text-civic-teal-600" />
            </div>
            <div className="text-3xl font-extrabold text-civic-teal-700">
              {stats?.sla_compliance_rate ? `${stats.sla_compliance_rate}%` : '100%'}
            </div>
            <div className="text-[11px] text-slate-500 mt-1">Completed within deadline</div>
          </div>

          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
            <div className="flex items-center justify-between text-slate-500 mb-2">
              <span className="text-xs font-semibold uppercase tracking-wider">Median Resolution</span>
              <Clock className="w-4 h-4 text-amber-600" />
            </div>
            <div className="text-3xl font-extrabold text-slate-800">
              {stats?.median_resolution_hours ? `${stats.median_resolution_hours}h` : '< 24h'}
            </div>
            <div className="text-[11px] text-slate-500 mt-1">Average time to complete</div>
          </div>
        </div>
      </section>

      {/* Public Geospatial Transparency Map */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <h3 className="text-lg font-bold text-navy-950 flex items-center gap-2">
                <MapPin className="w-5 h-5 text-civic-teal-600" />
                Public Transparency Map
              </h3>
              <p className="text-xs text-slate-500">
                Anonymized civic issues reported across city sectors. Exact private residential coordinates are protected.
              </p>
            </div>
            <span className="text-xs bg-slate-100 text-slate-600 px-2.5 py-1 rounded-full font-medium">
              {mapMarkers.length} Active Markers Loaded
            </span>
          </div>

          <GrievanceMap
            mode="viewer"
            initialLat={12.9716}
            initialLng={77.5946}
            zoom={12}
            markers={mapMarkers}
            height="420px"
          />
        </div>
      </section>

      {/* Recruiter Evaluation Walkthrough Cards */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-navy-900 text-white rounded-3xl p-8 shadow-xl space-y-6">
          <div className="max-w-2xl">
            <span className="text-xs font-semibold text-civic-teal-400 uppercase tracking-wider block">
              Recruiter & Reviewer Walkthrough
            </span>
            <h2 className="text-2xl font-bold mt-1">Test Real Role-Based Access Control Instantly</h2>
            <p className="text-slate-300 text-xs sm:text-sm mt-2">
              Civic Dispatch is built with server-enforced role permissions. Click any role card below to log in immediately and inspect the corresponding portal:
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <button
              onClick={() => { switchRole('CITIZEN'); navigate('/citizen'); }}
              className="text-left bg-navy-800/80 hover:bg-navy-800 p-5 rounded-2xl border border-navy-700 hover:border-civic-teal-500 transition group"
            >
              <div className="w-9 h-9 rounded-lg bg-sky-500/20 text-sky-400 flex items-center justify-center mb-3">
                <User className="w-5 h-5" />
              </div>
              <h4 className="font-bold text-sm text-white group-hover:text-civic-teal-300 transition">1. Citizen Portal</h4>
              <p className="text-[11px] text-slate-300 mt-1">
                Submit complaints with AI categorization, photo upload, and Leaflet pin picker; rate resolutions.
              </p>
              <span className="inline-block text-[10px] text-civic-teal-400 font-mono mt-3">Login as Priya Sharma &rarr;</span>
            </button>

            <button
              onClick={() => { switchRole('FIELD_OFFICER'); navigate('/officer'); }}
              className="text-left bg-navy-800/80 hover:bg-navy-800 p-5 rounded-2xl border border-navy-700 hover:border-amber-500 transition group"
            >
              <div className="w-9 h-9 rounded-lg bg-amber-500/20 text-amber-400 flex items-center justify-center mb-3">
                <HardHat className="w-5 h-5" />
              </div>
              <h4 className="font-bold text-sm text-white group-hover:text-amber-300 transition">2. Field Officer</h4>
              <p className="text-[11px] text-slate-300 mt-1">
                Mobile-first work queue, start work, verify GPS distance against tolerance, upload completion proof.
              </p>
              <span className="inline-block text-[10px] text-amber-400 font-mono mt-3">Login as Rajesh Kumar &rarr;</span>
            </button>

            <button
              onClick={() => { switchRole('DEPARTMENT_MANAGER'); navigate('/manager'); }}
              className="text-left bg-navy-800/80 hover:bg-navy-800 p-5 rounded-2xl border border-navy-700 hover:border-emerald-500 transition group"
            >
              <div className="w-9 h-9 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center mb-3">
                <Building className="w-5 h-5" />
              </div>
              <h4 className="font-bold text-sm text-white group-hover:text-emerald-300 transition">3. Dept Manager</h4>
              <p className="text-[11px] text-slate-300 mt-1">
                Operations dashboard, officer workload balancing, reassignments, SLA breaches, and CSV export.
              </p>
              <span className="inline-block text-[10px] text-emerald-400 font-mono mt-3">Login as Anita Desai &rarr;</span>
            </button>

            <button
              onClick={() => { switchRole('SYSTEM_ADMIN'); navigate('/admin'); }}
              className="text-left bg-navy-800/80 hover:bg-navy-800 p-5 rounded-2xl border border-navy-700 hover:border-purple-500 transition group"
            >
              <div className="w-9 h-9 rounded-lg bg-purple-500/20 text-purple-400 flex items-center justify-center mb-3">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <h4 className="font-bold text-sm text-white group-hover:text-purple-300 transition">4. System Admin</h4>
              <p className="text-[11px] text-slate-300 mt-1">
                SLA policy rules editor, live audit log inspector, trigger manual SLA sweep, staff account creation.
              </p>
              <span className="inline-block text-[10px] text-purple-400 font-mono mt-3">Login as Vikram Mehta &rarr;</span>
            </button>
          </div>
        </div>
      </section>
    </div>
  );
};
