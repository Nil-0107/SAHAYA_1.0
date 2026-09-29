import { api } from "./api";
import type { AIChatResponse } from "../types/ai";

export interface AIChatPayload {
  message: string;
  conversation_id?: number;
}

export const aiApi = {
  async chat(payload: AIChatPayload): Promise<AIChatResponse> {
    const { data } = await api.post<AIChatResponse>("/ai/chat", payload);
    return data;
  },
};


export interface AIVoiceResponse { transcript: string; source: "gemini" | "unavailable"; model_version: string | null; }

export async function transcribeVoice(blob: Blob): Promise<AIVoiceResponse> {
  const form = new FormData();
  form.append("file", blob, "sahaya-voice.webm");
  const { data } = await api.post<AIVoiceResponse>("/ai/voice/transcribe", form);
  return data;
}


export type AIHealthStatus = "unconfigured" | "reachable" | "working" | "unavailable";
export interface AIHealth { configured: boolean; reachable: boolean; generation_working: boolean; status: AIHealthStatus; model: string; }

export async function health(): Promise<AIHealth> { const { data } = await api.get<AIHealth>("/ai/health"); return data; }


export async function speakText(text: string): Promise<void> {
  const { data } = await api.post<Blob>("/ai/voice/speak", { text }, { responseType: "blob" });
  const url = URL.createObjectURL(data);
  const audio = new Audio(url);
  audio.onended = () => URL.revokeObjectURL(url);
  await audio.play();
}
