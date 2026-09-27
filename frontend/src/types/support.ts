export type SupportCategory = "counselling" | "legal_help" | "protection_relocation";
export type SupportRequestStatus = "pending" | "assigned" | "in_progress" | "resolved" | "cancelled";

export interface SupportAssignment {
  id: number;
  assignment_type: string;
  status: string;
  reason: string;
  active: boolean;
  assigned_at: string;
}

export interface SupportUpdate {
  id: number;
  action: string;
  status: "recorded" | "completed" | "failed";
  notes: string;
  created_at: string;
}

export interface SupportAction {
  id: number;
  support_request_id: number;
  actor_user_id: number;
  action: string;
  status: "recorded" | "completed" | "failed";
  notes: string;
  created_at: string;
  is_demo: boolean;
}

export interface SupportRequest {
  id: number;
  case_id: number;
  category: SupportCategory;
  status: SupportRequestStatus;
  priority: string;
  details: string;
  is_demo: boolean;
  created_at: string;
  updated_at: string;
  resolved_at: string | null;
  assignments: SupportAssignment[];
  updates: SupportUpdate[];
}
