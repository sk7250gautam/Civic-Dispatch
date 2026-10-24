import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Building, Lock, Mail, Sparkles, ArrowRight, AlertCircle } from 'lucide-react';

export const LoginPage: React.FC = () => {
  const { login, switchRole, user } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // If already logged in, redirect to appropriate role portal
  React.useEffect(() => {
    if (user) {
      if (user.role === 'CITIZEN') navigate('/citizen');
      else if (user.role === 'FIELD_OFFICER') navigate('/officer');
      else if (user.role === 'DEPARTMENT_MANAGER') navigate('/manager');
      else if (user.role === 'SYSTEM_ADMIN') navigate('/admin');
    }
  }, [user, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(email, password);
    } catch (err: any) {
      setError(err.message || 'Invalid credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = async (role: any) => {
    setError(null);
    setLoading(true);
    try {
      await switchRole(role);
    } catch (err: any) {
      setError('Demo login failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 bg-white p-8 rounded-2xl border border-slate-200 shadow-xl">
        <div className="text-center space-y-2">
          <div className="w-12 h-12 rounded-xl bg-navy-900 text-civic-teal-400 mx-auto flex items-center justify-center shadow">
            <Building className="w-6 h-6" />
          </div>
          <h2 className="text-2xl font-extrabold text-navy-950">Civic Dispatch Portal</h2>
          <p className="text-xs text-slate-500">Sign in to report or manage municipal services</p>
        </div>

        {/* 1-Click Demo Logins for Evaluator Convenience */}
        <div className="p-4 bg-navy-50 border border-navy-100 rounded-xl space-y-2">
          <div className="flex items-center gap-1.5 text-xs font-bold text-navy-900">
            <Sparkles className="w-4 h-4 text-civic-teal-600" />
            Recruiter 1-Click Demo Login
          </div>
          <p className="text-[11px] text-slate-600">Select any role to test live authenticated features instantly:</p>
          <div className="grid grid-cols-2 gap-2 pt-1">
            <button
              type="button"
              onClick={() => handleDemoLogin('CITIZEN')}
              className="py-1.5 px-2 bg-white hover:bg-slate-50 border border-slate-200 rounded-lg text-xs font-semibold text-slate-800 text-center shadow-sm"
            >
              Citizen
            </button>
            <button
              type="button"
              onClick={() => handleDemoLogin('FIELD_OFFICER')}
              className="py-1.5 px-2 bg-white hover:bg-slate-50 border border-slate-200 rounded-lg text-xs font-semibold text-amber-800 text-center shadow-sm"
            >
              Field Officer
            </button>
            <button
              type="button"
              onClick={() => handleDemoLogin('DEPARTMENT_MANAGER')}
              className="py-1.5 px-2 bg-white hover:bg-slate-50 border border-slate-200 rounded-lg text-xs font-semibold text-emerald-800 text-center shadow-sm"
            >
              Dept Manager
            </button>
            <button
              type="button"
              onClick={() => handleDemoLogin('SYSTEM_ADMIN')}
              className="py-1.5 px-2 bg-white hover:bg-slate-50 border border-slate-200 rounded-lg text-xs font-semibold text-purple-800 text-center shadow-sm"
            >
              Admin
            </button>
          </div>
        </div>

        {error && (
          <div className="p-3 bg-rose-50 text-rose-700 border border-rose-200 rounded-lg text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Email Address</label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              <input
                type="email"
                required
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="name@civicdispatch.org"
                className="w-full text-xs pl-9 pr-3 py-2.5 rounded-lg border border-slate-200 focus:ring-2 focus:ring-civic-teal-500 outline-none"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              <input
                type="password"
                required
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full text-xs pl-9 pr-3 py-2.5 rounded-lg border border-slate-200 focus:ring-2 focus:ring-civic-teal-500 outline-none"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 px-4 bg-navy-900 hover:bg-navy-800 text-white font-semibold text-xs rounded-lg shadow transition flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {loading ? 'Authenticating...' : 'Sign In'}
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>

        <div className="text-center text-xs text-slate-500 pt-2 border-t border-slate-100">
          New citizen?{' '}
          <Link to="/register" className="font-semibold text-civic-teal-700 hover:underline">
            Register an account
          </Link>
        </div>
      </div>
    </div>
  );
};
