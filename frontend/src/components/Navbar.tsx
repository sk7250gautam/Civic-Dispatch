import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import { NotificationItem } from '../types';
import {
  Building,
  Bell,
  LogOut,
  PlusCircle,
  ClipboardList,
  BarChart3,
  Shield,
  Layers,
  MapPin,
  CheckCircle2,
  Menu,
  X,
} from 'lucide-react';

export const Navbar: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [unreadCount, setUnreadCount] = useState<number>(0);
  const [showNotifications, setShowNotifications] = useState<boolean>(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState<boolean>(false);

  const fetchNotifs = async () => {
    if (!user) return;
    try {
      const res = await api.getNotifications();
      setNotifications(res.notifications || []);
      setUnreadCount(res.unread_count || 0);
    } catch {
      // ignore
    }
  };

  useEffect(() => {
    if (user) {
      fetchNotifs();
      const interval = setInterval(fetchNotifs, 20000); // Polling for in-app notifications
      return () => clearInterval(interval);
    }
  }, [user]);

  const handleMarkAllRead = async () => {
    try {
      await api.markAllNotificationsRead();
      setUnreadCount(0);
      setNotifications(notifications.map(n => ({ ...n, is_read: true })));
    } catch {
      // ignore
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  const role = user?.role;

  const isActive = (path: string) => location.pathname === path;

  return (
    <header className="bg-white border-b border-slate-200 sticky top-9 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          {/* Logo & Platform Name */}
          <div className="flex items-center gap-3">
            <Link to="/" className="flex items-center gap-2.5 group">
              <div className="w-10 h-10 rounded-lg bg-navy-900 flex items-center justify-center text-civic-teal-400 shadow-sm group-hover:bg-navy-800 transition">
                <Building className="w-5 h-5" />
              </div>
              <div>
                <span className="font-bold text-lg text-navy-950 tracking-tight block leading-tight">
                  CIVIC DISPATCH
                </span>
                <span className="text-[10px] font-semibold text-civic-teal-700 tracking-wider uppercase block">
                  Municipal Operations SLA Platform
                </span>
              </div>
            </Link>

            {/* Role indicator pill */}
            {user && (
              <span className="hidden sm:inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-slate-100 text-slate-700 border border-slate-200 ml-2">
                {role?.replace('_', ' ')}
              </span>
            )}
          </div>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center gap-1">
            <Link
              to="/"
              className={`px-3 py-2 rounded-md text-sm font-medium transition ${
                isActive('/') ? 'text-navy-900 font-semibold bg-slate-100' : 'text-slate-600 hover:text-navy-900 hover:bg-slate-50'
              }`}
            >
              Public Transparency
            </Link>

            {/* Citizen Links */}
            {role === 'CITIZEN' && (
              <>
                <Link
                  to="/citizen"
                  className={`px-3 py-2 rounded-md text-sm font-medium transition ${
                    isActive('/citizen') ? 'text-navy-900 font-semibold bg-slate-100' : 'text-slate-600 hover:text-navy-900 hover:bg-slate-50'
                  }`}
                >
                  My Grievances
                </Link>
                <Link
                  to="/citizen/new"
                  className="ml-2 inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-md text-sm font-semibold bg-civic-teal-600 text-white hover:bg-civic-teal-700 shadow-sm transition"
                >
                  <PlusCircle className="w-4 h-4" />
                  Report Issue
                </Link>
              </>
            )}

            {/* Officer Links */}
            {role === 'FIELD_OFFICER' && (
              <Link
                to="/officer"
                className={`flex items-center gap-1.5 px-3 py-2 rounded-md text-sm font-medium transition ${
                  isActive('/officer') ? 'text-navy-900 font-semibold bg-slate-100' : 'text-slate-600 hover:text-navy-900 hover:bg-slate-50'
                }`}
              >
                <ClipboardList className="w-4 h-4 text-amber-600" />
                Field Operations Queue
              </Link>
            )}

            {/* Manager Links */}
            {role === 'DEPARTMENT_MANAGER' && (
              <Link
                to="/manager"
                className={`flex items-center gap-1.5 px-3 py-2 rounded-md text-sm font-medium transition ${
                  isActive('/manager') ? 'text-navy-900 font-semibold bg-slate-100' : 'text-slate-600 hover:text-navy-900 hover:bg-slate-50'
                }`}
              >
                <BarChart3 className="w-4 h-4 text-emerald-600" />
                Command Center
              </Link>
            )}

            {/* Admin Links */}
            {role === 'SYSTEM_ADMIN' && (
              <Link
                to="/admin"
                className={`flex items-center gap-1.5 px-3 py-2 rounded-md text-sm font-medium transition ${
                  isActive('/admin') ? 'text-navy-900 font-semibold bg-slate-100' : 'text-slate-600 hover:text-navy-900 hover:bg-slate-50'
                }`}
              >
                <Shield className="w-4 h-4 text-purple-600" />
                System Administration
              </Link>
            )}
          </nav>

          {/* Right Controls: Notifications & Profile / Sign In */}
          <div className="flex items-center gap-3">
            {user ? (
              <>
                {/* Notifications Bell */}
                <div className="relative">
                  <button
                    onClick={() => setShowNotifications(!showNotifications)}
                    className="p-2 rounded-full text-slate-500 hover:text-slate-700 hover:bg-slate-100 relative transition"
                    title="Notifications"
                  >
                    <Bell className="w-5 h-5" />
                    {unreadCount > 0 && (
                      <span className="absolute top-1 right-1 w-4 h-4 bg-rose-600 text-white text-[10px] font-bold rounded-full flex items-center justify-center animate-pulse">
                        {unreadCount}
                      </span>
                    )}
                  </button>

                  {/* Notifications Popover */}
                  {showNotifications && (
                    <div className="absolute right-0 mt-2 w-80 sm:w-96 bg-white rounded-lg shadow-xl border border-slate-200 py-2 z-50">
                      <div className="px-4 py-2 border-b border-slate-100 flex items-center justify-between">
                        <span className="font-semibold text-sm text-slate-900">Notifications</span>
                        {unreadCount > 0 && (
                          <button
                            onClick={handleMarkAllRead}
                            className="text-xs text-civic-teal-700 hover:underline font-medium"
                          >
                            Mark all as read
                          </button>
                        )}
                      </div>
                      <div className="max-h-80 overflow-y-auto divide-y divide-slate-100">
                        {notifications.length === 0 ? (
                          <div className="p-4 text-center text-xs text-slate-500">No notifications yet.</div>
                        ) : (
                          notifications.map(n => (
                            <div
                              key={n.id}
                              className={`p-3 text-xs ${n.is_read ? 'bg-white' : 'bg-slate-50 font-medium'}`}
                            >
                              <div className="font-semibold text-slate-800">{n.title}</div>
                              <div className="text-slate-600 mt-0.5">{n.message}</div>
                              <div className="text-[10px] text-slate-400 mt-1">
                                {new Date(n.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                              </div>
                            </div>
                          ))
                        )}
                      </div>
                    </div>
                  )}
                </div>

                {/* User info & Logout */}
                <div className="flex items-center gap-2 pl-2 border-l border-slate-200">
                  <div className="hidden lg:block text-right">
                    <div className="text-xs font-semibold text-slate-800 leading-tight">{user.full_name}</div>
                    <div className="text-[10px] text-slate-500">{user.email}</div>
                  </div>
                  <button
                    onClick={handleLogout}
                    className="p-2 text-slate-500 hover:text-rose-600 hover:bg-rose-50 rounded-md transition"
                    title="Log Out"
                  >
                    <LogOut className="w-4 h-4" />
                  </button>
                </div>
              </>
            ) : (
              <div className="flex items-center gap-2">
                <Link
                  to="/login"
                  className="px-3 py-1.5 text-sm font-medium text-slate-700 hover:text-navy-900 hover:bg-slate-100 rounded-md transition"
                >
                  Sign In
                </Link>
                <Link
                  to="/register"
                  className="px-3.5 py-1.5 text-sm font-semibold text-white bg-navy-900 hover:bg-navy-800 rounded-md shadow-sm transition"
                >
                  Register
                </Link>
              </div>
            )}

            {/* Mobile Hamburger */}
            <div className="md:hidden flex items-center">
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="p-2 rounded-md text-slate-600 hover:bg-slate-100"
              >
                {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Mobile Menu Dropdown */}
      {mobileMenuOpen && (
        <div className="md:hidden px-4 pt-2 pb-4 border-t border-slate-100 bg-white space-y-1">
          <Link
            to="/"
            onClick={() => setMobileMenuOpen(false)}
            className="block px-3 py-2 rounded-md text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            Public Transparency
          </Link>
          {role === 'CITIZEN' && (
            <>
              <Link
                to="/citizen"
                onClick={() => setMobileMenuOpen(false)}
                className="block px-3 py-2 rounded-md text-sm font-medium text-slate-700 hover:bg-slate-50"
              >
                My Grievances
              </Link>
              <Link
                to="/citizen/new"
                onClick={() => setMobileMenuOpen(false)}
                className="block px-3 py-2 rounded-md text-sm font-semibold text-civic-teal-700 bg-civic-teal-50"
              >
                + Report New Grievance
              </Link>
            </>
          )}
          {role === 'FIELD_OFFICER' && (
            <Link
              to="/officer"
              onClick={() => setMobileMenuOpen(false)}
              className="block px-3 py-2 rounded-md text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              Field Operations Queue
            </Link>
          )}
          {role === 'DEPARTMENT_MANAGER' && (
            <Link
              to="/manager"
              onClick={() => setMobileMenuOpen(false)}
              className="block px-3 py-2 rounded-md text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              Command Center
            </Link>
          )}
          {role === 'SYSTEM_ADMIN' && (
            <Link
              to="/admin"
              onClick={() => setMobileMenuOpen(false)}
              className="block px-3 py-2 rounded-md text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              System Administration
            </Link>
          )}
        </div>
      )}
    </header>
  );
};
