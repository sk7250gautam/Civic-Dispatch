import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { api } from '../services/api';
import { Complaint } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { PriorityBadge } from '../components/PriorityBadge';
import { TimelineTracker } from '../components/TimelineTracker';
import { FeedbackModal } from '../components/FeedbackModal';
import {
  PlusCircle,
  Clock,
  CheckCircle2,
  AlertCircle,
  FileText,
  RotateCcw,
  Star,
  ExternalLink,
  X,
  Search,
} from 'lucide-react';

export const CitizenPortal: React.FC = () => {
  const location = useLocation();
  const [complaints, setComplaints] = useState<Complaint[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [selectedComplaint, setSelectedComplaint] = useState<Complaint | null>(null);
  const [feedbackComplaint, setFeedbackComplaint] = useState<Complaint | null>(null);
  
  // Reopen prompt state
  const [reopenPromptId, setReopenPromptId] = useState<number | null>(null);
  const [reopenReason, setReopenReason] = useState<string>('');
  const [reopenLoading, setReopenLoading] = useState<boolean>(false);

  const newRefId = location.state?.newReferenceId;

  const fetchComplaints = async () => {
    setLoading(true);
    try {
      const res = await api.getCitizenComplaints({ status: statusFilter || undefined });
      setComplaints(res.complaints || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchComplaints();
  }, [statusFilter]);

  const handleOpenDetails = async (id: number) => {
    try {
      const res = await api.getComplaintDetails(id);
      setSelectedComplaint(res.complaint);
    } catch (err) {
      console.error(err);
    }
  };

  const handleReopenSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reopenPromptId || !reopenReason.trim()) return;

    setReopenLoading(true);
    try {
      await api.reopenComplaint(reopenPromptId, reopenReason.trim());
      setReopenPromptId(null);
      setReopenReason('');
      fetchComplaints();
      if (selectedComplaint?.id === reopenPromptId) {
        handleOpenDetails(reopenPromptId);
      }
    } catch (err: any) {
      alert(err.message || 'Could not reopen grievance.');
    } finally {
      setReopenLoading(false);
    }
  };

  const handleFeedbackSubmit = async (fbData: any) => {
    if (!feedbackComplaint) return;
    await api.submitFeedback(feedbackComplaint.id, fbData);
    fetchComplaints();
    if (selectedComplaint?.id === feedbackComplaint.id) {
      handleOpenDetails(feedbackComplaint.id);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-navy-950">Citizen Grievance Workspace</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Track status updates, SLA countdowns, and rate resolutions of your reported civic issues.
          </p>
        </div>

        <Link
          to="/citizen/new"
          className="inline-flex items-center gap-2 px-4 py-2 bg-civic-teal-600 hover:bg-civic-teal-700 text-white text-xs font-bold rounded-xl shadow transition"
        >
          <PlusCircle className="w-4 h-4" />
          Lodge New Grievance
        </Link>
      </div>

      {newRefId && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-xs flex items-center justify-between shadow-sm">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
            <span>
              Your grievance has been submitted successfully! Reference ID:{' '}
              <strong className="font-mono">{newRefId}</strong>
            </span>
          </div>
        </div>
      )}

      {/* Filter and stats row */}
      <div className="flex items-center justify-between gap-3 bg-white p-4 rounded-xl border border-slate-200 shadow-sm text-xs">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-slate-700">Filter by Status:</span>
          <select
            value={statusFilter}
            onChange={e => setStatusFilter(e.target.value)}
            className="border border-slate-200 rounded-lg p-1.5 bg-white text-slate-800 font-medium"
          >
            <option value="">All Statuses ({complaints.length})</option>
            <option value="SUBMITTED">Submitted</option>
            <option value="ACKNOWLEDGED">Acknowledged</option>
            <option value="ASSIGNED">Assigned</option>
            <option value="IN_PROGRESS">In Progress</option>
            <option value="RESOLVED">Resolved</option>
            <option value="CLOSED">Closed</option>
            <option value="REOPENED">Reopened</option>
            <option value="REJECTED">Rejected</option>
          </select>
        </div>

        <div className="text-slate-500 text-xs">
          Total Filed: <strong className="text-slate-800">{complaints.length}</strong>
        </div>
      </div>

      {/* Complaints List */}
      {loading ? (
        <div className="p-12 text-center text-xs text-slate-500 bg-white rounded-xl border border-slate-200">
          Loading your grievances...
        </div>
      ) : complaints.length === 0 ? (
        <div className="p-12 text-center bg-white rounded-2xl border border-slate-200 shadow-sm space-y-3">
          <div className="w-12 h-12 bg-slate-100 rounded-full flex items-center justify-center mx-auto text-slate-400">
            <FileText className="w-6 h-6" />
          </div>
          <h3 className="text-sm font-bold text-slate-800">No grievances found</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            You haven't reported any municipal grievances matching this criteria yet.
          </p>
          <Link
            to="/citizen/new"
            className="inline-flex items-center gap-1.5 px-4 py-2 bg-navy-900 text-white rounded-lg text-xs font-semibold shadow hover:bg-navy-800 transition"
          >
            Report Your First Issue
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {complaints.map(c => (
            <div
              key={c.id}
              className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm hover:shadow-md transition space-y-3 flex flex-col justify-between"
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-mono font-bold text-navy-900 bg-navy-50 px-2 py-0.5 rounded">
                    {c.reference_id}
                  </span>
                  <StatusBadge status={c.status} size="sm" />
                </div>

                <h3 className="font-bold text-slate-900 text-sm line-clamp-1">{c.title}</h3>
                <p className="text-xs text-slate-600 line-clamp-2 leading-relaxed">{c.description}</p>
              </div>

              <div className="pt-3 border-t border-slate-100 space-y-2 text-xs">
                <div className="flex items-center justify-between text-slate-500 text-[11px]">
                  <span>Priority:</span>
                  <PriorityBadge priority={c.priority} showIcon={false} />
                </div>

                <div className="flex items-center justify-between text-slate-500 text-[11px]">
                  <span className="flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5 text-slate-400" />
                    SLA Deadline:
                  </span>
                  <span className={`font-medium ${c.is_overdue ? 'text-rose-600 font-bold' : 'text-slate-700'}`}>
                    {c.sla_deadline ? new Date(c.sla_deadline).toLocaleDateString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : 'Standard'}
                  </span>
                </div>

                <div className="flex items-center gap-2 pt-2">
                  <button
                    onClick={() => handleOpenDetails(c.id)}
                    className="flex-1 py-1.5 text-center text-xs font-semibold text-navy-900 bg-slate-100 hover:bg-slate-200 rounded-lg transition"
                  >
                    View Details
                  </button>

                  {(c.status === 'RESOLVED' || c.status === 'CLOSED') && (
                    <>
                      <button
                        onClick={() => setFeedbackComplaint(c)}
                        className="p-1.5 text-amber-600 hover:bg-amber-50 rounded-lg transition"
                        title="Rate Resolution"
                      >
                        <Star className="w-4 h-4 fill-amber-400" />
                      </button>
                      <button
                        onClick={() => setReopenPromptId(c.id)}
                        className="p-1.5 text-rose-600 hover:bg-rose-50 rounded-lg transition"
                        title="Reopen Grievance"
                      >
                        <RotateCcw className="w-4 h-4" />
                      </button>
                    </>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Details Modal */}
      {selectedComplaint && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto border border-slate-200">
            <div className="flex items-center justify-between p-6 border-b border-slate-100 bg-slate-50 sticky top-0 z-10">
              <div>
                <span className="text-xs font-mono font-bold text-navy-900 bg-navy-100 px-2 py-0.5 rounded">
                  {selectedComplaint.reference_id}
                </span>
                <h2 className="text-base font-bold text-slate-900 mt-1">{selectedComplaint.title}</h2>
              </div>
              <button
                onClick={() => setSelectedComplaint(null)}
                className="text-slate-400 hover:text-slate-600 p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 space-y-6 text-xs">
              <div className="flex flex-wrap gap-2 items-center">
                <StatusBadge status={selectedComplaint.status} />
                <PriorityBadge priority={selectedComplaint.priority} />
                <span className="text-slate-500 font-mono text-[11px] ml-auto">
                  Reported on {new Date(selectedComplaint.created_at).toLocaleString()}
                </span>
              </div>

              <div>
                <h4 className="font-bold text-slate-700 uppercase tracking-wider mb-1">Description</h4>
                <p className="text-slate-700 leading-relaxed bg-slate-50 p-3 rounded-xl border border-slate-100">
                  {selectedComplaint.description}
                </p>
              </div>

              <div className="grid grid-cols-2 gap-4 bg-slate-50 p-3 rounded-xl border border-slate-100">
                <div>
                  <span className="text-slate-400 block text-[10px]">Department</span>
                  <strong className="text-slate-800">{selectedComplaint.department_name || 'Municipal Works'}</strong>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px]">Location</span>
                  <strong className="text-slate-800">{selectedComplaint.address || 'Reported Geo Location'}</strong>
                </div>
              </div>

              {selectedComplaint.resolution_summary && (
                <div className="p-4 bg-emerald-50 text-emerald-900 border border-emerald-200 rounded-xl space-y-1">
                  <div className="font-bold flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                    Official Resolution Summary
                  </div>
                  <p>{selectedComplaint.resolution_summary}</p>
                  {selectedComplaint.resolved_at && (
                    <span className="text-[10px] text-emerald-700 block mt-1">
                      Completed at: {new Date(selectedComplaint.resolved_at).toLocaleString()}
                    </span>
                  )}
                </div>
              )}

              {/* Attachments */}
              {selectedComplaint.attachments && selectedComplaint.attachments.length > 0 && (
                <div>
                  <h4 className="font-bold text-slate-700 uppercase tracking-wider mb-2">Attachments</h4>
                  <div className="flex gap-2">
                    {selectedComplaint.attachments.map(att => (
                      <a
                        key={att.id}
                        href={att.url}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-800 rounded-lg text-xs font-semibold"
                      >
                        <ExternalLink className="w-3.5 h-3.5" />
                        {att.filename}
                      </a>
                    ))}
                  </div>
                </div>
              )}

              {/* Status History */}
              <div>
                <h4 className="font-bold text-slate-700 uppercase tracking-wider mb-3">Status Timeline</h4>
                <TimelineTracker history={selectedComplaint.status_history || []} />
              </div>
            </div>

            <div className="p-4 bg-slate-50 border-t border-slate-100 flex justify-end gap-2">
              {(selectedComplaint.status === 'RESOLVED' || selectedComplaint.status === 'CLOSED') && (
                <>
                  <button
                    onClick={() => {
                      setFeedbackComplaint(selectedComplaint);
                      setSelectedComplaint(null);
                    }}
                    className="px-4 py-2 bg-amber-500 hover:bg-amber-600 text-white rounded-lg text-xs font-bold"
                  >
                    Rate Resolution
                  </button>
                  <button
                    onClick={() => {
                      setReopenPromptId(selectedComplaint.id);
                      setSelectedComplaint(null);
                    }}
                    className="px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-xs font-bold"
                  >
                    Reopen Grievance
                  </button>
                </>
              )}
              <button
                onClick={() => setSelectedComplaint(null)}
                className="px-4 py-2 bg-slate-200 hover:bg-slate-300 text-slate-800 rounded-lg text-xs font-semibold"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Reopen Prompt Modal */}
      {reopenPromptId && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
          <form
            onSubmit={handleReopenSubmit}
            className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6 border border-slate-200 space-y-4"
          >
            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
              <h3 className="font-bold text-sm text-slate-900">Reopen Grievance</h3>
              <button type="button" onClick={() => setReopenPromptId(null)} className="text-slate-400">
                <X className="w-4 h-4" />
              </button>
            </div>

            <p className="text-xs text-slate-500">
              Please specify why this issue remains unresolved or has reoccurred. A formal explanation is required.
            </p>

            <textarea
              required
              rows={3}
              value={reopenReason}
              onChange={e => setReopenReason(e.target.value)}
              placeholder="e.g. The pothole was only filled with loose gravel and washed away in the rain..."
              className="w-full text-xs p-2.5 rounded-lg border border-slate-200 focus:ring-2 focus:ring-rose-500 outline-none"
            />

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setReopenPromptId(null)}
                className="px-4 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100 rounded-lg"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={reopenLoading}
                className="px-4 py-2 text-xs font-bold text-white bg-rose-600 hover:bg-rose-700 rounded-lg shadow disabled:opacity-50"
              >
                {reopenLoading ? 'Reopening...' : 'Confirm Reopen'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Feedback Modal */}
      {feedbackComplaint && (
        <FeedbackModal
          complaintId={feedbackComplaint.id}
          referenceId={feedbackComplaint.reference_id}
          isOpen={true}
          onClose={() => setFeedbackComplaint(null)}
          onSubmit={handleFeedbackSubmit}
        />
      )}
    </div>
  );
};
