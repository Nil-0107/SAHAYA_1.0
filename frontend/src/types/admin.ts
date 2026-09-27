import type { Notification } from "./notification";

export interface AdminAggregate {
  total_case_count: number;
  active_case_count: number;
  total_support_request_count: number;
  open_support_request_count: number;
  resolved_support_request_count: number;
  active_assignment_count: number;
  district_count: number;
  total_checkin_count: number;
  total_user_count: number;
  active_user_count: number;
  unread_admin_notification_count: number;
}

export interface AdminDistrictAnalytics {
  district: string;
  case_count: number;
  active_case_count: number;
  support_request_count: number;
  open_support_request_count: number;
  high_priority_request_count: number;
  active_assignment_count: number;
  is_demo: boolean;
}

export interface AdminCountBucket {
  label: string;
  count: number;
}

export interface AdminSupportRequestCounts {
  by_type: AdminCountBucket[];
  by_status: AdminCountBucket[];
}

export type AdministrativePriority = "HIGH" | "STANDARD" | "REVIEW";

export interface AdminPriorityFactors {
  verified_high_priority_category: boolean;
  open_protection_request: boolean;
  explicit_human_support_request: boolean;
  verified_wellbeing_review_flag: boolean;
}

export interface AdminPriorityQueueItem {
  case_id: number;
  case_number: string;
  district: string;
  category: string;
  category_verified: boolean;
  priority: AdministrativePriority;
  explanation: string;
  reasons: string[];
  factors: AdminPriorityFactors;
  is_demo: boolean;
}

export interface AdminEscalationTrendPoint {
  date: string;
  request_count: number;
  open_count: number;
  resolved_count: number;
}

export interface AdminAuditEntry {
  id: number;
  actor_user_id: number | null;
  action: string;
  resource_type: string;
  resource_id: string;
  metadata: Record<string, unknown>;
  created_at: string;
  is_demo: boolean;
}

export interface AdminDashboard {
  aggregate: AdminAggregate;
  district_analytics: AdminDistrictAnalytics[];
  support_request_counts: AdminSupportRequestCounts;
  priority_queue: AdminPriorityQueueItem[];
  escalation_trends: AdminEscalationTrendPoint[];
  notifications: Notification[];
  audit_entries: AdminAuditEntry[];
}


export interface AdminUserDetail {
  id: number; full_name: string; display_name: string; email: string | null; phone: string; date_of_birth: string | null;
  role: string; status: string; state_id: number | null; district_id: number | null; state_name: string | null; district_name: string | null;
  case_count: number; open_case_count: number; support_request_count: number; last_checkin_at: string | null; is_demo: boolean;
}
