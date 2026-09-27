import type { Notification } from "./notification";
import type { CaseStatus } from "./case";
import type { SupportRequestStatus } from "./support";

export interface DistrictCase {
  id: number;
  case_number: string;
  stage: string;
  status: CaseStatus;
  category_verified: boolean;
  next_hearing: string | null;
  is_demo: boolean;
}

export interface DistrictAssistanceRequest {
  id: number;
  case_id: number;
  category: string;
  status: SupportRequestStatus;
  priority: string;
  created_at: string;
  updated_at: string;
  is_demo: boolean;
}

export interface DistrictCoordinationRecord {
  id: number;
  case_id: number;
  support_request_id: number;
  assignment_type: string;
  status: string;
  reason: string;
  active: boolean;
  assigned_at: string;
  is_demo: boolean;
}

export interface DistrictAggregate {
  authorized_case_count: number;
  open_assistance_request_count: number;
  active_coordination_count: number;
  protection_request_count: number;
  unread_notification_count: number;
}

export interface DistrictDashboard {
  cases: DistrictCase[];
  assistance_requests: DistrictAssistanceRequest[];
  coordination: DistrictCoordinationRecord[];
  case_updates: Notification[];
  notifications: Notification[];
  aggregate: DistrictAggregate;
}
