import {
  User,
  Complaint,
  ManagerDashboardData,
  NotificationItem,
  SLAPolicy,
  Department
} from '../types';

const API_ROOT = (import.meta as any).env?.VITE_API_BASE_URL || '';
const BASE_URL = `${API_ROOT}/api/v1`;

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const defaultHeaders: HeadersInit = {
    'Accept': 'application/json',
  };

  // Only set Content-Type to JSON if body is not FormData
  if (!(options.body instanceof FormData)) {
    defaultHeaders['Content-Type'] = 'application/json';
  }

  const config: RequestInit = {
    ...options,
    credentials: 'include',
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  };

  const response = await fetch(`${BASE_URL}${endpoint}`, config);

  if (!response.ok) {
    let errorMessage = `HTTP error ${response.status}`;
    try {
      const errData = await response.json();
      errorMessage = errData.message || errData.error || errorMessage;
    } catch {
      // ignore
    }
    throw new Error(errorMessage);
  }

  return response.json();
}

export const api = {
  // Auth
  login: (credentials: { email: string; password: string }) =>
    request<{ user: User }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    }),

  register: (userData: { email: string; password: string; full_name: string; phone?: string }) =>
    request<{ user: User }>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    }),

  logout: () =>
    request<{ message: string }>('/auth/logout', {
      method: 'POST',
    }),

  getMe: () =>
    request<{ authenticated: boolean; user: User | null }>('/auth/me'),

  getDemoAccounts: () =>
    request<{ accounts: any[] }>('/auth/demo-accounts'),

  // Public Transparency
  getPublicStatistics: () =>
    request<any>('/public/statistics'),

  trackGrievance: (referenceId: string) =>
    request<{ complaint: any }>(`/public/complaints/${referenceId}`),

  getPublicMapMarkers: () =>
    request<{ markers: any[] }>('/public/map-clusters'),

  getDepartments: () =>
    request<{ departments: Department[]; service_zones: any[] }>('/public/departments'),

  // Citizen
  submitComplaint: (formData: FormData | object) => {
    const isForm = formData instanceof FormData;
    return request<{ complaint: Complaint }>('/citizens/complaints', {
      method: 'POST',
      body: isForm ? formData : JSON.stringify(formData),
    });
  },

  getCitizenComplaints: (params?: { page?: number; status?: string }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set('page', params.page.toString());
    if (params?.status) query.set('status', params.status);
    return request<{ complaints: Complaint[]; pagination: any }>(`/citizens/complaints?${query.toString()}`);
  },

  getComplaintDetails: (id: number) =>
    request<{ complaint: Complaint }>(`/citizens/complaints/${id}`),

  reopenComplaint: (id: number, reason: string) =>
    request<{ complaint: Complaint }>(`/citizens/complaints/${id}/reopen`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    }),

  submitFeedback: (id: number, feedback: { rating: number; comments?: string; speed_rating?: number; officer_rating?: number }) =>
    request<{ message: string }>(`/citizens/complaints/${id}/feedback`, {
      method: 'POST',
      body: JSON.stringify(feedback),
    }),

  // Officer
  getOfficerQueue: (status?: string) => {
    const query = status ? `?status=${status}` : '';
    return request<{ queue: Complaint[]; count: number }>(`/officers/queue${query}`);
  },

  acknowledgeComplaint: (id: number) =>
    request<{ complaint: Complaint }>(`/officers/complaints/${id}/acknowledge`, {
      method: 'POST',
    }),

  startWork: (id: number) =>
    request<{ complaint: Complaint }>(`/officers/complaints/${id}/start-work`, {
      method: 'POST',
    }),

  resolveComplaint: (id: number, payload: FormData | object) => {
    const isForm = payload instanceof FormData;
    return request<{ complaint: Complaint }>(`/officers/complaints/${id}/resolve`, {
      method: 'POST',
      body: isForm ? payload : JSON.stringify(payload),
    });
  },

  addInternalNote: (id: number, note: string) =>
    request<{ internal_notes: string }>(`/officers/complaints/${id}/notes`, {
      method: 'POST',
      body: JSON.stringify({ note }),
    }),

  // Manager
  getManagerDashboard: () =>
    request<ManagerDashboardData>('/managers/dashboard'),

  getDepartmentComplaints: (params?: any) => {
    const query = new URLSearchParams(params || {}).toString();
    return request<{ complaints: Complaint[]; pagination: any }>(`/managers/complaints?${query}`);
  },

  assignOfficer: (id: number, officerId: number, notes?: string) =>
    request<{ complaint: Complaint }>(`/managers/complaints/${id}/assign`, {
      method: 'POST',
      body: JSON.stringify({ officer_id: officerId, notes }),
    }),

  rejectComplaint: (id: number, reason: string) =>
    request<{ complaint: Complaint }>(`/managers/complaints/${id}/reject`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    }),

  getDepartmentOfficers: () =>
    request<{ officers: any[] }>('/managers/officers'),

  // Admin
  getAdminOverview: () =>
    request<any>('/admin/overview'),

  getAdminUsers: () =>
    request<{ users: User[] }>('/admin/users'),

  createStaffUser: (userData: any) =>
    request<{ user: User }>('/admin/users', {
      method: 'POST',
      body: JSON.stringify(userData),
    }),

  getSLAPolicies: () =>
    request<{ policies: SLAPolicy[] }>('/admin/sla-policies'),

  createSLAPolicy: (policyData: any) =>
    request<{ policy: SLAPolicy }>('/admin/sla-policies', {
      method: 'POST',
      body: JSON.stringify(policyData),
    }),

  getAuditLogs: (page: number = 1) =>
    request<{ audit_logs: any[]; pagination: any }>(`/admin/audit-logs?page=${page}`),

  triggerSLASweep: () =>
    request<{ message: string; results: any }>('/admin/trigger-sla-check', {
      method: 'POST',
    }),

  // AI Assistance
  aiCategorize: (title: string, description: string) =>
    request<{ category: string; confidence: number; source: string; reasoning: string }>('/ai/categorize', {
      method: 'POST',
      body: JSON.stringify({ title, description }),
    }),

  aiRecommendPriority: (title: string, description: string, category: string) =>
    request<{ recommended_priority: string; confidence: number; is_safety_hazard: boolean; triggers: string[]; reasoning: string; disclaimer: string }>('/ai/priority', {
      method: 'POST',
      body: JSON.stringify({ title, description, category }),
    }),

  aiDuplicateCheck: (payload: { latitude: number; longitude: number; category: string; title: string; description: string }) =>
    request<{ candidates: any[] }>('/ai/duplicate-check', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  aiSummarize: (payload: { title: string; description: string; category: string; address?: string }) =>
    request<{ summary: string; key_action_item: string; source: string }>('/ai/summarize', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  // Notifications
  getNotifications: () =>
    request<{ notifications: NotificationItem[]; unread_count: number }>('/notifications'),

  markNotificationRead: (id: number) =>
    request<{ message: string }>(`/notifications/${id}/read`, {
      method: 'POST',
    }),

  markAllNotificationsRead: () =>
    request<{ message: string }>('/notifications/read-all', {
      method: 'POST',
    }),
};
