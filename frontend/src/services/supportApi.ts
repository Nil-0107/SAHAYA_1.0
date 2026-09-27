import { api } from "./api";
import type { SupportAction, SupportCategory, SupportRequest } from "../types/support";

export interface CreateSupportRequestPayload {
  case_id: number;
  category: SupportCategory;
  details: string;
}

export const supportApi = {
  async listMine(): Promise<SupportRequest[]> {
    const { data } = await api.get<SupportRequest[]>("/support-requests/me");
    return data;
  },

  async get(id: number): Promise<SupportRequest> {
    const { data } = await api.get<SupportRequest>(`/support-requests/${id}`);
    return data;
  },

  async create(payload: CreateSupportRequestPayload): Promise<SupportRequest> {
    const { data } = await api.post<SupportRequest>("/support-requests", payload);
    return data;
  },

  async createAction(requestId: number, payload: { action: string; notes: string; request_status?: "assigned" | "in_progress" | "resolved" | "cancelled" }): Promise<SupportAction> {
    const { data } = await api.post<SupportAction>(`/support-requests/${requestId}/actions`, payload);
    return data;
  },
};
