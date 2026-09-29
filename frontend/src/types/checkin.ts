export type CheckinAnalysisStatus = "not_run" | "completed" | "failed";

export interface EmotionClassification {
  label: "sadness" | "joy" | "love" | "anger" | "fear" | "surprise";
  confidence: number;
  probabilities: Record<EmotionClassification["label"], number>;
  model_version: string;
}

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
  emotion: EmotionClassification | null;
}
