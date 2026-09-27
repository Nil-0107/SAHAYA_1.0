export type AIConversationStatus = "active" | "closed" | "unavailable";
export type AIMessageRole = "user" | "assistant" | "system";
export type AIMessageStatus = "complete" | "failed" | "blocked";

export interface AIChatMessage {
  id: number;
  role: AIMessageRole;
  status: AIMessageStatus;
  content: string;
  created_at: string;
}

export interface AIChatResponse {
  conversation_id: number;
  conversation_status: AIConversationStatus;
  source: "gemini" | "fallback";
  model_version: string | null;
  immediate_danger: boolean;
  user_message: AIChatMessage;
  assistant_message: AIChatMessage;
}
