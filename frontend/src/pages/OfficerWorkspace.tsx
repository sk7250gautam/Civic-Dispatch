import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { Complaint } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { PriorityBadge } from '../components/PriorityBadge';
import {
  HardHat,
  MapPin,
  Clock,
  CheckCircle2,
  Play,
  Check,
  FileEdit,
  Navigation,
  Upload,
  AlertTriangle,
  X,
  MessageSquare,
  Sparkles,
} from 'lucide-react';

export const OfficerWorkspace: React.FC = () => {
  const [queue, setQueue] = useState<Complaint[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');

  // Resolution Modal State
  const [resolvingComplaint, setResolvingComplaint] = useState<Complaint | null>(null);
  const [resolutionSummary, setResolutionSummary] = useState('');
  const [officerLat, setOfficerLat] = useState<number | null>(null);
  const [officerLng, setOfficerLng] = useState<number | null>(null);
  const [exceptionReason, setExceptionReason] = useState('');
  const [afterPhoto, setAfterPhoto] = useState<File | null>(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  // Note Modal State
  const [noteComplaint, setNoteComplaint] = useState<Complaint | null>(null);
  const [noteText, setNoteText] = useState('');

  const fetchQueue = async () => {
    setLoading(true);
    try {
      const res = await api.getOfficerQueue(statusFilter || undefined);
      setQueue(res.queue || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQueue();
  }, [statusFilter]);

  const handleAcknowledge = async (id: number) => {
    try {
      await api.acknowledgeComplaint(id);
      fetchQueue();
    } catch (err: any) {
      alert(err.message || 'Could not acknowledge ticket.');
    }
  };

  const handleStartWork = async (id: number) => {
    try {
      await api.startWork(id);
      fetchQueue();
    } catch (err: any) {
      alert(err.message || 'Could not start work.');
    }
  };

  const handleCaptureGps = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        pos => {
          setOfficerLat(parseFloat(pos.coords.latitude.toFixed(6)));
          setOfficerLng(parseFloat(pos.coords.longitude.toFixed(6)));
        },
        () => {
          alert('Could not access mobile GPS. If working remotely, provide an exception reason.');
        }
      );
    }
  };

  const handleResolveSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!resolvingComplaint || !resolutionSummary.trim()) {
      setActionError('Resolution description is required.');
      return;
    }

    setActionLoading(true);
    setActionError(null);

    try {
      const formData = new FormData();
      formData.append('resolution_summary', resolutionSummary.trim());
      if (officerLat !== null && officerLng !== null) {
        formData.append('latitude', officerLat.toString());
        formData.append('longitude', officerLng.toString());
      }
      if (exceptionReason) {
        formData.append('location_exception_reason', exceptionReason.trim());
      }
      if (afterPhoto) {
        formData.append('photo', afterPhoto);
      }

      await api.resolveComplaint(resolvingComplaint.id, formData);
      setResolvingComplaint(null);
      setResolutionSummary('');
      setOfficerLat(null);
      setOfficerLng(null);
      setExceptionReason('');
      setAfterPhoto(null);
      fetchQueue();
    } catch (err: any) {
      setActionError(err.message || 'Resolution failed.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleAddNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!noteComplaint || !noteText.trim()) return;

    try {
      await api.addInternalNote(noteComplaint.id, noteText.trim());
      setNoteComplaint(null);
      setNoteText('');
      fetchQueue();
    } catch (err: any) {
      alert(err.message || 'Could not add note.');
    }
  };

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-2 rounded-lg bg-amber-500/10 text-amber-600">
              <HardHat className="w-5 h-5" />
            </span>
            <h1 className="text-2xl font-extrabold text-navy-950">Field Operations Workspace</h1>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Mobile-optimized work queue. Inspect tickets, record GPS verifications, and submit resolution evidence.
          </p>
        </div>

        {/* Filter */}
        <select
          value={statusFilter}
          onChange={e => setStatusFilter(e.target.value)}
          className="text-xs border border-slate-200 rounded-lg p-2 bg-white text-slate-800 font-semibold shadow-sm"
        >
          <option value="">Active Assigned ({queue.length})</option>
          <option value="ASSIGNED">Assigned Only</option>
          <option value="IN_PROGRESS">In Progress</option>
          <option value="ACKNOWLEDGED">Acknowledged</option>
          <option value="RESOLVED">Resolved Archive</option>
        </select>
      </div>

      {/* Queue Cards */}
      {loading ? (
        <div className="p-12 text-center text-xs text-slate-500 bg-white rounded-2xl border border-slate-200">
          Loading assigned queue...
        </div>
      ) : queue.length === 0 ? (
        <div className="p-12 text-center bg-white rounded-2xl border border-slate-200 shadow-sm space-y-3">
          <CheckCircle2 className="w-10 h-10 text-emerald-500 mx-auto" />
          <h3 className="text-sm font-bold text-slate-800">Field Queue Clear!</h3>
          <p className="text-xs text-slate-500">You currently have no pending assigned tickets requiring field work.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {queue.map(item => (
            <div
              key={item.id}
              className={`bg-white rounded-2xl border p-5 shadow-sm transition space-y-4 ${
                item.priority === 'CRITICAL'
                  ? 'border-rose-300 ring-1 ring-rose-100'
                  : item.is_overdue
                  ? 'border-amber-300'
                  : 'border-slate-200'
              }`}
            >
              {/* Top row */}
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className="font-mono font-bold text-xs bg-navy-900 text-white px-2 py-0.5 rounded">
                    {item.reference_id}
                  </span>
                  <StatusBadge status={item.status} size="sm" />
                  <PriorityBadge priority={item.priority} />
                </div>

                <div className="text-xs flex items-center gap-2">
                  <span className={`flex items-center gap-1 font-semibold ${item.is_overdue ? 'text-rose-600' : 'text-slate-500'}`}>
                    <Clock className="w-3.5 h-3.5" />
                    SLA Deadline: {item.sla_deadline ? new Date(item.sla_deadline).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', month: 'short', day: 'numeric' }) : 'Standard'}
                  </span>
                </div>
              </div>

              {/* Title & Desc */}
              <div>
                <h3 className="font-bold text-sm text-slate-900">{item.title}</h3>
                <p className="text-xs text-slate-600 mt-1 leading-relaxed">{item.description}</p>
              </div>

              {/* Geo & Address info */}
              <div className="flex flex-wrap items-center gap-4 text-xs bg-slate-50 p-3 rounded-xl border border-slate-100">
                <div className="flex items-center gap-1.5 text-slate-700">
                  <MapPin className="w-3.5 h-3.5 text-civic-teal-600" />
                  <span>{item.address || 'Reported Location'}</span>
                </div>
                <div className="text-[11px] text-slate-400 font-mono">
                  Coordinates: {item.latitude}, {item.longitude}
                </div>
                {item.verified_location && (
                  <span className="ml-auto inline-flex items-center gap-1 text-[11px] text-emerald-700 font-semibold bg-emerald-50 px-2 py-0.5 rounded">
                    <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                    GPS Verified
                  </span>
                )}
              </div>

              {/* Internal Notes Preview */}
              {item.internal_notes && (
                <div className="p-3 bg-amber-50/60 text-amber-900 border border-amber-200/60 rounded-xl text-xs space-y-1">
                  <span className="font-semibold block text-[11px] uppercase tracking-wider text-amber-800">
                    Internal Staff Notes:
                  </span>
                  <pre className="font-sans whitespace-pre-wrap text-[11px] text-amber-900">{item.internal_notes}</pre>
                </div>
              )}

              {/* Actions Bar */}
              <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-100">
                {item.status === 'SUBMITTED' && (
                  <button
                    onClick={() => handleAcknowledge(item.id)}
                    className="px-3.5 py-1.5 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-xs font-semibold shadow-sm transition"
                  >
                    Acknowledge Ticket
                  </button>
                )}

                {(item.status === 'ACKNOWLEDGED' || item.status === 'ASSIGNED') && (
                  <button
                    onClick={() => handleStartWork(item.id)}
                    className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-amber-600 hover:bg-amber-700 text-white rounded-lg text-xs font-semibold shadow-sm transition"
                  >
                    <Play className="w-3.5 h-3.5" />
                    Start On-Site Work
                  </button>
                )}

                {item.status === 'IN_PROGRESS' && (
                  <button
                    onClick={() => setResolvingComplaint(item)}
                    className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-bold shadow-sm transition"
                  >
                    <Check className="w-3.5 h-3.5" />
                    Mark Resolved with Evidence
                  </button>
                )}

                <button
                  onClick={() => setNoteComplaint(item)}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-medium transition ml-auto"
                >
                  <MessageSquare className="w-3.5 h-3.5" />
                  Add Internal Note
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Resolution Modal */}
      {resolvingComplaint && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-lg w-full p-6 border border-slate-200 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <span className="text-xs font-mono font-bold text-navy-900 bg-navy-50 px-2 py-0.5 rounded">
                  {resolvingComplaint.reference_id}
                </span>
                <h3 className="font-bold text-slate-900 text-sm mt-1">Submit Field Resolution</h3>
              </div>
              <button onClick={() => setResolvingComplaint(null)} className="text-slate-400">
                <X className="w-5 h-5" />
              </button>
            </div>

            {actionError && (
              <div className="p-3 bg-rose-50 text-rose-700 border border-rose-200 rounded-lg text-xs flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 shrink-0" />
                {actionError}
              </div>
            )}

            <form onSubmit={handleResolveSubmit} className="space-y-4 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Work Description & Technical Remedy</label>
                <textarea
                  required
                  rows={3}
                  value={resolutionSummary}
                  onChange={e => setResolutionSummary(e.target.value)}
                  placeholder="Describe repair actions taken, materials used, and final site state..."
                  className="w-full text-xs p-2.5 rounded-lg border border-slate-200 focus:ring-2 focus:ring-emerald-500 outline-none"
                />
              </div>

              {/* GPS Verification Section */}
              <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-800 flex items-center gap-1.5">
                    <Navigation className="w-3.5 h-3.5 text-civic-teal-600" />
                    GPS Location Verification (250m Tolerance)
                  </span>
                  <button
                    type="button"
                    onClick={handleCaptureGps}
                    className="px-2.5 py-1 bg-white hover:bg-slate-100 text-slate-700 border border-slate-300 rounded font-semibold text-[11px] shadow-sm"
                  >
                    Capture GPS Now
                  </button>
                </div>

                {officerLat !== null ? (
                  <div className="text-[11px] text-emerald-700 font-mono bg-emerald-50 p-2 rounded border border-emerald-200">
                    Captured: {officerLat}, {officerLng}
                  </div>
                ) : (
                  <p className="text-[11px] text-slate-500">
                    Click "Capture GPS Now" while on site to verify physical presence against tolerance.
                  </p>
                )}

                <div>
                  <label className="block text-[11px] font-medium text-slate-600 mt-2 mb-1">
                    Location Exception Reason (Required if GPS verification fails or off-site resolution)
                  </label>
                  <input
                    type="text"
                    value={exceptionReason}
                    onChange={e => setExceptionReason(e.target.value)}
                    placeholder="e.g. Remote substation fix, GPS unavailable under tunnel..."
                    className="w-full text-xs p-2 rounded-lg border border-slate-200 bg-white outline-none"
                  />
                </div>
              </div>

              {/* After Photo Upload */}
              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  Upload Completion Evidence Photo (Optional)
                </label>
                <input
                  type="file"
                  accept="image/*"
                  onChange={e => setAfterPhoto(e.target.files?.[0] || null)}
                  className="w-full text-xs file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:bg-slate-100 file:text-slate-700 file:font-semibold"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setResolvingComplaint(null)}
                  className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="px-5 py-2 text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-700 rounded-lg shadow disabled:opacity-50"
                >
                  {actionLoading ? 'Verifying & Saving...' : 'Confirm Resolved'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Internal Note Modal */}
      {noteComplaint && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
          <form
            onSubmit={handleAddNote}
            className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6 border border-slate-200 space-y-4"
          >
            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
              <h3 className="font-bold text-sm text-slate-900">Add Staff Operational Note</h3>
              <button type="button" onClick={() => setNoteComplaint(null)} className="text-slate-400">
                <X className="w-4 h-4" />
              </button>
            </div>
            <p className="text-xs text-slate-500">
              Internal notes are only visible to authorized field officers and department managers.
            </p>
            <textarea
              required
              rows={3}
              value={noteText}
              onChange={e => setNoteText(e.target.value)}
              placeholder="e.g. Visited site at 14:00; contacted water board engineer for joint trench opening..."
              className="w-full text-xs p-2.5 rounded-lg border border-slate-200 focus:ring-2 focus:ring-amber-500 outline-none"
            />
            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setNoteComplaint(null)}
                className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-lg"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 text-xs font-bold text-white bg-navy-900 hover:bg-navy-800 rounded-lg shadow"
              >
                Save Note
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};
