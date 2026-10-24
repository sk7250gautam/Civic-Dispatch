export type Role = 'CITIZEN' | 'FIELD_OFFICER' | 'DEPARTMENT_MANAGER' | 'SYSTEM_ADMIN';

export type ComplaintStatus =
  | 'SUBMITTED'
  | 'ACKNOWLEDGED'
  | 'ASSIGNED'
  | 'IN_PROGRESS'
  | 'RESOLVED'
  | 'CLOSED'
  | 'REOPENED'
  | 'REJECTED';

export type ComplaintPriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export type ComplaintCategory =
  | 'ROAD_INFRASTRUCTURE'
  | 'WATER_SUPPLY'
  | 'SOLID_WASTE'
  | 'STREET_LIGHTING'
  | 'DRAINAGE_FLOODING'
  | 'HEALTH_SANITATION'
  | 'OTHER';

export interface User {
  id: number;
  email: string;
  full_name: string;
  phone?: string | null;
  role: Role;
  department_id?: number | null;
  department_name?: string | null;
  is_active: boolean;
  created_at?: string;
}

export interface Attachment {
  id: number;
  complaint_id: number;
  filename: string;
  file_size: number;
  mime_type: string;
  attachment_type: string;
  url: string;
  created_at: string;
}

export interface StatusHistory {
  id: number;
  complaint_id: number;
  previous_status?: string | null;
  new_status: string;
  acting_user_name: string;
  acting_user_role: string;
  reason?: string | null;
  metadata?: any;
  created_at: string;
}

export interface CitizenFeedback {
  id: number;
  rating: number;
  comments?: string | null;
  resolution_speed_rating?: number | null;
  officer_conduct_rating?: number | null;
  created_at: string;
}

export interface Complaint {
  id: number;
  reference_id: string;
  title: string;
  description: string;
  category: ComplaintCategory;
  priority: ComplaintPriority;
  status: ComplaintStatus;
  current_escalation_level: number;
  sla_deadline?: string | null;
  sla_duration_hours: number;
  is_overdue: boolean;
  department_id?: number | null;
  department_name?: string | null;
  service_zone_id?: number | null;
  service_zone_name?: string | null;
  assigned_officer_id?: number | null;
  assigned_officer_name?: string | null;
  internal_notes?: string | null;
  latitude: number;
  longitude: number;
  address?: string | null;
  verified_location: boolean;
  verification_distance_meters?: number | null;
  location_exception_reason?: string | null;
  resolution_summary?: string | null;
  reopen_count: number;
  reopen_reason?: string | null;
  created_at: string;
  updated_at?: string;
  resolved_at?: string | null;
  closed_at?: string | null;
  attachments?: Attachment[];
  status_history?: StatusHistory[];
  feedback?: CitizenFeedback | null;
}

export interface Department {
  id: number;
  name: string;
  code: string;
  description?: string;
  contact_email?: string;
  is_active: boolean;
}

export interface SLAPolicy {
  id: number;
  name: string;
  category?: string | null;
  priority?: string | null;
  duration_hours: number;
  grace_period_hours: number;
  warning_threshold_percent: number;
  escalation_target_role: string;
  is_active: boolean;
  created_at: string;
}

export interface DashboardMetrics {
  total_complaints: number;
  open_complaints: number;
  submitted: number;
  acknowledged: number;
  assigned: number;
  in_progress: number;
  resolved: number;
  rejected: number;
  overdue: number;
  sla_compliance_rate: number;
  avg_resolution_hours: number;
}

export interface ManagerDashboardData {
  metrics: DashboardMetrics;
  breakdown: {
    by_category: Record<string, number>;
    by_priority: Record<string, number>;
    by_escalation: {
      normal: number;
      warning_tier_1: number;
      overdue_tier_2: number;
      critical_tier_3: number;
    };
  };
}

export interface NotificationItem {
  id: number;
  user_id: number;
  complaint_id?: number;
  complaint_reference_id?: string;
  title: string;
  message: string;
  notification_type: string;
  is_read: boolean;
  created_at: string;
}
