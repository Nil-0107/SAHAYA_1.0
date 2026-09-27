import type { Notification } from "./notification";
import type { SupportRequestStatus } from "./support";

export interface CounsellorSupportRequest {
  id: number;
  case_id: number;
  category: string;
  status: SupportRequestStatus;
  priority: string;
  details: string;
  created_at: string;
  updated_at: string;
  is_demo: boolean;
}

export interface CounsellorFollowUp {
  id: number;
  support_request_id: number;
  action: string;
  status: "recorded" | "completed" | "failed";
  notes: string;
  created_at: string;
  is_demo: boolean;
}

export interface CounsellorAggregate {
  assigned_request_count: number;
  open_follow_up_count: number;
  support_action_count: number;
  resolved_request_count: number;
  unread_notification_count: number;
}

export interface CounsellorDashboard {
  support_requests: CounsellorSupportRequest[];
  follow_ups: CounsellorFollowUp[];
  support_actions: CounsellorFollowUp[];
  notifications: Notification[];
  aggregate: CounsellorAggregate;
}


export interface CounsellorUserDetail {
  id: number; full_name: string; display_name: string; email: string | null; phone: string; date_of_birth: string | null;
  district_name: string | null; case_id: number; case_number: string; support_request_id: number; support_category: string;
  support_status: SupportRequestStatus; last_checkin_at: string | null; is_demo: boolean;
}
