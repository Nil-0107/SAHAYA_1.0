export type CheckinAnalysisStatus = "not_run" | "completed" | "failed";

export interface Checkin {
  id: number;
  text: string;
  case_id: number | null;
  class_id: number | null;
  label: string | null;
  confidence: number | null;
  model_version: string | null;
  analysis_status: CheckinAnalysisStatus;
  created_at: string;
}
