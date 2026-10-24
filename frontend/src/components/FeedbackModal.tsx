import React, { useState } from 'react';
import { Star, X } from 'lucide-react';

interface FeedbackModalProps {
  complaintId: number;
  referenceId: string;
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (feedback: { rating: number; comments: string; speed_rating?: number; officer_rating?: number }) => Promise<void>;
}

export const FeedbackModal: React.FC<FeedbackModalProps> = ({
  complaintId,
  referenceId,
  isOpen,
  onClose,
  onSubmit,
}) => {
  const [rating, setRating] = useState<number>(5);
  const [comments, setComments] = useState<string>('');
  const [speedRating, setSpeedRating] = useState<number>(5);
  const [officerRating, setOfficerRating] = useState<number>(5);
  const [loading, setLoading] = useState<boolean>(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await onSubmit({
        rating,
        comments,
        speed_rating: speedRating,
        officer_rating: officerRating,
      });
      onClose();
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-md w-full overflow-hidden border border-slate-200">
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-slate-50">
          <div>
            <h3 className="font-bold text-slate-900 text-sm">Rate Municipal Resolution</h3>
            <span className="text-xs text-slate-500 font-mono">Ticket #{referenceId}</span>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-2">Overall Satisfaction</label>
            <div className="flex items-center gap-1.5 justify-center py-2 bg-slate-50 rounded-lg border border-slate-200">
              {[1, 2, 3, 4, 5].map(star => (
                <button
                  type="button"
                  key={star}
                  onClick={() => setRating(star)}
                  className="p-1 hover:scale-110 transition"
                >
                  <Star
                    className={`w-7 h-7 ${
                      star <= rating ? 'fill-amber-400 text-amber-500' : 'text-slate-300'
                    }`}
                  />
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs">
            <div>
              <label className="block font-medium text-slate-700 mb-1">Resolution Speed</label>
              <select
                value={speedRating}
                onChange={e => setSpeedRating(Number(e.target.value))}
                className="w-full border border-slate-200 rounded-md p-1.5 bg-white text-slate-800"
              >
                <option value={5}>5 - Very Fast</option>
                <option value={4}>4 - Fast</option>
                <option value={3}>3 - Acceptable</option>
                <option value={2}>2 - Delayed</option>
                <option value={1}>1 - Unacceptable</option>
              </select>
            </div>
            <div>
              <label className="block font-medium text-slate-700 mb-1">Field Staff Quality</label>
              <select
                value={officerRating}
                onChange={e => setOfficerRating(Number(e.target.value))}
                className="w-full border border-slate-200 rounded-md p-1.5 bg-white text-slate-800"
              >
                <option value={5}>5 - Excellent</option>
                <option value={4}>4 - Professional</option>
                <option value={3}>3 - Satisfactory</option>
                <option value={2}>2 - Subpar</option>
                <option value={1}>1 - Poor</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Feedback Comments (Optional)</label>
            <textarea
              rows={3}
              value={comments}
              onChange={e => setComments(e.target.value)}
              placeholder="Tell us what went well or how municipal services can improve..."
              className="w-full text-xs border border-slate-200 rounded-md p-2.5 focus:ring-1 focus:ring-civic-teal-500 outline-none"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100 rounded-md"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 text-xs font-semibold text-white bg-civic-teal-600 hover:bg-civic-teal-700 rounded-md shadow-sm transition disabled:opacity-50"
            >
              {loading ? 'Submitting...' : 'Submit Rating'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
