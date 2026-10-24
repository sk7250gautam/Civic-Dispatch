import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Navbar } from './components/Navbar';
import { RoleSwitcherBar } from './components/RoleSwitcherBar';
import { HomePage } from './pages/HomePage';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { CitizenPortal } from './pages/CitizenPortal';
import { NewComplaintPage } from './pages/NewComplaintPage';
import { OfficerWorkspace } from './pages/OfficerWorkspace';
import { ManagerCommandCenter } from './pages/ManagerCommandCenter';
import { AdminPanel } from './pages/AdminPanel';

const queryClient = new QueryClient();

// Protected Route Component
const ProtectedRoute: React.FC<{ children: React.ReactNode; allowedRoles?: string[] }> = ({
  children,
  allowedRoles,
}) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center text-xs text-slate-500">
        Authenticating municipal session...
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return (
      <div className="max-w-md mx-auto my-16 p-6 bg-white rounded-2xl border border-slate-200 shadow text-center space-y-3">
        <h3 className="font-bold text-rose-600 text-sm">Access Restricted</h3>
        <p className="text-xs text-slate-600">
          Your active account role (<strong>{user.role}</strong>) does not have authorization to view this workspace.
        </p>
        <p className="text-[11px] text-slate-400">Use the Demo Bar at the top to switch to an authorized role.</p>
      </div>
    );
  }

  return <>{children}</>;
};

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900 font-sans">
            {/* Top Recruiter Demo Bar */}
            <RoleSwitcherBar />
            {/* Municipal Navigation */}
            <Navbar />

            {/* Main Application Routes */}
            <main className="flex-1">
              <Routes>
                {/* Public Routes */}
                <Route path="/" element={<HomePage />} />
                <Route path="/login" element={<LoginPage />} />
                <Route path="/register" element={<RegisterPage />} />

                {/* Citizen Routes */}
                <Route
                  path="/citizen"
                  element={
                    <ProtectedRoute allowedRoles={['CITIZEN', 'SYSTEM_ADMIN']}>
                      <CitizenPortal />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/citizen/new"
                  element={
                    <ProtectedRoute allowedRoles={['CITIZEN', 'SYSTEM_ADMIN']}>
                      <NewComplaintPage />
                    </ProtectedRoute>
                  }
                />

                {/* Field Officer Routes */}
                <Route
                  path="/officer"
                  element={
                    <ProtectedRoute allowedRoles={['FIELD_OFFICER', 'DEPARTMENT_MANAGER', 'SYSTEM_ADMIN']}>
                      <OfficerWorkspace />
                    </ProtectedRoute>
                  }
                />

                {/* Department Manager Routes */}
                <Route
                  path="/manager"
                  element={
                    <ProtectedRoute allowedRoles={['DEPARTMENT_MANAGER', 'SYSTEM_ADMIN']}>
                      <ManagerCommandCenter />
                    </ProtectedRoute>
                  }
                />

                {/* System Admin Routes */}
                <Route
                  path="/admin"
                  element={
                    <ProtectedRoute allowedRoles={['SYSTEM_ADMIN']}>
                      <AdminPanel />
                    </ProtectedRoute>
                  }
                />

                {/* Fallback */}
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </main>

            {/* Municipal Footer */}
            <footer className="bg-white border-t border-slate-200 py-6 text-center text-xs text-slate-500">
              <div className="max-w-7xl mx-auto px-4 flex flex-wrap items-center justify-between gap-4">
                <span className="font-semibold text-slate-700">CIVIC DISPATCH &copy; 2026</span>
                <span className="text-[11px] text-slate-400">
                  Municipal Grievance, Field Operations & SLA Escalation Architecture
                </span>
                <span className="text-[11px] font-mono text-civic-teal-700">Production Build v1.0.0</span>
              </div>
            </footer>
          </div>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
};

export default App;
