export type CaseStatus = "open" | "in_progress" | "on_hold" | "resolved" | "closed";
export type DocumentStatus = "pending" | "stored" | "processing" | "processed" | "rejected" | "failed";

export interface CaseDocument {
  id: number;
  filename: string;
  mime_type: string;
  status: DocumentStatus;
  uploaded_at: string;
  size_bytes: number | null;
  is_demo: boolean;
}

export interface CaseSupportSummary {
  id: number;
  type: string;
  status: string;
  priority: string;
  is_demo: boolean;
}

export interface CaseUpdate {
  date: string;
  label: string;
  is_demo: boolean;
}

export interface CaseTimelineEvent {
  date: string;
  label: string;
  is_demo: boolean;
}

export interface Case {
  id: number;
  case_number: string;
  category: string;
  category_verified: boolean;
  status: CaseStatus;
  stage: string;
  court_name: string | null;
  next_hearing: string | null;
  summary: string | null;
  protection_request_open: boolean;
  created_at: string;
  is_demo: boolean;
  documents: CaseDocument[];
  support_information: CaseSupportSummary[];
  updates: CaseUpdate[];
  timeline: CaseTimelineEvent[];
}
