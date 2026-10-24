import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { GrievanceMap } from '../components/GrievanceMap';
import {
  FileText,
  MapPin,
  Upload,
  Sparkles,
  AlertTriangle,
  CheckCircle,
  Copy,
  Info,
  ArrowRight,
  ShieldAlert,
} from 'lucide-react';

const CATEGORIES = [
  { value: 'ROAD_INFRASTRUCTURE', label: 'Road & Pavement Damage' },
  { value: 'WATER_SUPPLY', label: 'Drinking Water & Pipeline Leakage' },
  { value: 'SOLID_WASTE', label: 'Garbage & Waste Clearance' },
  { value: 'STREET_LIGHTING', label: 'Street Lighting & Dark Alleys' },
  { value: 'DRAINAGE_FLOODING', label: 'Drainage & Monsoon Flooding' },
  { value: 'HEALTH_SANITATION', label: 'Health, Pest & Vector Control' },
  { value: 'OTHER', label: 'Other Municipal Services' },
];

export const NewComplaintPage: React.FC = () => {
  const navigate = useNavigate();

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('ROAD_INFRASTRUCTURE');
  const [priority, setPriority] = useState('MEDIUM');
  const [address, setAddress] = useState('');
  const [latitude, setLatitude] = useState(12.9716);
  const [longitude, setLongitude] = useState(77.5946);
  const [photo, setPhoto] = useState<File | null>(null);
  const [photoPreview, setPhotoPreview] = useState<string | null>(null);

  // AI Assistant States
  const [aiLoading, setAiLoading] = useState(false);
  const [aiCatSuggestion, setAiCatSuggestion] = useState<any>(null);
  const [aiHazardAlert, setAiHazardAlert] = useState<any>(null);
  const [duplicateCandidates, setDuplicateCandidates] = useState<any[]>([]);

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handlePhotoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setPhoto(file);
      setPhotoPreview(URL.createObjectURL(file));
    }
  };

  const handleRunAiAnalysis = async () => {
    if (!title.trim() && !description.trim()) {
      alert('Please enter a title or description first to run AI categorization.');
      return;
    }

    setAiLoading(true);
    try {
      // 1. Categorization
      const catRes = await api.aiCategorize(title, description);
      setAiCatSuggestion(catRes);
      if (catRes.category) {
        setCategory(catRes.category);
      }

      // 2. Priority & Hazard Detection
      const priRes = await api.aiRecommendPriority(title, description, catRes.category || category);
      setAiHazardAlert(priRes);
      if (priRes.recommended_priority) {
        setPriority(priRes.recommended_priority);
      }

      // 3. Proximity Duplicate Check
      const dupRes = await api.aiDuplicateCheck({
        latitude,
        longitude,
        category: catRes.category || category,
        title,
        description,
      });
      setDuplicateCandidates(dupRes.candidates || []);
    } catch (err) {
      console.error('AI assistant error:', err);
    } finally {
      setAiLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !description.trim()) {
      setError('Title and problem description are required.');
      return;
    }

    setError(null);
    setSubmitting(true);

    try {
      const formData = new FormData();
      formData.append('title', title);
      formData.append('description', description);
      formData.append('category', category);
      formData.append('priority', priority);
      formData.append('latitude', latitude.toString());
      formData.append('longitude', longitude.toString());
      formData.append('address', address);
      if (photo) {
        formData.append('photo', photo);
      }

      const res = await api.submitComplaint(formData);
      navigate('/citizen', { state: { newReferenceId: res.complaint.reference_id } });
    } catch (err: any) {
      setError(err.message || 'Failed to submit grievance.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 space-y-8">
      <div>
        <h1 className="text-2xl font-extrabold text-navy-950">Lodge Municipal Grievance</h1>
        <p className="text-xs text-slate-500 mt-1">
          Submit infrastructure or public utility issues directly to your municipal corporation.
        </p>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 text-rose-700 border border-rose-200 rounded-xl text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Step 1: Issue Description */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <FileText className="w-4 h-4 text-civic-teal-600" />
              1. Issue Details
            </h2>
            <button
              type="button"
              onClick={handleRunAiAnalysis}
              disabled={aiLoading}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-navy-50 hover:bg-navy-100 text-navy-800 border border-navy-200 transition"
            >
              <Sparkles className="w-3.5 h-3.5 text-civic-teal-600" />
              {aiLoading ? 'Analyzing...' : 'AI Auto-Detect & Hazard Check'}
            </button>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Grievance Title</label>
            <input
              type="text"
              required
              value={title}
              onChange={e => setTitle(e.target.value)}
              placeholder="e.g. Major pothole causing vehicle damage near 4th cross"
              className="w-full text-xs p-2.5 rounded-lg border border-slate-200 focus:ring-2 focus:ring-civic-teal-500 outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Detailed Description</label>
            <textarea
              required
              rows={4}
              value={description}
              onChange={e => setDescription(e.target.value)}
              placeholder="Provide specific details about the problem, visual landmarks, and severity..."
              className="w-full text-xs p-2.5 rounded-lg border border-slate-200 focus:ring-2 focus:ring-civic-teal-500 outline-none"
            />
          </div>

          {/* AI Feedback Banner */}
          {aiCatSuggestion && (
            <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs space-y-1">
              <div className="flex items-center gap-2">
                <span className="font-semibold text-slate-800">
                  AI Category Suggestion ({Math.round(aiCatSuggestion.confidence * 100)}% confidence):
                </span>
                <span className="font-mono text-civic-teal-700 font-bold">{aiCatSuggestion.category}</span>
              </div>
              <p className="text-[11px] text-slate-500">{aiCatSuggestion.reasoning}</p>
            </div>
          )}

          {/* Critical Hazard Alert */}
          {aiHazardAlert?.is_safety_hazard && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-800 flex items-start gap-2">
              <ShieldAlert className="w-4 h-4 shrink-0 text-rose-600 mt-0.5" />
              <div>
                <strong className="block font-bold">Public Safety Hazard Alert Flagged</strong>
                <p className="text-[11px] text-rose-700">{aiHazardAlert.reasoning}</p>
                <span className="text-[10px] text-rose-500 italic mt-0.5 block">{aiHazardAlert.disclaimer}</span>
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Category</label>
              <select
                value={category}
                onChange={e => setCategory(e.target.value)}
                className="w-full text-xs p-2.5 rounded-lg border border-slate-200 bg-white"
              >
                {CATEGORIES.map(c => (
                  <option key={c.value} value={c.value}>
                    {c.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Priority</label>
              <select
                value={priority}
                onChange={e => setPriority(e.target.value)}
                className="w-full text-xs p-2.5 rounded-lg border border-slate-200 bg-white"
              >
                <option value="LOW">Low (Standard routine maintenance)</option>
                <option value="MEDIUM">Medium (Normal priority)</option>
                <option value="HIGH">High (Urgent municipal impact)</option>
                <option value="CRITICAL">Critical (Immediate safety hazard)</option>
              </select>
            </div>
          </div>
        </div>

        {/* Potential Duplicates Section if Found */}
        {duplicateCandidates.length > 0 && (
          <div className="bg-amber-50 p-5 rounded-2xl border border-amber-200 text-xs space-y-3">
            <div className="flex items-center gap-2 font-bold text-amber-900">
              <Copy className="w-4 h-4 text-amber-600" />
              Possible Similar Grievances Reported Nearby ({duplicateCandidates.length} found)
            </div>
            <p className="text-[11px] text-amber-700">
              Someone may have already reported this issue recently. Check below before submitting a duplicate:
            </p>
            <div className="space-y-2">
              {duplicateCandidates.map(dup => (
                <div key={dup.id} className="bg-white p-3 rounded-lg border border-amber-200 shadow-sm flex items-center justify-between">
                  <div>
                    <span className="font-mono font-bold text-navy-900">{dup.reference_id}</span>
                    <div className="font-semibold text-slate-800">{dup.title}</div>
                    <div className="text-[10px] text-slate-500">
                      Approx {dup.distance_meters}m away • Status: {dup.status}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Step 2: Geospatial Map Pin Location */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <MapPin className="w-4 h-4 text-civic-teal-600" />
              2. Geographic Location Pin
            </h2>
            <span className="text-xs text-slate-400 font-mono">
              {latitude}, {longitude}
            </span>
          </div>

          <p className="text-xs text-slate-500">
            Click on the map or click "Use My GPS Location" to position the grievance pin accurately for field teams.
          </p>

          <GrievanceMap
            mode="picker"
            initialLat={latitude}
            initialLng={longitude}
            onLocationSelect={(lat, lng) => {
              setLatitude(lat);
              setLongitude(lng);
            }}
            height="360px"
          />

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Street Address or Landmark Note</label>
            <input
              type="text"
              value={address}
              onChange={e => setAddress(e.target.value)}
              placeholder="e.g. In front of City Public Hospital, Gate 2"
              className="w-full text-xs p-2.5 rounded-lg border border-slate-200 focus:ring-2 focus:ring-civic-teal-500 outline-none"
            />
          </div>
        </div>

        {/* Step 3: Photographic Evidence */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <Upload className="w-4 h-4 text-civic-teal-600" />
            3. Photographic Evidence (Optional)
          </h2>
          <p className="text-xs text-slate-500">
            Upload clear photographs of the civic problem. Photos help officers verify and prioritize field dispatch.
          </p>

          <div className="flex items-center gap-4">
            <label className="cursor-pointer px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg border border-slate-300 transition">
              Choose Photo File
              <input type="file" accept="image/*" onChange={handlePhotoChange} className="hidden" />
            </label>
            {photo && <span className="text-xs text-slate-600 font-medium">{photo.name}</span>}
          </div>

          {photoPreview && (
            <div className="mt-3">
              <img
                src={photoPreview}
                alt="Upload preview"
                className="max-h-48 rounded-lg border border-slate-200 object-cover shadow-sm"
              />
            </div>
          )}
        </div>

        {/* Submission Actions */}
        <div className="flex items-center justify-end gap-3 pt-4">
          <button
            type="button"
            onClick={() => navigate('/citizen')}
            className="px-5 py-2.5 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-xl"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={submitting}
            className="px-6 py-2.5 bg-civic-teal-600 hover:bg-civic-teal-700 text-white font-bold text-xs rounded-xl shadow-md transition flex items-center gap-2 disabled:opacity-50"
          >
            {submitting ? 'Submitting Grievance...' : 'Submit Municipal Grievance'}
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </form>
    </div>
  );
};
