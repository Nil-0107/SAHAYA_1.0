import { api } from "./api";
import type { Case, CaseDocument } from "../types/case";

export const caseApi = {
  async listMine(): Promise<Case[]> {
    const { data } = await api.get<Case[]>("/cases/me");
    return data;
  },

  async create(payload: { category: string; summary?: string | null }): Promise<Case> {
    const { data } = await api.post<Case>("/cases", payload);
    return data;
  },

  async get(id: number): Promise<Case> {
    const { data } = await api.get<Case>(`/cases/${id}`);
    return data;
  },

  async uploadDocument(caseId: number | null, file: File): Promise<CaseDocument> {
    const form = new FormData();
    if (caseId) form.append("case_id", String(caseId));
    form.append("file", file);
    const { data } = await api.post<CaseDocument>("/cases/upload", form);
    return data;
  },
};
